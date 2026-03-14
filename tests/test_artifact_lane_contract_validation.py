from __future__ import annotations

import json
from pathlib import Path

import pytest

from jigsaw.lanes.artifact_lane.validators import validate_artifact_v1, validate_judgment_request_v1


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "examples" / "inputs"


def load_example_artifact() -> dict:
    with (FIXTURES_DIR / "sample_gc_artifact.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_valid_artifact_payload_is_accepted() -> None:
    artifact = validate_artifact_v1(load_example_artifact())
    assert artifact.contract == "artifact"
    assert artifact.version == "v1"


def test_artifact_payload_missing_provenance_is_rejected() -> None:
    payload = load_example_artifact()
    del payload["provenance"]

    with pytest.raises(Exception):
        validate_artifact_v1(payload)


def test_judgment_request_requires_chunks() -> None:
    payload = {
        "contract": "judgment_request",
        "version": "v1",
        "request_id": "req:test",
        "artifact_id": "art:test",
        "subject": {"title": "example", "type": "document"},
        "context": {
            "source_system": "garbage_collector",
            "source_type": "note",
            "analysis_profile": "default",
        },
        "chunks": [],
        "evidence": {
            "provenance": {"artifact_id": "art:test"},
            "hash_sha256": "abc123",
        },
        "metadata": {
            "object_id": "req:test",
            "schema_version": "v1",
            "created_at": "2026-03-14T12:00:00Z",
            "updated_at": "2026-03-14T12:00:00Z",
            "source_system": "garbage_collector",
            "pipeline_run_id": "artifact-lane-first-slice",
            "confidence": 1.0,
            "tags": [],
            "lineage": [],
        },
    }

    with pytest.raises(Exception):
        validate_judgment_request_v1(payload)

