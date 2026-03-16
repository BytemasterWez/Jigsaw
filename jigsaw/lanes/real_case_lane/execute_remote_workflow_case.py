from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from jigsaw.controller.hypothesis_controller import build_case_input, build_gc_context_snapshot, hypothesis_state_from_gc_context
from jigsaw.lanes.artifact_lane.transforms import (
    artifact_to_extraction,
    chunks_to_judgment_request,
    extraction_to_chunks,
)
from jigsaw.lanes.artifact_lane.validators import (
    validate_artifact_v1,
    validate_chunk_v1,
    validate_extraction_v1,
    validate_judgment_request_v1,
)
from jigsaw.lanes.kernel_lane.arbiter_integration import (
    adjudicate_via_current_arbiter,
    kernel_bundle_result_to_arbiter_request,
)
from jigsaw.lanes.kernel_lane.validators import validate_kernel_bundle_result_v1, validate_kernel_input_v1


REPO_ROOT = Path(__file__).resolve().parents[3]
WORKSPACE_ROOT = REPO_ROOT.parent
GC_REPO = WORKSPACE_ROOT / "Garbage collector"
GC_DB_PATH = GC_REPO / "backend" / "garbage_collector.db"
OUTPUT_DIR = REPO_ROOT / "validation" / "real_case_remote_workflow" / "output"

PRIMARY_ITEM_ID = 45
SUPPORTING_ITEM_IDS = [8, 22, 14]


@dataclass(frozen=True)
class GCItem:
    item_id: int
    item_type: str
    title: str
    content: str
    created_at: str
    updated_at: str


def _dump_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def _fetch_gc_item(connection: sqlite3.Connection, item_id: int) -> GCItem:
    row = connection.execute(
        """
        SELECT id, item_type, title, content, created_at, updated_at
        FROM items
        WHERE id = ?
        """,
        (item_id,),
    ).fetchone()
    if row is None:
        raise RuntimeError(f"GC item {item_id} was not found in {GC_DB_PATH}")
    return GCItem(
        item_id=row[0],
        item_type=row[1],
        title=row[2],
        content=row[3],
        created_at=str(row[4]).replace(" ", "T") + "Z",
        updated_at=str(row[5]).replace(" ", "T") + "Z",
    )


def _artifact_from_gc_item(item: GCItem, *, pipeline_run_id: str) -> dict[str, object]:
    title_line, _, _ = item.content.partition("\n\n")
    raw_text = item.content.strip()
    source_type = {
        "pasted_text": "note",
        "pdf": "pdf",
        "url": "other",
    }.get(item.item_type, "other")
    return {
        "contract": "artifact",
        "version": "v1",
        "artifact_id": f"gc_item_{item.item_id}",
        "source_system": "garbage_collector",
        "source_type": source_type,
        "title": title_line.strip() or item.title,
        "created_at": item.created_at,
        "ingested_at": item.updated_at,
        "content_ref": f"gc://items/{item.item_id}",
        "raw_text": raw_text,
        "mime_type": "text/plain",
        "language": "en",
        "metadata": {
            "gc_item_id": item.item_id,
            "pipeline_run_id": pipeline_run_id,
        },
        "provenance": {
            "origin": "gc_sqlite_item",
            "path": f"items/{item.item_id}",
            "hash_sha256": f"gc-item-{item.item_id}",
        },
    }


def run_remote_workflow_case() -> dict[str, object]:
    from jigsaw.lanes.real_case_lane.case_input_composition import compose_case_from_case_input

    pipeline_run_id = "real-case-remote-workflow"
    generated_at = "2026-03-15T11:45:00Z"

    with sqlite3.connect(GC_DB_PATH) as connection:
        primary_item = _fetch_gc_item(connection, PRIMARY_ITEM_ID)
        supporting_items = [_fetch_gc_item(connection, item_id) for item_id in SUPPORTING_ITEM_IDS]

    artifact = validate_artifact_v1(_artifact_from_gc_item(primary_item, pipeline_run_id=pipeline_run_id))
    extraction = validate_extraction_v1(
        artifact_to_extraction(
            artifact,
            pipeline_run_id=pipeline_run_id,
            generated_at=generated_at,
        ).model_dump(mode="python")
    )
    chunks = [
        validate_chunk_v1(chunk.model_dump(mode="python"))
        for chunk in extraction_to_chunks(
            extraction,
            artifact=artifact,
            pipeline_run_id=pipeline_run_id,
            generated_at=generated_at,
        )
    ]
    judgment_request = validate_judgment_request_v1(
        chunks_to_judgment_request(
            artifact,
            chunks,
            pipeline_run_id=pipeline_run_id,
            analysis_profile="real_remote_workflow_case",
            generated_at=generated_at,
        ).model_dump(mode="python")
    )

    gc_context = build_gc_context_snapshot(
        {
        "primary_item_id": primary_item.item_id,
        "related_item_ids": [item.item_id for item in supporting_items],
        "summary": "Assess whether this remote workflow opportunity is ready to package for review.",
        "freshness": "recent",
        "known_gaps": [],
        "source_types": [primary_item.item_type] + [item.item_type for item in supporting_items],
        }
    )
    hypothesis_state = hypothesis_state_from_gc_context(
        gc_context,
        question_or_claim="Should this remote workflow opportunity be packaged for review?",
    )
    case_input = build_case_input(hypothesis_state, gc_context)
    composition = compose_case_from_case_input(
        case_input,
        {
            "primary_item": primary_item.__dict__,
            "supporting_items": [item.__dict__ for item in supporting_items],
        },
        pipeline_run_id=pipeline_run_id,
        generated_at=generated_at,
    )
    kernel_input = validate_kernel_input_v1(composition["kernel_input"])
    bundle_result = validate_kernel_bundle_result_v1(composition["kernel_bundle_result"])
    arbiter_request = kernel_bundle_result_to_arbiter_request(kernel_input, bundle_result)
    arbiter_response = adjudicate_via_current_arbiter(arbiter_request)

    _dump_json(OUTPUT_DIR / "gc_primary_item.json", primary_item.__dict__)
    _dump_json(OUTPUT_DIR / "gc_supporting_items.json", [item.__dict__ for item in supporting_items])
    _dump_json(OUTPUT_DIR / "gc_context.json", gc_context.model_dump(mode="python"))
    _dump_json(OUTPUT_DIR / "hypothesis_state.json", hypothesis_state.model_dump(mode="python"))
    _dump_json(OUTPUT_DIR / "case_input.json", case_input.model_dump(mode="python"))
    _dump_json(OUTPUT_DIR / "artifact.json", artifact.model_dump(mode="python"))
    _dump_json(OUTPUT_DIR / "extraction.json", extraction.model_dump(mode="python"))
    _dump_json(OUTPUT_DIR / "chunks.json", [chunk.model_dump(mode="python") for chunk in chunks])
    _dump_json(OUTPUT_DIR / "judgment_request.json", judgment_request.model_dump(mode="python"))
    _dump_json(OUTPUT_DIR / "kernel_input.json", kernel_input.model_dump(mode="python"))
    _dump_json(OUTPUT_DIR / "kernel_exchanges.json", composition["kernel_exchanges"])
    _dump_json(OUTPUT_DIR / "kernel_bundle_result.json", bundle_result.model_dump(mode="python"))
    _dump_json(OUTPUT_DIR / "arbiter_request.json", arbiter_request)
    _dump_json(OUTPUT_DIR / "arbiter_response.json", arbiter_response)
    _dump_json(
        OUTPUT_DIR / "run_log.json",
        {
            "pipeline_run_id": pipeline_run_id,
            "generated_at": generated_at,
            "gc_primary_item_id": primary_item.item_id,
            "gc_supporting_item_ids": [item.item_id for item in supporting_items],
            "hypothesis_id": hypothesis_state.hypothesis_id,
            "controller_state": hypothesis_state.state,
            "controller_next_probe": hypothesis_state.next_probe,
            "case_id": case_input.case_id,
            "artifact_id": artifact.artifact_id,
            "kernel_input_id": kernel_input.input_id,
            "bundle_judgment": bundle_result.composed_summary.bundle_judgment,
            "bundle_confidence": bundle_result.metadata.confidence,
            "arbiter_judgement": arbiter_response["judgement"],
            "recommended_action": arbiter_response["recommended_action"],
            "status": "success",
        },
    )

    return {
        "gc_primary_item_id": primary_item.item_id,
        "gc_supporting_item_ids": [item.item_id for item in supporting_items],
        "hypothesis_id": hypothesis_state.hypothesis_id,
        "controller_state": hypothesis_state.state,
        "case_id": case_input.case_id,
        "bundle_judgment": bundle_result.composed_summary.bundle_judgment,
        "bundle_confidence": bundle_result.metadata.confidence or 0.0,
        "arbiter_judgement": arbiter_response["judgement"],
        "recommended_action": arbiter_response["recommended_action"],
        "status": "success",
    }


if __name__ == "__main__":
    result = run_remote_workflow_case()
    print(json.dumps(result, indent=2))
