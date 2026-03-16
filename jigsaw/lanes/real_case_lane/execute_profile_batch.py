from __future__ import annotations

import json
import re
import sqlite3
import sys
import tomllib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from jigsaw.controller.hypothesis_controller import build_case_input, build_gc_context_snapshot, hypothesis_state_from_gc_context
from jigsaw.lanes.artifact_lane.transforms import artifact_to_extraction, chunks_to_judgment_request, extraction_to_chunks
from jigsaw.lanes.artifact_lane.validators import (
    validate_artifact_v1,
    validate_chunk_v1,
    validate_extraction_v1,
    validate_judgment_request_v1,
)
from jigsaw.lanes.kernel_lane.arbiter_integration import adjudicate_via_current_arbiter, kernel_bundle_result_to_arbiter_request
from jigsaw.lanes.kernel_lane.validators import (
    validate_kernel_bundle_result_v1,
    validate_kernel_input_v1,
)
from jigsaw.lanes.real_case_lane.execute_remote_workflow_case import GC_DB_PATH, GCItem, _artifact_from_gc_item, _fetch_gc_item


REPO_ROOT = Path(__file__).resolve().parents[3]
PROFILES_DIR = REPO_ROOT / "profiles"
DEFAULT_PROFILE = "remote_workflow_v1b"

STOPWORDS = {
    "this",
    "that",
    "with",
    "from",
    "into",
    "your",
    "have",
    "will",
    "about",
    "ideas",
    "note",
    "notes",
    "title",
}


@dataclass(frozen=True)
class CandidateScore:
    item: GCItem
    score: int
    overlap_score: int = 0
    profile_score: int = 0


def _dump_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def load_execution_profile(profile_name: str = DEFAULT_PROFILE) -> dict[str, Any]:
    profile_path = PROFILES_DIR / f"{profile_name}.toml"
    if not profile_path.exists():
        raise RuntimeError(f"Execution profile {profile_name} does not exist at {profile_path}")
    with profile_path.open("rb") as handle:
        return tomllib.load(handle)


def _load_all_gc_items() -> list[GCItem]:
    with sqlite3.connect(GC_DB_PATH) as connection:
        rows = connection.execute(
            """
            SELECT id, item_type, title, content, created_at, updated_at
            FROM items
            ORDER BY updated_at DESC, id DESC
            """
        ).fetchall()
    items: list[GCItem] = []
    for row in rows:
        items.append(
            GCItem(
                item_id=row[0],
                item_type=row[1],
                title=row[2],
                content=row[3],
                created_at=str(row[4]).replace(" ", "T") + "Z",
                updated_at=str(row[5]).replace(" ", "T") + "Z",
            )
        )
    return items


def _tokenize(value: str) -> set[str]:
    parts = re.findall(r"[a-z0-9]+", value.lower())
    return {part for part in parts if len(part) >= 3 and part not in STOPWORDS}


def _keyword_score(text: str, terms: list[str]) -> int:
    lowered = text.lower()
    return sum(1 for term in terms if term.lower() in lowered)


def _sort_key(item: GCItem) -> tuple[datetime, int]:
    return (datetime.fromisoformat(item.updated_at.replace("Z", "+00:00")), item.item_id)


def _cluster_key(item: GCItem) -> str:
    title = item.title.strip().lower()
    if not title:
        return f"id:{item.item_id}"
    return re.sub(r"\s+", " ", title)


def select_primary_items(profile: dict[str, Any], items: list[GCItem], *, case_limit: int | None = None) -> list[GCItem]:
    selection = profile["selection"]
    terms = selection["primary_terms"]
    min_score = int(selection["primary_min_score"])
    limit = case_limit or int(selection["primary_case_limit"])
    diversify = bool(selection.get("primary_diversify_clusters", False))
    low_band_threshold = int(selection.get("primary_low_band_threshold", min_score))

    scored: list[CandidateScore] = []
    for item in items:
        text = f"{item.title}\n{item.content}"
        score = _keyword_score(text, terms)
        if score >= min_score:
            scored.append(CandidateScore(item=item, score=score))

    scored.sort(key=lambda record: (-record.score, _sort_key(record.item)[0], _sort_key(record.item)[1]))

    if not diversify:
        return [record.item for record in scored[:limit]]

    selected: list[GCItem] = []
    seen_clusters: set[str] = set()
    low_band_candidates: list[GCItem] = []
    for record in scored:
        cluster = _cluster_key(record.item)
        if cluster in seen_clusters:
            continue
        if record.score <= low_band_threshold:
            low_band_candidates.append(record.item)
            continue
        selected.append(record.item)
        seen_clusters.add(cluster)
        if len(selected) >= max(0, limit - 1):
            break

    if low_band_candidates and len(selected) < limit:
        selected.append(low_band_candidates[0])

    for record in scored:
        if len(selected) >= limit:
            break
        if record.item.item_id in {item.item_id for item in selected}:
            continue
        cluster = _cluster_key(record.item)
        if cluster in seen_clusters:
            continue
        selected.append(record.item)
        seen_clusters.add(cluster)

    return selected[:limit]


def select_supporting_items(profile: dict[str, Any], primary_item: GCItem, items: list[GCItem]) -> list[GCItem]:
    selection = profile["selection"]
    profile_terms = selection["supporting_terms"]
    min_score = int(selection["supporting_min_score"])
    max_items = int(selection["max_supporting_items"])
    max_per_cluster = int(selection.get("supporting_max_per_cluster", max_items))
    include_weak_support = bool(selection.get("supporting_require_one_weaker_item", False))
    weak_band_max = int(selection.get("supporting_weak_band_max_score", min_score + 1))
    primary_tokens = _tokenize(f"{primary_item.title}\n{primary_item.content}")

    scored: list[CandidateScore] = []
    for item in items:
        if item.item_id == primary_item.item_id:
            continue
        item_text = f"{item.title}\n{item.content}"
        item_tokens = _tokenize(item_text)
        overlap_score = len(primary_tokens & item_tokens)
        profile_score = _keyword_score(item_text, profile_terms)
        total_score = overlap_score + profile_score
        if total_score >= min_score:
            scored.append(CandidateScore(item=item, score=total_score, overlap_score=overlap_score, profile_score=profile_score))

    scored.sort(key=lambda record: (-record.score, _sort_key(record.item)[0], _sort_key(record.item)[1]))

    selected: list[GCItem] = []
    cluster_counts: dict[str, int] = {}
    weaker_candidates: list[GCItem] = []
    for record in scored:
        cluster = _cluster_key(record.item)
        current_cluster_count = cluster_counts.get(cluster, 0)
        if current_cluster_count >= max_per_cluster:
            continue
        if include_weak_support and record.score <= weak_band_max:
            weaker_candidates.append(record.item)
            continue
        selected.append(record.item)
        cluster_counts[cluster] = current_cluster_count + 1
        if len(selected) >= max(0, max_items - (1 if include_weak_support else 0)):
            break

    if include_weak_support and weaker_candidates and len(selected) < max_items:
        selected.append(weaker_candidates[0])
        cluster = _cluster_key(weaker_candidates[0])
        cluster_counts[cluster] = cluster_counts.get(cluster, 0) + 1

    for record in scored:
        if len(selected) >= max_items:
            break
        if record.item.item_id in {item.item_id for item in selected}:
            continue
        cluster = _cluster_key(record.item)
        current_cluster_count = cluster_counts.get(cluster, 0)
        if current_cluster_count >= max_per_cluster:
            continue
        selected.append(record.item)
        cluster_counts[cluster] = current_cluster_count + 1

    return selected[:max_items]


def _case_signal_value(signal_terms: list[str], texts: list[str]) -> bool:
    combined = "\n".join(texts).lower()
    return any(term.lower() in combined for term in signal_terms)


def _signal_support_count(signal_terms: list[str], texts: list[str]) -> int:
    count = 0
    lowered_terms = [term.lower() for term in signal_terms]
    for text in texts:
        lowered = text.lower()
        if any(term in lowered for term in lowered_terms):
            count += 1
    return count


def _build_kernel_input_for_profile(
    profile: dict[str, Any],
    primary_item: GCItem,
    supporting_items: list[GCItem],
    *,
    pipeline_run_id: str,
    generated_at: str,
) -> Any:
    shaping = profile["shaping"]
    signal_terms = shaping["signal_terms"]
    texts = [primary_item.content] + [item.content for item in supporting_items]
    primary_text = primary_item.content
    require_primary_anchor = bool(shaping.get("require_primary_signal_anchor", False))
    min_signal_support = int(shaping.get("minimum_signal_support_count", 1))

    def signal_value(signal_key: str) -> bool:
        terms = signal_terms[signal_key]
        primary_match = _case_signal_value(terms, [primary_text])
        support_count = _signal_support_count(terms, texts)
        if require_primary_anchor and not primary_match:
            return False
        return support_count >= min_signal_support

    observed_items = [
        {"name": "workflow_automation_focus", "value": signal_value("workflow_automation_focus")},
        {"name": "consulting_use_case_defined", "value": signal_value("consulting_use_case_defined")},
        {"name": "offer_pricing_defined", "value": signal_value("offer_pricing_defined")},
        {"name": "operations_scaffold_present", "value": signal_value("operations_scaffold_present")},
    ]
    expected_items = [{"name": item["name"], "target_value": True} for item in observed_items]
    summary = (
        f"A remote-workflow opportunity case assembled from GC material for primary item {primary_item.item_id}, "
        f"with {len(supporting_items)} supporting items under profile {profile['profile_name']}."
    )
    evidence = []
    for item in [primary_item] + supporting_items:
        evidence.append(
            {
                "evidence_id": f"gc_ev_{item.item_id}",
                "kind": "observation",
                "text": item.content.strip(),
                "confidence": 0.78 if item.item_id == primary_item.item_id else 0.72,
                "observed_at": item.updated_at,
                "provenance": {
                    "source_system": "garbage_collector",
                    "item_id": item.item_id,
                },
            }
        )

    payload = {
        "contract": "kernel_input",
        "version": "v1",
        "input_id": f"kin_gc_{primary_item.item_id}_{profile['profile_name']}",
        "subject_id": f"gc_case:{profile['profile_name']}:{primary_item.item_id}",
        "subject_type": "opportunity_case",
        "content": {
            "title": primary_item.title,
            "summary": summary,
            "observed_items": observed_items,
            "expected_items": expected_items,
            "claims": [],
        },
        "context": {
            "minimum_expected_observations": int(shaping["minimum_expected_observations"]),
            "analysis_profile": profile["profile_name"],
            "gc_primary_item_id": primary_item.item_id,
            "gc_supporting_item_ids": [item.item_id for item in supporting_items],
        },
        "evidence": evidence,
        "metadata": {
            "object_id": f"kin_gc_{primary_item.item_id}_{profile['profile_name']}",
            "schema_version": "v1",
            "created_at": generated_at,
            "updated_at": generated_at,
            "source_system": "garbage_collector",
            "pipeline_run_id": pipeline_run_id,
            "confidence": 0.78,
            "tags": ["execution-profile", profile["profile_name"]],
            "lineage": [f"gc:item:{primary_item.item_id}"] + [f"gc:item:{item.item_id}" for item in supporting_items],
        },
    }
    return validate_kernel_input_v1(payload)


def _known_gaps_for_profile(profile: dict[str, Any], primary_item: GCItem, supporting_items: list[GCItem]) -> list[str]:
    signal_terms = profile["shaping"]["signal_terms"]
    texts = [primary_item.content] + [item.content for item in supporting_items]
    missing: list[str] = []
    gap_labels = {
        "workflow_automation_focus": "workflow automation focus is not yet clear",
        "consulting_use_case_defined": "consulting use case is not yet clearly framed",
        "offer_pricing_defined": "pricing is not yet clearly defined",
        "operations_scaffold_present": "operational setup is still incomplete",
    }
    for signal_key, terms in signal_terms.items():
        if not _case_signal_value(terms, texts):
            missing.append(gap_labels.get(signal_key, signal_key))
    return missing


def _run_one_case(profile: dict[str, Any], primary_item: GCItem, supporting_items: list[GCItem], output_dir: Path, case_index: int) -> dict[str, Any]:
    from jigsaw.lanes.real_case_lane.case_input_composition import compose_case_from_case_input

    pipeline_run_id = f"{profile['profile_name']}-case-{case_index:02d}"
    generated_at = "2026-03-15T12:15:00Z"

    artifact = validate_artifact_v1(_artifact_from_gc_item(primary_item, pipeline_run_id=pipeline_run_id))
    extraction = validate_extraction_v1(
        artifact_to_extraction(artifact, pipeline_run_id=pipeline_run_id, generated_at=generated_at).model_dump(mode="python")
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
            analysis_profile=profile["profile_name"],
            generated_at=generated_at,
        ).model_dump(mode="python")
    )
    gc_context = build_gc_context_snapshot(
        {
        "primary_item_id": primary_item.item_id,
        "related_item_ids": [item.item_id for item in supporting_items],
        "summary": f"Assess whether GC item {primary_item.item_id} should be packaged as a remote workflow opportunity case.",
        "freshness": "recent",
        "known_gaps": _known_gaps_for_profile(profile, primary_item, supporting_items),
        "source_types": [primary_item.item_type] + [item.item_type for item in supporting_items],
        }
    )
    hypothesis_state = hypothesis_state_from_gc_context(
        gc_context,
        question_or_claim=f"Should GC item {primary_item.item_id} be packaged for remote workflow review?",
        controller_config=profile.get("controller"),
    )
    case_input = build_case_input(hypothesis_state, gc_context)
    composition = compose_case_from_case_input(
        case_input,
        {
            "primary_item": primary_item.__dict__,
            "supporting_items": [item.__dict__ for item in supporting_items],
        },
        profile_name=profile["profile_name"],
        pipeline_run_id=pipeline_run_id,
        generated_at=generated_at,
    )
    kernel_input = validate_kernel_input_v1(composition["kernel_input"])
    bundle_result = validate_kernel_bundle_result_v1(composition["kernel_bundle_result"])
    arbiter_request = kernel_bundle_result_to_arbiter_request(kernel_input, bundle_result)
    arbiter_response = adjudicate_via_current_arbiter(arbiter_request)

    _dump_json(output_dir / "primary_item.json", primary_item.__dict__)
    _dump_json(output_dir / "supporting_items.json", [item.__dict__ for item in supporting_items])
    _dump_json(output_dir / "gc_context.json", gc_context.model_dump(mode="python"))
    _dump_json(output_dir / "hypothesis_state.json", hypothesis_state.model_dump(mode="python"))
    _dump_json(output_dir / "case_input.json", case_input.model_dump(mode="python"))
    _dump_json(output_dir / "artifact.json", artifact.model_dump(mode="python"))
    _dump_json(output_dir / "extraction.json", extraction.model_dump(mode="python"))
    _dump_json(output_dir / "chunks.json", [chunk.model_dump(mode="python") for chunk in chunks])
    _dump_json(output_dir / "judgment_request.json", judgment_request.model_dump(mode="python"))
    _dump_json(output_dir / "kernel_input.json", kernel_input.model_dump(mode="python"))
    _dump_json(output_dir / "kernel_exchanges.json", composition["kernel_exchanges"])
    _dump_json(output_dir / "kernel_bundle_result.json", bundle_result.model_dump(mode="python"))
    _dump_json(output_dir / "arbiter_request.json", arbiter_request)
    _dump_json(output_dir / "arbiter_response.json", arbiter_response)

    case_summary = {
        "profile_name": profile["profile_name"],
        "primary_item_id": primary_item.item_id,
        "supporting_item_ids": [item.item_id for item in supporting_items],
        "hypothesis_id": hypothesis_state.hypothesis_id,
        "controller_state": hypothesis_state.state,
        "controller_next_probe": hypothesis_state.next_probe,
        "case_id": case_input.case_id,
        "bundle_judgment": bundle_result.composed_summary.bundle_judgment,
        "bundle_confidence": bundle_result.metadata.confidence,
        "arbiter_fit_score": arbiter_request["evidence"]["fit_score"],
        "arbiter_judgement": arbiter_response["judgement"],
        "recommended_action": arbiter_response["recommended_action"],
        "kernel_engines": composition["case_summary"]["kernel_engines"],
        "kernel_runtime": composition["case_summary"]["kernel_runtime"],
        "shaping_issues": [] if supporting_items else ["no_supporting_items"],
    }
    _dump_json(output_dir / "case_summary.json", case_summary)
    return case_summary


def _summary_markdown(profile: dict[str, Any], cases: list[dict[str, Any]]) -> str:
    promoted = sum(1 for case in cases if case["arbiter_judgement"] == "promoted")
    watchlist = sum(1 for case in cases if case["arbiter_judgement"] == "watchlist")
    rejected = sum(1 for case in cases if case["arbiter_judgement"] == "rejected")
    lines = [
        f"# Execution Profile Summary: {profile['profile_name']}",
        "",
        f"- cases_run: `{len(cases)}`",
        f"- promoted: `{promoted}`",
        f"- watchlist: `{watchlist}`",
        f"- rejected: `{rejected}`",
        "",
        "## Case outcomes",
        "",
        "| case | primary | supporting | bundle | confidence | fit_score | arbiter |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for index, case in enumerate(cases, start=1):
        lines.append(
            f"| {index} | `{case['primary_item_id']}` | `{case['supporting_item_ids']}` | "
            f"`{case['bundle_judgment']}` | `{case['bundle_confidence']}` | "
            f"`{case['arbiter_fit_score']}` | `{case['arbiter_judgement']}` |"
        )
    lines.extend(
        [
            "",
            "## Honest note",
            "",
            "This batch uses one fixed execution profile and one fixed shaping process. "
            "Different outcomes are expected because the case material differs; the process stays fixed.",
        ]
    )
    return "\n".join(lines) + "\n"


def run_profile_batch(
    profile_name: str = DEFAULT_PROFILE,
    *,
    case_limit: int | None = None,
    output_root_override: str | Path | None = None,
) -> dict[str, Any]:
    profile = load_execution_profile(profile_name)
    output_root = Path(output_root_override) if output_root_override else REPO_ROOT / profile["outputs"]["root"]
    output_root.mkdir(parents=True, exist_ok=True)
    _write_text(output_root / "profile_used.toml", (PROFILES_DIR / f"{profile_name}.toml").read_text(encoding="utf-8"))

    items = _load_all_gc_items()
    primary_items = select_primary_items(profile, items, case_limit=case_limit)
    cases: list[dict[str, Any]] = []
    for index, primary_item in enumerate(primary_items, start=1):
        supporting_items = select_supporting_items(profile, primary_item, items)
        case_output_dir = output_root / f"case_{index:02d}_gc_{primary_item.item_id}"
        cases.append(_run_one_case(profile, primary_item, supporting_items, case_output_dir, index))

    summary = {
        "profile_name": profile["profile_name"],
        "profile_version": profile["profile_version"],
        "cases_run": len(cases),
        "promoted": sum(1 for case in cases if case["arbiter_judgement"] == "promoted"),
        "watchlist": sum(1 for case in cases if case["arbiter_judgement"] == "watchlist"),
        "rejected": sum(1 for case in cases if case["arbiter_judgement"] == "rejected"),
        "cases": cases,
    }
    _dump_json(output_root / "summary.json", summary)
    _write_text(output_root / "SUMMARY.md", _summary_markdown(profile, cases))
    return summary


if __name__ == "__main__":
    profile_name = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PROFILE
    result = run_profile_batch(profile_name)
    print(json.dumps(result, indent=2))
