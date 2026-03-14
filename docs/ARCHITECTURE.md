# Jigsaw Architecture

## Position in the wider system

Jigsaw sits between upstream normalization and downstream judgment.

```text
Raw input
  -> Garbage Collector ingestion / normalization
  -> Jigsaw artifact contract
  -> Jigsaw extraction contract
  -> Jigsaw chunk contract
  -> Jigsaw judgment_request contract
  -> Arbiter judgment
  -> judgment_response
```

## Architectural role

Jigsaw is the middle capability layer.

It provides:

- contract stability
- transform discipline
- shaping and composition
- provenance-preserving interoperability

It should remain narrow enough to stay reliable, but substantial enough to justify itself as more than passive schema storage.

## Core design rule

Adapters may change more often than contracts.

This means:

- source-specific mapping logic belongs in adapters
- core transforms should remain reusable and stable
- downstream consumers should receive standardized requests without bespoke reshaping in the middle

## Current proof lane

The current proof lane is:

`artifact -> extraction -> chunk -> judgment_request`

This lane is designed to validate that Jigsaw can standardize normalized material into a stable downstream request.

## Reserved capability lane

Jigsaw also reserves space for kernel-family primitives, including future `kernel.v1`-style judgment or middle-layer capability contracts.

These are part of the broader architecture, but are intentionally not mixed into the first artifact-lane proof.

## Success condition

Jigsaw succeeds when:

- upstream normalized material can enter through stable contracts
- provenance survives each transform
- source-specific mess stays in adapters
- downstream systems can consume Jigsaw outputs without ad hoc middle-layer mutation
- new lanes can be added without collapsing repo boundaries

