from __future__ import annotations

import json
from typing import Any

from .envelope import ArbiterDecision, CandidateItem, MemoryCase, MessageEnvelope, utc_now


def build_candidate_query(candidate: CandidateItem) -> str:
    return f"{candidate.title}\n{candidate.summary}".strip()


def memory_cases_from_gc_search_results(results: list[dict[str, Any]], limit: int) -> list[MemoryCase]:
    grouped: dict[int, dict[str, Any]] = {}

    for result in results:
        item_id = int(result["item_id"])
        current = grouped.get(item_id)
        if current is None or float(result["score"]) > float(current["score"]):
            grouped[item_id] = result

    ordered = sorted(grouped.values(), key=lambda item: float(item["score"]), reverse=True)
    cases: list[MemoryCase] = []
    for result in ordered[:limit]:
        cases.append(
            MemoryCase(
                case_id=f"gc-item-{result['item_id']}",
                outcome="unknown",
                similarity=round(float(result["score"]), 4),
                summary=result["chunk_text"][:280],
                provenance={
                    "source": "garbage_collector_api",
                    "item_id": result["item_id"],
                    "chunk_id": result["chunk_id"],
                    "item_type": result["item_type"],
                    "item_title": result["item_title"],
                    "source_url": result.get("source_url"),
                    "source_filename": result.get("source_filename"),
                },
            )
        )
    return cases


def memory_cases_from_gc_sqlite_rows(rows: list[dict[str, Any]], limit: int) -> list[MemoryCase]:
    ordered = sorted(rows, key=lambda item: float(item["score"]), reverse=True)
    cases: list[MemoryCase] = []

    for row in ordered[:limit]:
        cases.append(
            MemoryCase(
                case_id=f"gc-item-{row['id']}",
                outcome="unknown",
                similarity=round(float(row["score"]), 4),
                summary=row["summary"],
                provenance={
                    "source": "garbage_collector_sqlite",
                    "item_id": row["id"],
                    "item_type": row["item_type"],
                    "title": row["title"],
                    "source_url": row.get("source_url"),
                    "source_filename": row.get("source_filename"),
                },
            )
        )
    return cases


def envelope_to_gc_trace_text(envelope: MessageEnvelope) -> str:
    return "\n".join(
        [
            "[jigsaw_trace]",
            f"candidate_id: {envelope.candidate.candidate_id}",
            f"workflow: {envelope.workflow}",
            f"decision: {envelope.arbiter_decision.decision if envelope.arbiter_decision else 'unknown'}",
            "",
            json.dumps(envelope.to_dict(), indent=2, ensure_ascii=True, default=str),
        ]
    )


def envelope_to_gc_trace_metadata(envelope: MessageEnvelope) -> dict[str, Any]:
    return {
        "item_type": "jigsaw_trace",
        "workflow": envelope.workflow,
        "envelope_id": envelope.envelope_id,
        "candidate_id": envelope.candidate.candidate_id,
        "decision": envelope.arbiter_decision.decision if envelope.arbiter_decision else None,
        "priority": envelope.priority.level if envelope.priority else None,
        "fit": envelope.scores.get("fit"),
        "confidence": envelope.scores.get("confidence"),
        "persisted_at": utc_now(),
    }


def envelope_to_arbiter_request(envelope: MessageEnvelope) -> dict[str, Any]:
    unique_sources = {item.source for item in envelope.evidence}
    freshness_days = int(envelope.candidate.attributes.get("freshness_days", 30))

    request = {
        "candidate_id": envelope.candidate.candidate_id,
        "domain": str(envelope.metadata.get("arbiter_domain", "opportunity_triage")),
        "candidate_type": envelope.candidate.kind,
        "summary": envelope.explanation.summary if envelope.explanation else envelope.candidate.summary,
        "evidence": {
            "source_count": len(unique_sources),
            "freshness_days": max(0, freshness_days),
            "fit_score": float(envelope.scores.get("fit", 0.0)),
            "estimated_value_band": str(
                envelope.candidate.attributes.get("estimated_value_band")
                or envelope.candidate.attributes.get("budget_band")
                or "unknown"
            ),
        },
        "context": {
            "buyer_profile": str(
                envelope.candidate.attributes.get("buyer_profile")
                or envelope.candidate.attributes.get("strategic_fit")
                or envelope.candidate.source
            ),
            "current_queue_pressure": _normalize_band(
                envelope.metadata.get("current_queue_pressure", "medium"),
                allowed={"low", "medium", "high"},
                fallback="medium",
            ),
            "action_cost": _normalize_band(
                envelope.metadata.get("action_cost")
                or envelope.candidate.attributes.get("risk_flag")
                or "medium",
                allowed={"low", "medium", "high"},
                fallback="medium",
            ),
        },
    }
    return request


def arbiter_response_to_decision(response: dict[str, Any]) -> ArbiterDecision:
    judgement = str(response.get("judgement", "rejected"))
    decision_map = {
        "promoted": "approve",
        "watchlist": "watchlist",
        "rejected": "reject",
    }

    decision = decision_map.get(judgement, "reject")
    follow_up = []
    recommended_action = response.get("recommended_action")
    if isinstance(recommended_action, str) and recommended_action:
        follow_up.append(recommended_action)

    key_factors = response.get("key_factors")
    if isinstance(key_factors, list):
        follow_up.extend(str(item) for item in key_factors if str(item))

    return ArbiterDecision(
        decision=decision,  # type: ignore[arg-type]
        confidence=float(response.get("confidence", 0.0)),
        reason=str(response.get("reason_summary", "No reason was provided.")),
        required_follow_up=follow_up,
        checked_at=utc_now(),
    )


def _normalize_band(value: Any, *, allowed: set[str], fallback: str) -> str:
    text = str(value).lower()
    if text in allowed:
        return text
    return fallback
