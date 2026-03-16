from __future__ import annotations

import json
from pathlib import Path

from jigsaw.lanes.real_case_lane.seed_lifecycle_demo_case import seed_lifecycle_demo_case


def test_seed_lifecycle_demo_case_writes_end_to_end_proof(tmp_path: Path) -> None:
    result = seed_lifecycle_demo_case(demo_root=tmp_path / "lifecycle_demo")

    assert result["status"] == "success"
    summary_path = Path(tmp_path / "lifecycle_demo" / "summary.json")
    proof_path = Path(tmp_path / "lifecycle_demo" / "LIFECYCLE_DEMO_PROOF.md")
    assert summary_path.exists()
    assert proof_path.exists()

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["case_id"] == "case:hyp:gc:45"
    assert Path(summary["queue_path"]).exists()
    assert Path(summary["timeline_path"]).exists()
    assert Path(summary["reopen_queue_path"]).exists()

    review_now = summary["review_now"]
    rerun = summary["rerun_forward_pass"]
    assert review_now["decision"] == "review_now"
    assert rerun["decision"] == "rerun_forward_pass"
    assert Path(rerun["rerun_outputs_path"]).exists()
    assert (Path(rerun["rerun_outputs_path"]) / "arbiter_response.json").exists()
    assert (Path(rerun["rerun_outputs_path"]) / "kernel_watchdog_results.json").exists()
