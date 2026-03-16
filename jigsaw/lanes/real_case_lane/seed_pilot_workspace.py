from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from jigsaw.config import ensure_workspace_dirs, load_pilot_workspace, resolve_workspace_path
from jigsaw.lanes.real_case_lane.blocked_case_review import build_blocked_case_queue, build_blocked_case_review_packet
from jigsaw.lanes.real_case_lane.generate_case_monitor_queue import generate_case_monitor_queue
from jigsaw.lanes.real_case_lane.generate_case_timeline import generate_case_timeline
from jigsaw.lanes.real_case_lane.generate_reopen_review_packets import generate_reopen_review_packets


REPO_ROOT = Path(__file__).resolve().parents[3]
SOURCE_DEMO_ROOT = REPO_ROOT / "validation" / "lifecycle_demo_case"


def _dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def seed_pilot_workspace(*, workspace: str = "local") -> dict[str, Any]:
    workspace_config = load_pilot_workspace(workspace)
    ensure_workspace_dirs(workspace)

    lifecycle_root = resolve_workspace_path("lifecycle_root", workspace)
    monitor_root = resolve_workspace_path("case_monitor_root", workspace)
    timeline_root = resolve_workspace_path("timeline_root", workspace)
    reopen_review_root = resolve_workspace_path("reopen_review_root", workspace)
    blocked_review_root = resolve_workspace_path("blocked_review_root", workspace)
    logs_root = resolve_workspace_path("logs_root", workspace)

    if lifecycle_root.exists():
        shutil.rmtree(lifecycle_root)
    shutil.copytree(SOURCE_DEMO_ROOT / "case_lifecycle" / "base", lifecycle_root)

    case_dir = next(path for path in sorted(lifecycle_root.iterdir()) if path.is_dir())
    case_id = json.loads((case_dir / "case_state.json").read_text(encoding="utf-8"))["case_id"]

    queue_result = generate_case_monitor_queue(lifecycle_root=lifecycle_root, output_root=monitor_root)
    timeline_result = generate_case_timeline(case_dir=case_dir, output_root=timeline_root)
    reopen_review_result = generate_reopen_review_packets(lifecycle_root=lifecycle_root, output_root=reopen_review_root)
    blocked_queue_result = build_blocked_case_queue(lifecycle_root=lifecycle_root, output_root=blocked_review_root)
    blocked_packet_result = build_blocked_case_review_packet(
        case_id=case_id,
        lifecycle_root=lifecycle_root,
        output_root=blocked_review_root / "packets",
    )

    summary = {
        "workspace": workspace_config["workspace_name"],
        "active_profile": workspace_config["active_profile"],
        "lifecycle_root": str(lifecycle_root),
        "case_monitor_queue_path": queue_result["queue_path"],
        "timeline_path": timeline_result["timeline_path"],
        "reopen_queue_path": reopen_review_result["queue_path"],
        "blocked_queue_path": blocked_queue_result["queue_path"],
        "blocked_packet_path": blocked_packet_result["packet_path"],
        "status": "success",
    }
    _dump_json(logs_root / "pilot_workspace_seed_summary.json", summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(seed_pilot_workspace(), indent=2))
