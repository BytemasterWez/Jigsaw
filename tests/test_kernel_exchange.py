from __future__ import annotations

import json
from pathlib import Path

import pytest

import jigsaw.engines.kernel_runtime as kernel_runtime
from jigsaw.engines.exchange_manager import build_kernel_exchange, validate_kernel_exchange_v1
from jigsaw.engines.result_types import KernelRunResult
from jigsaw.lanes.kernel_lane.kernels import run_expected_state, run_observed_state
from jigsaw.lanes.kernel_lane.models import KernelInputV1
from jigsaw.lanes.kernel_lane.validators import validate_kernel_input_v1


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "examples" / "inputs"
PIPELINE_RUN_ID = "kernel-exchange-test"
GENERATED_AT = "2026-03-16T15:00:00Z"


def _load_example_input() -> KernelInputV1:
    with (FIXTURES_DIR / "sample_kernel_input.json").open("r", encoding="utf-8") as handle:
        return validate_kernel_input_v1(json.load(handle))


def test_runtime_emits_kernel_exchange_for_deterministic_kernel() -> None:
    payload = _load_example_input()
    result = kernel_runtime.run_kernel(
        "observed_state",
        "deterministic",
        payload,
        pipeline_run_id=PIPELINE_RUN_ID,
        generated_at=GENERATED_AT,
    )

    assert result.kernel_exchange is not None
    assert result.kernel_exchange.kernel_name == "observed_state"
    assert result.kernel_exchange.engine_mode == "deterministic"
    assert result.kernel_exchange.validation_passed is True


def test_runtime_emits_kernel_exchange_for_lm_backed_kernel(monkeypatch) -> None:
    payload = _load_example_input()

    def fake_lmstudio_expected(
        case_input: KernelInputV1,
        *,
        pipeline_run_id: str,
        generated_at: str,
        config: dict[str, object] | None = None,
        context: dict[str, object] | None = None,
    ) -> KernelRunResult:
        output = run_expected_state(case_input, pipeline_run_id=pipeline_run_id, generated_at=generated_at)
        return KernelRunResult(
            kernel_name="expected_state",
            engine_mode="lmstudio",
            validated_output=output,
            model_name="fake-lm-model",
            retries_used=0,
        )

    monkeypatch.setitem(kernel_runtime.KERNEL_REGISTRY, ("expected_state", "lmstudio"), fake_lmstudio_expected)
    result = kernel_runtime.run_kernel(
        "expected_state",
        "lmstudio",
        payload,
        pipeline_run_id=PIPELINE_RUN_ID,
        generated_at=GENERATED_AT,
    )

    assert result.kernel_exchange is not None
    assert result.kernel_exchange.engine_mode == "lmstudio"
    assert result.kernel_exchange.engine_metadata["model"] == "fake-lm-model"
    assert result.kernel_exchange.engine_metadata["retries_used"] == 0


def test_runtime_emits_failed_exchange_when_validation_fails(monkeypatch) -> None:
    payload = _load_example_input()

    def fake_invalid_observed(
        case_input: KernelInputV1,
        *,
        pipeline_run_id: str,
        generated_at: str,
        config: dict[str, object] | None = None,
        context: dict[str, object] | None = None,
    ) -> KernelRunResult:
        output = run_observed_state(case_input, pipeline_run_id=pipeline_run_id, generated_at=generated_at)
        invalid_output = output.model_dump(mode="python")
        invalid_output.pop("judgment")
        return KernelRunResult(
            kernel_name="observed_state",
            engine_mode="deterministic",
            validated_output=invalid_output,  # type: ignore[arg-type]
        )

    monkeypatch.setitem(kernel_runtime.KERNEL_REGISTRY, ("observed_state", "deterministic"), fake_invalid_observed)
    with pytest.raises(kernel_runtime.KernelRuntimeError) as exc_info:
        kernel_runtime.run_kernel(
            "observed_state",
            "deterministic",
            payload,
            pipeline_run_id=PIPELINE_RUN_ID,
            generated_at=GENERATED_AT,
        )

    exchange = exc_info.value.kernel_exchange
    assert exchange is not None
    assert exchange["validation_passed"] is False
    assert exchange["kernel_name"] == "observed_state"


def test_validate_kernel_exchange_v1_accepts_explicit_payload() -> None:
    exchange = validate_kernel_exchange_v1(
        {
            "contract": "kernel_exchange",
            "version": "v1",
            "exchange_id": "kx:test:observed_state",
            "kernel_name": "observed_state",
            "engine_mode": "lmstudio",
            "case_id": "case:hyp:gc:8",
            "input_packet": {"contract": "kernel_input"},
            "output_packet": {"contract": "kernel_output"},
            "validation_passed": True,
            "engine_metadata": {"model": "fake-model", "retries_used": 0},
            "timestamp": GENERATED_AT,
        }
    )

    assert exchange.engine_mode == "lmstudio"
    assert exchange.engine_metadata["model"] == "fake-model"
