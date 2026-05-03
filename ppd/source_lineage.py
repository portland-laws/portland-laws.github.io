"""Fixture-only public source lineage rollups for PP&D validation."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

_RAW_RESPONSE_KEYS = {
    "body",
    "content",
    "html",
    "raw_body",
    "raw_content",
    "raw_html",
    "response_body",
    "response_text",
}

_ID_CHARS = re.compile(r"[^a-z0-9]+")
_KNOWN_EXTENSIONS = re.compile(r"\.(html?|pdf|aspx?|json|txt)$")


def load_public_source_lineage_fixture(path: str | Path) -> dict[str, Any]:
    """Load a committed lineage fixture and return its deterministic rollup."""
    with Path(path).open("r", encoding="utf-8") as fixture_file:
        fixture = json.load(fixture_file)
    return build_public_source_lineage_rollup(fixture)


def build_public_source_lineage_rollup(fixture: dict[str, Any]) -> dict[str, Any]:
    """Summarize public PP&D source lineage from fixture data only.

    The fixture intentionally stores metadata, not crawl responses. This function
    rejects common raw response-body keys anywhere in the fixture so validation
    cannot accidentally bless downloaded page or document contents.
    """
    _reject_raw_response_bodies(fixture)

    seed_urls = _string_list(fixture.get("seed_urls", []))
    manifests = fixture.get("processor_handoff_manifests", []) or []
    freshness_records = fixture.get("source_freshness_records", []) or []
    skipped_actions = fixture.get("skipped_actions", []) or []

    document_ids = {_document_id_from_url(url) for url in seed_urls}
    handoff_rollups = []
    for manifest in manifests:
        documents = manifest.get("documents", []) or []
        manifest_ids = []
        for document in documents:
            doc_id = document.get("document_id") or _document_id_from_url(document.get("source_url", ""))
            normalized = normalize_document_id(doc_id)
            if normalized:
                manifest_ids.append(normalized)
                document_ids.add(normalized)
        handoff_rollups.append(
            {
                "manifest_id": str(manifest.get("manifest_id", "")),
                "processor": str(manifest.get("processor", "")),
                "document_ids": sorted(set(manifest_ids)),
                "document_count": len(set(manifest_ids)),
            }
        )

    freshness_rollups = []
    for record in freshness_records:
        doc_id = normalize_document_id(record.get("document_id") or _document_id_from_url(record.get("source_url", "")))
        if doc_id:
            document_ids.add(doc_id)
        freshness_rollups.append(
            {
                "document_id": doc_id,
                "freshness_checked_at": str(record.get("freshness_checked_at", "")),
                "last_seen_at": str(record.get("last_seen_at", "")),
                "status": str(record.get("status", "unknown")),
            }
        )

    skipped_reason_counts = Counter(str(action.get("reason", "unspecified")) for action in skipped_actions)

    return {
        "fixture_only": True,
        "seed_urls": sorted(seed_urls),
        "seed_url_count": len(seed_urls),
        "processor_handoff_manifests": sorted(handoff_rollups, key=lambda item: item["manifest_id"]),
        "normalized_document_ids": sorted(document_ids),
        "normalized_document_id_count": len(document_ids),
        "source_freshness_records": sorted(freshness_rollups, key=lambda item: item["document_id"]),
        "skipped_action_reasons": dict(sorted(skipped_reason_counts.items())),
    }


def normalize_document_id(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = _KNOWN_EXTENSIONS.sub("", text)
    text = _ID_CHARS.sub("-", text).strip("-")
    return f"ppd:{text}" if text and not text.startswith("ppd-") and not text.startswith("ppd:") else text.replace("ppd-", "ppd:", 1)


def _document_id_from_url(url: Any) -> str:
    parsed = urlparse(str(url or ""))
    path = parsed.path.strip("/")
    candidate = path.rsplit("/", 1)[-1] if path else parsed.netloc
    return normalize_document_id(candidate)


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _reject_raw_response_bodies(value: Any, path: str = "fixture") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in _RAW_RESPONSE_KEYS:
                raise ValueError(f"raw response body field is not allowed at {path}.{key}")
            _reject_raw_response_bodies(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_raw_response_bodies(child, f"{path}[{index}]")
