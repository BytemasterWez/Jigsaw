from __future__ import annotations

from pathlib import Path

from jigsaw.lanes.real_case_lane.execute_profile_batch import run_profile_batch
from jigsaw.lanes.real_case_lane.generate_opportunity_briefs import generate_opportunity_briefs
from jigsaw.lanes.real_case_lane.generate_summary_report import generate_summary_report


def test_generate_summary_report_after_briefs() -> None:
    run_profile_batch("remote_workflow_v1b")
    generate_opportunity_briefs()
    result = generate_summary_report()

    assert result["status"] == "success"
    assert result["cases"] == 5

    markdown_report = Path(result["markdown_report"])
    html_report = Path(result["html_report"])
    readme = Path(result["readme"])

    assert markdown_report.exists()
    assert html_report.exists()
    assert readme.exists()

    markdown_text = markdown_report.read_text(encoding="utf-8")
    assert "Remote Workflow Summary Report" in markdown_text
    assert "What this batch suggests" in markdown_text
    assert "| Case | Title | Outcome | Confidence | Next step |" in markdown_text
