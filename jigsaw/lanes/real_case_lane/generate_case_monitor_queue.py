from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jigsaw.controller import (
    validate_case_relevance_signal_v1,
    validate_case_state_v1,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_LIFECYCLE_ROOT = REPO_ROOT / "validation" / "case_lifecycle"
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "deliverables" / "remote_workflow" / "case_monitor_queue"


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _display_value(value: str | None) -> str:
    if not value:
        return "none"
    return value.replace("_", " ").strip()


def _recommended_next_move(entry: dict[str, Any]) -> str:
    if entry["latest_reopen_reason"] == "watchdog_fail":
        return "urgent watchdog review"
    if entry["latest_reopen_reason"] == "watchdog_warn":
        return "review watchdog warning"
    if entry["latest_outcome"] in {"invalidated", "weakened"}:
        return "review weakened case"
    if entry["latest_reopen_reason"] == "new_relevant_material_detected":
        return "review new material"
    if entry["reopen_required"]:
        return "manual reopen review"
    return "monitor only"


def _urgency_rank(entry: dict[str, Any]) -> tuple[int, str]:
    if entry["latest_reopen_reason"] == "watchdog_fail":
        return (0, entry["case_id"])
    if entry["latest_reopen_reason"] == "watchdog_warn":
        return (1, entry["case_id"])
    if entry["latest_outcome"] == "invalidated":
        return (2, entry["case_id"])
    if entry["latest_outcome"] == "weakened":
        return (3, entry["case_id"])
    if entry["latest_reopen_reason"] == "new_relevant_material_detected":
        return (4, entry["case_id"])
    if entry["reopen_required"]:
        return (5, entry["case_id"])
    return (6, entry["case_id"])


def _should_include(entry: dict[str, Any]) -> bool:
    if entry["reopen_required"]:
        return True
    if entry["latest_outcome"] in {"weakened", "invalidated"}:
        return True
    if entry["latest_relevance_effect"] == "reopen_case":
        return True
    return False


def _queue_markdown(entries: list[dict[str, Any]]) -> str:
    lines = [
        "# Case Monitor Queue",
        "",
        f"- cases_needing_attention: `{len(entries)}`",
        "",
        "| Case | Status | Decision | Confidence | Trajectory | Reopen | Reopen reason | Outcome | Relevance signal | Next move |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for entry in entries:
        lines.append(
            f"| `{entry['case_id']}` | `{entry['current_status']}` | `{entry['latest_decision']}` | "
            f"`{entry['confidence_current']}` | `{entry['confidence_trajectory']}` | `{entry['reopen_required']}` | "
            f"`{entry['latest_reopen_reason']}` | `{entry['latest_outcome']}` | "
            f"`{entry['latest_relevance_effect']}` | `{entry['recommended_next_move']}` |"
        )
    lines.append("")
    return "\n".join(lines)


def generate_case_monitor_queue(
    *,
    lifecycle_root: str | Path = DEFAULT_LIFECYCLE_ROOT,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
) -> dict[str, Any]:
    lifecycle_path = Path(lifecycle_root)
    output_path = Path(output_root)
    output_path.mkdir(parents=True, exist_ok=True)

    case_dirs = sorted(path for path in lifecycle_path.iterdir() if path.is_dir())
    queue_entries: list[dict[str, Any]] = []
    for case_dir in case_dirs:
        case_state = validate_case_state_v1(_load_json(case_dir / "case_state.json"))
        latest_relevance_effect = "none"
        if (case_dir / "case_relevance_signal.json").exists():
            relevance_signal = validate_case_relevance_signal_v1(_load_json(case_dir / "case_relevance_signal.json"))
            latest_relevance_effect = relevance_signal.recommended_effect

        entry = {
            "case_id": case_state.case_id,
            "current_status": case_state.current_status,
            "latest_decision": case_state.latest_decision,
            "confidence_current": case_state.confidence_current,
            "confidence_trajectory": case_state.confidence_trajectory,
            "reopen_required": case_state.reopen_required,
            "latest_reopen_reason": case_state.latest_reopen_reason or "none",
            "latest_outcome": case_state.latest_outcome or "none",
            "latest_relevance_effect": latest_relevance_effect,
        }
        if _should_include(entry):
            entry["recommended_next_move"] = _recommended_next_move(entry)
            queue_entries.append(entry)

    queue_entries.sort(key=_urgency_rank)
    queue_path = output_path / "CASE_MONITOR_QUEUE.md"
    _write_text(queue_path, _queue_markdown(queue_entries))
    return {
        "cases_needing_attention": len(queue_entries),
        "queue_path": str(queue_path),
        "status": "success",
    }


if __name__ == "__main__":
    print(json.dumps(generate_case_monitor_queue(), indent=2))
