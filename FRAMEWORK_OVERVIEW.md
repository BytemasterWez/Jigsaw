# Framework Overview

This architecture is still a **three-repository system**, but the current Jigsaw repo now contains more explicit internal structure than the older public framing showed.

At the current state:

- **Garbage Collector** is the substrate repo
- **Jigsaw** contains the Controller, composition runtime, execution profiles, and product artifact generation
- **Arbiter** is the judgment membrane repo

The strongest proven slice is the governed forward pass.

## Current Layers

### Garbage Collector

- ingests arbitrary material
- preserves provenance
- links related items
- surfaces grounded context

### Controller

- owns `hypothesis_state`
- transitions state
- selects `next_probe`
- emits `case_input` when a branch is ready to package

### Jigsaw Composition Layer

- consumes `case_input`
- runs bounded kernels
- composes `kernel_bundle_result`
- supports deterministic and LM-backed kernel execution

### Arbiter

- consumes the bounded case through a narrow public membrane
- returns `promoted`, `watchlist`, or `rejected`

### Product Layer

- generates opportunity briefs
- generates summary reports
- emits Markdown and static HTML artifacts

## How They Connect

```mermaid
flowchart TD
    GC["Garbage Collector<br/>substrate intelligence"]
    CTRL["Controller<br/>exploration state"]
    JIG["Jigsaw<br/>composition + runtime"]
    ARB["Arbiter<br/>judgment membrane"]
    PROD["Product artifacts<br/>briefs + summaries"]

    GC -->|gc_context_snapshot| CTRL
    CTRL -->|hypothesis_state / case_input| JIG
    JIG -->|kernel_bundle_result| ARB
    ARB -->|arbiter_response| PROD

    style GC fill:#2d4a3e,color:#fff
    style CTRL fill:#3f4a2d,color:#fff
    style JIG fill:#2d3a4a,color:#fff
    style ARB fill:#4a2d2d,color:#fff
    style PROD fill:#3a3a3a,color:#fff
```

```mermaid
sequenceDiagram
    participant GC as Garbage Collector
    participant C as Controller
    participant J as Jigsaw
    participant A as Arbiter
    participant P as Product

    GC-->>C: gc_context_snapshot
    C->>C: build / transition hypothesis_state
    C->>J: case_input
    J->>J: run observed_state / expected_state / contradiction
    J->>A: arbiter_request
    A-->>J: arbiter_response
    J-->>P: briefs / summary artifacts
```

## What Is Proven

- GC-backed context can enter the Controller through an explicit contract
- the Controller can emit `case_input`
- Jigsaw can compose that input into `kernel_bundle_result`
- Arbiter can judge the resulting bounded case
- execution profiles can run that same spine repeatedly
- deterministic and localmix kernel modes can now reach the same spread on the tested lane

## What Is Not Yet First-Class

- longitudinal case lifecycle management
- action outcome recording
- confidence trajectory over time
- human-assisted revision loop
- Autoresearcher
- companion UI

## Honest Position

The current stack is not just “Jigsaw between GC and Arbiter” anymore.

It is more precisely:

**GC substrate -> Controller state -> Jigsaw composition/runtime -> Arbiter judgment -> product artifact**

That is the current public architecture and the forward-pass demo is the strongest public proof of it.
