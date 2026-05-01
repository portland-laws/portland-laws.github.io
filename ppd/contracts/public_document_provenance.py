"""Fixture-only provenance validation for normalized public PP&D documents.

The validator intentionally accepts plain JSON-like dictionaries so fixture tests can
check provenance without widening stable normalized-document contracts. It verifies
that each normalized HTML or PDF record can be traced back to one source-index entry
by source index id, canonical URL, retrieval timestamp, and checksum/content hash.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping, Sequence


SUPPORTED_PUBLIC_DOCUMENT_TYPES = {"html", "text/html", "pdf", "application/pdf"}
CANONICAL_URL_KEYS = ("canonical_url", "canonicalUrl", "url")
RETRIEVED_AT_KEYS = ("retrieved_at", "retrievedAt", "retrieval_timestamp", "retrievalTimestamp", "captured_at", "capturedAt")
CHECKSUM_KEYS = ("checksum", "content_hash", "contentHash", "sha256")
SOURCE_INDEX_ID_KEYS = ("source_index_id", "sourceIndexId", "source_index_record_id", "sourceIndexRecordId")
DOCUMENT_TYPE_KEYS = ("document_type", "documentType", "content_type", "contentType", "media_type", "mediaType")
SOURCE_INDEX_TIME_KEYS = ("retrieved_at", "retrievedAt", "last_seen_at", "lastSeenAt", "captured_at", "capturedAt")
SOURCE_INDEX_HASH_KEYS = ("content_hash", "contentHash", "checksum", "sha256")
SOURCE_INDEX_ID_FIELD_KEYS = ("id", "source_index_id", "sourceIndexId", "record_id", "recordId")


@dataclass(frozen=True)
class PublicDocumentProvenanceFinding:
    document_id: str
    field: str
    reason: str


def validate_public_document_provenance(
    normalized_documents: Sequence[Mapping[str, Any]],
    source_index_records: Sequence[Mapping[str, Any]],
) -> list[PublicDocumentProvenanceFinding]:
    """Return provenance findings for normalized public document fixtures."""

    source_records_by_id = _index_source_records(source_index_records)
    findings: list[PublicDocumentProvenanceFinding] = []

    for document in normalized_documents:
        document_id = str(document.get("id") or document.get("document_id") or "")
        document_type = _normalized_document_type(document)
        if document_type not in SUPPORTED_PUBLIC_DOCUMENT_TYPES:
            findings.append(
                PublicDocumentProvenanceFinding(
                    document_id=document_id,
                    field="document_type",
                    reason="normalized public document must be HTML or PDF",
                )
            )

        source_index_id = _first_string(document, SOURCE_INDEX_ID_KEYS)
        if not source_index_id:
            findings.append(
                PublicDocumentProvenanceFinding(
                    document_id=document_id,
                    field="source_index_id",
                    reason="normalized document must name its source-index entry",
                )
            )
            continue

        source_record = source_records_by_id.get(source_index_id)
        if source_record is None:
            findings.append(
                PublicDocumentProvenanceFinding(
                    document_id=document_id,
                    field="source_index_id",
                    reason=f"source-index entry {source_index_id!r} was not found",
                )
            )
            continue

        findings.extend(_validate_url_tie(document_id, document, source_record))
        findings.extend(_validate_timestamp_tie(document_id, document, source_record))
        findings.extend(_validate_checksum_tie(document_id, document, source_record))

    return findings


def assert_public_document_provenance(
    normalized_documents: Sequence[Mapping[str, Any]],
    source_index_records: Sequence[Mapping[str, Any]],
) -> None:
    """Raise ValueError when fixture provenance cannot be traced to source index."""

    findings = validate_public_document_provenance(normalized_documents, source_index_records)
    if findings:
        details = "; ".join(f"{finding.document_id}.{finding.field}: {finding.reason}" for finding in findings)
        raise ValueError(f"public document provenance validation failed: {details}")


def _validate_url_tie(
    document_id: str,
    document: Mapping[str, Any],
    source_record: Mapping[str, Any],
) -> list[PublicDocumentProvenanceFinding]:
    findings: list[PublicDocumentProvenanceFinding] = []
    document_url = _first_string(document, CANONICAL_URL_KEYS)
    source_url = _first_string(source_record, CANONICAL_URL_KEYS)

    if not document_url:
        findings.append(
            PublicDocumentProvenanceFinding(
                document_id=document_id,
                field="canonical_url",
                reason="normalized document must include canonical URL",
            )
        )
        return findings

    if not source_url:
        findings.append(
            PublicDocumentProvenanceFinding(
                document_id=document_id,
                field="source_index.canonical_url",
                reason="source-index entry must include canonical URL",
            )
        )
        return findings

    if document_url != source_url:
        findings.append(
            PublicDocumentProvenanceFinding(
                document_id=document_id,
                field="canonical_url",
                reason="normalized document canonical URL must match source-index canonical URL",
            )
        )

    return findings


def _validate_timestamp_tie(
    document_id: str,
    document: Mapping[str, Any],
    source_record: Mapping[str, Any],
) -> list[PublicDocumentProvenanceFinding]:
    findings: list[PublicDocumentProvenanceFinding] = []
    document_time = _first_string(document, RETRIEVED_AT_KEYS)
    source_time = _first_string(source_record, SOURCE_INDEX_TIME_KEYS)

    if not document_time:
        findings.append(
            PublicDocumentProvenanceFinding(
                document_id=document_id,
                field="retrieved_at",
                reason="normalized document must include retrieval timestamp",
            )
        )
        return findings

    if _parse_utc_timestamp(document_time) is None:
        findings.append(
            PublicDocumentProvenanceFinding(
                document_id=document_id,
                field="retrieved_at",
                reason="retrieval timestamp must be an ISO-8601 UTC timestamp ending in Z",
            )
        )

    if not source_time:
        findings.append(
            PublicDocumentProvenanceFinding(
                document_id=document_id,
                field="source_index.retrieved_at",
                reason="source-index entry must include retrieval or last-seen timestamp",
            )
        )
        return findings

    if document_time != source_time:
        findings.append(
            PublicDocumentProvenanceFinding(
                document_id=document_id,
                field="retrieved_at",
                reason="normalized document retrieval timestamp must match source-index timestamp",
            )
        )

    return findings


def _validate_checksum_tie(
    document_id: str,
    document: Mapping[str, Any],
    source_record: Mapping[str, Any],
) -> list[PublicDocumentProvenanceFinding]:
    findings: list[PublicDocumentProvenanceFinding] = []
    document_checksum = _first_string(document, CHECKSUM_KEYS)
    source_checksum = _first_string(source_record, SOURCE_INDEX_HASH_KEYS)

    if not document_checksum:
        findings.append(
            PublicDocumentProvenanceFinding(
                document_id=document_id,
                field="checksum",
                reason="normalized document must include checksum",
            )
        )
        return findings

    if not _looks_like_sha256(document_checksum):
        findings.append(
            PublicDocumentProvenanceFinding(
                document_id=document_id,
                field="checksum",
                reason="checksum must be a sha256 digest or sha256-prefixed digest",
            )
        )

    if not source_checksum:
        findings.append(
            PublicDocumentProvenanceFinding(
                document_id=document_id,
                field="source_index.content_hash",
                reason="source-index entry must include content hash",
            )
        )
        return findings

    if _strip_sha256_prefix(document_checksum) != _strip_sha256_prefix(source_checksum):
        findings.append(
            PublicDocumentProvenanceFinding(
                document_id=document_id,
                field="checksum",
                reason="normalized document checksum must match source-index content hash",
            )
        )

    return findings


def _index_source_records(records: Iterable[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    indexed: dict[str, Mapping[str, Any]] = {}
    for record in records:
        record_id = _first_string(record, SOURCE_INDEX_ID_FIELD_KEYS)
        if record_id:
            indexed[record_id] = record
    return indexed


def _normalized_document_type(document: Mapping[str, Any]) -> str:
    value = _first_string(document, DOCUMENT_TYPE_KEYS)
    return value.lower().strip() if value else ""


def _first_string(record: Mapping[str, Any], keys: Sequence[str]) -> str | None:
    for key in keys:
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _parse_utc_timestamp(value: str) -> datetime | None:
    if not value.endswith("Z"):
        return None
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return None
    if parsed.tzinfo != timezone.utc:
        return None
    return parsed


def _looks_like_sha256(value: str) -> bool:
    digest = _strip_sha256_prefix(value)
    return len(digest) == 64 and all(character in "0123456789abcdef" for character in digest)


def _strip_sha256_prefix(value: str) -> str:
    lowered = value.lower().strip()
    if lowered.startswith("sha256:"):
        return lowered.removeprefix("sha256:")
    return lowered
