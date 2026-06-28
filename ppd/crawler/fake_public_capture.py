"""Deterministic fake public-capture transport for PP&D tests.

The transport accepts approved synthetic crawl intentions and emits
ArchiveManifest-style metadata records. It never fetches URLs and never returns
or persists raw response bodies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Protocol, Sequence


class FakeCaptureError(ValueError):
    """Raised when a synthetic capture intention is unsafe or malformed."""


class PublicCaptureTransport(Protocol):
    """Minimal injectable capture interface used by PP&D crawl tests."""

    def capture(self, intention: Mapping[str, Any]) -> Dict[str, Any]:
        """Capture one approved synthetic intention as manifest metadata."""

    def capture_many(self, intentions: Iterable[Mapping[str, Any]]) -> List[Dict[str, Any]]:
        """Capture multiple approved synthetic intentions as manifest metadata."""


@dataclass(frozen=True)
class FakeProcessorMetadata:
    name: str = "ppd.fake_public_capture"
    version: str = "0.1"


@dataclass(frozen=True)
class FakePublicCaptureTransport:
    """Metadata-only fake transport for approved synthetic crawl intentions."""

    capture_started_at: str = "2026-05-15T00:00:00Z"
    capture_finished_at: str = "2026-05-15T00:00:00Z"
    processor: FakeProcessorMetadata = field(default_factory=FakeProcessorMetadata)

    def capture_many(self, intentions: Iterable[Mapping[str, Any]]) -> List[Dict[str, Any]]:
        return [self.capture(intention) for intention in intentions]

    def capture(self, intention: Mapping[str, Any]) -> Dict[str, Any]:
        _require_approved_synthetic_intention(intention)

        source_id = _required_text(intention, "source_id")
        requested_url = _required_text(intention, "requested_url")
        canonical_url = _optional_text(intention, "canonical_url") or requested_url
        http_status = _integer_field(intention, "http_status", 200)
        mime_type = _required_text(intention, "mime_type")
        redirect_chain = _redirect_chain(intention.get("redirect_chain"), requested_url, canonical_url, http_status)
        content_hash = _content_hash(intention)
        manifest_id = _stable_identifier("archive-manifest:fake", source_id, requested_url, content_hash)
        normalized_document_id = _optional_text(intention, "normalized_document_id") or _stable_identifier(
            "document:fake", source_id, canonical_url, content_hash
        )
        archive_artifact_ref = _optional_text(intention, "archive_artifact_ref") or _stable_identifier(
            "metadata-only", source_id, requested_url, content_hash
        )

        return {
            "manifest_id": manifest_id,
            "source_id": source_id,
            "canonical_url": canonical_url,
            "requested_url": requested_url,
            "redirect_chain": redirect_chain,
            "http_status": http_status,
            "content_type": mime_type,
            "mime_type": mime_type,
            "content_hash": content_hash,
            "capture_started_at": self.capture_started_at,
            "capture_finished_at": self.capture_finished_at,
            "processor_name": self.processor.name,
            "processor_version": self.processor.version,
            "processor_metadata": {
                "transport": "fake_public_capture",
                "network_requests_made": 0,
                "raw_body_persisted": False,
            },
            "archive_artifact_ref": archive_artifact_ref,
            "normalized_document_id": normalized_document_id,
            "skipped_reason": None,
            "no_raw_body_persisted": True,
        }


def load_fixture_intentions(path: Path) -> List[Dict[str, Any]]:
    """Load synthetic crawl intentions from a committed PP&D fixture file."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise FakeCaptureError("Fixture payload must be a JSON object.")

    intentions = payload.get("intentions")
    if not isinstance(intentions, list):
        raise FakeCaptureError("Fixture payload must include an intentions list.")

    loaded: List[Dict[str, Any]] = []
    for index, intention in enumerate(intentions):
        if not isinstance(intention, Mapping):
            raise FakeCaptureError("Fixture intention at index %d must be an object." % index)
        loaded.append(dict(intention))
    return loaded


def _require_approved_synthetic_intention(intention: Mapping[str, Any]) -> None:
    if intention.get("synthetic") is not True:
        raise FakeCaptureError("Fake public capture only accepts synthetic crawl intentions.")

    approved = intention.get("approved") is True
    approval = intention.get("approval")
    if isinstance(approval, Mapping):
        approved = approved or approval.get("status") == "approved"

    if not approved:
        raise FakeCaptureError("Fake public capture requires an approved synthetic crawl intention.")


def _required_text(values: Mapping[str, Any], key: str) -> str:
    value = values.get(key)
    if not isinstance(value, str) or not value.strip():
        raise FakeCaptureError("Missing required text field: %s" % key)
    return value


def _optional_text(values: Mapping[str, Any], key: str) -> str:
    value = values.get(key)
    if value is None:
        return ""
    if not isinstance(value, str):
        raise FakeCaptureError("Optional text field must be a string when present: %s" % key)
    return value


def _integer_field(values: Mapping[str, Any], key: str, default: int) -> int:
    value = values.get(key, default)
    if isinstance(value, bool):
        raise FakeCaptureError("Integer field must not be boolean: %s" % key)
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise FakeCaptureError("Invalid integer field: %s" % key) from exc


def _redirect_chain(value: Any, requested_url: str, canonical_url: str, http_status: int) -> List[Dict[str, Any]]:
    if value is None:
        if requested_url == canonical_url:
            return [{"url": requested_url, "status": http_status}]
        return [
            {"url": requested_url, "status": 302, "location": canonical_url},
            {"url": canonical_url, "status": http_status},
        ]

    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise FakeCaptureError("redirect_chain must be a list of redirect hop objects.")

    chain: List[Dict[str, Any]] = []
    for index, hop in enumerate(value):
        if not isinstance(hop, Mapping):
            raise FakeCaptureError("redirect_chain hop %d must be an object." % index)
        url = _required_text(hop, "url")
        status = _integer_field(hop, "status", http_status)
        normalized: Dict[str, Any] = {"url": url, "status": status}
        location = _optional_text(hop, "location")
        if location:
            normalized["location"] = location
        chain.append(normalized)

    if not chain:
        raise FakeCaptureError("redirect_chain must contain at least one hop.")
    return chain


def _content_hash(intention: Mapping[str, Any]) -> str:
    explicit_hash = _optional_text(intention, "content_hash")
    if explicit_hash:
        return explicit_hash

    body = intention.get("synthetic_body")
    if not isinstance(body, str):
        raise FakeCaptureError("A synthetic_body string or content_hash is required.")

    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    return "sha256:%s" % digest


def _stable_identifier(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("\u001f".join(parts).encode("utf-8")).hexdigest()[:24]
    return "%s:%s" % (prefix, digest)


__all__ = [
    "FakeCaptureError",
    "FakeProcessorMetadata",
    "FakePublicCaptureTransport",
    "PublicCaptureTransport",
    "load_fixture_intentions",
]
