from __future__ import annotations

import json
from pathlib import Path

from jigsaw.engines.kernel_runtime import run_kernel

from .arbiter_integration import adjudicate_via_current_arbiter, kernel_bundle_result_to_arbiter_request
from .compose import compose_kernel_bundle
from .execute_first_kernel_bundle import INPUT_PATH
from .validators import (
    validate_kernel_bundle_result_v1,
    validate_kernel_input_v1,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_DIR = REPO_ROOT / "validation" / "kernel_lmstudio_test" / "output"


def _dump_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def run_lmstudio_observed_test() -> dict[str, str | int | float]:
    pipeline_run_id = "kernel-lmstudio-observed-test"
    generated_at = "2026-03-14T12:30:00Z"

    with INPUT_PATH.open("r", encoding="utf-8") as handle:
        source_payload = json.load(handle)
    kernel_input = validate_kernel_input_v1(source_payload)
    _dump_json(OUTPUT_DIR / "kernel_input.json", kernel_input.model_dump(mode="python"))
    try:
        lm_observed = run_kernel(
            "observed_state",
            "lmstudio",
            kernel_input,
            pipeline_run_id=pipeline_run_id,
            generated_at=generated_at,
            config={"max_retries": 1},
        )
        expected_result = run_kernel(
            "expected_state",
            "deterministic",
            kernel_input,
            pipeline_run_id=pipeline_run_id,
            generated_at=generated_at,
        )
        contradiction_result = run_kernel(
            "contradiction",
            "deterministic",
            kernel_input,
            pipeline_run_id=pipeline_run_id,
            generated_at=generated_at,
        )
        bundle_result = compose_kernel_bundle(
            kernel_input,
            [lm_observed.validated_output, expected_result.validated_output, contradiction_result.validated_output],
            pipeline_run_id=pipeline_run_id,
            generated_at=generated_at,
        )
        bundle_result = validate_kernel_bundle_result_v1(bundle_result.model_dump(mode="python"))
        arbiter_request = kernel_bundle_result_to_arbiter_request(kernel_input, bundle_result)
        arbiter_response = adjudicate_via_current_arbiter(arbiter_request)

        _dump_json(OUTPUT_DIR / "observed_state_raw_model_output.json", lm_observed.raw_model_output)
        _dump_json(OUTPUT_DIR / "observed_state_generated.json", lm_observed.generated_payload)
        _dump_json(OUTPUT_DIR / "observed_state_validated.json", lm_observed.validated_output.model_dump(mode="python"))
        _dump_json(OUTPUT_DIR / "expected_state.json", expected_result.validated_output.model_dump(mode="python"))
        _dump_json(OUTPUT_DIR / "contradiction.json", contradiction_result.validated_output.model_dump(mode="python"))
        _dump_json(OUTPUT_DIR / "kernel_bundle_result.json", bundle_result.model_dump(mode="python"))
        _dump_json(OUTPUT_DIR / "arbiter_request.json", arbiter_request)
        _dump_json(OUTPUT_DIR / "arbiter_response.json", arbiter_response)
        _dump_json(
            OUTPUT_DIR / "run_log.json",
            {
                "pipeline_run_id": pipeline_run_id,
                "generated_at": generated_at,
                "model_name": lm_observed.model_name,
                "retries_used": lm_observed.retries_used,
                "elapsed_seconds": lm_observed.elapsed_seconds,
                "observed_state_judgment": lm_observed.validated_output.judgment,
                "bundle_judgment": bundle_result.composed_summary.bundle_judgment,
                "arbiter_judgement": arbiter_response["judgement"],
                "kernel_engines": {
                    "observed_state": lm_observed.engine_mode,
                    "expected_state": expected_result.engine_mode,
                    "contradiction": contradiction_result.engine_mode,
                },
                "status": "success",
            },
        )

        return {
            "model_name": lm_observed.model_name,
            "retries_used": lm_observed.retries_used,
            "elapsed_seconds": lm_observed.elapsed_seconds,
            "observed_state_judgment": lm_observed.validated_output.judgment,
            "bundle_judgment": bundle_result.composed_summary.bundle_judgment,
            "arbiter_judgement": arbiter_response["judgement"],
            "status": "success",
        }
    except Exception as exc:
        cause = exc.__cause__
        _dump_json(
            OUTPUT_DIR / "run_log.json",
            {
                "pipeline_run_id": pipeline_run_id,
                "generated_at": generated_at,
                "status": "failed",
                "error": str(exc),
                "cause": str(cause) if cause else None,
            },
        )
        raise


if __name__ == "__main__":
    result = run_lmstudio_observed_test()
    print(json.dumps(result, indent=2))
