"""Small fail-closed sanitizer for PP&D action journal events.

The journal is intended to record high-level automation actions without
capturing secrets, browser state, raw documents, or authentication data.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


ALLOWED_EVENT_TYPES = frozenset(
    {
        "crawl_planned",
        "crawl_skipped",
        "document_discovered",
        "document_normalized",
        "validation_passed",
        "validation_failed",
        "manual_review_required",
    }
)

REQUIRED_FIELDS = frozenset({"event_type", "source", "message"})
ALLOWED_FIELDS = frozenset(
    {
        "event_type",
        "source",
        "message",
        "timestamp",
        "url",
        "document_id",
        "metadata",
    }
)

SENSITIVE_FIELD_NAMES = frozenset(
    {
        "authorization",
        "auth",
        "auth_state",
        "bearer",
        "captcha",
        "cookie",
        "cookies",
        "credential",
        "credentials",
        "csrf",
        "devhub_session",
        "mfa",
        "password",
        "payment",
        "private_key",
        "raw_crawl_output",
        "secret",
        "session",
        "session_file",
        "token",
        "trace",
        "upload",
    }
)

MAX_STRING_LENGTH = 2_000
MAX_METADATA_ITEMS = 25


@dataclass(frozen=True)
class ActionJournalValidationError(ValueError):
    """Raised when an action journal event is not safe to record."""

    reason: str

    def __str__(self) -> str:
        return self.reason


def sanitize_action_journal_event(event: Mapping[str, Any]) -> dict[str, Any]:
    """Return a sanitized journal event or raise on unsafe input.

    Handling is intentionally fail-closed: unknown event types, unknown top-level
    fields, sensitive field names at any depth, non-primitive metadata values,
    and oversized strings are rejected instead of silently retained.
    """

    if not isinstance(event, Mapping):
        raise ActionJournalValidationError("journal event must be a mapping")

    keys = set(event.keys())
    missing = REQUIRED_FIELDS - keys
    if missing:
        raise ActionJournalValidationError("journal event missing required field")

    unknown = keys - ALLOWED_FIELDS
    if unknown:
        raise ActionJournalValidationError("journal event contains unknown field")

    _reject_sensitive_keys(event)

    event_type = _clean_string(event["event_type"], "event_type")
    if event_type not in ALLOWED_EVENT_TYPES:
        raise ActionJournalValidationError("journal event_type is not allowed")

    sanitized: dict[str, Any] = {
        "event_type": event_type,
        "source": _clean_string(event["source"], "source"),
        "message": _clean_string(event["message"], "message"),
    }

    for optional_key in ("timestamp", "url", "document_id"):
        if optional_key in event and event[optional_key] is not None:
            sanitized[optional_key] = _clean_string(event[optional_key], optional_key)

    if "metadata" in event and event["metadata"] is not None:
        sanitized["metadata"] = _clean_metadata(event["metadata"])

    return sanitized


def _clean_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise ActionJournalValidationError(f"{field_name} must be a string")

    cleaned = value.strip()
    if not cleaned:
        raise ActionJournalValidationError(f"{field_name} must not be empty")
    if len(cleaned) > MAX_STRING_LENGTH:
        raise ActionJournalValidationError(f"{field_name} is too long")
    return cleaned


def _clean_metadata(value: Any) -> dict[str, str | int | float | bool | None]:
    if not isinstance(value, Mapping):
        raise ActionJournalValidationError("metadata must be a mapping")
    if len(value) > MAX_METADATA_ITEMS:
        raise ActionJournalValidationError("metadata has too many entries")

    cleaned: dict[str, str | int | float | bool | None] = {}
    for raw_key, raw_value in value.items():
        key = _clean_string(raw_key, "metadata key")
        normalized_key = _normalize_key(key)
        if normalized_key in SENSITIVE_FIELD_NAMES:
            raise ActionJournalValidationError("metadata contains sensitive field")
        if isinstance(raw_value, str):
            cleaned[key] = _clean_string(raw_value, key)
        elif isinstance(raw_value, bool) or raw_value is None:
            cleaned[key] = raw_value
        elif isinstance(raw_value, (int, float)) and not isinstance(raw_value, bool):
            cleaned[key] = raw_value
        else:
            raise ActionJournalValidationError("metadata values must be primitive")
    return cleaned


def _reject_sensitive_keys(value: Any) -> None:
    if isinstance(value, Mapping):
        for raw_key, raw_value in value.items():
            if isinstance(raw_key, str) and _normalize_key(raw_key) in SENSITIVE_FIELD_NAMES:
                raise ActionJournalValidationError("journal event contains sensitive field")
            _reject_sensitive_keys(raw_value)
    elif isinstance(value, list):
        for item in value:
            _reject_sensitive_keys(item)


def _normalize_key(value: str) -> str:
    return value.strip().lower().replace("-", "_")
