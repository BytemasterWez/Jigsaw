from __future__ import annotations

from dataclasses import replace
from typing import Any

from jigsaw.engines.exchange_manager import build_kernel_exchange
from jigsaw.engines.kernel_registry import KERNEL_REGISTRY
from jigsaw.engines.result_types import KernelRunResult
from jigsaw.lanes.kernel_lane.models import KernelInputV1
from jigsaw.lanes.kernel_lane.validators import validate_kernel_output_v1


class KernelRuntimeError(RuntimeError):
    def __init__(self, message: str, *, kernel_exchange: dict[str, Any] | None = None):
        super().__init__(message)
        self.kernel_exchange = kernel_exchange


def resolve_profile_engine(profile: dict[str, Any], kernel_name: str) -> str:
    kernel_engines = profile.get("kernel_engines") or profile.get("kernels") or {}
    engine_mode = kernel_engines.get(kernel_name)
    if not engine_mode:
        raise KernelRuntimeError(f"Profile {profile.get('profile_name', '<unknown>')} does not define an engine for {kernel_name}.")
    return str(engine_mode)


def engine_config_for_mode(profile: dict[str, Any], engine_mode: str, *, kernel_name: str | None = None) -> dict[str, Any]:
    engine_section = profile.get("engine", {})
    config = engine_section.get(engine_mode, {})
    if not isinstance(config, dict):
        return {}
    merged = {key: value for key, value in config.items() if not isinstance(value, dict)}
    if kernel_name and isinstance(config.get(kernel_name), dict):
        merged.update(config[kernel_name])
    return merged


def run_kernel(
    kernel_name: str,
    engine_mode: str,
    case_input: KernelInputV1,
    *,
    pipeline_run_id: str,
    generated_at: str,
    context: dict[str, Any] | None = None,
    config: dict[str, Any] | None = None,
) -> KernelRunResult:
    implementation = KERNEL_REGISTRY.get((kernel_name, engine_mode))
    if implementation is None:
        raise KernelRuntimeError(f"No kernel implementation registered for {kernel_name}/{engine_mode}.")

    result = implementation(
        case_input,
        pipeline_run_id=pipeline_run_id,
        generated_at=generated_at,
        context=context,
        config=config,
    )
    input_packet = case_input.model_dump(mode="python")
    case_id = str(case_input.context.get("case_id") or case_input.subject_id)
    output_packet = (
        result.validated_output.model_dump(mode="python")
        if hasattr(result.validated_output, "model_dump")
        else dict(result.validated_output)
    )
    engine_metadata: dict[str, Any] = {}
    if result.model_name:
        engine_metadata["model"] = result.model_name
    if result.retries_used or engine_mode == "lmstudio":
        engine_metadata["retries_used"] = result.retries_used
    if result.elapsed_seconds is not None:
        engine_metadata["elapsed_seconds"] = result.elapsed_seconds

    try:
        validated_output = validate_kernel_output_v1(output_packet)
        kernel_exchange = build_kernel_exchange(
            kernel_name=kernel_name,
            engine_mode=engine_mode,
            case_id=case_id,
            input_packet=input_packet,
            output_packet=validated_output.model_dump(mode="python"),
            validation_passed=True,
            timestamp=generated_at,
            pipeline_run_id=pipeline_run_id,
            engine_metadata=engine_metadata,
        )
        return replace(result, validated_output=validated_output, kernel_exchange=kernel_exchange)
    except Exception as exc:
        kernel_exchange = build_kernel_exchange(
            kernel_name=kernel_name,
            engine_mode=engine_mode,
            case_id=case_id,
            input_packet=input_packet,
            output_packet=output_packet,
            validation_passed=False,
            timestamp=generated_at,
            pipeline_run_id=pipeline_run_id,
            engine_metadata=engine_metadata,
        )
        raise KernelRuntimeError(
            f"Kernel {kernel_name}/{engine_mode} returned an invalid output packet.",
            kernel_exchange=kernel_exchange.model_dump(mode="python"),
        ) from exc


def run_kernel_for_profile(
    kernel_name: str,
    case_input: KernelInputV1,
    profile: dict[str, Any],
    *,
    pipeline_run_id: str,
    generated_at: str,
    context: dict[str, Any] | None = None,
) -> KernelRunResult:
    engine_mode = resolve_profile_engine(profile, kernel_name)
    config = engine_config_for_mode(profile, engine_mode, kernel_name=kernel_name)
    return run_kernel(
        kernel_name,
        engine_mode,
        case_input,
        pipeline_run_id=pipeline_run_id,
        generated_at=generated_at,
        context=context,
        config=config,
    )
