from __future__ import annotations

from dataclasses import dataclass

from .models import (
    ArtifactV1,
    ChunkV1,
    ExtractionV1,
    JudgmentRequestChunkV1,
    JudgmentRequestContextV1,
    JudgmentRequestEvidenceV1,
    JudgmentRequestSubjectV1,
    JudgmentRequestV1,
    MetadataV1,
)
from .utils import estimate_tokens, make_id, sha256_text, utc_now


@dataclass(frozen=True)
class ChunkBounds:
    text: str
    char_start: int
    char_end: int
    section_label: str


def _metadata(
    object_id: str,
    *,
    source_system: str,
    pipeline_run_id: str,
    confidence: float | None = None,
    tags: list[str] | None = None,
    lineage: list[str] | None = None,
    created_at: str | None = None,
) -> MetadataV1:
    timestamp = created_at or utc_now()
    return MetadataV1(
        object_id=object_id,
        created_at=timestamp,
        updated_at=timestamp,
        source_system=source_system,
        pipeline_run_id=pipeline_run_id,
        confidence=confidence,
        tags=tags or [],
        lineage=lineage or [],
    )


def artifact_to_extraction(
    artifact: ArtifactV1,
    *,
    pipeline_run_id: str,
    generated_at: str | None = None,
) -> ExtractionV1:
    generated_at = generated_at or utc_now()
    extraction_id = make_id("extraction", artifact.artifact_id)
    sections = []
    running_offset = 0
    for index, section_text in enumerate([part.strip() for part in artifact.raw_text.split("\n\n") if part.strip()], start=1):
        section_start = artifact.raw_text.find(section_text, running_offset)
        section_end = section_start + len(section_text)
        running_offset = section_end
        sections.append(
            {
                "label": f"section_{index}",
                "char_start": section_start,
                "char_end": section_end,
            }
        )

    return ExtractionV1(
        extraction_id=extraction_id,
        artifact_id=artifact.artifact_id,
        status="success",
        extracted_text=artifact.raw_text,
        sections=sections,
        tables=[],
        entities=[],
        warnings=[],
        metadata=_metadata(
            extraction_id,
            source_system=artifact.source_system,
            pipeline_run_id=pipeline_run_id,
            confidence=1.0,
            tags=["artifact-lane", "extraction"],
            lineage=[artifact.artifact_id],
            created_at=generated_at,
        ),
        provenance={
            "source_artifact_id": artifact.artifact_id,
            "transform": "artifact_to_extraction",
            "transform_version": "v1",
        },
    )


def _split_extraction_text(extracted_text: str, max_chars: int) -> list[ChunkBounds]:
    paragraphs = [part.strip() for part in extracted_text.split("\n\n") if part.strip()]
    if not paragraphs:
        return [ChunkBounds(text=extracted_text.strip(), char_start=0, char_end=len(extracted_text.strip()), section_label="body")]

    chunks: list[ChunkBounds] = []
    running_offset = 0
    buffer = ""
    buffer_start = 0
    section_index = 1
    for paragraph in paragraphs:
        paragraph_start = extracted_text.find(paragraph, running_offset)
        paragraph_end = paragraph_start + len(paragraph)
        running_offset = paragraph_end
        proposed = paragraph if not buffer else f"{buffer}\n\n{paragraph}"
        if buffer and len(proposed) > max_chars:
            chunks.append(
                ChunkBounds(
                    text=buffer,
                    char_start=buffer_start,
                    char_end=buffer_start + len(buffer),
                    section_label=f"section_{section_index}",
                )
            )
            section_index += 1
            buffer = paragraph
            buffer_start = paragraph_start
        else:
            if not buffer:
                buffer_start = paragraph_start
            buffer = proposed

    if buffer:
        chunks.append(
            ChunkBounds(
                text=buffer,
                char_start=buffer_start,
                char_end=buffer_start + len(buffer),
                section_label=f"section_{section_index}",
            )
        )
    return chunks


def extraction_to_chunks(
    extraction: ExtractionV1,
    *,
    artifact: ArtifactV1,
    pipeline_run_id: str,
    max_chars: int = 1200,
    generated_at: str | None = None,
) -> list[ChunkV1]:
    generated_at = generated_at or utc_now()
    chunks: list[ChunkV1] = []
    for index, bounds in enumerate(_split_extraction_text(extraction.extracted_text, max_chars=max_chars), start=1):
        chunk_id = make_id("chunk", artifact.artifact_id, str(index))
        chunks.append(
            ChunkV1(
                chunk_id=chunk_id,
                artifact_id=artifact.artifact_id,
                extraction_id=extraction.extraction_id,
                sequence=index,
                text=bounds.text,
                char_start=bounds.char_start,
                char_end=bounds.char_end,
                token_estimate=estimate_tokens(bounds.text),
                section_label=bounds.section_label,
                metadata=_metadata(
                    chunk_id,
                    source_system=artifact.source_system,
                    pipeline_run_id=pipeline_run_id,
                    confidence=1.0,
                    tags=["artifact-lane", "chunk"],
                    lineage=[artifact.artifact_id, extraction.extraction_id],
                    created_at=generated_at,
                ),
                provenance={
                    "source_artifact_id": artifact.artifact_id,
                    "source_extraction_id": extraction.extraction_id,
                    "transform": "extraction_to_chunks",
                    "transform_version": "v1",
                },
            )
        )
    return chunks


def chunks_to_judgment_request(
    artifact: ArtifactV1,
    chunks: list[ChunkV1],
    *,
    pipeline_run_id: str,
    analysis_profile: str = "default",
    generated_at: str | None = None,
) -> JudgmentRequestV1:
    generated_at = generated_at or utc_now()
    request_id = make_id("judgment_request", artifact.artifact_id, analysis_profile)
    return JudgmentRequestV1(
        request_id=request_id,
        artifact_id=artifact.artifact_id,
        subject=JudgmentRequestSubjectV1(
            title=artifact.title,
            type="document" if artifact.source_type in {"pdf", "note", "email", "other"} else "record",
        ),
        context=JudgmentRequestContextV1(
            source_system=artifact.source_system,
            source_type=artifact.source_type,
            analysis_profile=analysis_profile,
        ),
        chunks=[
            JudgmentRequestChunkV1(
                chunk_id=chunk.chunk_id,
                text=chunk.text,
                section_label=chunk.section_label,
            )
            for chunk in chunks
        ],
        evidence=JudgmentRequestEvidenceV1(
            provenance={
                "artifact_id": artifact.artifact_id,
                "chunk_count": len(chunks),
                "lineage": [artifact.artifact_id] + [chunk.chunk_id for chunk in chunks],
            },
            hash_sha256=sha256_text([artifact.provenance.hash_sha256] + [chunk.text for chunk in chunks]),
        ),
        metadata=_metadata(
            request_id,
            source_system=artifact.source_system,
            pipeline_run_id=pipeline_run_id,
            confidence=1.0,
            tags=["artifact-lane", "judgment-request"],
            lineage=[artifact.artifact_id] + [chunk.chunk_id for chunk in chunks],
            created_at=generated_at,
        ),
    )

