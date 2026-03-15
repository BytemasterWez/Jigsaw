from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any

from .lmstudio_client import LMStudioClient, LMStudioError
from .models import KernelInputV1, KernelOutputV1
from .utils import build_metadata, make_id
from .validators import validate_kernel_output_v1


@dataclass
class LMObservedStateRun:
    validated_output: KernelOutputV1
    raw_model_output: dict[str, Any]
    generated_payload: dict[str, Any]
    model_name: str
    retries_used: int
    elapsed_seconds: float


def _build_output_shell(
    payload: KernelInputV1,
    *,
    pipeline_run_id: str,
    generated_at: str,
    confidence: float = 0.0,
) -> dict[str, Any]:
    output_id = make_id("kernel_output", payload.input_id, "observed_state")
    return {
        "contract": "kernel_output",
        "version": "v1",
        "output_id": output_id,
        "kernel_type": "observed_state",
        "input_id": payload.input_id,
        "status": "success",
        "judgment": "observed_state_partial",
        "confidence": confidence,
        "reasons": ["Placeholder; must be replaced by the model."],
        "evidence_used": [record.evidence_id for record in payload.evidence[: len(payload.content.observed_items)]],
        "metadata": build_metadata(
            output_id,
            source_system="jigsaw",
            pipeline_run_id=pipeline_run_id,
            confidence=confidence,
            tags=["kernel-lane", "observed-state", "lmstudio"],
            lineage=[payload.input_id],
            created_at=generated_at,
        ).model_dump(mode="python"),
    }


def _generation_schema() -> dict[str, Any]:
    return {
        "title": "observed_state_generation_payload",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "kernel_type",
            "status",
            "judgment",
            "confidence",
            "reasons",
        ],
        "properties": {
            "kernel_type": {"type": "string", "enum": ["observed_state"]},
            "status": {"type": "string", "enum": ["success"]},
            "judgment": {
                "type": "string",
                "enum": [
                    "observed_state_clear",
                    "observed_state_partial",
                    "observed_state_sparse",
                ],
            },
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "reasons": {
                "type": "array",
                "minItems": 1,
                "items": {"type": "string", "minLength": 1},
            },
        },
    }


def _prompts(
    payload: KernelInputV1,
    shell: dict[str, Any],
    *,
    prompt_config: dict[str, Any] | None = None,
) -> tuple[str, str]:
    prompt_config = prompt_config or {}
    minimum_expected = int(payload.context.get("minimum_expected_observations", 3))
    observed_count = len(payload.content.observed_items)
    evidence_records = [
        {
            "evidence_id": record.evidence_id,
            "kind": record.kind,
            "text": record.text,
            "confidence": record.confidence,
        }
        for record in payload.evidence
    ]
    confidence_guidance = [
        "Confidence measures support for the chosen observed_state judgment, not perfection of the whole case.",
        "Do not use 0.0 unless the judgment is effectively unsupported by the evidence.",
        "If you choose observed_state_partial and the observations are usable, confidence should normally be above 0.0.",
        "For this case shape, observed_state_partial will usually imply confidence around 0.55 to 0.7 unless the evidence is nearly absent or deeply unreliable.",
        "If three observations are present, the minimum expected observations is four, and the evidence records are real and moderately confident, do not default to 0.4 or below without a clear reason.",
        "A conflicting claim may lower confidence somewhat, but it should not drive confidence near zero when the observed items themselves are still usable.",
    ]
    extra_rules: list[str] = []
    requirements = [
        "Return JSON only.",
        "Write concise reasons focused on observation completeness and clarity.",
        "Do not emit metadata, ids, timestamps, or evidence_used. Those will be added locally.",
        "Set a nonzero confidence when the evidence provides real support for the chosen judgment.",
        "If the judgment is observed_state_partial on this case shape, prefer confidence above 0.5 unless you can justify a lower value from near-absent or very weak evidence.",
    ]
    if prompt_config.get("complete_coverage_bias"):
        confidence_guidance.append(
            "If the minimum expected observations are present, treat the observed picture as strong on coverage grounds unless the evidence itself is unclear or missing."
        )
        extra_rules.append("Do not downgrade from observed_state_clear merely because one observed item has a false value if that value is still clearly evidenced.")
    if prompt_config.get("prefer_clear_on_complete_coverage"):
        requirements.append(
            "If observed_count meets or exceeds the minimum expected observations and the evidence is direct, prefer observed_state_clear unless the observations themselves are ambiguous."
        )
    if "confidence_floor_clear" in prompt_config:
        requirements.append(
            f"If you choose observed_state_clear for this profile, keep confidence at or above {float(prompt_config['confidence_floor_clear']):.2f} unless the evidence is directly unreliable."
        )

    user_payload = {
        "task": "Emit one kernel_output payload for observed_state only.",
        "rules": {
            "evaluate_only": "observation coverage and clarity",
            "do_not_do": [
                "expected-state reasoning",
                "contradiction reasoning",
                "consequence reasoning",
            ],
            "profile_bias": extra_rules,
            "judgment_thresholds": {
                "observed_state_clear": "observed_count >= minimum_expected_observations",
                "observed_state_partial": "observed_count >= max(1, minimum_expected_observations - 1) and not clear",
                "observed_state_sparse": "otherwise",
            },
            "confidence_scale": {
                "0.0": "no meaningful support for the stated judgment",
                "0.25": "weak but real support",
                "0.5": "partial support",
                "0.75": "strong support",
                "1.0": "near-complete support",
            },
            "confidence_guidance": confidence_guidance,
        },
        "input_summary": {
            "title": payload.content.title,
            "summary": payload.content.summary,
            "observed_count": observed_count,
            "minimum_expected_observations": minimum_expected,
            "observed_items": payload.content.observed_items,
            "evidence": evidence_records,
        },
        "generation_target": {
            "kernel_type": "observed_state",
            "status": "success",
            "allowed_judgments": [
                "observed_state_clear",
                "observed_state_partial",
                "observed_state_sparse",
            ],
        },
        "normalization_context": {
            "full_kernel_output_shell": shell,
            "allowed_evidence_ids": shell["evidence_used"],
        },
        "requirements": requirements,
    }
    user_prompt = (
        "You are the observed_state kernel inside Jigsaw.\n"
        "Return one strict kernel_output JSON object and nothing else.\n\n"
        f"{json.dumps(user_payload, indent=2)}"
    )
    return "", user_prompt


def _normalize_generated_payload(
    generated_payload: dict[str, Any],
    shell: dict[str, Any],
) -> dict[str, Any]:
    normalized = dict(shell)
    normalized["kernel_type"] = generated_payload["kernel_type"]
    normalized["status"] = generated_payload["status"]
    normalized["judgment"] = generated_payload["judgment"]
    normalized["confidence"] = generated_payload["confidence"]
    normalized["reasons"] = generated_payload["reasons"]
    normalized["evidence_used"] = shell["evidence_used"]
    normalized["metadata"]["confidence"] = generated_payload["confidence"]
    return normalized


def run_lmstudio_observed_state(
    payload: KernelInputV1,
    *,
    pipeline_run_id: str,
    generated_at: str,
    max_retries: int = 1,
    client: LMStudioClient | None = None,
    prompt_config: dict[str, Any] | None = None,
) -> LMObservedStateRun:
    client = client or LMStudioClient()
    shell = _build_output_shell(payload, pipeline_run_id=pipeline_run_id, generated_at=generated_at)
    schema = _generation_schema()
    system_prompt, user_prompt = _prompts(payload, shell, prompt_config=prompt_config)

    last_error: Exception | None = None
    raw_response: dict[str, Any] | None = None
    generated_payload: dict[str, Any] | None = None
    model_name = ""
    start = time.perf_counter()
    for attempt in range(max_retries + 1):
        try:
            result = client.create_structured_chat_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_schema=schema,
                temperature=0.0,
            )
            raw_response = result.raw_response
            model_name = result.model
            generated_payload = result.parsed_content
            payload_dict = _normalize_generated_payload(generated_payload, shell)
            validated = validate_kernel_output_v1(payload_dict)
            elapsed = round(time.perf_counter() - start, 4)
            return LMObservedStateRun(
                validated_output=validated,
                raw_model_output=raw_response,
                generated_payload=generated_payload,
                model_name=model_name,
                retries_used=attempt,
                elapsed_seconds=elapsed,
            )
        except (LMStudioError, Exception) as exc:
            last_error = exc
            if attempt >= max_retries:
                break

    elapsed = round(time.perf_counter() - start, 4)
    message = f"LM Studio observed_state failed after {max_retries + 1} attempt(s) in {elapsed:.4f}s."
    if last_error is not None:
        raise RuntimeError(message) from last_error
    raise RuntimeError(message)
