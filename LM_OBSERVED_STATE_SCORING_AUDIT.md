# LM Observed-State Scoring Audit

## Scope

This note audits `observed_state` scoring under:

- deterministic baseline: `remote_workflow_v1b`
- LM-backed comparison: `remote_workflow_localmix_v1`

Cases included:

- `gc:item:8` - flipped `promoted -> watchlist`
- `gc:item:45` - flipped `promoted -> watchlist`
- `gc:item:9` - stable `watchlist`, used as contrast

## Sharp question

Is LM `observed_state` wrong because it reads the evidence differently, or because it scores the same evidence too conservatively?

## Short answer

Mostly **different judgment criteria**, not just lower confidence.

Across all three cases, the deterministic path marks `observed_state_clear` whenever the minimum expected observations are present. The LM path instead treats any false observed item as enough to downgrade the class to `observed_state_partial`, even when:

- all four observations are present
- evidence coverage is complete
- the contradiction kernel is unchanged

So the main issue is not merely under-confidence on the same class. It is that LM `observed_state` is using a stricter internal definition of what counts as `clear`.

## Shared evidence pattern

All three audited cases have:

- `observed_count = 4`
- `minimum_expected_observations = 4`
- four direct evidence records

The deterministic logic reads that as sufficient coverage for `observed_state_clear`.

The LM path reads the same shape as `observed_state_partial` whenever at least one observed item is false.

That means the LM kernel is conflating:

- observation coverage

with:

- overall positivity / completeness of the observed values

Those are not the same thing.

## Case: `gc:item:8`

### Source evidence snapshot

- primary: `AI workflows / remote income`
- supporting: pricing notes, remote workflow systems, business ops
- observed items in kernel input:
  - `workflow_automation_focus = true`
  - `consulting_use_case_defined = true`
  - `offer_pricing_defined = false`
  - `operations_scaffold_present = true`

### Deterministic `observed_state`

- judgment: `observed_state_clear`
- confidence: `0.85`
- reason:
  - `Observed coverage meets the minimum expected threshold.`

### LM `observed_state`

- judgment: `observed_state_partial`
- confidence: `0.7`
- reasons:
  - coverage is exactly at the minimum expected threshold
  - one observed item is false, so not all expected items were observed clearly

### Read

- evidence references are not missing
- the LM is not failing to see the evidence
- the downgrade happens because it treats one false observed item as enough to invalidate `clear`

### Classification vs scoring

- classification drift: **yes**
- confidence drift: **yes** (`0.85 -> 0.7`)
- dominant issue: **classification threshold**

## Case: `gc:item:45`

### Source evidence snapshot

- primary: remote workflow systems / automation ideas
- supporting: remote income, business ops, adjacent remote-work item
- observed items in kernel input:
  - `workflow_automation_focus = true`
  - `consulting_use_case_defined = true`
  - `offer_pricing_defined = false`
  - `operations_scaffold_present = true`

### Deterministic `observed_state`

- judgment: `observed_state_clear`
- confidence: `0.85`
- reason:
  - `Observed coverage meets the minimum expected threshold.`

### LM `observed_state`

- judgment: `observed_state_partial`
- confidence: `0.6`
- reasons:
  - one false observed item reduces overall clarity
  - three true plus one false means not all expected aspects are clearly covered

### Read

- same structural issue as `gc:item:8`
- evidence is being read, but the rubric is harsher
- the confidence drop is larger here (`0.85 -> 0.6`)

### Classification vs scoring

- classification drift: **yes**
- confidence drift: **yes**
- dominant issue: **classification threshold with additional conservative scoring**

## Case: `gc:item:9`

### Source evidence snapshot

- primary: AI tools / prompt library cleanup
- supporting: remote income, remote workflow systems, business ops
- observed items in kernel input:
  - `workflow_automation_focus = true`
  - `consulting_use_case_defined = false`
  - `offer_pricing_defined = false`
  - `operations_scaffold_present = false`

### Deterministic `observed_state`

- judgment: `observed_state_clear`
- confidence: `0.85`

### LM `observed_state`

- judgment: `observed_state_partial`
- confidence: `0.7`
- reasons:
  - minimum observation count is met
  - only one observation is true while three are false

### Read

- this case did not flip class overall because deterministic already went `watchlist` from `expected_state`
- but LM `observed_state` still downgrades it from `clear` to `partial`
- that confirms the issue is systemic inside the LM observed-state rubric, not limited to the promoted cases

### Classification vs scoring

- classification drift: **yes**
- confidence drift: **yes**
- dominant issue: **systematic harsher reading of what “clear” means**

## What the deterministic logic sees that LM is down-weighting

The deterministic path treats `observed_state` as a coverage test:

- are the expected observation slots present?
- is minimum coverage reached?

The LM path is treating `observed_state` partly as a quality or positivity test:

- are most values true?
- does any false value make the observed picture less than clear?

That is why the LM kernel keeps saying `partial` even when coverage is complete.

## Evidence reference quality

No obvious evidence-reference failure showed up in the audited cases:

- LM used the expected evidence ids
- reasons refer to the actual observed-value pattern
- no missing or spurious evidence references were the main problem

So this is not mainly an evidence retrieval issue.

## Conclusion

The main localmix drift in `observed_state` is:

- **not** transport instability
- **not** missing evidence references
- **not** only lower confidence on the same semantic class

It is primarily:

- **classification threshold drift**

Specifically:

- deterministic `observed_state_clear` means complete observation coverage
- LM `observed_state_partial` means complete coverage but with one or more false observed values

That stricter LM rubric then drags confidence down and compresses strong cases into lower bundle confidence and lower Arbiter `fit_score`.

## Best next move

Do not add more profiles yet.

The next clean technical move is one of:

1. add a **kernel-specific normalization rule** for LM `observed_state`
   - if minimum coverage is met, do not allow `clear -> partial` solely because one observed item is false

2. rewrite the LM `observed_state` task so the rubric explicitly separates:
   - observation coverage
   - observed value polarity / completeness

If choosing between them, the cleaner next experiment is probably the second:

- tighten the `observed_state` rubric itself
- rerun only the audited cases first
- then rerun the 5-case batch

That keeps the next step forensic and bounded.
