from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator

from ..artifact_lane.models import MetadataV1


class KernelInputEvidenceV1(BaseModel):
    evidence_id: str
    kind: str
    text: str
    confidence: float = Field(ge=0, le=1)
    observed_at: str
    provenance: dict[str, Any]


class KernelInputContentV1(BaseModel):
    title: str
    summary: str
    observed_items: list[dict[str, Any]] = Field(default_factory=list)
    expected_items: list[dict[str, Any]] = Field(default_factory=list)
    claims: list[dict[str, Any]] = Field(default_factory=list)


class KernelInputV1(BaseModel):
    contract: str = "kernel_input"
    version: str = "v1"
    input_id: str
    subject_id: str
    subject_type: str
    content: KernelInputContentV1
    context: dict[str, Any] = Field(default_factory=dict)
    evidence: list[KernelInputEvidenceV1]
    metadata: MetadataV1

    @model_validator(mode="after")
    def ensure_evidence_present(self) -> "KernelInputV1":
        if not self.evidence:
            raise ValueError("KernelInputV1 must include at least one evidence record.")
        return self


class KernelOutputV1(BaseModel):
    contract: str = "kernel_output"
    version: str = "v1"
    output_id: str
    kernel_type: str
    input_id: str
    status: str
    judgment: str
    confidence: float = Field(ge=0, le=1)
    reasons: list[str] = Field(default_factory=list)
    evidence_used: list[str] = Field(default_factory=list)
    metadata: MetadataV1


class KernelBundleSummaryV1(BaseModel):
    bundle_judgment: str
    summary: str


class KernelBundleResultV1(BaseModel):
    contract: str = "kernel_bundle_result"
    version: str = "v1"
    bundle_id: str
    input_id: str
    kernel_outputs: list[KernelOutputV1]
    composed_summary: KernelBundleSummaryV1
    composition_notes: list[str] = Field(default_factory=list)
    metadata: MetadataV1

