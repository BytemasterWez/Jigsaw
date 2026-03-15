from __future__ import annotations

from jigsaw.controller.hypothesis_controller import (
    hypothesis_state_from_gc_context,
    refresh_hypothesis_state,
)


def test_hypothesis_state_builds_with_gathering_evidence_when_support_is_thin() -> None:
    state = hypothesis_state_from_gc_context(
        {
            "primary_item_id": 8,
            "related_item_ids": [],
            "summary": "Remote income opportunity still needs more grounding.",
            "freshness": "recent",
            "known_gaps": ["pricing", "use case definition"],
        }
    )

    assert state.contract == "hypothesis_state"
    assert state.state == "gathering_evidence"
    assert state.missing_evidence == ["pricing", "use case definition"]


def test_hypothesis_state_becomes_sufficient_when_support_is_adequate() -> None:
    state = hypothesis_state_from_gc_context(
        {
            "primary_item_id": 8,
            "related_item_ids": [22, 45, 14],
            "summary": "Remote income opportunity has enough nearby support.",
            "freshness": "recent",
            "known_gaps": [],
        }
    )

    assert state.state == "sufficient"
    assert state.confidence == 0.78
    assert "Package this branch" in state.next_probe


def test_hypothesis_state_becomes_conflicted_when_conflict_evidence_exists() -> None:
    state = hypothesis_state_from_gc_context(
        {
            "primary_item_id": 9,
            "related_item_ids": [8, 45],
            "summary": "AI tools branch has mixed evidence.",
            "freshness": "recent",
            "known_gaps": [],
            "conflicting_item_ids": [14],
        }
    )

    assert state.state == "conflicted"
    assert state.conflicting_evidence_ids == ["gc:item:14"]


def test_refresh_hypothesis_state_updates_state_from_new_context() -> None:
    initial = hypothesis_state_from_gc_context(
        {
            "primary_item_id": 8,
            "related_item_ids": [],
            "summary": "Remote income opportunity still needs more grounding.",
            "freshness": "stale",
            "known_gaps": ["pricing"],
        }
    )

    refreshed = refresh_hypothesis_state(
        initial,
        gc_context={
            "primary_item_id": 8,
            "related_item_ids": [22, 45, 14],
            "summary": "Remote income opportunity now has enough support.",
            "freshness": "recent",
            "known_gaps": [],
        },
    )

    assert refreshed.hypothesis_id == initial.hypothesis_id
    assert refreshed.question_or_claim == initial.question_or_claim
    assert refreshed.state == "sufficient"
