from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from jsonschema import Draft202012Validator
from pydantic import BaseModel, Field


REPO_ROOT = Path(__file__).resolve().parents[2]
HYPOTHESIS_SCHEMA_PATH = REPO_ROOT / "contracts" / "hypothesis_state" / "v1.json"
CASE_INPUT_SCHEMA_PATH = REPO_ROOT / "contracts" / "case_input" / "v1.json"

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


class CaseInputV1(BaseModel):
    contract: str = "case_input"
    version: str = "v1"
    case_id: str
    hypothesis_id: str
    question_or_claim: str
    primary_evidence_ids: list[str] = Field(default_factory=list)
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    conflicting_evidence_ids: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    current_confidence: float = Field(ge=0, le=1)
    reason_for_packaging: str


def _load_schema(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_hypothesis_state_v1(payload: dict[str, Any]) -> HypothesisStateV1:
    Draft202012Validator(_load_schema(HYPOTHESIS_SCHEMA_PATH)).validate(payload)
    return HypothesisStateV1.model_validate(payload)


def validate_case_input_v1(payload: dict[str, Any]) -> CaseInputV1:
    Draft202012Validator(_load_schema(CASE_INPUT_SCHEMA_PATH)).validate(payload)
    return CaseInputV1.model_validate(payload)


def _supporting_evidence_ids(primary_item_id: int | str, related_item_ids: list[int | str]) -> list[str]:
    supporting = [f"gc:item:{primary_item_id}"]
    supporting.extend(f"gc:item:{item_id}" for item_id in related_item_ids)
    return supporting


def _conflicting_evidence_ids(conflicting_item_ids: list[int | str] | None) -> list[str]:
    if not conflicting_item_ids:
        return []
    return [f"gc:item:{item_id}" for item_id in conflicting_item_ids]


def _transition_for_counts(
    *,
    supporting_count: int,
    conflicting_count: int,
    missing_evidence_count: int,
    freshness: str,
    minimum_supporting_evidence: int = 3,
    conflict_threshold: int = 1,
    escalate_if_gaps: bool = True,
) -> tuple[HypothesisStateValue, float]:
    freshness_value = freshness.strip().lower()
    if conflict_threshold > 0 and conflicting_count >= conflict_threshold:
        return ("conflicted", 0.4)
    if (
        supporting_count >= minimum_supporting_evidence
        and missing_evidence_count > 0
        and escalate_if_gaps
        and freshness_value in {"fresh", "recent"}
    ):
        return ("escalate", 0.64)
    if supporting_count >= minimum_supporting_evidence and freshness_value in {"fresh", "recent"}:
        return ("sufficient", 0.78)
    return ("gathering_evidence", 0.46)


def select_next_probe(hypothesis_state: HypothesisStateV1) -> str:
    if hypothesis_state.state == "conflicted":
        return "inspect_conflicts"
    if hypothesis_state.state == "sufficient":
        return "package_case"
    if hypothesis_state.state == "escalate":
        return "escalate"
    return "gather_related_context"


def transition_state(
    hypothesis_state: HypothesisStateV1,
    *,
    freshness: str = "recent",
    controller_config: dict[str, Any] | None = None,
) -> HypothesisStateV1:
    config = controller_config or {}
    state, confidence = _transition_for_counts(
        supporting_count=len(hypothesis_state.supporting_evidence_ids),
        conflicting_count=len(hypothesis_state.conflicting_evidence_ids),
        missing_evidence_count=len(hypothesis_state.missing_evidence),
        freshness=freshness,
        minimum_supporting_evidence=int(config.get("minimum_supporting_evidence", 3)),
        conflict_threshold=int(config.get("conflict_threshold", 1)),
        escalate_if_gaps=bool(config.get("escalate_if_gaps", True)),
    )
    payload = hypothesis_state.model_dump(mode="python")
    payload["state"] = state
    payload["confidence"] = confidence
    payload["next_probe"] = select_next_probe(HypothesisStateV1.model_validate({**payload, "state": state, "confidence": confidence}))
    return validate_hypothesis_state_v1(payload)


def hypothesis_state_from_gc_context(
    gc_context: dict[str, Any],
    *,
    hypothesis_id: str | None = None,
    question_or_claim: str | None = None,
    controller_config: dict[str, Any] | None = None,
) -> HypothesisStateV1:
    primary_item_id = gc_context["primary_item_id"]
    related_item_ids = list(gc_context.get("related_item_ids", []))
    known_gaps = list(gc_context.get("known_gaps", []))
    conflicting_item_ids = list(gc_context.get("conflicting_item_ids", []))
    question = question_or_claim or gc_context.get("question_or_claim") or gc_context.get("summary") or f"Assess item {primary_item_id}"

    payload = {
        "contract": "hypothesis_state",
        "version": "v1",
        "hypothesis_id": hypothesis_id or f"hyp:gc:{primary_item_id}",
        "question_or_claim": question,
        "supporting_evidence_ids": _supporting_evidence_ids(primary_item_id, related_item_ids),
        "conflicting_evidence_ids": _conflicting_evidence_ids(conflicting_item_ids),
        "missing_evidence": known_gaps,
        "confidence": 0.0,
        "state": "open",
        "next_probe": "gather_related_context",
    }
    return transition_state(
        validate_hypothesis_state_v1(payload),
        freshness=str(gc_context.get("freshness", "recent")),
        controller_config=controller_config,
    )


def refresh_hypothesis_state(
    state: HypothesisStateV1,
    *,
    gc_context: dict[str, Any],
    controller_config: dict[str, Any] | None = None,
) -> HypothesisStateV1:
    refreshed = hypothesis_state_from_gc_context(
        gc_context,
        hypothesis_id=state.hypothesis_id,
        question_or_claim=state.question_or_claim,
        controller_config=controller_config,
    )
    return refreshed


def build_case_input(hypothesis_state: HypothesisStateV1, gc_context: dict[str, Any]) -> CaseInputV1:
    if hypothesis_state.state != "sufficient" and hypothesis_state.next_probe != "package_case":
        raise ValueError("Hypothesis must be sufficient or explicitly marked for package_case before building case_input.")

    primary_item_id = gc_context["primary_item_id"]
    primary_evidence_id = f"gc:item:{primary_item_id}"
    supporting_evidence_ids = [evidence_id for evidence_id in hypothesis_state.supporting_evidence_ids if evidence_id != primary_evidence_id]

    payload = {
        "contract": "case_input",
        "version": "v1",
        "case_id": f"case:{hypothesis_state.hypothesis_id}",
        "hypothesis_id": hypothesis_state.hypothesis_id,
        "question_or_claim": hypothesis_state.question_or_claim,
        "primary_evidence_ids": [primary_evidence_id],
        "supporting_evidence_ids": supporting_evidence_ids,
        "conflicting_evidence_ids": hypothesis_state.conflicting_evidence_ids,
        "missing_evidence": hypothesis_state.missing_evidence,
        "current_confidence": hypothesis_state.confidence,
        "reason_for_packaging": "sufficient_support_low_conflict",
    }
    return validate_case_input_v1(payload)
