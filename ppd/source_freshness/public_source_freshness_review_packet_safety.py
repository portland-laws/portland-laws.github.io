"""Safety validation for public source freshness review packets.

The validator is deterministic and metadata-only. It performs no network access,
does not fetch URLs, and treats freshness review packets as review artifacts that
must fail closed before any source refresh or schedule mutation can be promoted.
"""

from __future__ import annotations

from dataclasses import dataclass
from ipaddress import ip_address
from typing import Any, Mapping
from urllib.parse import parse_qs, urlparse


ALLOWLISTED_HOSTS = frozenset(
    {
        "devhub.portlandoregon.gov",
        "efiles.portlandoregon.gov",
        "portland.gov",
        "publicnotices.portland.gov",
        "www.portland.gov",
        "www.portlandmaps.com",
        "www.portlandoregon.gov",
    }
)

SECRET_QUERY_KEYS = frozenset(
    {
        "access_token",
        "api_key",
        "apikey",
        "auth",
        "code",
        "key",
        "password",
        "private_key",
        "session",
        "signature",
        "signed",
        "token",
    }
)

PRIVATE_PATH_MARKERS = (
    "/account",
    "/admin",
    "/auth",
    "/dashboard",
    "/login",
    "/payment",
    "/session",
    "/upload",
)

RAW_OR_DOWNLOAD_PATH_MARKERS = (
    "/raw/",
    "/raw-body/",
    "/body/raw",
    "/download/",
    "/downloads/",
    "/archive/",
    "/archives/",
    "/export/",
    "/exports/",
)

RAW_OR_DOWNLOAD_SUFFIXES = (
    ".7z",
    ".bz2",
    ".doc",
    ".docx",
    ".gz",
    ".pdf",
    ".rar",
    ".tar",
    ".tgz",
    ".xls",
    ".xlsx",
    ".zip",
)

RAW_ARTIFACT_KEYS = frozenset(
    {
        "archive_path",
        "auth_state",
        "body",
        "cookie",
        "cookies",
        "credential",
        "credentials",
        "download_path",
        "downloaded_document_path",
        "har_path",
        "html",
        "local_path",
        "password",
        "raw_body",
        "raw_content",
        "raw_html",
        "screenshot_path",
        "session_state",
        "storage_state",
        "trace_path",
        "warc_path",
    }
)

LIVE_FETCH_KEYS = frozenset(
    {
        "allow_live_fetch",
        "allow_live_network",
        "download_documents",
        "executed_live_network",
        "fetch_urls",
        "fetched_live",
        "live_crawl",
        "live_fetch",
        "live_fetch_claimed",
        "live_network",
        "live_network_execution",
        "network_allowed",
        "network_executed",
        "network_invoked",
        "persist_raw_body",
        "raw_body_persisted",
    }
)

SCHEDULE_MUTATION_KEYS = frozenset(
    {
        "active_schedule_mutation",
        "auto_start",
        "cron_enabled",
        "live_schedule_mutated",
        "mutate_schedule",
        "schedule_mutation",
        "schedule_mutation_allowed",
        "schedule_mutation_enabled",
        "start_immediately",
        "writes_live_schedule",
    }
)


@dataclass(frozen=True)
class PublicSourceFreshnessReviewPacketSafetyResult:
    valid: bool
    errors: tuple[str, ...]


def validate_public_source_freshness_review_packet_safety(
    packet: Mapping[str, Any],
) -> PublicSourceFreshnessReviewPacketSafetyResult:
    """Return packet safety errors without side effects."""

    errors: list[str] = []
    source_ids = _string_list(packet.get("source_ids"))
    if not source_ids:
        errors.append("source_ids must be non-empty")

    packet_prereqs = _string_list(packet.get("packet_level_prerequisite_evidence_ids"))
    if not _has_robots_and_policy(packet_prereqs):
        errors.append("packet_level_prerequisite_evidence_ids must include robots and policy prerequisites")

    decisions = packet.get("reviewer_owned_source_freshness_decisions")
    if not isinstance(decisions, list) or not decisions:
        errors.append("reviewer_owned_source_freshness_decisions must be a non-empty list")
    else:
        declared = set(source_ids)
        for index, decision in enumerate(decisions):
            _validate_decision(decision, index, declared, errors)

    _scan_packet(packet, "$", errors)
    return PublicSourceFreshnessReviewPacketSafetyResult(valid=not errors, errors=tuple(errors))


def require_public_source_freshness_review_packet_safety(packet: Mapping[str, Any]) -> None:
    result = validate_public_source_freshness_review_packet_safety(packet)
    if not result.valid:
        raise ValueError("invalid public source freshness review packet safety: " + "; ".join(result.errors))


def _validate_decision(value: Any, index: int, declared_source_ids: set[str], errors: list[str]) -> None:
    prefix = f"reviewer_owned_source_freshness_decisions[{index}]"
    if not isinstance(value, Mapping):
        errors.append(prefix + " must be an object")
        return

    source_id = _text(value.get("source_id"))
    if not source_id:
        errors.append(prefix + ".source_id is required")
    elif source_id not in declared_source_ids:
        errors.append(prefix + ".source_id must be declared in source_ids")

    if not _text(value.get("reviewer_owner")):
        errors.append(prefix + ".reviewer_owner is required")

    prereqs = _string_list(value.get("prerequisite_robots_policy_evidence_ids"))
    if not _has_robots_and_policy(prereqs):
        errors.append(prefix + ".prerequisite_robots_policy_evidence_ids must include robots and policy prerequisites")


def _scan_packet(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, Mapping):
        _validate_stale_current(value, path, errors)
        for key, child in value.items():
            key_text = str(key)
            lowered = key_text.lower()
            child_path = f"{path}.{key_text}"
            if lowered in RAW_ARTIFACT_KEYS and _present(child):
                errors.append(child_path + " is forbidden in public source freshness review packets")
            if lowered in LIVE_FETCH_KEYS and _truthy(child):
                errors.append(child_path + " must not claim live fetching or network execution")
            if lowered in SCHEDULE_MUTATION_KEYS and _truthy(child):
                errors.append(child_path + " must not enable or claim active schedule mutation")
            _scan_packet(child, child_path, errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _scan_packet(child, f"{path}[{index}]", errors)
    elif isinstance(value, str):
        _validate_string_value(value, path, errors)


def _validate_stale_current(value: Mapping[str, Any], path: str, errors: list[str]) -> None:
    freshness_status = _text(value.get("freshness_status") or value.get("source_freshness_status")).lower()
    if freshness_status != "current":
        return
    stale = any(_truthy(value.get(key)) for key in ("is_stale", "stale", "stale_by_cadence", "stale_source"))
    if stale and not _has_stale_acknowledgement(value):
        errors.append(path + " marks a stale source current without stale_source_acknowledgement")


def _has_stale_acknowledgement(value: Mapping[str, Any]) -> bool:
    acknowledgement = value.get("stale_source_acknowledgement")
    if isinstance(acknowledgement, Mapping):
        if _text(acknowledgement.get("acknowledgement_id")):
            return True
        if acknowledgement.get("acknowledgement_status") == "acknowledged_for_review_only":
            return True
    return _truthy(value.get("stale_source_acknowledged")) or bool(_text(value.get("stale_source_acknowledgement_id")))


def _validate_string_value(value: str, path: str, errors: list[str]) -> None:
    lowered = value.lower()
    if any(marker in lowered for marker in (".har", ".warc", "trace.zip", "raw_body", "download_path")):
        errors.append(path + " must not reference raw crawl or browser artifacts")

    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"}:
        return

    hostname = (parsed.hostname or "").lower().rstrip(".")
    if parsed.username or parsed.password:
        errors.append(path + " must not reference private or authenticated URLs")
    if not hostname:
        errors.append(path + " must include an allowlisted host")
    elif _is_private_host(hostname):
        errors.append(path + " must not reference private or authenticated URLs")
    elif hostname not in ALLOWLISTED_HOSTS:
        errors.append(path + " host is not allowlisted: " + hostname)

    query_keys = {key.lower() for key in parse_qs(parsed.query, keep_blank_values=True)}
    if query_keys & SECRET_QUERY_KEYS:
        errors.append(path + " must not reference private or authenticated URLs")

    path_lower = parsed.path.lower()
    padded_path = f"/{path_lower.strip('/')}/" if path_lower else "/"
    if any(marker in path_lower for marker in PRIVATE_PATH_MARKERS):
        errors.append(path + " must not reference private or authenticated URLs")
    if any(marker in padded_path for marker in RAW_OR_DOWNLOAD_PATH_MARKERS) or path_lower.endswith(RAW_OR_DOWNLOAD_SUFFIXES):
        errors.append(path + " must not reference raw body, download, archive, export, or document artifact paths")


def _has_robots_and_policy(values: list[str]) -> bool:
    lowered = [value.lower() for value in values]
    has_robots = any("robot" in value for value in lowered)
    has_policy = any("policy" in value or "terms" in value for value in lowered)
    return has_robots and has_policy


def _is_private_host(hostname: str) -> bool:
    if hostname in {"localhost", "localhost.localdomain"} or hostname.endswith(".local"):
        return True
    try:
        address = ip_address(hostname)
    except ValueError:
        return False
    return address.is_private or address.is_loopback or address.is_link_local or address.is_reserved or address.is_multicast


def _string_list(value: Any) -> list[str]:
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    if isinstance(value, list):
        return [item.strip() for item in value if isinstance(item, str) and item.strip()]
    return []


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) and value.strip() else ""


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on", "enabled", "active"}
    if isinstance(value, int):
        return value != 0
    return bool(value)


def _present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True


__all__ = [
    "ALLOWLISTED_HOSTS",
    "PublicSourceFreshnessReviewPacketSafetyResult",
    "require_public_source_freshness_review_packet_safety",
    "validate_public_source_freshness_review_packet_safety",
]
