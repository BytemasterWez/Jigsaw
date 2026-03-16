from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from jigsaw.controller import (
    apply_outcome_event,
    apply_relevance_signal,
    apply_watchdog_result,
    build_action_record,
    build_case_relevance_signal,
    build_case_state,
    build_outcome_event,
    validate_case_input_v1,
    validate_gc_context_snapshot_v1,
)
from jigsaw.engines.watchdog import validate_kernel_watchdog_result_v1
from jigsaw.lanes.kernel_lane.arbiter_exchange import validate_arbiter_exchange_v1
from jigsaw.lanes.real_case_lane.generate_case_monitor_queue import generate_case_monitor_queue
from jigsaw.lanes.real_case_lane.generate_case_timeline import generate_case_timeline
from jigsaw.lanes.real_case_lane.generate_reopen_review_packets import generate_reopen_review_packets
from jigsaw.lanes.real_case_lane.review_case_from_queue import review_case_from_queue


REPO_ROOT = Path(__file__).resolve().parents[3]
SOURCE_REAL_CASE_ROOT = REPO_ROOT / "validation" / "real_case_remote_workflow" / "output"
DEFAULT_DEMO_ROOT = REPO_ROOT / "validation" / "lifecycle_demo_case"


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


def _load_gc_context(path: Path) -> Any:
    payload = _load_json(path)
    if payload.get("question_or_claim") is None:
        payload.pop("question_or_claim", None)
    return validate_gc_context_snapshot_v1(payload)


def _review_summary_markdown(payload: dict[str, Any]) -> str:
    return (
        "# Lifecycle Demo Proof\n\n"
        "This seeded demo starts from the real stored remote-workflow case and proves the lifecycle path end to end.\n\n"
        "## Seeded base case\n\n"
        f"- case_id: `{payload['case_id']}`\n"
        f"- base_case_dir: `{payload['base_case_dir']}`\n"
        f"- queue_path: `{payload['queue_path']}`\n"
        f"- timeline_path: `{payload['timeline_path']}`\n"
        f"- reopen_queue_path: `{payload['reopen_queue_path']}`\n\n"
        "## Operator review proofs\n\n"
        f"- review_now decision: `{payload['review_now']['decision']}`\n"
        f"- review_now case_state_path: `{payload['review_now']['case_state_path']}`\n"
        f"- rerun_forward_pass decision: `{payload['rerun_forward_pass']['decision']}`\n"
        f"- rerun_forward_pass case_state_path: `{payload['rerun_forward_pass']['case_state_path']}`\n"
        f"- rerun_forward_pass outputs: `{payload['rerun_forward_pass']['rerun_outputs_path']}`\n"
    )


def seed_lifecycle_demo_case(*, demo_root: str | Path = DEFAULT_DEMO_ROOT) -> dict[str, Any]:
    demo_path = Path(demo_root)
    if demo_path.exists():
        shutil.rmtree(demo_path)

    lifecycle_base_root = demo_path / "case_lifecycle" / "base"
    review_now_root = demo_path / "case_lifecycle" / "review_now"
    rerun_root = demo_path / "case_lifecycle" / "rerun_forward_pass"
    monitor_root = demo_path / "monitor_queue"
    timeline_root = demo_path / "timelines"
    reopen_review_root = demo_path / "reopen_review"
    review_outputs_root = demo_path / "case_reviews"
    base_case_dir = lifecycle_base_root / "case_01"

    gc_context = _load_gc_context(SOURCE_REAL_CASE_ROOT / "gc_context.json")
    case_input = validate_case_input_v1(_load_json(SOURCE_REAL_CASE_ROOT / "case_input.json"))
    arbiter_response = _load_json(SOURCE_REAL_CASE_ROOT / "arbiter_response.json")
    arbiter_exchange = validate_arbiter_exchange_v1(_load_json(SOURCE_REAL_CASE_ROOT / "arbiter_exchange.json"))

    case_state = build_case_state(case_input, gc_context, arbiter_response, reviewed_at=arbiter_exchange.timestamp)
    action_record = build_action_record(
        case_state,
        arbiter_response,
        "reviewed",
        timestamp="2026-03-15T12:30:00Z",
        notes="Seeded lifecycle demo analyst review.",
    )
    outcome_event = build_outcome_event(
        case_state,
        action_record,
        "weakened",
        -0.12,
        timestamp="2026-03-16T09:00:00Z",
        notes="Customer follow-up weakened the case.",
    )
    revised_state = apply_outcome_event(case_state, outcome_event)
    relevance_signal = build_case_relevance_signal(
        revised_state,
        gc_context,
        {
            "item_id": 18,
            "title": "Remote workflow update",
            "content": "New related remote workflow material arrived for the same opportunity area.",
            "related_item_ids": [45, 8],
            "source_types": ["gc_item"],
            "topic_hints": ["remote", "workflow", "opportunity"],
        },
        timestamp="2026-03-16T10:00:00Z",
    ).model_copy(update={"recommended_effect": "reopen_case"})
    revised_state = apply_relevance_signal(revised_state, relevance_signal)
    watchdog_result = validate_kernel_watchdog_result_v1(
        {
            "contract": "kernel_watchdog_result",
            "version": "v1",
            "watchdog_id": "kw:kx:lifecycle-demo:expected_state",
            "exchange_id": "kx:lifecycle-demo:expected_state",
            "kernel_name": "expected_state",
            "verdict": "warn",
            "reasons": ["engine_mode_mismatch"],
            "timestamp": "2026-03-16T11:00:00Z",
        }
    )
    revised_state = apply_watchdog_result(revised_state, watchdog_result)

    _dump_json(base_case_dir / "gc_context.json", gc_context.model_dump(mode="python", exclude_none=True))
    _dump_json(base_case_dir / "case_input.json", case_input.model_dump(mode="python"))
    _dump_json(base_case_dir / "case_state.json", revised_state.model_dump(mode="python"))
    _dump_json(base_case_dir / "action_record.json", action_record.model_dump(mode="python"))
    _dump_json(base_case_dir / "outcome_event.json", outcome_event.model_dump(mode="python"))
    _dump_json(base_case_dir / "case_relevance_signal.json", relevance_signal.model_dump(mode="python"))
    _dump_json(base_case_dir / "kernel_watchdog_result.json", watchdog_result.model_dump(mode="python"))
    _dump_json(base_case_dir / "arbiter_exchange.json", arbiter_exchange.model_dump(mode="python"))
    _dump_json(base_case_dir / "arbiter_response.json", arbiter_response)

    queue_result = generate_case_monitor_queue(lifecycle_root=lifecycle_base_root, output_root=monitor_root)
    timeline_result = generate_case_timeline(case_dir=base_case_dir, output_root=timeline_root)
    reopen_review_result = generate_reopen_review_packets(lifecycle_root=lifecycle_base_root, output_root=reopen_review_root)

    shutil.copytree(lifecycle_base_root, review_now_root)
    shutil.copytree(lifecycle_base_root, rerun_root)

    review_now_result = review_case_from_queue(
        case_id=revised_state.case_id,
        decision="review_now",
        lifecycle_root=review_now_root,
        timeline_root=timeline_root / "review_now",
        output_root=review_outputs_root / "review_now",
        reviewed_at="2026-03-16T12:00:00Z",
        notes="Seeded lifecycle demo review_now proof.",
    )
    rerun_result = review_case_from_queue(
        case_id=revised_state.case_id,
        decision="rerun_forward_pass",
        lifecycle_root=rerun_root,
        timeline_root=timeline_root / "rerun_forward_pass",
        output_root=review_outputs_root / "rerun_forward_pass",
        reviewed_at="2026-03-16T12:30:00Z",
        notes="Seeded lifecycle demo rerun proof.",
    )

    summary_payload = {
        "case_id": revised_state.case_id,
        "base_case_dir": str(base_case_dir),
        "queue_path": queue_result["queue_path"],
        "timeline_path": timeline_result["timeline_path"],
        "reopen_queue_path": reopen_review_result["queue_path"],
        "review_now": review_now_result,
        "rerun_forward_pass": rerun_result,
        "status": "success",
    }
    _dump_json(demo_path / "summary.json", summary_payload)
    _write_text(demo_path / "LIFECYCLE_DEMO_PROOF.md", _review_summary_markdown(summary_payload))
    return summary_payload


if __name__ == "__main__":
    print(json.dumps(seed_lifecycle_demo_case(), indent=2))
