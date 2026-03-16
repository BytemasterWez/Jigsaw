from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from jsonschema import Draft202012Validator
from pydantic import BaseModel, Field

from .hypothesis_controller import CaseInputV1, GCContextSnapshotV1, validate_case_input_v1, validate_gc_context_snapshot_v1


REPO_ROOT = Path(__file__).resolve().parents[2]
CASE_STATE_SCHEMA_PATH = REPO_ROOT / "contracts" / "case_state" / "v1.json"

CaseStatusValue = Literal["open", "watching", "promoted", "rejected", "closed"]
DecisionValue = Literal["promoted", "watchlist", "rejected"]
ConfidenceTrajectoryValue = Literal["up", "down", "flat", "stale"]


class CaseStateV1(BaseModel):
    contract: str = "case_state"
    version: str = "v1"
    case_id: str
    hypothesis_id: str
    current_status: CaseStatusValue
    latest_decision: DecisionValue
    latest_snapshot_id: str
    confidence_current: float = Field(ge=0, le=1)
    confidence_trajectory: ConfidenceTrajectoryValue
    last_reviewed_at: str
    reopen_conditions: list[str] = Field(default_factory=list)
    revision_count: int = Field(ge=0)


def _load_schema(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_case_state_v1(payload: dict[str, Any]) -> CaseStateV1:
    Draft202012Validator(_load_schema(CASE_STATE_SCHEMA_PATH)).validate(payload)
    return CaseStateV1.model_validate(payload)


def _status_from_decision(decision: str) -> CaseStatusValue:
    if decision == "promoted":
        return "promoted"
    if decision == "watchlist":
        return "watching"
    if decision == "rejected":
        return "rejected"
    raise ValueError(f"Unsupported latest_decision for case_state: {decision}")


def _reopen_conditions_for_decision(decision: str) -> list[str]:
    if decision == "promoted":
        return ["record_action_outcome", "review_if_stale"]
    if decision == "watchlist":
        return ["reopen_on_new_evidence", "review_if_stale"]
    if decision == "rejected":
        return ["reopen_on_stronger_evidence"]
    return []


def _trajectory(previous_confidence: float | None, current_confidence: float) -> ConfidenceTrajectoryValue:
    if previous_confidence is None:
        return "stale"
    delta = round(current_confidence - previous_confidence, 4)
    if delta > 0.02:
        return "up"
    if delta < -0.02:
        return "down"
    return "flat"


def build_case_state(
    case_input: CaseInputV1 | dict[str, Any],
    gc_context: GCContextSnapshotV1 | dict[str, Any],
    arbiter_response: dict[str, Any],
    *,
    reviewed_at: str,
) -> CaseStateV1:
    case = case_input if isinstance(case_input, CaseInputV1) else validate_case_input_v1(case_input)
    snapshot = gc_context if isinstance(gc_context, GCContextSnapshotV1) else validate_gc_context_snapshot_v1(gc_context)
    latest_decision = str(arbiter_response["judgement"])
    confidence_current = float(arbiter_response["confidence"])

    payload = {
        "contract": "case_state",
        "version": "v1",
        "case_id": case.case_id,
        "hypothesis_id": case.hypothesis_id,
        "current_status": _status_from_decision(latest_decision),
        "latest_decision": latest_decision,
        "latest_snapshot_id": snapshot.snapshot_id,
        "confidence_current": confidence_current,
        "confidence_trajectory": _trajectory(None, confidence_current),
        "last_reviewed_at": reviewed_at,
        "reopen_conditions": _reopen_conditions_for_decision(latest_decision),
        "revision_count": 1,
    }
    return validate_case_state_v1(payload)


def update_case_state(
    existing_state: CaseStateV1 | dict[str, Any],
    *,
    arbiter_response: dict[str, Any],
    snapshot_id: str,
    reviewed_at: str,
) -> CaseStateV1:
    state = existing_state if isinstance(existing_state, CaseStateV1) else validate_case_state_v1(existing_state)
    latest_decision = str(arbiter_response["judgement"])
    confidence_current = float(arbiter_response["confidence"])

    payload = state.model_dump(mode="python")
    payload["current_status"] = _status_from_decision(latest_decision)
    payload["latest_decision"] = latest_decision
    payload["latest_snapshot_id"] = snapshot_id
    payload["confidence_current"] = confidence_current
    payload["confidence_trajectory"] = _trajectory(state.confidence_current, confidence_current)
    payload["last_reviewed_at"] = reviewed_at
    payload["reopen_conditions"] = _reopen_conditions_for_decision(latest_decision)
    payload["revision_count"] = state.revision_count + 1
    return validate_case_state_v1(payload)
