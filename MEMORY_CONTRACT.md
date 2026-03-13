# Memory Contract

## Purpose

Jigsaw does not implement persistent memory in this proof. It depends on a `MemoryAdapter` interface that can be backed by the existing Garbage Collector.

## Adapter Interface

```python
class MemoryAdapter(Protocol):
    def retrieve_similar_cases(self, candidate: CandidateItem, limit: int = 3) -> list[MemoryCase]:
        ...

    def persist_trace(self, envelope: MessageEnvelope) -> None:
        ...
```

## Expectations

- retrieval returns prior cases with outcome, summary, similarity, and provenance
- persistence stores the final envelope or equivalent normalized trace
- retrieval failure may degrade to empty context, but must be traced
- persistence failure should not be silent

## Current Integration Reality

The existing Garbage Collector implementation exposes retrieval and generic item ingestion, but not a dedicated trace-ingestion contract.

Current adapter strategy:

- prefer Garbage Collector retrieval API when available
- fallback to the existing SQLite schema when needed
- persist Jigsaw traces as `jigsaw_trace` rows in SQLite or as generic pasted text through the existing HTTP API
