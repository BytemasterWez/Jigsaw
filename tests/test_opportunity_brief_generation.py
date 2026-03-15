from __future__ import annotations

from pathlib import Path

from jigsaw.lanes.real_case_lane.execute_profile_batch import run_profile_batch
from jigsaw.lanes.real_case_lane.generate_opportunity_briefs import generate_opportunity_briefs


def test_generate_opportunity_briefs_after_profile_batch() -> None:
    run_profile_batch("remote_workflow_v1b")
    result = generate_opportunity_briefs()

    assert result["status"] == "success"
    assert result["cases"] == 5

    brief_root = Path(result["generated_files"][0]).parent
    assert (brief_root / "README.md").exists()
    assert len(result["generated_files"]) == 5
    assert len(result["generated_html_files"]) == 5
    assert Path(result["generated_html_files"][0]).exists()
