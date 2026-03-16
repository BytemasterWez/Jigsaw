from __future__ import annotations

import json
from pathlib import Path

from jigsaw.engines.watchdog import validate_kernel_watchdog_result_v1
from jigsaw.lanes.real_case_lane.execute_profile_batch import run_profile_batch


def test_profile_batch_blocks_case_on_watchdog_fail(monkeypatch, tmp_path: Path) -> None:
    import jigsaw.lanes.real_case_lane.execute_profile_batch as batch_module

    def _forced_fail(*args, **kwargs):
        timestamp = kwargs["timestamp"]
        return [
            validate_kernel_watchdog_result_v1(
                {
                    "contract": "kernel_watchdog_result",
                    "version": "v1",
                    "watchdog_id": "kw:kx:forced",
                    "exchange_id": "kx:forced",
                    "kernel_name": "expected_state",
                    "verdict": "fail",
                    "reasons": ["forced_test_failure"],
                    "timestamp": timestamp,
                }
            )
        ]

    monkeypatch.setattr(batch_module, "inspect_kernel_exchanges", _forced_fail)

    output_root = tmp_path / "blocked_batch"
    summary = run_profile_batch(case_limit=1, output_root_override=output_root)

    assert summary["cases_run"] == 1
    assert summary["blocked"] == 1
    assert summary["cases"][0]["arbiter_judgement"] == "blocked"
    assert summary["cases"][0]["watchdog_policy_action"] == "block_case"

    case_dir = output_root / f"case_01_gc_{summary['cases'][0]['primary_item_id']}"
    assert (case_dir / "watchdog_policy.json").exists()
    assert (case_dir / "watchdog_policy_decision.json").exists()
    assert (case_dir / "BLOCKED_CASE.md").exists()
    assert not (case_dir / "arbiter_exchange.json").exists()

    with (case_dir / "watchdog_policy_decision.json").open("r", encoding="utf-8") as handle:
        policy_decision = json.load(handle)

    assert policy_decision["blocked"] is True
    assert policy_decision["highest_verdict"] == "fail"
    assert "expected_state:forced_test_failure" in policy_decision["reasons"]
