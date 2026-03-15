from __future__ import annotations

from jigsaw.controller.hypothesis_controller import (
    hypothesis_state_from_gc_context,
    refresh_hypothesis_state,
    select_next_probe,
    transition_state,
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
    assert state.next_probe == "gather_related_context"


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
    assert state.next_probe == "package_case"


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
    assert state.next_probe == "inspect_conflicts"


def test_hypothesis_state_becomes_escalate_when_promising_but_incomplete() -> None:
    state = hypothesis_state_from_gc_context(
        {
            "primary_item_id": 45,
            "related_item_ids": [8, 14],
            "summary": "Remote workflow systems branch is promising but still incomplete.",
            "freshness": "recent",
            "known_gaps": ["pricing detail"],
        }
    )

    assert state.state == "escalate"
    assert state.next_probe == "escalate"


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


def test_select_next_probe_uses_explicit_state_rules() -> None:
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

    assert select_next_probe(state) == "inspect_conflicts"


def test_transition_state_moves_open_hypothesis_to_package_case_when_support_is_adequate() -> None:
    state = hypothesis_state_from_gc_context(
        {
            "primary_item_id": 8,
            "related_item_ids": [22, 45, 14],
            "summary": "Remote income opportunity has enough nearby support.",
            "freshness": "recent",
            "known_gaps": [],
        }
    )
    open_payload = state.model_dump(mode="python")
    open_payload["state"] = "open"
    open_payload["next_probe"] = "gather_related_context"
    open_payload["confidence"] = 0.0

    transitioned = transition_state(type(state).model_validate(open_payload))

    assert transitioned.state == "sufficient"
    assert transitioned.next_probe == "package_case"
