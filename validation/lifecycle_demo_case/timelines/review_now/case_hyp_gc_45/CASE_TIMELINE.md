# Case Timeline

- case_id: `case:hyp:gc:45`
- latest_status: `watching`
- latest_decision: `promoted`
- confidence_current: `0.69`
- confidence_trajectory: `down`
- latest_reopen_reason: `watchdog_warn`

## Events

| Timestamp | Type | Summary | Confidence | Source |
| --- | --- | --- | --- | --- |
| `2026-03-15T11:45:00Z` | `case_created` | Case state opened for `case:hyp:gc:45`. | `-` | `case_state` |
| `2026-03-15T11:45:00Z` | `forward_pass_decision` | Forward pass returned `promoted` for the case. | `-` | `arbiter_exchange` |
| `2026-03-15T12:30:00Z` | `action_recorded` | Recorded `reviewed` after recommended action `prioritise_for_review`. | `-` | `action_record` |
| `2026-03-16T09:00:00Z` | `confidence_revised` | Confidence revised after `weakened`. | `0.81 -> 0.69` | `case_state` |
| `2026-03-16T09:00:00Z` | `outcome_recorded` | Outcome `weakened` was recorded. | `-` | `outcome_event` |
| `2026-03-16T10:00:00Z` | `relevance_signal` | New material produced `reopen_case`. | `-` | `case_relevance_signal` |
| `2026-03-16T11:00:00Z` | `latest_status` | Latest status is `watching` with decision `promoted`. | `None -> 0.69` | `case_state` |
| `2026-03-16T11:00:00Z` | `reopen_flagged` | Case marked for review due to `watchdog_warn`. | `-` | `case_state` |
| `2026-03-16T11:00:00Z` | `watchdog_warn` | Kernel watchdog returned `warn` for `expected_state`. | `-` | `kernel_watchdog_result` |
