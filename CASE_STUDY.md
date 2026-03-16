# GitHub-Ready Case Study

Jigsaw began as a set of promising but separate proofs. The goal was to turn those proofs into a **governed forward pass**: a system that could move from grounded context to bounded judgment through explicit intermediate objects, inspectable runtime behavior, and readable output.

#### Starting point

The system had four real things working:

- a bounded artifact lane
- a bounded kernel lane
- bounded local-model viability
- one real GC -> Jigsaw -> Arbiter case

That was enough to show the pieces could work, but not enough to show there was a repeatable engine.

#### The gaps

Three problems remained:

- **Repeatability**: one real case is not a reliable lane
- **Discrimination**: early runs were too flattering and not calibrated enough
- **Legibility**: the system worked better than the repo and outputs explained

#### What changed

##### 1. Standardized the lane

A calibrated execution profile, `remote_workflow_v1b`, fixed:

- case selection
- supporting-item selection
- shaping rules
- kernel bundle
- Arbiter mapping
- output structure

That turned one-off proofs into repeatable execution.

##### 2. Achieved believable spread

The early profile was too favorable. Tightening the profile produced a believable batch result across 5 live GC-backed cases:

- `2 promoted`
- `3 watchlist`
- `0 rejected`

That was the first point where the engine looked calibrated rather than lucky.

##### 3. Built a user-facing product slice

The system was then made readable through:

- opportunity briefs
- summary reports
- Markdown and static HTML outputs

That established that the engine could produce something a human could actually consume.

##### 4. Made the runtime explicit

The architecture was hardened into an explicit object spine:

`gc_context_snapshot -> hypothesis_state -> case_input -> kernel_bundle_result -> arbiter_request -> arbiter_response`

That replaced implied flow with executable structure.

##### 5. Added profile-driven runtime selection

Kernel execution moved behind a reusable runtime so profiles could choose engine behavior explicitly:

- deterministic mode
- localmix mode

That made the lane configurable without changing the architecture.

##### 6. Diagnosed and corrected localmix semantic drift

The localmix path initially underperformed. The important result was not just the failure, but how precisely the system localized it.

It was **not**:

- runtime
- retrieval
- contradiction
- Arbiter
- the controller spine

It was kernel semantics.

Two structural fixes restored parity:

- `observed_state`: separate observation coverage from polarity
- `expected_state`: separate expected-fit reporting from final class assignment

In both cases, the model was changed to report structured facts, and local deterministic logic enforced the semantic class boundary.

#### Result

The same lane can now run in:

- deterministic mode
- localmix mode

and produce the same spread on the tested batch:

- `2 promoted`
- `3 watchlist`
- `0 rejected`

with:

- stable runtime
- `0` retries
- no class flips versus baseline

#### Why it matters

This is not just a capability result. It is a **system legibility and governed execution** result.

The system’s strongest property is not that it produces decisions, but that it makes those decisions traceable through explicit objects, explicit runtime choices, and explicit decision membranes.

That means failures can be localized by layer rather than blamed on “the AI” in general.

#### Current state

**Jigsaw now implements a governed forward pass from grounded context to bounded judgment and readable output, with explicit intermediate objects, profile-driven runtime selection, and comparable deterministic/localmix execution.**

#### What comes next

Two next steps are now clear:

- **Product truth**: run human feedback sessions on the briefs
- **Architecture maturity**: add `case_state/v1`, `action_record/v1`, and `outcome_event/v1` to build the return loop over time
