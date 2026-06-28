"""Fixture-first PP&D public-data dry-run release packet validation.

This module validates a metadata-only operator review packet that links the
public-data dry-run artifacts produced before any live crawl or authenticated
DevHub automation is enabled.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

REQUIRED_OUTPUT_TYPES = (
    "source_coverage_audit",
    "processor_handoff_dry_run",
    "extraction_quality_review",
    "process_model_impact",
    "guardrail_candidate",
    "agent_gap_analysis_rerun",
)

REQUIRED_CHECKLIST_SECTIONS = (
    "source_coverage_audit",
    "processor_handoff_dry_run",
    "extraction_quality_review",
    "process_model_impact",
    "guardrail_candidate",
    "agent_gap_analysis_rerun",
    "operator_release_decision",
)

FORBIDDEN_CAPABILITIES = (
    "live_crawl",
    "devhub_session",
    "upload",
    "payment",
    "submission",
    "scheduling",
    "cancellation",
    "certification",
)

PRIVATE_KEYS = frozenset(
    {
        "auth_state",
        "card_number",
        "cookie",
        "credentials",
        "cvv",
        "downloaded_document_path",
        "email",
        "file_path",
        "local_path",
        "password",
        "payment_details",
        "phone",
        "private_value",
        "raw_value",
        "session_state",
        "ssn",
        "token",
        "user_value",
        "value",
    }
)

RAW_BODY_KEYS = frozenset(
    {
        "body",
        "document_body",
        "full_html",
        "full_text",
        "html",
        "page_body",
        "pdf_body",
        "raw_body",
        "raw_html",
        "raw_pdf",
        "raw_text",
        "text",
    }
)

PRIVATE_STRING_MARKERS = (
    "/home/",
    "/Users/",
    "C:\\Users\\",
    "/devhub/.auth/",
    "/devhub/downloads/",
    "/devhub/screenshots/",
    "/devhub/traces/",
    ".har",
    "auth-state",
    "bearer ",
    "cookie=",
    "password=",
    "storage-state",
    "token=",
    "trace.zip",
)

ACCEPTABLE_OUTPUT_STATUSES = frozenset(
    {
        "accepted_fixture",
        "dry_run_complete",
        "fixture_validated",
        "needs_operator_review",
        "review_ready",
    }
)

BLOCKING_DECISIONS = frozenset({"blocked", "manual_handoff", "not_enabled", "not_ready", "refused"})


@dataclass(frozen=True)
class PublicDataDryRunReleasePacket:
    """Validated metadata-only release packet summary."""

    packet_id: str
    output_types: tuple[str, ...]
    checklist_sections: tuple[str, ...]
    ready_for_live_release: bool
    disabled_capabilities: tuple[str, ...]
    blockers: tuple[str, ...]


def build_public_data_dry_run_release_packet(packet: Mapping[str, Any]) -> PublicDataDryRunReleasePacket:
    """Validate and summarize a fixture-backed public-data dry-run release packet."""

    errors = validate_public_data_dry_run_release_packet(packet)
    if errors:
        raise ValueError("invalid public-data dry-run release packet: " + "; ".join(errors))

    outputs = packet["linked_outputs"]
    checklist = packet["operator_review_checklist"]
    return PublicDataDryRunReleasePacket(
        packet_id=str(packet["packet_id"]),
        output_types=tuple(str(output["output_type"]) for output in outputs),
        checklist_sections=tuple(str(item["section"]) for item in checklist),
        ready_for_live_release=False,
        disabled_capabilities=tuple(FORBIDDEN_CAPABILITIES),
        blockers=tuple(str(item["review_prompt"]) for item in checklist if item.get("decision") != "accepted_for_operator_review"),
    )


def validate_public_data_dry_run_release_packet(packet: Mapping[str, Any]) -> list[str]:
    """Return deterministic validation errors for an unsafe release packet."""

    errors: list[str] = []
    if not isinstance(packet, Mapping):
        return ["release packet must be an object"]

    _scan_for_private_or_raw_values(packet, "$", errors)

    packet_id = packet.get("packet_id")
    if not isinstance(packet_id, str) or not packet_id:
        errors.append("packet_id is required")

    if packet.get("fixture_first") is not True:
        errors.append("fixture_first must be true")
    if packet.get("metadata_only") is not True:
        errors.append("metadata_only must be true")
    if packet.get("ready_for_live_release") is not False:
        errors.append("ready_for_live_release must remain false")

    disabled = packet.get("disabled_capabilities")
    if not isinstance(disabled, Mapping):
        errors.append("disabled_capabilities must be an object")
    else:
        for capability in FORBIDDEN_CAPABILITIES:
            if disabled.get(capability) is not True:
                errors.append(f"disabled_capabilities.{capability} must be true")

    linked_outputs = packet.get("linked_outputs")
    if not isinstance(linked_outputs, Sequence) or isinstance(linked_outputs, (str, bytes)):
        errors.append("linked_outputs must be a list")
        linked_outputs = []

    output_types: set[str] = set()
    for index, output in enumerate(linked_outputs):
        if not isinstance(output, Mapping):
            errors.append(f"linked_outputs[{index}] must be an object")
            continue
        output_type = _required_text(output, "output_type", f"linked_outputs[{index}]", errors)
        if output_type:
            output_types.add(output_type)
        _required_text(output, "artifact_id", f"linked_outputs[{index}]", errors)
        _required_text(output, "source_fixture_path", f"linked_outputs[{index}]", errors)
        fixture_path = str(output.get("source_fixture_path", ""))
        if fixture_path and not fixture_path.startswith("ppd/tests/fixtures/"):
            errors.append(f"linked_outputs[{index}].source_fixture_path must point under ppd/tests/fixtures/")
        status = _required_text(output, "validation_status", f"linked_outputs[{index}]", errors)
        if status and status not in ACCEPTABLE_OUTPUT_STATUSES:
            errors.append(f"linked_outputs[{index}].validation_status is not review-safe")
        citation_ids = output.get("citation_ids")
        if not isinstance(citation_ids, Sequence) or isinstance(citation_ids, (str, bytes)) or not citation_ids:
            errors.append(f"linked_outputs[{index}].citation_ids must be a non-empty list")
        if output.get("enables_live_execution") is not False:
            errors.append(f"linked_outputs[{index}].enables_live_execution must be false")

    for required_type in REQUIRED_OUTPUT_TYPES:
        if required_type not in output_types:
            errors.append(f"missing linked output: {required_type}")

    checklist = packet.get("operator_review_checklist")
    if not isinstance(checklist, Sequence) or isinstance(checklist, (str, bytes)):
        errors.append("operator_review_checklist must be a list")
        checklist = []

    checklist_sections: set[str] = set()
    for index, item in enumerate(checklist):
        if not isinstance(item, Mapping):
            errors.append(f"operator_review_checklist[{index}] must be an object")
            continue
        section = _required_text(item, "section", f"operator_review_checklist[{index}]", errors)
        if section:
            checklist_sections.add(section)
        _required_text(item, "linked_output_type", f"operator_review_checklist[{index}]", errors)
        _required_text(item, "review_prompt", f"operator_review_checklist[{index}]", errors)
        decision = _required_text(item, "decision", f"operator_review_checklist[{index}]", errors)
        if decision in {"ready_for_live_crawl", "ready_for_submission", "ready_for_payment", "ready_for_upload"}:
            errors.append(f"operator_review_checklist[{index}].decision cannot enable consequential work")
        required_operator = item.get("requires_operator_review")
        if required_operator is not True:
            errors.append(f"operator_review_checklist[{index}].requires_operator_review must be true")
        if item.get("agent_may_execute") is not False:
            errors.append(f"operator_review_checklist[{index}].agent_may_execute must be false")

    for section in REQUIRED_CHECKLIST_SECTIONS:
        if section not in checklist_sections:
            errors.append(f"missing operator checklist section: {section}")

    boundary = packet.get("consequential_action_boundary")
    if not isinstance(boundary, Mapping):
        errors.append("consequential_action_boundary must be an object")
    else:
        for capability in FORBIDDEN_CAPABILITIES:
            decision = boundary.get(capability)
            if decision not in BLOCKING_DECISIONS:
                errors.append(f"consequential_action_boundary.{capability} must remain blocked or manual handoff")

    return errors


def assert_public_data_dry_run_release_packet(packet: Mapping[str, Any]) -> PublicDataDryRunReleasePacket:
    """Validate the packet and assert the live-release boundary stays closed."""

    release_packet = build_public_data_dry_run_release_packet(packet)
    if release_packet.ready_for_live_release:
        raise AssertionError("public-data dry-run release packet cannot be live-release ready")
    for capability in FORBIDDEN_CAPABILITIES:
        if capability not in release_packet.disabled_capabilities:
            raise AssertionError(f"missing disabled capability: {capability}")
    return release_packet


def _required_text(item: Mapping[str, Any], key: str, path: str, errors: list[str]) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{path}.{key} is required")
        return ""
    return value


def _scan_for_private_or_raw_values(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            normalized_key = key_text.lower()
            if normalized_key in PRIVATE_KEYS:
                errors.append(f"{child_path} private value field is not allowed")
            if normalized_key in RAW_BODY_KEYS:
                errors.append(f"{child_path} raw body field is not allowed")
            _scan_for_private_or_raw_values(child, child_path, errors)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, child in enumerate(value):
            _scan_for_private_or_raw_values(child, f"{path}[{index}]", errors)
        return
    if isinstance(value, str):
        lowered = value.lower()
        for marker in PRIVATE_STRING_MARKERS:
            if marker.lower() in lowered:
                errors.append(f"{path} private artifact marker is not allowed")
                break
