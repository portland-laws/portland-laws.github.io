"""Fixture-first metadata-only source index export for PP&D tests.

The exporter deliberately accepts only fixture-shaped metadata. It rejects raw
bodies, private URLs, local private paths, and hashes that are not declared by
the archive manifest or document records.
"""

from __future__ import annotations

import hashlib
import ipaddress
import json
import re
from pathlib import PurePosixPath, PureWindowsPath
from typing import Any
from urllib.parse import urlparse

_RAW_BODY_KEYS = {
    "body",
    "content",
    "html",
    "markdown",
    "ocr_text",
    "raw",
    "raw_body",
    "raw_html",
    "text",
}
_HASH_RE = re.compile(r"^[a-f0-9]{64}$")
_WINDOWS_DRIVE_RE = re.compile(r"^[a-zA-Z]:[\\/]")


class SourceIndexError(ValueError):
    """Raised when fixture metadata is unsafe or internally inconsistent."""


def export_fixture_source_index(fixture: dict[str, Any]) -> dict[str, Any]:
    """Return a deterministic metadata-only index from synthetic PP&D fixtures."""

    _reject_raw_bodies(fixture)
    registry = _mapping(fixture, "source_registry")
    manifest = _mapping(fixture, "archive_manifest")
    documents = _list(fixture, "document_records")
    citations = _list(fixture, "citation_integrity")

    declared_hashes = _declared_hashes(manifest, documents)
    records = [_index_record(document, registry, declared_hashes) for document in documents]
    citation_records = [_citation_record(citation, declared_hashes) for citation in citations]

    records.sort(key=lambda item: item["document_id"])
    citation_records.sort(key=lambda item: (item["document_id"], item["citation_id"]))

    return {
        "schema_version": "ppd-source-index-fixture-v1",
        "source_registry_id": _required_str(registry, "registry_id"),
        "archive_manifest_id": _required_str(manifest, "manifest_id"),
        "documents": records,
        "citations": citation_records,
        "index_sha256": _stable_hash(
            {
                "source_registry_id": _required_str(registry, "registry_id"),
                "archive_manifest_id": _required_str(manifest, "manifest_id"),
                "documents": records,
                "citations": citation_records,
            }
        ),
    }


def _index_record(
    document: dict[str, Any], registry: dict[str, Any], declared_hashes: set[str]
) -> dict[str, str]:
    document_id = _required_str(document, "document_id")
    source_id = _required_str(document, "source_id")
    sources = _mapping(registry, "sources")
    source = _mapping(sources, source_id)
    public_url = _required_str(document, "public_url")
    archive_path = _required_str(document, "archive_path")
    content_sha256 = _required_hash(document, "content_sha256")

    if content_sha256 not in declared_hashes:
        raise SourceIndexError(f"invented hash for {document_id}: {content_sha256}")
    _reject_private_url(public_url, f"document {document_id} public_url")
    _reject_private_path(archive_path, f"document {document_id} archive_path")

    return {
        "archive_path": archive_path,
        "content_sha256": content_sha256,
        "document_id": document_id,
        "jurisdiction": _required_str(source, "jurisdiction"),
        "public_url": public_url,
        "source_id": source_id,
        "source_title": _required_str(source, "title"),
    }


def _citation_record(citation: dict[str, Any], declared_hashes: set[str]) -> dict[str, str]:
    citation_id = _required_str(citation, "citation_id")
    document_id = _required_str(citation, "document_id")
    content_sha256 = _required_hash(citation, "content_sha256")
    if content_sha256 not in declared_hashes:
        raise SourceIndexError(f"invented citation hash for {citation_id}: {content_sha256}")
    return {
        "citation_id": citation_id,
        "content_sha256": content_sha256,
        "document_id": document_id,
        "locator": _required_str(citation, "locator"),
    }


def _declared_hashes(manifest: dict[str, Any], documents: list[dict[str, Any]]) -> set[str]:
    hashes: set[str] = set()
    for entry in _list(manifest, "entries"):
        hashes.add(_required_hash(entry, "content_sha256"))
    for document in documents:
        hashes.add(_required_hash(document, "content_sha256"))
    return hashes


def _reject_raw_bodies(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in _RAW_BODY_KEYS:
                raise SourceIndexError(f"raw body field is not allowed at {path}.{key}")
            _reject_raw_bodies(nested, f"{path}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _reject_raw_bodies(nested, f"{path}[{index}]")


def _reject_private_url(url: str, label: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
        raise SourceIndexError(f"{label} must be an http(s) URL")
    host = parsed.hostname or ""
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        lowered = host.lower()
        if lowered in {"localhost", "0.0.0.0"} or lowered.endswith(".local"):
            raise SourceIndexError(f"{label} uses a private host")
        return
    if address.is_private or address.is_loopback or address.is_link_local:
        raise SourceIndexError(f"{label} uses a private address")


def _reject_private_path(path: str, label: str) -> None:
    if path.startswith("~") or _WINDOWS_DRIVE_RE.match(path):
        raise SourceIndexError(f"{label} uses a local private path")
    if PureWindowsPath(path).is_absolute() or PurePosixPath(path).is_absolute():
        raise SourceIndexError(f"{label} uses an absolute local path")
    if ".." in PurePosixPath(path).parts or ".." in PureWindowsPath(path).parts:
        raise SourceIndexError(f"{label} escapes fixture storage")


def _mapping(value: dict[str, Any], key: str) -> dict[str, Any]:
    nested = value.get(key)
    if not isinstance(nested, dict):
        raise SourceIndexError(f"{key} must be an object")
    return nested


def _list(value: dict[str, Any], key: str) -> list[dict[str, Any]]:
    nested = value.get(key)
    if not isinstance(nested, list) or not all(isinstance(item, dict) for item in nested):
        raise SourceIndexError(f"{key} must be a list of objects")
    return nested


def _required_str(value: dict[str, Any], key: str) -> str:
    nested = value.get(key)
    if not isinstance(nested, str) or not nested:
        raise SourceIndexError(f"{key} must be a non-empty string")
    return nested


def _required_hash(value: dict[str, Any], key: str) -> str:
    digest = _required_str(value, key)
    if not _HASH_RE.match(digest):
        raise SourceIndexError(f"{key} must be a sha256 hex digest")
    return digest


def _stable_hash(value: dict[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
