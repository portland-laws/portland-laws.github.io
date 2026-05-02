"""Fixture-friendly PP&D source freshness classification.

This module classifies source-index style records only from curated metadata. It
performs no network access and does not accept raw response bodies or downloaded
documents.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Iterable, Mapping, Optional


SOURCE_FRESHNESS_CONTRACT_VERSION = 1


class SourceFreshnessStatus(str, Enum):
    FRESH = "fresh"
    STALE_GUIDANCE = "stale_guidance"
    CONTENT_HASH_CHANGED = "content_hash_changed"
    PAGE_REMOVED = "page_removed"
    PRIORITY_RECRAWL = "priority_recrawl"


class SourceFreshnessReason(str, Enum):
    WITHIN_CADENCE = "within_cadence"
    STALE_BY_CADENCE = "stale_by_cadence"
    HASH_CHANGED = "hash_changed"
    REMOVED_STATUS = "removed_status"
    HIGH_PRIORITY_HINT = "high_priority_hint"
    HIGH_CHANGE_PAGE_TYPE = "high_change_page_type"
    MISSING_TIMESTAMP = "missing_timestamp"


HIGH_CHANGE_PAGE_TYPES = frozenset(
    {
        "devhub_faq",
        "devhub_guide",
        "permit_application",
        "permit_applications",
        "forms_index",
        "fee_page",
        "payment_page",
        "temporary_rule",
        "temporary_exemption",
    }
)

REMOVED_STATUSES = frozenset({"removed", "gone", "not_found", "not-found", "404", "410"})


@dataclass(frozen=True)
class SourceFreshnessRecord:
    id: str
    canonical_url: str
    last_seen_at: str
    recrawl_cadence_days: int
    previous_content_hash: Optional[str] = None
    current_content_hash: Optional[str] = None
    crawl_status: str = "ok"
    http_status: Optional[int] = None
    page_type: str = "guidance"
    recrawl_priority: str = "normal"
    as_of: Optional[str] = None


@dataclass(frozen=True)
class SourceFreshnessFinding:
    record_id: str
    canonical_url: str
    status: SourceFreshnessStatus
    reasons: tuple[SourceFreshnessReason, ...]
    recrawl_required: bool
    recrawl_priority: str


@dataclass(frozen=True)
class SourceFreshnessReport:
    schema_version: int
    findings: tuple[SourceFreshnessFinding, ...]

    def by_status(self, status: SourceFreshnessStatus) -> tuple[SourceFreshnessFinding, ...]:
        return tuple(finding for finding in self.findings if finding.status == status)


def classify_source_freshness(record: SourceFreshnessRecord, as_of: Optional[str] = None) -> SourceFreshnessFinding:
    reasons: list[SourceFreshnessReason] = []
    effective_as_of = as_of or record.as_of

    removed = _is_removed(record)
    changed = _hash_changed(record.previous_content_hash, record.current_content_hash)
    stale = _is_stale(record.last_seen_at, record.recrawl_cadence_days, effective_as_of)
    priority = _is_priority_recrawl(record)

    if removed:
        status = SourceFreshnessStatus.PAGE_REMOVED
        reasons.append(SourceFreshnessReason.REMOVED_STATUS)
    elif changed:
        status = SourceFreshnessStatus.CONTENT_HASH_CHANGED
        reasons.append(SourceFreshnessReason.HASH_CHANGED)
    elif stale:
        status = SourceFreshnessStatus.STALE_GUIDANCE
        reasons.append(SourceFreshnessReason.STALE_BY_CADENCE)
    elif priority:
        status = SourceFreshnessStatus.PRIORITY_RECRAWL
    else:
        status = SourceFreshnessStatus.FRESH
        reasons.append(SourceFreshnessReason.WITHIN_CADENCE)

    if stale and SourceFreshnessReason.STALE_BY_CADENCE not in reasons:
        reasons.append(SourceFreshnessReason.STALE_BY_CADENCE)
    if priority:
        if record.recrawl_priority.lower() in {"high", "urgent", "daily"}:
            reasons.append(SourceFreshnessReason.HIGH_PRIORITY_HINT)
        if record.page_type.lower() in HIGH_CHANGE_PAGE_TYPES:
            reasons.append(SourceFreshnessReason.HIGH_CHANGE_PAGE_TYPE)
    if stale is None:
        reasons.append(SourceFreshnessReason.MISSING_TIMESTAMP)

    return SourceFreshnessFinding(
        record_id=record.id,
        canonical_url=record.canonical_url,
        status=status,
        reasons=tuple(dict.fromkeys(reasons)),
        recrawl_required=status != SourceFreshnessStatus.FRESH,
        recrawl_priority=_normalized_priority(record, status),
    )


def classify_source_freshness_records(
    records: Iterable[SourceFreshnessRecord | Mapping[str, Any]], as_of: Optional[str] = None
) -> SourceFreshnessReport:
    findings = tuple(
        classify_source_freshness(
            record if isinstance(record, SourceFreshnessRecord) else source_freshness_record_from_dict(record),
            as_of=as_of,
        )
        for record in records
    )
    return SourceFreshnessReport(schema_version=SOURCE_FRESHNESS_CONTRACT_VERSION, findings=findings)


def source_freshness_record_from_dict(data: Mapping[str, Any]) -> SourceFreshnessRecord:
    return SourceFreshnessRecord(
        id=str(data.get("id", data.get("recordId", data.get("record_id", "")))),
        canonical_url=str(data.get("canonicalUrl", data.get("canonical_url", data.get("url", "")))),
        last_seen_at=str(data.get("lastSeenAt", data.get("last_seen_at", data.get("lastCrawledAt", data.get("last_crawled_at", ""))))),
        recrawl_cadence_days=int(data.get("recrawlCadenceDays", data.get("recrawl_cadence_days", 30))),
        previous_content_hash=_optional_string(data.get("previousContentHash", data.get("previous_content_hash", data.get("storedContentHash", data.get("stored_content_hash"))))),
        current_content_hash=_optional_string(data.get("currentContentHash", data.get("current_content_hash", data.get("observedContentHash", data.get("observed_content_hash"))))),
        crawl_status=str(data.get("crawlStatus", data.get("crawl_status", data.get("status", "ok")))),
        http_status=_optional_int(data.get("httpStatus", data.get("http_status", data.get("observedHttpStatus", data.get("observed_http_status"))))),
        page_type=str(data.get("pageType", data.get("page_type", "guidance"))),
        recrawl_priority=str(data.get("recrawlPriority", data.get("recrawl_priority", "normal"))),
        as_of=_optional_string(data.get("asOf", data.get("as_of"))),
    )


def _is_removed(record: SourceFreshnessRecord) -> bool:
    if record.http_status in {404, 410}:
        return True
    return record.crawl_status.strip().lower() in REMOVED_STATUSES


def _hash_changed(previous_hash: Optional[str], current_hash: Optional[str]) -> bool:
    if not previous_hash or not current_hash:
        return False
    return previous_hash.strip() != current_hash.strip()


def _is_stale(last_seen_at: str, cadence_days: int, as_of: Optional[str]) -> Optional[bool]:
    if not as_of:
        return False
    seen = _parse_utc(last_seen_at)
    now = _parse_utc(as_of)
    if seen is None or now is None:
        return None
    return (now - seen).days > cadence_days


def _is_priority_recrawl(record: SourceFreshnessRecord) -> bool:
    if record.recrawl_priority.strip().lower() in {"high", "urgent", "daily"}:
        return True
    return record.page_type.strip().lower() in HIGH_CHANGE_PAGE_TYPES


def _normalized_priority(record: SourceFreshnessRecord, status: SourceFreshnessStatus) -> str:
    explicit = record.recrawl_priority.strip().lower()
    if explicit in {"urgent", "high", "normal", "low", "daily", "weekly", "monthly"}:
        return explicit
    if status in {SourceFreshnessStatus.PAGE_REMOVED, SourceFreshnessStatus.CONTENT_HASH_CHANGED}:
        return "high"
    if status in {SourceFreshnessStatus.STALE_GUIDANCE, SourceFreshnessStatus.PRIORITY_RECRAWL}:
        return "normal"
    return "low"


def _parse_utc(value: str) -> Optional[datetime]:
    if not value:
        return None
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _optional_string(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value)
    if not text:
        return None
    return text


def _optional_int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
