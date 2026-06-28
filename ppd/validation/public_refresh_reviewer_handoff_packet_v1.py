"""Validation for public refresh reviewer handoff packet v1."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Requirement:
    field: str
    description: str


REQUIREMENTS: tuple[Requirement, ...] = (
    Requirement("citation_impact_queue_refs", "citation impact queue references"),
    Requirement("preflight_checklist_refs", "preflight checklist references"),
    Requirement("reviewer_ready_seed_decisions", "reviewer-ready seed decisions"),
    Requirement("metadata_only_archive_expectations", "metadata-only archive expectations"),
    Requirement("citation_refresh_priorities", "citation refresh priorities"),
    Requirement("stale_source_hold_recommendations", "stale-source hold recommendations"),
    Requirement("owner_routing", "owner routing"),
    Requirement("dependency_ordering", "dependency ordering"),
    Requirement("rollback_checkpoints", "rollback checkpoints"),
    Requirement("validation_commands", "validation commands"),
)

PROHIBITED_TERMS: tuple[tuple[str, str], ...] = (
    ("private artifact", "private artifacts are not allowed"),
    ("raw artifact", "raw artifacts are not allowed"),
    ("downloaded artifact", "downloaded artifacts are not allowed"),
    ("downloaded document", "downloaded documents are not allowed"),
    ("live crawl", "live crawl claims are not allowed"),
    ("devhub", "DevHub claims are not allowed"),
    ("release activation", "release activation claims are not allowed"),
    ("release activated", "release activation claims are not allowed"),
    ("official action complete", "official-action completion claims are not allowed"),
    ("official action completed", "official-action completion claims are not allowed"),
    ("legal guarantee", "legal guarantees are not allowed"),
    ("permitting guarantee", "permitting guarantees are not allowed"),
    ("active mutation", "active mutation flags are not allowed"),
)

MUTATION_FLAG_KEYS = frozenset(
    {
        "active_mutation",
        "active_mutations",
        "allow_mutation",
        "allow_mutations",
        "mutates_public_state",
        "mutation_enabled",
        "write_enabled",
    }
)


def validate_public_refresh_reviewer_handoff_packet_v1(packet: Mapping[str, Any]) -> list[str]:
    """Return validation errors for a public refresh reviewer handoff packet v1."""
    errors: list[str] = []

    version = packet.get("version")
    if version != "public-refresh-reviewer-handoff-packet-v1":
        errors.append("version must be public-refresh-reviewer-handoff-packet-v1")

    for requirement in REQUIREMENTS:
        if _is_missing(packet.get(requirement.field)):
            errors.append(f"missing {requirement.description}: {requirement.field}")

    flattened = "\n".join(_walk_text(packet)).lower()
    for term, message in PROHIBITED_TERMS:
        if term in flattened:
            errors.append(message)

    for key, value in _walk_items(packet):
        normalized_key = key.lower().replace("-", "_")
        if normalized_key in MUTATION_FLAG_KEYS and value is True:
            errors.append(f"active mutation flag is not allowed: {key}")

    return sorted(set(errors))


def assert_public_refresh_reviewer_handoff_packet_v1(packet: Mapping[str, Any]) -> None:
    errors = validate_public_refresh_reviewer_handoff_packet_v1(packet)
    if errors:
        raise ValueError("invalid public refresh reviewer handoff packet v1: " + "; ".join(errors))


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, Mapping):
        return not value
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        return len(value) == 0
    return False


def _walk_text(value: Any) -> list[str]:
    text: list[str] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            text.append(str(key))
            text.extend(_walk_text(nested))
    elif isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        for nested in value:
            text.extend(_walk_text(nested))
    elif isinstance(value, str):
        text.append(value)
    return text


def _walk_items(value: Any) -> list[tuple[str, Any]]:
    items: list[tuple[str, Any]] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = str(key)
            items.append((key_text, nested))
            items.extend(_walk_items(nested))
    elif isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        for nested in value:
            items.extend(_walk_items(nested))
    return items
