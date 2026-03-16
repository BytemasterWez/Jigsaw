from __future__ import annotations

import argparse
import json

from jigsaw.config import resolve_workspace_path
from jigsaw.lanes.real_case_lane.blocked_case_review import build_blocked_case_queue


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="List blocked watchdog cases from a lifecycle store.")
    parser.add_argument("--workspace", default="local")
    parser.add_argument("--lifecycle-root", default=None)
    parser.add_argument("--output-root", default=None)
    parser.add_argument("--generated-at", default="2026-03-16T17:00:00Z")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    kwargs = {"generated_at": args.generated_at}
    kwargs["lifecycle_root"] = args.lifecycle_root or str(resolve_workspace_path("lifecycle_root", args.workspace))
    kwargs["output_root"] = args.output_root or str(resolve_workspace_path("blocked_review_root", args.workspace))
    print(json.dumps(build_blocked_case_queue(**kwargs), indent=2))
