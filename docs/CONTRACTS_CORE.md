# Core Contracts

## Purpose

This document defines the first bounded set of core contracts for Jigsaw Phase 1A.

These contracts support the initial artifact interoperability lane:

`artifact -> extraction -> chunk -> judgment_request`

They are intentionally narrow.

## Design rules

- adapters may vary
- core contracts should vary slowly
- provenance and linkage fields must survive every transform
- source-specific shaping belongs in adapters, not in the contract definitions themselves
- shared metadata should use one stable embedded shape

## Contract set

The first contract pack contains:

1. `contracts/common/metadata.v1.json`
2. `contracts/artifact/v1.json`
3. `contracts/extraction/v1.json`
4. `contracts/chunk/v1.json`
5. `contracts/judgment_request/v1.json`
6. `contracts/judgment_response/v1.json`

## Priority for the first proof

For the first proof lane, the practical priority order is:

1. `artifact/v1`
2. `extraction/v1`
3. `chunk/v1`
4. `judgment_request/v1`

Lower immediate proof priority, but still defined now:

5. `judgment_response/v1`
6. `common/metadata.v1`

## Shared metadata pattern

`metadata.v1` is not the main flow object.

It is a shared embedded object pattern used by the other contracts where provenance, timestamps, lineage, confidence context, or tags need to be standardized.

## `artifact/v1`

Purpose:

- represent a normalized upstream handoff object

Use it when:

- Garbage Collector or another upstream normalizer has already turned messy input into a stable object Jigsaw can accept

## `extraction/v1`

Purpose:

- represent machine-usable extracted content derived from an artifact

Use it when:

- Jigsaw has validated an artifact and needs a stable representation of extracted text, sections, tables, entities, and warnings

## `chunk/v1`

Purpose:

- represent the standard analytical unit for downstream processing

Use it when:

- extracted text needs to be partitioned into stable, traceable units for downstream judgment preparation

## `judgment_request/v1`

Purpose:

- represent the stable downstream request shape sent toward Arbiter or another judgment engine

Use it when:

- Jigsaw has shaped enough normalized material into a machine-operable request and needs to preserve chunk linkage and evidence provenance

## `judgment_response/v1`

Purpose:

- represent a stable downstream decision or judgment response shape

Use it when:

- a downstream judgment engine returns a standardized result that Jigsaw or another consumer must interpret without bespoke glue

## Current non-goals

These contracts do not yet attempt to cover:

- multimodal ingestion complexity
- full memory substrate behavior
- kernel-family runtime composition
- UI or product state
- generalized workflow orchestration

They are the first strict contract lane inside the broader middle-layer architecture.

