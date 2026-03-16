from __future__ import annotations

import json
from pathlib import Path

from jigsaw.config import load_pilot_workspace, resolve_workspace_path
from jigsaw.lanes.real_case_lane.seed_pilot_workspace import seed_pilot_workspace


def test_pilot_workspace_config_loads() -> None:
    workspace = load_pilot_workspace("local")

    assert workspace["workspace_name"] == "pilot_local"
    assert workspace["active_profile"] == "remote_workflow_v1b"


def test_resolve_workspace_path_returns_repo_relative_roots() -> None:
    lifecycle_root = resolve_workspace_path("lifecycle_root", "local")

    assert lifecycle_root.name == "case_lifecycle"
    assert "pilot_local" in str(lifecycle_root)


def test_seed_pilot_workspace_materializes_known_paths() -> None:
    summary = seed_pilot_workspace(workspace="local")

    assert summary["status"] == "success"
    assert Path(summary["lifecycle_root"]).exists()
    assert Path(summary["case_monitor_queue_path"]).exists()
    assert Path(summary["blocked_queue_path"]).exists()
    assert Path(summary["blocked_packet_path"]).exists()

    logs_root = resolve_workspace_path("logs_root", "local")
    seed_summary_path = logs_root / "pilot_workspace_seed_summary.json"
    assert seed_summary_path.exists()

    payload = json.loads(seed_summary_path.read_text(encoding="utf-8"))
    assert payload["workspace"] == "pilot_local"
