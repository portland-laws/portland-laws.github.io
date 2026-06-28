from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

REQUIRED_FIELDS = (
    "inactive_promotion_candidate_references",
    "go_no_go_recommendation",
    "unresolved_hold_inventory",
    "source_freshness_clearance_status",
    "agent_api_compatibility_caveats",
    "rollback_owner_placeholders",
    "post_decision_smoke_replay_plan",
    "agent_notification_notes",
    "validation_commands",
)

PRIVATE_ARTIFACT_KEYS = re.compile(
    r"(auth|bearer|cookie|credential|devhub_session|oauth|password|private|secret|session|token)",
    re.IGNORECASE,
)

PRIVATE_ARTIFACT_TEXT = re.compile(
    r"(authorization:\s*bearer|session[_ -]?cookie|auth[_ -]?state|devhub[_ -]?session|private[_ -]?session|access[_ -]?token|refresh[_ -]?token)",
    re.IGNORECASE,
)

ACTIVE_ACTIVATION_TEXT = re.compile(
    r"\b(activated|activation\s+complete|active\s+activation|live\s+activation|promoted\s+to\s+active|now\s+active)\b",
    re.IGNORECASE,
)

OFFICIAL_ACTION_TEXT = re.compile(
    r"\b(official\s+action\s+(complete|completed|filed|submitted)|permit\s+(issued|approved)|application\s+submitted|certification\s+complete|inspection\s+passed)\b",
    re.IGNORECASE,
)

LEGAL_GUARANTEE_TEXT = re.compile(
    r"\b(guarantee(?:d|s)?\s+(approval|compliance|permit|permitting|legal)|legal\s+guarantee|permit\s+guarantee|will\s+be\s+approved|cannot\s+be\s+denied)\b",
    re.IGNORECASE,
)

MUTATION_FLAG_KEYS = {
    "active_mutation",
    "allow_mutation",
    "can_mutate",
    "live_mutation",
    "mutation_enabled",
    "mutations_enabled",
    "write_enabled",
}

MUTATION_MODE_KEYS = {"action_mode", "mode", "run_mode"}
MUTATION_MODE_VALUES = {"active", "apply", "live", "mutate", "mutation", "write"}


def validate_release_decision_packet_v5(packet: Mapping[str, Any]) -> list[str]:
    """Return validation errors for a PP&D release decision packet v5."""
    errors: list[str] = []

    if packet.get("schema_version") not in {"release-decision-packet-v5", "v5", 5}:
        errors.append("schema_version must identify release decision packet v5")

    for field in REQUIRED_FIELDS:
        if not _has_value(packet.get(field)):
            errors.append(f"missing required field: {field}")

    _scan_node(packet, (), errors)
    return errors


def require_valid_release_decision_packet_v5(packet: Mapping[str, Any]) -> None:
    errors = validate_release_decision_packet_v5(packet)
    if errors:
        raise ValueError("release decision packet v5 validation failed: " + "; ".join(errors))


def load_and_validate_release_decision_packet_v5(path: str | Path) -> Mapping[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        packet = json.load(handle)
    if not isinstance(packet, Mapping):
        raise ValueError("release decision packet v5 must be a JSON object")
    require_valid_release_decision_packet_v5(packet)
    return packet


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping) or (isinstance(value, Sequence) and not isinstance(value, bytes)):
        return len(value) > 0
    return True


def _scan_node(node: Any, path: tuple[str, ...], errors: list[str]) -> None:
    if isinstance(node, Mapping):
        for key, value in node.items():
            key_text = str(key)
            child_path = path + (key_text,)
            lowered_key = key_text.lower()

            if PRIVATE_ARTIFACT_KEYS.search(key_text):
                errors.append(f"private/session/auth artifact field is not allowed: {_format_path(child_path)}")

            if lowered_key in MUTATION_FLAG_KEYS and value is True:
                errors.append(f"active mutation flag is not allowed: {_format_path(child_path)}")

            if lowered_key in MUTATION_MODE_KEYS and isinstance(value, str) and value.strip().lower() in MUTATION_MODE_VALUES:
                errors.append(f"active mutation mode is not allowed: {_format_path(child_path)}")

            if lowered_key == "dry_run" and value is False:
                errors.append(f"active mutation dry_run=false is not allowed: {_format_path(child_path)}")

            _scan_node(value, child_path, errors)
        return

    if isinstance(node, str):
        location = _format_path(path)
        checks = (
            (PRIVATE_ARTIFACT_TEXT, "private/session/auth artifact text is not allowed"),
            (ACTIVE_ACTIVATION_TEXT, "active activation claim is not allowed"),
            (OFFICIAL_ACTION_TEXT, "official-action completion claim is not allowed"),
            (LEGAL_GUARANTEE_TEXT, "legal or permitting guarantee is not allowed"),
        )
        for pattern, message in checks:
            if pattern.search(node):
                errors.append(f"{message}: {location}")
        return

    if isinstance(node, Sequence) and not isinstance(node, (bytes, bytearray, str)):
        for index, value in enumerate(node):
            _scan_node(value, path + (str(index),), errors)


def _format_path(path: tuple[str, ...]) -> str:
    return ".".join(path) if path else "$"
