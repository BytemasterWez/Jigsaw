# Validation Target

## Current milestone

Validate one strict interoperability lane inside Jigsaw's broader middle-layer architecture.

The target lane is:

`artifact -> extraction -> chunk -> judgment_request`

## Objective

Demonstrate that Jigsaw can accept a normalized upstream artifact, validate it, transform it through stable contracts, and emit a downstream-operable judgment request while preserving provenance and linkage.

## Why this milestone matters

This milestone proves that Jigsaw is a real interoperability and shaping layer, not just a loose conceptual architecture.

It also proves that:

- adapters can absorb source-specific irregularities
- core middle-layer contracts can remain stable
- downstream judgment systems can consume standardized requests

## Input scope

For the first validation slice, input should be limited to a normalized text-bearing artifact already prepared by Garbage Collector or an equivalent upstream normalizer.

Recommended examples:

- note
- document text
- transcript text
- extracted PDF text

Avoid multimodal complexity for this milestone.

## Contracts exercised

The first slice should exercise:

- `artifact/v1`
- `extraction/v1`
- `chunk/v1`
- `judgment_request/v1`

`judgment_response/v1` should be defined in the repo but should not slow this proof.

## Required proof outputs

The validation run should produce:

- validated artifact payload
- extraction payload
- chunk payload(s)
- judgment_request payload
- run log
- validation note summarizing what held stable and what required adapter logic

## Pass condition

This milestone passes when:

- a normalized artifact enters through `artifact/v1`
- all transforms complete successfully
- provenance and linkage survive the full lane
- the outgoing `judgment_request/v1` is consumable by downstream judgment logic
- no source-specific irregularities leak into core transforms

## Non-goals

This milestone is not intended to prove:

- full multimodal ingestion
- long-term memory orchestration
- UI or product readiness
- generalized agent behavior
- complete kernel-family capability coverage

It is a bounded interoperability proof.

