from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from pydantic import BaseModel, Field


REPO_ROOT = Path(__file__).resolve().parents[2]
KERNEL_EXCHANGE_SCHEMA_PATH = REPO_ROOT / "contracts" / "kernel_exchange" / "v1.json"


class KernelExchangeV1(BaseModel):
    contract: str = "kernel_exchange"
    version: str = "v1"
    exchange_id: str
    kernel_name: str
    engine_mode: str
    case_id: str
    input_packet: dict[str, Any]
    output_packet: dict[str, Any]
    validation_passed: bool
    engine_metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: str


def _load_schema(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_kernel_exchange_v1(payload: dict[str, Any]) -> KernelExchangeV1:
    Draft202012Validator(_load_schema(KERNEL_EXCHANGE_SCHEMA_PATH)).validate(payload)
    return KernelExchangeV1.model_validate(payload)


def build_kernel_exchange(
    *,
    kernel_name: str,
    engine_mode: str,
    case_id: str,
    input_packet: dict[str, Any],
    output_packet: dict[str, Any],
    validation_passed: bool,
    timestamp: str,
    pipeline_run_id: str,
    engine_metadata: dict[str, Any] | None = None,
) -> KernelExchangeV1:
    payload = {
        "contract": "kernel_exchange",
        "version": "v1",
        "exchange_id": f"kx:{pipeline_run_id}:{kernel_name}",
        "kernel_name": kernel_name,
        "engine_mode": engine_mode,
        "case_id": case_id,
        "input_packet": input_packet,
        "output_packet": output_packet,
        "validation_passed": validation_passed,
        "engine_metadata": engine_metadata or {},
        "timestamp": timestamp,
    }
    return validate_kernel_exchange_v1(payload)
