from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from jsonschema import Draft202012Validator
from pydantic import BaseModel

from jigsaw.engines.watchdog import KernelWatchdogResultV1, validate_kernel_watchdog_result_v1


REPO_ROOT = Path(__file__).resolve().parents[2]
WATCHDOG_POLICY_SCHEMA_PATH = REPO_ROOT / "contracts" / "watchdog_policy" / "v1.json"
WATCHDOG_POLICY_DECISION_SCHEMA_PATH = REPO_ROOT / "contracts" / "watchdog_policy_decision" / "v1.json"

WatchdogActionValue = Literal["allow", "allow_with_review", "block_case"]
WatchdogVerdictValue = Literal["pass", "warn", "fail"]


class WatchdogPolicyV1(BaseModel):
    contract: str = "watchdog_policy"
    version: str = "v1"
    policy_id: str
    scope: Literal["kernel_exchange"] = "kernel_exchange"
    pass_action: Literal["allow"] = "allow"
    warn_action: Literal["allow_with_review"] = "allow_with_review"
    fail_action: Literal["block_case"] = "block_case"


class WatchdogPolicyDecisionV1(BaseModel):
    contract: str = "watchdog_policy_decision"
    version: str = "v1"
    decision_id: str
    policy_id: str
    case_id: str
    scope: Literal["kernel_exchange"] = "kernel_exchange"
    action: WatchdogActionValue
    highest_verdict: WatchdogVerdictValue
    blocked: bool
    reasons: list[str]
    exchange_ids: list[str]
    timestamp: str


def _load_schema(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_watchdog_policy_v1(payload: dict[str, Any]) -> WatchdogPolicyV1:
    Draft202012Validator(_load_schema(WATCHDOG_POLICY_SCHEMA_PATH)).validate(payload)
    return WatchdogPolicyV1.model_validate(payload)


def validate_watchdog_policy_decision_v1(payload: dict[str, Any]) -> WatchdogPolicyDecisionV1:
    Draft202012Validator(_load_schema(WATCHDOG_POLICY_DECISION_SCHEMA_PATH)).validate(payload)
    return WatchdogPolicyDecisionV1.model_validate(payload)


def default_watchdog_policy() -> WatchdogPolicyV1:
    return validate_watchdog_policy_v1(
        {
            "contract": "watchdog_policy",
            "version": "v1",
            "policy_id": "watchdog-policy:kernel:v1",
            "scope": "kernel_exchange",
            "pass_action": "allow",
            "warn_action": "allow_with_review",
            "fail_action": "block_case",
        }
    )


def evaluate_watchdog_policy(
    watchdog_results: list[KernelWatchdogResultV1 | dict[str, Any]],
    *,
    case_id: str,
    timestamp: str,
    policy: WatchdogPolicyV1 | dict[str, Any] | None = None,
) -> WatchdogPolicyDecisionV1:
    resolved_policy = (
        policy
        if isinstance(policy, WatchdogPolicyV1)
        else validate_watchdog_policy_v1(policy) if isinstance(policy, dict) else default_watchdog_policy()
    )
    normalized_results = [
        result if isinstance(result, KernelWatchdogResultV1) else validate_kernel_watchdog_result_v1(result)
        for result in watchdog_results
    ]

    highest_verdict: WatchdogVerdictValue = "pass"
    action: WatchdogActionValue = resolved_policy.pass_action
    reasons: list[str] = []

    if any(result.verdict == "fail" for result in normalized_results):
        highest_verdict = "fail"
        action = resolved_policy.fail_action
    elif any(result.verdict == "warn" for result in normalized_results):
        highest_verdict = "warn"
        action = resolved_policy.warn_action

    for result in normalized_results:
        reasons.extend(f"{result.kernel_name}:{reason}" for reason in result.reasons)

    return validate_watchdog_policy_decision_v1(
        {
            "contract": "watchdog_policy_decision",
            "version": "v1",
            "decision_id": f"wpd:{case_id}:{timestamp}",
            "policy_id": resolved_policy.policy_id,
            "case_id": case_id,
            "scope": resolved_policy.scope,
            "action": action,
            "highest_verdict": highest_verdict,
            "blocked": action == "block_case",
            "reasons": reasons,
            "exchange_ids": [result.exchange_id for result in normalized_results],
            "timestamp": timestamp,
        }
    )
