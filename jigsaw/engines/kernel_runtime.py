from __future__ import annotations

from dataclasses import replace
from typing import Any

from jigsaw.engines.kernel_registry import KERNEL_REGISTRY
from jigsaw.engines.result_types import KernelRunResult
from jigsaw.lanes.kernel_lane.models import KernelInputV1
from jigsaw.lanes.kernel_lane.validators import validate_kernel_output_v1


class KernelRuntimeError(RuntimeError):
    pass


def resolve_profile_engine(profile: dict[str, Any], kernel_name: str) -> str:
    kernel_engines = profile.get("kernel_engines") or profile.get("kernels") or {}
    engine_mode = kernel_engines.get(kernel_name)
    if not engine_mode:
        raise KernelRuntimeError(f"Profile {profile.get('profile_name', '<unknown>')} does not define an engine for {kernel_name}.")
    return str(engine_mode)


def engine_config_for_mode(profile: dict[str, Any], engine_mode: str) -> dict[str, Any]:
    engine_section = profile.get("engine", {})
    config = engine_section.get(engine_mode, {})
    return dict(config) if isinstance(config, dict) else {}


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
    validated_output = validate_kernel_output_v1(result.validated_output.model_dump(mode="python"))
    return replace(result, validated_output=validated_output)


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
    config = engine_config_for_mode(profile, engine_mode)
    return run_kernel(
        kernel_name,
        engine_mode,
        case_input,
        pipeline_run_id=pipeline_run_id,
        generated_at=generated_at,
        context=context,
        config=config,
    )
