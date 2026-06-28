"""Deterministic PP&D source recrawl eligibility helpers.

This module intentionally works from committed source-registry style fixtures. It
answers only the narrow scheduling question needed before a crawl: should this
source be considered eligible for recrawl as of a supplied timestamp?
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
import re
from typing import Any, Mapping


_CITATION_SOURCE_ID_RE = re.compile(r"^ppd:[a-z0-9][a-z0-9._-]*(?::[a-z0-9][a-z0-9._-]*)*$")
_RAW_BODY_KEYS = frozenset({"body", "html", "raw_body", "raw_content", "response_body", "text"})
_FREQUENCY_DAYS = {
    "daily": 1,
    "every_few_days": 3,
    "every-few-days": 3,
    "few_days": 3,
    "weekly": 7,
    "monthly": 30,
}
_MANUAL_FREQUENCIES = frozenset({"manual", "never", "on_demand", "on-demand"})
_POLICY_SKIP_VALUES = frozenset({"disallow", "disallowed", "blocked", "deny", "denied"})


@dataclass(frozen=True)
class RecrawlDecision:
    """A commit-safe recrawl decision for a single source."""

    source_id: str
    citation_source_id: str
    canonical_url: str
    crawl_frequency: str
    eligible: bool
    reason: str
    skip_reason: str | None
    last_seen_at: str | None
    next_recrawl_after: str | None
    no_raw_body_persisted: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_recrawl_decisions(path: str | Path, *, as_of: datetime | str) -> list[RecrawlDecision]:
    """Load a committed source fixture and return deterministic recrawl decisions."""

    fixture_path = Path(path)
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    sources = payload.get("sources", payload) if isinstance(payload, dict) else payload
    if not isinstance(sources, list):
        raise ValueError("source recrawl fixture must contain a list or a {'sources': [...]} object")
    checked_at = _coerce_datetime(as_of)
    return [source_recrawl_decision(source, as_of=checked_at) for source in sources]


def source_recrawl_decision(source: Mapping[str, Any], *, as_of: datetime | str) -> RecrawlDecision:
    """Return the recrawl eligibility decision for one source registry entry."""

    checked_at = _coerce_datetime(as_of)
    _assert_no_raw_body(source)

    source_id = _required_string(source, "source_id")
    if not _CITATION_SOURCE_ID_RE.fullmatch(source_id):
        raise ValueError(f"source_id is not citation-ready: {source_id!r}")

    canonical_url = _required_string(source, "canonical_url")
    crawl_frequency = _normalize_frequency(str(source.get("crawl_frequency", "weekly")))
    skip_reason = _optional_string(source.get("skipped_reason")) or _optional_string(source.get("skip_reason"))
    no_raw_body_persisted = source.get("no_raw_body_persisted", True)
    if no_raw_body_persisted is not True:
        raise ValueError(f"source {source_id} does not guarantee no raw body persistence")

    if skip_reason:
        return _decision(source_id, canonical_url, crawl_frequency, False, skip_reason, skip_reason, None, source)

    policy_reason = _policy_skip_reason(source)
    if policy_reason is not None:
        return _decision(source_id, canonical_url, crawl_frequency, False, policy_reason, policy_reason, None, source)

    if crawl_frequency in _MANUAL_FREQUENCIES:
        return _decision(source_id, canonical_url, crawl_frequency, False, f"recrawl disabled by crawl_frequency:{crawl_frequency}", None, None, source)

    frequency_days = _FREQUENCY_DAYS.get(crawl_frequency)
    if frequency_days is None:
        return _decision(source_id, canonical_url, crawl_frequency, False, f"unsupported crawl_frequency:{crawl_frequency}", None, None, source)

    last_seen_at = _optional_string(source.get("last_seen_at")) or _optional_string(source.get("last_checked_at"))
    if last_seen_at is None:
        return _decision(source_id, canonical_url, crawl_frequency, True, "never_seen", None, None, source)

    last_seen = _coerce_datetime(last_seen_at)
    next_recrawl = last_seen + timedelta(days=frequency_days)
    if checked_at >= next_recrawl:
        return _decision(source_id, canonical_url, crawl_frequency, True, f"stale:{crawl_frequency}", None, next_recrawl, source)
    return _decision(source_id, canonical_url, crawl_frequency, False, f"fresh:{crawl_frequency}", None, next_recrawl, source)


def _decision(
    source_id: str,
    canonical_url: str,
    crawl_frequency: str,
    eligible: bool,
    reason: str,
    skip_reason: str | None,
    next_recrawl_after: datetime | None,
    source: Mapping[str, Any],
) -> RecrawlDecision:
    last_seen_at = _optional_string(source.get("last_seen_at")) or _optional_string(source.get("last_checked_at"))
    return RecrawlDecision(
        source_id=source_id,
        citation_source_id=source_id,
        canonical_url=canonical_url,
        crawl_frequency=crawl_frequency,
        eligible=eligible,
        reason=reason,
        skip_reason=skip_reason,
        last_seen_at=last_seen_at,
        next_recrawl_after=_format_datetime(next_recrawl_after),
        no_raw_body_persisted=True,
    )


def _assert_no_raw_body(source: Mapping[str, Any]) -> None:
    present = sorted(key for key in source if key in _RAW_BODY_KEYS)
    if present:
        source_id = source.get("source_id", "")
        raise ValueError(f"source {source_id} contains raw body field(s): {', '.join(present)}")


def _policy_skip_reason(source: Mapping[str, Any]) -> str | None:
    allowlist_policy = str(source.get("allowlist_policy", "allow")).strip().lower()
    robots_policy = str(source.get("robots_policy", "allow")).strip().lower()
    processor_policy = str(source.get("processor_policy", "metadata_only")).strip().lower()
    if allowlist_policy in _POLICY_SKIP_VALUES:
        return "outside allowlist or blocked by allowlist policy"
    if robots_policy in _POLICY_SKIP_VALUES:
        return "disallowed by robots or policy"
    if processor_policy in {"raw_body", "persist_raw_body", "raw_download"}:
        return "raw download not permitted"
    return None


def _required_string(source: Mapping[str, Any], key: str) -> str:
    value = source.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"source is missing required string field: {key}")
    return value.strip()


def _optional_string(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _normalize_frequency(value: str) -> str:
    return value.strip().lower().replace(" ", "_")


def _coerce_datetime(value: datetime | str) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    parsed = datetime.fromisoformat(normalized)
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def _format_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
