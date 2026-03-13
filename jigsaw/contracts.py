from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .envelope import ArbiterDecision, CandidateItem, MemoryCase, MessageEnvelope


class Kernel(Protocol):
    name: str

    def run(self, envelope: MessageEnvelope) -> MessageEnvelope:
        ...


class MemoryAdapter(Protocol):
    def retrieve_similar_cases(self, candidate: CandidateItem, limit: int = 3) -> list[MemoryCase]:
        ...

    def persist_trace(self, envelope: MessageEnvelope) -> None:
        ...


class ArbiterAdapter(Protocol):
    def decide(self, envelope: MessageEnvelope) -> ArbiterDecision:
        ...


@dataclass
class PipelineResult:
    envelope: MessageEnvelope
    action_executed: bool
