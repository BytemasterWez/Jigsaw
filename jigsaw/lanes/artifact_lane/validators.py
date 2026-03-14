from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from pydantic import BaseModel
from referencing import Registry, Resource

from .models import ArtifactV1, ChunkV1, ExtractionV1, JudgmentRequestV1, JudgmentResponseV1


CONTRACT_ROOT = Path(__file__).resolve().parents[3] / "contracts"


def _load_schema(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _build_registry() -> Registry:
    registry = Registry()
    for path in CONTRACT_ROOT.rglob("*.json"):
        schema = _load_schema(path)
        registry = registry.with_resource(schema["$id"], Resource.from_contents(schema))
    return registry


SCHEMA_REGISTRY = _build_registry()


def _validate_against_schema(schema_path: Path, payload: dict[str, Any]) -> None:
    schema = _load_schema(schema_path)
    Draft202012Validator(schema, registry=SCHEMA_REGISTRY).validate(payload)


def _validate_model(model_type: type[BaseModel], payload: dict[str, Any]) -> BaseModel:
    return model_type.model_validate(payload)


def validate_artifact_v1(payload: dict[str, Any]) -> ArtifactV1:
    _validate_against_schema(CONTRACT_ROOT / "artifact" / "v1.json", payload)
    return _validate_model(ArtifactV1, payload)


def validate_extraction_v1(payload: dict[str, Any]) -> ExtractionV1:
    _validate_against_schema(CONTRACT_ROOT / "extraction" / "v1.json", payload)
    return _validate_model(ExtractionV1, payload)


def validate_chunk_v1(payload: dict[str, Any]) -> ChunkV1:
    _validate_against_schema(CONTRACT_ROOT / "chunk" / "v1.json", payload)
    return _validate_model(ChunkV1, payload)


def validate_judgment_request_v1(payload: dict[str, Any]) -> JudgmentRequestV1:
    _validate_against_schema(CONTRACT_ROOT / "judgment_request" / "v1.json", payload)
    return _validate_model(JudgmentRequestV1, payload)


def validate_judgment_response_v1(payload: dict[str, Any]) -> JudgmentResponseV1:
    _validate_against_schema(CONTRACT_ROOT / "judgment_response" / "v1.json", payload)
    return _validate_model(JudgmentResponseV1, payload)

