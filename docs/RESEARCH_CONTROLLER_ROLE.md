# Research Controller Role

## Purpose

The Research Controller is a small state-management layer that sits above Garbage Collector substrate context and beside Jigsaw case composition.

Its first job is not to perform deep research. Its first job is to keep track of what is currently being investigated, what evidence exists, what is missing, and whether a branch should continue, pause, or escalate.

## Boundary

The Research Controller is responsible for:

- tracking first-class `hypothesis_state` objects
- choosing the next bounded probe for a hypothesis
- deciding whether a hypothesis should remain open, gather more evidence, become conflicted, or be considered sufficient

The Research Controller is not responsible for:

- acting as the long-term memory substrate
- assembling Jigsaw evidence bundles itself
- performing final Arbiter judgment
- acting as a freeform autonomous agent

## Current scaffold

The current scaffold is intentionally small.

It introduces:

- `hypothesis_state/v1`
- one GC-backed context input path
- one controller module that can create and refresh a `hypothesis_state`

The scaffold only supports basic transitions:

- `gathering_evidence`
- `sufficient`
- `conflicted`

No Autoresearcher or deeper probe orchestration is included yet.

## Current GC-backed input contract

The controller now accepts `gc_context_snapshot/v1` as the GC -> Controller handoff object.

The snapshot contains:

- `snapshot_id`
- `primary_item_id`
- `related_item_ids`
- `surface_summary`
- `source_types`
- `freshness`
- `known_gaps`
- optional `conflicting_item_ids`
- optional `question_or_claim`

This keeps the upstream boundary explicit before the controller turns context into `hypothesis_state/v1`.

## Working principle

Garbage Collector supplies grounded context.
The Research Controller turns that context into tracked exploration state.
Jigsaw later packages promising branches into bounded analytical cases.
Arbiter later decides what is sufficient and what may happen next.
