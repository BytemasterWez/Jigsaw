# Jigsaw Architecture Overview

## Scope

This repository implements the **Jigsaw** component in isolation.

- Garbage Collector is treated as an external memory service.
- Arbiter is treated as an external judgment service.
- Jigsaw is responsible for gathering, transforming, and packaging evidence in a form those systems can consume.

The proof-of-concept stays intentionally narrow: **document or opportunity triage**.

## Core Sentence

Garbage Collector remembers, Jigsaw Kernels gather and transform evidence, Arbiter decides whether action is permitted.

## Design Goal

Prove that a kernelized evidence pipeline is:

- more inspectable than a monolithic agent step
- easier to gate than a direct action path
- auditable through a shared message envelope and explicit trace records

## Isolation Boundary

Jigsaw depends on two interfaces only:

1. `MemoryAdapter`
   - retrieves prior cases and context
   - persists completed decision traces

2. `ArbiterAdapter`
   - evaluates the assembled envelope
   - returns `approve`, `reject`, `watchlist`, or `escalate`

Everything else is internal to Jigsaw.

## Main Runtime Flow

1. A candidate item enters the Jigsaw pipeline.
2. Jigsaw asks the memory adapter for similar prior cases.
3. The shared envelope is created.
4. Kernels run in a fixed sequence:
   - `retrieve`
   - `score`
   - `infer_consequence`
   - `rank`
   - `explain`
5. Each kernel reads and writes the same envelope shape.
6. Jigsaw sends the fully populated envelope to the Arbiter.
7. The Arbiter returns a gated decision.
8. Jigsaw persists the final trace through the memory adapter.
9. Mock action executes only on `approve`.

## Repository Shape

```text
.
├── ARCHITECTURE_OVERVIEW.md
├── MESSAGE_BUS_SCHEMA.md
├── MEMORY_CONTRACT.md
├── ARBITER_DECISION_CONTRACT.md
├── CLAIM_OF_PROOF.md
├── FRAMEWORK_OVERVIEW.md
├── INTEGRATION_NOTES.md
├── README.md
├── SYSTEM_POSITIONING.md
├── pyproject.toml
└── jigsaw/
    ├── __init__.py
    ├── adapters.py
    ├── benchmark.py
    ├── contracts.py
    ├── demo_data.py
    ├── envelope.py
    ├── kernels.py
    ├── mappings.py
    ├── pipeline.py
    └── runner.py
```

## Success Criteria

The proof is successful if:

- the same envelope flows through every kernel
- every kernel contribution is traceable
- Arbiter receives enough structured evidence to gate action
- approved actions are mock-executed and logged
- benchmark output shows the behavioral difference between ungated and gated paths
