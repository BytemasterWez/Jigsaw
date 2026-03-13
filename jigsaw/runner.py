from __future__ import annotations

import json
import os
from pathlib import Path

from .adapters import (
    DemoArbiterAdapter,
    DemoMemoryAdapter,
    RealArbiterAdapter,
    RealMemoryAdapter,
    sibling_arbiter_repo_path,
    sibling_gc_sqlite_path,
)
from .demo_data import DEMO_CANDIDATES
from .kernels import ExplainKernel, InferConsequenceKernel, RankKernel, RetrieveKernel, ScoreKernel
from .pipeline import JigsawPipeline


def build_pipeline(adapter_mode: str = "demo", audit_path: Path | None = None):
    if adapter_mode == "real":
        use_sibling_discovery = os.getenv("JIGSAW_DEV_SIBLING_DISCOVERY", "").lower() in {"1", "true", "yes"}
        gc_sqlite_env = os.getenv("JIGSAW_GC_SQLITE_PATH")
        gc_sqlite_default = sibling_gc_sqlite_path() if use_sibling_discovery else None
        gc_sqlite_path = (
            Path(gc_sqlite_env)
            if gc_sqlite_env
            else gc_sqlite_default
            if gc_sqlite_default and gc_sqlite_default.exists()
            else None
        )
        arbiter_repo_env = os.getenv("JIGSAW_ARBITER_REPO")
        arbiter_repo_default = sibling_arbiter_repo_path() if use_sibling_discovery else None
        arbiter_repo_path = (
            Path(arbiter_repo_env)
            if arbiter_repo_env
            else arbiter_repo_default
            if arbiter_repo_default and arbiter_repo_default.exists()
            else None
        )
        memory = RealMemoryAdapter(
            gc_base_url=os.getenv("JIGSAW_GC_BASE_URL"),
            gc_sqlite_path=gc_sqlite_path,
        )
        arbiter = RealArbiterAdapter(arbiter_repo_path=arbiter_repo_path)
    else:
        memory = DemoMemoryAdapter()
        arbiter = DemoArbiterAdapter()

    kernels = [
        RetrieveKernel(),
        ScoreKernel(),
        InferConsequenceKernel(),
        RankKernel(),
        ExplainKernel(),
    ]
    return JigsawPipeline(memory=memory, arbiter=arbiter, kernels=kernels, audit_path=audit_path), memory


def main() -> None:
    adapter_mode = os.getenv("JIGSAW_ADAPTER_MODE", "demo").lower()
    audit_path = Path("artifacts") / "audit_log.jsonl"
    pipeline, memory = build_pipeline(adapter_mode=adapter_mode, audit_path=audit_path)

    for candidate in DEMO_CANDIDATES:
        result = pipeline.evaluate(candidate)
        print(
            json.dumps(
                {
                    "adapter_mode": adapter_mode,
                    "candidate_id": candidate.candidate_id,
                    "title": candidate.title,
                    "decision": result.envelope.arbiter_decision.decision,
                    "priority": result.envelope.priority.level if result.envelope.priority else None,
                    "fit": result.envelope.scores.get("fit"),
                    "confidence": result.envelope.scores.get("confidence"),
                    "action_status": result.envelope.action.status if result.envelope.action else None,
                    "trace_steps": [item.step for item in result.envelope.trace],
                }
            )
        )

    persisted_traces = len(getattr(memory, "stored_envelopes", []))
    print(
        json.dumps(
            {
                "adapter_mode": adapter_mode,
                "persisted_traces": persisted_traces,
                "audit_path": str(audit_path),
            }
        )
    )


if __name__ == "__main__":
    main()
