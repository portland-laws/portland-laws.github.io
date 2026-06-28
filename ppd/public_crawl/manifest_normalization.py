"""Manifest normalization helpers for PP&D public crawl records.

The public crawler may intentionally skip a source before any document is fetched.
Those records still need a stable manifest shape so archive validation and later
processor handoff code can treat them like ordinary crawl records.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping


_SKIPPED_STATUSES = {"skip", "skipped"}


def normalize_public_crawl_manifest_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """Return a normalized copy of one public crawl manifest record.

    For skipped records, fill only missing archive/processor-neutral defaults.
    Existing archive metadata and processor handoff fields are preserved exactly.
    """

    normalized = deepcopy(dict(record))
    status = str(normalized.get("status", "")).strip().lower()
    skipped = bool(normalized.get("skipped")) or status in _SKIPPED_STATUSES

    if not skipped:
        return normalized

    normalized["status"] = "skipped"
    normalized["skipped"] = True
    normalized.setdefault("documents", [])
    normalized.setdefault("document_count", len(normalized.get("documents") or []))
    normalized.setdefault("archive_items", [])
    normalized.setdefault("processor_handoff", [])
    normalized.setdefault("skip_reason", normalized.get("reason") or "not_applicable")
    return normalized


def normalize_public_crawl_manifest(records: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Normalize all records in a public crawl manifest list."""

    return [normalize_public_crawl_manifest_record(record) for record in records]
