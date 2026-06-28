"""Validation for PP&D processor archive integration manifests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


PRIVATE_MARKERS = (
    "devhub_private",
    "devhub_session",
    "auth_state",
    "cookie",
    "cookies",
    "csrf",
    "captcha",
    "mfa",
    "token",
    "password",
    "private_devhub",
)

RAW_CRAWL_MARKERS = (
    "raw_crawl",
    "crawl_dump",
    "playwright_trace",
    "har",
    "screenshot",
    "downloaded_document",
    "raw_html",
)


class ManifestValidationError(ValueError):
    """Raised when a processor archive manifest is not safe to hand off."""


def load_manifest(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ManifestValidationError("manifest must be a JSON object")
    return data


def deterministic_handoff_id(public_sources: list[dict[str, Any]]) -> str:
    canonical_sources = []
    for source in public_sources:
        canonical_sources.append(
            {
                "archive_path": source.get("archive_path"),
                "source_url": source.get("source_url"),
                "retrieved_at": source.get("retrieved_at"),
                "citations": source.get("citations", []),
            }
        )
    payload = json.dumps(canonical_sources, sort_keys=True, separators=(",", ":"))
    return "ppd-logic-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def validate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    public_sources = manifest.get("public_sources")
    if not isinstance(public_sources, list) or not public_sources:
        raise ManifestValidationError("manifest.public_sources must be a non-empty list")

    prohibited_paths = manifest.get("prohibited_paths", [])
    if not isinstance(prohibited_paths, list):
        raise ManifestValidationError("manifest.prohibited_paths must be a list when present")

    searchable_manifest = json.dumps(manifest, sort_keys=True).lower()
    for marker in PRIVATE_MARKERS:
        if marker in searchable_manifest:
            raise ManifestValidationError(f"manifest contains private DevHub marker: {marker}")
    for marker in RAW_CRAWL_MARKERS:
        if marker in searchable_manifest:
            raise ManifestValidationError(f"manifest contains raw crawl marker: {marker}")

    for index, source in enumerate(public_sources):
        if not isinstance(source, dict):
            raise ManifestValidationError(f"public_sources[{index}] must be an object")
        for field in ("archive_path", "source_url", "retrieved_at", "citations"):
            if field not in source:
                raise ManifestValidationError(f"public_sources[{index}] missing {field}")
        if not str(source["source_url"]).startswith(("https://", "http://")):
            raise ManifestValidationError(f"public_sources[{index}].source_url must be public HTTP(S)")
        citations = source["citations"]
        if not isinstance(citations, list) or not citations:
            raise ManifestValidationError(f"public_sources[{index}] must include at least one citation")
        for citation_index, citation in enumerate(citations):
            if not isinstance(citation, dict):
                raise ManifestValidationError(
                    f"public_sources[{index}].citations[{citation_index}] must be an object"
                )
            if not citation.get("url") or not citation.get("title"):
                raise ManifestValidationError(
                    f"public_sources[{index}].citations[{citation_index}] needs url and title"
                )

    expected_handoff_id = deterministic_handoff_id(public_sources)
    if manifest.get("handoff_id") != expected_handoff_id:
        raise ManifestValidationError("manifest.handoff_id is not deterministic for public_sources")

    return {"handoff_id": expected_handoff_id, "public_source_count": len(public_sources)}


def validate_manifest_file(path: str | Path) -> dict[str, Any]:
    return validate_manifest(load_manifest(path))
