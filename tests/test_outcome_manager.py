from __future__ import annotations

import pytest

from jigsaw.controller import (
    build_action_record,
    build_case_input,
    build_case_state,
    build_gc_context_snapshot,
    build_outcome_event,
    hypothesis_state_from_gc_context,
    validate_outcome_event_v1,
)


def _sample_case_state_and_action():
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
    return case_state, action_record


def test_build_outcome_event_links_case_state_and_action_record() -> None:
    case_state, action_record = _sample_case_state_and_action()

    outcome_event = build_outcome_event(
        case_state,
        action_record,
        "confirmed",
        0.1,
        recorded_by="human",
        timestamp="2026-03-16T12:00:00Z",
        notes="Manual review confirmed the opportunity signal.",
    )

    assert outcome_event.contract == "outcome_event"
    assert outcome_event.case_id == case_state.case_id
    assert outcome_event.action_id == action_record.action_id
    assert outcome_event.observed_outcome == "confirmed"
    assert outcome_event.effect_on_confidence == 0.1


def test_validate_outcome_event_v1_accepts_explicit_payload() -> None:
    outcome_event = validate_outcome_event_v1(
        {
            "contract": "outcome_event",
            "version": "v1",
            "event_id": "outcome:action:case:hyp:gc:8:1",
            "case_id": "case:hyp:gc:8",
            "action_id": "action:case:hyp:gc:8:1",
            "observed_outcome": "weakened",
            "recorded_by": "human",
            "timestamp": "2026-03-16T12:00:00Z",
            "effect_on_confidence": -0.15,
            "notes": "Follow-up weakened the initial recommendation.",
        }
    )

    assert outcome_event.observed_outcome == "weakened"
    assert outcome_event.effect_on_confidence == -0.15


def test_build_outcome_event_rejects_mismatched_case_ids() -> None:
    case_state, action_record = _sample_case_state_and_action()
    mismatched_action = action_record.model_copy(update={"case_id": "case:hyp:gc:99"})

    with pytest.raises(ValueError, match="must match"):
        build_outcome_event(
            case_state,
            mismatched_action,
            "unchanged",
            0.0,
            timestamp="2026-03-16T12:00:00Z",
        )
