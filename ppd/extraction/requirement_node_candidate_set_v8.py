"""Validation for PP&D RequirementNode candidate set v8.

The validator is fixture-first and side-effect free. It inspects a caller supplied
candidate-set mapping and rejects missing traceability, unresolved review fields,
unsafe execution claims, private artifacts, official-action claims, legal or
permitting guarantees, and active mutation flags.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

CANDIDATE_SET_VERSION = "requirement-node-candidate-set-v8"

ALLOWED_REQUIREMENT_TYPES = {
    "obligation",
    "prohibition",
    "permission",
    "precondition",
    "exception",
    "deadline",
    "fee_trigger",
    "license_requirement",
    "document_requirement",
    "action_gate",
}

_ALLOWED_REVIEW_PLACEHOLDERS = {
    "needs_review",
    "candidate_only",
    "pending_review",
    "review_required",
}

_ALLOWED_FORMALIZATION_PLACEHOLDERS = {
    "formalization_placeholder",
    "pending_formalization",
    "requires_formalization_review",
}

_LIVE_CRAWL_CLAIM_TERMS = (
    "live crawl executed",
    "live crawl completed",
    "ran live crawl",
    "executed live crawl",
    "crawled live",
    "downloaded live",
)

_RAW_OR_DOWNLOADED_ARTIFACT_TERMS = (
    "raw_html",
    "raw html",
    "raw_body",
    "raw body",
    "raw_crawl",
    "raw crawl",
    "downloaded_artifact",
    "downloaded artifact",
    "downloaded_document",
    "downloaded document",
    "downloaded_pdf",
    "downloaded pdf",
    "warc_path",
    "har_path",
    "trace_path",
    "screenshot_path",
)

_PRIVATE_OR_AUTH_ARTIFACT_TERMS = (
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "password",
    "session_state",
    "storage_state",
    "auth_state",
    "bearer token",
    "access_token",
    "refresh_token",
    "private_upload",
    "private file",
    "local_private_path",
)

_OFFICIAL_ACTION_COMPLETION_TERMS = (
    "official action completed",
    "permit submitted",
    "application submitted",
    "payment submitted",
    "inspection scheduled",
    "correction uploaded",
    "certification completed",
    "cancelled permit",
    "withdrew application",
)

_LEGAL_OR_PERMITTING_GUARANTEE_TERMS = (
    "guaranteed approval",
    "approval guaranteed",
    "permit guaranteed",
    "legally sufficient",
    "legal advice",
    "will be approved",
    "compliance guaranteed",
    "no review required",
)

_ACTIVE_MUTATION_KEYS = {
    "active_mutation",
    "active_mutation_flag",
    "active_mutation_flags",
    "mutation_enabled",
    "mutates_state",
    "writes_enabled",
    "submit_enabled",
    "payment_enabled",
    "upload_enabled",
    "schedule_enabled",
    "official_action_enabled",
}


@dataclass(frozen=True)
class CandidateSetValidationFinding:
    """A single deterministic candidate-set validation finding."""

    path: str
    message: str


@dataclass(frozen=True)
class CandidateSetValidationResult:
    """Validation result for a RequirementNode candidate set v8."""

    valid: bool
    findings: tuple[CandidateSetValidationFinding, ...]

    def messages(self) -> tuple[str, ...]:
        return tuple(f"{finding.path}: {finding.message}" for finding in self.findings)


def validate_requirement_node_candidate_set_v8(candidate_set: Mapping[str, Any]) -> CandidateSetValidationResult:
    """Validate a RequirementNode candidate set v8 mapping."""

    findings: list[CandidateSetValidationFinding] = []

    if not isinstance(candidate_set, Mapping):
        return CandidateSetValidationResult(
            valid=False,
            findings=(CandidateSetValidationFinding("$", "candidate set must be a mapping"),),
        )

    if candidate_set.get("candidate_set_version") != CANDIDATE_SET_VERSION:
        findings.append(
            CandidateSetValidationFinding(
                "candidate_set_version",
                f"must equal {CANDIDATE_SET_VERSION!r}",
            )
        )

    _require_non_empty_text(candidate_set, "candidate_set_id", findings)
    _require_non_empty_text(candidate_set, "work_packet_ref", findings)
    _require_validation_commands(candidate_set, findings)

    evidence_ids = _validate_evidence_catalog(candidate_set, findings)
    required_types = _validate_required_type_coverage(candidate_set, findings)
    observed_types: set[str] = set()

    rows = candidate_set.get("rows")
    if not _is_non_empty_sequence(rows):
        findings.append(CandidateSetValidationFinding("rows", "must include at least one RequirementNode candidate row"))
    else:
        for index, row in enumerate(rows):
            path = f"rows[{index}]"
            if not isinstance(row, Mapping):
                findings.append(CandidateSetValidationFinding(path, "must be a mapping"))
                continue
            row_type = _validate_row(row, path, evidence_ids, findings)
            if row_type:
                observed_types.add(row_type)

    missing_coverage = sorted(required_types - observed_types)
    if missing_coverage:
        findings.append(
            CandidateSetValidationFinding(
                "required_requirement_type_coverage",
                "missing candidate rows for required requirement_type coverage: " + ", ".join(missing_coverage),
            )
        )

    _scan_for_forbidden_content(candidate_set, "$", findings)

    return CandidateSetValidationResult(valid=not findings, findings=tuple(findings))


def assert_valid_requirement_node_candidate_set_v8(candidate_set: Mapping[str, Any]) -> None:
    """Raise ValueError when a RequirementNode candidate set v8 is invalid."""

    result = validate_requirement_node_candidate_set_v8(candidate_set)
    if not result.valid:
        raise ValueError("invalid RequirementNode candidate set v8: " + "; ".join(result.messages()))


def _validate_evidence_catalog(
    candidate_set: Mapping[str, Any],
    findings: list[CandidateSetValidationFinding],
) -> set[str]:
    catalog = candidate_set.get("source_evidence_catalog")
    evidence_ids: set[str] = set()
    if not _is_non_empty_sequence(catalog):
        findings.append(CandidateSetValidationFinding("source_evidence_catalog", "must include source evidence IDs"))
        return evidence_ids

    for index, evidence in enumerate(catalog):
        path = f"source_evidence_catalog[{index}]"
        if not isinstance(evidence, Mapping):
            findings.append(CandidateSetValidationFinding(path, "must be a mapping"))
            continue
        evidence_id = evidence.get("evidence_id")
        if not isinstance(evidence_id, str) or not evidence_id.strip():
            findings.append(CandidateSetValidationFinding(f"{path}.evidence_id", "must be a non-empty source evidence ID"))
        else:
            evidence_ids.add(evidence_id)
        _require_non_empty_text(evidence, "source_id", findings, path)

    return evidence_ids


def _validate_required_type_coverage(
    candidate_set: Mapping[str, Any],
    findings: list[CandidateSetValidationFinding],
) -> set[str]:
    values = candidate_set.get("required_requirement_type_coverage")
    required_types: set[str] = set()
    if not _is_non_empty_sequence(values):
        findings.append(
            CandidateSetValidationFinding(
                "required_requirement_type_coverage",
                "must list required RequirementNode requirement_type coverage",
            )
        )
        return required_types

    for index, requirement_type in enumerate(values):
        path = f"required_requirement_type_coverage[{index}]"
        if requirement_type not in ALLOWED_REQUIREMENT_TYPES:
            findings.append(CandidateSetValidationFinding(path, "must be a supported RequirementNode requirement_type"))
        else:
            required_types.add(str(requirement_type))

    return required_types


def _validate_row(
    row: Mapping[str, Any],
    path: str,
    evidence_ids: set[str],
    findings: list[CandidateSetValidationFinding],
) -> str | None:
    _require_non_empty_text(row, "requirement_id", findings, path)
    _require_non_empty_text(row, "work_packet_ref", findings, path)
    _require_non_empty_sequence(row, "source_evidence_ids", findings, path)

    for index, evidence_id in enumerate(row.get("source_evidence_ids", ())):
        evidence_path = f"{path}.source_evidence_ids[{index}]"
        if not isinstance(evidence_id, str) or not evidence_id.strip():
            findings.append(CandidateSetValidationFinding(evidence_path, "must be a non-empty source evidence ID"))
        elif evidence_ids and evidence_id not in evidence_ids:
            findings.append(CandidateSetValidationFinding(evidence_path, "must reference source_evidence_catalog"))

    requirement_type = row.get("requirement_type")
    if requirement_type not in ALLOWED_REQUIREMENT_TYPES:
        findings.append(CandidateSetValidationFinding(f"{path}.requirement_type", "must be a supported RequirementNode requirement_type"))
        normalized_type = None
    else:
        normalized_type = str(requirement_type)

    if "confidence" not in row or row.get("confidence") in (None, ""):
        findings.append(CandidateSetValidationFinding(f"{path}.confidence", "must include a confidence value or explicit candidate placeholder"))

    if row.get("formalization_status") not in _ALLOWED_FORMALIZATION_PLACEHOLDERS:
        findings.append(CandidateSetValidationFinding(f"{path}.formalization_status", "must include a formalization placeholder"))

    if row.get("human_review_status") not in _ALLOWED_REVIEW_PLACEHOLDERS:
        findings.append(CandidateSetValidationFinding(f"{path}.human_review_status", "must include a reviewer status placeholder"))

    candidate_action = row.get("candidate_action")
    if candidate_action in {"deprecate", "supersede", "replace"}:
        _require_non_empty_sequence(row, "superseded_requirement_refs", findings, path)

    return normalized_type


def _require_validation_commands(candidate_set: Mapping[str, Any], findings: list[CandidateSetValidationFinding]) -> None:
    commands = candidate_set.get("validation_commands")
    if not _is_non_empty_sequence(commands):
        findings.append(CandidateSetValidationFinding("validation_commands", "must include at least one validation command"))
        return

    for index, command in enumerate(commands):
        if not _is_non_empty_sequence(command) or not all(isinstance(part, str) and part for part in command):
            findings.append(
                CandidateSetValidationFinding(
                    f"validation_commands[{index}]",
                    "must be a non-empty sequence of command argument strings",
                )
            )


def _require_non_empty_text(
    mapping: Mapping[str, Any],
    key: str,
    findings: list[CandidateSetValidationFinding],
    parent_path: str | None = None,
) -> None:
    value = mapping.get(key)
    path = f"{parent_path}.{key}" if parent_path else key
    if not isinstance(value, str) or not value.strip():
        findings.append(CandidateSetValidationFinding(path, "must be a non-empty string"))


def _require_non_empty_sequence(
    mapping: Mapping[str, Any],
    key: str,
    findings: list[CandidateSetValidationFinding],
    parent_path: str | None = None,
) -> None:
    path = f"{parent_path}.{key}" if parent_path else key
    if not _is_non_empty_sequence(mapping.get(key)):
        findings.append(CandidateSetValidationFinding(path, "must be a non-empty sequence"))


def _is_non_empty_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)) and len(value) > 0


def _scan_for_forbidden_content(value: Any, path: str, findings: list[CandidateSetValidationFinding]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}" if path != "$" else key_text
            _reject_forbidden_key(key_text, child, child_path, findings)
            _scan_for_forbidden_content(child, child_path, findings)
        return

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _scan_for_forbidden_content(child, f"{path}[{index}]", findings)
        return

    if isinstance(value, str):
        lowered = value.lower()
        _reject_terms(lowered, _LIVE_CRAWL_CLAIM_TERMS, path, "must not claim live crawl execution", findings)
        _reject_terms(lowered, _RAW_OR_DOWNLOADED_ARTIFACT_TERMS, path, "must not include downloaded or raw crawl artifacts", findings)
        _reject_terms(lowered, _PRIVATE_OR_AUTH_ARTIFACT_TERMS, path, "must not include private, session, or auth artifacts", findings)
        _reject_terms(lowered, _OFFICIAL_ACTION_COMPLETION_TERMS, path, "must not claim official-action completion", findings)
        _reject_terms(lowered, _LEGAL_OR_PERMITTING_GUARANTEE_TERMS, path, "must not provide legal or permitting guarantees", findings)


def _reject_forbidden_key(
    key: str,
    value: Any,
    path: str,
    findings: list[CandidateSetValidationFinding],
) -> None:
    lowered_key = key.lower()
    if lowered_key in _ACTIVE_MUTATION_KEYS and _truthy_mutation_value(value):
        findings.append(CandidateSetValidationFinding(path, "must not contain active mutation flags"))

    _reject_terms(lowered_key, _RAW_OR_DOWNLOADED_ARTIFACT_TERMS, path, "must not include downloaded or raw crawl artifact fields", findings)
    _reject_terms(lowered_key, _PRIVATE_OR_AUTH_ARTIFACT_TERMS, path, "must not include private, session, or auth artifact fields", findings)


def _truthy_mutation_value(value: Any) -> bool:
    if value in (None, False, "", (), [], {}):
        return False
    if isinstance(value, str):
        return value.strip().lower() not in {"false", "none", "disabled", "inactive", "no"}
    return True


def _reject_terms(
    lowered_text: str,
    terms: tuple[str, ...],
    path: str,
    message: str,
    findings: list[CandidateSetValidationFinding],
) -> None:
    if any(term in lowered_text for term in terms):
        findings.append(CandidateSetValidationFinding(path, message))
