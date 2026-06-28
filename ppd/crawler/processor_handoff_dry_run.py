"""Fixture-first processor handoff dry-run packets for PP&D recrawl batches.

This module intentionally performs no network I/O and invokes no processor code. It
maps a reviewed public recrawl fixture into the metadata packet PP&D expects to
hand to the processor boundary later: processor inputs, archive manifest metadata,
normalized document references, content hashes, processor versions, and
metadata-only output paths.
"""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any, Mapping
from urllib.parse import urlparse

ALLOWED_PUBLIC_HOSTS = frozenset(
    {
        "www.portland.gov",
        "devhub.portlandoregon.gov",
        "www.portlandoregon.gov",
        "www.portlandmaps.com",
    }
)

PRIVATE_DEVHUB_PREFIXES = (
    "/account",
    "/accounts",
    "/application",
    "/applications",
    "/cart",
    "/dashboard",
    "/document",
    "/documents",
    "/inspection",
    "/inspections",
    "/my",
    "/payment",
    "/payments",
    "/permit",
    "/permits",
    "/secure",
    "/session",
    "/sessions",
    "/upload",
    "/uploads",
)

RAW_OR_PRIVATE_KEYS = frozenset(
    {
        "body",
        "raw_body",
        "rawbody",
        "html",
        "text",
        "content",
        "bytes",
        "archive_path",
        "archivepath",
        "warc_path",
        "warcpath",
        "download_path",
        "downloadpath",
        "document_path",
        "documentpath",
        "pdf_path",
        "pdfpath",
        "local_path",
        "localpath",
        "screenshot_path",
        "screenshotpath",
        "trace_path",
        "tracepath",
        "har_path",
        "harpath",
        "cookie",
        "cookies",
        "credential",
        "credentials",
        "auth_state",
        "authstate",
        "session_state",
        "sessionstate",
    }
)

DEFAULT_PROCESSOR = {
    "name": "ipfs_datasets_py.web_archive_processor",
    "version": "fixture-pinned-2026-05-28",
    "module": "ipfs_datasets_py.processors.web_archiving",
    "operation": "capture_url_metadata_only",
}


def build_processor_handoff_dry_run_packet(
    reviewed_recrawl_batch: Mapping[str, Any],
    *,
    generated_at: str,
    processor: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a deterministic metadata-only handoff packet from a fixture batch."""

    processor_info = dict(DEFAULT_PROCESSOR)
    if processor is not None:
        processor_info.update(dict(processor))

    documents = reviewed_recrawl_batch.get("documents")
    if not isinstance(documents, list) or not documents:
        raise ValueError("reviewed recrawl batch requires a non-empty documents list")

    batch_id = _required_text(reviewed_recrawl_batch, "batchId")
    reviewed_at = _required_text(reviewed_recrawl_batch, "reviewedAt")
    reviewer = _required_text(reviewed_recrawl_batch, "reviewer")

    packet_documents: list[dict[str, Any]] = []
    for index, document in enumerate(documents):
        if not isinstance(document, Mapping):
            raise ValueError(f"documents[{index}] must be an object")
        packet_documents.append(
            _build_document_packet(
                batch_id=batch_id,
                reviewed_at=reviewed_at,
                reviewer=reviewer,
                processor_info=processor_info,
                document=document,
                index=index,
            )
        )

    packet = {
        "schemaVersion": 1,
        "packetType": "ppd_processor_handoff_dry_run",
        "generatedAt": generated_at,
        "sourceBatch": {
            "batchId": batch_id,
            "reviewedAt": reviewed_at,
            "reviewer": reviewer,
            "reviewStatus": _required_text(reviewed_recrawl_batch, "reviewStatus"),
            "publicOnly": True,
        },
        "executionPolicy": {
            "dryRun": True,
            "networkInvoked": False,
            "processorInvoked": False,
            "metadataOnly": True,
            "persistRawBody": False,
            "downloadDocuments": False,
        },
        "documents": packet_documents,
    }
    errors = validate_processor_handoff_dry_run_packet(packet)
    if errors:
        raise ValueError("processor handoff dry-run packet failed validation: " + "; ".join(errors))
    return packet


def validate_processor_handoff_dry_run_packet(packet: Mapping[str, Any]) -> list[str]:
    """Return validation errors for a handoff dry-run packet."""

    errors: list[str] = []
    if packet.get("schemaVersion") != 1:
        errors.append("schemaVersion must be 1")
    if packet.get("packetType") != "ppd_processor_handoff_dry_run":
        errors.append("packetType must be ppd_processor_handoff_dry_run")
    if not _is_utc_timestamp(packet.get("generatedAt")):
        errors.append("generatedAt must be an ISO UTC timestamp ending in Z")

    policy = _mapping(packet.get("executionPolicy"))
    expected_policy = {
        "dryRun": True,
        "networkInvoked": False,
        "processorInvoked": False,
        "metadataOnly": True,
        "persistRawBody": False,
        "downloadDocuments": False,
    }
    for key, expected in expected_policy.items():
        if policy.get(key) is not expected:
            errors.append(f"executionPolicy.{key} must be {str(expected).lower()}")

    source_batch = _mapping(packet.get("sourceBatch"))
    for key in ("batchId", "reviewedAt", "reviewer", "reviewStatus"):
        if not isinstance(source_batch.get(key), str) or not source_batch.get(key, "").strip():
            errors.append(f"sourceBatch.{key} is required")
    if source_batch.get("publicOnly") is not True:
        errors.append("sourceBatch.publicOnly must be true")

    documents = packet.get("documents")
    if not isinstance(documents, list) or not documents:
        errors.append("documents must be a non-empty list")
        return errors

    seen_input_ids: set[str] = set()
    seen_manifest_ids: set[str] = set()
    seen_document_ids: set[str] = set()
    for index, document in enumerate(documents):
        if not isinstance(document, Mapping):
            errors.append(f"documents[{index}] must be an object")
            continue
        errors.extend(_validate_document_packet(document, index, seen_input_ids, seen_manifest_ids, seen_document_ids))
    errors.extend(_reject_raw_or_private_keys(packet, "packet"))
    return errors


def _build_document_packet(
    *,
    batch_id: str,
    reviewed_at: str,
    reviewer: str,
    processor_info: Mapping[str, Any],
    document: Mapping[str, Any],
    index: int,
) -> dict[str, Any]:
    source_id = _required_text(document, "sourceId")
    canonical_url = _required_text(document, "canonicalUrl")
    requested_url = str(document.get("requestedUrl", canonical_url))
    content_hash = _required_text(document, "contentHash")
    document_id = _required_text(document, "normalizedDocumentId")
    manifest_id = f"archive-manifest-{source_id}"
    input_id = f"processor-input-{index + 1:03d}"

    _raise_if_not_public_https(canonical_url, "canonicalUrl")
    _raise_if_not_public_https(requested_url, "requestedUrl")
    if not content_hash.startswith("sha256:"):
        raise ValueError(f"{source_id}: contentHash must start with sha256:")

    archive_manifest_path = _metadata_path("processor_handoff_dry_run", batch_id, "archive_manifests", f"{source_id}.json")
    normalized_document_path = _metadata_path("processor_handoff_dry_run", batch_id, "normalized_documents", f"{document_id}.json")
    processor_input_path = _metadata_path("processor_handoff_dry_run", batch_id, "processor_inputs", f"{input_id}.json")

    processor_name = _required_text(processor_info, "name")
    processor_version = _required_text(processor_info, "version")
    processor_module = _required_text(processor_info, "module")
    processor_operation = _required_text(processor_info, "operation")

    return {
        "sourceId": source_id,
        "processorInput": {
            "inputId": input_id,
            "batchId": batch_id,
            "sourceId": source_id,
            "canonicalUrl": canonical_url,
            "requestedUrl": requested_url,
            "reviewedAt": reviewed_at,
            "reviewer": reviewer,
            "rateLimitBucket": f"public-host:{urlparse(canonical_url).hostname or 'unknown'}",
            "processor": {
                "name": processor_name,
                "version": processor_version,
                "module": processor_module,
                "operation": processor_operation,
            },
            "arguments": {
                "url": requested_url,
                "canonicalUrl": canonical_url,
                "metadataOnly": True,
                "persistRawBody": False,
                "downloadDocuments": False,
                "expectedContentHash": content_hash,
                "normalizedDocumentId": document_id,
                "archiveManifestId": manifest_id,
            },
        },
        "archiveManifestMetadata": {
            "manifestId": manifest_id,
            "sourceId": source_id,
            "canonicalUrl": canonical_url,
            "requestedUrl": requested_url,
            "redirectChain": list(document.get("redirectChain", [requested_url])),
            "httpStatus": int(document.get("httpStatus", 200)),
            "contentType": _required_text(document, "contentType"),
            "contentHash": content_hash,
            "captureStartedAt": reviewed_at,
            "captureFinishedAt": None,
            "processorName": processor_name,
            "processorVersion": processor_version,
            "archiveArtifactRef": archive_manifest_path,
            "normalizedDocumentId": document_id,
            "skippedReason": None,
            "noRawBodyPersisted": True,
        },
        "normalizedDocumentReference": {
            "documentId": document_id,
            "sourceId": source_id,
            "title": _required_text(document, "title"),
            "documentType": _required_text(document, "documentType"),
            "canonicalUrl": canonical_url,
            "contentHash": content_hash,
            "language": str(document.get("language", "en")),
            "outputPath": normalized_document_path,
            "contentPersisted": False,
        },
        "metadataOnlyOutputPaths": {
            "processorInputPath": processor_input_path,
            "archiveManifestPath": archive_manifest_path,
            "normalizedDocumentPath": normalized_document_path,
        },
    }


def _validate_document_packet(
    document: Mapping[str, Any],
    index: int,
    seen_input_ids: set[str],
    seen_manifest_ids: set[str],
    seen_document_ids: set[str],
) -> list[str]:
    errors: list[str] = []
    source_id = document.get("sourceId")
    if not isinstance(source_id, str) or not source_id.strip():
        errors.append(f"documents[{index}].sourceId is required")

    processor_input = _mapping(document.get("processorInput"))
    archive_manifest = _mapping(document.get("archiveManifestMetadata"))
    normalized_ref = _mapping(document.get("normalizedDocumentReference"))
    output_paths = _mapping(document.get("metadataOnlyOutputPaths"))

    input_id = processor_input.get("inputId")
    if not isinstance(input_id, str) or not input_id.strip():
        errors.append(f"documents[{index}].processorInput.inputId is required")
    elif input_id in seen_input_ids:
        errors.append(f"duplicate processor input id {input_id}")
    else:
        seen_input_ids.add(input_id)

    manifest_id = archive_manifest.get("manifestId")
    if not isinstance(manifest_id, str) or not manifest_id.strip():
        errors.append(f"documents[{index}].archiveManifestMetadata.manifestId is required")
    elif manifest_id in seen_manifest_ids:
        errors.append(f"duplicate archive manifest id {manifest_id}")
    else:
        seen_manifest_ids.add(manifest_id)

    document_id = normalized_ref.get("documentId")
    if not isinstance(document_id, str) or not document_id.strip():
        errors.append(f"documents[{index}].normalizedDocumentReference.documentId is required")
    elif document_id in seen_document_ids:
        errors.append(f"duplicate normalized document id {document_id}")
    else:
        seen_document_ids.add(document_id)

    for url_field in ("canonicalUrl", "requestedUrl"):
        errors.extend(_public_url_errors(processor_input.get(url_field), f"documents[{index}].processorInput.{url_field}"))
        errors.extend(_public_url_errors(archive_manifest.get(url_field), f"documents[{index}].archiveManifestMetadata.{url_field}"))
    errors.extend(_public_url_errors(normalized_ref.get("canonicalUrl"), f"documents[{index}].normalizedDocumentReference.canonicalUrl"))

    content_hash = archive_manifest.get("contentHash")
    if not isinstance(content_hash, str) or not content_hash.startswith("sha256:"):
        errors.append(f"documents[{index}].archiveManifestMetadata.contentHash must start with sha256:")
    if processor_input.get("arguments", {}).get("expectedContentHash") != content_hash:
        errors.append(f"documents[{index}] expectedContentHash must match archive manifest contentHash")
    if normalized_ref.get("contentHash") != content_hash:
        errors.append(f"documents[{index}] normalized reference contentHash must match archive manifest contentHash")

    processor = _mapping(processor_input.get("processor"))
    if not isinstance(processor.get("version"), str) or not processor.get("version", "").strip():
        errors.append(f"documents[{index}].processorInput.processor.version is required")
    if archive_manifest.get("processorVersion") != processor.get("version"):
        errors.append(f"documents[{index}] archive processorVersion must match processor input version")
    if archive_manifest.get("processorName") != processor.get("name"):
        errors.append(f"documents[{index}] archive processorName must match processor input name")
    if processor.get("operation") != "capture_url_metadata_only":
        errors.append(f"documents[{index}].processorInput.processor.operation must be capture_url_metadata_only")
    module = processor.get("module")
    if not isinstance(module, str) or not module.startswith("ipfs_datasets_py."):
        errors.append(f"documents[{index}].processorInput.processor.module must reference ipfs_datasets_py")

    arguments = _mapping(processor_input.get("arguments"))
    if arguments.get("metadataOnly") is not True:
        errors.append(f"documents[{index}].processorInput.arguments.metadataOnly must be true")
    if arguments.get("persistRawBody") is not False:
        errors.append(f"documents[{index}].processorInput.arguments.persistRawBody must be false")
    if arguments.get("downloadDocuments") is not False:
        errors.append(f"documents[{index}].processorInput.arguments.downloadDocuments must be false")
    if archive_manifest.get("noRawBodyPersisted") is not True:
        errors.append(f"documents[{index}].archiveManifestMetadata.noRawBodyPersisted must be true")
    if normalized_ref.get("contentPersisted") is not False:
        errors.append(f"documents[{index}].normalizedDocumentReference.contentPersisted must be false")

    for path_key in ("processorInputPath", "archiveManifestPath", "normalizedDocumentPath"):
        path_value = output_paths.get(path_key)
        if not _is_metadata_json_path(path_value):
            errors.append(f"documents[{index}].metadataOnlyOutputPaths.{path_key} must be a relative JSON metadata path")
    if archive_manifest.get("archiveArtifactRef") != output_paths.get("archiveManifestPath"):
        errors.append(f"documents[{index}] archiveArtifactRef must match metadataOnlyOutputPaths.archiveManifestPath")
    if normalized_ref.get("outputPath") != output_paths.get("normalizedDocumentPath"):
        errors.append(f"documents[{index}] normalized outputPath must match metadataOnlyOutputPaths.normalizedDocumentPath")

    return errors


def _required_text(data: Mapping[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} is required")
    return value


def _mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    return {}


def _metadata_path(*parts: str) -> str:
    return str(PurePosixPath("metadata_outputs", *parts))


def _is_metadata_json_path(value: Any) -> bool:
    if not isinstance(value, str) or not value.endswith(".json"):
        return False
    if value.startswith(("/", "./", "../", "~")):
        return False
    return value.startswith("metadata_outputs/")


def _is_utc_timestamp(value: Any) -> bool:
    return isinstance(value, str) and value.endswith("Z") and "T" in value


def _raise_if_not_public_https(value: str, field: str) -> None:
    errors = _public_url_errors(value, field)
    if errors:
        raise ValueError("; ".join(errors))


def _public_url_errors(value: Any, field: str) -> list[str]:
    if not isinstance(value, str) or not value.strip():
        return [f"{field} must be a non-empty URL string"]
    parsed = urlparse(value)
    if parsed.scheme != "https":
        return [f"{field} must use https"]
    host = parsed.hostname or ""
    if host not in ALLOWED_PUBLIC_HOSTS:
        return [f"{field} host is not PP&D allowlisted: {host}"]
    if host == "devhub.portlandoregon.gov":
        path = "/" + parsed.path.strip("/").lower()
        if any(path == prefix or path.startswith(prefix + "/") for prefix in PRIVATE_DEVHUB_PREFIXES):
            return [f"{field} must not reference private DevHub account paths"]
    return []


def _reject_raw_or_private_keys(value: Any, path: str) -> list[str]:
    errors: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized = key_text.replace("-", "_").lower()
            child_path = f"{path}.{key_text}"
            if normalized in RAW_OR_PRIVATE_KEYS:
                errors.append(f"{child_path} is not allowed in metadata-only dry-run packets")
            errors.extend(_reject_raw_or_private_keys(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_reject_raw_or_private_keys(child, f"{path}[{index}]"))
    return errors
