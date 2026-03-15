from __future__ import annotations

from pathlib import Path

from jigsaw.lanes.real_case_lane.generate_profile_comparison import build_profile_comparison_markdown


def test_profile_comparison_markdown_includes_totals_and_flips() -> None:
    baseline = {
        "profile_name": "remote_workflow_v1b",
        "promoted": 2,
        "watchlist": 1,
        "rejected": 0,
        "cases": [
            {
                "primary_item_id": 8,
                "arbiter_judgement": "promoted",
                "bundle_confidence": 0.72,
                "arbiter_fit_score": 0.8,
                "kernel_runtime": {},
            },
            {
                "primary_item_id": 9,
                "arbiter_judgement": "watchlist",
                "bundle_confidence": 0.63,
                "arbiter_fit_score": 0.58,
                "kernel_runtime": {},
            },
        ],
    }
    experiment = {
        "profile_name": "remote_workflow_localmix_v1",
        "promoted": 1,
        "watchlist": 2,
        "rejected": 0,
        "cases": [
            {
                "primary_item_id": 8,
                "arbiter_judgement": "promoted",
                "bundle_confidence": 0.71,
                "arbiter_fit_score": 0.79,
                "kernel_runtime": {
                    "observed_state": {"retries_used": 0},
                    "expected_state": {"retries_used": 1},
                },
            },
            {
                "primary_item_id": 9,
                "arbiter_judgement": "promoted",
                "bundle_confidence": 0.7,
                "arbiter_fit_score": 0.74,
                "kernel_runtime": {
                    "observed_state": {"retries_used": 0},
                    "expected_state": {"retries_used": 0},
                },
            },
        ],
    }

    markdown = build_profile_comparison_markdown(baseline, experiment)

    assert "# Execution Profile Comparison" in markdown
    assert "| Promoted | `2` | `1` |" in markdown
    assert "gc:item:9: watchlist -> promoted" in markdown
    assert "Total LM retries used | `0` | `1` |" in markdown
