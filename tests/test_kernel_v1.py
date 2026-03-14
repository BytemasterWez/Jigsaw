from __future__ import annotations

import json
from pathlib import Path

import pytest

from jigsaw.kernel_v1 import KernelResultV1, kernel_result_to_envelope, validate_kernel_v1_payload


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


def load_fixture(name: str) -> dict:
    with (FIXTURES_DIR / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_valid_fixture_is_accepted_by_jigsaw_kernel_v1_models() -> None:
    payload = load_fixture("kernel_v1_valid_goal_alignment.json")
    validate_kernel_v1_payload(payload)
    model = KernelResultV1.model_validate(payload)

    assert model.engine_name == "goal_alignment"


def test_invalid_fixture_is_rejected_by_jigsaw_kernel_v1_validation() -> None:
    payload = load_fixture("kernel_v1_invalid_missing_confidence.json")

    with pytest.raises(Exception):
        validate_kernel_v1_payload(payload)


def test_kernel_result_is_converted_to_message_envelope() -> None:
    payload = load_fixture("kernel_v1_valid_goal_alignment.json")
    envelope = kernel_result_to_envelope(payload)

    assert envelope.candidate.candidate_id == "gc:item:123"
    assert envelope.scores["kernel_score"] == payload["score"]
    assert envelope.scores["kernel_confidence"] == payload["confidence"]
    assert len(envelope.evidence) == len(payload["evidence"])
    assert envelope.trace[-1].step == "kernel_v1.ingest"
