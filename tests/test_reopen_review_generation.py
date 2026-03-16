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
from jigsaw.lanes.real_case_lane.generate_reopen_review_packets import generate_reopen_review_packets


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_generate_reopen_review_queue_and_packet(tmp_path: Path) -> None:
    lifecycle_root = tmp_path / "lifecycle"
    output_root = tmp_path / "reopen_review"

    gc_context = build_gc_context_snapshot(
        {
            "primary_item_id": 8,
            "related_item_ids": [22, 45, 14],
            "summary": "Remote income opportunity has enough nearby support.",
            "freshness": "recent",
            "known_gaps": [],
        }
    )
    hypothesis_state = hypothesis_state_from_gc_context(gc_context)
    case_input = build_case_input(hypothesis_state, gc_context)
    case_state = build_case_state(
        case_input,
        gc_context,
        {
            "candidate_id": "gc_case:remote_workflow_v1b:8",
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
            "candidate_id": "gc_case:remote_workflow_v1b:8",
            "judgement": "promoted",
            "confidence": 0.81,
            "reason_summary": "Strong fit justifies review.",
            "key_factors": ["High relevance"],
            "recommended_action": "prioritise_for_review",
        },
        "reviewed",
        timestamp="2026-03-16T09:00:00Z",
        notes="Reviewed by analyst.",
    )
    outcome_event = build_outcome_event(
        case_state,
        action_record,
        "weakened",
        -0.1,
        timestamp="2026-03-16T12:00:00Z",
        notes="Follow-up weakened the case.",
    )
    reopened_case_state = apply_outcome_event(case_state, outcome_event)

    case_dir = lifecycle_root / "case_01"
    _write_json(case_dir / "gc_context.json", gc_context.model_dump(mode="python", exclude_none=True))
    _write_json(case_dir / "case_state.json", reopened_case_state.model_dump(mode="python"))
    _write_json(case_dir / "action_record.json", action_record.model_dump(mode="python"))
    _write_json(case_dir / "outcome_event.json", outcome_event.model_dump(mode="python"))

    result = generate_reopen_review_packets(lifecycle_root=lifecycle_root, output_root=output_root)

    assert result["status"] == "success"
    assert result["cases_requiring_review"] == 1

    queue_path = Path(result["queue_path"])
    assert queue_path.exists()
    queue_text = queue_path.read_text(encoding="utf-8")
    assert "Reopen Review Queue" in queue_text
    assert "case:hyp:gc:8" in queue_text

    packet_path = Path(result["packet_paths"][0])
    assert packet_path.exists()
    packet_text = packet_path.read_text(encoding="utf-8")
    assert "Reopen Review Packet" in packet_text
    assert "Fresh case_input preview" in packet_text
    assert "outcome_requires_review" in packet_text
