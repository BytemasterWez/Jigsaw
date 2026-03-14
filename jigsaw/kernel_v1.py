from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from pydantic import BaseModel, Field

from .envelope import CandidateItem, EvidenceRecord, ExplanationRecord, MessageEnvelope


SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "kernel_v1.schema.json"


class KernelSubject(BaseModel):
    subject_type: str
    subject_id: str


class KernelEvidence(BaseModel):
    evidence_type: str
    source_id: str
    source_item_id: str
    snippet: str
    relevance: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    observed_at: str
    provenance: dict[str, Any]


class KernelSignals(BaseModel):
    relevance: float = Field(ge=0, le=1)
    novelty: float = Field(ge=0, le=1)
    actionability: float = Field(ge=0, le=1)
    recurrence: float = Field(ge=0, le=1)


class KernelMatchedTarget(BaseModel):
    target_id: str
    label: str
    strength: float = Field(ge=0, le=1)


class KernelOutputs(BaseModel):
    matched_targets: list[KernelMatchedTarget]
    recommended_action: str
    tags: list[str]


class KernelProvenance(BaseModel):
    generated_at: str
    source_system: str
    engine_version: str


class KernelResultV1(BaseModel):
    contract_version: str
    engine_name: str
    subject: KernelSubject
    summary: str
    classification: str
    score: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    rationale: str
    evidence: list[KernelEvidence]
    signals: KernelSignals
    outputs: KernelOutputs
    provenance: KernelProvenance


def load_kernel_v1_schema() -> dict[str, Any]:
    with SCHEMA_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_kernel_v1_payload(payload: dict[str, Any]) -> None:
    Draft202012Validator(load_kernel_v1_schema()).validate(payload)


def kernel_result_to_envelope(payload: dict[str, Any], workflow: str = "kernel_v1_ingest") -> MessageEnvelope:
    validate_kernel_v1_payload(payload)
    result = KernelResultV1.model_validate(payload)

    candidate = CandidateItem(
        candidate_id=result.subject.subject_id,
        kind=result.subject.subject_type,
        title=f"{result.engine_name}:{result.classification}",
        source=result.provenance.source_system,
        summary=result.summary,
        attributes={
            "classification": result.classification,
            "recommended_action": result.outputs.recommended_action,
            "tags": result.outputs.tags,
            "engine_name": result.engine_name,
        },
    )
    envelope = MessageEnvelope(workflow=workflow, candidate=candidate)
    envelope.evidence = [
        EvidenceRecord(
            evidence_id=record.source_id,
            kind=record.evidence_type,
            value=record.snippet,
            source=record.provenance.get("source_system", result.provenance.source_system),
            provenance=record.provenance,
            confidence=record.confidence,
        )
        for record in result.evidence
    ]
    envelope.scores["kernel_score"] = result.score
    envelope.scores["kernel_confidence"] = result.confidence
    envelope.scores["fit"] = result.signals.relevance
    envelope.scores["confidence"] = result.confidence
    envelope.explanation = ExplanationRecord(
        summary=result.summary,
        why_now=result.rationale,
        supporting_points=[target.label for target in result.outputs.matched_targets],
        gaps=[] if result.evidence else ["No direct evidence records were supplied."],
    )
    envelope.metadata["kernel_v1"] = result.model_dump(mode="python")
    envelope.metadata["kernel_signals"] = result.signals.model_dump(mode="python")
    envelope.add_trace(
        step="kernel_v1.ingest",
        actor="adapter",
        summary=f"Ingested {result.engine_name} result into Jigsaw envelope.",
        payload={
            "classification": result.classification,
            "score": result.score,
            "confidence": result.confidence,
            "matched_targets": len(result.outputs.matched_targets),
        },
    )
    return envelope
