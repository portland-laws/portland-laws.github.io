"""Validation for PP&D source registry schedule update candidate packets.

The validator is intentionally metadata-only. It performs no network access,
processor invocation, crawl execution, registry mutation, or schedule mutation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import urlparse

DEFAULT_ALLOWED_HOSTS = (
    "www.portland.gov",
    "devhub.portlandoregon.gov",
    "www.portlandoregon.gov",
    "www.portlandmaps.com",
)

PRIVATE_URL_MARKERS = (
    "/login",
    "/sign-in",
    "/signin",
    "/register",
    "/account",
    "/dashboard",
    "/my-permits",
    "/mypermits",
    "/checkout",
    "/payment",
    "/upload",
    "/submit",
)

PRIVATE_SOURCE_TYPES = {"authenticated", "private", "devhub_authenticated", "account_scoped"}
PRIVATE_PRIVACY_CLASSES = {"authenticated", "private", "account_scoped", "user_private"}

RAW_DOWNLOAD_ARCHIVE_FIELDS = {
    "archive_artifact_ref",
    "archive_ref",
    "body",
    "body_ref",
    "download_path",
    "download_ref",
    "download_url",
    "downloaded_file_ref",
    "har_ref",
    "raw_body",
    "raw_body_path",
    "raw_body_ref",
    "response_body",
    "screenshot_ref",
    "trace_ref",
    "warc_ref",
}

LIVE_EXECUTION_TRUE_FIELDS = {
    "crawl_executed",
    "download_files",
    "execute_processors",
    "fetch_urls",
    "invoke_processors",
    "live_crawl_claimed",
    "live_crawl_completed",
    "live_fetch_allowed",
    "network_io_allowed",
    "processor_execution_allowed",
    "processor_invocation_allowed",
}

MUTATION_TRUE_FIELDS = {
    "active_registry_mutation",
    "active_schedule_mutation",
    "apply_registry_update",
    "apply_schedule_update",
    "mutate_registries",
    "mutate_registry",
    "mutate_schedule",
    "mutate_schedules",
    "registry_mutation_allowed",
    "schedule_mutation_allowed",
}

OUTCOME_GUARANTEE_MARKERS = (
    "approval guaranteed",
    "approved by pp&d",
    "approved by ppd",
    "guarantee approval",
    "guaranteed approval",
    "issuance guaranteed",
    "legal determination",
    "legal outcome",
    "permit approval guaranteed",
    "permit will be approved",
    "will be approved",
    "will pass inspection",
)

CITATION_KEYS = (
    "citation_refs",
    "citations",
    "evidence_refs",
    "policy_evidence_refs",
    "source_evidence_ids",
)

ADJUSTMENT_KEYS = (
    "source_adjustments",
    "schedule_adjustments",
    "candidate_adjustments",
    "registry_schedule_adjustments",
    "update_candidates",
)

REQUIRED_ABORT_MARKERS = (
    "allowlist",
    "authenticated",
    "raw",
    "download",
    "archive",
    "crawl",
    "processor",
    "guarantee",
    "registry",
    "schedule",
)


def load_source_registry_schedule_update_candidate_packet(path: Path) -> Mapping[str, Any]:
    """Load a candidate packet JSON object from disk."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object in {path}")
    return payload


def assert_valid_source_registry_schedule_update_candidate_packet(
    packet: Mapping[str, Any],
    *,
    allowed_hosts: Sequence[str] = DEFAULT_ALLOWED_HOSTS,
) -> None:
    """Raise ValueError when a source registry schedule update candidate is unsafe."""

    errors = validate_source_registry_schedule_update_candidate_packet(packet, allowed_hosts=allowed_hosts)
    if errors:
        raise ValueError("source registry schedule update candidate packet failed validation: " + "; ".join(errors))


def validate_source_registry_schedule_update_candidate_packet(
    packet: Mapping[str, Any],
    *,
    allowed_hosts: Sequence[str] = DEFAULT_ALLOWED_HOSTS,
) -> list[str]:
    """Return deterministic validation errors for an update candidate packet."""

    errors: list[str] = []
    allowlist = tuple(host.lower() for host in allowed_hosts)

    affected_source_ids = _string_list(packet.get("affected_source_ids"))
    if not affected_source_ids:
        errors.append("affected_source_ids_missing")

    errors.extend(_reviewer_owner_errors(packet))
    errors.extend(_abort_criteria_errors(packet))

    adjustments = _candidate_adjustments(packet)
    if not adjustments:
        errors.append("source_adjustments_missing")
    for index, adjustment in enumerate(adjustments):
        label = f"source_adjustments[{index}]"
        if not isinstance(adjustment, dict):
            errors.append(f"{label}_not_object")
            continue
        adjustment_source_ids = _string_list(adjustment.get("affected_source_ids"))
        if not adjustment_source_ids and not _non_empty_string(adjustment.get("source_id")):
            errors.append(f"{label}:affected_source_ids_missing")
        if not _has_citation(adjustment):
            errors.append(f"{label}:uncited_source_adjustment")

    errors.extend(_url_and_privacy_errors(packet, allowlist))
    errors.extend(_recursive_safety_errors(packet))
    return sorted(dict.fromkeys(errors))


def validate_source_registry_schedule_update_candidate_packet_file(
    path: Path,
    *,
    allowed_hosts: Sequence[str] = DEFAULT_ALLOWED_HOSTS,
) -> list[str]:
    """Load and validate a candidate packet fixture."""

    return validate_source_registry_schedule_update_candidate_packet(
        load_source_registry_schedule_update_candidate_packet(path),
        allowed_hosts=allowed_hosts,
    )


def _reviewer_owner_errors(packet: Mapping[str, Any]) -> list[str]:
    owners = packet.get("reviewer_owners", packet.get("reviewer_owner_fields"))
    if not isinstance(owners, dict):
        return ["reviewer_owners_missing"]
    errors: list[str] = []
    for field in ("primary_reviewer", "backup_reviewer", "review_queue"):
        if not _non_empty_string(owners.get(field)):
            errors.append(f"reviewer_owners.{field}_missing")
    return errors


def _abort_criteria_errors(packet: Mapping[str, Any]) -> list[str]:
    abort_criteria = packet.get("abort_criteria")
    if not isinstance(abort_criteria, list) or not abort_criteria:
        return ["abort_criteria_missing"]
    rendered = " ".join(str(item).lower() for item in abort_criteria)
    errors: list[str] = []
    for marker in REQUIRED_ABORT_MARKERS:
        if marker not in rendered:
            errors.append(f"abort_criteria_missing_{marker}")
    return errors


def _candidate_adjustments(packet: Mapping[str, Any]) -> list[Any]:
    for key in ADJUSTMENT_KEYS:
        value = packet.get(key)
        if isinstance(value, list):
            return list(value)
    return []


def _has_citation(adjustment: Mapping[str, Any]) -> bool:
    for key in CITATION_KEYS:
        if _string_list(adjustment.get(key)):
            return True
    evidence = adjustment.get("policy_evidence")
    if isinstance(evidence, dict):
        return _non_empty_string(evidence.get("evidence_ref")) or bool(_string_list(evidence.get("citation_refs")))
    return False


def _url_and_privacy_errors(packet: Mapping[str, Any], allowlist: Sequence[str]) -> list[str]:
    errors: list[str] = []
    for path, key, value in _walk_items(packet):
        normalized_key = key.lower()
        if normalized_key in {"source_type", "privacy_classification", "auth_scope"} and isinstance(value, str):
            normalized_value = value.strip().lower()
            if normalized_key == "source_type" and normalized_value in PRIVATE_SOURCE_TYPES:
                errors.append(f"{path}:private_or_authenticated_source_type")
            if normalized_key == "privacy_classification" and normalized_value in PRIVATE_PRIVACY_CLASSES:
                errors.append(f"{path}:private_or_authenticated_privacy_classification")
            if normalized_key == "auth_scope" and normalized_value not in {"public", "unauthenticated", "none"}:
                errors.append(f"{path}:private_or_authenticated_auth_scope")
        if _looks_like_url_key(normalized_key) and isinstance(value, str) and value:
            errors.extend(_url_errors(path, value, allowlist))
    return errors


def _url_errors(path: str, url: str, allowlist: Sequence[str]) -> list[str]:
    parsed = urlparse(url)
    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
        return [f"{path}:invalid_or_unsupported_url"]
    host = parsed.netloc.lower()
    lowered_path = parsed.path.lower()
    errors: list[str] = []
    if host not in allowlist:
        errors.append(f"{path}:outside_allowlist")
    if any(marker in lowered_path for marker in PRIVATE_URL_MARKERS):
        errors.append(f"{path}:private_or_authenticated_url")
    if "/download" in lowered_path or parsed.query.lower().startswith("download="):
        errors.append(f"{path}:raw_download_or_archive_reference")
    return errors


def _recursive_safety_errors(packet: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for path, key, value in _walk_items(packet):
        normalized_key = key.lower()
        if normalized_key in RAW_DOWNLOAD_ARCHIVE_FIELDS and _truthy_reference(value):
            errors.append(f"{path}:raw_body_download_or_archive_reference")
        if normalized_key in LIVE_EXECUTION_TRUE_FIELDS and value is True:
            errors.append(f"{path}:live_crawl_or_processor_execution_claim")
        if normalized_key in MUTATION_TRUE_FIELDS and value is True:
            errors.append(f"{path}:active_registry_or_schedule_mutation_flag")
        if "guarantee" in normalized_key and _truthy_reference(value):
            errors.append(f"{path}:legal_or_permitting_outcome_guarantee")
        if isinstance(value, str) and _contains_outcome_guarantee(value):
            errors.append(f"{path}:legal_or_permitting_outcome_guarantee")
    return errors


def _walk_items(value: Any, path: str = "$") -> Iterable[tuple[str, str, Any]]:
    if isinstance(value, dict):
        for key, child in value.items():
            child_key = str(key)
            child_path = f"{path}.{child_key}"
            yield child_path, child_key, child
            yield from _walk_items(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_items(child, f"{path}[{index}]")


def _looks_like_url_key(key: str) -> bool:
    return key == "url" or key.endswith("_url") or key.endswith("url") or key in {"canonical", "canonical_url", "requested_url"}


def _contains_outcome_guarantee(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in OUTCOME_GUARANTEE_MARKERS)


def _truthy_reference(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict, tuple, set)):
        return bool(value)
    return True


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())
