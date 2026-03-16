from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from pydantic import BaseModel, Field


REPO_ROOT = Path(__file__).resolve().parents[3]
ARBITER_EXCHANGE_SCHEMA_PATH = REPO_ROOT / "contracts" / "arbiter_exchange" / "v1.json"


class ArbiterExchangeV1(BaseModel):
    contract: str = "arbiter_exchange"
    version: str = "v1"
    exchange_id: str
    case_id: str
    sent_packet: dict[str, Any]
    received_packet: dict[str, Any]
    validation_passed: bool
    arbiter_metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: str


def _load_schema(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_arbiter_exchange_v1(payload: dict[str, Any]) -> ArbiterExchangeV1:
    Draft202012Validator(_load_schema(ARBITER_EXCHANGE_SCHEMA_PATH)).validate(payload)
    return ArbiterExchangeV1.model_validate(payload)


def build_arbiter_exchange(
    *,
    case_id: str,
    sent_packet: dict[str, Any],
    received_packet: dict[str, Any],
    validation_passed: bool,
    timestamp: str,
    exchange_scope: str,
    arbiter_metadata: dict[str, Any] | None = None,
) -> ArbiterExchangeV1:
    payload = {
        "contract": "arbiter_exchange",
        "version": "v1",
        "exchange_id": f"ax:{exchange_scope}:{case_id}",
        "case_id": case_id,
        "sent_packet": sent_packet,
        "received_packet": received_packet,
        "validation_passed": validation_passed,
        "arbiter_metadata": arbiter_metadata or {},
        "timestamp": timestamp,
    }
    return validate_arbiter_exchange_v1(payload)
