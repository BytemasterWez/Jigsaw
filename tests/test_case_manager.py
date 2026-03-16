from __future__ import annotations

from jigsaw.controller import (
    apply_outcome_event,
    build_action_record,
    build_case_input,
    build_case_state,
    build_gc_context_snapshot,
    build_outcome_event,
    hypothesis_state_from_gc_context,
    update_case_state,
)


def _sample_gc_context():
    return build_gc_context_snapshot(
        {
            "primary_item_id": 8,
            "related_item_ids": [22, 45, 14],
            "summary": "Remote income opportunity has enough nearby support.",
            "freshness": "recent",
            "known_gaps": [],
        }
    )


def _sample_case_input():
    gc_context = _sample_gc_context()
    hypothesis = hypothesis_state_from_gc_context(gc_context)
    return build_case_input(hypothesis, gc_context), gc_context


def _sample_case_state():
    case_input, gc_context = _sample_case_input()
    return build_case_state(
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


def _sample_action_and_outcome(observed_outcome: str, effect_on_confidence: float):
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
    outcome_event = build_outcome_event(
        case_state,
        action_record,
        observed_outcome,
        effect_on_confidence,
        recorded_by="human",
        timestamp="2026-03-16T12:00:00Z",
        notes="Lifecycle test outcome.",
    )
    return case_state, outcome_event


def test_build_case_state_from_completed_forward_pass() -> None:
    case_input, gc_context = _sample_case_input()

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

    assert case_state.contract == "case_state"
    assert case_state.case_id == case_input.case_id
    assert case_state.current_status == "promoted"
    assert case_state.latest_decision == "promoted"
    assert case_state.latest_snapshot_id == gc_context.snapshot_id
    assert case_state.confidence_current == 0.81
    assert case_state.confidence_trajectory == "stale"
    assert case_state.last_outcome_at is None
    assert case_state.latest_outcome is None
    assert case_state.reopen_required is False
    assert case_state.revision_count == 1


def test_update_case_state_increments_revision_and_tracks_upward_confidence() -> None:
    case_input, gc_context = _sample_case_input()
    initial = build_case_state(
        case_input,
        gc_context,
        {
            "candidate_id": "gc_case:remote_workflow_v1b:8",
            "judgement": "watchlist",
            "confidence": 0.63,
            "reason_summary": "Needs more evidence.",
            "key_factors": ["Moderate fit"],
            "recommended_action": "hold_for_recheck",
        },
        reviewed_at="2026-03-16T08:00:00Z",
    )

    updated = update_case_state(
        initial,
        arbiter_response={
            "candidate_id": "gc_case:remote_workflow_v1b:8",
            "judgement": "promoted",
            "confidence": 0.81,
            "reason_summary": "Strong fit justifies review.",
            "key_factors": ["High relevance"],
            "recommended_action": "prioritise_for_review",
        },
        snapshot_id="gcs:gc:8:rev2",
        reviewed_at="2026-03-17T08:00:00Z",
    )

    assert updated.current_status == "promoted"
    assert updated.latest_decision == "promoted"
    assert updated.latest_snapshot_id == "gcs:gc:8:rev2"
    assert updated.confidence_current == 0.81
    assert updated.confidence_trajectory == "up"
    assert updated.revision_count == 2


def test_update_case_state_tracks_flat_confidence_when_delta_is_small() -> None:
    case_input, gc_context = _sample_case_input()
    initial = build_case_state(
        case_input,
        gc_context,
        {
            "candidate_id": "gc_case:remote_workflow_v1b:8",
            "judgement": "watchlist",
            "confidence": 0.63,
            "reason_summary": "Needs more evidence.",
            "key_factors": ["Moderate fit"],
            "recommended_action": "hold_for_recheck",
        },
        reviewed_at="2026-03-16T08:00:00Z",
    )

    updated = update_case_state(
        initial,
        arbiter_response={
            "candidate_id": "gc_case:remote_workflow_v1b:8",
            "judgement": "watchlist",
            "confidence": 0.64,
            "reason_summary": "Still needs more evidence.",
            "key_factors": ["Moderate fit"],
            "recommended_action": "hold_for_recheck",
        },
        snapshot_id="gcs:gc:8:rev2",
        reviewed_at="2026-03-17T08:00:00Z",
    )

    assert updated.current_status == "watching"
    assert updated.confidence_trajectory == "flat"
    assert updated.revision_count == 2


def test_update_case_state_tracks_downward_confidence() -> None:
    case_input, gc_context = _sample_case_input()
    initial = build_case_state(
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

    updated = update_case_state(
        initial,
        arbiter_response={
            "candidate_id": "gc_case:remote_workflow_v1b:8",
            "judgement": "watchlist",
            "confidence": 0.63,
            "reason_summary": "Confidence weakened.",
            "key_factors": ["Evidence weakened"],
            "recommended_action": "hold_for_recheck",
        },
        snapshot_id="gcs:gc:8:rev2",
        reviewed_at="2026-03-17T08:00:00Z",
    )

    assert updated.current_status == "watching"
    assert updated.confidence_trajectory == "down"
    assert updated.revision_count == 2


def test_apply_outcome_event_strengthened_moves_confidence_up() -> None:
    case_state, outcome_event = _sample_action_and_outcome("strengthened", 0.1)

    updated = apply_outcome_event(case_state, outcome_event)

    assert updated.confidence_current == 0.91
    assert updated.confidence_trajectory == "up"
    assert updated.reopen_required is False
    assert updated.latest_outcome == "strengthened"


def test_apply_outcome_event_weakened_moves_confidence_down_and_reopens() -> None:
    case_state, outcome_event = _sample_action_and_outcome("weakened", -0.1)

    updated = apply_outcome_event(case_state, outcome_event)

    assert updated.current_status == "watching"
    assert updated.confidence_current == 0.71
    assert updated.confidence_trajectory == "down"
    assert updated.reopen_required is True


def test_apply_outcome_event_unchanged_sets_flat_trajectory() -> None:
    case_state, outcome_event = _sample_action_and_outcome("unchanged", 0.0)

    updated = apply_outcome_event(case_state, outcome_event)

    assert updated.confidence_current == 0.81
    assert updated.confidence_trajectory == "flat"
    assert updated.reopen_required is False


def test_apply_outcome_event_invalidated_marks_reopen_required() -> None:
    case_state, outcome_event = _sample_action_and_outcome("invalidated", -0.2)

    updated = apply_outcome_event(case_state, outcome_event)

    assert updated.current_status == "watching"
    assert updated.latest_outcome == "invalidated"
    assert updated.reopen_required is True


def test_apply_outcome_event_clamps_confidence_to_valid_range() -> None:
    case_state, outcome_event = _sample_action_and_outcome("confirmed", 0.5)

    updated = apply_outcome_event(case_state, outcome_event)

    assert updated.confidence_current == 1.0


def test_apply_outcome_event_increments_revision_count() -> None:
    case_state, outcome_event = _sample_action_and_outcome("confirmed", 0.1)

    updated = apply_outcome_event(case_state, outcome_event)

    assert updated.revision_count == case_state.revision_count + 1
