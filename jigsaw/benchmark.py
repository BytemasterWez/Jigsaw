from __future__ import annotations

import json
import os
from statistics import mean

from .demo_data import DEMO_CANDIDATES
from .runner import build_pipeline


def baseline_decision(candidate_summary: str) -> str:
    summary = candidate_summary.lower()
    if any(word in summary for word in ["pilot", "automation", "modernization"]):
        return "act"
    return "ignore"


def run_benchmark() -> None:
    adapter_mode = os.getenv("JIGSAW_ADAPTER_MODE", "demo").lower()
    pipeline_without_memory, _ = build_pipeline(adapter_mode=adapter_mode)
    pipeline_with_memory, _ = build_pipeline(adapter_mode=adapter_mode)

    baseline_actions = 0
    gated_actions = 0
    memory_gated_actions = 0
    gated_fits: list[float] = []
    memory_fits: list[float] = []

    for candidate in DEMO_CANDIDATES:
        if baseline_decision(candidate.summary) == "act":
            baseline_actions += 1

        no_memory_result = pipeline_without_memory.evaluate(candidate, memory_limit=0)
        gated_fits.append(no_memory_result.envelope.scores.get("fit", 0.0))
        if no_memory_result.action_executed:
            gated_actions += 1

        memory_result = pipeline_with_memory.evaluate(candidate, memory_limit=3)
        memory_fits.append(memory_result.envelope.scores.get("fit", 0.0))
        if memory_result.action_executed:
            memory_gated_actions += 1

    report = {
        "baseline": {
            "items": len(DEMO_CANDIDATES),
            "actions_taken": baseline_actions,
            "inspectability": "low",
            "gating": "none",
        },
        "gated_jigsaw": {
            "items": len(DEMO_CANDIDATES),
            "actions_taken": gated_actions,
            "avg_fit": round(mean(gated_fits), 3),
            "audit_trail": "full",
            "adapter_mode": adapter_mode,
        },
        "memory_informed_gated_jigsaw": {
            "items": len(DEMO_CANDIDATES),
            "actions_taken": memory_gated_actions,
            "avg_fit": round(mean(memory_fits), 3),
            "audit_trail": "full",
            "adapter_mode": adapter_mode,
        },
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    run_benchmark()
