# Forward-Pass Demo

## What happens

1. GC surfaces a grounded context snapshot from real corpus material.
2. The Controller creates and updates `hypothesis_state`.
3. The Controller emits `case_input` when the case is sufficient to package.
4. Jigsaw composes the case through bounded kernel execution.
5. Arbiter returns a bounded decision.
6. The product layer generates readable opportunity briefs.

## Proven batch result

Under `remote_workflow_v1b`:

- cases: 5
- promoted: 2
- watchlist: 3
- rejected: 0

## Why this matters

This shows that the system is not just an LLM wrapper. It is a governed forward pass with explicit intermediate objects, explicit composition, and explicit decision gating.
