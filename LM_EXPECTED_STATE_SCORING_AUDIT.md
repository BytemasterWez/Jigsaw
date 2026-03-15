# LM Expected-State Scoring Audit

## Scope

This audit compares deterministic and LM-backed `expected_state` behavior on:

- `gc:item:8`
- `gc:item:45`
- `gc:item:9`

The goal is to answer one question:

**Is LM `expected_state` reading expected fit differently, or is it just applying a stricter completeness standard than the deterministic path?**

## Deterministic baseline

Deterministic `expected_state` in [kernels.py](/E:/codex%20projects/Jigsaw/jigsaw/lanes/kernel_lane/kernels.py) is a simple alignment-ratio test:

- `ratio >= 0.75` -> `expected_state_aligned`
- `ratio >= 0.40 and < 0.75` -> `expected_state_partial`
- `ratio < 0.40` -> `expected_state_misaligned`

Confidence is then derived directly from that ratio.

This means the deterministic path treats:

- `3/4 aligned` as `aligned`
- `1/4 aligned` as `misaligned`

## Case comparisons

### `gc:item:8`

Observed/expected fit:

- `workflow_automation_focus = aligned`
- `consulting_use_case_defined = aligned`
- `offer_pricing_defined = misaligned`
- `operations_scaffold_present = aligned`
- alignment ratio: `0.75`

Deterministic:

- judgment: `expected_state_aligned`
- confidence: `0.8125`
- reason: `offer_pricing_defined is not aligned with the expected target.`

LM:

- judgment: `expected_state_partial`
- confidence: `0.75`
- reason: `The observed values for 'workflow_automation_focus' and 'operations_scaffold_present' align with the expected targets, but there is a misalignment in 'offer_pricing_defined'.`

Read:

- LM sees the same core evidence.
- LM does **not** miss the misaligned field.
- But LM downgrades `3/4 aligned` from `aligned` to `partial`.

### `gc:item:45`

Observed/expected fit:

- `workflow_automation_focus = aligned`
- `consulting_use_case_defined = aligned`
- `offer_pricing_defined = misaligned`
- `operations_scaffold_present = aligned`
- alignment ratio: `0.75`

Deterministic:

- judgment: `expected_state_aligned`
- confidence: `0.8125`
- reason: `offer_pricing_defined is not aligned with the expected target.`

LM:

- judgment: `expected_state_partial`
- confidence: `0.75`
- reasons include:
  - aligned workflow focus
  - aligned consulting use case
  - misaligned pricing

Read:

- Same pattern as `gc:item:8`.
- LM recognizes the aligned majority.
- It still classifies the case as `partial` instead of `aligned`.

### `gc:item:9`

Observed/expected fit:

- `workflow_automation_focus = aligned`
- `consulting_use_case_defined = misaligned`
- `offer_pricing_defined = misaligned`
- `operations_scaffold_present = misaligned`
- alignment ratio: `0.25`

Deterministic:

- judgment: `expected_state_misaligned`
- confidence: `0.6375`
- reasons:
  - `consulting_use_case_defined is not aligned with the expected target.`
  - `offer_pricing_defined is not aligned with the expected target.`
  - `operations_scaffold_present is not aligned with the expected target.`

LM:

- judgment: `expected_state_partial`
- confidence: `0.75`
- reasons:
  - workflow automation focus aligns
  - consulting use case and pricing do not align

Read:

- LM again sees the evidence direction correctly.
- But this time it upgrades a weak `1/4 aligned` case from `misaligned` to `partial`.
- It also under-reports the full extent of misalignment by omitting `operations_scaffold_present` from the reasons.

## Main finding

LM `expected_state` is **not** merely more conservative than the deterministic path.

If it were only stricter, we would expect:

- strong cases to move `aligned -> partial`
- weak cases to stay `misaligned` or move lower

That is **not** what happened.

Instead, LM is collapsing mixed-fit cases toward `expected_state_partial` in both directions:

- `gc:item:8`: `aligned -> partial`
- `gc:item:45`: `aligned -> partial`
- `gc:item:9`: `misaligned -> partial`

That means the LM is applying a different decision rule:

- deterministic path: **thresholded alignment ratio**
- LM path: **narrative mixed-fit judgment**

In practice, LM is acting as if:

- any meaningful mix of aligned and misaligned signals is `partial`

rather than:

- `0.75+ aligned = aligned`
- `below 0.40 = misaligned`

## What this rules out

This does **not** look like:

- transport/runtime instability
- wrong evidence ids
- contradiction spillover
- simple low-confidence under-scoring

The confidences are not especially low:

- strong cases dropped only slightly: `0.8125 -> 0.75`
- weak case was actually inflated: `0.6375 -> 0.75`

So the main issue is **classification semantics**, not confidence compression.

## Assessment

The LM is reading expected-fit evidence in a more narrative way than the deterministic kernel.

It appears to be using a standard closer to:

- "some expected fit exists, but not full fit" -> `partial`

instead of the intended standard:

- "how many expected targets are aligned?" -> thresholded final class

That means LM `expected_state` is answering a slightly different question than the deterministic kernel.

## Recommended next move

Do not do another broad prompt tweak first.

The clean next fix is a structural one, parallel to the `observed_state` repair:

1. have LM report structured expected-fit facts, not the final class
2. include fields such as:
   - `aligned_slots`
   - `misaligned_slots`
   - `missing_slots`
   - `alignment_ratio`
   - `fit_reason`
3. deterministically normalize those facts into the existing `kernel_output/v1` contract

That would let the system preserve the current external contract while restoring the intended semantics:

- `3/4 aligned` -> `expected_state_aligned`
- `1/4 aligned` -> `expected_state_misaligned`

## Bottom line

LM `expected_state` is failing because it is applying the wrong class boundary, not because it is unstable or simply too cautious.

The next fix should separate:

- **LM expected-fit reporting**
from
- **final expected-state classification**

using deterministic local normalization into the unchanged kernel contract.
