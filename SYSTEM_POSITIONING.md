# System Positioning

## Purpose

Jigsaw is the middle capability repo in a governed intelligence architecture.

Its current public role is to sit between:

- Garbage Collector as substrate intelligence
- Arbiter as final judgment membrane

and provide the explicit forward-pass spine that makes the system inspectable.

## What Jigsaw Is

Jigsaw currently includes:

- Controller-side exploration state handling
- case packaging into `case_input`
- bounded kernel execution
- case composition into `kernel_bundle_result`
- profile-driven runtime behavior
- readable product artifact generation

In practice, Jigsaw is now the engine center of the current stack.

## What Jigsaw Is Not

Jigsaw is not:

- the long-term memory substrate
- the final judgment engine
- the longitudinal case manager over time
- the action executor
- a merged orchestration monolith

## Boundary Rule

Jigsaw interoperates through explicit contracts and bounded handoffs:

- `gc_context_snapshot`
- `hypothesis_state`
- `case_input`
- `kernel_bundle_result`
- `arbiter_request`
- `arbiter_response`

The point is not to hide intelligence in one giant loop. The point is to keep each decision boundary visible.

## Current Strongest Public Slice

The strongest public slice of the repo is now the governed forward pass:

- GC-backed context grounding
- Controller state
- Jigsaw composition
- Arbiter judgment
- readable briefs and reports

That slice is exposed directly in [docs/demo/README.md](./docs/demo/README.md).
