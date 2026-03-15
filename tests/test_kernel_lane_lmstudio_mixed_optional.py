from __future__ import annotations

import os

import pytest

from jigsaw.lanes.kernel_lane.execute_lmstudio_mixed_test import OUTPUT_DIR, run_lmstudio_mixed_test
from jigsaw.lanes.kernel_lane.lmstudio_client import LMStudioClient


def test_lmstudio_mixed_runner_if_local_server_is_available() -> None:
    if os.getenv("JIGSAW_RUN_LMSTUDIO_TEST") != "1":
        pytest.skip("Set JIGSAW_RUN_LMSTUDIO_TEST=1 to enable the optional LM Studio mixed-bundle test.")

    client = LMStudioClient()
    if not client.is_available():
        pytest.skip("LM Studio local server is not available for the optional mixed-bundle test.")

    result = run_lmstudio_mixed_test()

    assert result["status"] == "success"
    assert result["observed_state_retries_used"] in {0, 1}
    assert result["expected_state_retries_used"] in {0, 1}
    assert (OUTPUT_DIR / "observed_state_validated.json").exists()
    assert (OUTPUT_DIR / "expected_state_validated.json").exists()
    assert (OUTPUT_DIR / "kernel_bundle_result.json").exists()
    assert (OUTPUT_DIR / "arbiter_response.json").exists()
