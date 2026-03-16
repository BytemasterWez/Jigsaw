from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Literal

from jsonschema import Draft202012Validator
from pydantic import BaseModel, Field

from .case_manager import CaseStateV1, validate_case_state_v1
from .hypothesis_controller import GCContextSnapshotV1, validate_gc_context_snapshot_v1


REPO_ROOT = Path(__file__).resolve().parents[2]
CASE_RELEVANCE_SIGNAL_SCHEMA_PATH = REPO_ROOT / "contracts" / "case_relevance_signal" / "v1.json"

RecommendedEffectValue = Literal["ignore", "attach_context", "reopen_case"]

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
    "item",
    "case",
    "should",
    "after",
    "review",
}


class CaseRelevanceSignalV1(BaseModel):
    contract: str = "case_relevance_signal"
    version: str = "v1"
    signal_id: str
    case_id: str
    candidate_item_id: str
    match_score: float = Field(ge=0, le=1)
    match_reason: str
    recommended_effect: RecommendedEffectValue
    timestamp: str


def _load_schema(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_case_relevance_signal_v1(payload: dict[str, Any]) -> CaseRelevanceSignalV1:
    Draft202012Validator(_load_schema(CASE_RELEVANCE_SIGNAL_SCHEMA_PATH)).validate(payload)
    return CaseRelevanceSignalV1.model_validate(payload)


def _tokenize(value: str) -> set[str]:
    parts = re.findall(r"[a-z0-9]+", value.lower())
    return {part for part in parts if len(part) >= 3 and part not in STOPWORDS}


def _jaccard_overlap(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def _normalize_candidate_item(payload: dict[str, Any]) -> dict[str, Any]:
    item_id = payload.get("candidate_item_id") or payload.get("item_id")
    if item_id is None:
        raise ValueError("candidate item payload must include candidate_item_id or item_id")
    candidate_item_id = str(item_id)
    if candidate_item_id.isdigit():
        candidate_item_id = f"gc:item:{candidate_item_id}"

    title = str(payload.get("title", "")).strip()
    content = str(payload.get("content", "")).strip()
    related_item_ids = [int(item) for item in payload.get("related_item_ids", [])]
    source_types = [str(value) for value in payload.get("source_types", [])]
    topic_hints = [str(value).lower() for value in payload.get("topic_hints", [])]

    return {
        "candidate_item_id": candidate_item_id,
        "title": title,
        "content": content,
        "related_item_ids": related_item_ids,
        "source_types": source_types,
        "topic_hints": topic_hints,
    }


def _match_reason(
    *,
    title_overlap: float,
    keyword_overlap: float,
    related_overlap: float,
    topic_overlap: float,
) -> str:
    parts: list[str] = []
    if title_overlap > 0:
        parts.append(f"title overlap {round(title_overlap, 2)}")
    if keyword_overlap > 0:
        parts.append(f"keyword overlap {round(keyword_overlap, 2)}")
    if related_overlap > 0:
        parts.append(f"related evidence overlap {round(related_overlap, 2)}")
    if topic_overlap > 0:
        parts.append(f"topic hint overlap {round(topic_overlap, 2)}")
    if not parts:
        return "No meaningful overlap with the existing case context."
    return ", ".join(parts) + "."


def _recommended_effect(match_score: float) -> RecommendedEffectValue:
    if match_score >= 0.65:
        return "reopen_case"
    if match_score >= 0.35:
        return "attach_context"
    return "ignore"


def build_case_relevance_signal(
    case_state: CaseStateV1 | dict[str, Any],
    case_gc_context: GCContextSnapshotV1 | dict[str, Any],
    candidate_item: dict[str, Any],
    *,
    timestamp: str,
) -> CaseRelevanceSignalV1:
    state = case_state if isinstance(case_state, CaseStateV1) else validate_case_state_v1(case_state)
    snapshot = case_gc_context if isinstance(case_gc_context, GCContextSnapshotV1) else validate_gc_context_snapshot_v1(case_gc_context)
    candidate = _normalize_candidate_item(candidate_item)

    case_title_tokens = _tokenize(snapshot.surface_summary)
    candidate_title_tokens = _tokenize(candidate["title"])
    title_overlap = _jaccard_overlap(case_title_tokens, candidate_title_tokens)

    case_keyword_tokens = _tokenize(" ".join([snapshot.surface_summary, state.hypothesis_id, state.case_id]))
    candidate_keyword_tokens = _tokenize(candidate["content"])
    keyword_overlap = _jaccard_overlap(case_keyword_tokens, candidate_keyword_tokens)

    existing_related = {snapshot.primary_item_id, *snapshot.related_item_ids}
    candidate_related = set(candidate["related_item_ids"])
    related_overlap = 0.0
    if existing_related and candidate_related:
        related_overlap = len(existing_related & candidate_related) / len(existing_related | candidate_related)

    case_topics = _tokenize(" ".join(snapshot.source_types + snapshot.known_gaps))
    candidate_topics = set(candidate["topic_hints"]) | _tokenize(" ".join(candidate["source_types"]))
    topic_overlap = _jaccard_overlap(case_topics, candidate_topics)

    match_score = round(
        min(
            1.0,
            (title_overlap * 0.35) + (keyword_overlap * 0.3) + (related_overlap * 0.2) + (topic_overlap * 0.15),
        ),
        4,
    )
    payload = {
        "contract": "case_relevance_signal",
        "version": "v1",
        "signal_id": f"crs:{state.case_id}:{candidate['candidate_item_id']}",
        "case_id": state.case_id,
        "candidate_item_id": candidate["candidate_item_id"],
        "match_score": match_score,
        "match_reason": _match_reason(
            title_overlap=title_overlap,
            keyword_overlap=keyword_overlap,
            related_overlap=related_overlap,
            topic_overlap=topic_overlap,
        ),
        "recommended_effect": _recommended_effect(match_score),
        "timestamp": timestamp,
    }
    return validate_case_relevance_signal_v1(payload)
