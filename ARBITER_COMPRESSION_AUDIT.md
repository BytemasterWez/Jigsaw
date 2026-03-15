# Arbiter Compression Audit

## Purpose

This note audits the current public Arbiter membrane against the richer Jigsaw kernel-bundle surface.

It does **not** propose a redesign. Its purpose is to show:

- what Arbiter currently consumes
- what Jigsaw currently knows that Arbiter cannot fully see
- what gets flattened in the adapter
- what appears to drive final decisions most strongly
- whether the current public membrane is still acceptable

## Scope

This audit is grounded in the current public Arbiter contracts and the executed Jigsaw integration proofs:

- Arbiter request: [arbiter_request.schema.json](/E:/codex%20projects/arbiter-public/schemas/arbiter_request.schema.json)
- Arbiter response: [arbiter_response.schema.json](/E:/codex%20projects/arbiter-public/schemas/arbiter_response.schema.json)
- Arbiter demo adjudication: [run.py](/E:/codex%20projects/arbiter-public/demo/run.py)
- Jigsaw adapter: [arbiter_integration.py](/E:/codex%20projects/Jigsaw/jigsaw/lanes/kernel_lane/arbiter_integration.py)
- Jigsaw integration note: [INTEGRATION_NOTE.md](/E:/codex%20projects/Jigsaw/validation/kernel_to_arbiter/INTEGRATION_NOTE.md)
- Jigsaw adapter sensitivity note: [ADAPTER_SENSITIVITY_NOTE.md](/E:/codex%20projects/Jigsaw/validation/kernel_lmstudio_test/ADAPTER_SENSITIVITY_NOTE.md)

## 1. What Arbiter currently consumes

The current public Arbiter request surface is intentionally narrow.

Required top-level fields:

- `candidate_id`
- `domain`
- `candidate_type`
- `summary`
- `evidence`
- `context`

Required evidence fields:

- `source_count`
- `freshness_days`
- `fit_score`

Optional evidence field currently used by Jigsaw:

- `estimated_value_band`

In practice, the Arbiter demo adjudicator makes decisions primarily from:

- `evidence.fit_score`
- `evidence.freshness_days`
- `evidence.source_count`

Current threshold behavior in [run.py](/E:/codex%20projects/arbiter-public/demo/run.py):

- `promoted` if `fit_score >= 0.75` and `freshness_days <= 7` and `source_count >= 2`
- `watchlist` if `fit_score >= 0.5`
- `rejected` otherwise

This means the current membrane is a small, threshold-driven judgment surface, not a rich multi-kernel case surface.

## 2. What Jigsaw now knows that Arbiter cannot really see

Jigsaw kernel bundles contain materially more structure than Arbiter can directly consume.

Example source bundle: [kernel_bundle_result.json](/E:/codex%20projects/Jigsaw/validation/kernel_first_bundle/output/kernel_bundle_result.json)

The bundle preserves:

- separate kernel outputs for:
  - `observed_state`
  - `expected_state`
  - `contradiction`
- per-kernel:
  - `judgment`
  - `confidence`
  - `reasons`
  - `evidence_used`
  - metadata and lineage
- bundle-level:
  - `bundle_judgment`
  - `composition_notes`
  - bundle metadata confidence
  - lineage across the whole bundle

What Arbiter cannot directly see in first-class fields:

- separate observed-state vs expected-state surfaces
- explicit contradiction as its own judgment primitive
- per-kernel reasons
- per-kernel evidence attribution
- bundle composition notes
- lineage depth
- confidence distribution across kernels

Arbiter receives only a compressed summary of that richer case.

## 3. What gets flattened in the adapter

The Jigsaw adapter is thin, but it is undeniably lossy.

Current adapter behavior in [arbiter_integration.py](/E:/codex%20projects/Jigsaw/jigsaw/lanes/kernel_lane/arbiter_integration.py):

- `subject_id` -> `candidate_id`
- `subject_type` -> `candidate_type`
- `composed_summary.summary` -> `summary`
- `len(kernel_input.evidence)` -> `evidence.source_count`
- freshness derived from timestamps -> `evidence.freshness_days`
- bundle judgment copied to `evidence.estimated_value_band`
- bundle judgment also copied to `context.jigsaw_bundle_judgment`
- kernel sequence copied to `context.kernel_sequence`

The main flattening happens here:

- the richer bundle is projected to **one** Arbiter `fit_score`

Current fit-score projection:

- `aligned` -> confidence floor around `0.8`
- `partially_aligned` -> confidence floor around `0.55`
- `contradictory` -> `max(bundle_confidence - 0.2, 0.4)`
- `insufficient` -> capped near `0.3`

This is the thinnest acceptable mapping for proof, but it compresses:

- contradiction severity
- confidence spread across kernels
- the difference between "usable but unstable" and "weak overall"
- whether a contradiction is narrow or systemic

Example deterministic integration request: [arbiter_request.json](/E:/codex%20projects/Jigsaw/validation/kernel_to_arbiter/output/arbiter_request.json)

Example deterministic integration response: [arbiter_response.json](/E:/codex%20projects/Jigsaw/validation/kernel_to_arbiter/output/arbiter_response.json)

## 4. What appears to drive the final decision most

For the current public membrane, final outcome appears to be driven overwhelmingly by `fit_score`.

Why:

- in the current proof cases, `freshness_days` stayed `0`
- `source_count` stayed `3`
- `summary` stayed effectively the same
- the bundle judgment stayed `contradictory`
- the key variable that changed outcome was compressed confidence -> `fit_score`

Observed decision behavior across executed proofs:

### Deterministic kernel bundle baseline

- bundle confidence = `0.74`
- contradiction penalty for `contradictory` bundle = `0.2`
- Arbiter `fit_score` = `0.54`
- Arbiter result = `watchlist`

Files:

- [kernel_bundle_result.json](/E:/codex%20projects/Jigsaw/validation/kernel_first_bundle/output/kernel_bundle_result.json)
- [arbiter_request.json](/E:/codex%20projects/Jigsaw/validation/kernel_to_arbiter/output/arbiter_request.json)
- [arbiter_response.json](/E:/codex%20projects/Jigsaw/validation/kernel_to_arbiter/output/arbiter_response.json)

### Early LM-backed observed-state path

- observed-state confidence dropped to `0.4`
- Jigsaw bundle confidence uses the minimum kernel confidence
- Arbiter `fit_score` compressed to `0.4`
- Arbiter result = `rejected`

Files:

- [ADAPTER_SENSITIVITY_NOTE.md](/E:/codex%20projects/Jigsaw/validation/kernel_lmstudio_test/ADAPTER_SENSITIVITY_NOTE.md)

### Calibrated LM-backed observed-state path

- observed-state confidence rose to `0.7`
- Arbiter `fit_score` rose to `0.5`
- Arbiter result returned to `watchlist`

Files:

- [validation/kernel_lmstudio_test/output/arbiter_request.json](/E:/codex%20projects/Jigsaw/validation/kernel_lmstudio_test/output/arbiter_request.json)
- [validation/kernel_lmstudio_test/output/arbiter_response.json](/E:/codex%20projects/Jigsaw/validation/kernel_lmstudio_test/output/arbiter_response.json)

### LM-backed expected-state path

- expected-state confidence = `0.75`
- Arbiter result = `watchlist`

Files:

- [validation/kernel_lmstudio_expected_test/output/arbiter_request.json](/E:/codex%20projects/Jigsaw/validation/kernel_lmstudio_expected_test/output/arbiter_request.json)
- [validation/kernel_lmstudio_expected_test/output/arbiter_response.json](/E:/codex%20projects/Jigsaw/validation/kernel_lmstudio_expected_test/output/arbiter_response.json)

## 5. What maps cleanly vs what compresses badly

What maps cleanly:

- identity:
  - `subject_id` -> `candidate_id`
  - `subject_type` -> `candidate_type`
- case summary:
  - Jigsaw composed summary -> Arbiter summary
- basic evidence scaffolding:
  - evidence count
  - freshness

What compresses acceptably but awkwardly:

- bundle judgment -> `estimated_value_band`
- kernel ordering -> `context.kernel_sequence`
- bundle identity -> `context.jigsaw_bundle_id`

What compresses badly:

- multiple kernel judgments -> single `fit_score`
- per-kernel confidence distribution -> one scalar
- contradiction meaning -> penalty folded into fit score
- composition notes -> effectively lost
- reasons/evidence attribution -> effectively lost
- lineage nuance -> not represented in decision logic

## 6. Is the current membrane still good enough?

Yes, for now.

More precisely:

- good enough for bounded integration proof
- good enough for current public demonstration
- good enough for narrow Jigsaw -> Arbiter handoff
- not expressive enough to faithfully carry the richer Jigsaw bundle surface

The current membrane is therefore:

- **acceptable as the present public membrane**
- **narrow enough that confidence compression matters a lot**
- **likely temporary if richer case governance becomes a core product need**

This does not justify an immediate redesign. It does justify being honest about the tradeoff:

- Jigsaw can already hand Arbiter a usable shaped case
- Arbiter can already return bounded judgments
- but the current public membrane remains narrower than Jigsaw's richer bundle semantics

## 7. Current conclusion

The current public Arbiter membrane is still sufficient for this phase, but it is now visibly the main compression point in the framework.

The cleanest evidence-based reading is:

- the adapter is thin enough
- the membrane works
- the main lossy step is the projection of rich bundle state into `fit_score`
- decision flips on the tested cases were driven mainly by that confidence compression, not by summary wording or evidence-count changes

So the current membrane is:

- acceptable for bounded use
- acceptable for current proof work
- not yet a full expression of the richer Jigsaw case surface

That is the pressure signal to keep, not a reason to redesign prematurely.
