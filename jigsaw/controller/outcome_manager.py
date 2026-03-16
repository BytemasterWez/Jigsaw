from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from jsonschema import Draft202012Validator
from pydantic import BaseModel, Field

from .action_manager import ActionRecordV1, validate_action_record_v1
from .case_manager import CaseStateV1, validate_case_state_v1


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTCOME_EVENT_SCHEMA_PATH = REPO_ROOT / "contracts" / "outcome_event" / "v1.json"

ObservedOutcomeValue = Literal["confirmed", "strengthened", "unchanged", "weakened", "invalidated"]
RecordedByValue = Literal["human", "system", "unknown"]


class OutcomeEventV1(BaseModel):
    contract: str = "outcome_event"
    version: str = "v1"
    event_id: str
    case_id: str
    action_id: str
    observed_outcome: ObservedOutcomeValue
    recorded_by: RecordedByValue
    timestamp: str
    effect_on_confidence: float = Field(ge=-1, le=1)
    notes: str = ""


def _load_schema(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_outcome_event_v1(payload: dict[str, Any]) -> OutcomeEventV1:
    Draft202012Validator(_load_schema(OUTCOME_EVENT_SCHEMA_PATH)).validate(payload)
    return OutcomeEventV1.model_validate(payload)


def build_outcome_event(
    case_state: CaseStateV1 | dict[str, Any],
    action_record: ActionRecordV1 | dict[str, Any],
    observed_outcome: ObservedOutcomeValue,
    effect_on_confidence: float,
    *,
    recorded_by: RecordedByValue = "human",
    timestamp: str,
    notes: str = "",
    event_id: str | None = None,
) -> OutcomeEventV1:
    state = case_state if isinstance(case_state, CaseStateV1) else validate_case_state_v1(case_state)
    action = action_record if isinstance(action_record, ActionRecordV1) else validate_action_record_v1(action_record)
    if action.case_id != state.case_id:
        raise ValueError("action_record.case_id must match case_state.case_id")

    record_event_id = event_id or f"outcome:{action.action_id}"
    payload = {
        "contract": "outcome_event",
        "version": "v1",
        "event_id": record_event_id,
        "case_id": state.case_id,
        "action_id": action.action_id,
        "observed_outcome": observed_outcome,
        "recorded_by": recorded_by,
        "timestamp": timestamp,
        "effect_on_confidence": effect_on_confidence,
        "notes": notes,
    }
    return validate_outcome_event_v1(payload)
