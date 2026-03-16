# Jigsaw Architecture Overview

## Scope

This repository implements the current Jigsaw-centered capability layer of a governed intelligence stack.

- Garbage Collector is external and supplies grounded context
- Arbiter is external and supplies bounded final judgment
- Jigsaw owns the middle forward-pass spine:
  - Controller state
  - case packaging
  - kernel execution
  - composition
  - product artifact generation

The current proof domain remains intentionally narrow: remote-workflow or opportunity triage.

## Core Sentence

Garbage Collector grounds context, the Controller tracks exploration state, Jigsaw composes bounded analysis, Arbiter gates the decision, and the product layer emits a readable artifact.

## Design Goal

Prove that an AI-capable forward pass can be:

- more inspectable than a monolithic agent loop
- more governable than direct model-to-action behavior
- auditable through explicit contracts and intermediate objects
- diagnosable when one bounded layer fails semantically

## Current Runtime Flow

1. GC-backed retrieval produces `gc_context_snapshot`.
2. The Controller creates or updates `hypothesis_state`.
3. The Controller selects a bounded `next_probe`.
4. When ready, the Controller emits `case_input`.
5. Jigsaw composes the case through:
   - `observed_state`
   - `expected_state`
   - `contradiction`
6. Jigsaw emits `kernel_bundle_result`.
7. A thin adapter maps that result into `arbiter_request`.
8. Arbiter returns `arbiter_response`.
9. The product layer emits readable briefs and summary reports.

## Explicit Object Spine

The current system is organized around this explicit chain:

`gc_context_snapshot -> hypothesis_state -> case_input -> kernel_bundle_result -> arbiter_request -> arbiter_response`

This is the core architectural achievement because it keeps:

- context
- exploration state
- composition
- judgment

as separate inspectable stages rather than one opaque prompt loop.

## Current Jigsaw Center

The current engine center of gravity is:

- Controller state transitions
- case packaging
- reusable kernel runtime
- execution profiles
- bounded composition
- product artifact generation

That is what makes Jigsaw the middle capability repo in the current stack.

## What This Repo Is Not Yet

This repo is not yet:

- a first-class longitudinal case manager
- an outcome-feedback engine
- a persistent action-execution system
- an Autoresearcher worker
- a companion UI

The forward pass is real. The return loop over time is not yet first-class.

## Potential Safety Primitive

One serious next safety pattern is an **independent exchange watchdog**.

The idea is deliberately narrow:

- one job
- one question
- one action

The watchdog would not judge whether content is good, useful, or domain-correct.
It would only check whether a returned packet is a legitimate response to what was sent.

That makes it structurally auditable because it can ask a bounded contract question:

- did the response conform to the declared output shape?
- did it stay within the scope of the kernel or membrane that issued the request?
- did it introduce fields, actions, or claims outside the authorized surface?

If the answer is no, the watchdog should cut access at the permission layer rather than argue with the calling component.

### Important boundary note

At the current Jigsaw -> Arbiter membrane, the repo already persists:

- `arbiter_request`
- `arbiter_response`

So an `arbiter_exchange/v1` object would be straightforward to add.

But if the real safety question is **whether an LLM obeyed the bounded task it was given**, then the stronger long-term boundary is probably the **kernel runtime exchange**, not Arbiter alone.

Why:

- Arbiter sees a compressed bounded case request
- the kernel runtime sees the model-facing prompt/input and the raw returned packet

So a serious watchdog design likely has two possible exchange boundaries:

- `arbiter_exchange/v1` for membrane obedience
- kernel exchange records for model obedience

The architectural point is the same in both cases:

**safety comes from independent, external, contract-scope checking rather than trusting the same component that issued the request to judge its own compliance.**

## Success Criteria

The current architecture is successful if:

- the same explicit spine runs in single-case and batch lanes
- profile selection changes runtime behavior without changing the lane shape
- failures can be localized to the responsible layer
- bounded local models can participate without owning semantic class boundaries
- the final output is readable by a human, not just technically valid
