from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from jigsaw.engines.exchange_manager import KernelExchangeV1
from jigsaw.lanes.kernel_lane.models import KernelOutputV1


@dataclass(frozen=True)
class KernelRunResult:
    kernel_name: str
    engine_mode: str
    validated_output: KernelOutputV1
    kernel_exchange: KernelExchangeV1 | None = None
    raw_model_output: dict[str, Any] | None = None
    generated_payload: dict[str, Any] | None = None
    model_name: str | None = None
    retries_used: int = 0
    elapsed_seconds: float | None = None
