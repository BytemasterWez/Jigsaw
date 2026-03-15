# Execution Profile Comparison

Baseline profile: `remote_workflow_localmix_v1`
Experiment profile: `remote_workflow_localmix_calibrated_v1`

## Batch totals

| Metric | Baseline | Experiment |
| --- | --- | --- |
| Promoted | `0` | `0` |
| Watchlist | `5` | `5` |
| Rejected | `0` | `0` |
| Avg bundle confidence | `0.68` | `0.53` |
| Avg Arbiter fit score | `0.63` | `0.55` |
| Total LM retries used | `0` | `0` |

## Case-by-case comparison

| Case | Baseline outcome | Experiment outcome | Baseline confidence | Experiment confidence | Baseline fit score | Experiment fit score | LM retries | Runtime stability |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `gc:item:8` | `watchlist` | `watchlist` | `0.7` | `0.6` | `0.65` | `0.55` | `0` | `clean` |
| `gc:item:9` | `watchlist` | `watchlist` | `0.7` | `0.6` | `0.65` | `0.55` | `0` | `clean` |
| `gc:item:14` | `watchlist` | `watchlist` | `0.7` | `0.25` | `0.65` | `0.55` | `0` | `clean` |
| `gc:item:18` | `watchlist` | `watchlist` | `0.7` | `0.6` | `0.65` | `0.55` | `0` | `clean` |
| `gc:item:45` | `watchlist` | `watchlist` | `0.6` | `0.6` | `0.55` | `0.55` | `0` | `clean` |

## Case class flips

- No case class flips in this run.

## What this suggests

The same controller-driven lane was run under `remote_workflow_localmix_v1` and `remote_workflow_localmix_calibrated_v1`. This comparison isolates kernel engine selection while keeping selection rules, controller logic, shaping, and Arbiter mapping fixed.
