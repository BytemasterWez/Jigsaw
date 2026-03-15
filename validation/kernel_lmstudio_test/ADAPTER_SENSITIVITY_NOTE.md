# Adapter Sensitivity Note

## Purpose

This note isolates why the LM-backed `observed_state` path returns a different Arbiter outcome than the deterministic Phase 1B baseline on the same case.

## Compared paths

### Deterministic baseline

- `observed_state.confidence` = `0.74`
- bundle confidence = `0.74`
- Arbiter request `fit_score` = `0.54`
- Arbiter result = `watchlist`

### LM-backed observed_state path

- `observed_state.confidence` = `0.4`
- bundle confidence = `0.4`
- Arbiter request `fit_score` = `0.4`
- Arbiter result = `rejected`

## What stayed the same

- same input case
- same `expected_state`
- same `contradiction`
- same bundle judgment: `contradictory`
- same composed summary
- same evidence count
- same freshness
- same Arbiter adapter logic

## What changed materially

The only meaningful shift is confidence:

- deterministic observed-state confidence was higher
- Jigsaw bundle metadata uses the minimum kernel confidence
- the LM-backed observed-state confidence became the minimum confidence in the bundle
- the Arbiter adapter maps that bundle confidence into Arbiter `fit_score`

That means the Arbiter outcome change is primarily a confidence-compression effect, not a summary-text effect.

## Interpretation

The current local-model path is now contract-valid and stable, but its lower confidence output is harshly amplified by the current bundle-to-Arbiter compression rule.

This does **not** mean the adapter is wrong. It means the current public Arbiter membrane is narrow enough that confidence becomes highly influential once the richer Jigsaw bundle is flattened.

## Practical takeaway

Before changing models, the framework now has a precise answer:

- local LM insertion works
- the output is stable
- the remaining quality gap is materially tied to confidence and its downstream compression into Arbiter `fit_score`

This makes a second-model comparison worthwhile, because it will test whether this confidence gap is model-specific or a broader small-local-model limitation for this slot.
