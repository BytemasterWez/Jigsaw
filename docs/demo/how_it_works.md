# How It Works

## Layers

### Garbage Collector

Grounds incoming material in a provenance-bearing substrate and surfaces related context.

### Controller

Tracks bounded investigation state through `hypothesis_state` and decides the next bounded move.

### Jigsaw

Consumes `case_input`, runs bounded kernels, and composes evidence into a structured case result.

### Arbiter

Receives the bounded case through a narrow membrane and decides whether the case is promoted, watchlisted, or rejected.

## Why the layers are separate

Each layer has:

- a distinct object boundary
- a distinct decision boundary
- a distinct failure boundary

That makes the system easier to inspect, debug, and govern.
