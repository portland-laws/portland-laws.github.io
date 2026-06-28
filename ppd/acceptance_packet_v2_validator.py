"""Validation for PP&D public PDF/form extraction acceptance packet v2."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str


REQUIRED_NON_EMPTY_SECTIONS: tuple[tuple[str, str], ...] = (
    ("page_anchors", "missing page anchors"),
    ("extraction_confidence", "missing extraction confidence"),
    ("checklist_rows", "missing checklist rows"),
    ("required_document_rows", "missing required-document rows"),
    ("fillable_field_metadata", "missing fillable field metadata"),
    ("deadline_rows", "missing deadline rows"),
    ("file_preparation_rows", "missing file-preparation rows"),
    ("ocr_review_holds", "missing OCR-review holds"),
    ("validation_commands", "missing validation commands"),
)

PROHIBITED_ARTIFACT_KEYS: tuple[str, ...] = (
    "raw_artifacts",
    "downloaded_artifacts",
    "private_session_artifacts",
    "browser_artifacts",
    "auth_state",
    "traces",
)

PROHIBITED_CLAIM_KEYS: tuple[str, ...] = (
    "live_crawl_claims",
    "devhub_claims",
    "official_action_completion_claims",
    "legal_guarantees",
    "permitting_guarantees",
)

ACTIVE_MUTATION_KEYS: tuple[str, ...] = (
    "active_mutation_flags",
    "mutates_remote_state",
    "submits_forms",
    "uploads_documents",
    "certifies_actions",
)


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if value is False:
        return True
    if isinstance(value, (str, bytes, Sequence, Mapping, set, frozenset)):
        return len(value) == 0
    return False


def _truthy_keys(packet: Mapping[str, Any], keys: Iterable[str]) -> list[str]:
    return [key for key in keys if key in packet and not _is_empty(packet[key])]


def validate_acceptance_packet_v2(packet: Mapping[str, Any]) -> list[ValidationIssue]:
    """Return validation issues for a public PDF/form extraction packet."""
    issues: list[ValidationIssue] = []

    if packet.get("packet_version") != 2:
        issues.append(ValidationIssue("packet_version", "acceptance packet version must be 2"))

    for key, message in REQUIRED_NON_EMPTY_SECTIONS:
        if _is_empty(packet.get(key)):
            issues.append(ValidationIssue(key, message))

    expected_labels = packet.get("expected_certification_block_labels", [])
    observed_labels = set(packet.get("certification_block_labels", []))
    missing_labels = [label for label in expected_labels if label not in observed_labels]
    if missing_labels:
        issues.append(
            ValidationIssue(
                "certification_block_labels",
                "missing certification-block labels where expected: " + ", ".join(missing_labels),
            )
        )

    prohibited_artifacts = _truthy_keys(packet, PROHIBITED_ARTIFACT_KEYS)
    if prohibited_artifacts:
        issues.append(
            ValidationIssue(
                "prohibited_artifacts",
                "raw/downloaded/private/session/browser artifacts are not allowed: "
                + ", ".join(prohibited_artifacts),
            )
        )

    prohibited_claims = _truthy_keys(packet, PROHIBITED_CLAIM_KEYS)
    if prohibited_claims:
        issues.append(
            ValidationIssue(
                "prohibited_claims",
                "live crawl, DevHub, official-action completion, legal, or permitting guarantee claims are not allowed: "
                + ", ".join(prohibited_claims),
            )
        )

    mutation_flags = _truthy_keys(packet, ACTIVE_MUTATION_KEYS)
    if mutation_flags:
        issues.append(
            ValidationIssue(
                "active_mutation_flags",
                "active mutation flags are not allowed: " + ", ".join(mutation_flags),
            )
        )

    return issues


def assert_valid_acceptance_packet_v2(packet: Mapping[str, Any]) -> None:
    issues = validate_acceptance_packet_v2(packet)
    if issues:
        detail = "; ".join(f"{issue.code}: {issue.message}" for issue in issues)
        raise ValueError(detail)
