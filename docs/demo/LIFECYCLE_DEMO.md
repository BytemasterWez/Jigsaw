# Lifecycle Demo

This demo shows the current strongest proven lifecycle slice of the system: a stored case can move from a prior forward-pass decision into recorded action, recorded outcome, explicit reopen state, operator review, and a governed rerun.

## What this demonstrates

- stored `case_state`
- recorded `action_record`
- recorded `outcome_event`
- recorded `case_relevance_signal`
- recorded `kernel_watchdog_result`
- stored `arbiter_exchange`
- operator-visible monitor queue
- operator-visible case timeline
- operator review packet
- explicit operator decisions
- governed rerun through the forward pass

## Lifecycle object chain

`case_state -> action_record -> outcome_event -> case_relevance_signal -> kernel_watchdog_result -> operator review -> governed rerun`

## Seeded demo case

The lifecycle demo is seeded from the real stored remote-workflow case:

- base proof: [Lifecycle demo proof](../../validation/lifecycle_demo_case/LIFECYCLE_DEMO_PROOF.md)
- seeded lifecycle case: [base case directory](../../validation/lifecycle_demo_case/case_lifecycle/base/case_01/)

## Included lifecycle artifacts

- [Lifecycle demo proof](../../validation/lifecycle_demo_case/LIFECYCLE_DEMO_PROOF.md)
- [Monitor queue](../../validation/lifecycle_demo_case/monitor_queue/CASE_MONITOR_QUEUE.md)
- [Base case timeline](../../validation/lifecycle_demo_case/timelines/case_hyp_gc_45/CASE_TIMELINE.md)
- [Reopen review queue](../../validation/lifecycle_demo_case/reopen_review/REOPEN_QUEUE.md)
- [Review packet](../../validation/lifecycle_demo_case/reopen_review/case_hyp_gc_45_review_packet.md)
- [Review-now decision](../../validation/lifecycle_demo_case/case_reviews/review_now/case_hyp_gc_45/REVIEW_DECISION.md)
- [Rerun-forward-pass decision](../../validation/lifecycle_demo_case/case_reviews/rerun_forward_pass/case_hyp_gc_45/REVIEW_DECISION.md)

## Operator proof

The seeded lifecycle demo proves two bounded operator actions:

- `review_now`
- `rerun_forward_pass`

In the rerun branch, the system writes fresh:

- `hypothesis_state`
- `case_input`
- `kernel_bundle_result`
- `kernel_exchanges`
- `kernel_watchdog_results`
- `arbiter_request`
- `arbiter_response`
- `arbiter_exchange`

## Why this matters

This shows that the system is no longer only a governed decision-at-a-point-in-time. It now has an explicit return path with stored state, recorded review, and a governed rerun path that stays inside the same object and membrane boundaries.

## What this does not yet claim

This demo is still intentionally bounded.

It does not yet claim:

- autonomous outcome detection
- automatic reruns
- background lifecycle watchers
- system-triggered shutdown or circuit breaking
- a full persistent case manager service

