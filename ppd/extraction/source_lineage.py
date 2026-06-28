"""Public-source lineage helpers for PP&D fixture-backed extraction.

The helpers in this module are intentionally side-effect-free: they only read
explicitly supplied committed fixture files and never attempt network access,
browser automation, or artifact creation.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse


class SourceLineageError(ValueError):
    """Raised when a fixture or source entry is not safe for public lineage."""


PUBLIC_SOURCE_TYPES = frozenset(
    {
        "public_html",
        "public_pdf",
        "public_form",
        "devhub_public",
        "external_reference",
    }
)

PUBLIC_HOST_ALLOWLIST = frozenset(
    {
        "www.portland.gov",
        "portland.gov",
        "devhub.portlandoregon.gov",
        "www.portlandoregon.gov",
        "portlandoregon.gov",
        "www.portlandmaps.com",
        "portlandmaps.com",
    }
)

_PRIVATE_PATH_MARKERS = frozenset(
    {
        ".auth",
        ".daemon",
        "auth-state",
        "auth_state",
        "browser-state",
        "cookies",
        "devhub-private",
        "har",
        "payment",
        "private",
        "raw-crawl",
        "screenshot",
        "session",
        "storage-state",
        "storagestate",
        "trace",
        "upload",
    }
)

_PRIVATE_URL_MARKERS = frozenset(
    {
        "account",
        "auth",
        "checkout",
        "login",
        "mypermits",
        "payment",
        "profile",
        "register",
        "session",
        "signin",
        "upload",
    }
)

_SENSITIVE_QUERY_KEYS = frozenset(
    {
        "access_token",
        "auth",
        "code",
        "cookie",
        "key",
        "password",
        "secret",
        "session",
        "state",
        "token",
    }
)

_FIXTURE_SUFFIXES = frozenset({".json"})


@dataclass(frozen=True)
class SourceLineage:
    """Normalized public source lineage for a committed PP&D fixture entry."""

    source_id: str
    canonical_url: str
    source_type: str
    title: str
    content_hash: str
    fixture_path: str
    evidence_id: str

    def to_dict(self) -> dict[str, str]:
        """Return a JSON-serializable representation."""

        return {
            "source_id": self.source_id,
            "canonical_url": self.canonical_url,
            "source_type": self.source_type,
            "title": self.title,
            "content_hash": self.content_hash,
            "fixture_path": self.fixture_path,
            "evidence_id": self.evidence_id,
        }


def load_public_source_lineage(
    fixture_path: str | Path,
    *,
    fixtures_root: str | Path | None = None,
) -> list[SourceLineage]:
    """Load public source lineage from a committed JSON fixture.

    The fixture may contain either a list of source entries or an object with a
    ``sources`` list. Each entry is validated before a ``SourceLineage`` object
    is returned.
    """

    path = _validate_fixture_path(Path(fixture_path), fixtures_root)
    payload = json.loads(path.read_text(encoding="utf-8"))
    entries = _extract_entries(payload)
    relative_path = _fixture_reference(path, fixtures_root)
    return [_lineage_from_entry(entry, relative_path) for entry in entries]


def public_source_lineage_dicts(
    fixture_path: str | Path,
    *,
    fixtures_root: str | Path | None = None,
) -> list[dict[str, str]]:
    """Load public source lineage and return plain dictionaries."""

    return [item.to_dict() for item in load_public_source_lineage(fixture_path, fixtures_root=fixtures_root)]


def _validate_fixture_path(path: Path, fixtures_root: str | Path | None) -> Path:
    resolved = path.expanduser().resolve(strict=True)
    if resolved.suffix.lower() not in _FIXTURE_SUFFIXES:
        raise SourceLineageError(f"unsupported lineage fixture suffix: {resolved.suffix}")

    parts = {part.lower() for part in resolved.parts}
    private_markers = parts.intersection(_PRIVATE_PATH_MARKERS)
    if private_markers:
        marker = sorted(private_markers)[0]
        raise SourceLineageError(f"private artifact path marker rejected: {marker}")

    if fixtures_root is not None:
        root = Path(fixtures_root).expanduser().resolve(strict=True)
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise SourceLineageError("lineage fixture must be under the supplied fixtures root") from exc

    return resolved


def _fixture_reference(path: Path, fixtures_root: str | Path | None) -> str:
    if fixtures_root is None:
        return path.name
    root = Path(fixtures_root).expanduser().resolve(strict=True)
    return path.relative_to(root).as_posix()


def _extract_entries(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        entries = payload
    elif isinstance(payload, dict) and isinstance(payload.get("sources"), list):
        entries = payload["sources"]
    else:
        raise SourceLineageError("lineage fixture must be a list or an object with a sources list")

    normalized: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise SourceLineageError("each source lineage entry must be an object")
        normalized.append(entry)
    return normalized


def _lineage_from_entry(entry: dict[str, Any], fixture_path: str) -> SourceLineage:
    source_id = _required_text(entry, "source_id")
    canonical_url = _required_text(entry, "canonical_url")
    source_type = _required_text(entry, "source_type")
    title = _required_text(entry, "title")
    content_hash = _content_hash(entry)

    _validate_source_type(source_type)
    _validate_public_url(canonical_url, source_type)

    evidence_id = _stable_evidence_id(source_id, canonical_url, content_hash)
    return SourceLineage(
        source_id=source_id,
        canonical_url=canonical_url,
        source_type=source_type,
        title=title,
        content_hash=content_hash,
        fixture_path=fixture_path,
        evidence_id=evidence_id,
    )


def _required_text(entry: dict[str, Any], key: str) -> str:
    value = entry.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SourceLineageError(f"missing required source lineage text field: {key}")
    return value.strip()


def _content_hash(entry: dict[str, Any]) -> str:
    value = entry.get("content_hash")
    if isinstance(value, str) and value.strip():
        return value.strip()

    text = entry.get("normalized_text")
    if not isinstance(text, str) or not text:
        raise SourceLineageError("source lineage entry requires content_hash or normalized_text")
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _validate_source_type(source_type: str) -> None:
    if source_type not in PUBLIC_SOURCE_TYPES:
        raise SourceLineageError(f"non-public source type rejected: {source_type}")


def _validate_public_url(canonical_url: str, source_type: str) -> None:
    parsed = urlparse(canonical_url)
    if parsed.scheme != "https":
        raise SourceLineageError("public lineage URLs must use https")

    host = (parsed.hostname or "").lower()
    if host not in PUBLIC_HOST_ALLOWLIST:
        raise SourceLineageError(f"source host is outside the PP&D public allowlist: {host}")

    if parsed.username or parsed.password:
        raise SourceLineageError("credentials in public lineage URLs are rejected")

    lower_path_parts = {part.lower() for part in parsed.path.split("/") if part}
    private_url_markers = lower_path_parts.intersection(_PRIVATE_URL_MARKERS)
    if private_url_markers:
        marker = sorted(private_url_markers)[0]
        raise SourceLineageError(f"private or authenticated URL path marker rejected: {marker}")

    query_keys = _query_keys(parsed.query)
    sensitive_keys = query_keys.intersection(_SENSITIVE_QUERY_KEYS)
    if sensitive_keys:
        key = sorted(sensitive_keys)[0]
        raise SourceLineageError(f"sensitive query parameter rejected: {key}")

    if host == "devhub.portlandoregon.gov" and source_type != "devhub_public":
        raise SourceLineageError("DevHub public URLs must use source_type devhub_public")


def _query_keys(query: str) -> set[str]:
    if not query:
        return set()
    return {part.split("=", 1)[0].lower() for part in query.split("&") if part}


def _stable_evidence_id(source_id: str, canonical_url: str, content_hash: str) -> str:
    digest = hashlib.sha256("\n".join((source_id, canonical_url, content_hash)).encode("utf-8")).hexdigest()
    return "evidence:" + digest[:24]


def lineage_index(lineage: Iterable[SourceLineage]) -> dict[str, SourceLineage]:
    """Index lineage entries by source_id and reject duplicates."""

    indexed: dict[str, SourceLineage] = {}
    for item in lineage:
        if item.source_id in indexed:
            raise SourceLineageError(f"duplicate source_id in lineage: {item.source_id}")
        indexed[item.source_id] = item
    return indexed
