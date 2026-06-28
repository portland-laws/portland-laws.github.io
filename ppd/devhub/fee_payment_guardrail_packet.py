"""Fixture-first fee/payment guardrail packet validation for DevHub workflows.

This module validates committed synthetic packets only. It does not launch a
browser, inspect live DevHub pages, collect payment details, execute payment
controls, or store authenticated session artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping

from ppd.devhub.fee_payment_guardrail_packet_validation import (
    FeePaymentGuardrailPacketError,
    validate_fee_payment_guardrail_packet as validate_commit_safe_packet,
)


REQUIRED_SECTION_IDS = (
    "fee_trigger_explanation",
    "fee_notice_read_only_review",
    "blocked_payment_detail_entry",
    "blocked_final_payment_execution",
    "exact_confirmation_language",
    "next_safe_alternatives",
)

BLOCKED_PAYMENT_ACTION_IDS = (
    "payment_detail_entry",
    "final_payment_execution",
)


@dataclass(frozen=True)
class FeePaymentGuardrailSection:
    """A normalized guardrail section from a synthetic fixture packet."""

    section_id: str
    title: str
    guardrail: str
    allowed_autonomous: bool
    requires_manual_handoff: bool
    requires_exact_confirmation: bool
    blocked_action_ids: tuple[str, ...]
    source_evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class FeePaymentGuardrailPacket:
    """Validated fee/payment guardrail packet summary."""

    packet_id: str
    workflow_id: str
    permit_type: str
    section_ids: tuple[str, ...]
    blocked_action_ids: tuple[str, ...]
    next_safe_alternative_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "packet_id": self.packet_id,
            "workflow_id": self.workflow_id,
            "permit_type": self.permit_type,
            "section_ids": list(self.section_ids),
            "blocked_action_ids": list(self.blocked_action_ids),
            "next_safe_alternative_ids": list(self.next_safe_alternative_ids),
            "validation_status": "accepted_fixture_first_fee_payment_guardrail_packet",
        }


def load_fee_payment_guardrail_packet(path: str | Path) -> dict[str, Any]:
    """Load a guardrail packet fixture from disk."""

    with Path(path).open(encoding="utf-8") as fixture_file:
        loaded = json.load(fixture_file)
    if not isinstance(loaded, dict):
        raise FeePaymentGuardrailPacketError("fee/payment guardrail fixture must be a JSON object")
    return loaded


def validate_fee_payment_guardrail_packet_file(path: str | Path) -> FeePaymentGuardrailPacket:
    """Load and validate a committed synthetic guardrail packet fixture."""

    return validate_fee_payment_guardrail_packet(load_fee_payment_guardrail_packet(path))


def validate_fee_payment_guardrail_packet(packet: Mapping[str, Any]) -> FeePaymentGuardrailPacket:
    """Validate the task-specific fee/payment guardrail packet shape."""

    validate_commit_safe_packet(packet)

    _require_false(packet, "live_devhub_session")
    _require_false(packet, "auth_state_saved")
    _require_text_value(packet, "source_mode", "synthetic_fixture_only")

    packet_id = _required_text(packet, "packet_id")
    workflow = _required_mapping(packet, "synthetic_workflow")
    workflow_id = _required_text(workflow, "workflow_id")
    permit_type = _required_text(workflow, "permit_type")

    sections = _sections_by_id(packet.get("guardrail_sections"))
    observed_section_ids = tuple(sections)
    if observed_section_ids != REQUIRED_SECTION_IDS:
        raise FeePaymentGuardrailPacketError(
            "guardrail_sections must appear in the required task order: " + ", ".join(REQUIRED_SECTION_IDS)
        )

    _validate_fee_trigger_section(sections["fee_trigger_explanation"])
    _validate_read_only_section(sections["fee_notice_read_only_review"])
    _validate_blocked_section(sections["blocked_payment_detail_entry"], "payment_detail_entry")
    _validate_blocked_section(sections["blocked_final_payment_execution"], "final_payment_execution")
    _validate_exact_confirmation_section(sections["exact_confirmation_language"])
    _validate_alternatives_section(sections["next_safe_alternatives"])

    next_safe_alternative_ids = _validate_next_safe_alternatives(packet.get("next_safe_alternatives"))

    return FeePaymentGuardrailPacket(
        packet_id=packet_id,
        workflow_id=workflow_id,
        permit_type=permit_type,
        section_ids=observed_section_ids,
        blocked_action_ids=BLOCKED_PAYMENT_ACTION_IDS,
        next_safe_alternative_ids=next_safe_alternative_ids,
    )


def _sections_by_id(value: Any) -> dict[str, FeePaymentGuardrailSection]:
    if not isinstance(value, list):
        raise FeePaymentGuardrailPacketError("guardrail_sections must be a list")

    sections: dict[str, FeePaymentGuardrailSection] = {}
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise FeePaymentGuardrailPacketError(f"guardrail_sections[{index}] must be an object")
        section = _section_from_mapping(item, index)
        if section.section_id in sections:
            raise FeePaymentGuardrailPacketError(f"duplicate guardrail section {section.section_id}")
        sections[section.section_id] = section
    return sections


def _section_from_mapping(value: Mapping[str, Any], index: int) -> FeePaymentGuardrailSection:
    path = f"guardrail_sections[{index}]"
    return FeePaymentGuardrailSection(
        section_id=_required_text(value, "section_id", path),
        title=_required_text(value, "title", path),
        guardrail=_required_text(value, "guardrail", path),
        allowed_autonomous=_required_bool(value, "allowed_autonomous", path),
        requires_manual_handoff=_required_bool(value, "requires_manual_handoff", path),
        requires_exact_confirmation=_required_bool(value, "requires_exact_confirmation", path),
        blocked_action_ids=_string_tuple(value.get("blocked_action_ids"), f"{path}.blocked_action_ids"),
        source_evidence_ids=_string_tuple(value.get("source_evidence_ids"), f"{path}.source_evidence_ids"),
    )


def _validate_fee_trigger_section(section: FeePaymentGuardrailSection) -> None:
    if not section.allowed_autonomous:
        raise FeePaymentGuardrailPacketError("fee_trigger_explanation must be available for autonomous explanation")
    if section.requires_manual_handoff or section.requires_exact_confirmation:
        raise FeePaymentGuardrailPacketError("fee_trigger_explanation must not be a handoff or exact-confirmation gate")
    if not section.source_evidence_ids:
        raise FeePaymentGuardrailPacketError("fee_trigger_explanation must cite source evidence")


def _validate_read_only_section(section: FeePaymentGuardrailSection) -> None:
    if not section.allowed_autonomous:
        raise FeePaymentGuardrailPacketError("fee_notice_read_only_review must allow read-only autonomous review")
    if section.requires_manual_handoff or section.requires_exact_confirmation:
        raise FeePaymentGuardrailPacketError("fee_notice_read_only_review must not require payment handoff")
    if section.blocked_action_ids:
        raise FeePaymentGuardrailPacketError("fee_notice_read_only_review must not block its own read-only observation")


def _validate_blocked_section(section: FeePaymentGuardrailSection, expected_action_id: str) -> None:
    if section.allowed_autonomous:
        raise FeePaymentGuardrailPacketError(f"{section.section_id} must not be autonomously allowed")
    if not section.requires_manual_handoff:
        raise FeePaymentGuardrailPacketError(f"{section.section_id} must require manual handoff")
    if not section.requires_exact_confirmation:
        raise FeePaymentGuardrailPacketError(f"{section.section_id} must require exact confirmation")
    if section.blocked_action_ids != (expected_action_id,):
        raise FeePaymentGuardrailPacketError(f"{section.section_id} must block only {expected_action_id}")


def _validate_exact_confirmation_section(section: FeePaymentGuardrailSection) -> None:
    if section.allowed_autonomous:
        raise FeePaymentGuardrailPacketError("exact_confirmation_language must not authorize automation")
    if not section.requires_manual_handoff or not section.requires_exact_confirmation:
        raise FeePaymentGuardrailPacketError("exact_confirmation_language must require attended exact confirmation")
    if set(section.blocked_action_ids) != set(BLOCKED_PAYMENT_ACTION_IDS):
        raise FeePaymentGuardrailPacketError("exact_confirmation_language must cover both payment stop points")


def _validate_alternatives_section(section: FeePaymentGuardrailSection) -> None:
    if not section.allowed_autonomous:
        raise FeePaymentGuardrailPacketError("next_safe_alternatives must be autonomously explainable")
    if section.requires_manual_handoff or section.requires_exact_confirmation:
        raise FeePaymentGuardrailPacketError("next_safe_alternatives must not be consequential actions")


def _validate_next_safe_alternatives(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list) or len(value) == 0:
        raise FeePaymentGuardrailPacketError("next_safe_alternatives must be a non-empty list")

    alternative_ids: list[str] = []
    for index, item in enumerate(value):
        path = f"next_safe_alternatives[{index}]"
        if not isinstance(item, Mapping):
            raise FeePaymentGuardrailPacketError(f"{path} must be an object")
        alternative_id = _required_text(item, "alternative_id", path)
        alternative_ids.append(alternative_id)
        if item.get("allowed_autonomous") is not True:
            raise FeePaymentGuardrailPacketError(f"{path} must be allowed as a safe autonomous alternative")
        if item.get("official_action") is True or item.get("financial_action") is True:
            raise FeePaymentGuardrailPacketError(f"{path} must not be official or financial")
        if item.get("requires_exact_confirmation") is True:
            raise FeePaymentGuardrailPacketError(f"{path} must not require exact confirmation")
        if not _string_tuple(item.get("source_evidence_ids"), f"{path}.source_evidence_ids"):
            raise FeePaymentGuardrailPacketError(f"{path} must cite source evidence")
    return tuple(alternative_ids)


def _required_mapping(value: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    child = value.get(key)
    if not isinstance(child, Mapping):
        raise FeePaymentGuardrailPacketError(f"{key} must be an object")
    return child


def _required_text(value: Mapping[str, Any], key: str, path: str | None = None) -> str:
    child = value.get(key)
    if not isinstance(child, str) or not child.strip():
        label = f"{path}.{key}" if path else key
        raise FeePaymentGuardrailPacketError(f"{label} must be a non-empty string")
    return child.strip()


def _required_bool(value: Mapping[str, Any], key: str, path: str) -> bool:
    child = value.get(key)
    if not isinstance(child, bool):
        raise FeePaymentGuardrailPacketError(f"{path}.{key} must be a boolean")
    return child


def _require_false(value: Mapping[str, Any], key: str) -> None:
    if value.get(key) is not False:
        raise FeePaymentGuardrailPacketError(f"{key} must be false for committed fixtures")


def _require_text_value(value: Mapping[str, Any], key: str, expected: str) -> None:
    observed = value.get(key)
    if observed != expected:
        raise FeePaymentGuardrailPacketError(f"{key} must be {expected}")


def _string_tuple(value: Any, path: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise FeePaymentGuardrailPacketError(f"{path} must be a list")
    strings: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise FeePaymentGuardrailPacketError(f"{path}[{index}] must be a non-empty string")
        strings.append(item.strip())
    return tuple(strings)
