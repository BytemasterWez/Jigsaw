from __future__ import annotations

from collections.abc import Callable
from typing import Any

from jigsaw.engines.result_types import KernelRunResult
from jigsaw.lanes.kernel_lane.kernels import run_contradiction, run_expected_state, run_observed_state
from jigsaw.lanes.kernel_lane.lmstudio_client import LMStudioClient
from jigsaw.lanes.kernel_lane.lmstudio_expected_state import run_lmstudio_expected_state
from jigsaw.lanes.kernel_lane.lmstudio_observed_state import run_lmstudio_observed_state
from jigsaw.lanes.kernel_lane.models import KernelInputV1


KernelImplementation = Callable[..., KernelRunResult]


def _run_observed_state_deterministic(
    payload: KernelInputV1,
    *,
    pipeline_run_id: str,
    generated_at: str,
    config: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
) -> KernelRunResult:
    output = run_observed_state(payload, pipeline_run_id=pipeline_run_id, generated_at=generated_at)
    return KernelRunResult(
        kernel_name="observed_state",
        engine_mode="deterministic",
        validated_output=output,
    )


def _run_expected_state_deterministic(
    payload: KernelInputV1,
    *,
    pipeline_run_id: str,
    generated_at: str,
    config: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
) -> KernelRunResult:
    output = run_expected_state(payload, pipeline_run_id=pipeline_run_id, generated_at=generated_at)
    return KernelRunResult(
        kernel_name="expected_state",
        engine_mode="deterministic",
        validated_output=output,
    )


def _run_contradiction_deterministic(
    payload: KernelInputV1,
    *,
    pipeline_run_id: str,
    generated_at: str,
    config: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
) -> KernelRunResult:
    output = run_contradiction(payload, pipeline_run_id=pipeline_run_id, generated_at=generated_at)
    return KernelRunResult(
        kernel_name="contradiction",
        engine_mode="deterministic",
        validated_output=output,
    )


def _run_observed_state_lmstudio(
    payload: KernelInputV1,
    *,
    pipeline_run_id: str,
    generated_at: str,
    config: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
) -> KernelRunResult:
    config = config or {}
    client = LMStudioClient(
        base_url=config.get("base_url"),
        model=config.get("model"),
        timeout_seconds=float(config.get("timeout_seconds", 30.0)),
    )
    run = run_lmstudio_observed_state(
        payload,
        pipeline_run_id=pipeline_run_id,
        generated_at=generated_at,
        max_retries=int(config.get("max_retries", 1)),
        client=client,
    )
    return KernelRunResult(
        kernel_name="observed_state",
        engine_mode="lmstudio",
        validated_output=run.validated_output,
        raw_model_output=run.raw_model_output,
        generated_payload=run.generated_payload,
        model_name=run.model_name,
        retries_used=run.retries_used,
        elapsed_seconds=run.elapsed_seconds,
    )


def _run_expected_state_lmstudio(
    payload: KernelInputV1,
    *,
    pipeline_run_id: str,
    generated_at: str,
    config: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
) -> KernelRunResult:
    config = config or {}
    client = LMStudioClient(
        base_url=config.get("base_url"),
        model=config.get("model"),
        timeout_seconds=float(config.get("timeout_seconds", 30.0)),
    )
    run = run_lmstudio_expected_state(
        payload,
        pipeline_run_id=pipeline_run_id,
        generated_at=generated_at,
        max_retries=int(config.get("max_retries", 1)),
        client=client,
    )
    return KernelRunResult(
        kernel_name="expected_state",
        engine_mode="lmstudio",
        validated_output=run.validated_output,
        raw_model_output=run.raw_model_output,
        generated_payload=run.generated_payload,
        model_name=run.model_name,
        retries_used=run.retries_used,
        elapsed_seconds=run.elapsed_seconds,
    )


KERNEL_REGISTRY: dict[tuple[str, str], KernelImplementation] = {
    ("observed_state", "deterministic"): _run_observed_state_deterministic,
    ("observed_state", "lmstudio"): _run_observed_state_lmstudio,
    ("expected_state", "deterministic"): _run_expected_state_deterministic,
    ("expected_state", "lmstudio"): _run_expected_state_lmstudio,
    ("contradiction", "deterministic"): _run_contradiction_deterministic,
}
