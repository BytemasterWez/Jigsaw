from __future__ import annotations

import json
from pathlib import Path

from jigsaw.controller import (
    apply_outcome_event,
    apply_relevance_signal,
    apply_watchdog_result,
    build_action_record,
    build_case_input,
    build_case_relevance_signal,
    build_case_state,
    build_gc_context_snapshot,
    build_outcome_event,
    hypothesis_state_from_gc_context,
)
from jigsaw.lanes.real_case_lane.generate_case_monitor_queue import generate_case_monitor_queue


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _base_case(case_id: int):
    gc_context = build_gc_context_snapshot(
        {
            "primary_item_id": case_id,
            "related_item_ids": [22, 45, 14],
            "summary": f"Assess whether case {case_id} is ready to package for review.",
            "freshness": "recent",
            "known_gaps": [],
        }
    )
    hypothesis_state = hypothesis_state_from_gc_context(gc_context)
    case_input = build_case_input(hypothesis_state, gc_context)
    case_state = build_case_state(
        case_input,
        gc_context,
        {
            "candidate_id": f"gc_case:remote_workflow_v1b:{case_id}",
            "judgement": "promoted",
            "confidence": 0.81,
            "reason_summary": "Strong fit justifies review.",
            "key_factors": ["High relevance"],
            "recommended_action": "prioritise_for_review",
        },
        reviewed_at="2026-03-16T08:00:00Z",
    )
    action_record = build_action_record(
        case_state,
        {
            "candidate_id": f"gc_case:remote_workflow_v1b:{case_id}",
            "judgement": "promoted",
            "confidence": 0.81,
            "reason_summary": "Strong fit justifies review.",
            "key_factors": ["High relevance"],
            "recommended_action": "prioritise_for_review",
        },
        "reviewed",
        timestamp="2026-03-16T09:00:00Z",
    )
    return gc_context, case_state, action_record


def test_generate_case_monitor_queue_merges_attention_sources(tmp_path: Path) -> None:
    lifecycle_root = tmp_path / "lifecycle"
    output_root = tmp_path / "monitor"

    gc_context_1, case_state_1, action_record_1 = _base_case(8)
    outcome_event_1 = build_outcome_event(
        case_state_1,
        action_record_1,
        "invalidated",
        -0.2,
        timestamp="2026-03-16T12:00:00Z",
    )
    monitored_1 = apply_outcome_event(case_state_1, outcome_event_1)
    case_dir_1 = lifecycle_root / "case_01"
    _write_json(case_dir_1 / "case_state.json", monitored_1.model_dump(mode="python"))

    gc_context_2, case_state_2, _ = _base_case(9)
    monitored_2 = case_state_2.model_copy(
        update={
            "reopen_required": True,
            "latest_reopen_reason": "manual_review_requested",
        }
    )
    case_dir_2 = lifecycle_root / "case_02"
    _write_json(case_dir_2 / "case_state.json", monitored_2.model_dump(mode="python"))

    gc_context_3, case_state_3, _ = _base_case(10)
    relevance_signal_3 = build_case_relevance_signal(
        case_state_3,
        gc_context_3,
        {
            "item_id": 900,
            "title": "Case 10 update",
            "content": "Case 10 update with related opportunity material.",
            "related_item_ids": [10, 22],
            "source_types": ["gc_item"],
            "topic_hints": ["case", "update"],
        },
        timestamp="2026-03-16T12:00:00Z",
    ).model_copy(update={"recommended_effect": "reopen_case"})
    monitored_3 = apply_relevance_signal(case_state_3, relevance_signal_3)
    case_dir_3 = lifecycle_root / "case_03"
    _write_json(case_dir_3 / "case_state.json", monitored_3.model_dump(mode="python"))
    _write_json(case_dir_3 / "case_relevance_signal.json", relevance_signal_3.model_dump(mode="python"))

    result = generate_case_monitor_queue(lifecycle_root=lifecycle_root, output_root=output_root)

    assert result["status"] == "success"
    assert result["cases_needing_attention"] == 3

    queue_path = Path(result["queue_path"])
    assert queue_path.exists()
    queue_text = queue_path.read_text(encoding="utf-8")
    assert "Case Monitor Queue" in queue_text
    assert "case:hyp:gc:8" in queue_text
    assert "case:hyp:gc:9" in queue_text
    assert "case:hyp:gc:10" in queue_text
    assert "invalidated" in queue_text
    assert "new_relevant_material_detected" in queue_text


def test_generate_case_monitor_queue_prioritises_watchdog_failures(tmp_path: Path) -> None:
    lifecycle_root = tmp_path / "lifecycle"
    output_root = tmp_path / "monitor"

    _, case_state_1, _ = _base_case(11)
    watchdog_case = apply_watchdog_result(
        case_state_1,
        {
            "contract": "kernel_watchdog_result",
            "version": "v1",
            "watchdog_id": "kw:kx:test:observed_state",
            "exchange_id": "kx:test:observed_state",
            "kernel_name": "observed_state",
            "verdict": "fail",
            "reasons": ["kernel_output_validation_failed"],
            "timestamp": "2026-03-16T12:00:00Z",
        },
    )
    _write_json((lifecycle_root / "case_01" / "case_state.json"), watchdog_case.model_dump(mode="python"))

    _, case_state_2, action_record_2 = _base_case(12)
    outcome_event_2 = build_outcome_event(
        case_state_2,
        action_record_2,
        "weakened",
        -0.1,
        timestamp="2026-03-16T12:30:00Z",
    )
    weakened_case = apply_outcome_event(case_state_2, outcome_event_2)
    _write_json((lifecycle_root / "case_02" / "case_state.json"), weakened_case.model_dump(mode="python"))

    result = generate_case_monitor_queue(lifecycle_root=lifecycle_root, output_root=output_root)

    assert result["cases_needing_attention"] == 2
    queue_text = Path(result["queue_path"]).read_text(encoding="utf-8")
    lines = [line for line in queue_text.splitlines() if line.startswith("| `case:hyp:gc:")]
    assert lines[0].startswith("| `case:hyp:gc:11`")
    assert "watchdog_fail" in queue_text
    assert "urgent watchdog review" in queue_text
