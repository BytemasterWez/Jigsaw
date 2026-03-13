# Message Bus Schema

## Purpose

All Jigsaw kernels accept and return the same message envelope.

This schema is Jigsaw's public capability-layer contract. It is independent of any specific Garbage Collector or Arbiter implementation.

## Envelope Fields

```python
MessageEnvelope(
    envelope_id: str,
    workflow: str,
    created_at: str,
    candidate: CandidateItem,
    memory_context: list[MemoryCase],
    evidence: list[EvidenceRecord],
    scores: dict[str, float],
    consequences: dict[str, str | float],
    priority: PriorityRecord | None,
    explanation: ExplanationRecord | None,
    arbiter_request: dict[str, object],
    arbiter_decision: ArbiterDecision | None,
    action: ActionRecord | None,
    trace: list[TraceEvent],
    metadata: dict[str, object],
)
```

## Kernel I/O Contract

Each kernel must:

1. accept a `MessageEnvelope`
2. return a `MessageEnvelope`
3. append a new `TraceEvent`
4. write outputs into designated envelope fields

## Trace Questions

Every step should preserve enough detail to answer:

- what evidence was used
- what changed
- why the next decision was possible
- where the data came from
