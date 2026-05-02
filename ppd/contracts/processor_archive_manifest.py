"""Offline validation for PP&D processor archive handoff manifests.

The handoff manifest proves that PP&D can reference archive outputs created by
ipfs_datasets_py processors while keeping only commit-safe provenance. It links
processor provenance to an existing PP&D source-index record and to a stable
normalized document identifier. It must not include raw crawl output, response
bodies, downloaded documents, browser traces, credentials, or private DevHub
artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urldefrag, urlparse


IPFS_DATASETS_PROCESSOR_BACKEND = "ipfs_datasets_py/ipfs_datasets_py/processors"
SHA256_PREFIX = "sha256:"
SHA256_HEX_LENGTH = 64
ALLOWED_PROCESSOR_FAMILIES = {
    "web_archiving",
    "legal_scraper",
    "website_graphrag",
    "advanced_graphrag",
    "specialized_scraper",
    "pdf_normalization",
}
FORBIDDEN_ARTIFACT_FIELDS = (
    "rawCrawlOutputPath",
    "privateDevhubArtifactPath",
    "downloadedDocumentPath",
    "tracePath",
    "screenshotPath",
    "authStatePath",
)


@dataclass(frozen=True)
class ProcessorArchiveHandoffRecord:
    id: str
    archive_record_id: str
    source_index_record_id: str
    source_url: str
    canonical_url: str
    content_hash: str
    normalized_document_id: str
    normalized_content_hash: str
    processor_backend_path: str
    processor_name: str
    processor_family: str
    processor_version: str
    processor_source_module: str
    capture_timestamp: str
    manifest_only: bool
    response_body_included: bool
    forbidden_artifact_paths: tuple[str, ...]


def validate_processor_archive_manifest(
    manifest: Mapping[str, Any],
    source_index_records: Mapping[str, Mapping[str, Any]],
) -> list[str]:
    """Validate an offline processor archive handoff manifest.

    ``source_index_records`` is keyed by source-index record id. The validator
    intentionally accepts already-loaded JSON data so tests and daemon checks can
    run without network, crawl output, or repository-root fixture assumptions.
    """

    errors: list[str] = []
    if manifest.get("schemaVersion") != 1:
        errors.append("processor archive manifest schemaVersion must be 1")
    if manifest.get("fixtureKind") != "processor_archive_handoff_manifest":
        errors.append("processor archive manifest fixtureKind must be processor_archive_handoff_manifest")
    generated_at = manifest.get("generatedAt")
    if not isinstance(generated_at, str) or not generated_at.endswith("Z"):
        errors.append("processor archive manifest generatedAt must be an ISO UTC timestamp ending in Z")

    raw_records = manifest.get("records")
    if not isinstance(raw_records, list) or not raw_records:
        errors.append("processor archive manifest records must be a non-empty array")
        return errors

    seen_ids: set[str] = set()
    for index, raw_record in enumerate(raw_records):
        if not isinstance(raw_record, Mapping):
            errors.append(f"records[{index}] must be an object")
            continue
        record = processor_archive_handoff_record_from_dict(raw_record)
        prefix = f"record {record.id or index}"
        if not record.id:
            errors.append(f"records[{index}].id is required")
        elif record.id in seen_ids:
            errors.append(f"duplicate processor archive handoff record id {record.id}")
        seen_ids.add(record.id)
        errors.extend(f"{prefix}: {error}" for error in _validate_record(record, source_index_records))
    return errors


def processor_archive_handoff_record_from_dict(data: Mapping[str, Any]) -> ProcessorArchiveHandoffRecord:
    processor = data.get("processorProvenance")
    if not isinstance(processor, Mapping):
        processor = {}
    normalized = data.get("normalizedDocument")
    if not isinstance(normalized, Mapping):
        normalized = {}
    forbidden_artifacts = data.get("forbiddenArtifacts")
    if not isinstance(forbidden_artifacts, Mapping):
        forbidden_artifacts = {}

    paths: list[str] = []
    for field in FORBIDDEN_ARTIFACT_FIELDS:
        value = forbidden_artifacts.get(field)
        if value is not None:
            paths.append(str(value))

    return ProcessorArchiveHandoffRecord(
        id=str(data.get("id", "")),
        archive_record_id=str(data.get("archiveRecordId", "")),
        source_index_record_id=str(data.get("sourceIndexRecordId", "")),
        source_url=str(data.get("sourceUrl", "")),
        canonical_url=str(data.get("canonicalUrl", "")),
        content_hash=str(data.get("contentHash", "")),
        normalized_document_id=str(normalized.get("id", "")),
        normalized_content_hash=str(normalized.get("contentHash", "")),
        processor_backend_path=str(processor.get("backendPath", "")),
        processor_name=str(processor.get("name", "")),
        processor_family=str(processor.get("family", "")),
        processor_version=str(processor.get("version", "")),
        processor_source_module=str(processor.get("sourceModule", "")),
        capture_timestamp=str(processor.get("captureTimestamp", "")),
        manifest_only=bool(processor.get("manifestOnly", False)),
        response_body_included=bool(forbidden_artifacts.get("responseBodyIncluded", False)),
        forbidden_artifact_paths=tuple(paths),
    )


def _validate_record(
    record: ProcessorArchiveHandoffRecord,
    source_index_records: Mapping[str, Mapping[str, Any]],
) -> list[str]:
    errors: list[str] = []
    if not record.archive_record_id.strip():
        errors.append("archiveRecordId is required")
    errors.extend(_validate_https_url(record.source_url, "sourceUrl"))
    errors.extend(_validate_https_url(record.canonical_url, "canonicalUrl"))
    errors.extend(_validate_content_hash(record.content_hash, "contentHash"))
    errors.extend(_validate_content_hash(record.normalized_content_hash, "normalizedDocument.contentHash"))
    errors.extend(_validate_normalized_document_id(record.normalized_document_id))

    if record.source_index_record_id not in source_index_records:
        errors.append(f"sourceIndexRecordId {record.source_index_record_id!r} does not reference a committed source-index record")
    else:
        source_record = source_index_records[record.source_index_record_id]
        if source_record.get("sourceUrl") != record.source_url:
            errors.append("sourceUrl must match the referenced source-index record")
        if source_record.get("canonicalUrl") != record.canonical_url:
            errors.append("canonicalUrl must match the referenced source-index record")
        if source_record.get("contentHash") != record.content_hash:
            errors.append("contentHash must match the referenced source-index record")

    if record.processor_backend_path != IPFS_DATASETS_PROCESSOR_BACKEND:
        errors.append("processor backendPath must reference the read-only ipfs_datasets_py processor suite")
    if not record.processor_name.strip():
        errors.append("processorProvenance.name is required")
    if record.processor_family not in ALLOWED_PROCESSOR_FAMILIES:
        errors.append("processorProvenance.family is not an allowed ipfs_datasets_py processor family")
    if not record.processor_version.strip():
        errors.append("processorProvenance.version is required")
    if not record.processor_source_module.startswith("ipfs_datasets_py.ipfs_datasets_py.processors."):
        errors.append("processorProvenance.sourceModule must stay under ipfs_datasets_py.ipfs_datasets_py.processors")
    if not record.capture_timestamp.endswith("Z"):
        errors.append("processorProvenance.captureTimestamp must be an ISO UTC timestamp ending in Z")
    if not record.manifest_only:
        errors.append("processorProvenance.manifestOnly must be true")
    if record.response_body_included:
        errors.append("forbiddenArtifacts.responseBodyIncluded must be false")
    for path in record.forbidden_artifact_paths:
        errors.append(f"forbidden artifact path must not be present: {path}")
    return errors


def _validate_https_url(value: str, field: str) -> list[str]:
    parsed = urlparse(value)
    errors: list[str] = []
    if parsed.scheme != "https" or not parsed.netloc:
        errors.append(f"{field} must be an HTTPS URL with a hostname")
    if urldefrag(value).fragment:
        errors.append(f"{field} must not include a fragment")
    return errors


def _validate_content_hash(value: str, field: str) -> list[str]:
    if not value.startswith(SHA256_PREFIX):
        return [f"{field} must use sha256: format"]
    digest = value[len(SHA256_PREFIX) :]
    if len(digest) != SHA256_HEX_LENGTH:
        return [f"{field} sha256 digest must be 64 lowercase hex characters"]
    if any(character not in "0123456789abcdef" for character in digest):
        return [f"{field} sha256 digest must be lowercase hex"]
    return []


def _validate_normalized_document_id(value: str) -> list[str]:
    if not value.strip():
        return ["normalizedDocument.id is required"]
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789-_")
    if any(character not in allowed for character in value):
        return ["normalizedDocument.id must be a stable lowercase identifier, not a path or URL"]
    if value.startswith("http") or "/" in value or "\\" in value:
        return ["normalizedDocument.id must not be a URL or filesystem path"]
    return []
