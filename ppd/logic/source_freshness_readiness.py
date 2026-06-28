"""Deterministic source-freshness readiness checks for PP&D guardrails.

The helper intentionally consumes plain registry/change-monitor dictionaries so tests can
use synthetic records and avoid any live crawl, authenticated session, or raw source data.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable, Mapping


def evaluate_source_freshness_readiness(
    *,
    registry_records: Iterable[Mapping[str, Any]],
    change_monitor_records: Iterable[Mapping[str, Any]],
    required_source_ids: Iterable[str],
    as_of: str | datetime | None = None,
    max_age_days: int = 14,
) -> dict[str, Any]:
    """Return whether official evidence is fresh enough for guardrail readiness.

    Readiness is blocked when any required source is missing from the registry,
    marked stale, older than ``max_age_days``, or has an unresolved hash-change
    monitor record.
    """

    checked_source_ids = _ordered_unique(required_source_ids)
    registry_by_source_id = {
        str(record.get("source_id")): record
        for record in registry_records
        if record.get("source_id") is not None
    }
    now = _parse_datetime(as_of) if as_of is not None else datetime.now(timezone.utc)

    missing_source_ids: list[str] = []
    stale_source_ids: list[str] = []
    hash_changed_source_ids: list[str] = []

    for source_id in checked_source_ids:
        record = registry_by_source_id.get(source_id)
        if record is None:
            missing_source_ids.append(source_id)
            continue
        if _is_registry_record_stale(record, now=now, max_age_days=max_age_days):
            stale_source_ids.append(source_id)

    monitored_required_sources = set(checked_source_ids)
    for record in change_monitor_records:
        source_id = record.get("source_id")
        if source_id is None or str(source_id) not in monitored_required_sources:
            continue
        if _is_unresolved_hash_change(record):
            hash_changed_source_ids.append(str(source_id))

    hash_changed_source_ids = _ordered_unique(hash_changed_source_ids)
    blocked_reasons: list[str] = []
    if missing_source_ids:
        blocked_reasons.append("missing_source_evidence")
    if stale_source_ids:
        blocked_reasons.append("stale_source_evidence")
    if hash_changed_source_ids:
        blocked_reasons.append("hash_changed_source_evidence")

    return {
        "ready": not blocked_reasons,
        "checked_source_ids": checked_source_ids,
        "blocked_reasons": blocked_reasons,
        "missing_source_ids": missing_source_ids,
        "stale_source_ids": stale_source_ids,
        "hash_changed_source_ids": hash_changed_source_ids,
    }


def _is_registry_record_stale(
    record: Mapping[str, Any], *, now: datetime, max_age_days: int
) -> bool:
    freshness_status = str(record.get("freshness_status", "")).lower()
    if freshness_status in {"stale", "missing", "expired", "unknown"}:
        return True

    last_seen_at = record.get("last_seen_at")
    if not last_seen_at:
        return True

    observed_at = _parse_datetime(last_seen_at)
    age_seconds = (now - observed_at).total_seconds()
    return age_seconds > max_age_days * 24 * 60 * 60


def _is_unresolved_hash_change(record: Mapping[str, Any]) -> bool:
    if str(record.get("resolution_status", "")).lower() in {"accepted", "reviewed", "resolved"}:
        return False

    event_type = str(record.get("event_type", "")).lower()
    if event_type in {"hash_changed", "content_hash_changed", "source_hash_changed"}:
        return True

    previous_hash = record.get("previous_hash")
    current_hash = record.get("current_hash")
    return bool(previous_hash and current_hash and previous_hash != current_hash)


def _parse_datetime(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _ordered_unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        normalized = str(value)
        if normalized not in seen:
            seen.add(normalized)
            ordered.append(normalized)
    return ordered
