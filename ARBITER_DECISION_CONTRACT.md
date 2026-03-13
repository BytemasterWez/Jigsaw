# Arbiter Decision Contract

## Purpose

Jigsaw assembles evidence. Arbiter decides whether action is permitted.

## Adapter Interface

```python
class ArbiterAdapter(Protocol):
    def decide(self, envelope: MessageEnvelope) -> ArbiterDecision:
        ...
```

## Allowed Decisions

- `approve`
- `reject`
- `watchlist`
- `escalate`

## Minimum Inputs

The Arbiter should inspect:

- candidate metadata
- evidence and provenance
- scores
- inferred consequences
- priority
- explanation
- trace

## Decision Record

The decision written back into the envelope should include:

- decision label
- confidence
- reason
- required follow-up
- timestamp

## Current Integration Reality

Jigsaw's full decision set is:

- `approve`
- `reject`
- `watchlist`
- `escalate`

The current public Arbiter contract exposes:

- `promoted`
- `watchlist`
- `rejected`

The real adapter therefore maps:

- `promoted` -> `approve`
- `watchlist` -> `watchlist`
- `rejected` -> `reject`

`escalate` remains part of the Jigsaw contract, but it is not currently available through the public Arbiter interface.
