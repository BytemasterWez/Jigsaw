from __future__ import annotations

import json
from pathlib import Path

from jigsaw.lanes.kernel_lane.lmstudio_observed_state import _build_output_shell, _normalize_generated_payload
from jigsaw.lanes.kernel_lane.validators import validate_kernel_input_v1, validate_kernel_output_v1


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "examples" / "inputs"
FIXED_GENERATED_AT = "2026-03-14T12:00:00Z"
PIPELINE_RUN_ID = "lmstudio-observed-rubric-test"


def load_example_input() -> dict:
    with (FIXTURES_DIR / "sample_kernel_input.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_lm_observed_normalization_maps_sufficient_coverage_to_clear() -> None:
    payload = validate_kernel_input_v1(load_example_input())
    shell = _build_output_shell(payload, pipeline_run_id=PIPELINE_RUN_ID, generated_at=FIXED_GENERATED_AT)
    generated_payload = {
        "kernel_type": "observed_state",
        "status": "success",
        "coverage_status": "sufficient",
        "polarity_status": "mixed",
        "observed_slots_present": 4,
        "missing_slots": [],
        "coverage_reason": "All required observation slots are present and directly evidenced.",
        "polarity_reason": "One observed value is false, so polarity is mixed rather than strong.",
        "notes": [],
    }

    normalized = _normalize_generated_payload(generated_payload, shell)
    validated = validate_kernel_output_v1(normalized)

    assert validated.judgment == "observed_state_clear"
    assert validated.confidence == 0.78
    assert validated.reasons[0] == "All required observation slots are present and directly evidenced."
