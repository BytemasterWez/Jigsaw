from __future__ import annotations

from dataclasses import dataclass

from .envelope import EvidenceRecord, ExplanationRecord, MessageEnvelope, PriorityRecord


def _contains(text: str, *needles: str) -> bool:
    lowered = text.lower()
    return any(needle in lowered for needle in needles)


@dataclass
class RetrieveKernel:
    name: str = "retrieve"

    def run(self, envelope: MessageEnvelope) -> MessageEnvelope:
        candidate = envelope.candidate
        evidence: list[EvidenceRecord] = []

        evidence.append(
            EvidenceRecord(
                evidence_id=f"{candidate.candidate_id}-summary",
                kind="candidate_summary",
                value=candidate.summary,
                source=candidate.source,
                provenance={"field": "summary", "candidate_id": candidate.candidate_id},
                confidence=0.8,
            )
        )

        for key, value in candidate.attributes.items():
            evidence.append(
                EvidenceRecord(
                    evidence_id=f"{candidate.candidate_id}-{key}",
                    kind="candidate_attribute",
                    value=f"{key}={value}",
                    source=candidate.source,
                    provenance={"field": key, "candidate_id": candidate.candidate_id},
                    confidence=0.9,
                )
            )

        for case in envelope.memory_context:
            evidence.append(
                EvidenceRecord(
                    evidence_id=f"{candidate.candidate_id}-{case.case_id}",
                    kind="memory_case",
                    value=case.summary,
                    source="memory",
                    provenance=case.provenance,
                    confidence=case.similarity,
                )
            )

        envelope.evidence.extend(evidence)
        envelope.add_trace(
            step=self.name,
            actor="kernel",
            summary="Collected candidate facts and similar cases.",
            payload={"evidence_count": len(evidence), "memory_cases": len(envelope.memory_context)},
        )
        return envelope


@dataclass
class ScoreKernel:
    name: str = "score"

    def run(self, envelope: MessageEnvelope) -> MessageEnvelope:
        summary = envelope.candidate.summary.lower()
        attrs = envelope.candidate.attributes
        fit_score = 0.2
        confidence = 0.4

        if attrs.get("strategic_fit") == "strong":
            fit_score += 0.35
        if attrs.get("budget_band") == "high":
            fit_score += 0.2
        if _contains(summary, "pilot", "automation", "modernization", "executive", "strategic"):
            fit_score += 0.15
        if envelope.memory_context:
            fit_score += min(0.2, max(case.similarity for case in envelope.memory_context) * 0.2)
            confidence += 0.2
        if attrs.get("urgency") in {"this_quarter", "next_quarter"}:
            fit_score += 0.05
        if attrs.get("risk_flag") == "high":
            fit_score -= 0.05

        provenance_ratio = 0.0
        if envelope.evidence:
            with_provenance = sum(1 for item in envelope.evidence if item.provenance)
            provenance_ratio = with_provenance / len(envelope.evidence)
            confidence += provenance_ratio * 0.3

        envelope.scores["fit"] = round(max(0.0, min(1.0, fit_score)), 3)
        envelope.scores["confidence"] = round(max(0.0, min(1.0, confidence)), 3)
        envelope.scores["provenance_coverage"] = round(provenance_ratio, 3)
        envelope.add_trace(
            step=self.name,
            actor="kernel",
            summary="Calculated fit, confidence, and provenance coverage.",
            payload=envelope.scores.copy(),
        )
        return envelope


@dataclass
class InferConsequenceKernel:
    name: str = "infer_consequence"

    def run(self, envelope: MessageEnvelope) -> MessageEnvelope:
        attrs = envelope.candidate.attributes
        fit = envelope.scores.get("fit", 0.0)

        upside = "moderate"
        if fit >= 0.75:
            upside = "high"
        elif fit < 0.45:
            upside = "low"

        downside = "medium" if attrs.get("risk_flag") == "medium" else "low"
        if attrs.get("risk_flag") == "high":
            downside = "high"

        recommended_action = "advance"
        if upside == "low":
            recommended_action = "defer"
        if downside == "high" and upside == "high":
            recommended_action = "review"

        envelope.consequences = {
            "upside": upside,
            "downside": downside,
            "recommended_action": recommended_action,
        }
        envelope.add_trace(
            step=self.name,
            actor="kernel",
            summary="Estimated opportunity upside and downside.",
            payload=envelope.consequences.copy(),
        )
        return envelope


@dataclass
class RankKernel:
    name: str = "rank"

    def run(self, envelope: MessageEnvelope) -> MessageEnvelope:
        fit = envelope.scores.get("fit", 0.0)
        confidence = envelope.scores.get("confidence", 0.0)
        downside = envelope.consequences.get("downside", "medium")

        priority_score = fit * 0.7 + confidence * 0.3
        if downside == "high":
            priority_score -= 0.1

        level = "low"
        if priority_score >= 0.75:
            level = "high"
        elif priority_score >= 0.5:
            level = "medium"

        envelope.priority = PriorityRecord(
            level=level,
            score=round(max(0.0, min(1.0, priority_score)), 3),
            reason=f"Derived from fit={fit:.2f}, confidence={confidence:.2f}, downside={downside}.",
        )
        envelope.add_trace(
            step=self.name,
            actor="kernel",
            summary="Assigned triage priority.",
            payload={
                "level": envelope.priority.level,
                "score": envelope.priority.score,
                "reason": envelope.priority.reason,
            },
        )
        return envelope


@dataclass
class ExplainKernel:
    name: str = "explain"

    def run(self, envelope: MessageEnvelope) -> MessageEnvelope:
        attrs = envelope.candidate.attributes
        support = [
            f"Fit score is {envelope.scores.get('fit', 0.0):.2f}.",
            f"Priority is {envelope.priority.level if envelope.priority else 'unknown'}.",
            f"Retrieved {len(envelope.memory_context)} similar prior case(s).",
        ]
        gaps: list[str] = []

        if attrs.get("strategic_fit") != "strong":
            gaps.append("Strategic alignment is not clearly strong.")
        if attrs.get("budget_band") == "low":
            gaps.append("Budget appears limited.")
        if envelope.consequences.get("downside") == "high":
            gaps.append("Risk or compliance exposure is high.")
        if not envelope.memory_context:
            gaps.append("No similar prior cases were available from memory.")

        envelope.explanation = ExplanationRecord(
            summary=f"{envelope.candidate.title} was evaluated through the Jigsaw kernel chain.",
            why_now=f"Current urgency is {attrs.get('urgency', 'unknown')} and recommended action is {envelope.consequences.get('recommended_action', 'unknown')}.",
            supporting_points=support,
            gaps=gaps,
        )
        envelope.add_trace(
            step=self.name,
            actor="kernel",
            summary="Produced structured rationale for Arbiter review.",
            payload={"supporting_points": len(support), "gaps": gaps},
        )
        return envelope
