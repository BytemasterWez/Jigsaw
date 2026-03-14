from __future__ import annotations

from typing import Any

from .models import ArtifactV1


def gc_payload_to_artifact_v1(payload: dict[str, Any]) -> ArtifactV1:
    """
    Thin adapter for GC-normalized payloads.

    If the payload is already in artifact/v1 shape, this adapter only validates and returns it.
    """
    return ArtifactV1.model_validate(payload)

