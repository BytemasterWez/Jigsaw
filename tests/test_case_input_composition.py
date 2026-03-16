from __future__ import annotations

import sqlite3

from jigsaw.controller.hypothesis_controller import build_case_input, hypothesis_state_from_gc_context
from jigsaw.lanes.real_case_lane.case_input_composition import compose_case_from_case_input
from jigsaw.lanes.real_case_lane.execute_remote_workflow_case import GC_DB_PATH, _fetch_gc_item


def test_sufficient_hypothesis_can_compose_case_from_case_input() -> None:
    gc_context = {
        "primary_item_id": 8,
        "related_item_ids": [22, 45, 14],
        "summary": "Remote income opportunity has enough nearby support.",
        "freshness": "recent",
        "known_gaps": [],
    }
    hypothesis_state = hypothesis_state_from_gc_context(gc_context)
    case_input = build_case_input(hypothesis_state, gc_context)

    with sqlite3.connect(GC_DB_PATH) as connection:
        primary_item = _fetch_gc_item(connection, 8)
        supporting_items = [_fetch_gc_item(connection, item_id) for item_id in [22, 45, 14]]

    result = compose_case_from_case_input(
        case_input,
        {
            "primary_item": primary_item.__dict__,
            "supporting_items": [item.__dict__ for item in supporting_items],
        },
    )

    assert result["status"] == "success"
    assert result["case_input"]["case_id"] == case_input.case_id
    assert result["kernel_input"]["context"]["case_id"] == case_input.case_id
    assert result["kernel_bundle_result"]["contract"] == "kernel_bundle_result"
    assert len(result["kernel_exchanges"]) == 3
    assert result["kernel_exchanges"][0]["contract"] == "kernel_exchange"
    assert result["case_summary"]["bundle_judgment"] in {"aligned", "partially_aligned", "contradictory"}
