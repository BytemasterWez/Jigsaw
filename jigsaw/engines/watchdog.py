from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from pydantic import BaseModel

from jigsaw.engines.exchange_manager import KernelExchangeV1


REPO_ROOT = Path(__file__).resolve().parents[2]
KERNEL_WATCHDOG_RESULT_SCHEMA_PATH = REPO_ROOT / "contracts" / "kernel_watchdog_result" / "v1.json"
LM_ENGINE_MODES = {"lmstudio"}
REQUIRED_EXCHANGE_FIELDS = {
    "contract",
    "version",
    "exchange_id",
    "kernel_name",
    "engine_mode",
    "case_id",
    "input_packet",
    "output_packet",
    "validation_passed",
    "engine_metadata",
    "timestamp",
}


class KernelWatchdogResultV1(BaseModel):
    contract: str = "kernel_watchdog_result"
    version: str = "v1"
    watchdog_id: str
    exchange_id: str
    kernel_name: str
    verdict: str
    reasons: list[str]
    timestamp: str


def _load_schema(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_kernel_watchdog_result_v1(payload: dict[str, Any]) -> KernelWatchdogResultV1:
    Draft202012Validator(_load_schema(KERNEL_WATCHDOG_RESULT_SCHEMA_PATH)).validate(payload)
    return KernelWatchdogResultV1.model_validate(payload)


def inspect_kernel_exchange(
    exchange: KernelExchangeV1 | dict[str, Any],
    *,
    expected_kernel_name: str | None = None,
    expected_engine_mode: str | None = None,
    timestamp: str | None = None,
) -> KernelWatchdogResultV1:
    payload = exchange.model_dump(mode="python") if isinstance(exchange, KernelExchangeV1) else dict(exchange)
    kernel_name = str(payload.get("kernel_name") or expected_kernel_name or "unknown")
    exchange_id = str(payload.get("exchange_id") or f"missing-exchange:{kernel_name}")
    result_timestamp = str(timestamp or payload.get("timestamp") or "")

    fail_reasons: list[str] = []
    warn_reasons: list[str] = []

    missing_fields = sorted(field for field in REQUIRED_EXCHANGE_FIELDS if field not in payload)
    if missing_fields:
        fail_reasons.append(f"missing_required_fields:{','.join(missing_fields)}")

    if payload.get("contract") != "kernel_exchange":
        fail_reasons.append("unexpected_exchange_contract")

    if expected_kernel_name and payload.get("kernel_name") != expected_kernel_name:
        fail_reasons.append("kernel_name_mismatch")

    if expected_engine_mode and payload.get("engine_mode") != expected_engine_mode:
        fail_reasons.append("engine_mode_mismatch")

    if payload.get("validation_passed") is False:
        fail_reasons.append("kernel_output_validation_failed")

    output_packet = payload.get("output_packet")
    if not isinstance(output_packet, dict) or not output_packet:
        fail_reasons.append("missing_output_packet")

    input_packet = payload.get("input_packet")
    if not isinstance(input_packet, dict) or not input_packet:
        warn_reasons.append("missing_or_empty_input_packet")

    engine_mode = payload.get("engine_mode")
    engine_metadata = payload.get("engine_metadata")
    if engine_mode in LM_ENGINE_MODES:
        if not isinstance(engine_metadata, dict) or not engine_metadata:
            warn_reasons.append("missing_engine_metadata_for_lm_mode")

    if not result_timestamp:
        fail_reasons.append("missing_timestamp")

    if fail_reasons:
        verdict = "fail"
        reasons = fail_reasons + warn_reasons
    elif warn_reasons:
        verdict = "warn"
        reasons = warn_reasons
    else:
        verdict = "pass"
        reasons = []

    return validate_kernel_watchdog_result_v1(
        {
            "contract": "kernel_watchdog_result",
            "version": "v1",
            "watchdog_id": f"kw:{exchange_id}",
            "exchange_id": exchange_id,
            "kernel_name": kernel_name,
            "verdict": verdict,
            "reasons": reasons,
            "timestamp": result_timestamp,
        }
    )


def inspect_kernel_exchanges(
    exchanges: list[KernelExchangeV1 | dict[str, Any]],
    *,
    expected_engine_modes: dict[str, str] | None = None,
    timestamp: str | None = None,
) -> list[KernelWatchdogResultV1]:
    return [
        inspect_kernel_exchange(
            exchange,
            expected_kernel_name=str((exchange.model_dump(mode="python") if isinstance(exchange, KernelExchangeV1) else exchange).get("kernel_name") or "unknown"),
            expected_engine_mode=(expected_engine_modes or {}).get(
                str((exchange.model_dump(mode="python") if isinstance(exchange, KernelExchangeV1) else exchange).get("kernel_name") or "")
            ),
            timestamp=timestamp,
        )
        for exchange in exchanges
    ]
