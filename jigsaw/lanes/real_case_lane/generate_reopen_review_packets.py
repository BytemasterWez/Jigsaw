from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jigsaw.config import resolve_workspace_path
from jigsaw.controller import (
    list_reopen_cases,
    mark_case_reviewed,
    prepare_reopened_case_input,
    validate_action_record_v1,
    validate_case_state_v1,
    validate_gc_context_snapshot_v1,
    validate_outcome_event_v1,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_WORKSPACE = "local"
DEFAULT_LIFECYCLE_ROOT = resolve_workspace_path("lifecycle_root", DEFAULT_WORKSPACE)
DEFAULT_OUTPUT_ROOT = resolve_workspace_path("reopen_review_root", DEFAULT_WORKSPACE)


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def _display_value(value: str | None) -> str:
    if not value:
        return "none"
    return value.replace("_", " ").strip()


def _packet_markdown(
    *,
    case_state: dict[str, Any],
    action_record: dict[str, Any],
    outcome_event: dict[str, Any],
    case_input_preview: dict[str, Any],
    confidence_delta: float,
) -> str:
    return (
        "# Reopen Review Packet\n\n"
        "## Case state\n\n"
        f"- case_id: `{case_state['case_id']}`\n"
        f"- hypothesis_id: `{case_state['hypothesis_id']}`\n"
        f"- current_status: `{case_state['current_status']}`\n"
        f"- latest_decision: `{case_state['latest_decision']}`\n"
        f"- confidence_current: `{case_state['confidence_current']}`\n"
        f"- confidence_trajectory: `{case_state['confidence_trajectory']}`\n"
        f"- latest_outcome: `{case_state['latest_outcome']}`\n"
        f"- reopen_required: `{case_state['reopen_required']}`\n\n"
        "## Latest action record\n\n"
        f"- action_id: `{action_record['action_id']}`\n"
        f"- recommended_action: `{action_record['recommended_action']}`\n"
        f"- action_taken: `{action_record['action_taken']}`\n"
        f"- taken_by: `{action_record['taken_by']}`\n"
        f"- timestamp: `{action_record['timestamp']}`\n"
        f"- notes: {_display_value(action_record.get('notes'))}\n\n"
        "## Latest outcome event\n\n"
        f"- event_id: `{outcome_event['event_id']}`\n"
        f"- observed_outcome: `{outcome_event['observed_outcome']}`\n"
        f"- recorded_by: `{outcome_event['recorded_by']}`\n"
        f"- timestamp: `{outcome_event['timestamp']}`\n"
        f"- effect_on_confidence: `{outcome_event['effect_on_confidence']}`\n"
        f"- confidence_delta: `{round(confidence_delta, 4)}`\n"
        f"- notes: {_display_value(outcome_event.get('notes'))}\n\n"
        "## Why this case was reopened\n\n"
        f"- reopen_conditions: `{case_state['reopen_conditions']}`\n"
        f"- reopen_required: `{case_state['reopen_required']}`\n\n"
        "## Fresh case_input preview\n\n"
        f"```json\n{json.dumps(case_input_preview, indent=2)}\n```\n"
    )


def _queue_markdown(queue_rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Reopen Review Queue",
        "",
        f"- cases_requiring_review: `{len(queue_rows)}`",
        "",
        "| Case | Status | Confidence | Latest outcome | Why reopened | Packet |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in queue_rows:
        lines.append(
            f"| `{row['case_id']}` | `{row['current_status']}` | `{row['confidence_current']}` | "
            f"`{row['latest_outcome']}` | `{row['reopen_reason']}` | [{row['packet_name']}]({row['packet_name']}) |"
        )
    lines.append("")
    return "\n".join(lines)


def generate_reopen_review_packets(
    *,
    lifecycle_root: str | Path = DEFAULT_LIFECYCLE_ROOT,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    reviewed_at: str = "2026-03-16T12:00:00Z",
) -> dict[str, Any]:
    lifecycle_path = Path(lifecycle_root)
    output_path = Path(output_root)
    output_path.mkdir(parents=True, exist_ok=True)

    case_dirs = sorted(path for path in lifecycle_path.iterdir() if path.is_dir())
    loaded_cases: list[dict[str, Any]] = []
    for case_dir in case_dirs:
        case_state = validate_case_state_v1(_load_json(case_dir / "case_state.json"))
        action_record = validate_action_record_v1(_load_json(case_dir / "action_record.json"))
        outcome_event = validate_outcome_event_v1(_load_json(case_dir / "outcome_event.json"))
        gc_context = validate_gc_context_snapshot_v1(_load_json(case_dir / "gc_context.json"))
        loaded_cases.append(
            {
                "case_dir": case_dir,
                "case_state": case_state,
                "action_record": action_record,
                "outcome_event": outcome_event,
                "gc_context": gc_context,
            }
        )

    reopen_cases = list_reopen_cases([entry["case_state"] for entry in loaded_cases])
    reopen_ids = {case.case_id for case in reopen_cases}
    queue_rows: list[dict[str, Any]] = []
    generated_packets: list[str] = []

    for entry in loaded_cases:
        case_state = entry["case_state"]
        if case_state.case_id not in reopen_ids:
            continue

        reviewed_state = mark_case_reviewed(case_state, reviewed_at=reviewed_at)
        hypothesis_state, case_input = prepare_reopened_case_input(reviewed_state, entry["gc_context"])
        packet_name = f"{case_state.case_id.replace(':', '_')}_review_packet.md"
        packet_path = output_path / packet_name
        confidence_delta = reviewed_state.confidence_current - case_state.confidence_current

        _write_text(
            packet_path,
            _packet_markdown(
                case_state=case_state.model_dump(mode="python"),
                action_record=entry["action_record"].model_dump(mode="python"),
                outcome_event=entry["outcome_event"].model_dump(mode="python"),
                case_input_preview=case_input.model_dump(mode="python"),
                confidence_delta=confidence_delta,
            ),
        )
        _dump_json(output_path / f"{case_state.case_id.replace(':', '_')}_reviewed_case_state.json", reviewed_state.model_dump(mode="python"))
        _dump_json(output_path / f"{case_state.case_id.replace(':', '_')}_hypothesis_state.json", hypothesis_state.model_dump(mode="python"))
        _dump_json(output_path / f"{case_state.case_id.replace(':', '_')}_case_input.json", case_input.model_dump(mode="python"))

        queue_rows.append(
            {
                "case_id": case_state.case_id,
                "current_status": case_state.current_status,
                "confidence_current": case_state.confidence_current,
                "latest_outcome": case_state.latest_outcome,
                "reopen_reason": ",".join(case_state.reopen_conditions) or "manual_review",
                "packet_name": packet_name,
            }
        )
        generated_packets.append(str(packet_path))

    _write_text(output_path / "REOPEN_QUEUE.md", _queue_markdown(queue_rows))
    return {
        "cases_requiring_review": len(queue_rows),
        "queue_path": str(output_path / "REOPEN_QUEUE.md"),
        "packet_paths": generated_packets,
        "status": "success",
    }


if __name__ == "__main__":
    print(json.dumps(generate_reopen_review_packets(), indent=2))
