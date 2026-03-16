# Arbiter Decision Contract

## Purpose

Jigsaw composes bounded cases. Arbiter decides what may happen next through a narrow public membrane.

## Current Boundary

The current Jigsaw -> Arbiter handoff is:

- `kernel_bundle_result`
- mapped through a thin adapter into:
- `arbiter_request`

Arbiter returns:

- `arbiter_response`

## Current Public Outcomes

The current public Arbiter membrane exposes:

- `promoted`
- `watchlist`
- `rejected`

Those are the outcomes Jigsaw currently treats as authoritative in the governed forward pass.

## Current Request Shape

In the current lane, `arbiter_request` includes:

- `candidate_id`
- `domain`
- `candidate_type`
- `summary`
- `evidence.source_count`
- `evidence.freshness_days`
- `evidence.fit_score`
- optional `evidence.estimated_value_band`
- `context.*` fields for bundle metadata

## Current Response Shape

In the current lane, `arbiter_response` includes:

- `candidate_id`
- `judgement`
- `confidence`
- `reason_summary`
- `key_factors`
- `recommended_action`

## Boundary Rule

Arbiter is responsible for:

- final bounded judgment
- action authorization
- decision confidence
- short decision rationale

Arbiter is not responsible for:

- retrieval
- controller state transitions
- case shaping
- kernel execution

## Honest Note

The current public Arbiter membrane is narrower than Jigsaw's richer internal case surface.

That is acceptable for the current phase, but it means some structure is still compressed into request fields such as `fit_score`.

## Current References

- [validation/execution_profiles/remote_workflow_v1b/case_01_gc_8/arbiter_request.json](./validation/execution_profiles/remote_workflow_v1b/case_01_gc_8/arbiter_request.json)
- [validation/execution_profiles/remote_workflow_v1b/case_01_gc_8/arbiter_response.json](./validation/execution_profiles/remote_workflow_v1b/case_01_gc_8/arbiter_response.json)
- [OPERATIONAL_PROOF.md](./OPERATIONAL_PROOF.md)
