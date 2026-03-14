from __future__ import annotations

import json
from pathlib import Path

from .arbiter_request_adapter import judgment_request_to_arbiter_preview
from .gc_artifact_adapter import gc_payload_to_artifact_v1
from .transforms import artifact_to_extraction, chunks_to_judgment_request, extraction_to_chunks
from .validators import (
    validate_artifact_v1,
    validate_chunk_v1,
    validate_extraction_v1,
    validate_judgment_request_v1,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
INPUT_PATH = REPO_ROOT / "examples" / "inputs" / "sample_gc_artifact.json"
OUTPUT_DIR = REPO_ROOT / "validation" / "first_slice" / "output"


def _dump_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def run_first_slice() -> dict:
    pipeline_run_id = "artifact-lane-first-slice"
    generated_at = "2026-03-14T12:00:00Z"

    with INPUT_PATH.open("r", encoding="utf-8") as handle:
        source_payload = json.load(handle)

    artifact = gc_payload_to_artifact_v1(source_payload)
    validate_artifact_v1(artifact.model_dump(mode="python"))

    extraction = artifact_to_extraction(artifact, pipeline_run_id=pipeline_run_id, generated_at=generated_at)
    validate_extraction_v1(extraction.model_dump(mode="python"))

    chunks = extraction_to_chunks(
        extraction,
        artifact=artifact,
        pipeline_run_id=pipeline_run_id,
        max_chars=500,
        generated_at=generated_at,
    )
    for chunk in chunks:
        validate_chunk_v1(chunk.model_dump(mode="python"))

    judgment_request = chunks_to_judgment_request(
        artifact,
        chunks,
        pipeline_run_id=pipeline_run_id,
        analysis_profile="default",
        generated_at=generated_at,
    )
    validate_judgment_request_v1(judgment_request.model_dump(mode="python"))

    arbiter_preview = judgment_request_to_arbiter_preview(judgment_request)

    _dump_json(OUTPUT_DIR / "validated_artifact.json", artifact.model_dump(mode="python"))
    _dump_json(OUTPUT_DIR / "extraction.json", extraction.model_dump(mode="python"))
    _dump_json(OUTPUT_DIR / "chunks.json", [chunk.model_dump(mode="python") for chunk in chunks])
    _dump_json(OUTPUT_DIR / "judgment_request.json", judgment_request.model_dump(mode="python"))
    _dump_json(OUTPUT_DIR / "arbiter_preview.json", arbiter_preview)
    _dump_json(
        OUTPUT_DIR / "run_log.json",
        {
            "pipeline_run_id": pipeline_run_id,
            "generated_at": generated_at,
            "input_path": str(INPUT_PATH),
            "output_dir": str(OUTPUT_DIR),
            "artifact_id": artifact.artifact_id,
            "extraction_id": extraction.extraction_id,
            "chunk_count": len(chunks),
            "judgment_request_id": judgment_request.request_id,
            "status": "success",
        },
    )

    return {
        "artifact_id": artifact.artifact_id,
        "extraction_id": extraction.extraction_id,
        "chunk_count": len(chunks),
        "judgment_request_id": judgment_request.request_id,
        "status": "success",
    }


if __name__ == "__main__":
    result = run_first_slice()
    print(json.dumps(result, indent=2))

