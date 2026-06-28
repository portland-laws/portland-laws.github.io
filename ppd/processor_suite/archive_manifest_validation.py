"""Validation for PP&D processor archive integration manifests.

This module validates only committed, metadata-only archive integration
manifests. It does not crawl, download documents, invoke browser automation, or
read private DevHub data.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse


PUBLIC_HOSTS = {"www.portland.gov", "devhub.portlandoregon.gov"}
FORBIDDEN_TEXT_MARKERS = (
    "ppd/data/private",
    "ppd/data/raw",
    "auth-state",
    "storage-state",
    "cookie",
    "credential",
    "csrf",
    "password",
    "token",
    "trace.zip",
    ".har",
    "screenshot",
    "raw_crawl",
    "raw-html",
    "raw_http_body",
    "downloaded_document_bytes",
)
REQUIRED_FALSE_FLAGS = (
    "networkAccess",
    "processorInvoked",
    "documentsDownloaded",
    "downloadedDocumentsIncluded",
    "rawBodiesIncluded",
    "rawCrawlOutputIncluded",
    "privateDevhubDataIncluded",
)


class ArchiveManifestValidationError(ValueError):
    """Raised when a processor archive integration manifest is unsafe."""


def load_manifest(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ArchiveManifestValidationError("manifest must be a JSON object")
    return data


def deterministic_handoff_id(archived_public_sources: list[Mapping[str, Any]]) -> str:
    """Build a stable formal-logic handoff id from public source metadata."""

    document_ids = sorted(str(source.get("canonicalDocumentId", "")) for source in archived_public_sources)
    if not document_ids or any(not document_id for document_id in document_ids):
        return "logic-handoff-invalid-source-set"
    return "logic-handoff-" + "--".join(document_ids)


def validate_manifest_file(path: str | Path) -> dict[str, Any]:
    return validate_manifest(load_manifest(path))


def validate_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[str] = []

    if manifest.get("schemaVersion") != 1:
        errors.append("schemaVersion must be 1")
    if manifest.get("manifestKind") != "processor_archive_integration_validation":
        errors.append("manifestKind must be processor_archive_integration_validation")
    if manifest.get("formalLogicExtractionReady") is not True:
        errors.append("formalLogicExtractionReady must be true")

    for flag in REQUIRED_FALSE_FLAGS:
        if manifest.get(flag) is not False:
            errors.append(f"{flag} must be false")

    archived_sources = manifest.get("archivedPublicSources")
    if not isinstance(archived_sources, list) or not archived_sources:
        errors.append("archivedPublicSources must be a non-empty list")
        archived_sources = []

    for marker in _forbidden_string_markers(manifest):
        errors.append(f"forbidden private, browser, download, or raw crawl marker present: {marker}")

    seen_sources: set[str] = set()
    seen_documents: set[str] = set()
    for index, source in enumerate(archived_sources):
        if not isinstance(source, Mapping):
            errors.append(f"archivedPublicSources[{index}] must be an object")
            continue
        errors.extend(_validate_source(index, source, seen_sources, seen_documents))

    expected_handoff_id = deterministic_handoff_id(archived_sources)
    if manifest.get("formalLogicHandoffId") != expected_handoff_id:
        errors.append("formalLogicHandoffId must be deterministic for archivedPublicSources")

    if errors:
        raise ArchiveManifestValidationError("; ".join(errors))
    return {
        "formalLogicHandoffId": expected_handoff_id,
        "archivedPublicSourceCount": len(archived_sources),
    }


def _validate_source(
    index: int,
    source: Mapping[str, Any],
    seen_sources: set[str],
    seen_documents: set[str],
) -> list[str]:
    errors: list[str] = []
    prefix = f"archivedPublicSources[{index}]"

    source_url = str(source.get("sourceUrl", ""))
    canonical_document_id = str(source.get("canonicalDocumentId", ""))
    archive_ref = str(source.get("archiveArtifactRef", ""))
    citations = source.get("citations")

    parsed = urlparse(source_url)
    if parsed.scheme != "https" or parsed.netloc not in PUBLIC_HOSTS:
        errors.append(f"{prefix}.sourceUrl must be a public PP&D HTTPS URL")
    if source_url in seen_sources:
        errors.append(f"{prefix}.sourceUrl must be unique")
    seen_sources.add(source_url)

    if not canonical_document_id.startswith("doc-"):
        errors.append(f"{prefix}.canonicalDocumentId must start with doc-")
    if canonical_document_id in seen_documents:
        errors.append(f"{prefix}.canonicalDocumentId must be unique")
    seen_documents.add(canonical_document_id)

    if not archive_ref.startswith("metadata_only_archive_manifests/") or not archive_ref.endswith(".json"):
        errors.append(f"{prefix}.archiveArtifactRef must be a metadata-only manifest ref")

    if not isinstance(citations, list) or not citations:
        errors.append(f"{prefix}.citations must include at least one citation")
    else:
        citation_urls: set[str] = set()
        for citation_index, citation in enumerate(citations):
            if not isinstance(citation, Mapping):
                errors.append(f"{prefix}.citations[{citation_index}] must be an object")
                continue
            citation_url = str(citation.get("url", ""))
            citation_urls.add(citation_url)
            if not citation.get("title") or not citation.get("evidenceId") or not citation.get("locator"):
                errors.append(f"{prefix}.citations[{citation_index}] needs title, evidenceId, and locator")
            parsed_citation = urlparse(citation_url)
            if parsed_citation.scheme != "https" or parsed_citation.netloc not in PUBLIC_HOSTS:
                errors.append(f"{prefix}.citations[{citation_index}].url must be a public PP&D HTTPS URL")
        if source_url not in citation_urls:
            errors.append(f"{prefix}.citations must cite the archived sourceUrl")

    processor_input = source.get("processorInput")
    if not isinstance(processor_input, Mapping):
        errors.append(f"{prefix}.processorInput must be an object")
    else:
        if processor_input.get("metadataOnly") is not True:
            errors.append(f"{prefix}.processorInput.metadataOnly must be true")
        if processor_input.get("persistRawBody") is not False:
            errors.append(f"{prefix}.processorInput.persistRawBody must be false")
        if processor_input.get("downloadDocuments") is not False:
            errors.append(f"{prefix}.processorInput.downloadDocuments must be false")

    return errors


def _forbidden_string_markers(value: Any) -> list[str]:
    found: list[str] = []

    def walk(item: Any) -> None:
        if isinstance(item, Mapping):
            for child in item.values():
                walk(child)
        elif isinstance(item, list):
            for child in item:
                walk(child)
        elif isinstance(item, str):
            lowered = item.lower()
            for marker in FORBIDDEN_TEXT_MARKERS:
                if marker in lowered and marker not in found:
                    found.append(marker)

    walk(value)
    return found
