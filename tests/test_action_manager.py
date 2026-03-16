from __future__ import annotations

from jigsaw.controller import (
    build_action_record,
    build_case_input,
    build_case_state,
    build_gc_context_snapshot,
    hypothesis_state_from_gc_context,
    validate_action_record_v1,
)


def _sample_case_state():
    gc_context = build_gc_context_snapshot(
        {
            "primary_item_id": 8,
            "related_item_ids": [22, 45, 14],
            "summary": "Remote income opportunity has enough nearby support.",
            "freshness": "recent",
            "known_gaps": [],
        }
    )
    hypothesis = hypothesis_state_from_gc_context(gc_context)
    case_input = build_case_input(hypothesis, gc_context)
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
    return case_state


def test_build_action_record_links_human_action_to_case_state() -> None:
    case_state = _sample_case_state()

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
        taken_by="human",
        timestamp="2026-03-16T09:00:00Z",
        notes="Reviewed by analyst after promotion.",
    )

    assert action_record.contract == "action_record"
    assert action_record.case_id == case_state.case_id
    assert action_record.recommended_action == "prioritise_for_review"
    assert action_record.action_taken == "reviewed"
    assert action_record.taken_by == "human"


def test_validate_action_record_v1_accepts_explicit_payload() -> None:
    action_record = validate_action_record_v1(
        {
            "contract": "action_record",
            "version": "v1",
            "action_id": "action:case:hyp:gc:8:1",
            "case_id": "case:hyp:gc:8",
            "recommended_action": "hold_for_recheck",
            "action_taken": "deferred",
            "taken_by": "human",
            "timestamp": "2026-03-16T09:00:00Z",
            "notes": "Deferred pending a second review.",
        }
    )

    assert action_record.recommended_action == "hold_for_recheck"
    assert action_record.action_taken == "deferred"
