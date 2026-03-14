from __future__ import annotations

import json
from pathlib import Path

import pytest

from jigsaw.lanes.kernel_lane.validators import validate_kernel_bundle_result_v1, validate_kernel_input_v1


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "examples" / "inputs"


def load_example_input() -> dict:
    with (FIXTURES_DIR / "sample_kernel_input.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_valid_kernel_input_is_accepted() -> None:
    payload = validate_kernel_input_v1(load_example_input())
    assert payload.contract == "kernel_input"


def test_kernel_input_missing_evidence_is_rejected() -> None:
    payload = load_example_input()
    payload["evidence"] = []

    with pytest.raises(Exception):
        validate_kernel_input_v1(payload)


def test_kernel_bundle_result_requires_outputs() -> None:
    payload = {
        "contract": "kernel_bundle_result",
        "version": "v1",
        "bundle_id": "bundle:test",
        "input_id": "kin:test",
        "kernel_outputs": [],
        "composed_summary": {
            "bundle_judgment": "insufficient_evidence",
            "summary": "example"
        },
        "composition_notes": [],
        "metadata": {
            "object_id": "bundle:test",
            "schema_version": "v1",
            "created_at": "2026-03-14T12:00:00Z",
            "updated_at": "2026-03-14T12:00:00Z",
            "source_system": "jigsaw",
            "pipeline_run_id": "kernel-lane-first-bundle",
            "confidence": 0.5,
            "tags": [],
            "lineage": []
        }
    }

    with pytest.raises(Exception):
        validate_kernel_bundle_result_v1(payload)

