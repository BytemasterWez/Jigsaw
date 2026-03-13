from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .contracts import ArbiterAdapter, Kernel, MemoryAdapter, PipelineResult
from .envelope import ActionRecord, CandidateItem, MessageEnvelope, utc_now


@dataclass
class JigsawPipeline:
    memory: MemoryAdapter
    arbiter: ArbiterAdapter
    kernels: list[Kernel]
    audit_path: Path | None = None

    def evaluate(self, candidate: CandidateItem, memory_limit: int = 3) -> PipelineResult:
        envelope = MessageEnvelope(workflow="document_or_opportunity_triage", candidate=candidate)
        envelope.add_trace(
            step="start",
            actor="pipeline",
            summary="Initialized Jigsaw envelope.",
            payload={"candidate_id": candidate.candidate_id},
        )

        try:
            envelope.memory_context = self.memory.retrieve_similar_cases(candidate, limit=memory_limit)
            envelope.add_trace(
                step="memory.retrieve",
                actor="memory_adapter",
                summary="Retrieved prior cases from external memory.",
                payload={"count": len(envelope.memory_context)},
            )
        except Exception as exc:  # pragma: no cover
            envelope.memory_context = []
            envelope.add_trace(
                step="memory.retrieve",
                actor="memory_adapter",
                summary="Memory retrieval failed.",
                payload={"error": str(exc)},
            )

        for kernel in self.kernels:
            envelope = kernel.run(envelope)

        envelope.arbiter_request = {
            "evidence_count": len(envelope.evidence),
            "fit": envelope.scores.get("fit"),
            "confidence": envelope.scores.get("confidence"),
            "priority": envelope.priority.level if envelope.priority else None,
            "downside": envelope.consequences.get("downside"),
        }
        envelope.add_trace(
            step="arbiter.request",
            actor="pipeline",
            summary="Prepared structured gating request for Arbiter.",
            payload=envelope.arbiter_request.copy(),
        )

        envelope.arbiter_decision = self.arbiter.decide(envelope)
        envelope.add_trace(
            step="arbiter.decision",
            actor="arbiter_adapter",
            summary=f"Arbiter returned {envelope.arbiter_decision.decision}.",
            payload={
                "decision": envelope.arbiter_decision.decision,
                "confidence": envelope.arbiter_decision.confidence,
                "reason": envelope.arbiter_decision.reason,
            },
        )

        action_executed = False
        if envelope.arbiter_decision.decision == "approve":
            envelope.action = ActionRecord(
                status="mock_executed",
                target="mock://triage_queue",
                notes=f"Approved candidate {candidate.candidate_id} queued for follow-up.",
                executed_at=utc_now(),
            )
            action_executed = True
        else:
            envelope.action = ActionRecord(
                status="blocked",
                target="mock://triage_queue",
                notes=f"Action blocked by Arbiter with decision {envelope.arbiter_decision.decision}.",
                executed_at=utc_now(),
            )

        envelope.add_trace(
            step="action",
            actor="pipeline",
            summary="Recorded mocked action outcome.",
            payload={"status": envelope.action.status, "target": envelope.action.target},
        )

        self.memory.persist_trace(envelope)
        self._append_audit(envelope)
        return PipelineResult(envelope=envelope, action_executed=action_executed)

    def _append_audit(self, envelope: MessageEnvelope) -> None:
        if self.audit_path is None:
            return
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        with self.audit_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(envelope.to_dict(), default=str) + "\n")
