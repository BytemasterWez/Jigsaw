from __future__ import annotations

from jigsaw.controller import (
    apply_watchdog_override,
    build_action_record,
    build_case_input,
    build_case_state,
    build_gc_context_snapshot,
    build_outcome_event,
    build_watchdog_override_record,
    hypothesis_state_from_gc_context,
)


def _sample_blocked_case_state():
    gc_context = build_gc_context_snapshot(
        {
            "primary_item_id": 45,
            "related_item_ids": [8, 22, 14],
            "summary": "Remote workflow opportunity needs follow-up.",
            "freshness": "recent",
            "known_gaps": [],
        }
    )
    hypothesis_state = hypothesis_state_from_gc_context(gc_context)
    case_input = build_case_input(hypothesis_state, gc_context)
    base_state = build_case_state(
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
        reviewed_at="2026-03-16T09:00:00Z",
    )
    return base_state.model_copy(
        update={
            "current_status": "watching",
            "reopen_required": True,
            "latest_reopen_reason": "watchdog_fail",
            "reopen_conditions": ["watchdog_fail"],
        }
    )


def test_build_watchdog_override_record() -> None:
    case_state = _sample_blocked_case_state()

    override = build_watchdog_override_record(
        case_state,
        exchange_id="kx:test:expected_state",
        watchdog_verdict="fail",
        operator_decision="override_and_continue",
        override_reason="Operator confirmed the case is still worth reviewing.",
        overridden_by="wesley",
        timestamp="2026-03-16T16:30:00Z",
    )

    assert override.case_id == case_state.case_id
    assert override.watchdog_verdict == "fail"
    assert override.operator_decision == "override_and_continue"


def test_apply_watchdog_override_continue_clears_reopen_flag() -> None:
    case_state = _sample_blocked_case_state()
    override = build_watchdog_override_record(
        case_state,
        exchange_id="kx:test:expected_state",
        watchdog_verdict="fail",
        operator_decision="override_and_continue",
        override_reason="Continue with operator accountability.",
        overridden_by="wesley",
        timestamp="2026-03-16T16:30:00Z",
    )

    updated = apply_watchdog_override(case_state, override)

    assert updated.reopen_required is False
    assert updated.current_status == "watching"
    assert updated.latest_reopen_reason == "watchdog_override_continue"


def test_apply_watchdog_override_close_as_invalid_closes_case() -> None:
    case_state = _sample_blocked_case_state()
    override = build_watchdog_override_record(
        case_state,
        exchange_id="kx:test:expected_state",
        watchdog_verdict="fail",
        operator_decision="close_as_invalid",
        override_reason="The blocked case is invalid.",
        overridden_by="wesley",
        timestamp="2026-03-16T16:35:00Z",
    )

    updated = apply_watchdog_override(case_state, override)

    assert updated.current_status == "closed"
    assert updated.reopen_required is False
    assert updated.latest_reopen_reason == "watchdog_closed_invalid"


def test_apply_watchdog_override_defer_keeps_case_in_review() -> None:
    case_state = _sample_blocked_case_state()
    override = build_watchdog_override_record(
        case_state,
        exchange_id="kx:test:expected_state",
        watchdog_verdict="warn",
        operator_decision="defer_for_manual_review",
        override_reason="Needs more careful manual review.",
        overridden_by="wesley",
        timestamp="2026-03-16T16:40:00Z",
    )

    updated = apply_watchdog_override(case_state, override)

    assert updated.current_status == "watching"
    assert updated.reopen_required is True
    assert updated.latest_reopen_reason == "watchdog_manual_review_deferred"
