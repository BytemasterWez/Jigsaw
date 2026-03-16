# Legacy Message Bus Schema

## Status

This document describes a historical Jigsaw design based on a shared `MessageEnvelope`.

It is preserved for lineage only.

It does **not** describe the current primary runtime architecture.

## Why It Is Legacy

The current Jigsaw forward pass no longer centers on one envelope flowing through every step.

The current explicit runtime spine is:

`gc_context_snapshot -> hypothesis_state -> case_input -> kernel_bundle_result -> arbiter_request -> arbiter_response`

That object chain is now the primary public architecture because it makes:

- context grounding
- exploration state
- case packaging
- bounded composition
- final judgment

visible as separate inspectable stages.

## Current Replacements

Use these current docs instead:

- [README.md](./README.md)
- [ARCHITECTURE_OVERVIEW.md](./ARCHITECTURE_OVERVIEW.md)
- [ARCHITECTURE_DIAGRAM.md](./ARCHITECTURE_DIAGRAM.md)
- [FRAMEWORK_OVERVIEW.md](./FRAMEWORK_OVERVIEW.md)
- [docs/RESEARCH_CONTROLLER_ROLE.md](./docs/RESEARCH_CONTROLLER_ROLE.md)

## Historical Note

The older `MessageEnvelope` design mattered because it helped establish:

- explicit kernel contracts
- auditability
- traceability

But it is no longer the best public description of the system that now exists in this repo.
