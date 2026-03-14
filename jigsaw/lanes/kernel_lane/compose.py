from __future__ import annotations

from .models import KernelBundleResultV1, KernelInputV1, KernelOutputV1
from .utils import build_metadata, make_id


def compose_kernel_bundle(
    payload: KernelInputV1,
    outputs: list[KernelOutputV1],
    *,
    pipeline_run_id: str,
    generated_at: str,
) -> KernelBundleResultV1:
    judgments = {output.kernel_type: output.judgment for output in outputs}
    notes: list[str] = []

    if judgments.get("observed_state") == "observed_state_sparse":
        bundle_judgment = "insufficient_evidence"
        summary = "Observed coverage is too sparse to trust stronger downstream judgment."
        notes.append("Observed-state limits trust in the rest of the bundle.")
    elif judgments.get("contradiction") in {"contradiction_detected", "critical_contradiction"}:
        bundle_judgment = "contradictory"
        summary = "The case is partially understood but internally unstable because the inputs conflict."
        notes.append("Contradiction lowers trust even where alignment is otherwise usable.")
    elif judgments.get("expected_state") == "expected_state_aligned":
        bundle_judgment = "aligned"
        summary = "The case is clear enough and aligns with the expected state."
        notes.append("No contradiction detected across the first kernel bundle.")
    else:
        bundle_judgment = "partially_aligned"
        summary = "The case is only partially aligned and should be treated cautiously."
        notes.append("Alignment remains partial even though the observed picture is usable.")

    bundle_id = make_id("kernel_bundle", payload.input_id)
    return KernelBundleResultV1(
        bundle_id=bundle_id,
        input_id=payload.input_id,
        kernel_outputs=outputs,
        composed_summary={
            "bundle_judgment": bundle_judgment,
            "summary": summary,
        },
        composition_notes=notes,
        metadata=build_metadata(
            bundle_id,
            source_system="jigsaw",
            pipeline_run_id=pipeline_run_id,
            confidence=min(output.confidence for output in outputs) if outputs else None,
            tags=["kernel-lane", "bundle-result"],
            lineage=[payload.input_id] + [output.output_id for output in outputs],
            created_at=generated_at,
        ),
    )

