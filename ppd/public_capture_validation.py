"""Validation for deterministic fake public-capture transport payloads.

The fake transport is allowed to model public metadata only.  It must not
smuggle authenticated URLs, local paths, downloaded files, raw response bodies,
or hashes for records that were intentionally skipped.
"""

from __future__ import annotations

import ipaddress
from pathlib import PurePosixPath
from typing import Any, Mapping
from urllib.parse import unquote, urlparse


RAW_BODY_FIELDS = frozenset({"body", "raw_body", "response_body", "html", "text", "content", "bytes"})
DOWNLOADED_PATH_FIELDS = frozenset({"downloaded_pdf_path", "pdf_path", "download_path", "local_pdf_path"})
HASH_FIELDS = frozenset({"sha256", "sha256_hex", "content_sha256", "digest", "hash"})
PRIVATE_PATH_PREFIXES = ("/private/", "/admin/", "/auth/", "/login", "/oauth", "/sso", "/session")
LOCAL_PATH_PREFIXES = ("/tmp/", "/var/tmp/", "/private/", "/home/", "/Users/", "~", "./", "../")


class PublicCaptureValidationError(ValueError):
    """Raised when a fake public-capture payload contains unsafe evidence."""


def validate_fake_public_capture(payload: Mapping[str, Any]) -> None:
    """Validate a fake public-capture payload.

    The function mutates nothing and raises ``PublicCaptureValidationError`` with
    a deterministic message for the first rejected field.
    """

    if not isinstance(payload, Mapping):
        raise PublicCaptureValidationError("capture payload must be a mapping")

    source_id = payload.get("source_id")
    if not isinstance(source_id, str) or not source_id.strip():
        raise PublicCaptureValidationError("capture payload is missing source_id")

    processor = payload.get("processor")
    if not isinstance(processor, Mapping):
        raise PublicCaptureValidationError("capture payload is missing processor metadata")
    processor_name = processor.get("name")
    processor_version = processor.get("version")
    if not isinstance(processor_name, str) or not processor_name.strip():
        raise PublicCaptureValidationError("processor metadata is missing name")
    if not isinstance(processor_version, str) or not processor_version.strip():
        raise PublicCaptureValidationError("processor metadata is missing version")

    _walk(payload, ())

    status = str(payload.get("status", "")).lower()
    skipped = bool(payload.get("skipped")) or status == "skipped"
    if skipped:
        for field in HASH_FIELDS:
            if payload.get(field):
                raise PublicCaptureValidationError("skipped captures must not include invented hashes")


def _walk(value: Any, path: tuple[str, ...]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            lowered = key_text.lower()
            child_path = path + (key_text,)
            if lowered in RAW_BODY_FIELDS:
                raise PublicCaptureValidationError(f"raw body field is not allowed: {'.'.join(child_path)}")
            if lowered in DOWNLOADED_PATH_FIELDS:
                raise PublicCaptureValidationError(f"downloaded PDF path is not allowed: {'.'.join(child_path)}")
            if lowered.endswith("url") or lowered == "url":
                _validate_public_url(child, child_path)
            if lowered.endswith("path") or lowered in {"path", "file"}:
                _validate_not_local_private_path(child, child_path)
            _walk(child, child_path)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _walk(item, path + (str(index),))


def _validate_public_url(value: Any, path: tuple[str, ...]) -> None:
    if not isinstance(value, str) or not value.strip():
        raise PublicCaptureValidationError(f"URL field must be a non-empty string: {'.'.join(path)}")
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"}:
        raise PublicCaptureValidationError(f"URL must use http or https: {'.'.join(path)}")
    if not parsed.hostname:
        raise PublicCaptureValidationError(f"URL is missing host: {'.'.join(path)}")
    host = parsed.hostname.lower()
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".localhost"):
        raise PublicCaptureValidationError(f"private host is not allowed: {'.'.join(path)}")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address and (address.is_private or address.is_loopback or address.is_link_local or address.is_reserved):
        raise PublicCaptureValidationError(f"private host is not allowed: {'.'.join(path)}")
    decoded_path = unquote(parsed.path).lower()
    if any(decoded_path.startswith(prefix) for prefix in PRIVATE_PATH_PREFIXES):
        raise PublicCaptureValidationError(f"authenticated URL path is not allowed: {'.'.join(path)}")


def _validate_not_local_private_path(value: Any, path: tuple[str, ...]) -> None:
    if not isinstance(value, str) or not value:
        return
    normalized = value.replace("\\", "/")
    lowered = normalized.lower()
    if lowered.endswith(".pdf") and (normalized.startswith("/") or normalized.startswith(".") or normalized.startswith("~")):
        raise PublicCaptureValidationError(f"downloaded PDF path is not allowed: {'.'.join(path)}")
    if normalized.startswith(LOCAL_PATH_PREFIXES):
        raise PublicCaptureValidationError(f"local private path is not allowed: {'.'.join(path)}")
    parts = PurePosixPath(normalized).parts
    if ".." in parts:
        raise PublicCaptureValidationError(f"local private path is not allowed: {'.'.join(path)}")
