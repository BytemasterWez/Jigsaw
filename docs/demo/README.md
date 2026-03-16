# Jigsaw Demo Pack

This demo pack shows the two strongest proven public slices of the system:

- a governed forward pass from grounded context to bounded judgment and readable output
- an early governed lifecycle with stored case state, operator review, and governed rerun

## What this demonstrates

- GC-backed context grounding
- Controller hypothesis state
- Jigsaw case composition
- Arbiter decision membrane
- user-facing opportunity briefs
- lifecycle recording and reopen logic
- operator-visible queue, timeline, and review packet
- explicit operator decisions and governed rerun

## Current object chain

`gc_context_snapshot -> hypothesis_state -> case_input -> kernel_bundle_result -> arbiter_request -> arbiter_response`

## Lifecycle object chain

`case_state -> action_record -> outcome_event -> case_relevance_signal -> kernel_watchdog_result -> operator review -> governed rerun`

## Included demo artifacts

- [Forward pass walkthrough](FORWARD_PASS_DEMO.md)
- [Lifecycle walkthrough](LIFECYCLE_DEMO.md)
- [How it works](how_it_works.md)
- [Batch summary](remote_workflow_v1b_summary.md)
- [Promoted brief](promoted_brief.md)
- [Watchlist brief](watchlist_brief.md)

## Reproduce locally

```powershell
python -m pytest
python -m jigsaw.lanes.real_case_lane.execute_profile_batch
python -m jigsaw.lanes.real_case_lane.generate_opportunity_briefs
python -m jigsaw.lanes.real_case_lane.generate_summary_report
```

## Scope note

This demo pack shows the governed forward pass and an early governed lifecycle.

It does not yet claim:

- autonomous outcome detection
- background lifecycle orchestration
- system-triggered shutdown or circuit breaking
- full persistent case-manager governance
