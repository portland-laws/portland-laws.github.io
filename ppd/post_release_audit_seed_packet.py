"""Validation for PP&D post-release audit seed packets.

The validator is intentionally deterministic and side-effect free. It checks
committed seed-packet fixtures before they can be used as evidence for agent
readiness, production labels, or post-release audit promotion.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePath
from typing import Any, Mapping, Sequence


CONSEQUENTIAL_CAPABILITIES = {
    "payment",
    "pay_fee",
    "fee_payment",
    "upload",
    "official_upload",
    "submission",
    "submit",
    "submit_application",
    "scheduling",
    "schedule",
    "schedule_inspection",
    "cancellation",
    "cancel",
    "withdraw",
    "certification",
    "certify",
    "acknowledgement_certification",
}

_PRIVATE_SESSION_MARKERS = (
    "auth_state",
    "storage_state",
    "cookie",
    "cookies",
    "session",
    "session_state",
    "localstorage",
    "indexeddb",
    "har",
    "trace.zip",
    "playwright-trace",
    "screenshot",
    "private_upload",
    "payment_detail",
    "credential",
    "password",
    "token",
)

_RAW_REFERENCE_MARKERS = (
    "/raw/",
    "/raw_bodies/",
    "/body_cache/",
    "/crawl_cache/",
    "/download/",
    "/downloads/",
    "/archive/",
    "/archives/",
    ".warc",
    ".warc.gz",
    ".har",
    ".zip",
)

_RAW_REFERENCE_SUFFIXES = {".html", ".htm", ".pdf", ".doc", ".docx", ".warc", ".gz", ".zip", ".har"}

_GUARANTEE_PHRASES = (
    "guarantee approval",
    "guaranteed approval",
    "approval guaranteed",
    "permit guaranteed",
    "permit will be approved",
    "permit will be issued",
    "will be approved",
    "will be issued",
    "ensures approval",
    "ensure approval",
    "legally sufficient",
    "legal determination",
    "binding legal advice",
)

_LIVE_EXECUTION_PHRASES = (
    "live network fetch performed",
    "live crawl performed",
    "downloaded from live",
    "executed in devhub",
    "devhub execution completed",
    "submitted in devhub",
    "uploaded in devhub",
    "paid in devhub",
    "scheduled in devhub",
    "certified in devhub",
)


@dataclass(frozen=True)
class PostReleaseAuditSeedPacketVerdict:
    """Machine-readable validation result for one audit seed packet."""

    allowed: bool
    reasons: tuple[str, ...]


def validate_post_release_audit_seed_packet(packet: Mapping[str, Any]) -> PostReleaseAuditSeedPacketVerdict:
    """Validate a post-release audit seed packet.

    The accepted shape is deliberately plain JSON-compatible data. Unknown
    fields are allowed, but any unsafe value anywhere in the packet blocks it.
    """

    reasons: list[str] = []

    if packet.get("packet_kind") != "post_release_audit_seed_packet":
        reasons.append("packet_kind_not_post_release_audit_seed_packet")

    if not _has_complete_prerequisite_links(packet.get("prerequisite_links")):
        reasons.append("missing_prerequisite_links")

    if _has_uncited_audit_claims(packet.get("audit_claims")):
        reasons.append("uncited_audit_claims")

    flattened = tuple(_flatten_values(packet))

    if any(_looks_like_private_session_artifact(value) for value in flattened):
        reasons.append("private_or_session_artifact_reference")

    if any(_looks_like_raw_reference(value) for value in flattened):
        reasons.append("raw_crawl_download_or_archive_reference")

    if any(_contains_phrase(value, _GUARANTEE_PHRASES) for value in flattened):
        reasons.append("legal_or_permitting_outcome_guarantee")

    if _production_ready_with_blockers(packet):
        reasons.append("production_ready_label_with_blockers")

    if _claims_live_execution(packet, flattened):
        reasons.append("live_network_or_devhub_execution_claim")

    if _has_enabled_consequential_capabilities(packet):
        reasons.append("enabled_consequential_capability")

    return PostReleaseAuditSeedPacketVerdict(allowed=not reasons, reasons=tuple(dict.fromkeys(reasons)))


def assert_post_release_audit_seed_packet_safe(packet: Mapping[str, Any]) -> None:
    """Raise ValueError when a seed packet is unsafe for promotion."""

    verdict = validate_post_release_audit_seed_packet(packet)
    if not verdict.allowed:
        raise ValueError("post-release audit seed packet rejected: " + ", ".join(verdict.reasons))


def _has_complete_prerequisite_links(value: Any) -> bool:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return False
    if not value:
        return False
    for item in value:
        if not isinstance(item, Mapping):
            return False
        source_id = item.get("source_id")
        citation = item.get("citation_url", item.get("canonical_url", item.get("source_evidence_id")))
        relation = item.get("relation", item.get("required_before"))
        if not _non_empty_string(source_id) or not _non_empty_string(citation) or not _non_empty_string(relation):
            return False
    return True


def _has_uncited_audit_claims(value: Any) -> bool:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return True
    if not value:
        return True
    for item in value:
        if not isinstance(item, Mapping):
            return True
        claim = item.get("claim")
        citations = item.get("citations", item.get("source_evidence_ids"))
        if not _non_empty_string(claim):
            return True
        if not isinstance(citations, Sequence) or isinstance(citations, (str, bytes)) or not citations:
            return True
        if any(not _non_empty_string(citation) for citation in citations):
            return True
    return False


def _production_ready_with_blockers(packet: Mapping[str, Any]) -> bool:
    labels = packet.get("labels", ())
    label_values = [str(labels)] if isinstance(labels, str) else [str(label) for label in labels or ()]
    status_values = (
        str(packet.get("status", "")),
        str(packet.get("readiness_label", "")),
        str(packet.get("release_label", "")),
        *label_values,
    )
    marked_production_ready = packet.get("production_ready") is True or any(
        value.strip().lower().replace("_", "-") == "production-ready" for value in status_values
    )
    blockers = packet.get("blockers", ())
    has_blockers = bool(blockers) or str(packet.get("validation_status", "")).strip().lower() in {"blocked", "has_blockers"}
    return marked_production_ready and has_blockers


def _claims_live_execution(packet: Mapping[str, Any], flattened: Sequence[str]) -> bool:
    boolean_flags = (
        "live_network_performed",
        "live_fetch_performed",
        "live_crawl_performed",
        "devhub_execution_performed",
        "devhub_action_executed",
    )
    if any(packet.get(flag) is True for flag in boolean_flags):
        return True
    return any(_contains_phrase(value, _LIVE_EXECUTION_PHRASES) for value in flattened)


def _has_enabled_consequential_capabilities(packet: Mapping[str, Any]) -> bool:
    capabilities = packet.get("capabilities", ())
    if isinstance(capabilities, Mapping):
        capabilities = [capabilities]
    if isinstance(capabilities, Sequence) and not isinstance(capabilities, (str, bytes)):
        for capability in capabilities:
            if isinstance(capability, Mapping):
                name = _normalize_capability_name(capability.get("name", capability.get("capability", "")))
                if capability.get("enabled") is True and name in CONSEQUENTIAL_CAPABILITIES:
                    return True
            elif _normalize_capability_name(capability) in CONSEQUENTIAL_CAPABILITIES:
                return True

    enabled = packet.get("enabled_capabilities", ())
    if isinstance(enabled, Sequence) and not isinstance(enabled, (str, bytes)):
        return any(_normalize_capability_name(name) in CONSEQUENTIAL_CAPABILITIES for name in enabled)
    return False


def _flatten_values(value: Any) -> list[str]:
    values: list[str] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            values.append(str(key))
            values.extend(_flatten_values(nested))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for nested in value:
            values.extend(_flatten_values(nested))
    elif value is not None:
        values.append(str(value))
    return values


def _looks_like_private_session_artifact(value: str) -> bool:
    lowered = value.replace("\\", "/").lower()
    return any(marker in lowered for marker in _PRIVATE_SESSION_MARKERS)


def _looks_like_raw_reference(value: str) -> bool:
    lowered = value.replace("\\", "/").lower()
    if any(marker in lowered for marker in _RAW_REFERENCE_MARKERS):
        return True
    suffix = PurePath(lowered).suffix
    return suffix in _RAW_REFERENCE_SUFFIXES and ("/crawl" in lowered or "/download" in lowered or "/archive" in lowered)


def _contains_phrase(value: str, phrases: Sequence[str]) -> bool:
    lowered = " ".join(value.lower().split())
    return any(phrase in lowered for phrase in phrases)


def _normalize_capability_name(value: Any) -> str:
    return str(value).strip().lower().replace("-", "_").replace(" ", "_")


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())
