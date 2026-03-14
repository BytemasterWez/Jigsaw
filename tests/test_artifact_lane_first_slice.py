from __future__ import annotations

import json
from pathlib import Path

from jigsaw.lanes.artifact_lane.execute_first_slice import OUTPUT_DIR, run_first_slice


def test_first_slice_runner_generates_expected_outputs() -> None:
    result = run_first_slice()

    assert result["status"] == "success"
    assert result["chunk_count"] >= 1

    expected_files = [
        "validated_artifact.json",
        "extraction.json",
        "chunks.json",
        "judgment_request.json",
        "arbiter_preview.json",
        "run_log.json",
    ]
    for name in expected_files:
        assert (OUTPUT_DIR / name).exists()

    with (OUTPUT_DIR / "judgment_request.json").open("r", encoding="utf-8") as handle:
        judgment_request = json.load(handle)

    assert judgment_request["contract"] == "judgment_request"
    assert judgment_request["version"] == "v1"
    assert len(judgment_request["chunks"]) == result["chunk_count"]

