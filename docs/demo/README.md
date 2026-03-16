# Governed Forward-Pass Demo

This demo shows the current strongest proven slice of the system: a governed forward pass from grounded context to bounded judgment and readable output.

## What this demonstrates

- GC-backed context grounding
- Controller hypothesis state
- Jigsaw case composition
- Arbiter decision membrane
- user-facing opportunity briefs

## Current object chain

`gc_context_snapshot -> hypothesis_state -> case_input -> kernel_bundle_result -> arbiter_request -> arbiter_response`

## Included demo artifacts

- [Forward pass walkthrough](FORWARD_PASS_DEMO.md)
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

This demo shows the governed forward pass only.

It does not yet claim:

- longitudinal case lifecycle management
- outcome-event feedback loops
- human-assisted revision over time
- persistent case-state governance
