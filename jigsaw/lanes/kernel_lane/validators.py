from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from .models import KernelBundleResultV1, KernelInputV1, KernelOutputV1


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


def _validate(schema_path: Path, payload: dict[str, Any]) -> None:
    schema = _load_schema(schema_path)
    Draft202012Validator(schema, registry=SCHEMA_REGISTRY).validate(payload)


def validate_kernel_input_v1(payload: dict[str, Any]) -> KernelInputV1:
    _validate(CONTRACT_ROOT / "kernel_input" / "v1.json", payload)
    return KernelInputV1.model_validate(payload)


def validate_kernel_output_v1(payload: dict[str, Any]) -> KernelOutputV1:
    _validate(CONTRACT_ROOT / "kernel_output" / "v1.json", payload)
    return KernelOutputV1.model_validate(payload)


def validate_kernel_bundle_result_v1(payload: dict[str, Any]) -> KernelBundleResultV1:
    _validate(CONTRACT_ROOT / "kernel_bundle_result" / "v1.json", payload)
    return KernelBundleResultV1.model_validate(payload)

