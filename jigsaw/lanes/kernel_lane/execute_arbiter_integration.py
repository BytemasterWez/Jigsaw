from __future__ import annotations

import json
from pathlib import Path

from .arbiter_integration import adjudicate_with_exchange, kernel_bundle_result_to_arbiter_request
from .execute_first_kernel_bundle import OUTPUT_DIR as KERNEL_OUTPUT_DIR
from .execute_first_kernel_bundle import run_first_kernel_bundle
from .validators import validate_kernel_bundle_result_v1, validate_kernel_input_v1


REPO_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_DIR = REPO_ROOT / "validation" / "kernel_to_arbiter" / "output"


def _dump_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def run_kernel_to_arbiter_integration() -> dict[str, str]:
    pipeline_run_id = "kernel-to-arbiter-integration"
    run_first_kernel_bundle()

    with (KERNEL_OUTPUT_DIR / "kernel_input.json").open("r", encoding="utf-8") as handle:
        kernel_input = validate_kernel_input_v1(json.load(handle))
    with (KERNEL_OUTPUT_DIR / "kernel_bundle_result.json").open("r", encoding="utf-8") as handle:
        bundle_result = validate_kernel_bundle_result_v1(json.load(handle))

    arbiter_request = kernel_bundle_result_to_arbiter_request(kernel_input, bundle_result)
    arbiter_response, arbiter_exchange = adjudicate_with_exchange(
        arbiter_request,
        case_id=arbiter_request["candidate_id"],
        timestamp=kernel_input.metadata.updated_at,
        exchange_scope=pipeline_run_id,
        arbiter_metadata={"domain": arbiter_request["domain"]},
    )

    _dump_json(OUTPUT_DIR / "kernel_input.json", kernel_input.model_dump(mode="python"))
    _dump_json(OUTPUT_DIR / "kernel_bundle_result.json", bundle_result.model_dump(mode="python"))
    _dump_json(OUTPUT_DIR / "arbiter_request.json", arbiter_request)
    _dump_json(OUTPUT_DIR / "arbiter_response.json", arbiter_response)
    _dump_json(OUTPUT_DIR / "arbiter_exchange.json", arbiter_exchange.model_dump(mode="python"))
    _dump_json(
        OUTPUT_DIR / "run_log.json",
        {
            "pipeline_run_id": pipeline_run_id,
            "source_bundle_id": bundle_result.bundle_id,
            "candidate_id": arbiter_request["candidate_id"],
            "arbiter_exchange_id": arbiter_exchange.exchange_id,
            "arbiter_judgement": arbiter_response["judgement"],
            "status": "success",
        },
    )

    return {
        "bundle_id": bundle_result.bundle_id,
        "candidate_id": arbiter_request["candidate_id"],
        "arbiter_judgement": arbiter_response["judgement"],
        "status": "success",
    }


if __name__ == "__main__":
    result = run_kernel_to_arbiter_integration()
    print(json.dumps(result, indent=2))
