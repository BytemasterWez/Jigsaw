from __future__ import annotations

import os
import pytest

from jigsaw.lanes.kernel_lane.execute_lmstudio_observed_test import OUTPUT_DIR, run_lmstudio_observed_test
from jigsaw.lanes.kernel_lane.lmstudio_client import LMStudioClient


def test_lmstudio_observed_state_runner_if_local_server_is_available() -> None:
    if os.getenv("JIGSAW_RUN_LMSTUDIO_TEST") != "1":
        pytest.skip("Set JIGSAW_RUN_LMSTUDIO_TEST=1 to enable the optional LM Studio pressure test.")

    client = LMStudioClient()
    if not client.is_available():
        pytest.skip("LM Studio local server is not available for the optional pressure test.")

    result = run_lmstudio_observed_test()

    assert result["status"] == "success"
    assert result["retries_used"] in {0, 1}
    assert (OUTPUT_DIR / "observed_state_validated.json").exists()
    assert (OUTPUT_DIR / "kernel_bundle_result.json").exists()
    assert (OUTPUT_DIR / "arbiter_response.json").exists()
