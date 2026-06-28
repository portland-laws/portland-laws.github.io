"""Validation for public HTML extraction acceptance packet v4.

The validator is intentionally fixture-first and side-effect free. It rejects
packets that are missing the review and evidence structure needed before public
HTML extraction output can be accepted into later PP&D guardrail work.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


REQUIRED_ORDERED_STRUCTURE = (
    "source_metadata",
    "document_structure",
    "evidence_rows",
    "review_controls",
    "validation_commands",
    "safety_attestation",
)

PROHIBITED_ARTIFACT_KINDS = {
    "raw_html",
    "raw_download",
    "downloaded_pdf",
    "warc",
    "har",
    "trace",
    "screenshot",
    "browser_profile",
    "auth_state",
    "session_cookie",
    "private_devhub_capture",
}

PROHIBITED_CLAIM_TERMS = (
    "live crawl",
    "live-crawl",
    "devhub login",
    "authenticated devhub",
    "browser session",
    "session replay",
)

PROHIBITED_GUARANTEE_TERMS = (
    "legal advice",
    "legal guarantee",
    "permitting guarantee",
    "permit guaranteed",
    "approval guaranteed",
    "guaranteed approval",
    "will be approved",
    "will receive a permit",
)

MUTATION_FLAG_KEYS = (
    "mutates_remote_state",
    "writes_to_devhub",
    "submits_application",
    "uploads_documents",
    "pays_fees",
    "schedules_inspection",
    "cancels_request",
    "certifies_information",
)


@dataclass(frozen=True)
class PacketValidationResult:
    """Side-effect-free validation result."""

    accepted: bool
    errors: tuple[str, ...]


def validate_public_html_acceptance_packet_v4(packet: Mapping[str, Any]) -> PacketValidationResult:
    """Validate a public HTML extraction acceptance packet v4."""

    errors: list[str] = []
    if not isinstance(packet, Mapping):
        return PacketValidationResult(False, ("packet must be a mapping",))

    version = packet.get("packet_version")
    if version != "public_html_extraction_acceptance_packet_v4":
        errors.append("packet_version must be public_html_extraction_acceptance_packet_v4")

    _validate_ordered_structure(packet.get("ordered_structure"), errors)
    _validate_source_metadata(packet.get("source_metadata"), errors)
    _validate_document_structure(packet.get("document_structure"), errors)
    _validate_evidence_rows(packet.get("evidence_rows"), errors)
    _validate_review_controls(packet.get("review_controls"), errors)
    _validate_validation_commands(packet.get("validation_commands"), errors)
    _validate_artifacts(packet.get("artifacts"), errors)
    _validate_safety_attestation(packet.get("safety_attestation"), errors)
    _validate_mutation_flags(packet.get("mutation_flags"), errors)
    _validate_textual_claims(packet, errors)

    return PacketValidationResult(len(errors) == 0, tuple(errors))


def require_public_html_acceptance_packet_v4(packet: Mapping[str, Any]) -> None:
    """Raise ValueError when a packet is not acceptable."""

    result = validate_public_html_acceptance_packet_v4(packet)
    if not result.accepted:
        raise ValueError("public HTML acceptance packet v4 rejected: " + "; ".join(result.errors))


def _validate_ordered_structure(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        errors.append("ordered_structure must be a list of ordered stage mappings")
        return
    if len(value) != len(REQUIRED_ORDERED_STRUCTURE):
        errors.append("ordered_structure must include every required stage")
        return

    seen_names: list[str] = []
    seen_orders: list[int] = []
    for item in value:
        if not isinstance(item, Mapping):
            errors.append("ordered_structure entries must be mappings")
            return
        order = item.get("order")
        name = item.get("name")
        if not isinstance(order, int) or isinstance(order, bool) or order not in range(1, 7):
            errors.append("ordered_structure entries must have integer order 1 through 6")
            return
        if not isinstance(name, str) or name == "":
            errors.append("ordered_structure entries must have a non-empty name")
            return
        seen_orders.append(order)
        seen_names.append(name)

    expected_orders = list(range(1, 7))
    if sorted(seen_orders) != expected_orders:
        errors.append("ordered_structure orders must be exactly 1 through 6")
    if seen_names != list(REQUIRED_ORDERED_STRUCTURE):
        errors.append("ordered_structure names must appear in the required order")


def _validate_source_metadata(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("source_metadata is required")
        return
    required = ("canonical_url", "source_type", "content_hash", "captured_at", "no_raw_body_persisted")
    for key in required:
        if key not in value:
            errors.append("source_metadata missing " + key)
    if value.get("source_type") != "public_html":
        errors.append("source_metadata.source_type must be public_html")
    if value.get("no_raw_body_persisted") is not True:
        errors.append("source_metadata.no_raw_body_persisted must be true")
    metadata = value.get("downloadable_link_metadata")
    if not isinstance(metadata, Sequence) or isinstance(metadata, (str, bytes)) or len(metadata) == 0:
        errors.append("downloadable_link_metadata is required")
    else:
        for link in metadata:
            if not isinstance(link, Mapping):
                errors.append("downloadable_link_metadata entries must be mappings")
                return
            for key in ("url", "link_text", "content_type", "download_allowed", "raw_download_persisted"):
                if key not in link:
                    errors.append("downloadable_link_metadata entries missing " + key)
            if link.get("raw_download_persisted") is not False:
                errors.append("downloadable links must not persist raw downloads")


def _validate_document_structure(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("document_structure is required")
        return
    ordered_steps = value.get("ordered_steps")
    callouts = value.get("callout_rows")
    warnings = value.get("warning_rows")
    tables = value.get("table_rows")
    expected_tables = value.get("expected_table_row_groups")
    citations = value.get("citation_spans")
    confidence = value.get("extraction_confidence")

    if not isinstance(ordered_steps, Sequence) or isinstance(ordered_steps, (str, bytes)) or len(ordered_steps) == 0:
        errors.append("document_structure.ordered_steps is required")
    if not isinstance(callouts, Sequence) or isinstance(callouts, (str, bytes)) or len(callouts) == 0:
        errors.append("document_structure.callout_rows is required")
    if not isinstance(warnings, Sequence) or isinstance(warnings, (str, bytes)) or len(warnings) == 0:
        errors.append("document_structure.warning_rows is required")
    if not isinstance(tables, Sequence) or isinstance(tables, (str, bytes)) or len(tables) == 0:
        errors.append("document_structure.table_rows is required")
    if not isinstance(expected_tables, Sequence) or isinstance(expected_tables, (str, bytes)) or len(expected_tables) == 0:
        errors.append("document_structure.expected_table_row_groups is required")
    if not isinstance(citations, Sequence) or isinstance(citations, (str, bytes)) or len(citations) == 0:
        errors.append("document_structure.citation_spans is required")
    if not _is_confidence(confidence):
        errors.append("document_structure.extraction_confidence must be a number from 0.0 to 1.0")


def _validate_evidence_rows(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or len(value) == 0:
        errors.append("evidence_rows are required")
        return
    for row in value:
        if not isinstance(row, Mapping):
            errors.append("evidence_rows entries must be mappings")
            return
        for key in ("row_id", "row_type", "source_url", "citation_span_id", "text", "confidence"):
            if key not in row:
                errors.append("evidence_rows entries missing " + key)
        if row.get("row_type") == "table" and row.get("table_row_index") is None:
            errors.append("table evidence rows must include table_row_index")
        if row.get("row_type") in {"callout", "warning"} and row.get("severity") is None:
            errors.append("callout and warning rows must include severity")
        if not _is_confidence(row.get("confidence")):
            errors.append("evidence_rows confidence must be a number from 0.0 to 1.0")


def _validate_review_controls(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("review_controls are required")
        return
    holds = value.get("reviewer_holds")
    if not isinstance(holds, Sequence) or isinstance(holds, (str, bytes)) or len(holds) == 0:
        errors.append("reviewer_holds are required")
    else:
        for hold in holds:
            if not isinstance(hold, Mapping):
                errors.append("reviewer_holds entries must be mappings")
                return
            for key in ("hold_id", "reason", "required_before_acceptance"):
                if key not in hold:
                    errors.append("reviewer_holds entries missing " + key)
            if hold.get("required_before_acceptance") is not True:
                errors.append("reviewer_holds must be required before acceptance")


def _validate_validation_commands(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or len(value) == 0:
        errors.append("validation_commands are required")
        return
    for command in value:
        if not isinstance(command, Sequence) or isinstance(command, (str, bytes)) or len(command) == 0:
            errors.append("validation_commands entries must be argv lists")
            return
        for part in command:
            if not isinstance(part, str) or part == "":
                errors.append("validation_commands argv parts must be non-empty strings")
                return


def _validate_artifacts(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        errors.append("artifacts must be a list")
        return
    for artifact in value:
        if not isinstance(artifact, Mapping):
            errors.append("artifacts entries must be mappings")
            return
        kind = artifact.get("kind")
        if kind in PROHIBITED_ARTIFACT_KINDS:
            errors.append("prohibited artifact kind present: " + str(kind))
        if artifact.get("committed") is True and artifact.get("privacy_classification") in {"private", "session", "browser"}:
            errors.append("private, session, and browser artifacts must not be committed")


def _validate_safety_attestation(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("safety_attestation is required")
        return
    required_false = (
        "live_crawl_performed",
        "devhub_claims_made",
        "legal_guarantees_made",
        "permitting_guarantees_made",
    )
    for key in required_false:
        if value.get(key) is not False:
            errors.append("safety_attestation." + key + " must be false")


def _validate_mutation_flags(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("mutation_flags are required")
        return
    for key in MUTATION_FLAG_KEYS:
        if value.get(key) is not False:
            errors.append("mutation_flags." + key + " must be false")


def _validate_textual_claims(packet: Mapping[str, Any], errors: list[str]) -> None:
    text = _flatten_text(packet).lower()
    for term in PROHIBITED_CLAIM_TERMS:
        if term in text:
            errors.append("packet contains prohibited live crawl or DevHub claim: " + term)
    for term in PROHIBITED_GUARANTEE_TERMS:
        if term in text:
            errors.append("packet contains prohibited legal or permitting guarantee: " + term)


def _is_confidence(value: Any) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    numeric = float(value)
    return numeric == max(0.0, min(1.0, numeric))


def _flatten_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        return " ".join(_flatten_text(item) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return " ".join(_flatten_text(item) for item in value)
    return ""
