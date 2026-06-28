"""Deterministic fixture-first source recrawl eligibility.

This module intentionally works only from committed metadata fixtures or caller-provided
records. It performs no network access and never persists raw response bodies.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
import json

PUBLIC_SOURCE_TYPES = {
    "public_html",
    "public_pdf",
    "public_form",
    "devhub_public",
    "external_reference",
}

FREQUENCY_DAYS = {
    "daily": 1,
    "every_few_days": 3,
    "weekly": 7,
    "monthly": 30,
    "quarterly": 90,
}

ALLOWED_POLICY_VALUES = {"allowed", "allow", "public_allowlist", "listed"}
DISALLOWED_POLICY_VALUES = {"blocked", "disallowed", "deny", "outside_allowlist"}


@dataclass(frozen=True)
class RecrawlCandidate:
    """Public metadata needed to schedule a recrawl candidate."""

    source_id: str
    canonical_url: str
    source_type: str
    crawl_frequency: str
    last_seen_at: str | None
    freshness_status: str
    prior_content_hash: str | None
    eligibility_reason: str
    no_raw_body_persisted: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "canonical_url": self.canonical_url,
            "source_type": self.source_type,
            "crawl_frequency": self.crawl_frequency,
            "last_seen_at": self.last_seen_at,
            "freshness_status": self.freshness_status,
            "prior_content_hash": self.prior_content_hash,
            "eligibility_reason": self.eligibility_reason,
            "no_raw_body_persisted": self.no_raw_body_persisted,
        }


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_fixture_bundle(fixture_dir: Path) -> dict[str, Any]:
    """Load committed recrawl eligibility fixtures from a test-local directory."""

    return {
        "sources": load_json(fixture_dir / "source_registry.json"),
        "archive_manifests": load_json(fixture_dir / "archive_manifests.json"),
        "deferred_sources": load_json(fixture_dir / "deferred_sources.json"),
    }


def select_recrawl_candidates(
    sources: Iterable[dict[str, Any]],
    archive_manifests: Iterable[dict[str, Any]],
    deferred_sources: Iterable[dict[str, Any]],
    *,
    as_of: datetime,
) -> list[dict[str, Any]]:
    """Return a stable public recrawl candidate list from metadata only.

    Eligibility requires a public source type, an allowlisted URL, an allowed robots
    decision, and no active intentional deferral. A source becomes a candidate when
    it is stale by freshness metadata, is older than its crawl frequency, or has no
    prior archive hash.
    """

    if as_of.tzinfo is None:
        as_of = as_of.replace(tzinfo=timezone.utc)

    deferred_ids = _active_deferred_source_ids(deferred_sources, as_of)
    hashes_by_source = _latest_hash_by_source(archive_manifests)
    candidates: list[RecrawlCandidate] = []

    for source in sources:
        source_id = _required_str(source, "source_id")
        source_type = str(source.get("source_type", ""))
        if source_type not in PUBLIC_SOURCE_TYPES:
            continue
        if source_id in deferred_ids:
            continue
        if not _is_allowed(source.get("allowlist_policy")):
            continue
        if not _is_allowed(source.get("robots_policy")):
            continue

        prior_hash = hashes_by_source.get(source_id)
        reason = _eligibility_reason(source, prior_hash, as_of)
        if reason is None:
            continue

        candidates.append(
            RecrawlCandidate(
                source_id=source_id,
                canonical_url=_required_str(source, "canonical_url"),
                source_type=source_type,
                crawl_frequency=str(source.get("crawl_frequency", "unknown")),
                last_seen_at=_optional_str(source.get("last_seen_at")),
                freshness_status=str(source.get("freshness_status", "unknown")),
                prior_content_hash=prior_hash,
                eligibility_reason=reason,
            )
        )

    return [candidate.as_dict() for candidate in sorted(candidates, key=lambda item: item.source_id)]


def _active_deferred_source_ids(records: Iterable[dict[str, Any]], as_of: datetime) -> set[str]:
    active: set[str] = set()
    for record in records:
        source_id = record.get("source_id")
        if not isinstance(source_id, str) or not source_id:
            continue
        until = record.get("defer_until")
        if until is None or _parse_datetime(str(until)) > as_of:
            active.add(source_id)
    return active


def _latest_hash_by_source(manifests: Iterable[dict[str, Any]]) -> dict[str, str]:
    latest: dict[str, tuple[datetime, str]] = {}
    for manifest in manifests:
        source_id = manifest.get("source_id")
        content_hash = manifest.get("content_hash")
        if not isinstance(source_id, str) or not isinstance(content_hash, str):
            continue
        captured_at = _parse_datetime(str(manifest.get("capture_finished_at") or manifest.get("capture_started_at") or "1970-01-01T00:00:00Z"))
        previous = latest.get(source_id)
        if previous is None or captured_at >= previous[0]:
            latest[source_id] = (captured_at, content_hash)
    return {source_id: content_hash for source_id, (_captured_at, content_hash) in latest.items()}


def _eligibility_reason(source: dict[str, Any], prior_hash: str | None, as_of: datetime) -> str | None:
    freshness_status = str(source.get("freshness_status", "unknown"))
    if freshness_status in {"stale", "unknown", "missing"}:
        return f"freshness_status:{freshness_status}"
    if prior_hash is None:
        return "missing_prior_archive_hash"

    frequency = str(source.get("crawl_frequency", ""))
    frequency_days = FREQUENCY_DAYS.get(frequency)
    last_seen_at = source.get("last_seen_at")
    if frequency_days is not None and isinstance(last_seen_at, str) and last_seen_at:
        age_days = (as_of - _parse_datetime(last_seen_at)).days
        if age_days >= frequency_days:
            return f"crawl_frequency_due:{frequency}"

    return None


def _is_allowed(value: Any) -> bool:
    policy = str(value or "").strip().lower()
    if policy in DISALLOWED_POLICY_VALUES:
        return False
    return policy in ALLOWED_POLICY_VALUES


def _parse_datetime(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _required_str(record: dict[str, Any], field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value:
        raise ValueError(f"record is missing required string field: {field}")
    return value


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("optional timestamp value must be a string or null")
    return value
