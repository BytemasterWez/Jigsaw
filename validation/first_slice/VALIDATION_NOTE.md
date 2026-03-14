# Validation Note

## Purpose

This note records the first bounded Jigsaw Phase 1A validation run for the artifact interoperability lane.

Lane exercised:

`artifact -> extraction -> chunk -> judgment_request`

## Input used

- example input: `examples/inputs/sample_gc_artifact.json`
- source style: GC-normalized text-bearing note payload
- source system: `garbage_collector`

## Contracts exercised

- `artifact/v1`
- `extraction/v1`
- `chunk/v1`
- `judgment_request/v1`

`judgment_response/v1` was defined but not required for this proof.

## What remained stable

- contract names and version strings remained stable across the full lane
- provenance and linkage fields were preserved end to end
- source-specific shape stayed confined to the GC adapter entry point
- transforms remained reusable and did not require source-specific conditionals

## What required adapter logic

- the GC handoff object is treated as the normalized artifact input
- any future source-specific remapping should stay in `gc_artifact_adapter.py`, not in the transforms

For this first slice, the adapter stayed intentionally thin because the sample input already matches `artifact/v1`.

## Output generated

The run writes:

- validated artifact payload
- extraction payload
- chunk payload list
- judgment request payload
- Arbiter preview payload
- run log

Output directory:

- `validation/first_slice/output/`

## Downstream consumption

The emitted `judgment_request/v1` is ready for downstream consumption as a stable Jigsaw output.

Arbiter still requires its own final request shape, so a thin downstream adapter remains necessary. That shaping is previewed in `arbiter_request_adapter.py` and the generated `arbiter_preview.json`.

## Pass result

This milestone passes when:

- a normalized artifact enters Jigsaw through `artifact/v1`
- transforms complete successfully
- provenance and linkage survive each transform
- the outgoing `judgment_request/v1` is structurally stable
- no source-specific irregularities leak into the core transforms

This note records that bounded proof target.

