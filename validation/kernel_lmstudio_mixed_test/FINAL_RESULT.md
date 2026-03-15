# Final Result: LM Studio Mixed Bundle

## Bounded claim

A small local language model can support both the `observed_state` and `expected_state` slots inside the Jigsaw Phase 1B kernel lane, with deterministic `contradiction` preserved, while keeping the real contracts, validators, composition rules, and Arbiter handoff intact.

## What was held fixed

- `kernel_input/v1`
- `kernel_output/v1`
- `kernel_bundle_result/v1`
- local validators
- deterministic `contradiction`
- bundle composition
- Jigsaw to Arbiter adapter
- current public Arbiter membrane

## What changed

- `observed_state` was produced through the bounded LM Studio path
- `expected_state` was produced through the bounded LM Studio path
- both used simplified generation schemas only for transport compatibility
- both were normalized locally into the full internal contract before validation

## What was proven

- two upstream kernel slots can be LM-backed at once without breaking Jigsaw discipline
- both outputs can pass the unchanged local validator
- the composed bundle remains runnable and interpretable
- the current Arbiter membrane remains usable after the mixed bundle
- downstream `watchlist` parity was preserved on the tested case

## What is not proven

- universal parity across all cases
- universal parity across all kernel bundles
- that `contradiction` should also be LM-backed
- that the current Arbiter membrane is sufficient for all richer Jigsaw cases
- that local small models are generally equal to deterministic or frontier-model paths

## Honest conclusion

This is a stronger bounded systems proof than the earlier single-slot runs.

It shows that Jigsaw can sustain a mixed local bundle before the known Arbiter compression point, and that the current membrane is still usable at this level of local-model insertion.
