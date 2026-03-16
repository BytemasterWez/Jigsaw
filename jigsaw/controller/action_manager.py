from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from jsonschema import Draft202012Validator
from pydantic import BaseModel

from .case_manager import CaseStateV1, validate_case_state_v1


REPO_ROOT = Path(__file__).resolve().parents[2]
ACTION_RECORD_SCHEMA_PATH = REPO_ROOT / "contracts" / "action_record" / "v1.json"

RecommendedActionValue = Literal["prioritise_for_review", "hold_for_recheck", "defer", "no_action"]
ActionTakenValue = Literal["reviewed", "deferred", "ignored", "followed_up", "no_action_taken"]
TakenByValue = Literal["human", "system", "unknown"]


class ActionRecordV1(BaseModel):
    contract: str = "action_record"
    version: str = "v1"
    action_id: str
    case_id: str
    recommended_action: RecommendedActionValue
    action_taken: ActionTakenValue
    taken_by: TakenByValue
    timestamp: str
    notes: str = ""


def _load_schema(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_action_record_v1(payload: dict[str, Any]) -> ActionRecordV1:
    Draft202012Validator(_load_schema(ACTION_RECORD_SCHEMA_PATH)).validate(payload)
    return ActionRecordV1.model_validate(payload)


def _recommended_action_from_arbiter(arbiter_response: dict[str, Any]) -> RecommendedActionValue:
    recommended_action = str(arbiter_response.get("recommended_action", "no_action"))
    if recommended_action not in {"prioritise_for_review", "hold_for_recheck", "defer", "no_action"}:
        return "no_action"
    return recommended_action  # type: ignore[return-value]


def build_action_record(
    case_state: CaseStateV1 | dict[str, Any],
    arbiter_response: dict[str, Any],
    action_taken: ActionTakenValue,
    *,
    taken_by: TakenByValue = "human",
    timestamp: str,
    notes: str = "",
    action_id: str | None = None,
) -> ActionRecordV1:
    state = case_state if isinstance(case_state, CaseStateV1) else validate_case_state_v1(case_state)
    recommended_action = _recommended_action_from_arbiter(arbiter_response)
    record_action_id = action_id or f"action:{state.case_id}:{state.revision_count}"

    payload = {
        "contract": "action_record",
        "version": "v1",
        "action_id": record_action_id,
        "case_id": state.case_id,
        "recommended_action": recommended_action,
        "action_taken": action_taken,
        "taken_by": taken_by,
        "timestamp": timestamp,
        "notes": notes,
    }
    return validate_action_record_v1(payload)


def build_manual_review_action_record(
    case_state: CaseStateV1 | dict[str, Any],
    *,
    timestamp: str,
    taken_by: TakenByValue = "human",
    notes: str = "",
    action_id: str | None = None,
) -> ActionRecordV1:
    state = case_state if isinstance(case_state, CaseStateV1) else validate_case_state_v1(case_state)
    record_action_id = action_id or f"action:{state.case_id}:manual-review:{state.revision_count + 1}"
    recommended_action: RecommendedActionValue = "hold_for_recheck" if state.reopen_required else "no_action"

    payload = {
        "contract": "action_record",
        "version": "v1",
        "action_id": record_action_id,
        "case_id": state.case_id,
        "recommended_action": recommended_action,
        "action_taken": "reviewed",
        "taken_by": taken_by,
        "timestamp": timestamp,
        "notes": notes,
    }
    return validate_action_record_v1(payload)
