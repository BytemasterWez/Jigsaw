from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Iterable


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def make_id(prefix: str, *parts: str) -> str:
    normalized = "-".join(part for part in parts if part)
    return f"{prefix}:{normalized}" if normalized else prefix


def estimate_tokens(text: str) -> int:
    return max(1, len(text.split()))


def sha256_text(parts: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(part.encode("utf-8"))
    return digest.hexdigest()

