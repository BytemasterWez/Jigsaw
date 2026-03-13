from __future__ import annotations

import importlib.util
import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable
from urllib import error, request

from .contracts import ArbiterAdapter, MemoryAdapter
from .demo_data import DEMO_MEMORY
from .envelope import ArbiterDecision, CandidateItem, MemoryCase, MessageEnvelope, utc_now
from .mappings import (
    arbiter_response_to_decision,
    build_candidate_query,
    envelope_to_arbiter_request,
    envelope_to_gc_trace_metadata,
    envelope_to_gc_trace_text,
    memory_cases_from_gc_search_results,
    memory_cases_from_gc_sqlite_rows,
)


def sibling_gc_sqlite_path() -> Path:
    """Local-dev shortcut only. This is not the canonical integration contract."""
    return Path(__file__).resolve().parents[2] / "Garbage collector" / "backend" / "garbage_collector.db"


def sibling_arbiter_repo_path() -> Path:
    """Local-dev shortcut only. This is not the canonical integration contract."""
    return Path(__file__).resolve().parents[2] / "arbiter-public"


@dataclass
class DemoMemoryAdapter(MemoryAdapter):
    cases: list[MemoryCase] = field(default_factory=lambda: list(DEMO_MEMORY))
    stored_envelopes: list[dict[str, Any]] = field(default_factory=list)

    def retrieve_similar_cases(self, candidate: CandidateItem, limit: int = 3) -> list[MemoryCase]:
        if limit <= 0:
            return []

        title = candidate.title.lower()
        scored: list[tuple[float, MemoryCase]] = []
        for case in self.cases:
            score = case.similarity
            if "health" in title and "healthcare" in case.summary.lower():
                score += 0.05
            if "public sector" in title and "public sector" in case.summary.lower():
                score += 0.1
            if "consulting" in title and "consulting" in case.summary.lower():
                score += 0.1
            scored.append((score, case))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [case for _, case in scored[:limit]]

    def persist_trace(self, envelope: MessageEnvelope) -> None:
        self.stored_envelopes.append(envelope.to_dict())


@dataclass
class DemoArbiterAdapter(ArbiterAdapter):
    def decide(self, envelope: MessageEnvelope) -> ArbiterDecision:
        fit = envelope.scores.get("fit", 0.0)
        confidence = envelope.scores.get("confidence", 0.0)
        evidence_count = len(envelope.evidence)
        downside = envelope.consequences.get("downside", "medium")

        if evidence_count < 4 or confidence < 0.55:
            return ArbiterDecision(
                decision="reject",
                confidence=0.7,
                reason="Insufficient evidence or confidence for action.",
                required_follow_up=["Collect more evidence."],
                checked_at=utc_now(),
            )

        if downside == "high" and fit >= 0.7:
            return ArbiterDecision(
                decision="escalate",
                confidence=0.83,
                reason="Potential upside exists but risk requires human review.",
                required_follow_up=["Legal/compliance review."],
                checked_at=utc_now(),
            )

        if fit >= 0.72 and confidence >= 0.75:
            return ArbiterDecision(
                decision="approve",
                confidence=0.88,
                reason="Evidence, provenance, and confidence satisfy action threshold.",
                required_follow_up=[],
                checked_at=utc_now(),
            )

        if fit >= 0.5:
            return ArbiterDecision(
                decision="watchlist",
                confidence=0.76,
                reason="Candidate is promising but not yet strong enough for action.",
                required_follow_up=["Monitor for stronger sponsor, scope, or budget signal."],
                checked_at=utc_now(),
            )

        return ArbiterDecision(
            decision="reject",
            confidence=0.82,
            reason="Low fit relative to current triage thresholds.",
            required_follow_up=[],
            checked_at=utc_now(),
        )


@dataclass
class RealMemoryAdapter(MemoryAdapter):
    gc_base_url: str | None = None
    gc_sqlite_path: Path | None = None
    timeout_seconds: int = 10

    def retrieve_similar_cases(self, candidate: CandidateItem, limit: int = 3) -> list[MemoryCase]:
        if limit <= 0:
            return []

        if self.gc_base_url:
            try:
                return self._retrieve_via_http(candidate, limit)
            except Exception:
                if self.gc_sqlite_path is None:
                    raise

        if self.gc_sqlite_path:
            return self._retrieve_via_sqlite(candidate, limit)

        raise RuntimeError("RealMemoryAdapter requires either gc_base_url or gc_sqlite_path.")

    def persist_trace(self, envelope: MessageEnvelope) -> None:
        if self.gc_sqlite_path:
            self._persist_via_sqlite(envelope)
            return

        if self.gc_base_url:
            self._persist_via_http(envelope)
            return

        raise RuntimeError("RealMemoryAdapter requires either gc_base_url or gc_sqlite_path.")

    def _retrieve_via_http(self, candidate: CandidateItem, limit: int) -> list[MemoryCase]:
        payload = json.dumps({"query": build_candidate_query(candidate), "limit": min(20, max(limit * 3, 6))}).encode(
            "utf-8"
        )
        response = self._http_request("/api/retrieval/search", payload)
        results = json.loads(response.decode("utf-8"))
        return memory_cases_from_gc_search_results(results, limit)

    def _retrieve_via_sqlite(self, candidate: CandidateItem, limit: int) -> list[MemoryCase]:
        path = Path(self.gc_sqlite_path)
        if not path.exists():
            raise FileNotFoundError(f"Garbage Collector sqlite database not found: {path}")

        query_tokens = _tokenize(build_candidate_query(candidate))
        rows: list[dict[str, Any]] = []

        with sqlite3.connect(path) as connection:
            connection.row_factory = sqlite3.Row
            raw_rows = connection.execute(
                """
                select id, item_type, source_url, source_filename, title, content
                from items
                where coalesce(item_type, '') <> 'jigsaw_trace'
                order by updated_at desc
                limit 200
                """
            ).fetchall()

        for row in raw_rows:
            haystack = f"{row['title']} {row['content']}".lower()
            overlap = len([token for token in query_tokens if token in haystack])
            if overlap == 0:
                continue

            score = overlap / max(len(query_tokens), 1)
            rows.append(
                {
                    "id": row["id"],
                    "item_type": row["item_type"],
                    "source_url": row["source_url"],
                    "source_filename": row["source_filename"],
                    "title": row["title"],
                    "summary": row["content"][:280],
                    "score": score,
                }
            )

        return memory_cases_from_gc_sqlite_rows(rows, limit)

    def _persist_via_http(self, envelope: MessageEnvelope) -> None:
        payload = json.dumps({"content": envelope_to_gc_trace_text(envelope)}).encode("utf-8")
        self._http_request("/api/items", payload, method="POST")

    def _persist_via_sqlite(self, envelope: MessageEnvelope) -> None:
        path = Path(self.gc_sqlite_path)
        if not path.exists():
            raise FileNotFoundError(f"Garbage Collector sqlite database not found: {path}")

        metadata = envelope_to_gc_trace_metadata(envelope)
        entities = {"people": [], "organizations": [], "places": [], "dates": []}
        title = f"Jigsaw trace: {envelope.candidate.title[:60]}"
        content = envelope_to_gc_trace_text(envelope)
        now = utc_now()

        with sqlite3.connect(path) as connection:
            connection.execute(
                """
                insert into items (
                    item_type,
                    source_url,
                    source_filename,
                    stored_file_path,
                    metadata_json,
                    entities_json,
                    title,
                    content,
                    created_at,
                    updated_at
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "jigsaw_trace",
                    None,
                    None,
                    None,
                    json.dumps(metadata, ensure_ascii=True, sort_keys=True),
                    json.dumps(entities, ensure_ascii=True, sort_keys=True),
                    title,
                    content,
                    now,
                    now,
                ),
            )
            connection.commit()

    def _http_request(self, path: str, payload: bytes | None = None, method: str = "POST") -> bytes:
        base = self.gc_base_url.rstrip("/")
        req = request.Request(
            url=f"{base}{path}",
            data=payload,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                return response.read()
        except error.URLError as exc:  # pragma: no cover - network dependent
            raise RuntimeError(f"Garbage Collector request failed: {exc}") from exc


@dataclass
class RealArbiterAdapter(ArbiterAdapter):
    arbiter_repo_path: Path | None = None
    _adjudicate: Callable[[dict[str, Any]], dict[str, Any]] | None = field(default=None, init=False, repr=False)

    def decide(self, envelope: MessageEnvelope) -> ArbiterDecision:
        adjudicate = self._load_adjudicate()
        request_payload = envelope_to_arbiter_request(envelope)
        response_payload = adjudicate(request_payload)
        return arbiter_response_to_decision(response_payload)

    def _load_adjudicate(self) -> Callable[[dict[str, Any]], dict[str, Any]]:
        if self._adjudicate is not None:
            return self._adjudicate

        if self.arbiter_repo_path is None:
            raise RuntimeError("RealArbiterAdapter requires an explicit arbiter_repo_path.")

        repo_path = Path(self.arbiter_repo_path)
        module_path = repo_path / "demo" / "run.py"
        if not module_path.exists():
            raise FileNotFoundError(f"Arbiter demo runner not found: {module_path}")

        spec = importlib.util.spec_from_file_location("arbiter_public_demo_run", module_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Could not load Arbiter module from {module_path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        adjudicate = getattr(module, "adjudicate", None)
        if not callable(adjudicate):
            raise RuntimeError("Arbiter module does not expose a callable 'adjudicate'.")

        self._adjudicate = adjudicate
        return adjudicate


def _tokenize(text: str) -> list[str]:
    seen: dict[str, None] = {}
    for raw in text.lower().replace("/", " ").replace("-", " ").split():
        token = raw.strip(".,:;()[]{}!?\"'")
        if len(token) < 3:
            continue
        seen.setdefault(token, None)
    return list(seen.keys())
