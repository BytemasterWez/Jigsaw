from __future__ import annotations

import json

from jigsaw.lanes.real_case_lane.execute_remote_workflow_case import OUTPUT_DIR, run_remote_workflow_case


def test_real_case_remote_workflow_runner_generates_outputs() -> None:
    result = run_remote_workflow_case()

    assert result["status"] == "success"
    assert result["arbiter_judgement"] in {"promoted", "watchlist", "rejected"}

    expected_files = [
        "gc_primary_item.json",
        "gc_supporting_items.json",
        "gc_context.json",
        "hypothesis_state.json",
        "case_input.json",
        "artifact.json",
        "extraction.json",
        "chunks.json",
        "judgment_request.json",
        "kernel_input.json",
        "kernel_bundle_result.json",
        "arbiter_request.json",
        "arbiter_response.json",
        "run_log.json",
    ]
    for name in expected_files:
        assert (OUTPUT_DIR / name).exists()

    with (OUTPUT_DIR / "arbiter_response.json").open("r", encoding="utf-8") as handle:
        response = json.load(handle)

    assert response["judgement"] == result["arbiter_judgement"]
    assert result["controller_state"] == "sufficient"
