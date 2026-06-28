"""Validation for attended DevHub read-only observation authorization checklist v1.

This module is intentionally deterministic and fixture-friendly. It validates a
plain mapping that describes whether a proposed DevHub observation packet has
the prerequisites needed before any attended, read-only manual observation.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

CHECKLIST_VERSION = "devhub-readonly-observation-authorization-v1"

REQUIRED_FIELDS: tuple[str, ...] = (
    "seed_packet_references",
    "official_devhub_guidance_placeholders",
    "attendance_prerequisites",
    "account_scope_reminders",
    "readonly_route_expectations",
    "manual_login_mfa_captcha_handoff_notes",
    "prohibited_capture_artifact_reminders",
    "redaction_acceptance_prerequisites",
    "reviewer_routing",
    "rollback_notes",
    "validation_commands",
)

PROHIBITED_FLAGS: tuple[str, ...] = (
    "private_session_or_auth_artifacts",
    "screenshots_traces_or_har_claims",
    "live_devhub_interaction_claims",
    "form_fill_claims",
    "official_action_completion_claims",
    "legal_or_permitting_guarantees",
    "active_mutation_flags",
)


@dataclass(frozen=True)
class ChecklistValidationResult:
    """Result returned by ``validate_devhub_readonly_observation_checklist``."""

    ok: bool
    errors: tuple[str, ...]


def validate_devhub_readonly_observation_checklist(packet: Mapping[str, Any]) -> ChecklistValidationResult:
    """Validate a DevHub read-only observation authorization checklist packet.

    Required checklist fields must be present and non-empty. Prohibited fields
    must be absent, false, or empty. The packet must explicitly identify the v1
    checklist version so future revisions can be introduced without ambiguity.
    """

    errors: list[str] = []

    version = packet.get("checklist_version")
    if version != CHECKLIST_VERSION:
        errors.append(f"checklist_version must be {CHECKLIST_VERSION!r}")

    for field in REQUIRED_FIELDS:
        if _is_missing(packet.get(field)):
            errors.append(f"missing required checklist item: {field}")

    for field in PROHIBITED_FLAGS:
        if _is_present_or_enabled(packet.get(field)):
            errors.append(f"prohibited checklist claim or artifact present: {field}")

    return ChecklistValidationResult(ok=not errors, errors=tuple(errors))


def assert_valid_devhub_readonly_observation_checklist(packet: Mapping[str, Any]) -> None:
    """Raise ``ValueError`` when the checklist packet is not valid."""

    result = validate_devhub_readonly_observation_checklist(packet)
    if not result.ok:
        raise ValueError("; ".join(result.errors))


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, Mapping):
        return not value
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return len(value) == 0
    return value is False


def _is_present_or_enabled(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return bool(value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return len(value) > 0
    return bool(value)
