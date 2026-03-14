from __future__ import annotations

from .models import KernelInputV1, KernelOutputV1
from .utils import build_metadata, make_id


def run_observed_state(
    payload: KernelInputV1,
    *,
    pipeline_run_id: str,
    generated_at: str,
) -> KernelOutputV1:
    observed_count = len(payload.content.observed_items)
    minimum_expected = int(payload.context.get("minimum_expected_observations", 3))
    if observed_count >= minimum_expected:
        judgment = "observed_state_clear"
        confidence = 0.85
        reasons = ["Observed coverage meets the minimum expected threshold."]
    elif observed_count >= max(1, minimum_expected - 1):
        judgment = "observed_state_partial"
        confidence = 0.74
        reasons = ["Observed coverage is usable but still incomplete across core categories."]
    else:
        judgment = "observed_state_sparse"
        confidence = 0.58
        reasons = ["Observed coverage is too thin to treat the case picture as complete."]

    output_id = make_id("kernel_output", payload.input_id, "observed_state")
    return KernelOutputV1(
        output_id=output_id,
        kernel_type="observed_state",
        input_id=payload.input_id,
        status="success",
        judgment=judgment,
        confidence=confidence,
        reasons=reasons,
        evidence_used=[record.evidence_id for record in payload.evidence[:observed_count]],
        metadata=build_metadata(
            output_id,
            source_system="jigsaw",
            pipeline_run_id=pipeline_run_id,
            confidence=confidence,
            tags=["kernel-lane", "observed-state"],
            lineage=[payload.input_id],
            created_at=generated_at,
        ),
    )


def run_expected_state(
    payload: KernelInputV1,
    *,
    pipeline_run_id: str,
    generated_at: str,
) -> KernelOutputV1:
    observed_by_name = {
        item["name"]: item.get("value")
        for item in payload.content.observed_items
        if "name" in item
    }
    expected_items = payload.content.expected_items
    satisfied = 0
    reasons: list[str] = []
    for expected in expected_items:
        name = expected.get("name")
        target_value = expected.get("target_value")
        observed_value = observed_by_name.get(name)
        if observed_value == target_value:
            satisfied += 1
        else:
            reasons.append(f"{name} is not aligned with the expected target.")

    ratio = 1.0 if not expected_items else satisfied / len(expected_items)
    if ratio >= 0.75:
        judgment = "expected_state_aligned"
    elif ratio >= 0.40:
        judgment = "expected_state_partial"
    else:
        judgment = "expected_state_misaligned"

    confidence = round(min(0.95, 0.55 + 0.35 * ratio), 4)
    if not reasons:
        reasons = ["Observed values are aligned with the expected target state."]

    output_id = make_id("kernel_output", payload.input_id, "expected_state")
    return KernelOutputV1(
        output_id=output_id,
        kernel_type="expected_state",
        input_id=payload.input_id,
        status="success",
        judgment=judgment,
        confidence=confidence,
        reasons=reasons,
        evidence_used=[record.evidence_id for record in payload.evidence],
        metadata=build_metadata(
            output_id,
            source_system="jigsaw",
            pipeline_run_id=pipeline_run_id,
            confidence=confidence,
            tags=["kernel-lane", "expected-state"],
            lineage=[payload.input_id],
            created_at=generated_at,
        ),
    )


def run_contradiction(
    payload: KernelInputV1,
    *,
    pipeline_run_id: str,
    generated_at: str,
) -> KernelOutputV1:
    contradictions = 0
    reasons: list[str] = []
    observed_by_name = {
        item["name"]: item.get("value")
        for item in payload.content.observed_items
        if "name" in item
    }
    for claim in payload.content.claims:
        name = claim.get("name")
        claim_value = claim.get("value")
        observed_value = observed_by_name.get(name)
        if observed_value is None:
            continue
        if observed_value != claim_value:
            contradictions += 1
            reasons.append(f"{name} is observed as {observed_value!r} but claimed as {claim_value!r}.")

    if contradictions == 0:
        judgment = "contradiction_not_detected"
        confidence = 0.72
        reasons = ["No material contradiction detected across the provided input set."]
    elif contradictions == 1:
        judgment = "contradiction_detected"
        confidence = 0.81
    else:
        judgment = "critical_contradiction"
        confidence = 0.89

    output_id = make_id("kernel_output", payload.input_id, "contradiction")
    return KernelOutputV1(
        output_id=output_id,
        kernel_type="contradiction",
        input_id=payload.input_id,
        status="success",
        judgment=judgment,
        confidence=confidence,
        reasons=reasons,
        evidence_used=[record.evidence_id for record in payload.evidence],
        metadata=build_metadata(
            output_id,
            source_system="jigsaw",
            pipeline_run_id=pipeline_run_id,
            confidence=confidence,
            tags=["kernel-lane", "contradiction"],
            lineage=[payload.input_id],
            created_at=generated_at,
        ),
    )

