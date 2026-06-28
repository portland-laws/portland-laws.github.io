"""Validation for public source registry promotion decision packets.

The validator is deliberately dictionary-based and side-effect free. It checks
committed fixtures or daemon-produced decision packets before anything can be
promoted into the public source registry.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Mapping, Sequence
from urllib.parse import urlparse


ALLOWED_PUBLIC_HOSTS = {
    "www.portland.gov",
    "devhub.portlandoregon.gov",
    "www.portlandoregon.gov",
    "www.portlandmaps.com",
}

PROMOTED_DECISIONS = {"promote", "promoted", "approved_for_promotion", "release"}
RESOLVED_BLOCKER_STATES = {"resolved", "cleared", "closed", "not_blocking", "accepted_risk"}
UNRESOLVED_BLOCKER_STATES = {"", "open", "unresolved", "blocking", "blocked", "pending", "todo"}

REHEARSAL_LINK_KEYS = {
    "rehearsal_link",
    "rehearsal_links",
    "rehearsal_evidence_link",
    "rehearsal_packet_link",
    "rehearsal_report_link",
}

RELEASE_GATE_LINK_KEYS = {
    "release_gate_link",
    "release_gate_links",
    "release_gate_evidence_link",
    "release_gate_packet_link",
    "release_gate_report_link",
}

ROLLBACK_NOTE_KEYS = {
    "rollback_note",
    "rollback_notes",
    "rollback_plan",
    "rollback_summary",
}

LIVE_MUTATION_KEYS = {
    "apply_to_live_registry",
    "commit_to_registry",
    "committed_to_registry",
    "live_registry_mutation",
    "live_registry_mutation_requested",
    "mutate_live_registry",
    "mutate_registry",
    "registry_mutation",
    "registry_write",
    "write_registry",
    "writes_live_registry",
}

NETWORK_EXECUTION_KEYS = {
    "crawl_executed",
    "fetch_executed",
    "http_request_performed",
    "live_fetch_performed",
    "network_claim",
    "network_execution",
    "network_execution_claim",
    "network_executed",
    "network_performed",
    "performed_network",
    "request_executed",
}

NETWORK_EXECUTION_TEXT_MARKERS = (
    "curl ",
    "fetch executed",
    "http request performed",
    "live crawl executed",
    "live fetch performed",
    "network call performed",
    "network executed",
    "request executed",
)

PRIVATE_URL_PATH_MARKERS = (
    "/account",
    "/admin",
    "/auth",
    "/cart",
    "/dashboard",
    "/login",
    "/my-permits",
    "/oauth",
    "/payment",
    "/signin",
    "/sign-in",
    "/upload",
    "/user",
)

PRIVATE_URL_QUERY_MARKERS = (
    "access_token",
    "auth=",
    "code=",
    "credential",
    "password",
    "session",
    "state=",
    "token",
)

RAW_PATH_MARKERS = (
    "/archive/",
    "/archives/",
    "/crawl-output/",
    "/crawl_output/",
    "/download/",
    "/downloads/",
    "/raw/",
    "/raw-crawl/",
    "/raw_crawl/",
    "/raw_bodies/",
    "/warc/",
    "archive_artifact_ref",
    "body_cache",
    "downloaded_documents",
    "raw_crawl",
    "raw_response_body",
    "warc.gz",
)

RAW_PATH_SUFFIXES = {
    ".arc",
    ".har",
    ".html",
    ".htm",
    ".pdf",
    ".warc",
    ".warc.gz",
    ".zip",
}


@dataclass(frozen=True)
class PublicSourceRegistryPromotionVerdict:
    """Result of public source registry promotion packet validation."""

    allowed: bool
    reasons: tuple[str, ...]


def validate_public_source_registry_promotion_packet(packet: Mapping[str, Any]) -> PublicSourceRegistryPromotionVerdict:
    """Return whether a source registry promotion packet may be accepted.

    A promoted packet must carry rehearsal evidence, release-gate evidence, and
    rollback notes. All packets are rejected when they contain private URLs, raw
    crawl/download/archive paths, live registry mutation flags, or claims that a
    network action was executed.
    """

    reasons: list[str] = []
    decision_is_promoted = _is_promoted_decision(packet)

    if decision_is_promoted and not _has_required_link(packet, REHEARSAL_LINK_KEYS):
        reasons.append("missing_rehearsal_link")

    if decision_is_promoted and not _has_required_link(packet, RELEASE_GATE_LINK_KEYS):
        reasons.append("missing_release_gate_link")

    if decision_is_promoted and not _has_required_note(packet, ROLLBACK_NOTE_KEYS):
        reasons.append("missing_rollback_notes")

    if decision_is_promoted and _has_unresolved_blocker(packet):
        reasons.append("unresolved_blocker_marked_promoted")

    scan_reasons: set[str] = set()
    _scan_packet(packet, "$", scan_reasons)
    reasons.extend(reason for reason in sorted(scan_reasons) if reason not in reasons)

    return PublicSourceRegistryPromotionVerdict(allowed=not reasons, reasons=tuple(reasons))


def assert_public_source_registry_promotion_packet(packet: Mapping[str, Any]) -> None:
    """Raise ValueError when a promotion packet fails validation."""

    verdict = validate_public_source_registry_promotion_packet(packet)
    if not verdict.allowed:
        raise ValueError("; ".join(verdict.reasons))


def _is_promoted_decision(packet: Mapping[str, Any]) -> bool:
    for key in ("decision", "promotion_decision", "status", "verdict"):
        value = packet.get(key)
        if isinstance(value, str) and value.strip().lower() in PROMOTED_DECISIONS:
            return True
    promoted = packet.get("promoted")
    return promoted is True


def _has_required_link(packet: Mapping[str, Any], keys: set[str]) -> bool:
    for value in _values_for_keys(packet, keys):
        if isinstance(value, str) and value.strip():
            return True
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            if any(isinstance(item, str) and item.strip() for item in value):
                return True
    return False


def _has_required_note(packet: Mapping[str, Any], keys: set[str]) -> bool:
    for value in _values_for_keys(packet, keys):
        if isinstance(value, str) and value.strip():
            return True
        if isinstance(value, Mapping) and any(str(child).strip() for child in value.values()):
            return True
    rollback = packet.get("rollback")
    return isinstance(rollback, Mapping) and any(str(child).strip() for child in rollback.values())


def _values_for_keys(value: Any, keys: set[str]) -> list[Any]:
    found: list[Any] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in keys:
                found.append(child)
            found.extend(_values_for_keys(child, keys))
    elif isinstance(value, list):
        for child in value:
            found.extend(_values_for_keys(child, keys))
    return found


def _has_unresolved_blocker(packet: Mapping[str, Any]) -> bool:
    blockers = packet.get("unresolved_blockers")
    if _non_empty_sequence(blockers):
        return True

    blockers = packet.get("blockers", packet.get("blocking_issues", ()))
    if not isinstance(blockers, Sequence) or isinstance(blockers, (str, bytes)):
        return False

    for blocker in blockers:
        if isinstance(blocker, Mapping):
            state = str(blocker.get("status", blocker.get("state", ""))).strip().lower()
            if blocker.get("resolved") is True or state in RESOLVED_BLOCKER_STATES:
                continue
            if blocker.get("resolved") is False or state in UNRESOLVED_BLOCKER_STATES:
                return True
        elif str(blocker).strip():
            return True
    return False


def _non_empty_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes)) and len(value) > 0


def _scan_packet(value: Any, path: str, reasons: set[str]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            lowered_key = key_text.lower()
            if lowered_key in LIVE_MUTATION_KEYS and _truthy_or_live(child):
                reasons.add("live_registry_mutation_flag")
            if lowered_key in NETWORK_EXECUTION_KEYS and _truthy_network_claim(child):
                reasons.add("network_execution_claim")
            if lowered_key == "mutation_mode" and str(child).strip().lower() in {"live", "registry", "write"}:
                reasons.add("live_registry_mutation_flag")
            _scan_packet(child, f"{path}.{key_text}", reasons)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _scan_packet(child, f"{path}[{index}]", reasons)
    elif isinstance(value, str):
        if _is_private_or_authenticated_url(value):
            reasons.add("private_or_authenticated_url")
        if _looks_like_raw_path(value):
            reasons.add("raw_crawl_download_or_archive_path")
        if _looks_like_network_execution_text(value):
            reasons.add("network_execution_claim")


def _truthy_or_live(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "live", "write", "mutate", "committed"}
    return False


def _truthy_network_claim(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, str):
        text = value.strip().lower()
        return text not in {"", "false", "no", "none", "not_performed", "dry_run_only"}
    return False


def _is_private_or_authenticated_url(text: str) -> bool:
    parsed = urlparse(text.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False
    if parsed.username or parsed.password:
        return True
    if parsed.scheme != "https":
        return True
    host = parsed.netloc.lower()
    if host not in ALLOWED_PUBLIC_HOSTS:
        return True
    lowered_path = parsed.path.lower()
    if any(marker in lowered_path for marker in PRIVATE_URL_PATH_MARKERS):
        return True
    lowered_query = parsed.query.lower()
    return any(marker in lowered_query for marker in PRIVATE_URL_QUERY_MARKERS)


def _looks_like_raw_path(text: str) -> bool:
    normalized = text.strip().replace("\\", "/").lower()
    if not normalized:
        return False
    if any(marker in normalized for marker in RAW_PATH_MARKERS):
        return True
    suffix = PurePosixPath(normalized).suffix
    if suffix in RAW_PATH_SUFFIXES:
        return True
    return normalized.endswith(".warc.gz")


def _looks_like_network_execution_text(text: str) -> bool:
    lowered = " " + text.strip().lower() + " "
    return any(marker in lowered for marker in NETWORK_EXECUTION_TEXT_MARKERS)


__all__ = [
    "PublicSourceRegistryPromotionVerdict",
    "assert_public_source_registry_promotion_packet",
    "validate_public_source_registry_promotion_packet",
]
