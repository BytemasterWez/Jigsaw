from __future__ import annotations

from jigsaw.engines.watchdog import validate_kernel_watchdog_result_v1
from jigsaw.engines.watchdog_policy import (
    default_watchdog_policy,
    evaluate_watchdog_policy,
    validate_watchdog_policy_decision_v1,
)


GENERATED_AT = "2026-03-16T16:00:00Z"


def _result(*, kernel_name: str, verdict: str, reasons: list[str] | None = None) -> dict[str, object]:
    return {
        "contract": "kernel_watchdog_result",
        "version": "v1",
        "watchdog_id": f"kw:kx:{kernel_name}",
        "exchange_id": f"kx:{kernel_name}",
        "kernel_name": kernel_name,
        "verdict": verdict,
        "reasons": reasons or [],
        "timestamp": GENERATED_AT,
    }


def test_watchdog_policy_allows_pass_results() -> None:
    decision = evaluate_watchdog_policy(
        [validate_kernel_watchdog_result_v1(_result(kernel_name="observed_state", verdict="pass"))],
        case_id="case:test:1",
        timestamp=GENERATED_AT,
        policy=default_watchdog_policy(),
    )

    assert decision.action == "allow"
    assert decision.blocked is False
    assert decision.highest_verdict == "pass"


def test_watchdog_policy_warns_without_blocking() -> None:
    decision = evaluate_watchdog_policy(
        [validate_kernel_watchdog_result_v1(_result(kernel_name="expected_state", verdict="warn", reasons=["metadata_missing"]))],
        case_id="case:test:2",
        timestamp=GENERATED_AT,
    )

    validated = validate_watchdog_policy_decision_v1(decision.model_dump(mode="python"))
    assert validated.action == "allow_with_review"
    assert validated.blocked is False
    assert validated.highest_verdict == "warn"
    assert validated.reasons == ["expected_state:metadata_missing"]


def test_watchdog_policy_blocks_fail_results() -> None:
    decision = evaluate_watchdog_policy(
        [
            validate_kernel_watchdog_result_v1(_result(kernel_name="observed_state", verdict="pass")),
            validate_kernel_watchdog_result_v1(
                _result(kernel_name="expected_state", verdict="fail", reasons=["engine_mode_mismatch"])
            ),
        ],
        case_id="case:test:3",
        timestamp=GENERATED_AT,
    )

    assert decision.action == "block_case"
    assert decision.blocked is True
    assert decision.highest_verdict == "fail"
    assert "expected_state:engine_mode_mismatch" in decision.reasons
