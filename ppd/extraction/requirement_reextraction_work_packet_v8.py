"""Validation for PP&D requirement re-extraction work packet v8.

The validator is intentionally side-effect free. It only inspects a caller supplied
mapping and returns deterministic validation findings; it never crawls, downloads,
opens browser sessions, or mutates PP&D state.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

PACKET_VERSION = "requirement-reextraction-work-packet-v8"

_ALLOWED_REQUIREMENT_TYPES = {
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
class WorkPacketValidationFinding:
    """A single deterministic validation finding."""

    path: str
    message: str


@dataclass(frozen=True)
class WorkPacketValidationResult:
    """Validation result for a requirement re-extraction work packet."""

    valid: bool
    findings: tuple[WorkPacketValidationFinding, ...]

    def messages(self) -> tuple[str, ...]:
        return tuple(f"{finding.path}: {finding.message}" for finding in self.findings)


def validate_requirement_reextraction_work_packet_v8(packet: Mapping[str, Any]) -> WorkPacketValidationResult:
    """Validate a requirement re-extraction work packet v8 mapping.

    The packet must provide all source-grounded extraction inputs and must not
    contain claims or artifacts that imply live crawling, authenticated session
    capture, official action completion, legal guarantees, or active mutation.
    """

    findings: list[WorkPacketValidationFinding] = []

    if not isinstance(packet, Mapping):
        return WorkPacketValidationResult(
            valid=False,
            findings=(WorkPacketValidationFinding("$", "packet must be a mapping"),),
        )

    if packet.get("packet_version") != PACKET_VERSION:
        findings.append(
            WorkPacketValidationFinding(
                "packet_version",
                f"must equal {PACKET_VERSION!r}",
            )
        )

    _require_non_empty_text(packet, "reextraction_queue_ref", findings)
    _require_non_empty_sequence(packet, "normalized_document_record_refs", findings)
    _require_non_empty_sequence(packet, "unsupported_path_notes", findings)
    _require_non_empty_sequence(packet, "skipped_candidate_rows", findings)
    _require_validation_commands(packet, findings)

    work_items = packet.get("source_scoped_extraction_work_items")
    if not _is_non_empty_sequence(work_items):
        findings.append(
            WorkPacketValidationFinding(
                "source_scoped_extraction_work_items",
                "must include at least one source-scoped extraction work item",
            )
        )
    else:
        for index, item in enumerate(work_items):
            path = f"source_scoped_extraction_work_items[{index}]"
            if not isinstance(item, Mapping):
                findings.append(WorkPacketValidationFinding(path, "must be a mapping"))
                continue
            _validate_work_item(item, path, findings)

    _scan_for_forbidden_content(packet, "$", findings)

    return WorkPacketValidationResult(valid=not findings, findings=tuple(findings))


def assert_valid_requirement_reextraction_work_packet_v8(packet: Mapping[str, Any]) -> None:
    """Raise ValueError when a v8 work packet is invalid."""

    result = validate_requirement_reextraction_work_packet_v8(packet)
    if not result.valid:
        raise ValueError("invalid requirement re-extraction work packet v8: " + "; ".join(result.messages()))


def _validate_work_item(item: Mapping[str, Any], path: str, findings: list[WorkPacketValidationFinding]) -> None:
    _require_non_empty_text(item, "source_id", findings, path)
    _require_non_empty_text(item, "normalized_document_record_ref", findings, path)
    _require_non_empty_text(item, "extraction_work_item_id", findings, path)
    _require_non_empty_sequence(item, "citation_span_inputs", findings, path)
    _require_non_empty_sequence(item, "requirement_type_expectations", findings, path)

    expected_types = item.get("requirement_type_expectations")
    if _is_non_empty_sequence(expected_types):
        for type_index, requirement_type in enumerate(expected_types):
            if requirement_type not in _ALLOWED_REQUIREMENT_TYPES:
                findings.append(
                    WorkPacketValidationFinding(
                        f"{path}.requirement_type_expectations[{type_index}]",
                        "must be a supported RequirementNode requirement_type",
                    )
                )

    if "confidence_placeholder" not in item:
        findings.append(WorkPacketValidationFinding(f"{path}.confidence_placeholder", "is required"))
    elif item.get("confidence_placeholder") not in (None, "pending_reextraction", "requires_review"):
        findings.append(
            WorkPacketValidationFinding(
                f"{path}.confidence_placeholder",
                "must be a placeholder, not a final confidence claim",
            )
        )

    if "human_review_placeholder" not in item:
        findings.append(WorkPacketValidationFinding(f"{path}.human_review_placeholder", "is required"))
    elif item.get("human_review_placeholder") not in ("pending", "required", "not_started"):
        findings.append(
            WorkPacketValidationFinding(
                f"{path}.human_review_placeholder",
                "must keep human review unresolved before re-extraction",
            )
        )


def _require_validation_commands(packet: Mapping[str, Any], findings: list[WorkPacketValidationFinding]) -> None:
    commands = packet.get("validation_commands")
    if not _is_non_empty_sequence(commands):
        findings.append(WorkPacketValidationFinding("validation_commands", "must include at least one validation command"))
        return

    for index, command in enumerate(commands):
        if not _is_non_empty_sequence(command) or not all(isinstance(part, str) and part for part in command):
            findings.append(
                WorkPacketValidationFinding(
                    f"validation_commands[{index}]",
                    "must be a non-empty sequence of command argument strings",
                )
            )


def _require_non_empty_text(
    mapping: Mapping[str, Any],
    key: str,
    findings: list[WorkPacketValidationFinding],
    parent_path: str | None = None,
) -> None:
    value = mapping.get(key)
    path = f"{parent_path}.{key}" if parent_path else key
    if not isinstance(value, str) or not value.strip():
        findings.append(WorkPacketValidationFinding(path, "must be a non-empty string"))


def _require_non_empty_sequence(
    mapping: Mapping[str, Any],
    key: str,
    findings: list[WorkPacketValidationFinding],
    parent_path: str | None = None,
) -> None:
    path = f"{parent_path}.{key}" if parent_path else key
    if not _is_non_empty_sequence(mapping.get(key)):
        findings.append(WorkPacketValidationFinding(path, "must be a non-empty sequence"))


def _is_non_empty_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)) and len(value) > 0


def _scan_for_forbidden_content(value: Any, path: str, findings: list[WorkPacketValidationFinding]) -> None:
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
    findings: list[WorkPacketValidationFinding],
) -> None:
    lowered_key = key.lower()
    if lowered_key in _ACTIVE_MUTATION_KEYS and _truthy_mutation_value(value):
        findings.append(WorkPacketValidationFinding(path, "must not contain active mutation flags"))

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
    findings: list[WorkPacketValidationFinding],
) -> None:
    if any(term in lowered_text for term in terms):
        findings.append(WorkPacketValidationFinding(path, message))
