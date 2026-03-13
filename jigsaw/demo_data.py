from __future__ import annotations

from .envelope import CandidateItem, MemoryCase


DEMO_CANDIDATES = [
    CandidateItem(
        candidate_id="opp-001",
        kind="opportunity",
        title="Expansion partnership with regional hospital group",
        source="inbound_email",
        summary="Hospital network requested a pilot for workflow automation across three sites.",
        attributes={
            "budget_band": "high",
            "strategic_fit": "strong",
            "urgency": "this_quarter",
            "risk_flag": "low",
        },
    ),
    CandidateItem(
        candidate_id="opp-002",
        kind="opportunity",
        title="Small ad hoc consulting request",
        source="contact_form",
        summary="One-off low budget request with unclear business sponsor and unclear problem statement.",
        attributes={
            "budget_band": "low",
            "strategic_fit": "weak",
            "urgency": "unknown",
            "risk_flag": "medium",
        },
    ),
    CandidateItem(
        candidate_id="opp-003",
        kind="opportunity",
        title="Public sector data modernization RFI",
        source="partner_referral",
        summary="Potentially strategic public sector RFI with large upside but strict compliance requirements.",
        attributes={
            "budget_band": "high",
            "strategic_fit": "strong",
            "urgency": "next_quarter",
            "risk_flag": "high",
        },
    ),
]


DEMO_MEMORY = [
    MemoryCase(
        case_id="case-100",
        outcome="approved_then_won",
        similarity=0.91,
        summary="Large healthcare automation pilot with strong executive sponsor converted successfully.",
        provenance={"source": "gc_demo", "record_id": "case-100"},
    ),
    MemoryCase(
        case_id="case-101",
        outcome="watchlisted_then_stalled",
        similarity=0.65,
        summary="Small unscoped consulting lead stalled due to no budget and weak sponsor.",
        provenance={"source": "gc_demo", "record_id": "case-101"},
    ),
    MemoryCase(
        case_id="case-102",
        outcome="escalated_for_review",
        similarity=0.73,
        summary="Public sector modernization bid required legal and compliance review before action.",
        provenance={"source": "gc_demo", "record_id": "case-102"},
    ),
]
