"""Validation for PP&D public freshness watchlist handoff packet v7.

The packet is validated as plain data so the daemon can reject incomplete or
unsafe public refresh handoffs before any crawler, browser, processor, registry,
requirement, or guardrail mutation code is allowed to run.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any, Iterable, Mapping, Sequence


REQUIRED_SECTION_ALIASES: tuple[tuple[str, tuple[str, ...], str], ...] = (
    ("compatibility_refs", ("compatibility_refs", "agent_api_compatibility_refs", "compatibility_matrix_refs"), "compatibility references"),
    ("smoke_replay_refs", ("smoke_replay_refs", "post_decision_smoke_replay_refs", "smoke_replay_packet_refs"), "smoke replay references"),
    ("rollback_readiness_refs", ("rollback_readiness_refs", "rollback_refs", "rollback_packet_refs"), "rollback references"),
    ("source_registry_refs", ("source_registry_refs", "source_registry_reference_rows", "source_registry_handoff_refs"), "source registry references"),
    ("next_refresh_watch_rows", ("next_refresh_watch_rows", "next_refresh_watchlist_rows", "freshness_watch_rows"), "next-refresh watch rows"),
    ("stale_source_risk_notes", ("stale_source_risk_notes", "stale_source_risks", "stale_source_risk_rows"), "stale-source risk notes"),
    ("citation_repair_owner_placeholders", ("citation_repair_owner_placeholders", "citation_repair_owner_rows"), "citation repair owner placeholders"),
    ("guarded_automation_hold_conditions", ("guarded_automation_hold_conditions", "automation_hold_conditions", "guarded_hold_conditions"), "guarded automation hold conditions"),
    ("public_recrawl_authorization_prerequisites", ("public_recrawl_authorization_prerequisites", "recrawl_authorization_prerequisites"), "public recrawl authorization prerequisites"),
    ("validation_commands", ("validation_commands",), "validation commands"),
)

FORBIDDEN_KEY_FRAGMENTS: tuple[tuple[str, str], ...] = (
    ("live_crawl_execution_claim", "live crawl execution claims"),
    ("live_crawl_executed", "live crawl execution claims"),
    ("crawl_executed", "live crawl execution claims"),
    ("downloaded_artifact", "downloaded or raw crawl artifacts"),
    ("downloaded_document", "downloaded or raw crawl artifacts"),
    ("raw_crawl_artifact", "downloaded or raw crawl artifacts"),
    ("raw_crawl_output", "downloaded or raw crawl artifacts"),
    ("raw_download", "downloaded or raw crawl artifacts"),
    ("session_artifact", "private/session/auth artifacts"),
    ("session_state", "private/session/auth artifacts"),
    ("auth_artifact", "private/session/auth artifacts"),
    ("auth_state", "private/session/auth artifacts"),
    ("cookie", "private/session/auth artifacts"),
    ("credential", "private/session/auth artifacts"),
    ("trace", "private/session/auth artifacts"),
    ("har", "private/session/auth artifacts"),
    ("screenshot", "private/session/auth artifacts"),
    ("official_action_completion", "official-action completion claims"),
    ("official_action_completed", "official-action completion claims"),
    ("permit_guarantee", "legal or permitting guarantees"),
    ("permitting_guarantee", "legal or permitting guarantees"),
    ("legal_guarantee", "legal or permitting guarantees"),
    ("active_mutation", "active mutation flags"),
    ("mutation_enabled", "active mutation flags"),
)

FORBIDDEN_TEXT_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\blive\s+crawl\s+(?:was\s+)?(?:executed|run|completed)\b", re.I), "live crawl execution claims"),
    (re.compile(r"\bran\s+a\s+live\s+crawl\b", re.I), "live crawl execution claims"),
    (re.compile(r"\bdownloaded\s+(?:crawl\s+)?(?:artifact|document)\b", re.I), "downloaded or raw crawl artifacts"),
    (re.compile(r"\braw\s+crawl\s+(?:artifact|output)\b", re.I), "downloaded or raw crawl artifacts"),
    (re.compile(r"\b(?:private|session|auth)\s+artifact\b", re.I), "private/session/auth artifacts"),
    (re.compile(r"\bofficial\s+action\s+(?:was\s+)?completed\b", re.I), "official-action completion claims"),
    (re.compile(r"\b(?:legal|permit|permitting)\s+guarantee\b", re.I), "legal or permitting guarantees"),
    (re.compile(r"\bmutation\s+(?:is\s+)?(?:active|enabled)\b", re.I), "active mutation flags"),
)

SAFE_TEXT_PATH_FRAGMENTS = (
    "prohibition",
    "reminder",
    "precondition",
    "prerequisite",
    "hold",
    "validation",
    "allowlist",
    "forbidden",
)


@dataclass(frozen=True)
class ValidationResult:
    """Result from public freshness watchlist handoff v7 validation."""

    valid: bool
    errors: tuple[str, ...]


class PublicRefreshAuthorizationV7Error(ValueError):
    """Raised when a packet is not valid for public refresh authorization v7."""


def validate_public_refresh_authorization_packet_v7(packet: Mapping[str, Any] | str | bytes) -> ValidationResult:
    """Validate a public freshness watchlist handoff packet v7."""

    parsed = _parse_packet(packet)
    errors: list[str] = []

    version = parsed.get("packet_version", parsed.get("version"))
    if version != 7 and version != "7" and version != "v7":
        errors.append("packet version must be v7")

    for canonical, aliases, label in REQUIRED_SECTION_ALIASES:
        value = _first_present(parsed, aliases)
        if not _is_present(value):
            errors.append(f"missing {label}")
        elif canonical == "validation_commands" and not _valid_validation_commands(value):
            errors.append("validation commands must be non-empty argv arrays")

    errors.extend(_forbidden_key_errors(parsed))
    errors.extend(_forbidden_text_errors(parsed))

    return ValidationResult(valid=not errors, errors=tuple(dict.fromkeys(errors)))


def require_public_refresh_authorization_packet_v7(packet: Mapping[str, Any] | str | bytes) -> Mapping[str, Any]:
    """Return the parsed packet or raise if it is not authorized for v7 refresh."""

    parsed = _parse_packet(packet)
    result = validate_public_refresh_authorization_packet_v7(parsed)
    if not result.valid:
        raise PublicRefreshAuthorizationV7Error("; ".join(result.errors))
    return parsed


def _parse_packet(packet: Mapping[str, Any] | str | bytes) -> Mapping[str, Any]:
    if isinstance(packet, Mapping):
        return packet
    if isinstance(packet, bytes):
        packet = packet.decode("utf-8")
    if isinstance(packet, str):
        decoded = json.loads(packet)
        if not isinstance(decoded, Mapping):
            raise PublicRefreshAuthorizationV7Error("packet JSON must decode to an object")
        return decoded
    raise PublicRefreshAuthorizationV7Error("packet must be a mapping, JSON string, or JSON bytes")


def _first_present(packet: Mapping[str, Any], aliases: Sequence[str]) -> Any:
    for alias in aliases:
        if alias in packet:
            return packet[alias]
    return None


def _is_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return bool(value) and all(_is_present(item) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        return bool(value) and all(_is_present(item) for item in value)
    return True


def _valid_validation_commands(value: Any) -> bool:
    if not isinstance(value, Sequence) or isinstance(value, (bytes, bytearray, str)) or not value:
        return False
    for command in value:
        if not isinstance(command, Sequence) or isinstance(command, (bytes, bytearray, str)) or not command:
            return False
        if not all(isinstance(part, str) and part.strip() for part in command):
            return False
    return True


def _walk(value: Any, path: tuple[str, ...] = ()) -> Iterable[tuple[tuple[str, ...], Any]]:
    yield path, value
    if isinstance(value, Mapping):
        for key, child in value.items():
            yield from _walk(child, (*path, str(key)))
    elif isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        for index, child in enumerate(value):
            yield from _walk(child, (*path, str(index)))


def _normalized_path(path: tuple[str, ...]) -> str:
    return ".".join(part.strip().lower().replace("-", "_").replace(" ", "_") for part in path)


def _truthy_for_rejection(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip()) and value.strip().lower() not in {"false", "no", "none", "null", "0"}
    return bool(value)


def _forbidden_key_errors(packet: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for path, value in _walk(packet):
        normalized = _normalized_path(path)
        if not path:
            continue
        for fragment, label in FORBIDDEN_KEY_FRAGMENTS:
            if fragment in normalized and _truthy_for_rejection(value):
                errors.append(f"rejects {label}")
        if "mutation" in normalized and _truthy_for_rejection(value):
            errors.append("rejects active mutation flags")
    return errors


def _forbidden_text_errors(packet: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for path, value in _walk(packet):
        if not isinstance(value, str) or not value.strip():
            continue
        normalized = _normalized_path(path)
        if any(fragment in normalized for fragment in SAFE_TEXT_PATH_FRAGMENTS):
            continue
        for pattern, label in FORBIDDEN_TEXT_PATTERNS:
            if pattern.search(value):
                errors.append(f"rejects {label}")
    return errors
