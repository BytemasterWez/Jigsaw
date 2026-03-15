# Execution Profile Spec

## Purpose

An execution profile is the configuration layer above contracts and lanes.

It exists to keep execution behavior repeatable across varying cases by fixing:

- selection rules
- shaping rules
- kernel bundle choice
- Arbiter handoff behavior
- output pack structure
- validation expectations

Different cases should produce different outputs. The profile ensures they pass through the same disciplined process.

## Model

The framework now has three distinct control layers:

1. **Contracts**
   - define object shapes
2. **Lanes**
   - define execution steps
3. **Execution profiles**
   - define how a lane is parameterized for a repeatable use case

## Naming

Profiles should use:

`<use_lane>_v<major>`

Examples:

- `remote_workflow_v1`
- `document_triage_v1`
- `planning_signal_v1`

Version changes should be deliberate. If the process changes materially, the profile version should change.

## Required profile sections

Every profile must define:

### Identity

- `profile_name`
- `profile_version`

### Selection

Defines how primary and supporting material are chosen.

Required fields:

- `primary_rule`
- `supporting_rule`
- `max_supporting_items`

Optional fields may include:

- primary query terms
- minimum primary score
- primary case limit
- supporting query terms
- supporting minimum score

### Shaping

Defines how selected material is shaped into the active lane input.

Required fields:

- whether the artifact lane is used
- case template name

Optional fields may include:

- signal term groups
- domain-specific heuristics
- minimum expected observations

### Kernels

Defines which kernel bundle is used and whether each slot is deterministic or model-backed.

Required fields:

- kernel implementation mode for each slot used by the profile

### Arbiter

Defines the Arbiter handoff behavior.

Required fields:

- adapter name
- confidence projection rule
- output mode

### Outputs

Defines what gets written for each case and for the batch summary.

Required fields:

- output root
- whether request, bundle, response, run log, and summary are saved

### Validation

Defines the minimum proof conditions for the profile.

Required fields:

- whether a primary item is required
- minimum supporting item count
- whether a kernel bundle is required
- whether an Arbiter response is required

## What must stay fixed within a profile run

Within one profile batch run, these should not drift between cases:

- selection rules
- shaping rules
- kernel bundle choice
- Arbiter mapping rule
- output format
- logging fields
- pass/fail conditions

If these change, the run is no longer one coherent profile execution.

## What may vary between cases

These may vary naturally:

- selected primary item
- selected supporting items
- kernel outputs
- bundle judgment
- bundle confidence
- Arbiter fit score
- Arbiter result

That variation is the point. The process stays fixed while the data differs.

## First calibrated use

The first calibrated execution profile is:

- `remote_workflow_v1b`

Its purpose is to run a small batch of live Garbage Collector-backed remote-workflow cases through the same Jigsaw and Arbiter path so outcomes can be compared without process drift and without uniformly flattering results.
