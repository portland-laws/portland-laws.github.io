"""Redacted fixture-backed synthetic user case store.

The adapter accepts synthetic case facts and document metadata from committed
fixtures only. It normalizes freshness/confidence fields and rejects private or
live-automation artifacts before storing anything in memory.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
import json
import re


class SyntheticUserCaseStoreError(ValueError):
    """Raised when a synthetic user case fixture contains unsafe data."""


@dataclass(frozen=True)
class NormalizedFact:
    key: str
    value: Any
    freshness: str
    confidence: float
    source_document_id: str | None = None


@dataclass(frozen=True)
class DocumentMetadata:
    document_id: str
    title: str
    url: str | None = None
    published_at: str | None = None


@dataclass(frozen=True)
class SyntheticUserCase:
    case_id: str
    facts: tuple[NormalizedFact, ...]
    documents: tuple[DocumentMetadata, ...]


_BLOCKED_KEY_PARTS = (
    "authorization",
    "auth_state",
    "authstate",
    "bearer",
    "card_cvc",
    "card_number",
    "cookie",
    "credentials",
    "credit_card",
    "cvv",
    "har",
    "local_path",
    "password",
    "payment",
    "private_path",
    "raw_private",
    "refresh_token",
    "screenshot",
    "secret",
    "session",
    "ssn",
    "token",
    "trace",
)

_BLOCKED_PATH_RE = re.compile(
    r"(^|[\s\"'])(/Users/|/home/|/var/folders/|/private/|[A-Za-z]:\\\\|~[/\\])"
)

_PAYMENT_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")
_AUTH_RE = re.compile(r"\b(?:Bearer|Basic)\s+[A-Za-z0-9._~+/=-]+", re.IGNORECASE)
_PRIVATE_VALUE_RE = re.compile(
    r"\b(?:password|access_token|refresh_token|api_key|secret|ssn)\b\s*[:=]",
    re.IGNORECASE,
)

_FRESHNESS_ALIASES = {
    "new": "current",
    "fresh": "current",
    "current": "current",
    "recent": "recent",
    "stale": "stale",
    "old": "stale",
    "unknown": "unknown",
    "": "unknown",
}

_CONFIDENCE_ALIASES = {
    "high": 0.9,
    "medium": 0.6,
    "med": 0.6,
    "low": 0.3,
    "unknown": 0.0,
    "": 0.0,
}


class RedactedSyntheticUserCaseStore:
    """In-memory adapter for redacted synthetic user case fixtures."""

    def __init__(self) -> None:
        self._cases: dict[str, SyntheticUserCase] = {}

    def add_case(self, payload: Mapping[str, Any]) -> SyntheticUserCase:
        """Validate, normalize, and store a synthetic case mapping."""
        self._reject_unsafe(payload)
        case = _normalize_case(payload)
        self._cases[case.case_id] = case
        return case

    def load_fixture(self, fixture_path: str | Path) -> SyntheticUserCase:
        """Load a JSON fixture from disk and store the normalized case."""
        path = Path(fixture_path)
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, Mapping):
            raise SyntheticUserCaseStoreError("synthetic case fixture must be a JSON object")
        return self.add_case(data)

    def get_case(self, case_id: str) -> SyntheticUserCase | None:
        return self._cases.get(case_id)

    def list_cases(self) -> tuple[SyntheticUserCase, ...]:
        return tuple(self._cases.values())

    def _reject_unsafe(self, value: Any, path: str = "$.") -> None:
        if isinstance(value, Mapping):
            for key, child in value.items():
                key_text = str(key)
                normalized_key = key_text.lower().replace("-", "_")
                if any(part in normalized_key for part in _BLOCKED_KEY_PARTS):
                    raise SyntheticUserCaseStoreError(f"unsafe private field rejected at {path}{key_text}")
                self._reject_unsafe(child, f"{path}{key_text}.")
            return

        if isinstance(value, list | tuple):
            for index, child in enumerate(value):
                self._reject_unsafe(child, f"{path}[{index}].")
            return

        if isinstance(value, str):
            if _BLOCKED_PATH_RE.search(value):
                raise SyntheticUserCaseStoreError(f"local private path rejected at {path}")
            if _AUTH_RE.search(value):
                raise SyntheticUserCaseStoreError(f"authorization material rejected at {path}")
            if _PAYMENT_RE.search(value):
                raise SyntheticUserCaseStoreError(f"payment detail rejected at {path}")
            if _PRIVATE_VALUE_RE.search(value):
                raise SyntheticUserCaseStoreError(f"raw private value rejected at {path}")


def _normalize_case(payload: Mapping[str, Any]) -> SyntheticUserCase:
    case_id = _required_text(payload, "case_id")
    raw_facts = payload.get("facts", [])
    raw_documents = payload.get("documents", [])

    if not isinstance(raw_facts, list):
        raise SyntheticUserCaseStoreError("facts must be a list")
    if not isinstance(raw_documents, list):
        raise SyntheticUserCaseStoreError("documents must be a list")

    facts = tuple(_normalize_fact(item) for item in raw_facts)
    documents = tuple(_normalize_document(item) for item in raw_documents)
    return SyntheticUserCase(case_id=case_id, facts=facts, documents=documents)


def _normalize_fact(item: Any) -> NormalizedFact:
    if not isinstance(item, Mapping):
        raise SyntheticUserCaseStoreError("each fact must be an object")
    return NormalizedFact(
        key=_required_text(item, "key"),
        value=item.get("value"),
        freshness=_normalize_freshness(item.get("freshness")),
        confidence=_normalize_confidence(item.get("confidence")),
        source_document_id=_optional_text(item.get("source_document_id")),
    )


def _normalize_document(item: Any) -> DocumentMetadata:
    if not isinstance(item, Mapping):
        raise SyntheticUserCaseStoreError("each document must be an object")
    return DocumentMetadata(
        document_id=_required_text(item, "document_id"),
        title=_required_text(item, "title"),
        url=_optional_text(item.get("url")),
        published_at=_normalize_date(item.get("published_at")),
    )


def _required_text(mapping: Mapping[str, Any], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SyntheticUserCaseStoreError(f"{key} must be a non-empty string")
    return value.strip()


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise SyntheticUserCaseStoreError("optional text fields must be strings when present")
    cleaned = value.strip()
    return cleaned or None


def _normalize_freshness(value: Any) -> str:
    if value is None:
        return "unknown"
    if not isinstance(value, str):
        raise SyntheticUserCaseStoreError("freshness must be a string")
    key = value.strip().lower()
    if key not in _FRESHNESS_ALIASES:
        raise SyntheticUserCaseStoreError(f"unsupported freshness value: {value}")
    return _FRESHNESS_ALIASES[key]


def _normalize_confidence(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, bool):
        raise SyntheticUserCaseStoreError("confidence must be numeric or a confidence label")
    if isinstance(value, int | float):
        return max(0.0, min(1.0, float(value)))
    if isinstance(value, str):
        key = value.strip().lower()
        if key in _CONFIDENCE_ALIASES:
            return _CONFIDENCE_ALIASES[key]
        try:
            return max(0.0, min(1.0, float(key)))
        except ValueError as exc:
            raise SyntheticUserCaseStoreError(f"unsupported confidence value: {value}") from exc
    raise SyntheticUserCaseStoreError("confidence must be numeric or a confidence label")


def _normalize_date(value: Any) -> str | None:
    text = _optional_text(value)
    if text is None:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise SyntheticUserCaseStoreError("published_at must be ISO-8601 when present") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).date().isoformat()
