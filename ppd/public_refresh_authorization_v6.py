"""Validation for PP&D public refresh authorization packet v6.

The validator is intentionally data-shape oriented so it can be used by tests,
daemon preflight code, or fixture checks without depending on crawler runtime
state. It rejects packets that omit required safety references and rejects any
claim that implies live crawling, persisted raw/private artifacts, official
completion, legal guarantees, or active mutation.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


REQUIRED_NON_EMPTY_FIELDS: tuple[tuple[str, ...], ...] = (
    ("freshness_watchlist_refs",),
    ("smoke_replay_refs",),
    ("live_crawl_deferral_criteria",),
    ("allowlisted_source_groups",),
    ("robots_policy_preflight_checklist_rows",),
    ("no_raw_body_persistence_reminders",),
    ("processor_handoff_manifest_expectations",),
    ("reviewer_authorization_placeholders",),
    ("abort_thresholds",),
    ("validation_commands",),
)

PROHIBITED_TRUE_FIELDS: tuple[str, ...] = (
    "claims_live_crawl_execution",
    "has_downloaded_or_raw_crawl_artifacts",
    "has_private_session_or_auth_artifacts",
    "claims_official_action_completion",
    "claims_legal_or_permitting_guarantees",
    "has_active_mutation_flags",
)

PROHIBITED_TEXT = (
    "live crawl executed",
    "live crawl completed",
    "downloaded artifact",
    "raw crawl artifact",
    "private session",
    "auth artifact",
    "official action completed",
    "official-action completion",
    "legal guarantee",
    "permitting guarantee",
    "active mutation",
)


def _get_path(packet: Mapping[str, Any], path: tuple[str, ...]) -> Any:
    current: Any = packet
    for part in path:
        if not isinstance(current, Mapping) or part not in current:
            return None
        current = current[part]
    return current


def _is_non_empty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return bool(value)
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        return len(value) > 0
    return True


def _walk_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, Mapping):
        strings: list[str] = []
        for item in value.values():
            strings.extend(_walk_strings(item))
        return strings
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        strings = []
        for item in value:
            strings.extend(_walk_strings(item))
        return strings
    return []


def validate_public_refresh_authorization_packet_v6(packet: Mapping[str, Any]) -> list[str]:
    """Return validation errors for a public refresh authorization packet v6."""
    errors: list[str] = []

    if packet.get("version") not in (6, "6", "v6"):
        errors.append("version must be v6")

    for path in REQUIRED_NON_EMPTY_FIELDS:
        if not _is_non_empty(_get_path(packet, path)):
            errors.append(f"missing required {'.'.join(path)}")

    for field in PROHIBITED_TRUE_FIELDS:
        if packet.get(field) is True:
            errors.append(f"prohibited {field}")

    for text in _walk_strings(packet):
        lowered = text.lower()
        for phrase in PROHIBITED_TEXT:
            if phrase in lowered:
                errors.append(f"prohibited claim text: {phrase}")

    return errors


def assert_valid_public_refresh_authorization_packet_v6(packet: Mapping[str, Any]) -> None:
    """Raise ValueError if a packet is not acceptable for public refresh."""
    errors = validate_public_refresh_authorization_packet_v6(packet)
    if errors:
        raise ValueError("public refresh authorization packet v6 rejected: " + "; ".join(errors))
