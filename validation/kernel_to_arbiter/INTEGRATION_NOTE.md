# Integration Note

## Purpose

This note records the first bounded proof that a real Jigsaw `kernel_bundle_result` can pass through a thin adapter into the current public Arbiter membrane.

Flow exercised:

`kernel_bundle_result -> thin adapter -> arbiter_request -> Arbiter adjudication -> arbiter_response`

## Source used

- Jigsaw source lane: `jigsaw.lanes.kernel_lane.execute_first_kernel_bundle`
- source contracts:
  - `kernel_input/v1`
  - `kernel_output/v1`
  - `kernel_bundle_result/v1`
- Arbiter target contracts:
  - `arbiter_request.schema.json`
  - `arbiter_response.schema.json`

## What mapped cleanly

- `subject_id` mapped directly to `candidate_id`
- `subject_type` mapped directly to `candidate_type`
- the composed Jigsaw summary mapped directly to Arbiter `summary`
- evidence count mapped directly from Jigsaw evidence records to Arbiter `source_count`
- freshness could be computed from preserved `observed_at` timestamps
- the adapter stayed outside both core Jigsaw composition logic and Arbiter adjudication logic

## What was compressed

- multiple kernel judgments had to be compressed into one Arbiter `fit_score`
- the Jigsaw bundle judgment had to be carried partly in `estimated_value_band` and partly in extra `context` fields
- Arbiter's current public membrane has no first-class place for separate observed-state, expected-state, and contradiction outputs

## What felt awkward

- the fit-score projection is the thinnest acceptable lossy step in the mapping, but it is still a compression
- contradiction remains visible to Arbiter only indirectly through the compressed fit score and contextual hints
- this means the current Arbiter membrane is usable, but narrower than the richer Jigsaw bundle surface

## Thin-adapter assessment

The adapter stayed acceptably thin for this proof:

- it did not invent a new case outside the Jigsaw output
- it did not re-run middle-layer reasoning
- it did not modify Arbiter's public schema
- it only projected the Jigsaw bundle into the narrower current Arbiter request shape

## Sufficiency assessment

The current public Arbiter membrane is sufficient for a first integration proof.

It is not fully expressive of the richer Jigsaw kernel bundle, but it is workable without forcing a redesign during this phase.

## Output written

The run writes:

- `validation/kernel_to_arbiter/output/kernel_input.json`
- `validation/kernel_to_arbiter/output/kernel_bundle_result.json`
- `validation/kernel_to_arbiter/output/arbiter_request.json`
- `validation/kernel_to_arbiter/output/arbiter_response.json`
- `validation/kernel_to_arbiter/output/run_log.json`
