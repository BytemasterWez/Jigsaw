from __future__ import annotations

from typing import Any

from jigsaw.controller.hypothesis_controller import CaseInputV1, validate_case_input_v1
from jigsaw.engines.kernel_runtime import run_kernel_for_profile
from jigsaw.lanes.kernel_lane.compose import compose_kernel_bundle
from jigsaw.lanes.kernel_lane.models import KernelInputV1
from jigsaw.lanes.kernel_lane.validators import validate_kernel_bundle_result_v1
from jigsaw.lanes.real_case_lane.execute_profile_batch import (
    DEFAULT_PROFILE,
    GCItem,
    _build_kernel_input_for_profile,
    load_execution_profile,
)


def _coerce_gc_item(item: GCItem | dict[str, Any]) -> GCItem:
    if isinstance(item, GCItem):
        return item
    return GCItem(
        item_id=int(item["item_id"]),
        item_type=str(item["item_type"]),
        title=str(item["title"]),
        content=str(item["content"]),
        created_at=str(item["created_at"]),
        updated_at=str(item["updated_at"]),
    )


def _evidence_id(item_id: int) -> str:
    return f"gc:item:{item_id}"


def _validate_case_input_against_context(case_input: CaseInputV1, primary_item: GCItem, supporting_items: list[GCItem]) -> None:
    expected_primary = {_evidence_id(primary_item.item_id)}
    if set(case_input.primary_evidence_ids) != expected_primary:
        raise ValueError("case_input primary_evidence_ids do not match the supplied primary GC item.")

    available_support = {_evidence_id(item.item_id) for item in supporting_items}
    if not set(case_input.supporting_evidence_ids).issubset(available_support):
        raise ValueError("case_input supporting_evidence_ids are not present in the supplied supporting GC context.")


def build_kernel_input_from_case_input(
    case_input: CaseInputV1 | dict[str, Any],
    gc_context: dict[str, Any],
    *,
    profile_name: str = DEFAULT_PROFILE,
    pipeline_run_id: str = "case-input-composition",
    generated_at: str = "2026-03-15T16:30:00Z",
) -> KernelInputV1:
    validated_case_input = case_input if isinstance(case_input, CaseInputV1) else validate_case_input_v1(case_input)
    profile = load_execution_profile(profile_name)
    primary_item = _coerce_gc_item(gc_context["primary_item"])
    supporting_items = [_coerce_gc_item(item) for item in gc_context.get("supporting_items", [])]
    _validate_case_input_against_context(validated_case_input, primary_item, supporting_items)

    kernel_input = _build_kernel_input_for_profile(
        profile,
        primary_item,
        supporting_items,
        pipeline_run_id=pipeline_run_id,
        generated_at=generated_at,
    )
    context = dict(kernel_input.context)
    context.update(
        {
            "case_id": validated_case_input.case_id,
            "hypothesis_id": validated_case_input.hypothesis_id,
            "reason_for_packaging": validated_case_input.reason_for_packaging,
            "current_confidence": validated_case_input.current_confidence,
        }
    )
    metadata = kernel_input.metadata.model_copy(update={"confidence": validated_case_input.current_confidence})
    return kernel_input.model_copy(update={"context": context, "metadata": metadata})


def compose_case_from_case_input(
    case_input: CaseInputV1 | dict[str, Any],
    gc_context: dict[str, Any],
    *,
    profile_name: str = DEFAULT_PROFILE,
    pipeline_run_id: str = "case-input-composition",
    generated_at: str = "2026-03-15T16:30:00Z",
) -> dict[str, Any]:
    validated_case_input = case_input if isinstance(case_input, CaseInputV1) else validate_case_input_v1(case_input)
    profile = load_execution_profile(profile_name)
    kernel_input = build_kernel_input_from_case_input(
        validated_case_input,
        gc_context,
        profile_name=profile_name,
        pipeline_run_id=pipeline_run_id,
        generated_at=generated_at,
    )
    observed_result = run_kernel_for_profile(
        "observed_state",
        kernel_input,
        profile,
        pipeline_run_id=pipeline_run_id,
        generated_at=generated_at,
    )
    expected_result = run_kernel_for_profile(
        "expected_state",
        kernel_input,
        profile,
        pipeline_run_id=pipeline_run_id,
        generated_at=generated_at,
    )
    contradiction_result = run_kernel_for_profile(
        "contradiction",
        kernel_input,
        profile,
        pipeline_run_id=pipeline_run_id,
        generated_at=generated_at,
    )
    bundle_result = validate_kernel_bundle_result_v1(
        compose_kernel_bundle(
            kernel_input,
            [
                observed_result.validated_output,
                expected_result.validated_output,
                contradiction_result.validated_output,
            ],
            pipeline_run_id=pipeline_run_id,
            generated_at=generated_at,
        ).model_dump(mode="python")
    )
    case_summary = {
        "case_id": validated_case_input.case_id,
        "hypothesis_id": validated_case_input.hypothesis_id,
        "bundle_judgment": bundle_result.composed_summary.bundle_judgment,
        "bundle_confidence": bundle_result.metadata.confidence,
        "reason_for_packaging": validated_case_input.reason_for_packaging,
        "kernel_engines": {
            "observed_state": observed_result.engine_mode,
            "expected_state": expected_result.engine_mode,
            "contradiction": contradiction_result.engine_mode,
        },
        "kernel_runtime": {
            "observed_state": {
                "engine_mode": observed_result.engine_mode,
                "model_name": observed_result.model_name,
                "retries_used": observed_result.retries_used,
                "elapsed_seconds": observed_result.elapsed_seconds,
                "judgment": observed_result.validated_output.judgment,
            },
            "expected_state": {
                "engine_mode": expected_result.engine_mode,
                "model_name": expected_result.model_name,
                "retries_used": expected_result.retries_used,
                "elapsed_seconds": expected_result.elapsed_seconds,
                "judgment": expected_result.validated_output.judgment,
            },
            "contradiction": {
                "engine_mode": contradiction_result.engine_mode,
                "model_name": contradiction_result.model_name,
                "retries_used": contradiction_result.retries_used,
                "elapsed_seconds": contradiction_result.elapsed_seconds,
                "judgment": contradiction_result.validated_output.judgment,
            },
        },
    }
    return {
        "case_input": validated_case_input.model_dump(mode="python"),
        "kernel_input": kernel_input.model_dump(mode="python"),
        "kernel_bundle_result": bundle_result.model_dump(mode="python"),
        "case_summary": case_summary,
        "status": "success",
    }
