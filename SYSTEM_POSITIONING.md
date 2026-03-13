# System Positioning

## Purpose

Jigsaw is the middle layer in a three-repository architecture:

- Garbage Collector remembers
- Jigsaw gathers and transforms evidence
- Arbiter judges whether action is permitted

## What Jigsaw Is

Jigsaw is a capability layer built from a small fixed kernel chain.

Its job is to take a candidate and convert it into an explicit evidence bundle with:

- retrieved context
- structured evidence
- scores
- inferred consequences
- priority
- explanation

## What Jigsaw Is Not

Jigsaw is not:

- the memory substrate
- the judgment engine
- a merged orchestration monolith
- a hidden prompt chain that smuggles state between repos

## Boundary Rule

Jigsaw interoperates with the other systems only through explicit contracts:

- memory adapter contract
- message envelope contract
- Arbiter decision contract

The kernel logic itself should not contain repo-specific hacks.

## Standalone Use

Jigsaw can run alone in demo mode with local demo adapters.

That standalone mode exists to prove:

- kernel composition
- inspectability
- audit trace behavior

## Integrated Use

When connected to the other repos:

- Garbage Collector supplies prior context and stores the final trace
- Jigsaw transforms the candidate into an explicit bundle
- Arbiter returns the gating decision

The architectural stack is real, but the codebases remain separate.
