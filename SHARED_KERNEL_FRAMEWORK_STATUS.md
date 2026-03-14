# Shared Kernel Framework Status

## Purpose

This document records the current state of `kernel.v1` across Garbage Collector, Jigsaw, and Arbiter.

The goal is precision:

- what is native now
- what is still mapped
- what remains to be done before the shared kernel framework is fully mature

## Current State

`kernel.v1` is now a machine-readable shared engine-result primitive with:

- a frozen prose contract in Garbage Collector
- mirrored JSON Schema in all three repos
- typed models in Garbage Collector and Jigsaw
- shared validation fixtures in all three repos
- one live reference engine in Garbage Collector
- native ingest support in Jigsaw
- a native Arbiter adapter path from `kernel.v1` into the public Arbiter request contract

The three repos remain separate. Interoperability happens through schemas, adapters, and documented mappings.

## What Is Native

### Garbage Collector

- `kernel.v1` is the contract origin
- Goal Alignment emits `kernel.v1`
- backend validates engine output against JSON Schema before returning it
- contract fixtures and tests guard against drift

### Jigsaw

- `kernel.v1` is accepted as a first-class input schema
- Jigsaw can validate a `kernel.v1` payload directly
- Jigsaw can convert a valid `kernel.v1` result into the native `MessageEnvelope`
- tests prove valid payloads are accepted and converted

### Arbiter

- Arbiter includes a first-class adapter for `kernel.v1`
- the adapter validates the payload, maps it into the public Arbiter request shape, and adjudicates it
- tests prove valid `kernel.v1` payloads can be transformed and judged

## What Is Still Mapped

`kernel.v1` is not the only native runtime contract in the stack.

Remaining mappings:

- Jigsaw still runs its internal kernel chain on `MessageEnvelope`
- Arbiter still exposes its public request and response schemas as the primary external contract
- `kernel.v1` therefore enters Jigsaw through an adapter and reaches Arbiter through an adapter

That is acceptable for this phase. The important point is that the mappings are now explicit, documented, and test-backed.

## What Remains To Be Done

The shared kernel framework is stronger, but it is not complete.

Still open:

- choose a single canonical source location for the JSON Schema rather than mirroring it manually
- decide whether Arbiter should expose an official alternate `kernel.v1` request surface
- decide whether Jigsaw should emit `kernel.v1` directly for some kernel chains, not only ingest it
- add cross-repo fixture synchronization discipline so schema mirrors cannot silently drift
- expand judgment coverage if public Arbiter later adds first-class `escalate`

## Architectural Status

The honest position now is:

- Garbage Collector has the contract origin and a live reference engine
- Jigsaw has native `kernel.v1` ingest support
- Arbiter has native `kernel.v1` adapter support
- the framework is real enough to validate and move data across repos without hand-waving
- the repos still keep distinct runtime contracts and responsibilities

This is Shared Kernel Framework Phase 1, not the final form of the system.
