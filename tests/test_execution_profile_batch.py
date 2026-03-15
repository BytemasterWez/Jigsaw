from __future__ import annotations

import json
from pathlib import Path

from jigsaw.lanes.real_case_lane.execute_profile_batch import (
    DEFAULT_PROFILE,
    load_execution_profile,
    run_profile_batch,
)


def test_execution_profile_can_load() -> None:
    profile = load_execution_profile(DEFAULT_PROFILE)

    assert profile["profile_name"] == "remote_workflow_v1b"
    assert profile["selection"]["primary_case_limit"] >= 5
    assert profile["validation"]["require_arbiter_response"] is True


def test_calibrated_execution_profile_can_load() -> None:
    profile = load_execution_profile("remote_workflow_v1b")

    assert profile["profile_name"] == "remote_workflow_v1b"
    assert profile["selection"]["supporting_max_per_cluster"] == 1
    assert profile["shaping"]["require_primary_signal_anchor"] is True
    assert profile["kernel_engines"]["observed_state"] == "deterministic"


def test_execution_profile_batch_generates_summary(tmp_path: Path) -> None:
    output_root = tmp_path / "execution_profile_batch"
    summary = run_profile_batch(case_limit=2, output_root_override=output_root)

    assert summary["cases_run"] == 2
    assert (output_root / "summary.json").exists()
    assert (output_root / "SUMMARY.md").exists()

    with (output_root / "summary.json").open("r", encoding="utf-8") as handle:
        saved = json.load(handle)

    assert saved["profile_name"] == "remote_workflow_v1b"
    assert len(saved["cases"]) == 2
