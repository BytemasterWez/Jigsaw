from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from jsonschema import Draft202012Validator
from pydantic import BaseModel

from .case_manager import CaseStateV1, validate_case_state_v1


REPO_ROOT = Path(__file__).resolve().parents[2]
WATCHDOG_OVERRIDE_RECORD_SCHEMA_PATH = REPO_ROOT / "contracts" / "watchdog_override_record" / "v1.json"

WatchdogVerdictValue = Literal["warn", "fail"]
WatchdogOperatorDecisionValue = Literal["override_and_continue", "close_as_invalid", "defer_for_manual_review"]


class WatchdogOverrideRecordV1(BaseModel):
    contract: str = "watchdog_override_record"
    version: str = "v1"
    override_id: str
    case_id: str
    exchange_id: str
    watchdog_verdict: WatchdogVerdictValue
    operator_decision: WatchdogOperatorDecisionValue
    override_reason: str
    overridden_by: str
    timestamp: str


def _load_schema(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_watchdog_override_record_v1(payload: dict[str, Any]) -> WatchdogOverrideRecordV1:
    Draft202012Validator(_load_schema(WATCHDOG_OVERRIDE_RECORD_SCHEMA_PATH)).validate(payload)
    return WatchdogOverrideRecordV1.model_validate(payload)


def build_watchdog_override_record(
    case_state: CaseStateV1 | dict[str, Any],
    *,
    exchange_id: str,
    watchdog_verdict: WatchdogVerdictValue,
    operator_decision: WatchdogOperatorDecisionValue,
    override_reason: str,
    overridden_by: str,
    timestamp: str,
    override_id: str | None = None,
) -> WatchdogOverrideRecordV1:
    state = case_state if isinstance(case_state, CaseStateV1) else validate_case_state_v1(case_state)
    record_override_id = override_id or f"wov:{state.case_id}:{state.revision_count + 1}"
    return validate_watchdog_override_record_v1(
        {
            "contract": "watchdog_override_record",
            "version": "v1",
            "override_id": record_override_id,
            "case_id": state.case_id,
            "exchange_id": exchange_id,
            "watchdog_verdict": watchdog_verdict,
            "operator_decision": operator_decision,
            "override_reason": override_reason,
            "overridden_by": overridden_by,
            "timestamp": timestamp,
        }
    )


def apply_watchdog_override(
    case_state: CaseStateV1 | dict[str, Any],
    override_record: WatchdogOverrideRecordV1 | dict[str, Any],
) -> CaseStateV1:
    state = case_state if isinstance(case_state, CaseStateV1) else validate_case_state_v1(case_state)
    record = (
        override_record
        if isinstance(override_record, WatchdogOverrideRecordV1)
        else validate_watchdog_override_record_v1(override_record)
    )
    if record.case_id != state.case_id:
        raise ValueError("watchdog_override_record.case_id must match case_state.case_id")

    payload = state.model_dump(mode="python")
    payload["last_reviewed_at"] = record.timestamp
    payload["revision_count"] = state.revision_count + 1

    if record.operator_decision == "override_and_continue":
        payload["current_status"] = "watching"
        payload["reopen_required"] = False
        payload["latest_reopen_reason"] = "watchdog_override_continue"
        payload["reopen_conditions"] = []
    elif record.operator_decision == "close_as_invalid":
        payload["current_status"] = "closed"
        payload["reopen_required"] = False
        payload["latest_reopen_reason"] = "watchdog_closed_invalid"
        payload["reopen_conditions"] = []
    else:
        payload["current_status"] = "watching"
        payload["reopen_required"] = True
        payload["latest_reopen_reason"] = "watchdog_manual_review_deferred"
        payload["reopen_conditions"] = ["manual_watchdog_review"]

    return validate_case_state_v1(payload)
