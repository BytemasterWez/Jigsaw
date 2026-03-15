# Execution Profile Comparison

Baseline profile: `remote_workflow_v1b`
Experiment profile: `remote_workflow_localmix_v1`

## Batch totals

| Metric | Baseline | Experiment |
| --- | --- | --- |
| Promoted | `2` | `2` |
| Watchlist | `3` | `3` |
| Rejected | `0` | `0` |
| Avg bundle confidence | `0.687` | `0.687` |
| Avg Arbiter fit score | `0.689` | `0.689` |
| Total LM retries used | `0` | `0` |

## Case-by-case comparison

| Case | Baseline outcome | Experiment outcome | Baseline confidence | Experiment confidence | Baseline fit score | Experiment fit score | LM retries | Runtime stability |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `gc:item:8` | `promoted` | `promoted` | `0.72` | `0.72` | `0.8` | `0.8` | `0` | `clean` |
| `gc:item:9` | `watchlist` | `watchlist` | `0.6375` | `0.6375` | `0.5875` | `0.5875` | `0` | `clean` |
| `gc:item:14` | `watchlist` | `watchlist` | `0.6375` | `0.6375` | `0.5875` | `0.5875` | `0` | `clean` |
| `gc:item:18` | `watchlist` | `watchlist` | `0.72` | `0.72` | `0.67` | `0.67` | `0` | `clean` |
| `gc:item:45` | `promoted` | `promoted` | `0.72` | `0.72` | `0.8` | `0.8` | `0` | `clean` |

## Case class flips

- No case class flips in this run.

## What this suggests

The same controller-driven lane was run under `remote_workflow_v1b` and `remote_workflow_localmix_v1`. This comparison isolates kernel engine selection while keeping selection rules, controller logic, shaping, and Arbiter mapping fixed.
