# Shared Kernel Framework Status

## Purpose

This document records the current position of `kernel.v1` in relation to the newer controller-driven runtime architecture.

The important clarification is:

`kernel.v1` still exists, but it is no longer the best top-level description of the current forward-pass system.

## Current Position

`kernel.v1` remains useful as:

- a shared engine-result primitive
- an interoperability surface
- a compatibility contract across repos

But the current strongest Jigsaw runtime story is now:

`gc_context_snapshot -> hypothesis_state -> case_input -> kernel_bundle_result -> arbiter_request -> arbiter_response`

That means `kernel.v1` is now a **secondary compatibility surface**, not the center of the current public architecture.

## What Is Still True

- `kernel.v1` remains a real shared contract
- schema and validation work around it still matter
- cross-repo interoperability through explicit contracts still matters

## What Changed

The repo moved from an older public framing centered on:

- one envelope-like internal runtime
- kernel interoperability as the main public story

to a stronger public framing centered on:

- Controller state
- explicit case packaging
- bounded kernel composition
- Arbiter membrane
- readable product artifacts

## Current Best Use Of This Doc

Treat this as a note about interoperability maturity, not as the main description of the current architecture.

For the current public architecture, use:

- [README.md](./README.md)
- [ARCHITECTURE_OVERVIEW.md](./ARCHITECTURE_OVERVIEW.md)
- [ARCHITECTURE_DIAGRAM.md](./ARCHITECTURE_DIAGRAM.md)
- [docs/demo/README.md](./docs/demo/README.md)
