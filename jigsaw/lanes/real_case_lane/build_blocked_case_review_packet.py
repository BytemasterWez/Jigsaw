from __future__ import annotations

import argparse
import json

from jigsaw.config import resolve_workspace_path
from jigsaw.lanes.real_case_lane.blocked_case_review import build_blocked_case_review_packet


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a factual review packet for one blocked case.")
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--workspace", default="local")
    parser.add_argument("--lifecycle-root", default=None)
    parser.add_argument("--output-root", default=None)
    parser.add_argument("--generated-at", default="2026-03-16T17:00:00Z")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    kwargs = {
        "case_id": args.case_id,
        "generated_at": args.generated_at,
        "lifecycle_root": args.lifecycle_root or str(resolve_workspace_path("lifecycle_root", args.workspace)),
        "output_root": args.output_root or str(resolve_workspace_path("blocked_review_root", args.workspace) / "packets"),
    }
    print(json.dumps(build_blocked_case_review_packet(**kwargs), indent=2))
