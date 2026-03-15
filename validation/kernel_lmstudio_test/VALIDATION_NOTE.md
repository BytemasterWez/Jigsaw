# Validation Note

## Purpose

This note records the bounded LM Studio pressure test for Jigsaw Phase 1B.

The test replaces `observed_state` only with an LM Studio-backed local model while preserving:

- the existing `kernel_input/v1` contract
- the existing `kernel_output/v1` validator
- the existing deterministic `expected_state` kernel
- the existing deterministic `contradiction` kernel
- the existing bundle composition logic
- the existing thin Arbiter handoff

Generation-side compromise:

- LM Studio now generates against a simplified observed-state schema only
- Jigsaw then normalizes that payload into the full internal `kernel_output/v1` shape locally
- the real validator remains unchanged and still decides whether the output is trusted

## Flow exercised

`kernel_input -> LM-backed observed_state -> deterministic expected_state -> deterministic contradiction -> kernel_bundle_result -> Arbiter`

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

## Pass condition

This test passes if:

- LM Studio produces a valid `observed_state` output
- validation succeeds with at most one retry
- the bundle composes successfully
- the result remains semantically interpretable
- Arbiter still returns a sensible bounded judgment

## Fail condition

This test fails if:

- the model repeatedly breaks schema discipline
- validation still fails after one retry
- the output technically validates but damages the bundle surface
- the downstream bundle or Arbiter handoff becomes nonsensical

## Latest local result

Latest calibrated result in this workspace passed the contract boundary and recovered downstream parity on the tested case.

Observed behavior:

- LM Studio was reachable at the local endpoint
- the simplified generation schema produced valid JSON on the first attempt
- local normalization successfully mapped that payload into the full internal `kernel_output/v1` shape
- the real validator passed
- the full bundle composed successfully
- the Arbiter handoff completed successfully

Recorded outputs from the final calibrated run:

- `observed_state` -> `observed_state_partial`
- `observed_state.confidence` -> `0.7`
- bundle -> `contradictory`
- Arbiter -> `watchlist`

Quality improvement:

- the earlier `confidence: 0.0` failure mode was removed by prompt calibration
- the model now returns a stronger confidence that is semantically plausible for `observed_state_partial`
- the downstream Arbiter outcome now matches the deterministic baseline on this tested case

Current interpretation:

- the compatibility shim worked
- the strict Jigsaw contract still held
- the lane remained runnable
- the calibrated local model is now strong enough to act as a bounded observed-state worker under contract discipline on this case
- downstream parity with the deterministic baseline was recovered without changing the real contract, validator, composition rule, or Arbiter adapter
