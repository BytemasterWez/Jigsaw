# Execution Profile Comparison

Baseline profile: `remote_workflow_v1b`
Experiment profile: `remote_workflow_localmix_calibrated_v1`

## Batch totals

| Metric | Baseline | Experiment |
| --- | --- | --- |
| Promoted | `2` | `0` |
| Watchlist | `3` | `5` |
| Rejected | `0` | `0` |
| Avg bundle confidence | `0.687` | `0.53` |
| Avg Arbiter fit score | `0.689` | `0.55` |
| Total LM retries used | `0` | `0` |

## Case-by-case comparison

| Case | Baseline outcome | Experiment outcome | Baseline confidence | Experiment confidence | Baseline fit score | Experiment fit score | LM retries | Runtime stability |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `gc:item:8` | `promoted` | `watchlist` | `0.72` | `0.6` | `0.8` | `0.55` | `0` | `clean` |
| `gc:item:9` | `watchlist` | `watchlist` | `0.6375` | `0.6` | `0.5875` | `0.55` | `0` | `clean` |
| `gc:item:14` | `watchlist` | `watchlist` | `0.6375` | `0.25` | `0.5875` | `0.55` | `0` | `clean` |
| `gc:item:18` | `watchlist` | `watchlist` | `0.72` | `0.6` | `0.67` | `0.55` | `0` | `clean` |
| `gc:item:45` | `promoted` | `watchlist` | `0.72` | `0.6` | `0.8` | `0.55` | `0` | `clean` |

## Case class flips

- gc:item:8: promoted -> watchlist
- gc:item:45: promoted -> watchlist

## What this suggests

The same controller-driven lane was run under `remote_workflow_v1b` and `remote_workflow_localmix_calibrated_v1`. This comparison isolates kernel engine selection while keeping selection rules, controller logic, shaping, and Arbiter mapping fixed.
