"""Fixture-first public source refresh batch packet builder.

This module deliberately performs no network I/O, processor invocation, file download,
schedule mutation, or source registry mutation. It turns already-collected planning
fixtures into ordered batch manifests that reviewers can inspect before any live
refresh work is considered.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import urlparse

DEFAULT_ALLOWED_HOSTS = (
    "www.portland.gov",
    "devhub.portlandoregon.gov",
    "www.portlandoregon.gov",
    "www.portlandmaps.com",
)

FORBIDDEN_OPERATIONS = (
    "fetch_urls",
    "invoke_processors",
    "download_files",
    "mutate_schedules",
    "mutate_registries",
    "persist_raw_bodies",
    "authenticated_automation",
)

PRIVATE_SOURCE_TYPES = {"devhub_authenticated", "private", "authenticated"}
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
)
FORBIDDEN_REFERENCE_FIELDS = {
    "archive_artifact_ref",
    "archive_ref",
    "body_ref",
    "download_path",
    "download_ref",
    "downloaded_file_ref",
    "har_ref",
    "raw_body",
    "raw_body_path",
    "raw_body_ref",
    "screenshot_ref",
    "trace_ref",
    "warc_ref",
}
LIVE_EXECUTION_TRUE_FIELDS = {
    "download_files",
    "execute_processors",
    "fetch_urls",
    "invoke_processors",
    "live_fetch_allowed",
    "network_io_allowed",
    "processor_execution_allowed",
    "processor_invocation_allowed",
}
MUTATION_TRUE_FIELDS = {
    "active_registry_mutation",
    "active_schedule",
    "mutate_registries",
    "mutate_schedules",
    "registry_mutation_allowed",
    "schedule_mutation_allowed",
}


@dataclass(frozen=True)
class SourceRefreshBatchInputs:
    """Input packet paths for a fixture-first source refresh batch."""

    runbook_candidate_path: Path
    coverage_gap_packet_path: Path
    freshness_badge_packet_path: Path


def load_json_file(path: Path) -> Mapping[str, Any]:
    """Load a JSON object from ``path`` with deterministic validation."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object in {path}")
    return payload


def validate_public_source_refresh_batch_inputs(
    runbook_candidate: Mapping[str, Any],
    *,
    allowed_hosts: Sequence[str] = DEFAULT_ALLOWED_HOSTS,
) -> list[str]:
    """Return deterministic validation errors for a public refresh runbook candidate."""

    errors: list[str] = []
    reviewer_owner_fields = runbook_candidate.get("reviewer_owner_fields")
    if not isinstance(reviewer_owner_fields, dict):
        errors.append("reviewer_owner_fields_missing")
    else:
        for field in ("primary_reviewer", "backup_reviewer", "review_queue"):
            value = reviewer_owner_fields.get(field)
            if not isinstance(value, str) or not value:
                errors.append(f"reviewer_owner_fields.{field}_missing")

    abort_criteria = runbook_candidate.get("abort_criteria")
    if not isinstance(abort_criteria, list) or not abort_criteria:
        errors.append("abort_criteria_missing")
    else:
        rendered_abort_criteria = " ".join(str(item).lower() for item in abort_criteria)
        for marker in ("allowlist", "robots", "policy", "rate", "authenticated", "download", "processor", "schedule", "registry"):
            if marker not in rendered_abort_criteria:
                errors.append(f"abort_criteria_missing_{marker}")

    candidate_sources = runbook_candidate.get("candidate_sources")
    if not isinstance(candidate_sources, list):
        return errors + ["candidate_sources_missing"]

    allowlist = tuple(allowed_hosts)
    for index, source in enumerate(candidate_sources):
        label = f"candidate_sources[{index}]"
        if not isinstance(source, dict):
            errors.append(f"{label}_not_object")
            continue
        errors.extend(_source_rejection_errors(source, label, allowlist))
    return errors


def build_public_source_refresh_batch_packet(
    inputs: SourceRefreshBatchInputs,
    *,
    allowed_hosts: Sequence[str] = DEFAULT_ALLOWED_HOSTS,
) -> dict[str, Any]:
    """Build an ordered metadata-only source refresh batch packet."""

    runbook_candidate = load_json_file(inputs.runbook_candidate_path)
    coverage_gap_packet = load_json_file(inputs.coverage_gap_packet_path)
    freshness_badge_packet = load_json_file(inputs.freshness_badge_packet_path)

    validation_errors = validate_public_source_refresh_batch_inputs(runbook_candidate, allowed_hosts=allowed_hosts)
    if validation_errors:
        raise ValueError("public source refresh batch packet failed validation: " + "; ".join(validation_errors))

    runbook_sources = _require_sequence(runbook_candidate, "candidate_sources")
    coverage_gaps = _index_by_source_id(_require_sequence(coverage_gap_packet, "coverage_gaps"), "coverage_gaps")
    freshness_badges = _index_by_source_id(_require_sequence(freshness_badge_packet, "freshness_badges"), "freshness_badges")
    reviewer_owner_fields = _require_mapping(runbook_candidate, "reviewer_owner_fields")
    abort_criteria = _require_sequence(runbook_candidate, "abort_criteria")

    manifests = []
    allowlist = tuple(allowed_hosts)
    for position, source in enumerate(runbook_sources, start=1):
        source_mapping = _as_mapping(source, f"candidate_sources[{position - 1}]")
        source_id = _require_str(source_mapping, "source_id")
        canonical_url = _require_str(source_mapping, "canonical_url")
        host = _host_for_url(canonical_url)
        expected_delta = {
            "source_id": source_id,
            "metadata_only": True,
            "registry_mutation_allowed": False,
            "schedule_mutation_allowed": False,
            "expected_fields": _expected_delta_fields(source_id, coverage_gaps.get(source_id), freshness_badges.get(source_id)),
        }
        manifests.append(
            {
                "batch_order": position,
                "source_id": source_id,
                "canonical_url": canonical_url,
                "host": host,
                "source_type": _require_str(source_mapping, "source_type"),
                "owning_surface": _require_str(source_mapping, "owning_surface"),
                "refresh_reason": _require_str(source_mapping, "refresh_reason"),
                "allowlist_decision": {"allowed": True, "allowed_hosts": list(allowlist), "decision_basis": "fixture_host_match"},
                "robots_policy": dict(_require_mapping(source_mapping, "robots_policy")),
                "policy_evidence": dict(_require_mapping(source_mapping, "policy_evidence")),
                "rate_limit_window": dict(_require_mapping(source_mapping, "rate_limit_window")),
                "processor_policy": _require_str(source_mapping, "processor_policy"),
                "expected_metadata_only_delta": expected_delta,
                "reviewer_owner_fields": dict(reviewer_owner_fields),
                "abort_criteria": list(abort_criteria),
                "forbidden_operations": list(FORBIDDEN_OPERATIONS),
            }
        )

    return {
        "packet_type": "ppd_public_source_refresh_batch_packet",
        "packet_version": "1.1",
        "fixture_first": True,
        "side_effect_boundary": {
            "network_io_allowed": False,
            "processor_invocation_allowed": False,
            "downloads_allowed": False,
            "schedule_mutation_allowed": False,
            "registry_mutation_allowed": False,
            "raw_body_persistence_allowed": False,
        },
        "input_refs": {
            "runbook_candidate": str(inputs.runbook_candidate_path),
            "source_registry_coverage_gap_packet": str(inputs.coverage_gap_packet_path),
            "source_freshness_badge_packet": str(inputs.freshness_badge_packet_path),
        },
        "batch_manifests": manifests,
        "blocked_sources": [],
        "abort_criteria": list(abort_criteria),
        "reviewer_owner_fields": dict(reviewer_owner_fields),
    }


def build_public_source_refresh_batch_packet_from_files(runbook_candidate_path: Path, coverage_gap_packet_path: Path, freshness_badge_packet_path: Path) -> dict[str, Any]:
    """Convenience wrapper for callers that already have fixture paths."""

    return build_public_source_refresh_batch_packet(
        SourceRefreshBatchInputs(runbook_candidate_path=runbook_candidate_path, coverage_gap_packet_path=coverage_gap_packet_path, freshness_badge_packet_path=freshness_badge_packet_path)
    )


def _source_rejection_errors(source: Mapping[str, Any], label: str, allowlist: Sequence[str]) -> list[str]:
    errors: list[str] = []
    source_id = source.get("source_id", label)
    canonical_url = source.get("canonical_url")
    if not isinstance(canonical_url, str) or not canonical_url:
        errors.append(f"{source_id}:canonical_url_missing")
        return errors

    host = _host_for_url(canonical_url)
    parsed = urlparse(canonical_url)
    path = parsed.path.lower()
    if host not in allowlist:
        errors.append(f"{source_id}:outside_allowlist")
    if any(marker in path for marker in PRIVATE_URL_MARKERS):
        errors.append(f"{source_id}:private_or_authenticated_target")
    if "/download" in path or parsed.query.lower().startswith("download="):
        errors.append(f"{source_id}:download_target_reference")

    source_type = source.get("source_type")
    if isinstance(source_type, str) and source_type.lower() in PRIVATE_SOURCE_TYPES:
        errors.append(f"{source_id}:private_or_authenticated_source_type")
    privacy_classification = source.get("privacy_classification")
    if isinstance(privacy_classification, str) and privacy_classification.lower() in {"private", "authenticated", "account_scoped"}:
        errors.append(f"{source_id}:private_or_authenticated_privacy_classification")

    for evidence_key in ("robots_policy", "policy_evidence", "rate_limit_window"):
        evidence = source.get(evidence_key)
        if not isinstance(evidence, dict) or not isinstance(evidence.get("evidence_ref"), str) or not evidence.get("evidence_ref"):
            errors.append(f"{source_id}:{evidence_key}_evidence_missing")
    rate_limit_window = source.get("rate_limit_window")
    if isinstance(rate_limit_window, dict):
        window = rate_limit_window.get("window")
        if not isinstance(window, str) or not window:
            errors.append(f"{source_id}:rate_limit_window_missing")

    processor_policy = source.get("processor_policy")
    if processor_policy != "metadata_only_no_processor":
        errors.append(f"{source_id}:processor_execution_claim")

    for key, value in _walk_mapping_items(source):
        if key in FORBIDDEN_REFERENCE_FIELDS and value:
            errors.append(f"{source_id}:forbidden_reference:{key}")
        if key in LIVE_EXECUTION_TRUE_FIELDS and value is True:
            errors.append(f"{source_id}:live_fetch_or_processor_execution:{key}")
        if key in MUTATION_TRUE_FIELDS and value is True:
            errors.append(f"{source_id}:active_schedule_or_registry_mutation:{key}")
    return errors


def _expected_delta_fields(source_id: str, coverage_gap: Mapping[str, Any] | None, freshness_badge: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    fields: list[dict[str, Any]] = []
    if coverage_gap is not None:
        for field_name in _require_sequence(coverage_gap, "missing_metadata_fields"):
            if not isinstance(field_name, str):
                raise ValueError(f"missing_metadata_fields for {source_id} must be strings")
            fields.append({"field": field_name, "reason": "registry_coverage_gap", "expected_change": "populate_metadata_if_available_from_existing_evidence"})
    if freshness_badge is not None:
        fields.append({"field": "freshness_status", "reason": "source_freshness_badge", "current_badge": _require_str(freshness_badge, "freshness_status"), "expected_change": "record_reviewer_observed_status_without_recrawl"})
        fields.append({"field": "last_verified_at", "reason": "source_freshness_badge", "current_value": _require_str(freshness_badge, "last_verified_at"), "expected_change": "carry_forward_existing_verification_timestamp"})
    if not fields:
        fields.append({"field": "review_packet_status", "reason": "runbook_candidate_only", "expected_change": "mark_ready_for_manual_review_only"})
    return fields


def _walk_mapping_items(value: Any) -> list[tuple[str, Any]]:
    items: list[tuple[str, Any]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            normalized_key = str(key).lower()
            items.append((normalized_key, child))
            items.extend(_walk_mapping_items(child))
    elif isinstance(value, list):
        for child in value:
            items.extend(_walk_mapping_items(child))
    return items


def _index_by_source_id(items: Sequence[Any], label: str) -> dict[str, Mapping[str, Any]]:
    indexed: dict[str, Mapping[str, Any]] = {}
    for index, item in enumerate(items):
        mapping = _as_mapping(item, f"{label}[{index}]")
        source_id = _require_str(mapping, "source_id")
        indexed[source_id] = mapping
    return indexed


def _host_for_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
        raise ValueError(f"unsupported or invalid URL: {url}")
    return parsed.netloc.lower()


def _require_mapping(payload: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be an object")
    return value


def _require_sequence(payload: Mapping[str, Any], key: str) -> Sequence[Any]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list")
    return value


def _require_str(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _as_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value
