"""Validation for the PP&D agent API compatibility matrix v7.

The matrix is release evidence, not an activation switch. This module keeps the
schema intentionally flexible while enforcing the safety coverage that agents
must prove before a v7 matrix can be accepted.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping


MATRIX_VERSION = "v7"

REQUIRED_REFERENCE_KEYS = {
    "smoke_replay_ref": (
        "smoke_replay_ref",
        "smoke_replay",
        "smokeReplayRef",
        "smokeReplay",
    ),
    "release_decision_ref": (
        "release_decision_ref",
        "release_decision",
        "releaseDecisionRef",
        "releaseDecision",
    ),
}

REQUIRED_ROW_GROUPS = {
    "supported_query_rows": (
        "supported_query_rows",
        "supported_queries",
        "query_rows",
        "queries",
    ),
    "blocked_action_classes": (
        "blocked_action_classes",
        "blocked_actions",
        "refused_action_classes",
        "refused_actions",
    ),
    "exact_confirmation_checkpoints": (
        "exact_confirmation_checkpoints",
        "confirmation_checkpoints",
        "checkpoints",
    ),
    "manual_handoff_surfaces": (
        "manual_handoff_surfaces",
        "handoff_surfaces",
        "manual_handoffs",
    ),
    "rollback_visibility": (
        "rollback_visibility",
        "rollback_surfaces",
        "rollback",
    ),
    "validation_commands": (
        "validation_commands",
        "validationCommands",
        "commands",
    ),
}

REQUIRED_BEHAVIOR_KEYS = {
    "citation_explanation_behavior": (
        "citation_explanation_behavior",
        "citation_explanations",
        "citationExplanationBehavior",
    ),
    "stale_evidence_hold_behavior": (
        "stale_evidence_hold_behavior",
        "stale_evidence_hold",
        "staleEvidenceHoldBehavior",
    ),
    "missing_information_prompts": (
        "missing_information_prompts",
        "missing_info_prompts",
        "missingInformationPrompts",
    ),
    "reversible_draft_boundaries": (
        "reversible_draft_boundaries",
        "reversible_draft_boundary",
        "reversibleDraftBoundaries",
    ),
    "local_pdf_preview_boundaries": (
        "local_pdf_preview_boundaries",
        "local_pdf_preview_boundary",
        "localPdfPreviewBoundaries",
    ),
}

PROHIBITED_CLAIM_PATTERNS = {
    "actual_activation_or_promotion_claim": (
        "activated",
        "activation complete",
        "promoted to production",
        "production promoted",
        "live promoted",
        "release is active",
    ),
    "live_crawl_execution_claim": (
        "live crawl executed",
        "live crawl completed",
        "crawled live",
        "ran live crawl",
        "executed live crawl",
    ),
    "private_session_or_auth_artifact_claim": (
        "cookie",
        "cookies",
        "session storage",
        "auth state",
        "credential",
        "password",
        "har file",
        "trace.zip",
        "screenshot",
    ),
    "official_action_completion_claim": (
        "submitted permit",
        "submission complete",
        "payment complete",
        "inspection scheduled",
        "correction uploaded",
        "certification complete",
        "official action completed",
    ),
    "legal_or_permitting_guarantee": (
        "guaranteed approval",
        "permit guaranteed",
        "legal guarantee",
        "compliance guaranteed",
        "will be approved",
        "legally sufficient",
    ),
}

PROHIBITED_TRUE_FLAGS = {
    "active_mutation_flags": (
        "active_mutation",
        "active_mutations",
        "active_mutation_enabled",
        "mutation_enabled",
        "mutations_enabled",
        "live_mutation",
        "live_mutations",
        "can_submit",
        "can_upload",
        "can_pay",
        "can_schedule",
        "can_certify",
        "can_cancel",
    ),
    "actual_activation_or_promotion_claim": (
        "activated",
        "active_release",
        "promoted",
        "promoted_to_production",
        "production_active",
    ),
    "live_crawl_execution_claim": (
        "live_crawl_executed",
        "live_crawl_completed",
        "ran_live_crawl",
    ),
    "private_session_or_auth_artifact_claim": (
        "stores_auth_state",
        "stores_cookies",
        "stores_credentials",
        "stores_session",
        "commits_traces",
        "commits_screenshots",
    ),
    "official_action_completion_claim": (
        "official_action_completed",
        "submitted",
        "paid",
        "scheduled",
        "uploaded_to_record",
        "certified",
    ),
    "legal_or_permitting_guarantee": (
        "guarantees_approval",
        "guarantees_permit",
        "guarantees_compliance",
    ),
}


@dataclass(frozen=True)
class MatrixValidationFinding:
    """A deterministic validation failure for a matrix candidate."""

    code: str
    message: str


def validate_agent_api_compatibility_matrix_v7(matrix: Mapping[str, Any]) -> list[MatrixValidationFinding]:
    """Return all v7 compatibility matrix validation failures.

    The validator accepts a mapping with flexible key names so fixture and
    daemon-produced matrices can evolve without weakening the required PP&D
    guardrails.
    """

    findings: list[MatrixValidationFinding] = []

    version = matrix.get("version") or matrix.get("matrix_version") or matrix.get("matrixVersion")
    if version != MATRIX_VERSION:
        findings.append(
            MatrixValidationFinding(
                "missing_matrix_v7_version",
                "agent API compatibility matrix must declare version v7",
            )
        )

    for canonical, aliases in REQUIRED_REFERENCE_KEYS.items():
        if not _has_non_empty_alias(matrix, aliases):
            findings.append(
                MatrixValidationFinding(
                    f"missing_{canonical}",
                    f"matrix v7 must include a non-empty {canonical}",
                )
            )

    for canonical, aliases in REQUIRED_ROW_GROUPS.items():
        if not _has_non_empty_alias(matrix, aliases):
            findings.append(
                MatrixValidationFinding(
                    f"missing_{canonical}",
                    f"matrix v7 must include at least one {canonical} entry",
                )
            )

    for canonical, aliases in REQUIRED_BEHAVIOR_KEYS.items():
        if not _has_non_empty_alias(matrix, aliases):
            findings.append(
                MatrixValidationFinding(
                    f"missing_{canonical}",
                    f"matrix v7 must describe {canonical}",
                )
            )

    for code, aliases in PROHIBITED_TRUE_FLAGS.items():
        for path, value in _walk_items(matrix):
            leaf = path[-1] if path else ""
            if leaf in aliases and value is True:
                findings.append(
                    MatrixValidationFinding(
                        code,
                        f"matrix v7 must not set {'.'.join(path)} to true",
                    )
                )

    for code, patterns in PROHIBITED_CLAIM_PATTERNS.items():
        for path, value in _walk_items(matrix):
            if isinstance(value, str):
                lowered = value.lower()
                if any(pattern in lowered for pattern in patterns):
                    findings.append(
                        MatrixValidationFinding(
                            code,
                            f"matrix v7 includes prohibited claim at {'.'.join(path)}",
                        )
                    )

    return _dedupe_findings(findings)


def assert_agent_api_compatibility_matrix_v7(matrix: Mapping[str, Any]) -> None:
    """Raise ValueError when a v7 compatibility matrix is not releasable."""

    findings = validate_agent_api_compatibility_matrix_v7(matrix)
    if findings:
        details = "; ".join(f"{finding.code}: {finding.message}" for finding in findings)
        raise ValueError(details)


def is_agent_api_compatibility_matrix_v7_valid(matrix: Mapping[str, Any]) -> bool:
    """Return True when the matrix has no v7 validation failures."""

    return not validate_agent_api_compatibility_matrix_v7(matrix)


def _has_non_empty_alias(matrix: Mapping[str, Any], aliases: Iterable[str]) -> bool:
    for alias in aliases:
        if _is_non_empty(matrix.get(alias)):
            return True
    return False


def _is_non_empty(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return any(_is_non_empty(nested) for nested in value.values())
    if isinstance(value, (list, tuple, set, frozenset)):
        return any(_is_non_empty(item) for item in value)
    return True


def _walk_items(value: Any, path: tuple[str, ...] = ()) -> Iterable[tuple[tuple[str, ...], Any]]:
    yield path, value
    if isinstance(value, Mapping):
        for key, nested in value.items():
            yield from _walk_items(nested, path + (str(key),))
    elif isinstance(value, (list, tuple)):
        for index, nested in enumerate(value):
            yield from _walk_items(nested, path + (str(index),))


def _dedupe_findings(findings: Iterable[MatrixValidationFinding]) -> list[MatrixValidationFinding]:
    seen: set[tuple[str, str]] = set()
    deduped: list[MatrixValidationFinding] = []
    for finding in findings:
        key = (finding.code, finding.message)
        if key not in seen:
            seen.add(key)
            deduped.append(finding)
    return deduped
