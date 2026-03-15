from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from jigsaw.lanes.artifact_lane.transforms import (
    artifact_to_extraction,
    chunks_to_judgment_request,
    extraction_to_chunks,
)
from jigsaw.lanes.artifact_lane.validators import (
    validate_artifact_v1,
    validate_extraction_v1,
    validate_chunk_v1,
    validate_judgment_request_v1,
)
from jigsaw.lanes.kernel_lane.arbiter_integration import (
    adjudicate_via_current_arbiter,
    kernel_bundle_result_to_arbiter_request,
)
from jigsaw.lanes.kernel_lane.compose import compose_kernel_bundle
from jigsaw.lanes.kernel_lane.kernels import run_contradiction, run_expected_state, run_observed_state
from jigsaw.lanes.kernel_lane.models import KernelInputV1
from jigsaw.lanes.kernel_lane.validators import (
    validate_kernel_bundle_result_v1,
    validate_kernel_input_v1,
    validate_kernel_output_v1,
)


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
    title_line, _, body = item.content.partition("\n\n")
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


def _build_kernel_input(
    primary_item: GCItem,
    supporting_items: list[GCItem],
    *,
    pipeline_run_id: str,
    generated_at: str,
) -> KernelInputV1:
    supporting_lookup = {item.item_id: item for item in supporting_items}
    item_8 = supporting_lookup[8]
    item_22 = supporting_lookup[22]
    item_14 = supporting_lookup[14]

    payload = {
        "contract": "kernel_input",
        "version": "v1",
        "input_id": f"kin_gc_{primary_item.item_id}",
        "subject_id": f"gc_case:remote_workflow:{primary_item.item_id}",
        "subject_type": "opportunity_case",
        "content": {
            "title": primary_item.title,
            "summary": (
                "A remote workflow opportunity case assembled from live Garbage Collector notes "
                "covering workflow automation, consulting use, pricing, and basic operations."
            ),
            "observed_items": [
                {"name": "workflow_automation_focus", "value": True},
                {"name": "consulting_use_case_defined", "value": True},
                {"name": "offer_pricing_defined", "value": True},
                {"name": "operations_scaffold_present", "value": True},
            ],
            "expected_items": [
                {"name": "workflow_automation_focus", "target_value": True},
                {"name": "consulting_use_case_defined", "target_value": True},
                {"name": "offer_pricing_defined", "target_value": True},
                {"name": "operations_scaffold_present", "target_value": True},
            ],
            "claims": [],
        },
        "context": {
            "minimum_expected_observations": 4,
            "analysis_profile": "real_remote_workflow_case",
            "gc_primary_item_id": primary_item.item_id,
            "gc_supporting_item_ids": [item.item_id for item in supporting_items],
        },
        "evidence": [
            {
                "evidence_id": f"gc_ev_{primary_item.item_id}",
                "kind": "observation",
                "text": primary_item.content.strip(),
                "confidence": 0.82,
                "observed_at": primary_item.updated_at,
                "provenance": {
                    "source_system": "garbage_collector",
                    "item_id": primary_item.item_id,
                },
            },
            {
                "evidence_id": f"gc_ev_{item_8.item_id}",
                "kind": "observation",
                "text": item_8.content.strip(),
                "confidence": 0.8,
                "observed_at": item_8.updated_at,
                "provenance": {
                    "source_system": "garbage_collector",
                    "item_id": item_8.item_id,
                },
            },
            {
                "evidence_id": f"gc_ev_{item_22.item_id}",
                "kind": "observation",
                "text": item_22.content.strip(),
                "confidence": 0.79,
                "observed_at": item_22.updated_at,
                "provenance": {
                    "source_system": "garbage_collector",
                    "item_id": item_22.item_id,
                },
            },
            {
                "evidence_id": f"gc_ev_{item_14.item_id}",
                "kind": "observation",
                "text": item_14.content.strip(),
                "confidence": 0.72,
                "observed_at": item_14.updated_at,
                "provenance": {
                    "source_system": "garbage_collector",
                    "item_id": item_14.item_id,
                },
            },
        ],
        "metadata": {
            "object_id": f"kin_gc_{primary_item.item_id}",
            "schema_version": "v1",
            "created_at": generated_at,
            "updated_at": generated_at,
            "source_system": "garbage_collector",
            "pipeline_run_id": pipeline_run_id,
            "confidence": 0.8,
            "tags": ["real-case-lane", "remote-workflow"],
            "lineage": [f"gc:item:{primary_item.item_id}"]
            + [f"gc:item:{item.item_id}" for item in supporting_items],
        },
    }
    return validate_kernel_input_v1(payload)


def run_remote_workflow_case() -> dict[str, object]:
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

    kernel_input = _build_kernel_input(
        primary_item,
        supporting_items,
        pipeline_run_id=pipeline_run_id,
        generated_at=generated_at,
    )
    observed_output = validate_kernel_output_v1(
        run_observed_state(kernel_input, pipeline_run_id=pipeline_run_id, generated_at=generated_at).model_dump(mode="python")
    )
    expected_output = validate_kernel_output_v1(
        run_expected_state(kernel_input, pipeline_run_id=pipeline_run_id, generated_at=generated_at).model_dump(mode="python")
    )
    contradiction_output = validate_kernel_output_v1(
        run_contradiction(kernel_input, pipeline_run_id=pipeline_run_id, generated_at=generated_at).model_dump(mode="python")
    )
    bundle_result = validate_kernel_bundle_result_v1(
        compose_kernel_bundle(
            kernel_input,
            [observed_output, expected_output, contradiction_output],
            pipeline_run_id=pipeline_run_id,
            generated_at=generated_at,
        ).model_dump(mode="python")
    )
    arbiter_request = kernel_bundle_result_to_arbiter_request(kernel_input, bundle_result)
    arbiter_response = adjudicate_via_current_arbiter(arbiter_request)

    _dump_json(OUTPUT_DIR / "gc_primary_item.json", primary_item.__dict__)
    _dump_json(OUTPUT_DIR / "gc_supporting_items.json", [item.__dict__ for item in supporting_items])
    _dump_json(OUTPUT_DIR / "artifact.json", artifact.model_dump(mode="python"))
    _dump_json(OUTPUT_DIR / "extraction.json", extraction.model_dump(mode="python"))
    _dump_json(OUTPUT_DIR / "chunks.json", [chunk.model_dump(mode="python") for chunk in chunks])
    _dump_json(OUTPUT_DIR / "judgment_request.json", judgment_request.model_dump(mode="python"))
    _dump_json(OUTPUT_DIR / "kernel_input.json", kernel_input.model_dump(mode="python"))
    _dump_json(OUTPUT_DIR / "observed_state.json", observed_output.model_dump(mode="python"))
    _dump_json(OUTPUT_DIR / "expected_state.json", expected_output.model_dump(mode="python"))
    _dump_json(OUTPUT_DIR / "contradiction.json", contradiction_output.model_dump(mode="python"))
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
        "bundle_judgment": bundle_result.composed_summary.bundle_judgment,
        "bundle_confidence": bundle_result.metadata.confidence or 0.0,
        "arbiter_judgement": arbiter_response["judgement"],
        "recommended_action": arbiter_response["recommended_action"],
        "status": "success",
    }


if __name__ == "__main__":
    result = run_remote_workflow_case()
    print(json.dumps(result, indent=2))
