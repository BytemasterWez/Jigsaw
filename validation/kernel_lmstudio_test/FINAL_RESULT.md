# Final Result: LM Studio Observed-State Slot

## Bounded claim

A small local language model can operate inside the `observed_state` slot of Jigsaw Phase 1B under strict contract discipline and, with narrow confidence calibration, recover downstream parity with the deterministic baseline on the tested case.

## What was held fixed

- `kernel_input/v1`
- `kernel_output/v1`
- local validators
- bundle composition
- deterministic `expected_state`
- deterministic `contradiction`
- Jigsaw to Arbiter adapter

## What changed

- LM Studio generation moved to a simplified schema for transport compatibility
- generated output was normalized locally into the full `kernel_output/v1` shape
- confidence guidance for the LM-backed `observed_state` prompt was tightened

## What was proven

- local model insertion into a Jigsaw kernel slot works
- contract discipline remains intact
- validator discipline remains intact
- the lane remains runnable
- Arbiter handoff remains runnable
- a narrow confidence calibration can recover a `watchlist` result matching the deterministic baseline on this case

## What is not proven

- universal parity across all cases
- universal parity across all kernel slots
- parity across all local models
- superiority over the deterministic baseline

## Honest conclusion

This is a bounded systems proof, not a universal model-quality claim.

It shows that small local inference can live inside the framework without weakening the architecture, and that the remaining quality gap on this case was narrow enough to close through slot-level calibration rather than system redesign.
