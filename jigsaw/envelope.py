from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4


DecisionLabel = Literal["approve", "reject", "watchlist", "escalate"]


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class CandidateItem:
    candidate_id: str
    kind: str
    title: str
    source: str
    summary: str
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryCase:
    case_id: str
    outcome: str
    similarity: float
    summary: str
    provenance: dict[str, Any]


@dataclass
class EvidenceRecord:
    evidence_id: str
    kind: str
    value: str
    source: str
    provenance: dict[str, Any]
    confidence: float


@dataclass
class PriorityRecord:
    level: str
    score: float
    reason: str


@dataclass
class ExplanationRecord:
    summary: str
    why_now: str
    supporting_points: list[str]
    gaps: list[str]


@dataclass
class ArbiterDecision:
    decision: DecisionLabel
    confidence: float
    reason: str
    required_follow_up: list[str]
    checked_at: str


@dataclass
class ActionRecord:
    status: str
    target: str
    notes: str
    executed_at: str


@dataclass
class TraceEvent:
    step: str
    actor: str
    timestamp: str
    summary: str
    payload: dict[str, Any]


@dataclass
class MessageEnvelope:
    workflow: str
    candidate: CandidateItem
    envelope_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=utc_now)
    memory_context: list[MemoryCase] = field(default_factory=list)
    evidence: list[EvidenceRecord] = field(default_factory=list)
    scores: dict[str, float] = field(default_factory=dict)
    consequences: dict[str, Any] = field(default_factory=dict)
    priority: PriorityRecord | None = None
    explanation: ExplanationRecord | None = None
    arbiter_request: dict[str, Any] = field(default_factory=dict)
    arbiter_decision: ArbiterDecision | None = None
    action: ActionRecord | None = None
    trace: list[TraceEvent] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_trace(self, step: str, actor: str, summary: str, payload: dict[str, Any]) -> None:
        self.trace.append(
            TraceEvent(
                step=step,
                actor=actor,
                timestamp=utc_now(),
                summary=summary,
                payload=payload,
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
