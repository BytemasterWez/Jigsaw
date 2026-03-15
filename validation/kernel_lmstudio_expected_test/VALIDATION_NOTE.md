# Validation Note

## Purpose

This note records the bounded LM Studio pressure test for the `expected_state` slot in Jigsaw Phase 1B.

The test replaces `expected_state` only with an LM Studio-backed local model while preserving:

- the existing `kernel_input/v1` contract
- the existing `kernel_output/v1` validator
- the existing deterministic `observed_state` kernel
- the existing deterministic `contradiction` kernel
- the existing bundle composition logic
- the existing thin Arbiter handoff

Generation-side compromise:

- LM Studio generates against a simplified expected-state schema only
- Jigsaw normalizes that payload into the full internal `kernel_output/v1` shape locally
- the real validator remains unchanged and still decides whether the output is trusted

## Flow exercised

`kernel_input -> deterministic observed_state -> LM-backed expected_state -> deterministic contradiction -> kernel_bundle_result -> Arbiter`

## What this test is checking

- whether LM Studio returns schema-valid JSON
- whether the returned payload passes the existing kernel validator
- whether one retry at most is sufficient
- whether the composed bundle remains usable and interpretable
- whether the existing Arbiter handoff still returns a sensible bounded judgment

## Baseline for comparison

Known-good deterministic baseline:

- `observed_state` -> `observed_state_partial`
- `expected_state` -> `expected_state_partial`
- `contradiction` -> `contradiction_detected`
- bundle -> `contradictory`
- Arbiter -> `watchlist`

## Latest local result

Latest run in this workspace passed cleanly on the first attempt.

Observed behavior:

- LM Studio was reachable at the local endpoint
- the simplified generation schema produced valid JSON on the first attempt
- local normalization successfully mapped that payload into the full internal `kernel_output/v1` shape
- the real validator passed
- the full bundle composed successfully
- the Arbiter handoff completed successfully

Recorded outputs from the latest run:

- `expected_state` -> `expected_state_partial`
- `expected_state.confidence` -> `0.75`
- bundle -> `contradictory`
- Arbiter -> `watchlist`

Current interpretation:

- the compatibility shim worked
- the strict Jigsaw contract still held
- the lane remained runnable
- this local-model slot achieved downstream parity with the deterministic baseline on the tested case without changing the real contract, validator, composition rule, or Arbiter adapter
