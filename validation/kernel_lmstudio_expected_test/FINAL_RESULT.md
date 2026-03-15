# Final Result: LM Studio Expected-State Slot

## Bounded claim

A small local language model can operate inside the `expected_state` slot of Jigsaw Phase 1B under strict contract discipline and preserve downstream parity with the deterministic baseline on the tested case.

## What was held fixed

- `kernel_input/v1`
- `kernel_output/v1`
- local validators
- bundle composition
- deterministic `observed_state`
- deterministic `contradiction`
- Jigsaw to Arbiter adapter

## What changed

- LM Studio generation used a simplified expected-state schema for transport compatibility
- generated output was normalized locally into the full `kernel_output/v1` shape

## What was proven

- local model insertion into the `expected_state` slot works
- contract discipline remains intact
- validator discipline remains intact
- the lane remains runnable
- Arbiter handoff remains runnable
- the local path preserved a `watchlist` result matching the deterministic baseline on this case

## What is not proven

- universal parity across all cases
- universal parity across all kernel slots
- parity across all local models
- superiority over the deterministic baseline

## Honest conclusion

This is a bounded systems proof, not a universal model-quality claim.

It shows that a second kernel slot can host small local inference inside Jigsaw without weakening the architecture, and that bounded downstream parity is possible beyond the first `observed_state` slot.
