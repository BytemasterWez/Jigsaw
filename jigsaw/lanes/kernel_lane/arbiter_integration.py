from __future__ import annotations

import importlib.util
import json
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .models import KernelBundleResultV1, KernelInputV1


REPO_ROOT = Path(__file__).resolve().parents[3]
WORKSPACE_ROOT = REPO_ROOT.parent
ARBITER_REPO = WORKSPACE_ROOT / "arbiter-public"
ARBITER_REQUEST_SCHEMA_PATH = ARBITER_REPO / "schemas" / "arbiter_request.schema.json"
ARBITER_RESPONSE_SCHEMA_PATH = ARBITER_REPO / "schemas" / "arbiter_response.schema.json"
ARBITER_RUN_MODULE_PATH = ARBITER_REPO / "demo" / "run.py"


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=1)
def _load_arbiter_run_module() -> Any:
    spec = importlib.util.spec_from_file_location("arbiter_demo_run", ARBITER_RUN_MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load Arbiter demo module from {ARBITER_RUN_MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_arbiter_request_schema() -> dict[str, Any]:
    return _load_json(ARBITER_REQUEST_SCHEMA_PATH)


def load_arbiter_response_schema() -> dict[str, Any]:
    return _load_json(ARBITER_RESPONSE_SCHEMA_PATH)


def validate_arbiter_request(payload: dict[str, Any]) -> None:
    Draft202012Validator(load_arbiter_request_schema()).validate(payload)


def validate_arbiter_response(payload: dict[str, Any]) -> None:
    Draft202012Validator(load_arbiter_response_schema()).validate(payload)


def _freshness_days(kernel_input: KernelInputV1, bundle: KernelBundleResultV1) -> int:
    newest_observation = max(
        datetime.fromisoformat(record.observed_at.replace("Z", "+00:00")) for record in kernel_input.evidence
    )
    bundle_created = datetime.fromisoformat(bundle.metadata.created_at.replace("Z", "+00:00"))
    return max(0, (bundle_created.astimezone(UTC) - newest_observation.astimezone(UTC)).days)


def _bundle_fit_score(bundle: KernelBundleResultV1) -> float:
    bundle_judgment = bundle.composed_summary.bundle_judgment
    base_confidence = bundle.metadata.confidence or 0.5
    contradiction_penalty = 0.0
    if any(output.judgment in {"contradiction_detected", "critical_contradiction"} for output in bundle.kernel_outputs):
        contradiction_penalty = 0.2

    if bundle_judgment == "aligned":
        score = max(base_confidence, 0.8)
    elif bundle_judgment == "partially_aligned":
        score = max(base_confidence - 0.05, 0.55)
    elif bundle_judgment == "contradictory":
        score = max(base_confidence - contradiction_penalty, 0.4)
    else:
        score = min(base_confidence, 0.3)

    return round(min(max(score, 0.0), 1.0), 4)


def kernel_bundle_result_to_arbiter_request(
    kernel_input: KernelInputV1,
    bundle: KernelBundleResultV1,
) -> dict[str, Any]:
    request = {
        "candidate_id": kernel_input.subject_id,
        "domain": "jigsaw_kernel_bundle",
        "candidate_type": kernel_input.subject_type,
        "summary": bundle.composed_summary.summary,
        "evidence": {
            "source_count": len(kernel_input.evidence),
            "freshness_days": _freshness_days(kernel_input, bundle),
            "fit_score": _bundle_fit_score(bundle),
            "estimated_value_band": bundle.composed_summary.bundle_judgment,
        },
        "context": {
            "buyer_profile": kernel_input.context.get("analysis_profile", "default"),
            "current_queue_pressure": "medium",
            "action_cost": "medium",
            "jigsaw_bundle_id": bundle.bundle_id,
            "jigsaw_bundle_judgment": bundle.composed_summary.bundle_judgment,
            "kernel_sequence": [output.kernel_type for output in bundle.kernel_outputs],
        },
    }
    validate_arbiter_request(request)
    return request


def adjudicate_via_current_arbiter(request: dict[str, Any]) -> dict[str, Any]:
    validate_arbiter_request(request)
    module = _load_arbiter_run_module()
    response = module.adjudicate(request)
    validate_arbiter_response(response)
    return response
