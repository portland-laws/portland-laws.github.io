"""Validation for PP&D evidence freshness watchlist packets.

The validator is intentionally deterministic and offline-only. It checks packet
metadata and references before any automation can treat the packet as eligible
for review or processing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable
from urllib.parse import urlparse


ALLOWLISTED_HOSTS = {
    "portland.gov",
    "www.portland.gov",
    "efiles.portlandoregon.gov",
}

AUTH_QUERY_MARKERS = {
    "access_token",
    "api_key",
    "apikey",
    "auth",
    "bearer",
    "client_secret",
    "code",
    "jwt",
    "key",
    "oauth",
    "password",
    "refresh_token",
    "session",
    "sid",
    "signature",
    "token",
}

RAW_REFERENCE_MARKERS = (
    "raw_body",
    "raw_html",
    "raw_text",
    "downloaded_body",
    "downloaded_file",
    "archive_body",
    "archive_url",
    "warc",
)

RAW_URL_SEGMENTS = {
    "archive",
    "download",
    "raw",
    "raw-body",
    "raw-html",
    "snapshot",
    "warc",
}

LIVE_EXECUTION_MARKERS = (
    "live crawl",
    "live-crawl",
    "live processor",
    "processor executed",
    "executed processor",
    "ran crawler",
    "ran processor",
)

OUTCOME_GUARANTEE_MARKERS = (
    "approval guaranteed",
    "approved guaranteed",
    "guarantee approval",
    "guarantees approval",
    "guarantee permit",
    "guarantees permit",
    "permit will be approved",
    "permit outcome guaranteed",
    "legal outcome guaranteed",
)

MUTATION_FLAGS = (
    "mutates_registry",
    "registry_mutation",
    "mutates_requirements",
    "requirement_mutation",
    "mutates_guardrails",
    "guardrail_mutation",
    "mutates_schedule",
    "schedule_mutation",
    "mutates_release_state",
    "release_state_mutation",
    "active_registry_mutation",
    "active_requirement_mutation",
    "active_guardrail_mutation",
    "active_schedule_mutation",
    "active_release_state_mutation",
)

REFERENCE_FIELDS = (
    "source_refs",
    "requirement_refs",
    "guardrail_refs",
)


@dataclass(frozen=True)
class WatchlistValidationResult:
    """Result returned by :func:`validate_watchlist_packet`."""

    ok: bool
    errors: tuple[str, ...]


def validate_watchlist_packet(packet: dict[str, Any]) -> WatchlistValidationResult:
    """Validate a PP&D evidence freshness watchlist packet.

    The packet must be fully cited, owned for offline review, limited to public
    allowlisted URLs, and free of execution claims, outcome guarantees, raw
    body/download/archive references, and active mutation flags.
    """

    errors: list[str] = []

    if not isinstance(packet, dict):
        return WatchlistValidationResult(False, ("packet must be an object",))

    cited_ids = _cited_reference_ids(packet)
    for field in REFERENCE_FIELDS:
        for ref in _as_list(packet.get(field)):
            ref_id = _ref_id(ref)
            if not ref_id:
                errors.append(f"{field} contains an empty reference")
            elif ref_id not in cited_ids:
                errors.append(f"{field} reference is uncited: {ref_id}")

    if not _as_list(packet.get("offline_review_triggers")):
        errors.append("offline_review_triggers must contain at least one trigger")

    reviewers = _as_list(packet.get("reviewers"))
    if not reviewers:
        errors.append("reviewers must contain at least one reviewer owner")
    else:
        for index, reviewer in enumerate(reviewers):
            owner = reviewer.get("owner") if isinstance(reviewer, dict) else reviewer
            if not isinstance(owner, str) or not owner.strip():
                errors.append(f"reviewers[{index}] is missing an owner")

    for key, value in _walk(packet):
        lowered_key = key.lower()
        if lowered_key in RAW_REFERENCE_MARKERS and value:
            errors.append(f"raw/download/archive reference is not allowed: {key}")
        if lowered_key in MUTATION_FLAGS and value is True:
            errors.append(f"active mutation flag is not allowed: {key}")
        if lowered_key in {"live_crawl", "live_processor", "processor_executed", "crawler_executed"} and value is True:
            errors.append(f"live crawl or processor execution claim is not allowed: {key}")
        if isinstance(value, str):
            text = value.lower()
            if _looks_like_url(value):
                errors.extend(_validate_url(value, key))
            if any(marker in text for marker in LIVE_EXECUTION_MARKERS):
                errors.append(f"live crawl or processor execution claim is not allowed: {key}")
            if any(marker in text for marker in OUTCOME_GUARANTEE_MARKERS):
                errors.append(f"legal or permitting outcome guarantee is not allowed: {key}")

    return WatchlistValidationResult(not errors, tuple(errors))


def require_valid_watchlist_packet(packet: dict[str, Any]) -> None:
    """Raise ``ValueError`` when a packet fails watchlist validation."""

    result = validate_watchlist_packet(packet)
    if not result.ok:
        raise ValueError("invalid evidence freshness watchlist packet: " + "; ".join(result.errors))


def _cited_reference_ids(packet: dict[str, Any]) -> set[str]:
    cited: set[str] = set()
    for field in ("citations", "sources", "requirements", "guardrails"):
        for item in _as_list(packet.get(field)):
            ref_id = _ref_id(item)
            if not ref_id:
                continue
            if field == "citations" or not isinstance(item, dict) or item.get("cited") is True or item.get("citation"):
                cited.add(ref_id)
    return cited


def _validate_url(value: str, key: str) -> list[str]:
    parsed = urlparse(value)
    errors: list[str] = []
    host = (parsed.hostname or "").lower()

    if parsed.scheme != "https":
        errors.append(f"URL must use https: {key}")
    if host not in ALLOWLISTED_HOSTS:
        errors.append(f"URL host is not allowlisted: {value}")
    if parsed.username or parsed.password:
        errors.append(f"authenticated URL is not allowed: {key}")

    query_names = {part.split("=", 1)[0].lower() for part in parsed.query.split("&") if part}
    if query_names & AUTH_QUERY_MARKERS:
        errors.append(f"authenticated URL query is not allowed: {key}")

    path_segments = {segment.lower() for segment in parsed.path.split("/") if segment}
    if path_segments & RAW_URL_SEGMENTS:
        errors.append(f"raw/download/archive URL is not allowed: {key}")

    return errors


def _walk(value: Any, prefix: str = "") -> Iterable[tuple[str, Any]]:
    if isinstance(value, dict):
        for key, child in value.items():
            child_key = str(key)
            full_key = f"{prefix}.{child_key}" if prefix else child_key
            yield full_key, child
            yield from _walk(child, full_key)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            full_key = f"{prefix}[{index}]"
            yield full_key, child
            yield from _walk(child, full_key)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _ref_id(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        for key in ("id", "ref", "reference", "slug", "name"):
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
    return ""


def _looks_like_url(value: str) -> bool:
    parsed = urlparse(value)
    return bool(parsed.scheme and parsed.netloc)
