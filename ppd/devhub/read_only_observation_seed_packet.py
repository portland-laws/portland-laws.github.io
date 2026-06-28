"""Validation for fixture-only DevHub read-only observation seed packets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence


EXPECTED_PACKET_VERSION = "next-devhub-read-only-observation-seed-packet-v1"

REQUIRED_NON_EMPTY_FIELDS: tuple[str, ...] = (
    "post_decision_smoke_replay_references",
    "official_devhub_guidance_placeholders",
    "attended_read_only_observation_targets",
    "authorization_prerequisites",
    "redaction_expectations",
    "fixture_only_capture_schema_updates",
    "unsupported_manual_handoff_reminders",
    "rollback_notes",
    "reviewer_routing",
    "validation_commands",
)

PRIVATE_ARTIFACT_TERMS: tuple[str, ...] = (
    "auth_state",
    "browser_context_storage",
    "cookie",
    "credential",
    "devhub_session",
    "local_private_path",
    "password",
    "payment_detail",
    "private_upload",
    "session_storage",
    "storage_state",
    "token",
)

PROHIBITED_CLAIM_TERMS: tuple[str, ...] = (
    "completed official action",
    "filled form",
    "form fill",
    "form-fill",
    "guarantee permit",
    "guaranteed approval",
    "har captured",
    "legal guarantee",
    "live devhub interaction",
    "made official change",
    "permit guaranteed",
    "screenshot captured",
    "submitted application",
    "trace captured",
    "uploaded correction",
)

MUTATION_FLAG_KEYS: tuple[str, ...] = (
    "active_mutation",
    "allow_live_mutation",
    "can_cancel",
    "can_certify",
    "can_pay",
    "can_schedule",
    "can_submit",
    "can_upload",
    "form_fill_enabled",
    "live_write_enabled",
    "mutation_enabled",
    "official_action_enabled",
    "submit_enabled",
    "upload_enabled",
    "write_enabled",
)

MUTATING_ACTION_TERMS: tuple[str, ...] = (
    "cancel inspection",
    "certify acknowledgement",
    "create account",
    "enter payment",
    "final payment",
    "pay fee",
    "schedule inspection",
    "submit application",
    "submit permit",
    "upload correction",
)


@dataclass(frozen=True)
class SeedPacketValidationResult:
    """Result returned by read-only seed packet validation."""

    accepted: bool
    errors: tuple[str, ...]


def validate_next_devhub_read_only_observation_seed_packet_v1(
    packet: Mapping[str, Any],
) -> SeedPacketValidationResult:
    """Validate a fixture-only DevHub read-only observation seed packet.

    The packet is intended to describe the next attended, read-only observation
    pass. It must include review, rollback, redaction, and validation scaffolding,
    and it must not claim private captures, live interactions, form filling,
    official-action completion, legal outcomes, or enabled mutation behavior.
    """

    errors: list[str] = []

    version = packet.get("version")
    if version != EXPECTED_PACKET_VERSION:
        errors.append(
            f"version must be {EXPECTED_PACKET_VERSION!r}; got {version!r}"
        )

    for field_name in REQUIRED_NON_EMPTY_FIELDS:
        value = packet.get(field_name)
        if not _is_non_empty_sequence(value):
            errors.append(f"{field_name} must be a non-empty list")

    _validate_validation_commands(packet.get("validation_commands"), errors)

    for path, key, value in _walk_packet(packet):
        normalized_key = _normalize(key)
        normalized_value = _normalize(value) if isinstance(value, str) else ""
        search_text = f"{normalized_key} {normalized_value}"

        for term in PRIVATE_ARTIFACT_TERMS:
            if term in search_text:
                errors.append(f"{path} references private/session/auth artifact term {term!r}")

        for term in PROHIBITED_CLAIM_TERMS:
            if term in search_text:
                errors.append(f"{path} contains prohibited claim term {term!r}")

        for term in MUTATING_ACTION_TERMS:
            if term in search_text:
                errors.append(f"{path} contains unsupported manual-action term {term!r}")

        if normalized_key in MUTATION_FLAG_KEYS and value is True:
            errors.append(f"{path} enables active mutation flag {key!r}")

    return SeedPacketValidationResult(accepted=not errors, errors=tuple(errors))


def assert_next_devhub_read_only_observation_seed_packet_v1(
    packet: Mapping[str, Any],
) -> None:
    """Raise ValueError when a seed packet fails validation."""

    result = validate_next_devhub_read_only_observation_seed_packet_v1(packet)
    if not result.accepted:
        raise ValueError("; ".join(result.errors))


def _validate_validation_commands(value: Any, errors: list[str]) -> None:
    if not _is_non_empty_sequence(value):
        return

    for index, command in enumerate(value):
        if not _is_non_empty_sequence(command):
            errors.append(f"validation_commands[{index}] must be a non-empty command list")
            continue
        if not all(isinstance(part, str) and part for part in command):
            errors.append(f"validation_commands[{index}] must contain only non-empty strings")


def _is_non_empty_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes)) and bool(value)


def _walk_packet(value: Any, path: str = "$", key: str = "") -> Iterable[tuple[str, str, Any]]:
    if isinstance(value, Mapping):
        for child_key, child_value in value.items():
            child_key_text = str(child_key)
            child_path = f"{path}.{child_key_text}"
            yield child_path, child_key_text, child_value
            yield from _walk_packet(child_value, child_path, child_key_text)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, child_value in enumerate(value):
            child_path = f"{path}[{index}]"
            yield child_path, key, child_value
            yield from _walk_packet(child_value, child_path, key)


def _normalize(value: Any) -> str:
    return str(value).replace("-", "_").lower()
