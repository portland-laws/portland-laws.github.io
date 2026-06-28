"""Validation for public refresh metadata manifest dry-run plan v1.

The dry-run plan is commit-safe metadata. It must describe the intended public
refresh without storing raw/downloaded artifacts or implying live crawl results,
official PP&D action completion, source promotion, or active mutation.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any

SCHEMA_VERSION = "public-refresh-metadata-manifest-dry-run-plan.v1"

PRIVATE_ARTIFACT_TOKENS = (
    "auth_state",
    "browser_state",
    "cookie",
    "cookies",
    "credential",
    "devhub_session",
    "downloaded_artifact",
    "downloaded_document",
    "har",
    "password",
    "private_artifact",
    "raw_body",
    "raw_crawl_output",
    "session_storage",
    "screenshot",
    "trace",
)

LIVE_CRAWL_CLAIM_TOKENS = (
    "crawled live",
    "devhub verified",
    "fetched from devhub",
    "live crawl completed",
    "live crawl succeeded",
    "live devhub crawl",
    "observed in authenticated devhub",
)

PROMOTION_CLAIM_TOKENS = (
    "archive manifest promoted",
    "archive promoted",
    "current source promoted",
    "promote to active",
    "promoted source registry",
    "source registry promoted",
)

OFFICIAL_COMPLETION_CLAIM_TOKENS = (
    "approved by pp&d",
    "approved by ppd",
    "city accepted",
    "official action completed",
    "permit issued",
    "request submitted",
    "submission completed",
)

LEGAL_GUARANTEE_TOKENS = (
    "guaranteed approval",
    "guarantees approval",
    "legally sufficient",
    "permit guarantee",
    "will be approved",
    "will satisfy code",
)

MUTATION_FLAGS = (
    "apply_changes",
    "execute",
    "finalize",
    "live_crawl",
    "mutate",
    "promote_archive_manifest",
    "promote_source_registry",
    "publish",
    "submit",
    "upload",
    "write_current_corpus",
)


@dataclass(frozen=True)
class ValidationIssue:
    """A deterministic validation failure with a stable code and path."""

    code: str
    path: str
    message: str


class PublicRefreshMetadataManifestDryRunPlanV1Error(ValueError):
    """Raised when a dry-run plan fails validation."""

    def __init__(self, issues: Sequence[ValidationIssue]) -> None:
        self.issues = tuple(issues)
        formatted = "; ".join(f"{issue.code} at {issue.path}: {issue.message}" for issue in issues)
        super().__init__(formatted)


def validate_public_refresh_metadata_manifest_dry_run_plan_v1(plan: Mapping[str, Any]) -> None:
    """Validate a public refresh metadata manifest dry-run plan v1.

    The function raises PublicRefreshMetadataManifestDryRunPlanV1Error when the
    plan is not commit-safe or omits required dry-run evidence.
    """

    issues: list[ValidationIssue] = []

    if not isinstance(plan, Mapping):
        raise TypeError("plan must be a mapping")

    schema_version = plan.get("schema_version")
    if schema_version != SCHEMA_VERSION:
        issues.append(
            ValidationIssue(
                "invalid_schema_version",
                "schema_version",
                f"expected {SCHEMA_VERSION!r}",
            )
        )

    _require_non_empty_sequence(plan, "preflight_checklist_references", issues)
    _require_placeholder_rows(
        plan,
        "source_registry_placeholder_rows",
        ("source_id", "canonical_url", "source_type", "freshness_status"),
        issues,
    )
    _require_placeholder_rows(
        plan,
        "archive_manifest_placeholder_rows",
        (
            "source_id",
            "canonical_url",
            "redirect_chain",
            "http_status",
            "content_type",
            "content_hash",
            "skipped_reason",
            "no_raw_body_persisted",
        ),
        issues,
    )
    _require_non_empty_sequence(plan, "redirect_chain_placeholders", issues)
    _require_non_empty_sequence(plan, "http_status_placeholders", issues)
    _require_non_empty_sequence(plan, "content_type_expectations", issues)
    _require_mapping(plan, "content_hash_placeholder_policy", issues)
    _require_non_empty_sequence(plan, "freshness_status_impacts", issues)
    _require_non_empty_sequence(plan, "skipped_reason_handling", issues)
    _require_non_empty_sequence(plan, "reviewer_holds", issues)
    _require_non_empty_sequence(plan, "rollback_notes", issues)
    _require_non_empty_sequence(plan, "validation_commands", issues)

    for index, row in enumerate(_as_sequence(plan.get("archive_manifest_placeholder_rows"))):
        if not isinstance(row, Mapping):
            continue
        if row.get("no_raw_body_persisted") is not True:
            issues.append(
                ValidationIssue(
                    "raw_body_persistence_not_blocked",
                    f"archive_manifest_placeholder_rows[{index}].no_raw_body_persisted",
                    "archive placeholder rows must explicitly set no_raw_body_persisted to true",
                )
            )

    _reject_private_artifact_refs(plan, issues)
    _reject_claim_tokens(plan, LIVE_CRAWL_CLAIM_TOKENS, "live_crawl_or_devhub_claim", issues)
    _reject_claim_tokens(plan, PROMOTION_CLAIM_TOKENS, "active_source_or_archive_promotion_claim", issues)
    _reject_claim_tokens(plan, OFFICIAL_COMPLETION_CLAIM_TOKENS, "official_action_completion_claim", issues)
    _reject_claim_tokens(plan, LEGAL_GUARANTEE_TOKENS, "legal_or_permitting_guarantee", issues)
    _reject_active_mutation_flags(plan, issues)

    if issues:
        raise PublicRefreshMetadataManifestDryRunPlanV1Error(issues)


def collect_public_refresh_metadata_manifest_dry_run_plan_v1_issues(
    plan: Mapping[str, Any],
) -> tuple[ValidationIssue, ...]:
    """Return validation issues instead of raising."""

    try:
        validate_public_refresh_metadata_manifest_dry_run_plan_v1(plan)
    except PublicRefreshMetadataManifestDryRunPlanV1Error as error:
        return error.issues
    return ()


def _require_mapping(plan: Mapping[str, Any], key: str, issues: list[ValidationIssue]) -> None:
    value = plan.get(key)
    if not isinstance(value, Mapping) or not value:
        issues.append(ValidationIssue(f"missing_{key}", key, "expected a non-empty object"))


def _require_non_empty_sequence(plan: Mapping[str, Any], key: str, issues: list[ValidationIssue]) -> None:
    value = plan.get(key)
    if isinstance(value, str) or not isinstance(value, Sequence) or not value:
        issues.append(ValidationIssue(f"missing_{key}", key, "expected a non-empty list"))


def _require_placeholder_rows(
    plan: Mapping[str, Any],
    key: str,
    required_fields: Iterable[str],
    issues: list[ValidationIssue],
) -> None:
    rows = plan.get(key)
    if isinstance(rows, str) or not isinstance(rows, Sequence) or not rows:
        issues.append(ValidationIssue(f"missing_{key}", key, "expected one or more placeholder rows"))
        return

    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            issues.append(ValidationIssue(f"invalid_{key}_row", f"{key}[{index}]", "expected object row"))
            continue
        for field in required_fields:
            if _is_blank(row.get(field)):
                issues.append(
                    ValidationIssue(
                        f"missing_{field}",
                        f"{key}[{index}].{field}",
                        "required placeholder field is missing",
                    )
                )


def _reject_private_artifact_refs(plan: Mapping[str, Any], issues: list[ValidationIssue]) -> None:
    for path, value in _walk(plan):
        if not isinstance(value, str):
            continue
        normalized = _normalize(value)
        if any(token in normalized for token in PRIVATE_ARTIFACT_TOKENS):
            issues.append(
                ValidationIssue(
                    "private_raw_or_downloaded_artifact_ref",
                    path,
                    "dry-run plans must not reference private, raw, trace, screenshot, HAR, or downloaded artifacts",
                )
            )
        if _looks_like_raw_or_downloaded_path(normalized):
            issues.append(
                ValidationIssue(
                    "private_raw_or_downloaded_artifact_path",
                    path,
                    "dry-run plans must not include raw, private, or downloaded artifact paths",
                )
            )


def _reject_claim_tokens(
    plan: Mapping[str, Any],
    tokens: Sequence[str],
    code: str,
    issues: list[ValidationIssue],
) -> None:
    for path, value in _walk(plan):
        if isinstance(value, str):
            normalized = _normalize(value)
            if any(token in normalized for token in tokens):
                issues.append(ValidationIssue(code, path, "claim is not allowed in a public dry-run plan"))


def _reject_active_mutation_flags(plan: Mapping[str, Any], issues: list[ValidationIssue]) -> None:
    for path, value in _walk(plan):
        key = path.rsplit(".", 1)[-1]
        key = key.split("[", 1)[0]
        normalized_key = _normalize(key).replace("-", "_")
        if normalized_key in MUTATION_FLAGS and value not in (False, None, "false", "False", "dry_run_only"):
            issues.append(
                ValidationIssue(
                    "active_mutation_flag",
                    path,
                    "mutation, upload, submit, publish, crawl, and promotion flags must be false or absent",
                )
            )


def _walk(value: Any, path: str = "$") -> Iterable[tuple[str, Any]]:
    yield path, value
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            yield from _walk(child, child_path)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            yield from _walk(child, f"{path}[{index}]")


def _as_sequence(value: Any) -> Sequence[Any]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return value
    return ()


def _is_blank(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


def _normalize(value: str) -> str:
    return " ".join(value.lower().replace("_", " ").replace("-", " ").split())


def _looks_like_raw_or_downloaded_path(value: str) -> bool:
    if not value:
        return False
    parts = set(PurePosixPath(value.replace("\\", "/")).parts)
    blocked_parts = {"private", "raw", "downloads", "downloaded", "traces", "screenshots", "har"}
    return bool(parts & blocked_parts)
