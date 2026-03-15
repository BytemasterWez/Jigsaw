# Validation Note: LM Studio Mixed Bundle

## Purpose

This note records the bounded mixed-bundle proof:

- LM-backed `observed_state`
- LM-backed `expected_state`
- deterministic `contradiction`

The goal is to test whether both upstream kernel surfaces can be model-produced at once while preserving:

- `kernel_output/v1` contract discipline
- local validator discipline
- bundle composition
- thin Arbiter handoff

## What is held fixed

- `kernel_input/v1`
- `kernel_output/v1`
- `kernel_bundle_result/v1`
- local validators
- deterministic `contradiction`
- bundle composition rules
- Jigsaw to Arbiter adapter

## Outputs

The mixed test writes:

- `validation/kernel_lmstudio_mixed_test/output/kernel_input.json`
- `validation/kernel_lmstudio_mixed_test/output/observed_state_raw_model_output.json`
- `validation/kernel_lmstudio_mixed_test/output/observed_state_generated.json`
- `validation/kernel_lmstudio_mixed_test/output/observed_state_validated.json`
- `validation/kernel_lmstudio_mixed_test/output/expected_state_raw_model_output.json`
- `validation/kernel_lmstudio_mixed_test/output/expected_state_generated.json`
- `validation/kernel_lmstudio_mixed_test/output/expected_state_validated.json`
- `validation/kernel_lmstudio_mixed_test/output/contradiction.json`
- `validation/kernel_lmstudio_mixed_test/output/kernel_bundle_result.json`
- `validation/kernel_lmstudio_mixed_test/output/arbiter_request.json`
- `validation/kernel_lmstudio_mixed_test/output/arbiter_response.json`
- `validation/kernel_lmstudio_mixed_test/output/run_log.json`

## Result

- model used: `deepseek/deepseek-r1-0528-qwen3-8b`
- schema validity: passed
- observed-state retries used: `0`
- expected-state retries used: `0`
- observed-state result: `observed_state_partial` with confidence `0.7`
- expected-state result: `expected_state_partial` with confidence `0.75`
- deterministic contradiction result: `contradiction_detected`
- bundle result: `contradictory`
- bundle confidence: `0.7`
- Arbiter fit score: `0.5`
- Arbiter result: `watchlist`

## Interpretation

This mixed bundle passed under the same contract discipline as the earlier single-slot proofs:

- both LM-backed kernel outputs normalized into the real `kernel_output/v1`
- both passed the unchanged local validator
- bundle composition stayed unchanged
- the current Arbiter membrane still produced a bounded usable result

The initial mixed-run failure was not a bundle failure. It came from LM Studio model selection:

- the client defaulted to the first model returned by `/models`
- that model was installed but unloaded
- rerunning with `JIGSAW_LMSTUDIO_MODEL=deepseek/deepseek-r1-0528-qwen3-8b` produced a clean success

## Bounded conclusion

Jigsaw can sustain a mixed local bundle in which both `observed_state` and `expected_state` are LM-backed while `contradiction` remains deterministic.

On this tested case:

- contract discipline held
- validator discipline held
- the bundle remained interpretable
- the existing Arbiter membrane remained usable
- downstream `watchlist` parity was preserved
