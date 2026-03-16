# Jigsaw

Jigsaw is the middle capability repo in a governed intelligence stack.

It currently proves an early governed lifecycle in which:

- Garbage Collector grounds context
- a Controller holds exploration state
- Jigsaw composes bounded analytical cases
- Arbiter returns a gated decision
- the product layer emits readable artifacts
- lifecycle state records what happened after action and whether the case should reopen

The current proof domain is remote-workflow or opportunity triage over live GC-backed material.

## Start Here

This repo currently has three best entry points:

- [Governed forward-pass demo](docs/demo/README.md) — the fastest way to see the system working
- [Case study](CASE_STUDY.md) — what was built, what changed, and why it matters
- [Operational proof](OPERATIONAL_PROOF.md) — the bounded claims the repo can currently support

## Current Architecture

The current stack is:

`Garbage Collector -> Controller -> Jigsaw -> Arbiter -> Product artifact`

Within that stack:

- **Garbage Collector** is the substrate intelligence layer
- **Controller** holds `hypothesis_state` and chooses the next bounded move
- **Jigsaw** consumes `case_input`, runs bounded kernels, and emits `kernel_bundle_result`
- **Arbiter** is the final judgment membrane
- **Product** generates readable briefs and summary reports

## Current Object Spine

The strongest architectural achievement so far is the explicit runtime object chain:

`gc_context_snapshot -> hypothesis_state -> case_input -> kernel_bundle_result -> arbiter_request -> arbiter_response`

This is what makes the system inspectable, diagnosable, and governable by layer.

The governed lifecycle now extends that forward-pass spine with:

`case_state -> action_record -> outcome_event -> case_relevance_signal`

## Governed Forward-Pass Demo

A public demo pack is available under [docs/demo/README.md](./docs/demo/README.md).

It shows the current strongest public slice:

- grounded GC context
- Controller state
- bounded Jigsaw composition
- Arbiter judgment
- batch summary
- promoted and watchlist brief examples
- exact reproduction commands

## What Has Been Proven

Jigsaw currently has bounded proof for:

### Artifact lane

A normalized artifact can enter Jigsaw, be validated, transformed, and emitted as stable downstream material with provenance preserved.

### Kernel trio

A shared `kernel_input` can run through:

- `observed_state`
- `expected_state`
- `contradiction`

and emit a composed `kernel_bundle_result`.

### Controller-driven spine

A live GC-backed case can now move through:

- `gc_context_snapshot`
- `hypothesis_state`
- `case_input`
- Jigsaw composition
- Arbiter judgment

in both single-case and standardized batch execution.

### Standardized execution profiles

Jigsaw now supports repeatable execution profiles. The calibrated deterministic profile, `remote_workflow_v1b`, produced a believable spread on 5 live GC-backed cases:

- `2 promoted`
- `3 watchlist`
- `0 rejected`

### Localmix parity

Jigsaw now supports a localmix profile in which:

- `observed_state = lmstudio`
- `expected_state = lmstudio`
- `contradiction = deterministic`

After structural normalization of LM kernel semantics, `remote_workflow_localmix_v1` recovered parity with the deterministic calibrated baseline on the tested 5-case batch:

- `2 promoted`
- `3 watchlist`
- `0 rejected`

with:

- stable runtime
- `0` retries
- no class flips versus `remote_workflow_v1b`

### Product artifacts

The current lane produces user-facing outputs:

- opportunity briefs in Markdown and static HTML
- batch summary reports
- a public forward-pass demo pack
- reopen review packets
- case monitoring queue

### Early governed lifecycle

Jigsaw now supports bounded lifecycle behavior beyond the forward pass:

- `case_state/v1`
- `action_record/v1`
- `outcome_event/v1`
- confidence revision and trajectory updates
- explicit reopen rules
- manual reopen/review flow
- GC-triggered reopen evaluation through `case_relevance_signal`
- operator-visible review artifacts and monitoring queue

## Systems Alignment Contribution

Jigsaw does not claim to solve alignment in the broadest philosophical sense.

It does contribute to a serious systems-alignment question:

**How do you build AI-capable systems whose context, exploration, analysis, judgment, and action remain modular, inspectable, and governable instead of collapsing into one opaque agent loop?**

The current architecture answers that in a bounded but practical way:

- explicit object boundaries
- explicit decision boundaries
- membrane-controlled judgment
- diagnosable failure by layer
- local enforcement of semantic thresholds where they matter

The localmix kernel work is a concrete proof of that property:

- runtime was not the problem
- retrieval was not the problem
- controller and Arbiter boundaries were not the problem
- the fault was isolated to kernel semantics
- parity was recovered by moving class boundaries back into local deterministic normalization

## What Exists Now

- GC substrate integration
- Controller state layer
- Jigsaw composition and kernel runtime layer
- Arbiter judgment membrane
- standardized execution profiles
- deterministic and LM-backed runtime modes
- readable brief and summary outputs
- a public governed forward-pass demo pack
- bounded lifecycle objects and revision rules
- operator-visible reopen review artifacts
- case monitoring queue

## What Is Not First-Class Yet

- automated outcome detection
- exchange-record objects such as `kernel_exchange/v1` or `arbiter_exchange/v1`
- external watchdog / circuit-breaker enforcement
- Autoresearcher worker
- companion UI

The system is now strong on the **governed forward pass** and in an **early governed lifecycle** phase, but weaker on full automation and independent watchdog enforcement.

## Reproduce The Current Strongest Slice

```powershell
python -m pytest
python -m jigsaw.lanes.real_case_lane.execute_profile_batch
python -m jigsaw.lanes.real_case_lane.generate_opportunity_briefs
python -m jigsaw.lanes.real_case_lane.generate_summary_report
```

## Key Files

- [docs/demo/README.md](./docs/demo/README.md)
- [ARCHITECTURE_OVERVIEW.md](./ARCHITECTURE_OVERVIEW.md)
- [ARCHITECTURE_DIAGRAM.md](./ARCHITECTURE_DIAGRAM.md)
- [FRAMEWORK_OVERVIEW.md](./FRAMEWORK_OVERVIEW.md)
- [OPERATIONAL_PROOF.md](./OPERATIONAL_PROOF.md)
- [docs/EXECUTION_PROFILE_SPEC.md](./docs/EXECUTION_PROFILE_SPEC.md)
- [docs/RESEARCH_CONTROLLER_ROLE.md](./docs/RESEARCH_CONTROLLER_ROLE.md)
- [validation/execution_profiles/remote_workflow_v1b/SUMMARY.md](./validation/execution_profiles/remote_workflow_v1b/SUMMARY.md)
- [validation/execution_profiles/remote_workflow_localmix_v1/COMPARISON_vs_remote_workflow_v1b.md](./validation/execution_profiles/remote_workflow_localmix_v1/COMPARISON_vs_remote_workflow_v1b.md)
