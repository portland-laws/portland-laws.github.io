"""Fixture-only public source discovery index validation for PP&D.

This module intentionally does not crawl, fetch, download, or persist page bodies.
It validates committed discovery fixtures that describe official PP&D seed-page
links and policy decisions before any live archival workflow is introduced.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

ALLOWED_HOSTS = frozenset(
    {
        "www.portland.gov",
        "devhub.portlandoregon.gov",
        "www.portlandoregon.gov",
        "www.portlandmaps.com",
    }
)

DECISIONS = frozenset({"allow", "skip"})

SKIP_REASON_CODES = frozenset(
    {
        "outside_allowlist",
        "unsupported_scheme",
        "private_authenticated",
        "disallowed_by_robots_or_policy",
        "raw_download_not_permitted",
        "too_large",
        "unsupported_content_type",
    }
)

CONTENT_TYPE_HINTS = frozenset(
    {
        "public_html",
        "public_pdf",
        "public_form",
        "devhub_public",
        "external_reference",
        "unknown",
    }
)

REQUIRED_RECORD_FIELDS = frozenset(
    {
        "discovery_id",
        "canonical_url",
        "source_page_url",
        "link_text",
        "content_type_hint",
        "decision",
        "skip_reason_code",
    }
)


def canonicalize_url(url: str) -> str:
    """Return a stable canonical form suitable for fixture comparisons."""
    parsed = urlsplit(url.strip())
    scheme = parsed.scheme.lower()
    hostname = (parsed.hostname or "").lower()

    if not scheme or not hostname:
        return url.strip()

    port = parsed.port
    include_port = port is not None and not (
        (scheme == "http" and port == 80) or (scheme == "https" and port == 443)
    )
    netloc = f"{hostname}:{port}" if include_port else hostname
    path = parsed.path or ""
    if path != "/":
        path = path.rstrip("/")

    return urlunsplit((scheme, netloc, path, parsed.query, ""))


def load_discovery_index(path: str | Path) -> dict[str, Any]:
    """Load a committed fixture-only discovery index from JSON."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_discovery_index(index: dict[str, Any]) -> list[str]:
    """Validate a fixture-only discovery index and return human-readable errors."""
    errors: list[str] = []

    metadata = index.get("metadata")
    if not isinstance(metadata, dict):
        return ["metadata must be an object"]

    if metadata.get("fixture_only") is not True:
        errors.append("metadata.fixture_only must be true")
    if metadata.get("no_live_crawl") is not True:
        errors.append("metadata.no_live_crawl must be true")
    if metadata.get("no_raw_page_bodies") is not True:
        errors.append("metadata.no_raw_page_bodies must be true")

    declared_skip_codes = metadata.get("skip_reason_codes")
    if sorted(SKIP_REASON_CODES) != sorted(declared_skip_codes or []):
        errors.append("metadata.skip_reason_codes must match the supported reason-code set")

    records = index.get("records")
    if not isinstance(records, list) or not records:
        errors.append("records must be a non-empty list")
        return errors

    seen_ids: set[str] = set()
    seen_urls: set[str] = set()

    for position, record in enumerate(records):
        prefix = f"records[{position}]"
        if not isinstance(record, dict):
            errors.append(f"{prefix} must be an object")
            continue

        missing = sorted(REQUIRED_RECORD_FIELDS - set(record))
        if missing:
            errors.append(f"{prefix} missing required fields: {', '.join(missing)}")
            continue

        discovery_id = record.get("discovery_id")
        if not isinstance(discovery_id, str) or not discovery_id:
            errors.append(f"{prefix}.discovery_id must be a non-empty string")
        elif discovery_id in seen_ids:
            errors.append(f"{prefix}.discovery_id duplicates {discovery_id}")
        else:
            seen_ids.add(discovery_id)

        canonical_url = record.get("canonical_url")
        if not isinstance(canonical_url, str) or not canonical_url:
            errors.append(f"{prefix}.canonical_url must be a non-empty string")
        elif canonicalize_url(canonical_url) != canonical_url:
            errors.append(f"{prefix}.canonical_url is not canonicalized")
        elif canonical_url in seen_urls:
            errors.append(f"{prefix}.canonical_url duplicates {canonical_url}")
        else:
            seen_urls.add(canonical_url)

        source_page_url = record.get("source_page_url")
        if not isinstance(source_page_url, str) or not source_page_url:
            errors.append(f"{prefix}.source_page_url must be a non-empty string")
        elif source_page_url.startswith("http") and canonicalize_url(source_page_url) != source_page_url:
            errors.append(f"{prefix}.source_page_url is not canonicalized")

        link_text = record.get("link_text")
        if not isinstance(link_text, str) or not link_text.strip():
            errors.append(f"{prefix}.link_text must be a non-empty string")

        content_type_hint = record.get("content_type_hint")
        if content_type_hint not in CONTENT_TYPE_HINTS:
            errors.append(f"{prefix}.content_type_hint is unsupported: {content_type_hint!r}")

        decision = record.get("decision")
        if decision not in DECISIONS:
            errors.append(f"{prefix}.decision must be one of {sorted(DECISIONS)}")

        skip_reason_code = record.get("skip_reason_code")
        if decision == "allow" and skip_reason_code is not None:
            errors.append(f"{prefix}.skip_reason_code must be null when decision is allow")
        if decision == "skip" and skip_reason_code not in SKIP_REASON_CODES:
            errors.append(f"{prefix}.skip_reason_code is unsupported: {skip_reason_code!r}")

        parsed = urlsplit(str(canonical_url))
        if parsed.scheme not in {"http", "https"}:
            if decision != "skip" or skip_reason_code != "unsupported_scheme":
                errors.append(f"{prefix} unsupported schemes must be skipped with unsupported_scheme")
        elif parsed.hostname not in ALLOWED_HOSTS:
            if decision != "skip" or skip_reason_code != "outside_allowlist":
                errors.append(f"{prefix} outside hosts must be skipped with outside_allowlist")

        if decision == "allow" and parsed.hostname not in ALLOWED_HOSTS:
            errors.append(f"{prefix} allowed records must use a PP&D allowlisted host")

    return errors


def allowed_records(index: dict[str, Any]) -> list[dict[str, Any]]:
    """Return records that policy allows for later preflight/handoff steps."""
    return [record for record in index.get("records", []) if record.get("decision") == "allow"]
