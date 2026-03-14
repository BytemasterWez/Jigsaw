from __future__ import annotations

from .models import JudgmentRequestV1


def judgment_request_to_arbiter_preview(request: JudgmentRequestV1) -> dict:
    """
    Thin preview adapter showing how the Jigsaw request can be shaped
    into a downstream Arbiter-oriented input without changing the core request.
    """
    return {
        "candidate_id": request.artifact_id,
        "domain": request.context.analysis_profile,
        "candidate_type": request.subject.type,
        "summary": request.subject.title,
        "evidence": {
            "source_count": len(request.chunks),
            "freshness_days": 0,
            "fit_score": None,
        },
        "context": {
            "source_system": request.context.source_system,
            "source_type": request.context.source_type,
            "jigsaw_request_id": request.request_id,
        },
    }

