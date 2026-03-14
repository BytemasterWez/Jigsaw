# Kernel Lane Validation Target

## Current milestone

Validate one fixed kernel-family lane inside Jigsaw:

`kernel_input -> observed_state -> expected_state -> contradiction -> kernel_bundle_result`

## Objective

Demonstrate that a stable kernel input can enter Jigsaw, pass through three narrow portable kernels in fixed order, and exit as a composed bundle result with evidence and lineage preserved.

## Contracts exercised

- `kernel_input/v1`
- `kernel_output/v1`
- `kernel_bundle_result/v1`

## Pass condition

This milestone passes when:

- a valid `kernel_input/v1` enters the lane
- all three kernels emit valid `kernel_output/v1`
- evidence and lineage survive the full sequence
- Jigsaw emits one valid `kernel_bundle_result/v1`
- composition remains in Jigsaw rather than collapsing into a single kernel

## Non-goals

This milestone is not intended to prove:

- dynamic kernel routing
- consequence or temporal composition
- runtime reconciliation policy
- production operator UI
- full kernel-family coverage

