from __future__ import annotations

from jigsaw.controller import (
    build_case_input,
    build_case_relevance_signal,
    build_case_state,
    build_gc_context_snapshot,
    hypothesis_state_from_gc_context,
    validate_case_relevance_signal_v1,
)


def _sample_case_state_and_context():
    gc_context = build_gc_context_snapshot(
        {
            "primary_item_id": 45,
            "related_item_ids": [8, 22, 14],
            "summary": "Assess whether this remote workflow opportunity is ready to package for review.",
            "freshness": "recent",
            "known_gaps": [],
            "source_types": ["pasted_text", "pasted_text"],
        }
    )
    hypothesis_state = hypothesis_state_from_gc_context(
        gc_context,
        question_or_claim="Should this remote workflow opportunity be packaged for review?",
    )
    case_input = build_case_input(hypothesis_state, gc_context)
    case_state = build_case_state(
        case_input,
        gc_context,
        {
            "candidate_id": "gc_case:remote_workflow_v1b:45",
            "judgement": "promoted",
            "confidence": 0.81,
            "reason_summary": "Strong fit justifies review.",
            "key_factors": ["High relevance"],
            "recommended_action": "prioritise_for_review",
        },
        reviewed_at="2026-03-16T08:00:00Z",
    )
    return case_state, gc_context


def test_build_case_relevance_signal_reopens_for_strong_overlap() -> None:
    case_state, gc_context = _sample_case_state_and_context()

    signal = build_case_relevance_signal(
        case_state,
        gc_context,
        {
            "item_id": 101,
            "title": "Remote workflow opportunity pricing update",
            "content": "This note adds pricing and remote workflow review details for the same opportunity case.",
            "related_item_ids": [45, 8],
            "source_types": ["pasted_text"],
            "topic_hints": ["pricing", "workflow"],
        },
        timestamp="2026-03-16T12:00:00Z",
    )

    assert signal.case_id == case_state.case_id
    assert signal.candidate_item_id == "gc:item:101"
    assert signal.match_score >= 0.35
    assert signal.recommended_effect in {"attach_context", "reopen_case"}


def test_build_case_relevance_signal_ignores_weak_overlap() -> None:
    case_state, gc_context = _sample_case_state_and_context()

    signal = build_case_relevance_signal(
        case_state,
        gc_context,
        {
            "item_id": 202,
            "title": "Gardening notes",
            "content": "Tomato planting schedule and compost notes.",
            "related_item_ids": [303],
            "source_types": ["note"],
            "topic_hints": ["garden"],
        },
        timestamp="2026-03-16T12:00:00Z",
    )

    assert signal.match_score == 0.0
    assert signal.recommended_effect == "ignore"


def test_validate_case_relevance_signal_v1_accepts_explicit_payload() -> None:
    signal = validate_case_relevance_signal_v1(
        {
            "contract": "case_relevance_signal",
            "version": "v1",
            "signal_id": "crs:case:hyp:gc:45:gc:item:101",
            "case_id": "case:hyp:gc:45",
            "candidate_item_id": "gc:item:101",
            "match_score": 0.72,
            "match_reason": "title overlap 0.5, related evidence overlap 0.67.",
            "recommended_effect": "reopen_case",
            "timestamp": "2026-03-16T12:00:00Z",
        }
    )

    assert signal.recommended_effect == "reopen_case"
    assert signal.match_score == 0.72
