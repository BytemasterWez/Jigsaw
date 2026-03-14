# Jigsaw Role

## Purpose

Jigsaw is the middle capability layer of the wider system architecture.

Its job is to provide stable contracts, disciplined transforms, composition logic, and interoperability between upstream normalized material and downstream judgment engines.

Jigsaw exists to make different system parts work together without forcing each component to absorb the others' responsibilities.

## Jigsaw is responsible for

- defining and versioning core contracts
- validating normalized payloads
- shaping and composing payloads into downstream-operable forms
- preserving provenance, lineage, and transform identity
- exposing reusable interfaces for downstream engines
- hosting middle-layer primitives and kernel-family capabilities where appropriate

## Jigsaw is not responsible for

- raw arbitrary-file ingestion as a primary concern
- being the long-term memory substrate
- acting as the operator-facing product UI
- replacing judgment engines such as Arbiter
- becoming a general-purpose logic bucket for anything useful

## Boundary with Garbage Collector

Garbage Collector is responsible for accepting arbitrary material and normalizing it into structured handoff objects.

Jigsaw receives normalized material and applies disciplined contracts, transforms, shaping, and composition.

GC handles messy entry.  
Jigsaw handles standardized middle-layer capability.

## Boundary with Arbiter

Arbiter consumes structured requests and produces judgments, rankings, or consequence-oriented outputs.

Jigsaw prepares and standardizes the payloads Arbiter receives, but does not itself become the full judgment product.

## Working principle

Adapters may vary.  
Core contracts should vary slowly.

Source-specific irregularities belong in adapters.  
Stable shaping and composition belong in Jigsaw.  
Final judgment belongs downstream.

## Current phase

The current Jigsaw phase focuses on a strict interoperability lane for normalized artifacts:

`artifact -> extraction -> chunk -> judgment_request`

This phase is a bounded proof of disciplined interoperability inside Jigsaw's broader middle-layer role.

It does not redefine Jigsaw as only a schema repository.

## Future expansion

Jigsaw is expected to support both:

1. normalized artifact-processing contracts
2. kernel-family judgment primitives and related middle-layer capabilities

These must coexist without being blurred together.

