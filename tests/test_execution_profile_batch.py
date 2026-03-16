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
    assert profile["controller"]["escalate_if_gaps"] is False
    assert profile["kernel_engines"]["observed_state"] == "deterministic"


def test_localmix_execution_profile_can_load() -> None:
    profile = load_execution_profile("remote_workflow_localmix_v1")

    assert profile["profile_name"] == "remote_workflow_localmix_v1"
    assert profile["kernel_engines"]["observed_state"] == "lmstudio"
    assert profile["kernel_engines"]["expected_state"] == "lmstudio"
    assert profile["kernel_engines"]["contradiction"] == "deterministic"


def test_localmix_calibrated_execution_profile_can_load() -> None:
    profile = load_execution_profile("remote_workflow_localmix_calibrated_v1")

    assert profile["profile_name"] == "remote_workflow_localmix_calibrated_v1"
    assert profile["engine"]["lmstudio"]["observed_state"]["complete_coverage_bias"] is True
    assert profile["engine"]["lmstudio"]["expected_state"]["prefer_aligned_at_threshold"] is True


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
    first_case_dir = output_root / f"case_01_gc_{saved['cases'][0]['primary_item_id']}"
    assert (first_case_dir / "gc_context.json").exists()
    assert (first_case_dir / "hypothesis_state.json").exists()
    assert (first_case_dir / "case_input.json").exists()
    assert (first_case_dir / "kernel_exchanges.json").exists()
    assert (first_case_dir / "kernel_watchdog_results.json").exists()
    assert saved["cases"][0]["controller_next_probe"] == "package_case"
    assert "kernel_runtime" in saved["cases"][0]
