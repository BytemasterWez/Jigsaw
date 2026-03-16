# Blocked Case Review Packet

- case_id: `case:hyp:gc:45`
- blocked_status: `watchdog_manual_review`
- blocked_reason: `watchdog_warn`
- reopen_flag: `True`
- priority_hint: `review_soon`
- generated_at: `2026-03-16T17:00:00Z`

## Watchdog

- verdict: `warn`
- exchange_id: `kx:lifecycle-demo:expected_state`
- kernel_name: `expected_state`
- reasons: `['engine_mode_mismatch']`

## References

- latest_case_summary_ref: `None`
- latest_evidence_refs: `['gc:item:45', 'gc:item:8', 'gc:item:22', 'gc:item:14']`
- latest_watchdog_event_refs: `['E:\\codex projects\\Jigsaw\\validation\\pilot_local\\case_lifecycle\\case_01\\kernel_watchdog_result.json', 'kx:lifecycle-demo:expected_state']`
- override_history_refs: `[]`

## Recommended operator actions

- `override_and_continue`
- `close_as_invalid`
- `defer_for_manual_review`
