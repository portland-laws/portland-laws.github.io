"""Fixture-first processor handoff dry-run manifest v8.

This module turns source recrawl preflight queue v8 fixtures into inert processor
handoff planning manifests. It never invokes processors, fetches URLs, opens
DevHub, reads private documents, persists raw bodies, uploads, submits, pays,
schedules, certifies, or makes legal/permitting guarantees.
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from ppd.agent_readiness.source_recrawl_preflight_queue_v8 import (
    REQUIRED_SKIPPED_REASON_CODES,
    validate_source_recrawl_preflight_queue_v8,
)

EXACT_OFFLINE_VALIDATION_COMMANDS: list[list[str]] = [
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]

FORBIDDEN_RAW_OR_PRIVATE_KEYS = {
    "raw_body",
    "body",
    "html",
    "pdf_bytes",
    "downloaded_document",
    "downloaded_or_raw_crawl_artifacts",
    "screenshot",
    "trace",
    "har",
    "cookies",
    "auth_state",
    "credentials",
    "password",
    "payment_details",
    "private_document_path",
    "private_document_contents",
}

FORBIDDEN_ACTION_CLAIM_FIELDS = {
    "live_crawl_execution_claims",
    "private_session_auth_artifacts",
    "official_action_completion_claims",
    "legal_or_permitting_guarantees",
    "uploads",
    "submissions",
    "certifications",
    "payments",
    "scheduled_inspections",
    "devhub_opened",
    "processors_invoked",
    "raw_artifacts_downloaded",
}

SUPPORTED_PROCESSORS_BY_SOURCE_TYPE = {
    "public_html": "ipfs_datasets_py.web_archive_html_processor",
    "devhub_public": "ipfs_datasets_py.web_archive_html_processor",
    "public_pdf": "ipfs_datasets_py.public_pdf_metadata_processor",
    "public_form": "ipfs_datasets_py.public_form_metadata_processor",
}


@dataclass(frozen=True)
class ValidationResult:
    """Validation outcome for processor handoff dry-run manifest v8."""

    accepted: bool
    errors: tuple[str, ...]


def load_source_recrawl_preflight_queue_v8_fixture(path: Path) -> dict[str, Any]:
    """Load a committed source recrawl preflight queue v8 fixture."""

    return json.loads(path.read_text(encoding="utf-8"))


def build_processor_handoff_dry_run_manifest_v8(
    source_recrawl_preflight_queue_v8_fixture: Mapping[str, Any],
    *,
    fixture_ref: str = "source_recrawl_preflight_queue_v8_fixture",
) -> dict[str, Any]:
    """Build an inert processor handoff dry-run manifest from a v8 queue fixture."""

    preflight_validation = validate_source_recrawl_preflight_queue_v8(source_recrawl_preflight_queue_v8_fixture)
    if not preflight_validation.accepted:
        raise ValueError("source recrawl preflight queue v8 fixture is invalid: " + "; ".join(preflight_validation.errors))

    candidate_rows = list(source_recrawl_preflight_queue_v8_fixture.get("ordered_public_source_candidates", []))
    allowlist_by_source_id = {
        str(row.get("source_id")): row
        for row in _mapping_sequence(source_recrawl_preflight_queue_v8_fixture.get("allowlist_decisions"))
    }
    robots_by_source_id = {
        str(row.get("source_id")): row
        for row in _mapping_sequence(source_recrawl_preflight_queue_v8_fixture.get("robots_policy_decision_placeholders"))
    }

    planned_invocations: list[dict[str, Any]] = []
    skipped_rows: list[dict[str, Any]] = []

    for order, candidate in enumerate(_mapping_sequence(candidate_rows), start=1):
        source_id = _text(candidate.get("source_id"))
        source_type = _text(candidate.get("source_type"))
        canonical_url = _text(candidate.get("url"))
        allowlist_row = allowlist_by_source_id.get(source_id, {})
        robots_row = robots_by_source_id.get(source_id, {})
        processor_name = SUPPORTED_PROCESSORS_BY_SOURCE_TYPE.get(source_type)

        if not processor_name:
            skipped_rows.append(
                {
                    "source_id": source_id,
                    "canonical_url": canonical_url,
                    "source_type": source_type,
                    "skipped_reason": "unsupported_content_type",
                    "source_queue_order": candidate.get("order", order),
                    "raw_body_persisted": False,
                }
            )
            continue

        planned_invocations.append(
            {
                "invocation_id": f"processor-handoff-dry-run-v8::{order:03d}::{source_id}",
                "source_queue_order": candidate.get("order", order),
                "source_id": source_id,
                "canonical_url": canonical_url,
                "requested_url_placeholder": canonical_url,
                "source_type": source_type,
                "processor_name": processor_name,
                "processor_version_placeholder": "fixture_pending_no_processor_invocation",
                "invocation_mode": "dry_run_plan_only_from_preflight_fixture",
                "allowlist_decision": _text(allowlist_row.get("decision")),
                "robots_policy_decision_placeholder": _text(robots_row.get("robots_decision")),
                "policy_decision_placeholder": _text(robots_row.get("policy_decision")),
                "response_metadata_placeholder": {
                    "http_status": "placeholder_pending_no_fetch",
                    "content_type": "placeholder_pending_no_fetch",
                    "redirect_chain": [],
                    "capture_started_at": "not_started_dry_run_only",
                    "capture_finished_at": "not_started_dry_run_only",
                },
                "content_hash_placeholder": {
                    "algorithm": "sha256",
                    "value": "placeholder_pending_processor_output_no_raw_body",
                    "raw_body_persisted": False,
                },
                "normalized_document_reference_placeholder": {
                    "document_id": f"doc-placeholder-{source_id}",
                    "source_id": source_id,
                    "normalized_ref": f"ppd://documents/placeholders/{source_id}",
                    "content_hash": "sha256:placeholder_pending_processor_output_no_raw_body",
                    "status": "placeholder_pending_processor_output",
                },
                "no_raw_body_persistence_assertion": {
                    "no_raw_body_persisted": True,
                    "raw_artifact_ref_allowed": False,
                    "manifest_only": True,
                },
            }
        )

    skipped_rows.extend(_skipped_rows_from_preflight(source_recrawl_preflight_queue_v8_fixture))

    manifest = {
        "manifest_version": "v8",
        "fixture_scope": "source_recrawl_preflight_queue_v8_fixtures_only",
        "source_recrawl_preflight_queue_fixture_ref": fixture_ref,
        "source_queue_version": source_recrawl_preflight_queue_v8_fixture.get("queue_version"),
        "authorization_reference": source_recrawl_preflight_queue_v8_fixture.get("authorization_reference"),
        "planned_processor_invocations": planned_invocations,
        "response_metadata_placeholders": [
            {
                "invocation_id": row["invocation_id"],
                "source_id": row["source_id"],
                "response_metadata_placeholder": copy.deepcopy(row["response_metadata_placeholder"]),
            }
            for row in planned_invocations
        ],
        "content_hash_placeholders": [
            {
                "invocation_id": row["invocation_id"],
                "source_id": row["source_id"],
                "content_hash_placeholder": copy.deepcopy(row["content_hash_placeholder"]),
            }
            for row in planned_invocations
        ],
        "normalized_document_reference_placeholders": [
            {
                "invocation_id": row["invocation_id"],
                "source_id": row["source_id"],
                "normalized_document_reference_placeholder": copy.deepcopy(row["normalized_document_reference_placeholder"]),
            }
            for row in planned_invocations
        ],
        "no_raw_body_persistence_assertions": [
            {
                "invocation_id": row["invocation_id"],
                "source_id": row["source_id"],
                **copy.deepcopy(row["no_raw_body_persistence_assertion"]),
            }
            for row in planned_invocations
        ],
        "skipped_source_rows": skipped_rows,
        "blocked_activity_assertions": {
            "processors_invoked": False,
            "live_urls_fetched": False,
            "raw_artifacts_downloaded": False,
            "devhub_opened": False,
            "private_documents_read": False,
            "uploads_performed": False,
            "submissions_performed": False,
            "certifications_performed": False,
            "payments_performed": False,
            "inspections_scheduled": False,
            "legal_or_permitting_guarantees_made": False,
        },
        "exact_offline_validation_commands": copy.deepcopy(EXACT_OFFLINE_VALIDATION_COMMANDS),
        "validation_commands": copy.deepcopy(EXACT_OFFLINE_VALIDATION_COMMANDS),
    }
    return manifest


def validate_processor_handoff_dry_run_manifest_v8(manifest: Mapping[str, Any]) -> ValidationResult:
    """Validate that a processor handoff dry-run manifest v8 is complete and inert."""

    errors: list[str] = []

    if manifest.get("manifest_version") != "v8":
        errors.append("manifest_version must be v8")
    if manifest.get("fixture_scope") != "source_recrawl_preflight_queue_v8_fixtures_only":
        errors.append("fixture_scope must be source_recrawl_preflight_queue_v8_fixtures_only")
    if not _non_empty_string(manifest.get("source_recrawl_preflight_queue_fixture_ref")):
        errors.append("source_recrawl_preflight_queue_fixture_ref is required")
    if manifest.get("source_queue_version") != "v8":
        errors.append("source_queue_version must be v8")

    planned_invocations = manifest.get("planned_processor_invocations")
    if not _non_empty_sequence(planned_invocations):
        errors.append("planned_processor_invocations must be non-empty")
    else:
        _validate_planned_invocations(planned_invocations, errors)

    _validate_placeholder_rows(
        manifest.get("response_metadata_placeholders"),
        "response_metadata_placeholders",
        "response_metadata_placeholder",
        errors,
    )
    _validate_placeholder_rows(
        manifest.get("content_hash_placeholders"),
        "content_hash_placeholders",
        "content_hash_placeholder",
        errors,
    )
    _validate_placeholder_rows(
        manifest.get("normalized_document_reference_placeholders"),
        "normalized_document_reference_placeholders",
        "normalized_document_reference_placeholder",
        errors,
    )
    _validate_no_raw_body_assertions(manifest.get("no_raw_body_persistence_assertions"), errors)
    _validate_skipped_rows(manifest.get("skipped_source_rows"), errors)
    _validate_blocked_activity_assertions(manifest.get("blocked_activity_assertions"), errors)

    if manifest.get("exact_offline_validation_commands") != EXACT_OFFLINE_VALIDATION_COMMANDS:
        errors.append("exact_offline_validation_commands must contain only the exact daemon self-test command")
    if manifest.get("validation_commands") != EXACT_OFFLINE_VALIDATION_COMMANDS:
        errors.append("validation_commands must contain only the exact daemon self-test command")

    _validate_no_forbidden_keys(manifest, errors)
    return ValidationResult(accepted=not errors, errors=tuple(errors))


def build_processor_handoff_dry_run_manifest_v8_fixture() -> dict[str, Any]:
    """Return a valid deterministic fixture-backed dry-run manifest."""

    from ppd.agent_readiness.source_recrawl_preflight_queue_v8 import build_source_recrawl_preflight_queue_v8_fixture

    return build_processor_handoff_dry_run_manifest_v8(
        build_source_recrawl_preflight_queue_v8_fixture(),
        fixture_ref="generated:build_source_recrawl_preflight_queue_v8_fixture",
    )


def _validate_planned_invocations(rows: Sequence[Any], errors: list[str]) -> None:
    seen_ids: set[str] = set()
    for index, row in enumerate(rows):
        prefix = f"planned_processor_invocations[{index}]"
        if not isinstance(row, Mapping):
            errors.append(f"{prefix} must be an object")
            continue
        invocation_id = row.get("invocation_id")
        if not _non_empty_string(invocation_id):
            errors.append(f"{prefix}.invocation_id is required")
        elif invocation_id in seen_ids:
            errors.append(f"{prefix}.invocation_id must be unique")
        else:
            seen_ids.add(str(invocation_id))
        if row.get("invocation_mode") != "dry_run_plan_only_from_preflight_fixture":
            errors.append(f"{prefix}.invocation_mode must be dry_run_plan_only_from_preflight_fixture")
        if not _non_empty_string(row.get("processor_name")):
            errors.append(f"{prefix}.processor_name is required")
        if row.get("processor_version_placeholder") != "fixture_pending_no_processor_invocation":
            errors.append(f"{prefix}.processor_version_placeholder must show no processor invocation")
        if not _non_empty_string(row.get("source_id")):
            errors.append(f"{prefix}.source_id is required")
        if not _non_empty_string(row.get("canonical_url")):
            errors.append(f"{prefix}.canonical_url is required")
        response_placeholder = row.get("response_metadata_placeholder")
        if not isinstance(response_placeholder, Mapping) or response_placeholder.get("http_status") != "placeholder_pending_no_fetch":
            errors.append(f"{prefix}.response_metadata_placeholder must remain pending no-fetch")
        content_hash = row.get("content_hash_placeholder")
        if not isinstance(content_hash, Mapping) or content_hash.get("raw_body_persisted") is not False:
            errors.append(f"{prefix}.content_hash_placeholder.raw_body_persisted must be false")
        normalized = row.get("normalized_document_reference_placeholder")
        if not isinstance(normalized, Mapping) or normalized.get("status") != "placeholder_pending_processor_output":
            errors.append(f"{prefix}.normalized_document_reference_placeholder must remain pending")
        no_raw_body = row.get("no_raw_body_persistence_assertion")
        if not isinstance(no_raw_body, Mapping) or no_raw_body.get("no_raw_body_persisted") is not True:
            errors.append(f"{prefix}.no_raw_body_persistence_assertion.no_raw_body_persisted must be true")
        if isinstance(no_raw_body, Mapping) and no_raw_body.get("raw_artifact_ref_allowed") is not False:
            errors.append(f"{prefix}.no_raw_body_persistence_assertion.raw_artifact_ref_allowed must be false")


def _validate_placeholder_rows(rows: Any, collection_name: str, placeholder_key: str, errors: list[str]) -> None:
    if not _non_empty_sequence(rows):
        errors.append(f"{collection_name} must be non-empty")
        return
    for index, row in enumerate(rows):
        prefix = f"{collection_name}[{index}]"
        if not isinstance(row, Mapping):
            errors.append(f"{prefix} must be an object")
            continue
        if not _non_empty_string(row.get("invocation_id")):
            errors.append(f"{prefix}.invocation_id is required")
        if not _non_empty_string(row.get("source_id")):
            errors.append(f"{prefix}.source_id is required")
        if not isinstance(row.get(placeholder_key), Mapping):
            errors.append(f"{prefix}.{placeholder_key} must be an object")


def _validate_no_raw_body_assertions(rows: Any, errors: list[str]) -> None:
    if not _non_empty_sequence(rows):
        errors.append("no_raw_body_persistence_assertions must be non-empty")
        return
    for index, row in enumerate(rows):
        prefix = f"no_raw_body_persistence_assertions[{index}]"
        if not isinstance(row, Mapping):
            errors.append(f"{prefix} must be an object")
            continue
        if row.get("no_raw_body_persisted") is not True:
            errors.append(f"{prefix}.no_raw_body_persisted must be true")
        if row.get("raw_artifact_ref_allowed") is not False:
            errors.append(f"{prefix}.raw_artifact_ref_allowed must be false")
        if row.get("manifest_only") is not True:
            errors.append(f"{prefix}.manifest_only must be true")


def _validate_skipped_rows(rows: Any, errors: list[str]) -> None:
    if not _non_empty_sequence(rows):
        errors.append("skipped_source_rows must be non-empty")
        return
    observed: set[str] = set()
    for index, row in enumerate(rows):
        prefix = f"skipped_source_rows[{index}]"
        if not isinstance(row, Mapping):
            errors.append(f"{prefix} must be an object")
            continue
        reason = row.get("skipped_reason")
        if _non_empty_string(reason):
            observed.add(str(reason))
        else:
            errors.append(f"{prefix}.skipped_reason is required")
        if row.get("raw_body_persisted") is not False:
            errors.append(f"{prefix}.raw_body_persisted must be false")
    missing = sorted(REQUIRED_SKIPPED_REASON_CODES - observed)
    if missing:
        errors.append("skipped_source_rows missing required preflight reasons: " + ", ".join(missing))


def _validate_blocked_activity_assertions(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("blocked_activity_assertions must be an object")
        return
    required_false = {
        "processors_invoked",
        "live_urls_fetched",
        "raw_artifacts_downloaded",
        "devhub_opened",
        "private_documents_read",
        "uploads_performed",
        "submissions_performed",
        "certifications_performed",
        "payments_performed",
        "inspections_scheduled",
        "legal_or_permitting_guarantees_made",
    }
    for key in sorted(required_false):
        if value.get(key) is not False:
            errors.append(f"blocked_activity_assertions.{key} must be false")


def _validate_no_forbidden_keys(value: Any, errors: list[str], path: str = "manifest") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text in FORBIDDEN_RAW_OR_PRIVATE_KEYS:
                errors.append(f"{child_path} is forbidden in processor handoff dry-run manifest v8")
            if key_text in FORBIDDEN_ACTION_CLAIM_FIELDS and child not in (False, [], (), "", None):
                errors.append(f"{child_path} must not claim live or consequential activity")
            _validate_no_forbidden_keys(child, errors, child_path)
    elif isinstance(value, Sequence) and not isinstance(value, str):
        for index, child in enumerate(value):
            _validate_no_forbidden_keys(child, errors, f"{path}[{index}]")


def _skipped_rows_from_preflight(preflight_queue: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(_mapping_sequence(preflight_queue.get("skipped_url_reason_rows")), start=1):
        rows.append(
            {
                "source_id": f"skipped-preflight-placeholder-{index:03d}",
                "canonical_url": _text(row.get("example_url")),
                "source_type": "preflight_skip_placeholder",
                "skipped_reason": _text(row.get("reason_code")),
                "source_queue_order": None,
                "raw_body_persisted": False,
            }
        )
    return rows


def _mapping_sequence(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, str):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _non_empty_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, str) and bool(value)


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)
