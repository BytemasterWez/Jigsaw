# Claim Of Proof

## What Is Proven Now

This repository currently proves that:

- Jigsaw can remain a stable middle capability repo while Garbage Collector and Arbiter stay external
- GC-backed context can enter the system through an explicit `gc_context_snapshot`
- the Controller can hold and transition `hypothesis_state`
- the Controller can emit `case_input` as a real handoff into Jigsaw composition
- Jigsaw can run a bounded kernel trio and emit `kernel_bundle_result`
- Arbiter can consume the bounded case through a thin public membrane
- standardized execution profiles can run the same spine repeatedly across live GC-backed cases
- deterministic and localmix kernel modes can reach the same decision spread on the tested lane when semantic class boundaries are normalized locally
- the system can emit readable user-facing briefs and summary reports from that governed forward pass

## What Is Not Yet Proven

This repository does not yet prove that:

- the longitudinal case lifecycle is first-class
- action outcomes are recorded and fed back into case confidence
- `case_state/v1`, `action_record/v1`, and `outcome_event/v1` are operational
- an Autoresearcher worker exists and runs under controller control
- the full governed loop over time is operational
- the system is production-ready, high-scale, or policy-complete
- the current architecture is superior across multiple domains beyond the current narrow wedge

## Honest Boundary

The strongest current claim is:

Jigsaw is now a stable, inspectable middle capability repo with a real governed forward pass:

`gc_context_snapshot -> hypothesis_state -> case_input -> kernel_bundle_result -> arbiter_request -> arbiter_response`

The strongest claim that should **not** be made yet is:

that the full longitudinal governed loop, including case-state revision and outcome feedback over time, is already complete.
