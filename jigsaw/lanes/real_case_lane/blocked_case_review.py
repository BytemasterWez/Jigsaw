from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from jigsaw.config import resolve_workspace_path
from jigsaw.controller import validate_case_state_v1
from jigsaw.engines.watchdog import validate_kernel_watchdog_result_v1
from jigsaw.controller.watchdog_override_manager import validate_watchdog_override_record_v1


REPO_ROOT = Path(__file__).resolve().parents[3]
BLOCKED_CASE_REVIEW_PACKET_SCHEMA_PATH = REPO_ROOT / "contracts" / "blocked_case_review_packet" / "v1.json"
DEFAULT_WORKSPACE = "local"
DEFAULT_LIFECYCLE_ROOT = resolve_workspace_path("lifecycle_root", DEFAULT_WORKSPACE)
DEFAULT_QUEUE_OUTPUT_ROOT = resolve_workspace_path("blocked_review_root", DEFAULT_WORKSPACE)
DEFAULT_PACKET_OUTPUT_ROOT = DEFAULT_QUEUE_OUTPUT_ROOT / "packets"
BLOCKED_REASONS = {
    "watchdog_fail",
    "watchdog_warn",
    "watchdog_manual_review_deferred",
}


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


def _load_schema(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_blocked_case_review_packet_v1(payload: dict[str, Any]) -> dict[str, Any]:
    Draft202012Validator(_load_schema(BLOCKED_CASE_REVIEW_PACKET_SCHEMA_PATH)).validate(payload)
    return payload


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _days_since(value: str | None, now: str) -> int:
    event_time = _parse_timestamp(value)
    now_time = _parse_timestamp(now)
    if event_time is None or now_time is None:
        return 0
    return max(0, int((now_time - event_time).total_seconds() // 86400))


def _blocked_status(case_state: Any) -> str:
    if case_state.latest_reopen_reason == "watchdog_manual_review_deferred":
        return "watchdog_deferred"
    if case_state.latest_reopen_reason == "watchdog_warn":
        return "watchdog_manual_review"
    return "blocked"


def _priority_hint(case_state: Any, watchdog_result: Any | None) -> str:
    if watchdog_result is not None and watchdog_result.verdict == "fail":
        return "urgent"
    if case_state.latest_reopen_reason == "watchdog_manual_review_deferred":
        return "pending_manual_review"
    return "review_soon"


def _case_summary_ref(case_dir: Path) -> str | None:
    summary_path = case_dir / "case_summary.json"
    if summary_path.exists():
        return str(summary_path)
    return None


def _evidence_refs(case_dir: Path) -> list[str]:
    refs: list[str] = []
    case_input_path = case_dir / "case_input.json"
    if case_input_path.exists():
        payload = _load_json(case_input_path)
        for evidence in payload.get("evidence", []):
            evidence_id = evidence.get("evidence_id")
            if isinstance(evidence_id, str):
                refs.append(evidence_id)
    gc_context_path = case_dir / "gc_context.json"
    if gc_context_path.exists():
        payload = _load_json(gc_context_path)
        primary_item_id = payload.get("primary_item_id")
        if primary_item_id is not None:
            refs.append(f"gc:item:{primary_item_id}")
        for item_id in payload.get("related_item_ids", []):
            refs.append(f"gc:item:{item_id}")
    return refs


def _watchdog_event_refs(case_dir: Path, watchdog_result: Any | None) -> list[str]:
    refs: list[str] = []
    if watchdog_result is not None:
        refs.append(str(case_dir / "kernel_watchdog_result.json"))
        refs.append(watchdog_result.exchange_id)
    return refs


def _override_history_refs(case_dir: Path) -> list[str]:
    refs: list[str] = []
    override_path = case_dir / "watchdog_override_record.json"
    if override_path.exists():
        validate_watchdog_override_record_v1(_load_json(override_path))
        refs.append(str(override_path))
    return refs


def _recommended_actions() -> list[str]:
    return [
        "override_and_continue",
        "close_as_invalid",
        "defer_for_manual_review",
    ]


def _find_case_dir(case_id: str, lifecycle_root: Path) -> Path:
    for candidate in sorted(path for path in lifecycle_root.iterdir() if path.is_dir()):
        case_state_path = candidate / "case_state.json"
        if not case_state_path.exists():
            continue
        case_state = validate_case_state_v1(_load_json(case_state_path))
        if case_state.case_id == case_id:
            return candidate
    raise FileNotFoundError(f"Case {case_id} was not found under {lifecycle_root}")


def is_blocked_case(case_dir: Path) -> bool:
    case_state_path = case_dir / "case_state.json"
    if not case_state_path.exists():
        return False
    case_state = validate_case_state_v1(_load_json(case_state_path))
    return case_state.latest_reopen_reason in BLOCKED_REASONS


def build_blocked_case_review_packet(
    *,
    case_id: str,
    lifecycle_root: str | Path = DEFAULT_LIFECYCLE_ROOT,
    output_root: str | Path = DEFAULT_PACKET_OUTPUT_ROOT,
    generated_at: str = "2026-03-16T17:00:00Z",
) -> dict[str, Any]:
    lifecycle_path = Path(lifecycle_root)
    output_path = Path(output_root)
    case_dir = _find_case_dir(case_id, lifecycle_path)
    case_state = validate_case_state_v1(_load_json(case_dir / "case_state.json"))
    if case_state.latest_reopen_reason not in BLOCKED_REASONS:
        raise ValueError(f"Case {case_id} is not currently in a blocked watchdog state.")

    watchdog_result = None
    watchdog_result_path = case_dir / "kernel_watchdog_result.json"
    if watchdog_result_path.exists():
        watchdog_result = validate_kernel_watchdog_result_v1(_load_json(watchdog_result_path))

    packet = validate_blocked_case_review_packet_v1(
        {
            "contract": "blocked_case_review_packet",
            "version": "v1",
            "case_id": case_state.case_id,
            "generated_at": generated_at,
            "case_state": case_state.model_dump(mode="python"),
            "blocked_status": _blocked_status(case_state),
            "blocked_reason": case_state.latest_reopen_reason,
            "watchdog_status": (
                watchdog_result.model_dump(mode="python") if watchdog_result is not None else {"verdict": "unknown"}
            ),
            "reopen_flag": case_state.reopen_required,
            "latest_case_summary_ref": _case_summary_ref(case_dir),
            "latest_evidence_refs": _evidence_refs(case_dir),
            "latest_watchdog_event_refs": _watchdog_event_refs(case_dir, watchdog_result),
            "override_history_refs": _override_history_refs(case_dir),
            "recommended_operator_actions": _recommended_actions(),
            "days_blocked": _days_since(case_state.last_reviewed_at, generated_at),
            "last_meaningful_update_at": case_state.last_reviewed_at,
            "priority_hint": _priority_hint(case_state, watchdog_result),
        }
    )

    packet_dir = output_path / case_state.case_id.replace(":", "_")
    _dump_json(packet_dir / "blocked_case_review_packet.json", packet)
    _write_text(packet_dir / "BLOCKED_CASE_REVIEW_PACKET.md", blocked_case_review_packet_markdown(packet))
    return {
        "case_id": case_state.case_id,
        "packet_json_path": str(packet_dir / "blocked_case_review_packet.json"),
        "packet_path": str(packet_dir / "BLOCKED_CASE_REVIEW_PACKET.md"),
        "status": "success",
    }


def blocked_case_review_packet_markdown(packet: dict[str, Any]) -> str:
    lines = [
        "# Blocked Case Review Packet",
        "",
        f"- case_id: `{packet['case_id']}`",
        f"- blocked_status: `{packet['blocked_status']}`",
        f"- blocked_reason: `{packet['blocked_reason']}`",
        f"- reopen_flag: `{packet['reopen_flag']}`",
        f"- priority_hint: `{packet['priority_hint']}`",
        f"- generated_at: `{packet['generated_at']}`",
        "",
        "## Watchdog",
        "",
        f"- verdict: `{packet['watchdog_status'].get('verdict', 'unknown')}`",
        f"- exchange_id: `{packet['watchdog_status'].get('exchange_id', 'none')}`",
        f"- kernel_name: `{packet['watchdog_status'].get('kernel_name', 'unknown')}`",
        f"- reasons: `{packet['watchdog_status'].get('reasons', [])}`",
        "",
        "## References",
        "",
        f"- latest_case_summary_ref: `{packet['latest_case_summary_ref']}`",
        f"- latest_evidence_refs: `{packet['latest_evidence_refs']}`",
        f"- latest_watchdog_event_refs: `{packet['latest_watchdog_event_refs']}`",
        f"- override_history_refs: `{packet['override_history_refs']}`",
        "",
        "## Recommended operator actions",
        "",
    ]
    lines.extend(f"- `{action}`" for action in packet["recommended_operator_actions"])
    lines.append("")
    return "\n".join(lines)


def build_blocked_case_queue(
    *,
    lifecycle_root: str | Path = DEFAULT_LIFECYCLE_ROOT,
    output_root: str | Path = DEFAULT_QUEUE_OUTPUT_ROOT,
    generated_at: str = "2026-03-16T17:00:00Z",
) -> dict[str, Any]:
    lifecycle_path = Path(lifecycle_root)
    output_path = Path(output_root)
    output_path.mkdir(parents=True, exist_ok=True)

    entries: list[dict[str, Any]] = []
    for case_dir in sorted(path for path in lifecycle_path.iterdir() if path.is_dir()):
        if not is_blocked_case(case_dir):
            continue
        case_state = validate_case_state_v1(_load_json(case_dir / "case_state.json"))
        watchdog_result = None
        watchdog_result_path = case_dir / "kernel_watchdog_result.json"
        if watchdog_result_path.exists():
            watchdog_result = validate_kernel_watchdog_result_v1(_load_json(watchdog_result_path))
        queue_reason = case_state.latest_reopen_reason
        entry = {
            "case_id": case_state.case_id,
            "queue_reason": queue_reason,
            "blocked_reason": case_state.latest_reopen_reason,
            "since": case_state.last_reviewed_at,
            "last_update_at": case_state.last_reviewed_at,
            "available_actions": _recommended_actions(),
            "priority_hint": _priority_hint(case_state, watchdog_result),
        }
        entries.append(entry)

    entries.sort(key=lambda item: (0 if item["priority_hint"] == "urgent" else 1, item["case_id"]))
    queue_payload = {
        "generated_at": generated_at,
        "blocked_cases": entries,
        "count": len(entries),
    }
    _dump_json(output_path / "blocked_case_queue.json", queue_payload)
    _write_text(output_path / "BLOCKED_CASE_QUEUE.md", blocked_case_queue_markdown(queue_payload))
    return {
        "count": len(entries),
        "queue_json_path": str(output_path / "blocked_case_queue.json"),
        "queue_path": str(output_path / "BLOCKED_CASE_QUEUE.md"),
        "status": "success",
    }


def blocked_case_queue_markdown(queue_payload: dict[str, Any]) -> str:
    lines = [
        "# Blocked Case Queue",
        "",
        f"- blocked_cases: `{queue_payload['count']}`",
        "",
        "| Case | Queue reason | Since | Priority | Available actions |",
        "| --- | --- | --- | --- | --- |",
    ]
    for entry in queue_payload["blocked_cases"]:
        lines.append(
            f"| `{entry['case_id']}` | `{entry['queue_reason']}` | `{entry['since']}` | "
            f"`{entry['priority_hint']}` | `{entry['available_actions']}` |"
        )
    lines.append("")
    return "\n".join(lines)
