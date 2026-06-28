"""Fixture-first PP&D source coverage audit packet validation.

This module validates committed metadata packets that compare official PP&D
source anchors with source registry records, skipped URL policy reasons,
freshness cadence, owning surface, and downstream requirement/process/guardrail
links. It is intentionally side-effect free: no crawl, no download, no DevHub
session access, and no raw response body persistence.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import urlsplit

from ppd.source_anchor_matrix import ORIGINAL_PUBLIC_SOURCE_ANCHORS


MODULE_PURPOSE = "fixture_first_source_coverage_audit_packet"
SCHEMA_VERSION = 1

ALLOWED_PUBLIC_HOSTS = {
    "www.portland.gov",
    "devhub.portlandoregon.gov",
    "www.portlandoregon.gov",
    "www.portlandmaps.com",
}

ALLOWED_SOURCE_TYPES = {
    "public_html",
    "public_pdf",
    "public_form",
    "devhub_public",
    "devhub_authenticated",
    "external_reference",
}

ALLOWED_SKIP_REASONS = {
    "outside_allowlist",
    "unsupported_scheme",
    "private_authenticated",
    "disallowed_by_robots_or_policy",
    "raw_download_not_permitted",
    "too_large",
    "unsupported_content_type",
}

ALLOWED_FRESHNESS_CADENCES = {
    "daily_or_every_few_days",
    "weekly",
    "monthly",
    "only_when_linked_from_ppd_guidance",
}

REQUIRED_REGISTRY_FIELDS = (
    "source_id",
    "canonical_url",
    "source_type",
    "owning_surface",
    "allowlist_policy",
    "robots_policy",
    "crawl_frequency",
    "processor_policy",
    "privacy_classification",
    "last_seen_at",
    "freshness_status",
)

FORBIDDEN_KEYS = {
    "authorization",
    "auth",
    "body",
    "content",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "download_path",
    "downloaded_document",
    "html",
    "password",
    "raw_body",
    "raw_content",
    "raw_html",
    "raw_response",
    "raw_response_body",
    "response_body",
    "screenshot",
    "screenshot_path",
    "secret",
    "session",
    "storage_state",
    "text",
    "token",
    "trace",
    "trace_path",
    "username",
}

FORBIDDEN_VALUE_MARKERS = (
    "ppd/data/private",
    "devhub/session",
    "devhub/sessions",
    "storage_state",
    "auth_state",
    "cookies.json",
    "localstorage.json",
    "trace.zip",
    "playwright-report",
    "/screenshots/",
    "screenshot.png",
    "screenshot.jpg",
    "screenshot.jpeg",
    "screenshot.webp",
    "/downloads/",
    "downloaded_documents",
    "raw_body",
    "rawbody",
    "response_body",
    "responsebody",
    "raw_html",
    "rawhtml",
    "credential",
    "credentials",
    "password",
    "bearer",
    "authorization",
    "session_cookie",
)


class SourceCoverageAuditPacketError(ValueError):
    """Raised when a fixture-only source coverage audit packet is unsafe."""


def load_audit_packet(path: str | Path) -> dict[str, Any]:
    """Load and validate a committed source coverage audit packet fixture."""

    packet_path = Path(path)
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    validate_audit_packet(packet)
    return packet


def validate_audit_packet(packet: Mapping[str, Any]) -> None:
    """Validate packet shape, coverage, and no-raw-artifact constraints."""

    errors: list[str] = []
    _collect_forbidden_content(packet, "$", errors)

    if packet.get("schemaVersion") != SCHEMA_VERSION:
        errors.append("schemaVersion must be 1")
    if packet.get("packetType") != "ppd_source_coverage_audit_packet":
        errors.append("packetType must be ppd_source_coverage_audit_packet")
    if packet.get("sourceMode") != "fixture_first_no_crawl":
        errors.append("sourceMode must be fixture_first_no_crawl")
    if packet.get("liveCrawlingUsed") is not False:
        errors.append("liveCrawlingUsed must be false")
    if packet.get("authenticatedAutomationUsed") is not False:
        errors.append("authenticatedAutomationUsed must be false")
    if packet.get("rawBodiesPersisted") is not False:
        errors.append("rawBodiesPersisted must be false")
    if not str(packet.get("generatedAt", "")).endswith("Z"):
        errors.append("generatedAt must be an ISO UTC timestamp ending in Z")

    official_anchor_urls = _validate_official_anchors(packet.get("officialAnchors"), errors)
    registry_by_url = _validate_registry_records(packet.get("sourceRegistryRecords"), errors)
    _validate_anchor_registry_coverage(official_anchor_urls, registry_by_url, errors)
    _validate_skipped_urls(packet.get("skippedUrls"), errors)
    _validate_downstream_links(packet.get("downstreamLinks"), registry_by_url, errors)
    _validate_audit_rows(packet.get("auditRows"), official_anchor_urls, registry_by_url, errors)

    if errors:
        raise SourceCoverageAuditPacketError("; ".join(errors))


def source_ids_by_anchor(packet: Mapping[str, Any]) -> dict[str, str]:
    """Return canonical URL to source ID mapping after validation."""

    validate_audit_packet(packet)
    return {
        str(record["canonical_url"]): str(record["source_id"])
        for record in _as_list(packet.get("sourceRegistryRecords"))
    }


def _validate_official_anchors(value: Any, errors: list[str]) -> set[str]:
    anchors = _as_list(value)
    urls: set[str] = set()
    for index, anchor in enumerate(anchors):
        if not isinstance(anchor, Mapping):
            errors.append(f"officialAnchors[{index}] must be an object")
            continue
        url = str(anchor.get("canonical_url", "")).strip()
        if not url:
            errors.append(f"officialAnchors[{index}].canonical_url is required")
            continue
        _validate_public_url(url, f"officialAnchors[{index}].canonical_url", errors)
        urls.add(url)
        if str(anchor.get("anchor_basis", "")) != "ppd_plan_official_source_anchor":
            errors.append(f"officialAnchors[{index}].anchor_basis must be ppd_plan_official_source_anchor")

    expected = set(ORIGINAL_PUBLIC_SOURCE_ANCHORS)
    missing = sorted(expected - urls)
    extra = sorted(urls - expected)
    if missing:
        errors.append("officialAnchors missing URLs: " + ", ".join(missing))
    if extra:
        errors.append("officialAnchors contain unexpected URLs: " + ", ".join(extra))
    return urls


def _validate_registry_records(value: Any, errors: list[str]) -> dict[str, Mapping[str, Any]]:
    records = _as_list(value)
    by_url: dict[str, Mapping[str, Any]] = {}
    source_ids: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"sourceRegistryRecords[{index}] must be an object")
            continue
        prefix = f"sourceRegistryRecords[{index}]"
        for field in REQUIRED_REGISTRY_FIELDS:
            if not str(record.get(field, "")).strip():
                errors.append(f"{prefix}.{field} is required")
        source_id = str(record.get("source_id", "")).strip()
        url = str(record.get("canonical_url", "")).strip()
        if source_id in source_ids:
            errors.append(f"duplicate source_id {source_id}")
        if source_id:
            source_ids.add(source_id)
        if url in by_url:
            errors.append(f"duplicate canonical_url {url}")
        if url:
            by_url[url] = record
            _validate_public_url(url, f"{prefix}.canonical_url", errors)
        if str(record.get("source_type", "")) not in ALLOWED_SOURCE_TYPES:
            errors.append(f"{prefix}.source_type is not supported")
        if str(record.get("crawl_frequency", "")) not in ALLOWED_FRESHNESS_CADENCES:
            errors.append(f"{prefix}.crawl_frequency is not an allowed freshness cadence")
        if str(record.get("allowlist_policy", "")) != "allowed_public_seed":
            errors.append(f"{prefix}.allowlist_policy must be allowed_public_seed")
        if str(record.get("privacy_classification", "")) != "public_metadata_only":
            errors.append(f"{prefix}.privacy_classification must be public_metadata_only")
    return by_url


def _validate_anchor_registry_coverage(
    official_anchor_urls: set[str],
    registry_by_url: Mapping[str, Mapping[str, Any]],
    errors: list[str],
) -> None:
    missing = sorted(official_anchor_urls - set(registry_by_url))
    extra = sorted(set(registry_by_url) - official_anchor_urls)
    if missing:
        errors.append("sourceRegistryRecords missing official anchors: " + ", ".join(missing))
    if extra:
        errors.append("sourceRegistryRecords contain non-anchor URLs: " + ", ".join(extra))


def _validate_skipped_urls(value: Any, errors: list[str]) -> None:
    skipped = _as_list(value)
    seen_reasons: set[str] = set()
    for index, item in enumerate(skipped):
        if not isinstance(item, Mapping):
            errors.append(f"skippedUrls[{index}] must be an object")
            continue
        prefix = f"skippedUrls[{index}]"
        url = str(item.get("url", "")).strip()
        reason = str(item.get("reason", "")).strip()
        if not url:
            errors.append(f"{prefix}.url is required")
        if reason not in ALLOWED_SKIP_REASONS:
            errors.append(f"{prefix}.reason is not supported")
        else:
            seen_reasons.add(reason)
        if str(item.get("raw_body_stored", "")) != "False" and item.get("raw_body_stored") is not False:
            errors.append(f"{prefix}.raw_body_stored must be false")
        if reason != "unsupported_scheme" and url:
            parsed = urlsplit(url)
            if parsed.scheme != "https":
                errors.append(f"{prefix}.url must be HTTPS unless reason is unsupported_scheme")
    missing_reasons = sorted(ALLOWED_SKIP_REASONS - seen_reasons)
    if missing_reasons:
        errors.append("skippedUrls missing reason coverage: " + ", ".join(missing_reasons))


def _validate_downstream_links(
    value: Any,
    registry_by_url: Mapping[str, Mapping[str, Any]],
    errors: list[str],
) -> None:
    links = _as_list(value)
    linked_source_ids: set[str] = set()
    registry_source_ids = {str(record.get("source_id", "")) for record in registry_by_url.values()}
    for index, link in enumerate(links):
        if not isinstance(link, Mapping):
            errors.append(f"downstreamLinks[{index}] must be an object")
            continue
        prefix = f"downstreamLinks[{index}]"
        source_id = str(link.get("source_id", "")).strip()
        if source_id not in registry_source_ids:
            errors.append(f"{prefix}.source_id does not match a registry record")
        else:
            linked_source_ids.add(source_id)
        for field in ("requirement_ids", "process_ids", "guardrail_bundle_ids"):
            values = link.get(field)
            if not isinstance(values, list) or not values or not all(str(item).strip() for item in values):
                errors.append(f"{prefix}.{field} must be a non-empty list")
    missing_links = sorted(registry_source_ids - linked_source_ids)
    if missing_links:
        errors.append("downstreamLinks missing source IDs: " + ", ".join(missing_links))


def _validate_audit_rows(
    value: Any,
    official_anchor_urls: set[str],
    registry_by_url: Mapping[str, Mapping[str, Any]],
    errors: list[str],
) -> None:
    rows = _as_list(value)
    row_urls: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            errors.append(f"auditRows[{index}] must be an object")
            continue
        prefix = f"auditRows[{index}]"
        url = str(row.get("canonical_url", "")).strip()
        row_urls.add(url)
        record = registry_by_url.get(url)
        if record is None:
            errors.append(f"{prefix}.canonical_url must match a registry record")
            continue
        comparisons = {
            "source_id": "source_id",
            "owning_surface": "owning_surface",
            "freshness_cadence": "crawl_frequency",
            "freshness_status": "freshness_status",
        }
        for row_field, registry_field in comparisons.items():
            if str(row.get(row_field, "")) != str(record.get(registry_field, "")):
                errors.append(f"{prefix}.{row_field} must match registry {registry_field}")
        if row.get("registry_record_present") is not True:
            errors.append(f"{prefix}.registry_record_present must be true")
        if row.get("downstream_links_present") is not True:
            errors.append(f"{prefix}.downstream_links_present must be true")
        if row.get("raw_body_stored") is not False:
            errors.append(f"{prefix}.raw_body_stored must be false")
    missing_rows = sorted(official_anchor_urls - row_urls)
    if missing_rows:
        errors.append("auditRows missing official anchors: " + ", ".join(missing_rows))


def _validate_public_url(url: str, path: str, errors: list[str]) -> None:
    parsed = urlsplit(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not host:
        errors.append(f"{path} must be an HTTPS URL")
    if parsed.username or parsed.password:
        errors.append(f"{path} must not contain credentials")
    if host and host not in ALLOWED_PUBLIC_HOSTS:
        errors.append(f"{path} host is not allowed: {host}")


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _collect_forbidden_content(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            lower_key = key_text.lower()
            if lower_key in FORBIDDEN_KEYS and child not in (None, "", [], {}, False):
                errors.append(f"{path}.{key_text} must not contain private, raw, or authenticated content")
            _collect_forbidden_content(child, f"{path}.{key_text}", errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _collect_forbidden_content(child, f"{path}[{index}]", errors)
    elif isinstance(value, str):
        lower_value = value.lower()
        for marker in FORBIDDEN_VALUE_MARKERS:
            if marker in lower_value:
                errors.append(f"{path} contains forbidden private/raw artifact marker {marker}")


__all__ = [
    "MODULE_PURPOSE",
    "SourceCoverageAuditPacketError",
    "load_audit_packet",
    "source_ids_by_anchor",
    "validate_audit_packet",
]
