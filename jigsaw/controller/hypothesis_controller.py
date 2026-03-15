from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from jsonschema import Draft202012Validator
from pydantic import BaseModel, Field


REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "contracts" / "hypothesis_state" / "v1.json"

HypothesisStateValue = Literal["open", "gathering_evidence", "conflicted", "sufficient", "escalate", "closed"]


class HypothesisStateV1(BaseModel):
    contract: str = "hypothesis_state"
    version: str = "v1"
    hypothesis_id: str
    question_or_claim: str
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    conflicting_evidence_ids: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    state: HypothesisStateValue
    next_probe: str


def _load_schema() -> dict[str, Any]:
    with SCHEMA_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_hypothesis_state_v1(payload: dict[str, Any]) -> HypothesisStateV1:
    Draft202012Validator(_load_schema()).validate(payload)
    return HypothesisStateV1.model_validate(payload)


def _supporting_evidence_ids(primary_item_id: int | str, related_item_ids: list[int | str]) -> list[str]:
    supporting = [f"gc:item:{primary_item_id}"]
    supporting.extend(f"gc:item:{item_id}" for item_id in related_item_ids)
    return supporting


def _conflicting_evidence_ids(conflicting_item_ids: list[int | str] | None) -> list[str]:
    if not conflicting_item_ids:
        return []
    return [f"gc:item:{item_id}" for item_id in conflicting_item_ids]


def _state_from_context(
    *,
    supporting_count: int,
    conflicting_count: int,
    known_gaps: list[str],
    freshness: str,
) -> tuple[HypothesisStateValue, float, str]:
    freshness_value = freshness.strip().lower()
    if conflicting_count > 0:
        return ("conflicted", 0.4, "Review conflicting evidence before packaging this branch.")
    if supporting_count >= 3 and not known_gaps and freshness_value in {"fresh", "recent"}:
        return ("sufficient", 0.78, "Package this branch into a bounded Jigsaw case.")
    return ("gathering_evidence", 0.46, "Fetch more related context from Garbage Collector.")


def hypothesis_state_from_gc_context(
    gc_context: dict[str, Any],
    *,
    hypothesis_id: str | None = None,
    question_or_claim: str | None = None,
) -> HypothesisStateV1:
    primary_item_id = gc_context["primary_item_id"]
    related_item_ids = list(gc_context.get("related_item_ids", []))
    known_gaps = list(gc_context.get("known_gaps", []))
    conflicting_item_ids = list(gc_context.get("conflicting_item_ids", []))
    freshness = str(gc_context.get("freshness", "stale"))
    question = question_or_claim or gc_context.get("question_or_claim") or gc_context.get("summary") or f"Assess item {primary_item_id}"

    state, confidence, next_probe = _state_from_context(
        supporting_count=1 + len(related_item_ids),
        conflicting_count=len(conflicting_item_ids),
        known_gaps=known_gaps,
        freshness=freshness,
    )

    payload = {
        "contract": "hypothesis_state",
        "version": "v1",
        "hypothesis_id": hypothesis_id or f"hyp:gc:{primary_item_id}",
        "question_or_claim": question,
        "supporting_evidence_ids": _supporting_evidence_ids(primary_item_id, related_item_ids),
        "conflicting_evidence_ids": _conflicting_evidence_ids(conflicting_item_ids),
        "missing_evidence": known_gaps,
        "confidence": confidence,
        "state": state,
        "next_probe": next_probe,
    }
    return validate_hypothesis_state_v1(payload)


def refresh_hypothesis_state(
    state: HypothesisStateV1,
    *,
    gc_context: dict[str, Any],
) -> HypothesisStateV1:
    refreshed = hypothesis_state_from_gc_context(
        gc_context,
        hypothesis_id=state.hypothesis_id,
        question_or_claim=state.question_or_claim,
    )
    return refreshed
