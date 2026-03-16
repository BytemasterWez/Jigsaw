from __future__ import annotations

import json
from pathlib import Path

from jigsaw.controller import build_case_input, build_case_state, build_gc_context_snapshot, hypothesis_state_from_gc_context
from jigsaw.engines.watchdog import validate_kernel_watchdog_result_v1
from jigsaw.controller.watchdog_override_manager import build_watchdog_override_record
from jigsaw.lanes.real_case_lane.blocked_case_review import (
    build_blocked_case_queue,
    build_blocked_case_review_packet,
)
from jigsaw.lanes.real_case_lane.override_blocked_case import override_blocked_case


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _seed_case(case_root: Path, *, case_num: int, blocked_reason: str | None = None, with_override: bool = False) -> tuple[Path, str]:
    case_dir = case_root / f"case_{case_num:02d}"
    gc_context = build_gc_context_snapshot(
        {
            "primary_item_id": 40 + case_num,
            "related_item_ids": [8, 22, 14],
            "summary": f"Case {case_num} for blocked queue tests.",
            "freshness": "recent",
            "known_gaps": [],
            "source_types": ["note", "note", "note", "note"],
        }
    )
    hypothesis_state = hypothesis_state_from_gc_context(gc_context)
    case_input = build_case_input(hypothesis_state, gc_context)
    case_state = build_case_state(
        case_input,
        gc_context,
        {
            "candidate_id": f"gc_case:remote_workflow_v1b:{40 + case_num}",
            "judgement": "watchlist",
            "confidence": 0.64,
            "reason_summary": "Needs more evidence.",
            "key_factors": ["Moderate fit"],
            "recommended_action": "hold_for_recheck",
        },
        reviewed_at="2026-03-16T08:00:00Z",
    )
    if blocked_reason is not None:
        case_state = case_state.model_copy(
            update={
                "reopen_required": True,
                "latest_reopen_reason": blocked_reason,
                "reopen_conditions": [blocked_reason],
                "current_status": "watching",
            }
        )
        watchdog_result = validate_kernel_watchdog_result_v1(
            {
                "contract": "kernel_watchdog_result",
                "version": "v1",
                "watchdog_id": f"kw:kx:test:{case_num}",
                "exchange_id": f"kx:test:{case_num}",
                "kernel_name": "expected_state",
                "verdict": "fail" if blocked_reason == "watchdog_fail" else "warn",
                "reasons": ["forced_test_failure"],
                "timestamp": "2026-03-16T09:00:00Z",
            }
        )
        _write_json(case_dir / "kernel_watchdog_result.json", watchdog_result.model_dump(mode="python"))
    _write_json(case_dir / "case_state.json", case_state.model_dump(mode="python"))
    _write_json(case_dir / "gc_context.json", gc_context.model_dump(mode="python"))
    _write_json(case_dir / "case_input.json", case_input.model_dump(mode="python"))

    if with_override:
        override = build_watchdog_override_record(
            case_state,
            exchange_id=f"kx:test:{case_num}",
            watchdog_verdict="warn",
            operator_decision="defer_for_manual_review",
            override_reason="Keep for manual review.",
            overridden_by="wesley",
            timestamp="2026-03-16T10:00:00Z",
        )
        _write_json(case_dir / "watchdog_override_record.json", override.model_dump(mode="python"))
    return case_dir, case_state.case_id


def test_blocked_case_queue_includes_only_blocked_cases(tmp_path: Path) -> None:
    lifecycle_root = tmp_path / "lifecycle"
    _seed_case(lifecycle_root, case_num=1, blocked_reason="watchdog_fail")
    _seed_case(lifecycle_root, case_num=2, blocked_reason=None)

    result = build_blocked_case_queue(lifecycle_root=lifecycle_root, output_root=tmp_path / "queue")

    assert result["count"] == 1
    payload = json.loads((tmp_path / "queue" / "blocked_case_queue.json").read_text(encoding="utf-8"))
    assert payload["blocked_cases"][0]["queue_reason"] == "watchdog_fail"


def test_blocked_case_review_packet_contains_required_refs_and_actions(tmp_path: Path) -> None:
    lifecycle_root = tmp_path / "lifecycle"
    _, case_id = _seed_case(lifecycle_root, case_num=1, blocked_reason="watchdog_fail", with_override=True)

    result = build_blocked_case_review_packet(case_id=case_id, lifecycle_root=lifecycle_root, output_root=tmp_path / "packets")

    packet = json.loads(Path(result["packet_json_path"]).read_text(encoding="utf-8"))
    assert packet["blocked_reason"] == "watchdog_fail"
    assert packet["latest_watchdog_event_refs"]
    assert packet["override_history_refs"]
    assert packet["recommended_operator_actions"] == [
        "override_and_continue",
        "close_as_invalid",
        "defer_for_manual_review",
    ]


def test_override_and_continue_removes_case_from_blocked_queue(tmp_path: Path) -> None:
    lifecycle_root = tmp_path / "lifecycle"
    _, case_id = _seed_case(lifecycle_root, case_num=1, blocked_reason="watchdog_fail")

    before = build_blocked_case_queue(lifecycle_root=lifecycle_root, output_root=tmp_path / "queue_before")
    assert before["count"] == 1

    override_blocked_case(
        case_id=case_id,
        decision="override_and_continue",
        override_reason="Proceed with operator accountability.",
        overridden_by="wesley",
        lifecycle_root=lifecycle_root,
        timeline_root=tmp_path / "timelines",
        output_root=tmp_path / "overrides",
        timestamp="2026-03-16T16:30:00Z",
    )
    after = build_blocked_case_queue(lifecycle_root=lifecycle_root, output_root=tmp_path / "queue_after")
    assert after["count"] == 0


def test_deferred_case_remains_visible_with_manual_review_reason(tmp_path: Path) -> None:
    lifecycle_root = tmp_path / "lifecycle"
    _, case_id = _seed_case(lifecycle_root, case_num=1, blocked_reason="watchdog_warn")

    override_blocked_case(
        case_id=case_id,
        decision="defer_for_manual_review",
        override_reason="Hold for later review.",
        overridden_by="wesley",
        lifecycle_root=lifecycle_root,
        timeline_root=tmp_path / "timelines",
        output_root=tmp_path / "overrides",
        timestamp="2026-03-16T16:30:00Z",
    )
    queue = build_blocked_case_queue(lifecycle_root=lifecycle_root, output_root=tmp_path / "queue")
    payload = json.loads(Path(queue["queue_json_path"]).read_text(encoding="utf-8"))
    assert payload["blocked_cases"][0]["queue_reason"] == "watchdog_manual_review_deferred"


def test_closed_invalid_case_no_longer_appears(tmp_path: Path) -> None:
    lifecycle_root = tmp_path / "lifecycle"
    _, case_id = _seed_case(lifecycle_root, case_num=1, blocked_reason="watchdog_fail")

    override_blocked_case(
        case_id=case_id,
        decision="close_as_invalid",
        override_reason="Invalid case.",
        overridden_by="wesley",
        lifecycle_root=lifecycle_root,
        timeline_root=tmp_path / "timelines",
        output_root=tmp_path / "overrides",
        timestamp="2026-03-16T16:30:00Z",
    )
    queue = build_blocked_case_queue(lifecycle_root=lifecycle_root, output_root=tmp_path / "queue")
    assert queue["count"] == 0
