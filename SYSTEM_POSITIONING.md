# System Positioning

## Purpose

Jigsaw is the middle capability repo in a governed intelligence architecture.

Its current public role is to sit between:

- Garbage Collector as substrate intelligence
- Arbiter as final judgment membrane

and provide the explicit forward-pass spine plus early lifecycle surface that make the system inspectable over time.

## What Jigsaw Is

Jigsaw currently includes:

- Controller-side exploration state handling
- case packaging into `case_input`
- bounded kernel execution
- case composition into `kernel_bundle_result`
- profile-driven runtime behavior
- readable product artifact generation
- lifecycle objects and revision rules
- reopen review artifacts and monitoring queue

In practice, Jigsaw is now the engine center of the current stack.

## What Jigsaw Is Not

Jigsaw is not:

- the long-term memory substrate
- the final judgment engine
- the action executor
- a merged orchestration monolith

It now does own an **early governed lifecycle**, but not a fully automated long-horizon case-management process.

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

The strongest public slice of the repo is now the governed forward pass plus early governed lifecycle:

- GC-backed context grounding
- Controller state
- Jigsaw composition
- Arbiter judgment
- readable briefs and reports
- reopen review packets
- case monitoring queue

That slice is exposed directly in [docs/demo/README.md](./docs/demo/README.md).
