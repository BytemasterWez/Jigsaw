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
class LMExpectedStateRun:
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
    output_id = make_id("kernel_output", payload.input_id, "expected_state")
    return {
        "contract": "kernel_output",
        "version": "v1",
        "output_id": output_id,
        "kernel_type": "expected_state",
        "input_id": payload.input_id,
        "status": "success",
        "judgment": "expected_state_partial",
        "confidence": confidence,
        "reasons": ["Placeholder; must be replaced by the model."],
        "evidence_used": [record.evidence_id for record in payload.evidence],
        "metadata": build_metadata(
            output_id,
            source_system="jigsaw",
            pipeline_run_id=pipeline_run_id,
            confidence=confidence,
            tags=["kernel-lane", "expected-state", "lmstudio"],
            lineage=[payload.input_id],
            created_at=generated_at,
        ).model_dump(mode="python"),
    }


def _generation_schema() -> dict[str, Any]:
    return {
        "title": "expected_state_generation_payload",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "kernel_type",
            "status",
            "expected_slots_present",
            "aligned_slots",
            "misaligned_slots",
            "missing_slots",
            "fit_reason",
            "missing_reason",
        ],
        "properties": {
            "kernel_type": {"type": "string", "enum": ["expected_state"]},
            "status": {"type": "string", "enum": ["success"]},
            "expected_slots_present": {"type": "integer", "minimum": 0},
            "aligned_slots": {
                "type": "array",
                "items": {"type": "string", "minLength": 1},
            },
            "misaligned_slots": {
                "type": "array",
                "items": {"type": "string", "minLength": 1},
            },
            "missing_slots": {
                "type": "array",
                "items": {"type": "string", "minLength": 1},
            },
            "alignment_ratio": {"type": "number", "minimum": 0, "maximum": 1},
            "fit_reason": {"type": "string", "minLength": 1},
            "missing_reason": {"type": "string", "minLength": 1},
            "notes": {
                "type": "array",
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
    observed_by_name = {
        item.get("name"): item.get("value")
        for item in payload.content.observed_items
        if item.get("name")
    }
    expected_pairs = []
    for expected in payload.content.expected_items:
        name = expected.get("name")
        expected_pairs.append(
            {
                "name": name,
                "expected_value": expected.get("target_value"),
                "observed_value": observed_by_name.get(name),
                "aligned": observed_by_name.get(name) == expected.get("target_value"),
            }
        )

    ratio = 1.0 if not expected_pairs else sum(1 for item in expected_pairs if item["aligned"]) / len(expected_pairs)
    confidence_guidance = [
        "Report expected-fit facts, not the final expected_state class.",
        "Do not collapse all mixed-fit cases into one narrative middle bucket.",
        "A case with 3 of 4 slots aligned should still be reported as mostly aligned even if one slot is misaligned.",
        "A case with only 1 of 4 slots aligned should be reported as mostly misaligned, not merely mixed.",
    ]
    requirements = [
        "Return JSON only.",
        "Write concise reasons focused on which expected slots align, which do not, and which are missing.",
        "Do not emit metadata, ids, timestamps, or evidence_used. Those will be added locally.",
        "Do not emit the final expected_state class. Local logic will determine the final class.",
        "Do not treat any mixture of aligned and misaligned slots as automatically 'partial'.",
    ]
    profile_bias: list[str] = []
    if prompt_config.get("prefer_aligned_at_threshold"):
        profile_bias.append(
            "If three quarters or more of the expected slots align, report that the fit is mostly aligned even if one slot remains misaligned."
        )

    user_payload = {
        "task": "Report structured expected-fit facts for expected_state only.",
        "rules": {
            "evaluate_only": "alignment between observed values and expected targets",
            "do_not_do": [
                "observed-state coverage judgment",
                "contradiction reasoning",
                "consequence reasoning",
            ],
            "profile_bias": profile_bias,
            "reporting_rubric": {
                "core_question": "Which expected slots align, which do not, and which are missing from the observed picture?",
                "important_distinction": [
                    "Fit reporting is not the same as final class assignment.",
                    "If three quarters of slots align, report that alignment clearly rather than flattening it into a generic mixed-fit description.",
                    "If only one quarter of slots aligns, report that the fit is mostly misaligned rather than generic partial fit.",
                    "Missing slots should be reported separately from directly misaligned slots.",
                ],
                "target_thresholds": {
                    "mostly_aligned": "alignment_ratio >= 0.75",
                    "mixed_fit": "alignment_ratio >= 0.40 and < 0.75",
                    "mostly_misaligned": "alignment_ratio < 0.40",
                },
            },
            "confidence_guidance": confidence_guidance,
        },
        "input_summary": {
            "title": payload.content.title,
            "summary": payload.content.summary,
            "alignment_ratio": round(ratio, 4),
            "expected_pairs": expected_pairs,
            "evidence": [
                {
                    "evidence_id": record.evidence_id,
                    "kind": record.kind,
                    "text": record.text,
                    "confidence": record.confidence,
                }
                for record in payload.evidence
            ],
        },
        "generation_target": {
            "kernel_type": "expected_state",
            "status": "success",
            "required_fields": [
                "expected_slots_present",
                "aligned_slots",
                "misaligned_slots",
                "missing_slots",
                "fit_reason",
                "missing_reason",
            ],
        },
        "normalization_context": {
            "full_kernel_output_shell": shell,
            "allowed_evidence_ids": shell["evidence_used"],
        },
        "requirements": requirements,
    }
    user_prompt = (
        "You are the expected_state kernel inside Jigsaw.\n"
        "Return one strict kernel_output JSON object and nothing else.\n\n"
        f"{json.dumps(user_payload, indent=2)}"
    )
    return "", user_prompt


def _normalize_generated_payload(generated_payload: dict[str, Any], shell: dict[str, Any]) -> dict[str, Any]:
    expected_slots_present = int(generated_payload["expected_slots_present"])
    aligned_slots = list(generated_payload.get("aligned_slots", []))
    misaligned_slots = list(generated_payload.get("misaligned_slots", []))
    missing_slots = list(generated_payload.get("missing_slots", []))
    fit_reason = generated_payload["fit_reason"]
    missing_reason = generated_payload["missing_reason"]
    notes = list(generated_payload.get("notes", []))

    if expected_slots_present <= 0:
        ratio = 0.0
    else:
        ratio = round(len(aligned_slots) / expected_slots_present, 4)

    if ratio >= 0.75:
        judgment = "expected_state_aligned"
    elif ratio >= 0.40:
        judgment = "expected_state_partial"
    else:
        judgment = "expected_state_misaligned"

    confidence = round(min(0.95, 0.55 + 0.35 * ratio), 4)

    reasons = [fit_reason]
    if misaligned_slots:
        reasons.append(f"Misaligned expected slots: {', '.join(misaligned_slots)}.")
    if missing_slots:
        reasons.append(missing_reason)
    reasons.extend(notes[:1])

    normalized = dict(shell)
    normalized["kernel_type"] = generated_payload["kernel_type"]
    normalized["status"] = generated_payload["status"]
    normalized["judgment"] = judgment
    normalized["confidence"] = confidence
    normalized["reasons"] = reasons
    normalized["evidence_used"] = shell["evidence_used"]
    normalized["metadata"]["confidence"] = confidence
    return normalized


def run_lmstudio_expected_state(
    payload: KernelInputV1,
    *,
    pipeline_run_id: str,
    generated_at: str,
    max_retries: int = 1,
    client: LMStudioClient | None = None,
    prompt_config: dict[str, Any] | None = None,
) -> LMExpectedStateRun:
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
            return LMExpectedStateRun(
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
    message = f"LM Studio expected_state failed after {max_retries + 1} attempt(s) in {elapsed:.4f}s."
    if last_error is not None:
        raise RuntimeError(message) from last_error
    raise RuntimeError(message)
