from __future__ import annotations

import json
from pathlib import Path

from jigsaw.lanes.artifact_lane.transforms import (
    artifact_to_extraction,
    chunks_to_judgment_request,
    extraction_to_chunks,
)
from jigsaw.lanes.artifact_lane.validators import (
    validate_artifact_v1,
    validate_chunk_v1,
    validate_extraction_v1,
    validate_judgment_request_v1,
)


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "examples" / "inputs"
FIXED_GENERATED_AT = "2026-03-14T12:00:00Z"


def load_example_artifact() -> dict:
    with (FIXTURES_DIR / "sample_gc_artifact.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_artifact_to_extraction_preserves_linkage() -> None:
    artifact = validate_artifact_v1(load_example_artifact())
    extraction = artifact_to_extraction(
        artifact,
        pipeline_run_id="artifact-lane-first-slice",
        generated_at=FIXED_GENERATED_AT,
    )
    validated = validate_extraction_v1(extraction.model_dump(mode="python"))

    assert validated.artifact_id == artifact.artifact_id
    assert validated.extracted_text == artifact.raw_text
    assert validated.provenance.source_artifact_id == artifact.artifact_id


def test_extraction_to_chunks_creates_sequenced_chunks() -> None:
    artifact = validate_artifact_v1(load_example_artifact())
    extraction = artifact_to_extraction(
        artifact,
        pipeline_run_id="artifact-lane-first-slice",
        generated_at=FIXED_GENERATED_AT,
    )
    chunks = extraction_to_chunks(
        extraction,
        artifact=artifact,
        pipeline_run_id="artifact-lane-first-slice",
        max_chars=120,
        generated_at=FIXED_GENERATED_AT,
    )

    assert len(chunks) >= 2
    assert [chunk.sequence for chunk in chunks] == list(range(1, len(chunks) + 1))
    for chunk in chunks:
        validated = validate_chunk_v1(chunk.model_dump(mode="python"))
        assert len(validated.text) <= 120 or "\n\n" not in validated.text
        assert validated.provenance.source_extraction_id == extraction.extraction_id


def test_chunks_to_judgment_request_preserves_provenance() -> None:
    artifact = validate_artifact_v1(load_example_artifact())
    extraction = artifact_to_extraction(
        artifact,
        pipeline_run_id="artifact-lane-first-slice",
        generated_at=FIXED_GENERATED_AT,
    )
    chunks = extraction_to_chunks(
        extraction,
        artifact=artifact,
        pipeline_run_id="artifact-lane-first-slice",
        generated_at=FIXED_GENERATED_AT,
    )
    request = chunks_to_judgment_request(
        artifact,
        chunks,
        pipeline_run_id="artifact-lane-first-slice",
        generated_at=FIXED_GENERATED_AT,
    )
    validated = validate_judgment_request_v1(request.model_dump(mode="python"))

    assert validated.artifact_id == artifact.artifact_id
    assert len(validated.chunks) == len(chunks)
    assert validated.evidence.provenance["artifact_id"] == artifact.artifact_id

