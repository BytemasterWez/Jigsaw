from __future__ import annotations

import json
from pathlib import Path

from .compose import compose_kernel_bundle
from .kernels import run_contradiction, run_expected_state, run_observed_state
from .validators import (
    validate_kernel_bundle_result_v1,
    validate_kernel_input_v1,
    validate_kernel_output_v1,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
INPUT_PATH = REPO_ROOT / "examples" / "inputs" / "sample_kernel_input.json"
OUTPUT_DIR = REPO_ROOT / "validation" / "kernel_first_bundle" / "output"


def _dump_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def run_first_kernel_bundle() -> dict:
    pipeline_run_id = "kernel-lane-first-bundle"
    generated_at = "2026-03-14T12:00:00Z"

    with INPUT_PATH.open("r", encoding="utf-8") as handle:
        source_payload = json.load(handle)

    kernel_input = validate_kernel_input_v1(source_payload)
    observed_output = validate_kernel_output_v1(
        run_observed_state(kernel_input, pipeline_run_id=pipeline_run_id, generated_at=generated_at).model_dump(mode="python")
    )
    expected_output = validate_kernel_output_v1(
        run_expected_state(kernel_input, pipeline_run_id=pipeline_run_id, generated_at=generated_at).model_dump(mode="python")
    )
    contradiction_output = validate_kernel_output_v1(
        run_contradiction(kernel_input, pipeline_run_id=pipeline_run_id, generated_at=generated_at).model_dump(mode="python")
    )

    bundle_result = compose_kernel_bundle(
        kernel_input,
        [observed_output, expected_output, contradiction_output],
        pipeline_run_id=pipeline_run_id,
        generated_at=generated_at,
    )
    validate_kernel_bundle_result_v1(bundle_result.model_dump(mode="python"))

    _dump_json(OUTPUT_DIR / "kernel_input.json", kernel_input.model_dump(mode="python"))
    _dump_json(OUTPUT_DIR / "observed_state.json", observed_output.model_dump(mode="python"))
    _dump_json(OUTPUT_DIR / "expected_state.json", expected_output.model_dump(mode="python"))
    _dump_json(OUTPUT_DIR / "contradiction.json", contradiction_output.model_dump(mode="python"))
    _dump_json(OUTPUT_DIR / "kernel_bundle_result.json", bundle_result.model_dump(mode="python"))
    _dump_json(
        OUTPUT_DIR / "run_log.json",
        {
            "pipeline_run_id": pipeline_run_id,
            "generated_at": generated_at,
            "input_path": str(INPUT_PATH),
            "output_dir": str(OUTPUT_DIR),
            "input_id": kernel_input.input_id,
            "bundle_id": bundle_result.bundle_id,
            "kernel_order": ["observed_state", "expected_state", "contradiction"],
            "status": "success",
        },
    )

    return {
        "input_id": kernel_input.input_id,
        "bundle_id": bundle_result.bundle_id,
        "status": "success",
    }


if __name__ == "__main__":
    result = run_first_kernel_bundle()
    print(json.dumps(result, indent=2))

