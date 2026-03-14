# Three-Layer Architecture Diagram

```mermaid
flowchart LR
    GC["Garbage Collector<br/>material · normalization · substrate"]
    JI["Jigsaw<br/>middle capability layer"]
    AR["Arbiter<br/>final judgment membrane"]

    GC --> JL1
    JL1 --> JL2
    JL2 --> KA
    KA --> AR

    subgraph JI ["Jigsaw"]
        JL1["Artifact lane<br/>artifact -> extraction -> chunk -> judgment_request"]
        JL2["Kernel lane<br/>kernel_input -> observed_state -> expected_state -> contradiction -> kernel_bundle_result"]
    end

    KA["Thin adapter<br/>kernel_bundle_result -> arbiter_request"]
    AR --> RESP["arbiter_response"]
```

## Reading the diagram

- Garbage Collector prepares usable material and normalization boundaries.
- Jigsaw owns the middle lanes that shape artifacts and compose kernel-family outputs.
- The current Jigsaw to Arbiter connection is intentionally thin.
- Arbiter consumes the adapted case through its existing public membrane and returns a bounded judgment.

## Current pressure point

Jigsaw's kernel bundle surface is richer than Arbiter's current request membrane.

In the current proof this richer structure is compressed into narrower Arbiter fields such as `fit_score`. That is the main interface pressure signal exposed by the current milestone.
