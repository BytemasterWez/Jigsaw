from __future__ import annotations

import json

from jigsaw.lanes.kernel_lane.arbiter_integration import (
    adjudicate_via_current_arbiter,
    kernel_bundle_result_to_arbiter_request,
)
from jigsaw.lanes.kernel_lane.execute_arbiter_integration import OUTPUT_DIR, run_kernel_to_arbiter_integration
from jigsaw.lanes.kernel_lane.execute_first_kernel_bundle import OUTPUT_DIR as KERNEL_OUTPUT_DIR
from jigsaw.lanes.kernel_lane.execute_first_kernel_bundle import run_first_kernel_bundle
from jigsaw.lanes.kernel_lane.validators import validate_kernel_bundle_result_v1, validate_kernel_input_v1


def test_kernel_bundle_can_map_into_current_arbiter_request() -> None:
    run_first_kernel_bundle()

    with (KERNEL_OUTPUT_DIR / "kernel_input.json").open("r", encoding="utf-8") as handle:
        kernel_input = validate_kernel_input_v1(json.load(handle))
    with (KERNEL_OUTPUT_DIR / "kernel_bundle_result.json").open("r", encoding="utf-8") as handle:
        bundle_result = validate_kernel_bundle_result_v1(json.load(handle))

    request = kernel_bundle_result_to_arbiter_request(kernel_input, bundle_result)
    response = adjudicate_via_current_arbiter(request)

    assert request["candidate_id"] == kernel_input.subject_id
    assert request["evidence"]["source_count"] == len(kernel_input.evidence)
    assert request["context"]["jigsaw_bundle_judgment"] == bundle_result.composed_summary.bundle_judgment
    assert response["candidate_id"] == kernel_input.subject_id
    assert response["judgement"] in {"promoted", "watchlist", "rejected"}


def test_kernel_to_arbiter_runner_writes_integration_outputs() -> None:
    result = run_kernel_to_arbiter_integration()

    assert result["status"] == "success"

    expected_files = [
        "kernel_input.json",
        "kernel_bundle_result.json",
        "arbiter_request.json",
        "arbiter_response.json",
        "run_log.json",
    ]
    for name in expected_files:
        assert (OUTPUT_DIR / name).exists()
