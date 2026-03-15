from __future__ import annotations

import json
from pathlib import Path

from jigsaw.lanes.kernel_lane.lmstudio_expected_state import _build_output_shell, _normalize_generated_payload
from jigsaw.lanes.kernel_lane.validators import validate_kernel_input_v1, validate_kernel_output_v1


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "examples" / "inputs"
FIXED_GENERATED_AT = "2026-03-15T12:00:00Z"
PIPELINE_RUN_ID = "lmstudio-expected-rubric-test"


def load_example_input() -> dict:
    with (FIXTURES_DIR / "sample_kernel_input.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_lm_expected_normalization_maps_three_quarters_aligned_to_aligned() -> None:
    payload = validate_kernel_input_v1(load_example_input())
    shell = _build_output_shell(payload, pipeline_run_id=PIPELINE_RUN_ID, generated_at=FIXED_GENERATED_AT)
    generated_payload = {
        "kernel_type": "expected_state",
        "status": "success",
        "expected_slots_present": 4,
        "aligned_slots": [
            "workflow_automation_focus",
            "consulting_use_case_defined",
            "operations_scaffold_present",
        ],
        "misaligned_slots": ["offer_pricing_defined"],
        "missing_slots": [],
        "alignment_ratio": 0.75,
        "fit_reason": "Three of four expected slots align with the observed picture.",
        "missing_reason": "No expected slots are missing from the observed picture.",
        "notes": [],
    }

    normalized = _normalize_generated_payload(generated_payload, shell)
    validated = validate_kernel_output_v1(normalized)

    assert validated.judgment == "expected_state_aligned"
    assert validated.confidence == 0.8125
    assert validated.reasons[0] == "Three of four expected slots align with the observed picture."


def test_lm_expected_normalization_maps_one_quarter_aligned_to_misaligned() -> None:
    payload = validate_kernel_input_v1(load_example_input())
    shell = _build_output_shell(payload, pipeline_run_id=PIPELINE_RUN_ID, generated_at=FIXED_GENERATED_AT)
    generated_payload = {
        "kernel_type": "expected_state",
        "status": "success",
        "expected_slots_present": 4,
        "aligned_slots": ["workflow_automation_focus"],
        "misaligned_slots": [
            "consulting_use_case_defined",
            "offer_pricing_defined",
            "operations_scaffold_present",
        ],
        "missing_slots": [],
        "alignment_ratio": 0.25,
        "fit_reason": "Only one of four expected slots aligns with the observed picture.",
        "missing_reason": "No expected slots are missing from the observed picture.",
        "notes": [],
    }

    normalized = _normalize_generated_payload(generated_payload, shell)
    validated = validate_kernel_output_v1(normalized)

    assert validated.judgment == "expected_state_misaligned"
    assert validated.confidence == 0.6375
    assert validated.reasons[0] == "Only one of four expected slots aligns with the observed picture."
