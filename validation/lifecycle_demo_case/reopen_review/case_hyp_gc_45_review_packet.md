# Reopen Review Packet

## Case state

- case_id: `case:hyp:gc:45`
- hypothesis_id: `hyp:gc:45`
- current_status: `watching`
- latest_decision: `promoted`
- confidence_current: `0.69`
- confidence_trajectory: `down`
- latest_outcome: `weakened`
- reopen_required: `True`

## Latest action record

- action_id: `action:case:hyp:gc:45:1`
- recommended_action: `prioritise_for_review`
- action_taken: `reviewed`
- taken_by: `human`
- timestamp: `2026-03-15T12:30:00Z`
- notes: Seeded lifecycle demo analyst review.

## Latest outcome event

- event_id: `outcome:action:case:hyp:gc:45:1`
- observed_outcome: `weakened`
- recorded_by: `human`
- timestamp: `2026-03-16T09:00:00Z`
- effect_on_confidence: `-0.12`
- confidence_delta: `0.0`
- notes: Customer follow-up weakened the case.

## Why this case was reopened

- reopen_conditions: `['watchdog_warn']`
- reopen_required: `True`

## Fresh case_input preview

```json
{
  "contract": "case_input",
  "version": "v1",
  "case_id": "case:hyp:gc:45",
  "hypothesis_id": "hyp:gc:45",
  "question_or_claim": "Assess whether this remote workflow opportunity is ready to package for review.",
  "primary_evidence_ids": [
    "gc:item:45"
  ],
  "supporting_evidence_ids": [
    "gc:item:8",
    "gc:item:22",
    "gc:item:14"
  ],
  "conflicting_evidence_ids": [],
  "missing_evidence": [],
  "current_confidence": 0.78,
  "reason_for_packaging": "sufficient_support_low_conflict"
}
```
