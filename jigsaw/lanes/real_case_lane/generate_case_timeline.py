from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jigsaw.config import resolve_workspace_path
from jigsaw.controller import (
    validate_action_record_v1,
    validate_case_relevance_signal_v1,
    validate_case_state_v1,
    validate_outcome_event_v1,
)
from jigsaw.engines.watchdog import validate_kernel_watchdog_result_v1
from jigsaw.lanes.kernel_lane.arbiter_exchange import validate_arbiter_exchange_v1


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_WORKSPACE = "local"
DEFAULT_LIFECYCLE_ROOT = resolve_workspace_path("lifecycle_root", DEFAULT_WORKSPACE)
DEFAULT_OUTPUT_ROOT = resolve_workspace_path("timeline_root", DEFAULT_WORKSPACE)


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


def _event(
    *,
    timestamp: str,
    event_type: str,
    summary: str,
    source_object: str,
    confidence_before: float | None = None,
    confidence_after: float | None = None,
) -> dict[str, Any]:
    return {
        "timestamp": timestamp,
        "event_type": event_type,
        "summary": summary,
        "confidence_before": confidence_before,
        "confidence_after": confidence_after,
        "source_object": source_object,
    }


def _reopen_timestamp(case_state: Any, outcome_event: Any | None, relevance_signal: Any | None, watchdog_result: Any | None) -> str:
    if case_state.latest_reopen_reason in {"watchdog_warn", "watchdog_fail"} and watchdog_result is not None:
        return watchdog_result.timestamp
    if case_state.latest_reopen_reason in {"new_relevant_material_detected", "relevant_material_attached"} and relevance_signal is not None:
        return relevance_signal.timestamp
    if case_state.latest_reopen_reason == "outcome_requires_review" and outcome_event is not None:
        return outcome_event.timestamp
    return case_state.last_reviewed_at


def _timeline_markdown(case_id: str, events: list[dict[str, Any]], latest_status: dict[str, Any]) -> str:
    lines = [
        "# Case Timeline",
        "",
        f"- case_id: `{case_id}`",
        f"- latest_status: `{latest_status['current_status']}`",
        f"- latest_decision: `{latest_status['latest_decision']}`",
        f"- confidence_current: `{latest_status['confidence_current']}`",
        f"- confidence_trajectory: `{latest_status['confidence_trajectory']}`",
        f"- latest_reopen_reason: `{latest_status['latest_reopen_reason']}`",
        "",
        "## Events",
        "",
        "| Timestamp | Type | Summary | Confidence | Source |",
        "| --- | --- | --- | --- | --- |",
    ]
    for event in events:
        if event["confidence_before"] is not None or event["confidence_after"] is not None:
            confidence_text = f"`{event['confidence_before']} -> {event['confidence_after']}`"
        else:
            confidence_text = "`-`"
        lines.append(
            f"| `{event['timestamp']}` | `{event['event_type']}` | {event['summary']} | {confidence_text} | `{event['source_object']}` |"
        )
    lines.append("")
    return "\n".join(lines)


def generate_case_timeline(
    *,
    case_dir: str | Path,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
) -> dict[str, Any]:
    case_path = Path(case_dir)
    output_path = Path(output_root)

    case_state = validate_case_state_v1(_load_json(case_path / "case_state.json"))
    action_record = validate_action_record_v1(_load_json(case_path / "action_record.json")) if (case_path / "action_record.json").exists() else None
    outcome_event = validate_outcome_event_v1(_load_json(case_path / "outcome_event.json")) if (case_path / "outcome_event.json").exists() else None
    relevance_signal = (
        validate_case_relevance_signal_v1(_load_json(case_path / "case_relevance_signal.json"))
        if (case_path / "case_relevance_signal.json").exists()
        else None
    )
    watchdog_result = (
        validate_kernel_watchdog_result_v1(_load_json(case_path / "kernel_watchdog_result.json"))
        if (case_path / "kernel_watchdog_result.json").exists()
        else None
    )
    arbiter_exchange = (
        validate_arbiter_exchange_v1(_load_json(case_path / "arbiter_exchange.json"))
        if (case_path / "arbiter_exchange.json").exists()
        else None
    )

    first_timestamp = (
        arbiter_exchange.timestamp
        if arbiter_exchange is not None
        else action_record.timestamp
        if action_record is not None
        else case_state.last_reviewed_at
    )
    events: list[dict[str, Any]] = [
        _event(
            timestamp=first_timestamp,
            event_type="case_created",
            summary=f"Case state opened for `{case_state.case_id}`.",
            source_object="case_state",
        )
    ]

    if arbiter_exchange is not None:
        judgment = arbiter_exchange.received_packet.get("judgement", case_state.latest_decision)
        events.append(
            _event(
                timestamp=arbiter_exchange.timestamp,
                event_type="forward_pass_decision",
                summary=f"Forward pass returned `{judgment}` for the case.",
                confidence_after=case_state.confidence_current if outcome_event is None else None,
                source_object="arbiter_exchange",
            )
        )

    if action_record is not None:
        events.append(
            _event(
                timestamp=action_record.timestamp,
                event_type="action_recorded",
                summary=f"Recorded `{action_record.action_taken}` after recommended action `{action_record.recommended_action}`.",
                source_object="action_record",
            )
        )

    if outcome_event is not None:
        confidence_before = round(case_state.confidence_current - outcome_event.effect_on_confidence, 4)
        confidence_after = case_state.confidence_current
        events.append(
            _event(
                timestamp=outcome_event.timestamp,
                event_type="outcome_recorded",
                summary=f"Outcome `{outcome_event.observed_outcome}` was recorded.",
                source_object="outcome_event",
            )
        )
        events.append(
            _event(
                timestamp=outcome_event.timestamp,
                event_type="confidence_revised",
                summary=f"Confidence revised after `{outcome_event.observed_outcome}`.",
                confidence_before=confidence_before,
                confidence_after=confidence_after,
                source_object="case_state",
            )
        )

    if relevance_signal is not None:
        events.append(
            _event(
                timestamp=relevance_signal.timestamp,
                event_type="relevance_signal",
                summary=f"New material produced `{relevance_signal.recommended_effect}`.",
                source_object="case_relevance_signal",
            )
        )

    if watchdog_result is not None and watchdog_result.verdict != "pass":
        events.append(
            _event(
                timestamp=watchdog_result.timestamp,
                event_type=f"watchdog_{watchdog_result.verdict}",
                summary=f"Kernel watchdog returned `{watchdog_result.verdict}` for `{watchdog_result.kernel_name}`.",
                source_object="kernel_watchdog_result",
            )
        )

    if case_state.latest_reopen_reason is not None:
        events.append(
            _event(
                timestamp=_reopen_timestamp(case_state, outcome_event, relevance_signal, watchdog_result),
                event_type="reopen_flagged",
                summary=f"Case marked for review due to `{case_state.latest_reopen_reason}`.",
                source_object="case_state",
            )
        )

    events.append(
        _event(
            timestamp=case_state.last_reviewed_at,
            event_type="latest_status",
            summary=f"Latest status is `{case_state.current_status}` with decision `{case_state.latest_decision}`.",
            confidence_after=case_state.confidence_current,
            source_object="case_state",
        )
    )
    events.sort(key=lambda item: (item["timestamp"], item["event_type"]))

    timeline_payload = {
        "case_id": case_state.case_id,
        "events": events,
        "latest_status": {
            "current_status": case_state.current_status,
            "latest_decision": case_state.latest_decision,
            "confidence_current": case_state.confidence_current,
            "confidence_trajectory": case_state.confidence_trajectory,
            "latest_reopen_reason": case_state.latest_reopen_reason,
        },
    }

    case_output_dir = output_path / case_state.case_id.replace(":", "_")
    _dump_json(case_output_dir / "case_timeline.json", timeline_payload)
    _write_text(
        case_output_dir / "CASE_TIMELINE.md",
        _timeline_markdown(case_state.case_id, events, timeline_payload["latest_status"]),
    )
    return {
        "case_id": case_state.case_id,
        "timeline_path": str(case_output_dir / "CASE_TIMELINE.md"),
        "timeline_json_path": str(case_output_dir / "case_timeline.json"),
        "status": "success",
    }


if __name__ == "__main__":
    default_case_dir = next(path for path in sorted(DEFAULT_LIFECYCLE_ROOT.iterdir()) if path.is_dir())
    print(json.dumps(generate_case_timeline(case_dir=default_case_dir), indent=2))
