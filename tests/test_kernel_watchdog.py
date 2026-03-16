from __future__ import annotations

import json
from pathlib import Path

from jigsaw.engines.exchange_manager import validate_kernel_exchange_v1
from jigsaw.engines.watchdog import inspect_kernel_exchange, validate_kernel_watchdog_result_v1


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "examples" / "inputs"
GENERATED_AT = "2026-03-16T15:30:00Z"


def _valid_exchange_payload(*, engine_mode: str = "deterministic") -> dict[str, object]:
    with (FIXTURES_DIR / "sample_kernel_input.json").open("r", encoding="utf-8") as handle:
        input_packet = json.load(handle)
    return {
        "contract": "kernel_exchange",
        "version": "v1",
        "exchange_id": "kx:test:observed_state",
        "kernel_name": "observed_state",
        "engine_mode": engine_mode,
        "case_id": "case:hyp:gc:8",
        "input_packet": input_packet,
        "output_packet": {
            "contract": "kernel_output",
            "version": "v1",
            "output_id": "ko:test:observed_state",
            "kernel_name": "observed_state",
            "subject_id": "case:hyp:gc:8",
            "judgment": "observed_state_clear",
            "confidence": 0.8,
            "reasoning": "Sufficient observed coverage.",
            "evidence_refs": ["gc_ev_8"],
            "generated_at": GENERATED_AT,
        },
        "validation_passed": True,
        "engine_metadata": {"model": "fake-model", "retries_used": 0} if engine_mode == "lmstudio" else {},
        "timestamp": GENERATED_AT,
    }


def test_watchdog_passes_valid_exchange() -> None:
    exchange = validate_kernel_exchange_v1(_valid_exchange_payload())

    result = inspect_kernel_exchange(
        exchange,
        expected_kernel_name="observed_state",
        expected_engine_mode="deterministic",
    )

    assert result.verdict == "pass"
    assert result.reasons == []


def test_watchdog_fails_when_validation_failed() -> None:
    payload = _valid_exchange_payload()
    payload["validation_passed"] = False
    exchange = validate_kernel_exchange_v1(payload)

    result = inspect_kernel_exchange(exchange, expected_engine_mode="deterministic")

    assert result.verdict == "fail"
    assert "kernel_output_validation_failed" in result.reasons


def test_watchdog_fails_on_missing_required_fields() -> None:
    payload = _valid_exchange_payload()
    payload.pop("output_packet")

    result = inspect_kernel_exchange(payload, expected_engine_mode="deterministic")
    validated = validate_kernel_watchdog_result_v1(result.model_dump(mode="python"))

    assert validated.verdict == "fail"
    assert any(reason.startswith("missing_required_fields:") for reason in validated.reasons)


def test_watchdog_warns_when_lm_exchange_lacks_engine_metadata() -> None:
    payload = _valid_exchange_payload(engine_mode="lmstudio")
    payload["engine_metadata"] = {}
    exchange = validate_kernel_exchange_v1(payload)

    result = inspect_kernel_exchange(
        exchange,
        expected_kernel_name="observed_state",
        expected_engine_mode="lmstudio",
    )

    assert result.verdict == "warn"
    assert "missing_engine_metadata_for_lm_mode" in result.reasons
