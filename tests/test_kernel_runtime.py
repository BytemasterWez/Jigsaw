from __future__ import annotations

import json
from pathlib import Path

import jigsaw.engines.kernel_runtime as kernel_runtime
from jigsaw.engines.result_types import KernelRunResult
from jigsaw.lanes.kernel_lane.compose import compose_kernel_bundle
from jigsaw.lanes.kernel_lane.kernels import run_expected_state, run_observed_state
from jigsaw.lanes.kernel_lane.models import KernelInputV1
from jigsaw.lanes.kernel_lane.validators import (
    validate_kernel_bundle_result_v1,
    validate_kernel_input_v1,
)


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "examples" / "inputs"
PIPELINE_RUN_ID = "kernel-runtime-test"
GENERATED_AT = "2026-03-15T15:00:00Z"


def _load_example_input() -> KernelInputV1:
    with (FIXTURES_DIR / "sample_kernel_input.json").open("r", encoding="utf-8") as handle:
        return validate_kernel_input_v1(json.load(handle))


def test_runtime_resolves_deterministic_observed_state() -> None:
    payload = _load_example_input()
    result = kernel_runtime.run_kernel(
        "observed_state",
        "deterministic",
        payload,
        pipeline_run_id=PIPELINE_RUN_ID,
        generated_at=GENERATED_AT,
    )

    assert result.engine_mode == "deterministic"
    assert result.validated_output.kernel_type == "observed_state"
    assert result.validated_output.judgment == "observed_state_partial"


def test_runtime_resolves_deterministic_expected_state() -> None:
    payload = _load_example_input()
    result = kernel_runtime.run_kernel(
        "expected_state",
        "deterministic",
        payload,
        pipeline_run_id=PIPELINE_RUN_ID,
        generated_at=GENERATED_AT,
    )

    assert result.engine_mode == "deterministic"
    assert result.validated_output.kernel_type == "expected_state"
    assert result.validated_output.judgment == "expected_state_partial"


def test_runtime_resolves_deterministic_contradiction() -> None:
    payload = _load_example_input()
    result = kernel_runtime.run_kernel(
        "contradiction",
        "deterministic",
        payload,
        pipeline_run_id=PIPELINE_RUN_ID,
        generated_at=GENERATED_AT,
    )

    assert result.engine_mode == "deterministic"
    assert result.validated_output.kernel_type == "contradiction"
    assert result.validated_output.judgment == "contradiction_detected"


def test_profile_engine_selection_is_honored(monkeypatch) -> None:
    payload = _load_example_input()
    seen: dict[str, object] = {}

    def fake_lmstudio_observed(
        case_input: KernelInputV1,
        *,
        pipeline_run_id: str,
        generated_at: str,
        config: dict[str, object] | None = None,
        context: dict[str, object] | None = None,
    ) -> KernelRunResult:
        seen["config"] = config or {}
        output = run_observed_state(case_input, pipeline_run_id=pipeline_run_id, generated_at=generated_at)
        return KernelRunResult(
            kernel_name="observed_state",
            engine_mode="lmstudio",
            validated_output=output,
            model_name="fake-model",
        )

    monkeypatch.setitem(kernel_runtime.KERNEL_REGISTRY, ("observed_state", "lmstudio"), fake_lmstudio_observed)
    profile = {
        "profile_name": "runtime_test_profile",
        "kernel_engines": {"observed_state": "lmstudio"},
        "engine": {"lmstudio": {"model": "fake-model", "max_retries": 1}},
    }

    result = kernel_runtime.run_kernel_for_profile(
        "observed_state",
        payload,
        profile,
        pipeline_run_id=PIPELINE_RUN_ID,
        generated_at=GENERATED_AT,
    )

    assert result.engine_mode == "lmstudio"
    assert seen["config"] == {"model": "fake-model", "max_retries": 1}


def test_mixed_bundle_can_run_through_runtime(monkeypatch) -> None:
    payload = _load_example_input()

    def fake_lmstudio_observed(
        case_input: KernelInputV1,
        *,
        pipeline_run_id: str,
        generated_at: str,
        config: dict[str, object] | None = None,
        context: dict[str, object] | None = None,
    ) -> KernelRunResult:
        output = run_observed_state(case_input, pipeline_run_id=pipeline_run_id, generated_at=generated_at)
        return KernelRunResult(
            kernel_name="observed_state",
            engine_mode="lmstudio",
            validated_output=output,
            model_name="fake-observed-model",
        )

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
            model_name="fake-expected-model",
        )

    monkeypatch.setitem(kernel_runtime.KERNEL_REGISTRY, ("observed_state", "lmstudio"), fake_lmstudio_observed)
    monkeypatch.setitem(kernel_runtime.KERNEL_REGISTRY, ("expected_state", "lmstudio"), fake_lmstudio_expected)

    observed = kernel_runtime.run_kernel(
        "observed_state",
        "lmstudio",
        payload,
        pipeline_run_id=PIPELINE_RUN_ID,
        generated_at=GENERATED_AT,
        config={"max_retries": 1},
    )
    expected = kernel_runtime.run_kernel(
        "expected_state",
        "lmstudio",
        payload,
        pipeline_run_id=PIPELINE_RUN_ID,
        generated_at=GENERATED_AT,
        config={"max_retries": 1},
    )
    contradiction = kernel_runtime.run_kernel(
        "contradiction",
        "deterministic",
        payload,
        pipeline_run_id=PIPELINE_RUN_ID,
        generated_at=GENERATED_AT,
    )

    bundle = compose_kernel_bundle(
        payload,
        [observed.validated_output, expected.validated_output, contradiction.validated_output],
        pipeline_run_id=PIPELINE_RUN_ID,
        generated_at=GENERATED_AT,
    )
    validated_bundle = validate_kernel_bundle_result_v1(bundle.model_dump(mode="python"))

    assert observed.engine_mode == "lmstudio"
    assert expected.engine_mode == "lmstudio"
    assert contradiction.engine_mode == "deterministic"
    assert validated_bundle.composed_summary.bundle_judgment == "contradictory"
