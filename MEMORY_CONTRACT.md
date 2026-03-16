# Legacy Memory Contract

## Status

This document describes a historical `MemoryAdapter` framing.

It is preserved for lineage only.

It does **not** describe the current primary GC -> Controller boundary.

## Current Boundary

The current upstream handoff into the governed forward pass is:

- `gc_context_snapshot/v1`

That object now carries grounded GC context into the Controller and includes:

- `snapshot_id`
- `primary_item_id`
- `related_item_ids`
- `surface_summary`
- `source_types`
- `freshness`
- `known_gaps`
- optional `conflicting_item_ids`
- optional `question_or_claim`

## Current Position

Garbage Collector still functions as the substrate intelligence layer, but the current public story is no longer:

- "Jigsaw asks a MemoryAdapter for similar prior cases"

It is now:

- GC surfaces grounded context
- the Controller builds `hypothesis_state`
- the Controller emits `case_input`
- Jigsaw composes the bounded case

## What Is Not Yet First-Class

Longitudinal memory and persistence over time are still incomplete.

The system does **not** yet have a first-class public contract for:

- `case_state/v1`
- `action_record/v1`
- `outcome_event/v1`

So this repo is currently strongest on the governed forward pass, not the full return loop over time.

## Current References

- [contracts/gc_context_snapshot/v1.json](./contracts/gc_context_snapshot/v1.json)
- [docs/RESEARCH_CONTROLLER_ROLE.md](./docs/RESEARCH_CONTROLLER_ROLE.md)
- [README.md](./README.md)
