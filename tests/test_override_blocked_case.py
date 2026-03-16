from __future__ import annotations

import json
from pathlib import Path

from jigsaw.controller import build_case_input, build_case_state, build_gc_context_snapshot, hypothesis_state_from_gc_context
from jigsaw.engines.watchdog import validate_kernel_watchdog_result_v1
from jigsaw.lanes.real_case_lane.override_blocked_case import override_blocked_case


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _seed_blocked_case_dir(base: Path) -> tuple[Path, str]:
    case_dir = base / "case_01"
    gc_context = build_gc_context_snapshot(
        {
            "primary_item_id": 45,
            "related_item_ids": [8, 22, 14],
            "summary": "Blocked remote workflow case.",
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
            "candidate_id": "gc_case:remote_workflow_v1b:45",
            "judgement": "watchlist",
            "confidence": 0.64,
            "reason_summary": "Needs more evidence.",
            "key_factors": ["Moderate fit"],
            "recommended_action": "hold_for_recheck",
        },
        reviewed_at="2026-03-16T08:00:00Z",
    ).model_copy(
        update={
            "reopen_required": True,
            "latest_reopen_reason": "watchdog_fail",
            "reopen_conditions": ["watchdog_fail"],
            "current_status": "watching",
        }
    )
    watchdog_result = validate_kernel_watchdog_result_v1(
        {
            "contract": "kernel_watchdog_result",
            "version": "v1",
            "watchdog_id": "kw:kx:test",
            "exchange_id": "kx:test",
            "kernel_name": "expected_state",
            "verdict": "fail",
            "reasons": ["forced_test_failure"],
            "timestamp": "2026-03-16T09:00:00Z",
        }
    )

    _write_json(case_dir / "case_state.json", case_state.model_dump(mode="python"))
    _write_json(case_dir / "gc_context.json", gc_context.model_dump(mode="python"))
    _write_json(case_dir / "kernel_watchdog_result.json", watchdog_result.model_dump(mode="python"))
    return case_dir, case_state.case_id


def test_override_blocked_case_override_and_continue_updates_case_state(tmp_path: Path) -> None:
    lifecycle_root = tmp_path / "lifecycle"
    timeline_root = tmp_path / "timelines"
    output_root = tmp_path / "blocked_reviews"
    case_dir, case_id = _seed_blocked_case_dir(lifecycle_root)

    result = override_blocked_case(
        case_id=case_id,
        decision="override_and_continue",
        override_reason="Proceed under explicit operator review.",
        overridden_by="wesley",
        lifecycle_root=lifecycle_root,
        timeline_root=timeline_root,
        output_root=output_root,
        timestamp="2026-03-16T16:30:00Z",
    )

    assert result["status"] == "success"
    updated_state = json.loads((case_dir / "case_state.json").read_text(encoding="utf-8"))
    assert updated_state["reopen_required"] is False
    assert updated_state["latest_reopen_reason"] == "watchdog_override_continue"
    assert (case_dir / "watchdog_override_record.json").exists()
    assert (output_root / case_id.replace(":", "_") / "watchdog_override_decision.json").exists()


def test_override_blocked_case_close_as_invalid_closes_case(tmp_path: Path) -> None:
    lifecycle_root = tmp_path / "lifecycle"
    timeline_root = tmp_path / "timelines"
    output_root = tmp_path / "blocked_reviews"
    case_dir, case_id = _seed_blocked_case_dir(lifecycle_root)

    result = override_blocked_case(
        case_id=case_id,
        decision="close_as_invalid",
        override_reason="Blocked case is not valid.",
        overridden_by="wesley",
        lifecycle_root=lifecycle_root,
        timeline_root=timeline_root,
        output_root=output_root,
        timestamp="2026-03-16T16:35:00Z",
    )

    assert result["status"] == "success"
    updated_state = json.loads((case_dir / "case_state.json").read_text(encoding="utf-8"))
    assert updated_state["current_status"] == "closed"
    assert updated_state["reopen_required"] is False
