from __future__ import annotations

import json
from pathlib import Path

from jigsaw.controller import (
    apply_outcome_event,
    build_action_record,
    build_case_input,
    build_case_state,
    build_gc_context_snapshot,
    build_outcome_event,
    hypothesis_state_from_gc_context,
)
from jigsaw.lanes.kernel_lane.arbiter_exchange import build_arbiter_exchange
from jigsaw.lanes.real_case_lane.review_case_from_queue import review_case_from_queue


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _seed_case_dir(base: Path, primary_item_id: int = 8) -> tuple[Path, str]:
    case_dir = base / "case_01"
    gc_context = build_gc_context_snapshot(
        {
            "primary_item_id": primary_item_id,
            "related_item_ids": [22, 45, 14],
            "summary": "Remote income opportunity has enough nearby support.",
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
            "candidate_id": f"gc_case:remote_workflow_v1b:{primary_item_id}",
            "judgement": "promoted",
            "confidence": 0.81,
            "reason_summary": "Strong fit justifies review.",
            "key_factors": ["High relevance"],
            "recommended_action": "prioritise_for_review",
        },
        reviewed_at="2026-03-16T08:00:00Z",
    )
    action_record = build_action_record(
        case_state,
        {
            "candidate_id": f"gc_case:remote_workflow_v1b:{primary_item_id}",
            "judgement": "promoted",
            "confidence": 0.81,
            "reason_summary": "Strong fit justifies review.",
            "key_factors": ["High relevance"],
            "recommended_action": "prioritise_for_review",
        },
        "reviewed",
        timestamp="2026-03-16T09:00:00Z",
    )
    outcome_event = build_outcome_event(
        case_state,
        action_record,
        "weakened",
        -0.1,
        timestamp="2026-03-16T10:00:00Z",
    )
    reopened_state = apply_outcome_event(case_state, outcome_event)
    arbiter_exchange = build_arbiter_exchange(
        case_id=reopened_state.case_id,
        sent_packet={"candidate_id": f"gc_case:remote_workflow_v1b:{primary_item_id}"},
        received_packet={"judgement": "promoted"},
        validation_passed=True,
        timestamp="2026-03-16T08:00:00Z",
        exchange_scope="review-queue-test",
        arbiter_metadata={"profile_name": "remote_workflow_v1b"},
    )

    _write_json(case_dir / "gc_context.json", gc_context.model_dump(mode="python"))
    _write_json(case_dir / "case_state.json", reopened_state.model_dump(mode="python"))
    _write_json(case_dir / "action_record.json", action_record.model_dump(mode="python"))
    _write_json(case_dir / "outcome_event.json", outcome_event.model_dump(mode="python"))
    _write_json(case_dir / "arbiter_exchange.json", arbiter_exchange.model_dump(mode="python"))
    return case_dir, reopened_state.case_id


def test_review_case_from_queue_review_now_clears_reopen_flag(tmp_path: Path) -> None:
    lifecycle_root = tmp_path / "lifecycle"
    timeline_root = tmp_path / "timelines"
    output_root = tmp_path / "reviews"
    case_dir, case_id = _seed_case_dir(lifecycle_root)

    result = review_case_from_queue(
        case_id=case_id,
        decision="review_now",
        lifecycle_root=lifecycle_root,
        timeline_root=timeline_root,
        output_root=output_root,
        reviewed_at="2026-03-16T13:00:00Z",
    )

    assert result["status"] == "success"
    updated_state = json.loads((case_dir / "case_state.json").read_text(encoding="utf-8"))
    assert updated_state["reopen_required"] is False
    assert updated_state["latest_reopen_reason"] is None
    assert (output_root / case_id.replace(":", "_") / "review_decision.json").exists()


def test_review_case_from_queue_reruns_forward_pass_and_saves_outputs(tmp_path: Path) -> None:
    lifecycle_root = tmp_path / "lifecycle"
    timeline_root = tmp_path / "timelines"
    output_root = tmp_path / "reviews"
    case_dir, case_id = _seed_case_dir(lifecycle_root, primary_item_id=8)

    result = review_case_from_queue(
        case_id=case_id,
        decision="rerun_forward_pass",
        lifecycle_root=lifecycle_root,
        timeline_root=timeline_root,
        output_root=output_root,
        reviewed_at="2026-03-16T13:30:00Z",
    )

    assert result["status"] == "success"
    rerun_dir = Path(result["rerun_outputs_path"])
    assert rerun_dir.exists()
    assert (rerun_dir / "hypothesis_state.json").exists()
    assert (rerun_dir / "case_input.json").exists()
    assert (rerun_dir / "kernel_bundle_result.json").exists()
    assert (rerun_dir / "arbiter_response.json").exists()
    assert (rerun_dir / "arbiter_exchange.json").exists()

    updated_state = json.loads((case_dir / "case_state.json").read_text(encoding="utf-8"))
    assert updated_state["reopen_required"] is False
    assert updated_state["latest_reopen_reason"] is None
