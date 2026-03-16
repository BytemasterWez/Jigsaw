from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any, Literal

from jigsaw.controller import (
    apply_watchdog_result,
    build_manual_review_action_record,
    mark_case_reviewed,
    prepare_reopened_case_input,
    update_case_state,
    validate_action_record_v1,
    validate_case_state_v1,
    validate_gc_context_snapshot_v1,
)
from jigsaw.engines.watchdog import inspect_kernel_exchanges
from jigsaw.engines.watchdog_policy import default_watchdog_policy, evaluate_watchdog_policy
from jigsaw.lanes.kernel_lane.arbiter_integration import adjudicate_with_exchange, kernel_bundle_result_to_arbiter_request
from jigsaw.lanes.kernel_lane.validators import validate_kernel_bundle_result_v1, validate_kernel_input_v1
from jigsaw.lanes.real_case_lane.case_input_composition import compose_case_from_case_input
from jigsaw.lanes.real_case_lane.execute_profile_batch import DEFAULT_PROFILE, load_execution_profile
from jigsaw.lanes.real_case_lane.execute_remote_workflow_case import GC_DB_PATH, _fetch_gc_item
from jigsaw.lanes.real_case_lane.generate_case_timeline import DEFAULT_OUTPUT_ROOT as DEFAULT_TIMELINE_ROOT
from jigsaw.lanes.real_case_lane.generate_case_timeline import generate_case_timeline


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_LIFECYCLE_ROOT = REPO_ROOT / "validation" / "case_lifecycle"
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "validation" / "case_reviews"
OperatorDecision = Literal["review_now", "defer", "close", "rerun_forward_pass"]


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


def _load_gc_context_snapshot(path: Path) -> Any:
    payload = _load_json(path)
    if payload.get("question_or_claim") is None:
        payload.pop("question_or_claim", None)
    return validate_gc_context_snapshot_v1(payload)


def _find_case_dir(case_id: str, lifecycle_root: Path) -> Path:
    for candidate in sorted(path for path in lifecycle_root.iterdir() if path.is_dir()):
        case_state_path = candidate / "case_state.json"
        if not case_state_path.exists():
            continue
        case_state = validate_case_state_v1(_load_json(case_state_path))
        if case_state.case_id == case_id:
            return candidate
    raise FileNotFoundError(f"Case {case_id} was not found under {lifecycle_root}")


def _profile_name_for_case(case_dir: Path) -> str:
    arbiter_exchange_path = case_dir / "arbiter_exchange.json"
    if arbiter_exchange_path.exists():
        payload = _load_json(arbiter_exchange_path)
        metadata = payload.get("arbiter_metadata", {})
        profile_name = metadata.get("profile_name")
        if isinstance(profile_name, str) and profile_name:
            return profile_name
    return DEFAULT_PROFILE


def _operator_action_record(
    case_state: Any,
    *,
    decision: OperatorDecision,
    timestamp: str,
    notes: str,
) -> Any:
    if decision == "review_now":
        return build_manual_review_action_record(case_state, timestamp=timestamp, notes=notes)

    action_taken_map = {
        "defer": "deferred",
        "close": "no_action_taken",
        "rerun_forward_pass": "followed_up",
    }
    recommended_action_map = {
        "defer": "defer",
        "close": "no_action",
        "rerun_forward_pass": "hold_for_recheck",
    }
    state = validate_case_state_v1(case_state if isinstance(case_state, dict) else case_state.model_dump(mode="python"))
    return validate_action_record_v1(
        {
            "contract": "action_record",
            "version": "v1",
            "action_id": f"action:{state.case_id}:operator:{decision}:{state.revision_count + 1}",
            "case_id": state.case_id,
            "recommended_action": recommended_action_map[decision],
            "action_taken": action_taken_map[decision],
            "taken_by": "human",
            "timestamp": timestamp,
            "notes": notes,
        }
    )


def _updated_case_state_for_decision(case_state: Any, *, decision: OperatorDecision, timestamp: str) -> Any:
    state = validate_case_state_v1(case_state if isinstance(case_state, dict) else case_state.model_dump(mode="python"))
    if decision == "review_now":
        return mark_case_reviewed(state, reviewed_at=timestamp)

    payload = state.model_dump(mode="python")
    payload["last_reviewed_at"] = timestamp
    payload["reopen_required"] = False
    payload["latest_reopen_reason"] = None
    payload["reopen_conditions"] = []
    payload["revision_count"] = state.revision_count + 1

    if decision == "defer":
        payload["current_status"] = "watching"
        return validate_case_state_v1(payload)
    if decision == "close":
        payload["current_status"] = "closed"
        return validate_case_state_v1(payload)

    raise ValueError(f"Unsupported decision for direct case-state update: {decision}")


def _load_gc_case_context(gc_context: Any) -> dict[str, Any]:
    with sqlite3.connect(GC_DB_PATH) as connection:
        primary_item = _fetch_gc_item(connection, gc_context.primary_item_id)
        supporting_items = [_fetch_gc_item(connection, item_id) for item_id in gc_context.related_item_ids]
    return {
        "primary_item": primary_item.__dict__,
        "supporting_items": [item.__dict__ for item in supporting_items],
    }


def _review_markdown(payload: dict[str, Any]) -> str:
    return (
        "# Review Decision\n\n"
        f"- case_id: `{payload['case_id']}`\n"
        f"- decision: `{payload['decision']}`\n"
        f"- reviewed_at: `{payload['reviewed_at']}`\n"
        f"- timeline_path: `{payload['timeline_path']}`\n"
        f"- case_state_path: `{payload['case_state_path']}`\n"
        f"- action_record_path: `{payload['action_record_path']}`\n"
        f"- rerun_outputs_path: `{payload.get('rerun_outputs_path', 'none')}`\n"
        f"- notes: `{payload['notes']}`\n"
    )


def review_case_from_queue(
    *,
    case_id: str,
    decision: OperatorDecision,
    lifecycle_root: str | Path = DEFAULT_LIFECYCLE_ROOT,
    timeline_root: str | Path = DEFAULT_TIMELINE_ROOT,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    reviewed_at: str = "2026-03-16T13:00:00Z",
    notes: str = "",
) -> dict[str, Any]:
    lifecycle_path = Path(lifecycle_root)
    timeline_path = Path(timeline_root)
    output_path = Path(output_root)
    case_dir = _find_case_dir(case_id, lifecycle_path)

    case_state = validate_case_state_v1(_load_json(case_dir / "case_state.json"))
    gc_context = _load_gc_context_snapshot(case_dir / "gc_context.json") if (case_dir / "gc_context.json").exists() else None
    timeline_result = generate_case_timeline(case_dir=case_dir, output_root=timeline_path)

    action_record = _operator_action_record(
        case_state,
        decision=decision,
        timestamp=reviewed_at,
        notes=notes or f"operator_decision:{decision}",
    )

    case_review_dir = output_path / case_id.replace(":", "_")
    _dump_json(case_review_dir / "action_record.json", action_record.model_dump(mode="python"))

    rerun_outputs_path: str | None = None
    if decision == "rerun_forward_pass":
        if gc_context is None:
            raise FileNotFoundError("gc_context.json is required to rerun the forward pass for a queued case.")
        profile_name = _profile_name_for_case(case_dir)
        profile = load_execution_profile(profile_name)
        hypothesis_state, case_input = prepare_reopened_case_input(case_state, gc_context, controller_config=profile.get("controller"))
        composition = compose_case_from_case_input(
            case_input,
            _load_gc_case_context(gc_context),
            profile_name=profile_name,
            pipeline_run_id=f"review-rerun-{case_id.replace(':', '_')}",
            generated_at=reviewed_at,
        )
        kernel_watchdog_results = [
            result.model_dump(mode="python")
            for result in inspect_kernel_exchanges(
                composition["kernel_exchanges"],
                expected_engine_modes=profile.get("kernel_engines") or profile.get("kernels") or {},
                timestamp=reviewed_at,
            )
        ]
        watchdog_policy = default_watchdog_policy()
        watchdog_policy_decision = evaluate_watchdog_policy(
            kernel_watchdog_results,
            case_id=case_id,
            timestamp=reviewed_at,
            policy=watchdog_policy,
        )
        kernel_input = validate_kernel_input_v1(composition["kernel_input"])
        kernel_bundle_result = validate_kernel_bundle_result_v1(composition["kernel_bundle_result"])

        rerun_dir = case_review_dir / "rerun_forward_pass"
        _dump_json(rerun_dir / "hypothesis_state.json", hypothesis_state.model_dump(mode="python"))
        _dump_json(rerun_dir / "case_input.json", case_input.model_dump(mode="python"))
        _dump_json(rerun_dir / "kernel_bundle_result.json", kernel_bundle_result.model_dump(mode="python"))
        _dump_json(rerun_dir / "kernel_exchanges.json", composition["kernel_exchanges"])
        _dump_json(rerun_dir / "kernel_watchdog_results.json", kernel_watchdog_results)
        _dump_json(rerun_dir / "watchdog_policy.json", watchdog_policy.model_dump(mode="python"))
        _dump_json(rerun_dir / "watchdog_policy_decision.json", watchdog_policy_decision.model_dump(mode="python"))
        if watchdog_policy_decision.blocked:
            blocked_result = next(
                (
                    result
                    for result in kernel_watchdog_results
                    if result["verdict"] == "fail"
                ),
                kernel_watchdog_results[0],
            )
            updated_case_state = apply_watchdog_result(case_state, blocked_result)
        else:
            arbiter_request = kernel_bundle_result_to_arbiter_request(kernel_input, kernel_bundle_result)
            arbiter_response, arbiter_exchange = adjudicate_with_exchange(
                arbiter_request,
                case_id=case_id,
                timestamp=reviewed_at,
                exchange_scope=f"review-rerun-{case_id.replace(':', '_')}",
                arbiter_metadata={"profile_name": profile_name},
            )
            updated_case_state = update_case_state(
                case_state,
                arbiter_response=arbiter_response,
                snapshot_id=gc_context.snapshot_id,
                reviewed_at=reviewed_at,
            )
            payload = updated_case_state.model_dump(mode="python")
            payload["reopen_required"] = False
            payload["latest_reopen_reason"] = None
            payload["reopen_conditions"] = []
            updated_case_state = validate_case_state_v1(payload)
            _dump_json(rerun_dir / "arbiter_request.json", arbiter_request)
            _dump_json(rerun_dir / "arbiter_response.json", arbiter_response)
            _dump_json(rerun_dir / "arbiter_exchange.json", arbiter_exchange.model_dump(mode="python"))
        rerun_outputs_path = str(rerun_dir)
    else:
        updated_case_state = _updated_case_state_for_decision(case_state, decision=decision, timestamp=reviewed_at)

    _dump_json(case_dir / "case_state.json", updated_case_state.model_dump(mode="python"))
    _dump_json(case_dir / "action_record.json", action_record.model_dump(mode="python"))

    review_payload = {
        "case_id": case_id,
        "decision": decision,
        "reviewed_at": reviewed_at,
        "timeline_path": timeline_result["timeline_path"],
        "case_state_path": str(case_dir / "case_state.json"),
        "action_record_path": str(case_dir / "action_record.json"),
        "rerun_outputs_path": rerun_outputs_path,
        "notes": notes or f"operator_decision:{decision}",
        "status": "success",
    }
    _dump_json(case_review_dir / "review_decision.json", review_payload)
    _write_text(case_review_dir / "REVIEW_DECISION.md", _review_markdown(review_payload))
    return review_payload


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Review a queued case and optionally rerun the governed forward pass.")
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--decision", required=True, choices=["review_now", "defer", "close", "rerun_forward_pass"])
    parser.add_argument("--lifecycle-root", default=str(DEFAULT_LIFECYCLE_ROOT))
    parser.add_argument("--timeline-root", default=str(DEFAULT_TIMELINE_ROOT))
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--reviewed-at", default="2026-03-16T13:00:00Z")
    parser.add_argument("--notes", default="")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    result = review_case_from_queue(
        case_id=args.case_id,
        decision=args.decision,
        lifecycle_root=args.lifecycle_root,
        timeline_root=args.timeline_root,
        output_root=args.output_root,
        reviewed_at=args.reviewed_at,
        notes=args.notes,
    )
    print(json.dumps(result, indent=2))
