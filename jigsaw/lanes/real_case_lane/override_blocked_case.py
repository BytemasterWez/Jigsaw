from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Literal

from jigsaw.controller import (
    apply_watchdog_override,
    build_watchdog_override_record,
    validate_case_state_v1,
    validate_watchdog_override_record_v1,
)
from jigsaw.engines.watchdog import validate_kernel_watchdog_result_v1
from jigsaw.lanes.real_case_lane.generate_case_timeline import DEFAULT_OUTPUT_ROOT as DEFAULT_TIMELINE_ROOT
from jigsaw.lanes.real_case_lane.generate_case_timeline import generate_case_timeline


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_LIFECYCLE_ROOT = REPO_ROOT / "validation" / "case_lifecycle"
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "validation" / "blocked_case_reviews"
BlockedDecision = Literal["override_and_continue", "close_as_invalid", "defer_for_manual_review"]


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _find_case_dir(case_id: str, lifecycle_root: Path) -> Path:
    for candidate in sorted(path for path in lifecycle_root.iterdir() if path.is_dir()):
        case_state_path = candidate / "case_state.json"
        if not case_state_path.exists():
            continue
        case_state = validate_case_state_v1(_load_json(case_state_path))
        if case_state.case_id == case_id:
            return candidate
    raise FileNotFoundError(f"Case {case_id} was not found under {lifecycle_root}")


def _override_markdown(payload: dict[str, Any]) -> str:
    return (
        "# Watchdog Override Decision\n\n"
        f"- case_id: `{payload['case_id']}`\n"
        f"- decision: `{payload['decision']}`\n"
        f"- watchdog_verdict: `{payload['watchdog_verdict']}`\n"
        f"- exchange_id: `{payload['exchange_id']}`\n"
        f"- timestamp: `{payload['timestamp']}`\n"
        f"- timeline_path: `{payload['timeline_path']}`\n"
        f"- case_state_path: `{payload['case_state_path']}`\n"
        f"- override_record_path: `{payload['override_record_path']}`\n"
        f"- reason: `{payload['override_reason']}`\n"
        f"- overridden_by: `{payload['overridden_by']}`\n"
    )


def override_blocked_case(
    *,
    case_id: str,
    decision: BlockedDecision,
    override_reason: str,
    overridden_by: str,
    lifecycle_root: str | Path = DEFAULT_LIFECYCLE_ROOT,
    timeline_root: str | Path = DEFAULT_TIMELINE_ROOT,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    timestamp: str = "2026-03-16T16:30:00Z",
) -> dict[str, Any]:
    lifecycle_path = Path(lifecycle_root)
    timeline_path = Path(timeline_root)
    output_path = Path(output_root)
    case_dir = _find_case_dir(case_id, lifecycle_path)

    case_state = validate_case_state_v1(_load_json(case_dir / "case_state.json"))
    if case_state.latest_reopen_reason not in {"watchdog_warn", "watchdog_fail"}:
        raise ValueError(f"Case {case_id} is not currently flagged by the watchdog.")
    watchdog_result_path = case_dir / "kernel_watchdog_result.json"
    if not watchdog_result_path.exists():
        raise FileNotFoundError(f"{watchdog_result_path} is required for blocked-case override flow.")
    watchdog_result = validate_kernel_watchdog_result_v1(_load_json(watchdog_result_path))

    timeline_result = generate_case_timeline(case_dir=case_dir, output_root=timeline_path)
    override_record = build_watchdog_override_record(
        case_state,
        exchange_id=watchdog_result.exchange_id,
        watchdog_verdict=watchdog_result.verdict,
        operator_decision=decision,
        override_reason=override_reason,
        overridden_by=overridden_by,
        timestamp=timestamp,
    )
    updated_case_state = apply_watchdog_override(case_state, override_record)

    _dump_json(case_dir / "case_state.json", updated_case_state.model_dump(mode="python"))
    _dump_json(case_dir / "watchdog_override_record.json", override_record.model_dump(mode="python"))

    case_review_dir = output_path / case_id.replace(":", "_")
    review_payload = {
        "case_id": case_id,
        "decision": decision,
        "watchdog_verdict": watchdog_result.verdict,
        "exchange_id": watchdog_result.exchange_id,
        "timestamp": timestamp,
        "timeline_path": timeline_result["timeline_path"],
        "case_state_path": str(case_dir / "case_state.json"),
        "override_record_path": str(case_dir / "watchdog_override_record.json"),
        "override_reason": override_reason,
        "overridden_by": overridden_by,
        "status": "success",
    }
    _dump_json(case_review_dir / "watchdog_override_decision.json", review_payload)
    _write_text(case_review_dir / "WATCHDOG_OVERRIDE_DECISION.md", _override_markdown(review_payload))
    return review_payload


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Record an operator override for a watchdog-flagged case.")
    parser.add_argument("--case-id", required=True)
    parser.add_argument(
        "--decision",
        required=True,
        choices=["override_and_continue", "close_as_invalid", "defer_for_manual_review"],
    )
    parser.add_argument("--override-reason", required=True)
    parser.add_argument("--overridden-by", default="human_operator")
    parser.add_argument("--lifecycle-root", default=str(DEFAULT_LIFECYCLE_ROOT))
    parser.add_argument("--timeline-root", default=str(DEFAULT_TIMELINE_ROOT))
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--timestamp", default="2026-03-16T16:30:00Z")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    result = override_blocked_case(
        case_id=args.case_id,
        decision=args.decision,
        override_reason=args.override_reason,
        overridden_by=args.overridden_by,
        lifecycle_root=args.lifecycle_root,
        timeline_root=args.timeline_root,
        output_root=args.output_root,
        timestamp=args.timestamp,
    )
    print(json.dumps(result, indent=2))
