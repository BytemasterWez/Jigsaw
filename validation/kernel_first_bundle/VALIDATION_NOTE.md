# Validation Note

## Purpose

This note records the first bounded Jigsaw Phase 1B validation run for the kernel-family lane.

Lane exercised:

`kernel_input -> observed_state -> expected_state -> contradiction -> kernel_bundle_result`

## Input used

- example input: `examples/inputs/sample_kernel_input.json`
- source style: stable Jigsaw kernel input object
- source system: `garbage_collector`

## Contracts exercised

- `kernel_input/v1`
- `kernel_output/v1`
- `kernel_bundle_result/v1`

## What remained stable

- a single shared kernel input entered the full lane
- all three kernels emitted the same output contract shape
- kernel order remained fixed and reproducible
- evidence identifiers and lineage survived into the bundle result
- composition stayed in Jigsaw rather than being buried in any one kernel

## What required adapter logic

No source-specific adapter shaping was required inside this lane.

The input is already a normalized Jigsaw-side kernel input. Any future source-specific mapping into `kernel_input/v1` should happen before this lane starts.

## Output generated

The run writes:

- validated kernel input
- observed-state kernel output
- expected-state kernel output
- contradiction kernel output
- kernel bundle result
- run log

Output directory:

- `validation/kernel_first_bundle/output/`

## Pass result

This milestone passes when:

- all three kernels emit valid `kernel_output/v1`
- the order is controlled and deterministic
- evidence and lineage survive the full sequence
- Jigsaw emits one valid `kernel_bundle_result/v1`

This note records that bounded proof target.

