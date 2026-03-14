from __future__ import annotations

import json
from pathlib import Path

from jigsaw.lanes.kernel_lane.kernels import run_contradiction, run_expected_state, run_observed_state
from jigsaw.lanes.kernel_lane.validators import validate_kernel_input_v1, validate_kernel_output_v1


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "examples" / "inputs"
FIXED_GENERATED_AT = "2026-03-14T12:00:00Z"
PIPELINE_RUN_ID = "kernel-lane-first-bundle"


def load_example_input() -> dict:
    with (FIXTURES_DIR / "sample_kernel_input.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_observed_state_kernel_output_shape() -> None:
    payload = validate_kernel_input_v1(load_example_input())
    output = run_observed_state(payload, pipeline_run_id=PIPELINE_RUN_ID, generated_at=FIXED_GENERATED_AT)
    validated = validate_kernel_output_v1(output.model_dump(mode="python"))

    assert validated.kernel_type == "observed_state"
    assert validated.judgment == "observed_state_partial"


def test_expected_state_kernel_output_shape() -> None:
    payload = validate_kernel_input_v1(load_example_input())
    output = run_expected_state(payload, pipeline_run_id=PIPELINE_RUN_ID, generated_at=FIXED_GENERATED_AT)
    validated = validate_kernel_output_v1(output.model_dump(mode="python"))

    assert validated.kernel_type == "expected_state"
    assert validated.judgment == "expected_state_partial"


def test_contradiction_kernel_output_shape() -> None:
    payload = validate_kernel_input_v1(load_example_input())
    output = run_contradiction(payload, pipeline_run_id=PIPELINE_RUN_ID, generated_at=FIXED_GENERATED_AT)
    validated = validate_kernel_output_v1(output.model_dump(mode="python"))

    assert validated.kernel_type == "contradiction"
    assert validated.judgment == "contradiction_detected"

