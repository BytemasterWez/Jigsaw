from __future__ import annotations

from jigsaw.controller import (
    apply_outcome_event,
    apply_relevance_signal,
    apply_watchdog_result,
    build_action_record,
    build_case_input,
    build_case_relevance_signal,
    build_case_state,
    build_gc_context_snapshot,
    build_outcome_event,
    hypothesis_state_from_gc_context,
    list_reopen_cases,
    mark_case_reviewed,
    prepare_reopened_case_input,
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


def test_list_reopen_cases_filters_only_reopen_required_cases() -> None:
    case_state = _sample_case_state()
    reopened = case_state.model_copy(update={"reopen_required": True})

    cases = list_reopen_cases([case_state, reopened])

    assert [case.case_id for case in cases] == [reopened.case_id]


def test_mark_case_reviewed_clears_reopen_flag_and_increments_revision() -> None:
    case_state = _sample_case_state().model_copy(
        update={
            "reopen_required": True,
            "reopen_conditions": ["outcome_requires_review"],
        }
    )

    reviewed = mark_case_reviewed(case_state, reviewed_at="2026-03-17T09:00:00Z")

    assert reviewed.reopen_required is False
    assert reviewed.reopen_conditions == []
    assert reviewed.revision_count == case_state.revision_count + 1


def test_prepare_reopened_case_input_builds_new_case_input_from_reviewed_state() -> None:
    case_state = _sample_case_state().model_copy(update={"reopen_required": True})
    gc_context = _sample_gc_context()

    reviewed = mark_case_reviewed(case_state, reviewed_at="2026-03-17T09:00:00Z")
    hypothesis_state, case_input = prepare_reopened_case_input(reviewed, gc_context)

    assert hypothesis_state.hypothesis_id == reviewed.hypothesis_id
    assert case_input.case_id == reviewed.case_id
    assert case_input.hypothesis_id == reviewed.hypothesis_id


def test_apply_relevance_signal_reopen_case_sets_reopen_required() -> None:
    case_state = _sample_case_state()
    gc_context = _sample_gc_context()
    signal = build_case_relevance_signal(
        case_state,
        gc_context,
        {
            "item_id": 501,
            "title": "Remote income opportunity review update",
            "content": "Remote income review update with matching opportunity details and linked items.",
            "related_item_ids": [8, 22],
            "source_types": ["gc_item"],
            "topic_hints": ["remote", "income"],
        },
        timestamp="2026-03-17T10:00:00Z",
    ).model_copy(update={"recommended_effect": "reopen_case"})

    updated = apply_relevance_signal(case_state, signal)

    assert updated.reopen_required is True
    assert updated.latest_relevance_signal_id == signal.signal_id
    assert updated.latest_reopen_reason == "new_relevant_material_detected"


def test_apply_relevance_signal_attach_context_does_not_reopen() -> None:
    case_state = _sample_case_state()
    gc_context = _sample_gc_context()
    signal = build_case_relevance_signal(
        case_state,
        gc_context,
        {
            "item_id": 502,
            "title": "Related note",
            "content": "Some overlap with remote income context.",
            "related_item_ids": [8],
            "source_types": ["note"],
            "topic_hints": ["income"],
        },
        timestamp="2026-03-17T10:00:00Z",
    ).model_copy(update={"recommended_effect": "attach_context"})

    updated = apply_relevance_signal(case_state, signal)

    assert updated.reopen_required is False
    assert updated.latest_relevance_signal_id == signal.signal_id
    assert updated.latest_reopen_reason == "relevant_material_attached"


def test_apply_relevance_signal_ignore_leaves_lifecycle_unchanged() -> None:
    case_state = _sample_case_state()
    gc_context = _sample_gc_context()
    signal = build_case_relevance_signal(
        case_state,
        gc_context,
        {
            "item_id": 503,
            "title": "Unrelated note",
            "content": "Nothing relevant here.",
            "related_item_ids": [],
            "source_types": ["note"],
            "topic_hints": [],
        },
        timestamp="2026-03-17T10:00:00Z",
    ).model_copy(update={"recommended_effect": "ignore"})

    updated = apply_relevance_signal(case_state, signal)

    assert updated.reopen_required is False
    assert updated.latest_relevance_signal_id == signal.signal_id
    assert updated.latest_reopen_reason is None


def test_apply_relevance_signal_does_not_reopen_closed_case() -> None:
    case_state = _sample_case_state().model_copy(update={"current_status": "closed"})
    gc_context = _sample_gc_context()
    signal = build_case_relevance_signal(
        case_state,
        gc_context,
        {
            "item_id": 504,
            "title": "Remote income opportunity update",
            "content": "Potentially relevant material.",
            "related_item_ids": [8],
            "source_types": ["gc_item"],
            "topic_hints": ["remote"],
        },
        timestamp="2026-03-17T10:00:00Z",
    ).model_copy(update={"recommended_effect": "reopen_case"})

    updated = apply_relevance_signal(case_state, signal)

    assert updated.current_status == "closed"
    assert updated.reopen_required is False


def test_apply_watchdog_result_warn_marks_case_for_review() -> None:
    case_state = _sample_case_state()

    updated = apply_watchdog_result(
        case_state,
        {
            "contract": "kernel_watchdog_result",
            "version": "v1",
            "watchdog_id": "kw:kx:test:observed_state",
            "exchange_id": "kx:test:observed_state",
            "kernel_name": "observed_state",
            "verdict": "warn",
            "reasons": ["missing_engine_metadata_for_lm_mode"],
            "timestamp": "2026-03-17T11:00:00Z",
        },
    )

    assert updated.current_status == "watching"
    assert updated.reopen_required is True
    assert updated.latest_reopen_reason == "watchdog_warn"
    assert updated.reopen_conditions == ["watchdog_warn"]
    assert updated.revision_count == case_state.revision_count + 1


def test_apply_watchdog_result_fail_marks_case_for_urgent_review() -> None:
    case_state = _sample_case_state()

    updated = apply_watchdog_result(
        case_state,
        {
            "contract": "kernel_watchdog_result",
            "version": "v1",
            "watchdog_id": "kw:kx:test:expected_state",
            "exchange_id": "kx:test:expected_state",
            "kernel_name": "expected_state",
            "verdict": "fail",
            "reasons": ["kernel_output_validation_failed"],
            "timestamp": "2026-03-17T11:00:00Z",
        },
    )

    assert updated.current_status == "watching"
    assert updated.reopen_required is True
    assert updated.latest_reopen_reason == "watchdog_fail"
    assert updated.reopen_conditions == ["watchdog_fail"]


def test_apply_watchdog_result_pass_leaves_lifecycle_unchanged() -> None:
    case_state = _sample_case_state()

    updated = apply_watchdog_result(
        case_state,
        {
            "contract": "kernel_watchdog_result",
            "version": "v1",
            "watchdog_id": "kw:kx:test:contradiction",
            "exchange_id": "kx:test:contradiction",
            "kernel_name": "contradiction",
            "verdict": "pass",
            "reasons": [],
            "timestamp": "2026-03-17T11:00:00Z",
        },
    )

    assert updated.reopen_required is False
    assert updated.latest_reopen_reason is None
    assert updated.current_status == case_state.current_status
