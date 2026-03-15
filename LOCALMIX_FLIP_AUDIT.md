# Localmix Flip Audit

## Scope

This note audits the two cases that changed class when the same controller-driven lane was run under:

- `remote_workflow_v1b`
- `remote_workflow_localmix_v1`

Flipped cases:

- `gc:item:8`
- `gc:item:45`

## High-level result

`remote_workflow_localmix_v1` is operationally stable, but it is materially more conservative than the deterministic baseline.

The flips are not caused by runtime instability:

- no retries were used
- no kernel failures occurred
- contradiction stayed unchanged

The flips are caused by both LM-backed upstream kernels downgrading strong cases from:

- `observed_state_clear` -> `observed_state_partial`
- `expected_state_aligned` -> `expected_state_partial`

The larger confidence drop is in `observed_state`.

## Case: `gc:item:8`

### Deterministic baseline

- `observed_state`: `observed_state_clear`, confidence `0.85`
- `expected_state`: `expected_state_aligned`, confidence `0.8125`
- `contradiction`: `contradiction_not_detected`, confidence `0.72`
- bundle judgment: `aligned`
- bundle confidence: `0.72`
- Arbiter `fit_score`: `0.8`
- final result: `promoted`

### Localmix

- `observed_state`: `observed_state_partial`, confidence `0.7`
- `expected_state`: `expected_state_partial`, confidence `0.75`
- `contradiction`: `contradiction_not_detected`, confidence `0.72`
- bundle judgment: `partially_aligned`
- bundle confidence: `0.7`
- Arbiter `fit_score`: `0.65`
- final result: `watchlist`

### Read

- semantic judgment changed in both LM-backed slots, not just confidence
- the sharper drop is `observed_state` (`0.85 -> 0.7`)
- the LM path interprets one false observed item (`offer_pricing_defined`) as enough to downgrade the whole observed picture from `clear` to `partial`

## Case: `gc:item:45`

### Deterministic baseline

- `observed_state`: `observed_state_clear`, confidence `0.85`
- `expected_state`: `expected_state_aligned`, confidence `0.8125`
- `contradiction`: `contradiction_not_detected`, confidence `0.72`
- bundle judgment: `aligned`
- bundle confidence: `0.72`
- Arbiter `fit_score`: `0.8`
- final result: `promoted`

### Localmix

- `observed_state`: `observed_state_partial`, confidence `0.6`
- `expected_state`: `expected_state_partial`, confidence `0.75`
- `contradiction`: `contradiction_not_detected`, confidence `0.72`
- bundle judgment: `partially_aligned`
- bundle confidence: `0.6`
- Arbiter `fit_score`: `0.55`
- final result: `watchlist`

### Read

- semantic judgment changed in both LM-backed slots, not just confidence
- the strongest drop is again `observed_state` (`0.85 -> 0.6`)
- `expected_state` also shifts from `aligned` to `partial`, but the dominant compression into Arbiter comes from the weaker observed-side score

## Pattern across both flips

- contradiction is stable and not the cause
- both LM-backed kernels are more conservative than the deterministic baseline
- `observed_state` is the main pressure point
- localmix is under-scoring strong cases that the deterministic profile currently treats as promotion-grade

## Conclusion

The localmix path is not unstable or incoherent. It is stable, but it is systematically cautious.

The current issue looks like under-confidence plus harsher semantic downgrading in the LM-backed upstream kernels, especially `observed_state`. That compression flows into:

- `partially_aligned` bundle judgments
- lower bundle confidence
- lower Arbiter `fit_score`
- `promoted -> watchlist` flips on strong cases

## Best next move

Do one bounded calibration pass, not a redesign:

- create `remote_workflow_localmix_calibrated_v1`
- keep the same lane, controller, shaping, and Arbiter mapping
- only tighten confidence/judgment behavior for LM-backed:
  - `observed_state`
  - `expected_state`

Use `remote_workflow_v1b` as the current default profile until localmix earns parity on the same 5-case batch.
