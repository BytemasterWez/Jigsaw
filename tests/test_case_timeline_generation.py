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
from jigsaw.lanes.kernel_lane.arbiter_exchange import build_arbiter_exchange
from jigsaw.lanes.real_case_lane.generate_case_timeline import generate_case_timeline


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_generate_case_timeline_writes_ordered_history(tmp_path: Path) -> None:
    lifecycle_root = tmp_path / "lifecycle"
    case_dir = lifecycle_root / "case_01"
    output_root = tmp_path / "timelines"

    gc_context = build_gc_context_snapshot(
        {
            "primary_item_id": 8,
            "related_item_ids": [22, 45, 14],
            "summary": "Remote income opportunity has enough nearby support.",
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
            "candidate_id": "gc_case:remote_workflow_v1b:8",
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
            "candidate_id": "gc_case:remote_workflow_v1b:8",
            "judgement": "promoted",
            "confidence": 0.81,
            "reason_summary": "Strong fit justifies review.",
            "key_factors": ["High relevance"],
            "recommended_action": "prioritise_for_review",
        },
        "reviewed",
        timestamp="2026-03-16T09:00:00Z",
        notes="Reviewed by analyst.",
    )
    outcome_event = build_outcome_event(
        case_state,
        action_record,
        "weakened",
        -0.1,
        timestamp="2026-03-16T10:00:00Z",
        notes="Follow-up weakened the case.",
    )
    revised_state = apply_outcome_event(case_state, outcome_event)
    relevance_signal = build_case_relevance_signal(
        revised_state,
        gc_context,
        {
            "item_id": 900,
            "title": "Case 8 update",
            "content": "Related opportunity material arrived.",
            "related_item_ids": [8, 22],
            "source_types": ["gc_item"],
            "topic_hints": ["case", "update"],
        },
        timestamp="2026-03-16T11:00:00Z",
    ).model_copy(update={"recommended_effect": "reopen_case"})
    revised_state = apply_relevance_signal(revised_state, relevance_signal)
    revised_state = apply_watchdog_result(
        revised_state,
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
    arbiter_exchange = build_arbiter_exchange(
        case_id=case_state.case_id,
        sent_packet={"candidate_id": "gc_case:remote_workflow_v1b:8"},
        received_packet={"judgement": "promoted"},
        validation_passed=True,
        timestamp="2026-03-16T08:00:00Z",
        exchange_scope="timeline-test",
        arbiter_metadata={"profile_name": "remote_workflow_v1b"},
    )

    _write_json(case_dir / "case_state.json", revised_state.model_dump(mode="python"))
    _write_json(case_dir / "action_record.json", action_record.model_dump(mode="python"))
    _write_json(case_dir / "outcome_event.json", outcome_event.model_dump(mode="python"))
    _write_json(case_dir / "case_relevance_signal.json", relevance_signal.model_dump(mode="python"))
    _write_json(case_dir / "kernel_watchdog_result.json", {
        "contract": "kernel_watchdog_result",
        "version": "v1",
        "watchdog_id": "kw:kx:test:observed_state",
        "exchange_id": "kx:test:observed_state",
        "kernel_name": "observed_state",
        "verdict": "fail",
        "reasons": ["kernel_output_validation_failed"],
        "timestamp": "2026-03-16T12:00:00Z",
    })
    _write_json(case_dir / "arbiter_exchange.json", arbiter_exchange.model_dump(mode="python"))

    result = generate_case_timeline(case_dir=case_dir, output_root=output_root)

    assert result["status"] == "success"
    timeline_md = Path(result["timeline_path"])
    timeline_json = Path(result["timeline_json_path"])
    assert timeline_md.exists()
    assert timeline_json.exists()

    timeline_text = timeline_md.read_text(encoding="utf-8")
    assert "Case Timeline" in timeline_text
    assert "forward_pass_decision" in timeline_text
    assert "action_recorded" in timeline_text
    assert "outcome_recorded" in timeline_text
    assert "confidence_revised" in timeline_text
    assert "relevance_signal" in timeline_text
    assert "watchdog_fail" in timeline_text
    assert "reopen_flagged" in timeline_text

    payload = json.loads(timeline_json.read_text(encoding="utf-8"))
    event_types = [event["event_type"] for event in payload["events"]]
    assert "latest_status" in event_types
    assert payload["latest_status"]["latest_reopen_reason"] == "watchdog_fail"
