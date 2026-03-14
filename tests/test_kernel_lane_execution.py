from __future__ import annotations

import json

from jigsaw.lanes.kernel_lane.execute_first_kernel_bundle import OUTPUT_DIR, run_first_kernel_bundle


def test_first_kernel_bundle_runner_generates_expected_outputs() -> None:
    result = run_first_kernel_bundle()

    assert result["status"] == "success"

    expected_files = [
        "kernel_input.json",
        "observed_state.json",
        "expected_state.json",
        "contradiction.json",
        "kernel_bundle_result.json",
        "run_log.json",
    ]
    for name in expected_files:
        assert (OUTPUT_DIR / name).exists()

    with (OUTPUT_DIR / "kernel_bundle_result.json").open("r", encoding="utf-8") as handle:
        bundle = json.load(handle)

    assert bundle["contract"] == "kernel_bundle_result"
    assert bundle["version"] == "v1"
    assert len(bundle["kernel_outputs"]) == 3

