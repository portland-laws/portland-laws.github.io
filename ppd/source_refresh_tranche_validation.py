"""Safety validation for public source refresh tranche proposal packets.

The validator is intentionally side-effect free. It accepts already-built packet
objects and rejects proposal content that would cross PP&D public-source refresh
boundaries.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
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
PRIVATE_PATH_MARKERS = (
    "/account",
    "/admin",
    "/auth",
    "/dashboard",
    "/login",
    "/payment",
    "/session",
    "/signin",
    "/sign-in",
    "/upload",
)
PRIVATE_QUERY_MARKERS = ("access_token=", "auth=", "password=", "session=", "token=")
RAW_REFERENCE_KEYS = frozenset(
    {
        "archive_path",
        "archive_ref",
        "archive_url",
        "body",
        "download_path",
        "download_url",
        "downloaded_document_path",
        "raw_archive",
        "raw_archive_path",
        "raw_body",
        "raw_content",
        "raw_html",
        "warc_path",
    }
)
ACTIVE_MUTATION_KEYS = frozenset(
    {
        "active_registry_mutation",
        "active_schedule_mutation",
        "apply_to_live_registry",
        "edit_live_registry",
        "live_registry_mutated",
        "live_registry_updated",
        "live_schedule_mutated",
        "mutates_active_registry",
        "mutates_active_schedule",
        "registry_mutation_enabled",
        "schedule_mutation_allowed",
        "schedule_mutation_enabled",
        "writes_live_registry",
        "writes_live_schedule",
    }
)
LIVE_EXECUTION_CLAIM_PATTERN = re.compile(
    r"\b(live crawl(?:ed|ing)?|crawler (?:ran|executed|invoked)|ran the crawler|"
    r"processor (?:ran|executed|invoked)|ran the processor|fetched urls?|downloaded documents?)\b",
    re.IGNORECASE,
)
OUTCOME_GUARANTEE_PATTERN = re.compile(
    r"\b(approval is guaranteed|guaranteed approval|permit (?:will be|is) approved|"
    r"permitting outcome (?:is )?guaranteed|legal outcome (?:is )?guaranteed)\b",
    re.IGNORECASE,
)
RAW_URL_PATH_PATTERN = re.compile(
    r"(^|/)(download|downloads|archive|raw)(/|$)|\.(pdf|warc|zip|tar|tgz|gz)$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class RefreshTrancheValidationResult:
    """Validation outcome with stable violation codes."""

    valid: bool
    errors: tuple[str, ...]

    def codes(self) -> tuple[str, ...]:
        return tuple(error.split(":", 1)[0] for error in self.errors)


def validate_public_source_refresh_tranche_proposal_packet(packet: Mapping[str, Any]) -> RefreshTrancheValidationResult:
    """Validate a public source refresh tranche proposal without side effects."""

    errors: list[str] = []
    if packet.get("packet_type") != "ppd_public_source_refresh_tranche_proposal":
        errors.append("invalid_packet_type: packet_type must be ppd_public_source_refresh_tranche_proposal")
    if packet.get("proposal_status") != "metadata_only_review_required":
        errors.append("invalid_proposal_status: proposal_status must require metadata-only review")

    consumes = packet.get("consumes_packet_ids")
    if not _non_empty_text_list(consumes):
        errors.append("missing_consumed_packet_refs: consumes_packet_ids must be a non-empty string list")

    attestations = packet.get("attestations")
    if not isinstance(attestations, Mapping):
        errors.append("missing_attestations: attestations must be an object")
    else:
        for key in ("no_fetch_performed", "no_download_performed", "no_processor_invoked", "no_schedule_mutation_performed"):
            if attestations.get(key) is not True:
                errors.append(f"missing_no_execution_attestation: attestations.{key} must be true")

    sources = packet.get("ordered_sources")
    if not isinstance(sources, list) or not sources:
        errors.append("missing_ordered_sources: ordered_sources must be a non-empty list")
    else:
        _validate_ordered_sources(sources, errors)

    _scan_for_unsafe_content(packet, "packet", errors)
    return RefreshTrancheValidationResult(valid=not errors, errors=tuple(errors))


def require_public_source_refresh_tranche_proposal_packet(packet: Mapping[str, Any]) -> None:
    """Raise ValueError when a proposal packet is invalid."""

    result = validate_public_source_refresh_tranche_proposal_packet(packet)
    if not result.valid:
        raise ValueError("invalid public source refresh tranche proposal packet: " + "; ".join(result.errors))


def _validate_ordered_sources(sources: list[Any], errors: list[str]) -> None:
    seen: set[str] = set()
    for expected_index, source in enumerate(sources, start=1):
        prefix = f"ordered_sources[{expected_index - 1}]"
        if not isinstance(source, Mapping):
            errors.append(f"invalid_source_entry: {prefix} must be an object")
            continue
        if source.get("order_index") != expected_index:
            errors.append(f"unordered_source_entry: {prefix}.order_index must be {expected_index}")
        source_id = _text(source.get("source_id"))
        if not source_id:
            errors.append(f"missing_source_id: {prefix}.source_id must be non-empty")
        elif source_id in seen:
            errors.append(f"duplicate_source_entry: duplicate source_id {source_id}")
        seen.add(source_id)

        _validate_public_url(_text(source.get("canonical_url")), f"{prefix}.canonical_url", errors)
        for key in ("refresh_reason", "proposed_frequency", "owner", "reviewer"):
            if not _text(source.get(key)):
                errors.append(f"missing_reviewer_owners: {prefix}.{key} must be non-empty")
        if not _non_empty_text_list(source.get("source_evidence_refs")):
            errors.append(f"uncited_source_entry: {prefix}.source_evidence_refs must be a non-empty string list")
        if not _text(source.get("allowlist_evidence_ref")).startswith("allowlist://"):
            errors.append(f"missing_allowlist_evidence: {prefix}.allowlist_evidence_ref must start with allowlist://")
        if not _text(source.get("robots_evidence_ref")).startswith("robots://"):
            errors.append(f"missing_robots_evidence: {prefix}.robots_evidence_ref must start with robots://")
        if not _non_empty_text_list(source.get("abort_criteria")):
            errors.append(f"missing_abort_criteria: {prefix}.abort_criteria must be a non-empty string list")
        if not _non_empty_text_list(source.get("runbook_step_refs")):
            errors.append(f"missing_runbook_refs: {prefix}.runbook_step_refs must be a non-empty string list")


def _validate_public_url(url: str, label: str, errors: list[str]) -> None:
    if not url:
        errors.append(f"invalid_public_url: {label} must be non-empty")
        return
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        errors.append(f"invalid_public_url: {label} must be an http(s) URL")
        return
    host = parsed.netloc.lower()
    lowered_url = url.lower()
    if host not in ALLOWED_PUBLIC_HOSTS:
        errors.append(f"non_allowlisted_url: {label} is outside the PP&D public allowlist")
    if any(marker in parsed.path.lower() for marker in PRIVATE_PATH_MARKERS) or any(marker in lowered_url for marker in PRIVATE_QUERY_MARKERS):
        errors.append(f"authenticated_url: {label} appears private or authenticated")
    if RAW_URL_PATH_PATTERN.search(parsed.path):
        errors.append(f"raw_download_archive_reference: {label} must not reference raw body, download, or archive artifacts")


def _scan_for_unsafe_content(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            key_lower = key_text.lower()
            child_path = f"{path}.{key_text}"
            if key_lower in RAW_REFERENCE_KEYS:
                errors.append(f"raw_download_archive_reference: {child_path} is not allowed")
            if key_lower in ACTIVE_MUTATION_KEYS and not _falsey_claim(child):
                errors.append(f"active_registry_or_schedule_mutation: {child_path} must be absent or false")
            _scan_for_unsafe_content(child, child_path, errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _scan_for_unsafe_content(child, f"{path}[{index}]", errors)
    elif isinstance(value, str):
        if LIVE_EXECUTION_CLAIM_PATTERN.search(value):
            errors.append(f"live_crawl_or_processor_execution_claim: {path} claims live crawl or processor execution")
        if OUTCOME_GUARANTEE_PATTERN.search(value):
            errors.append(f"legal_or_permitting_outcome_guarantee: {path} guarantees an outcome")
        if value.startswith(("http://", "https://")):
            _validate_public_url(value, path, errors)


def _falsey_claim(value: Any) -> bool:
    return value is False or value is None or value in {"false", "not_applied", "proposed_only"}


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _non_empty_text_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item.strip() for item in value)
