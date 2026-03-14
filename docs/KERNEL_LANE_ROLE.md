# Kernel Lane Role

## Purpose

The kernel lane is the first bounded proof that Jigsaw can run portable judgment primitives under shared discipline.

It exists to demonstrate that Jigsaw can:

- accept a stable kernel input
- execute a fixed sequence of narrow kernels
- preserve evidence and lineage across the sequence
- emit a composed bundle result without flattening all judgments into one vague score

## Current Phase 1B Scope

The first kernel lane uses exactly three kernels:

- `observed_state`
- `expected_state`
- `contradiction`

Execution order is fixed.

## What the lane proves

- portable kernels can run under Jigsaw control
- shared contracts can hold across a multi-kernel lane
- composition can remain in Jigsaw rather than being buried inside one kernel

## What the lane does not prove

- dynamic routing
- broad kernel orchestration
- consequence or temporal handling
- score fusion
- agent behavior

