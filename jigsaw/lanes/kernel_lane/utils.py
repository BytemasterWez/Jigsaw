from __future__ import annotations

from ..artifact_lane.models import MetadataV1
from ..artifact_lane.utils import make_id, utc_now


def build_metadata(
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


__all__ = ["build_metadata", "make_id", "utc_now"]

