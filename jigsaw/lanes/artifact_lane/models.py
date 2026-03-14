from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator


class MetadataV1(BaseModel):
    object_id: str
    schema_version: str = "v1"
    created_at: str
    updated_at: str
    source_system: str
    pipeline_run_id: str
    confidence: float | None = Field(default=None, ge=0, le=1)
    tags: list[str] = Field(default_factory=list)
    lineage: list[str] = Field(default_factory=list)


class ArtifactProvenanceV1(BaseModel):
    origin: str
    path: str
    hash_sha256: str


class ArtifactV1(BaseModel):
    contract: str = "artifact"
    version: str = "v1"
    artifact_id: str
    source_system: str
    source_type: str
    title: str
    created_at: str
    ingested_at: str
    content_ref: str
    raw_text: str
    mime_type: str
    language: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    provenance: ArtifactProvenanceV1

    @model_validator(mode="after")
    def ensure_raw_text_present(self) -> "ArtifactV1":
        if not self.raw_text.strip():
            raise ValueError("Artifact raw_text must not be empty.")
        return self


class ExtractionProvenanceV1(BaseModel):
    source_artifact_id: str
    transform: str = "artifact_to_extraction"
    transform_version: str = "v1"


class ExtractionV1(BaseModel):
    contract: str = "extraction"
    version: str = "v1"
    extraction_id: str
    artifact_id: str
    status: str
    extracted_text: str
    sections: list[dict[str, Any]] = Field(default_factory=list)
    tables: list[dict[str, Any]] = Field(default_factory=list)
    entities: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metadata: MetadataV1
    provenance: ExtractionProvenanceV1


class ChunkProvenanceV1(BaseModel):
    source_artifact_id: str
    source_extraction_id: str
    transform: str = "extraction_to_chunks"
    transform_version: str = "v1"


class ChunkV1(BaseModel):
    contract: str = "chunk"
    version: str = "v1"
    chunk_id: str
    artifact_id: str
    extraction_id: str
    sequence: int = Field(ge=1)
    text: str
    char_start: int = Field(ge=0)
    char_end: int = Field(ge=0)
    token_estimate: int = Field(ge=0)
    section_label: str = ""
    metadata: MetadataV1
    provenance: ChunkProvenanceV1

    @model_validator(mode="after")
    def ensure_valid_offsets(self) -> "ChunkV1":
        if self.char_end < self.char_start:
            raise ValueError("Chunk char_end must be greater than or equal to char_start.")
        if not self.text.strip():
            raise ValueError("Chunk text must not be empty.")
        return self


class JudgmentRequestSubjectV1(BaseModel):
    title: str
    type: str


class JudgmentRequestContextV1(BaseModel):
    source_system: str
    source_type: str
    analysis_profile: str = "default"


class JudgmentRequestChunkV1(BaseModel):
    chunk_id: str
    text: str
    section_label: str = ""


class JudgmentRequestEvidenceV1(BaseModel):
    provenance: dict[str, Any]
    hash_sha256: str


class JudgmentRequestV1(BaseModel):
    contract: str = "judgment_request"
    version: str = "v1"
    request_id: str
    artifact_id: str
    subject: JudgmentRequestSubjectV1
    context: JudgmentRequestContextV1
    chunks: list[JudgmentRequestChunkV1]
    evidence: JudgmentRequestEvidenceV1
    metadata: MetadataV1

    @model_validator(mode="after")
    def ensure_chunks_present(self) -> "JudgmentRequestV1":
        if not self.chunks:
            raise ValueError("JudgmentRequestV1 must contain at least one chunk.")
        return self


class JudgmentResponseV1(BaseModel):
    contract: str = "judgment_response"
    version: str = "v1"
    response_id: str
    request_id: str
    status: str
    decision: str
    score: float = Field(ge=0, le=1)
    summary: str
    reasons: list[str] = Field(default_factory=list)
    evidence_used: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metadata: MetadataV1

