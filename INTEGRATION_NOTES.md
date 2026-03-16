# Integration Notes

## Purpose

This document records the current minimum real integration points between Jigsaw, Garbage Collector, and Arbiter.

It reflects the **current governed forward pass**, not the older shared-envelope architecture.

## Current Runtime Spine

The current runtime chain is:

`gc_context_snapshot -> hypothesis_state -> case_input -> kernel_bundle_result -> arbiter_request -> arbiter_response`

This is the current integration spine because it keeps:

- substrate context
- exploration state
- packaging intent
- bounded analysis
- final judgment

as separate inspectable boundaries.

## Garbage Collector -> Controller

### Real handoff object

- `gc_context_snapshot/v1`

### Current contents

- `snapshot_id`
- `primary_item_id`
- `related_item_ids`
- `surface_summary`
- `source_types`
- `freshness`
- `known_gaps`
- optional `conflicting_item_ids`
- optional `question_or_claim`

### Current role

GC supplies grounded substrate context.

The Controller then turns that context into `hypothesis_state/v1`.

## Controller -> Jigsaw

### Real handoff object

- `case_input/v1`

### Current contents

- `case_id`
- `hypothesis_id`
- `question_or_claim`
- `primary_evidence_ids`
- `supporting_evidence_ids`
- `conflicting_evidence_ids`
- `missing_evidence`
- `current_confidence`
- `reason_for_packaging`

### Current role

The Controller emits `case_input` only when the branch is ready to package into bounded analysis.

## Jigsaw -> Arbiter

### Real handoff sequence

- Jigsaw composes `kernel_bundle_result`
- a thin adapter maps that result into `arbiter_request`
- Arbiter returns `arbiter_response`

### Current kernel trio

- `observed_state`
- `expected_state`
- `contradiction`

Supported runtime modes in the current proven lane:

- `deterministic`
- `lmstudio`

## Execution Profiles

The current integration story is no longer just a one-off lane.

It now also includes standardized execution profiles that hold fixed:

- case selection
- case shaping
- controller thresholds
- kernel engine selection
- output behavior

Current important profiles:

- `remote_workflow_v1b`
- `remote_workflow_localmix_v1`

## `kernel.v1` Position

`kernel.v1` still exists as a compatibility and shared-result surface.

It is **not** the center of the current public forward-pass story.

The current strongest public story is the controller-driven case spine described above.

So the right current framing is:

- `kernel.v1` remains useful as an interoperability surface
- but the current repo is best understood through:
  - `gc_context_snapshot`
  - `hypothesis_state`
  - `case_input`
  - `kernel_bundle_result`
  - `arbiter_request`
  - `arbiter_response`

## Current References

- [README.md](./README.md)
- [ARCHITECTURE_OVERVIEW.md](./ARCHITECTURE_OVERVIEW.md)
- [docs/RESEARCH_CONTROLLER_ROLE.md](./docs/RESEARCH_CONTROLLER_ROLE.md)
- [contracts/gc_context_snapshot/v1.json](./contracts/gc_context_snapshot/v1.json)
- [contracts/hypothesis_state/v1.json](./contracts/hypothesis_state/v1.json)
- [contracts/case_input/v1.json](./contracts/case_input/v1.json)
