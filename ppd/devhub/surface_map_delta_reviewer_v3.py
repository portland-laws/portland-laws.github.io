"""Validation for inactive DevHub surface-map delta reviewer packet v3.

The validator is intentionally deterministic and side-effect free. It only inspects a
packet object supplied by tests or higher-level PP&D review code; it does not open
DevHub, read browser state, persist traces, or mutate the active surface map.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence


REQUIRED_PACKET_FIELDS: tuple[str, ...] = (
    "delta_candidate_refs",
    "reviewer_ready_surface_rows",
    "evidence_refs",
    "safety_attestations",
    "selector_confidence_notes",
    "unresolved_reviewer_holds",
    "rollback_notes",
    "validation_commands",
)

_REQUIRED_FIELD_CODES: dict[str, str] = {
    "delta_candidate_refs": "missing_delta_candidate_references",
    "reviewer_ready_surface_rows": "missing_reviewer_ready_surface_rows",
    "evidence_refs": "missing_evidence_references",
    "safety_attestations": "missing_safety_attestations",
    "selector_confidence_notes": "missing_selector_confidence_notes",
    "unresolved_reviewer_holds": "missing_unresolved_reviewer_holds",
    "rollback_notes": "missing_rollback_notes",
    "validation_commands": "missing_validation_commands",
}

_PRIVATE_ARTIFACT_TERMS: tuple[str, ...] = (
    "auth_state",
    "storage_state",
    "session state",
    "session cookie",
    "cookie jar",
    "credential",
    "password",
    "mfa secret",
    "bearer token",
    "access token",
    "refresh token",
    "devhub_session",
    "playwright/.auth",
    "local private path",
)

_CAPTURE_CLAIM_TERMS: tuple[str, ...] = (
    "screenshot",
    "screenshots",
    "trace.zip",
    "playwright trace",
    "har file",
    ".har",
    "network trace",
)

_LIVE_DEVHUB_CLAIM_TERMS: tuple[str, ...] = (
    "logged into devhub",
    "opened devhub",
    "clicked in devhub",
    "observed live devhub",
    "live devhub session",
    "authenticated devhub",
    "visited devhub",
    "ran playwright against devhub",
)

_ACTIVE_MUTATION_CLAIM_TERMS: tuple[str, ...] = (
    "mutated active surface map",
    "updated active surface map",
    "wrote active surface map",
    "committed active surface map",
    "applied to active surface map",
    "changed active surface map",
)

_FORM_FILL_OR_UPLOAD_TERMS: tuple[str, ...] = (
    "filled form",
    "form fill",
    "entered field",
    "entered application data",
    "uploaded",
    "upload staged",
    "attached document",
    "submitted file",
)

_OFFICIAL_ACTION_TERMS: tuple[str, ...] = (
    "submitted permit",
    "submission completed",
    "certified acknowledgement",
    "paid fee",
    "payment completed",
    "scheduled inspection",
    "cancelled inspection",
    "purchased permit",
    "official action completed",
)

_LEGAL_GUARANTEE_TERMS: tuple[str, ...] = (
    "guaranteed approval",
    "permit will be approved",
    "legally sufficient",
    "legal advice",
    "no permitting risk",
    "complies with all laws",
    "guarantees issuance",
)

_ACTIVE_MUTATION_FLAG_PATHS: tuple[tuple[str, ...], ...] = (
    ("active_mutation",),
    ("active_surface_map_mutation",),
    ("mutates_active_surface_map",),
    ("mutation_mode",),
    ("flags", "active_mutation"),
    ("flags", "mutates_active_surface_map"),
)

_MUTATION_FLAG_TRUE_VALUES: frozenset[str] = frozenset(
    {"true", "yes", "active", "enabled", "mutate", "mutation", "write"}
)


@dataclass(frozen=True)
class PacketValidationIssue:
    """A single deterministic packet validation issue."""

    code: str
    message: str
    path: str


@dataclass(frozen=True)
class PacketValidationResult:
    """Validation result for a reviewer packet."""

    valid: bool
    issues: tuple[PacketValidationIssue, ...]

    def require_valid(self) -> None:
        if self.valid:
            return
        codes = ", ".join(issue.code for issue in self.issues)
        raise ValueError(f"invalid DevHub surface-map delta reviewer packet v3: {codes}")


def validate_surface_map_delta_reviewer_packet_v3(packet: Mapping[str, Any]) -> PacketValidationResult:
    """Validate an inactive DevHub surface-map delta reviewer packet v3."""

    issues: list[PacketValidationIssue] = []

    if not isinstance(packet, Mapping):
        return PacketValidationResult(
            valid=False,
            issues=(
                PacketValidationIssue(
                    code="packet_not_mapping",
                    message="Reviewer packet must be a mapping.",
                    path="$",
                ),
            ),
        )

    packet_version = packet.get("packet_version")
    if packet_version not in ("devhub-surface-map-delta-reviewer-packet-v3", "v3", 3):
        issues.append(
            PacketValidationIssue(
                code="invalid_packet_version",
                message="Reviewer packet must declare packet_version v3.",
                path="$.packet_version",
            )
        )

    active_state = packet.get("active", packet.get("is_active", False))
    if active_state is True:
        issues.append(
            PacketValidationIssue(
                code="packet_must_be_inactive",
                message="Reviewer packet must be inactive and detached from live DevHub workflows.",
                path="$.active",
            )
        )

    for field_name in REQUIRED_PACKET_FIELDS:
        value = packet.get(field_name)
        if _is_missing_or_empty(value):
            issues.append(
                PacketValidationIssue(
                    code=_REQUIRED_FIELD_CODES[field_name],
                    message=f"Reviewer packet requires non-empty {field_name}.",
                    path=f"$.{field_name}",
                )
            )

    issues.extend(_scan_for_banned_terms(packet))
    issues.extend(_scan_for_active_mutation_flags(packet))

    return PacketValidationResult(valid=not issues, issues=tuple(issues))


def validate_packet_or_raise(packet: Mapping[str, Any]) -> None:
    """Raise ValueError unless the packet passes v3 validation."""

    validate_surface_map_delta_reviewer_packet_v3(packet).require_valid()


def _is_missing_or_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, Mapping):
        return len(value) == 0
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        return len(value) == 0
    return False


def _scan_for_banned_terms(packet: Mapping[str, Any]) -> list[PacketValidationIssue]:
    issues: list[PacketValidationIssue] = []
    scanners: tuple[tuple[str, str, tuple[str, ...]], ...] = (
        ("private_session_or_auth_artifact", "Private/session/auth artifacts are not allowed.", _PRIVATE_ARTIFACT_TERMS),
        ("screenshot_trace_or_har_claim", "Screenshots, traces, and HAR claims are not allowed.", _CAPTURE_CLAIM_TERMS),
        ("live_devhub_interaction_claim", "Live DevHub interaction claims are not allowed.", _LIVE_DEVHUB_CLAIM_TERMS),
        ("active_surface_map_mutation_claim", "Active surface-map mutation claims are not allowed.", _ACTIVE_MUTATION_CLAIM_TERMS),
        ("form_fill_or_upload_claim", "Form-fill and upload claims are not allowed.", _FORM_FILL_OR_UPLOAD_TERMS),
        ("official_action_completion_claim", "Official-action completion claims are not allowed.", _OFFICIAL_ACTION_TERMS),
        ("legal_or_permitting_guarantee", "Legal or permitting guarantees are not allowed.", _LEGAL_GUARANTEE_TERMS),
    )

    for path, text in _iter_strings(packet):
        normalized = " ".join(text.lower().split())
        for code, message, terms in scanners:
            if any(term in normalized for term in terms):
                issues.append(PacketValidationIssue(code=code, message=message, path=path))
                break
    return issues


def _scan_for_active_mutation_flags(packet: Mapping[str, Any]) -> list[PacketValidationIssue]:
    issues: list[PacketValidationIssue] = []
    for path_parts in _ACTIVE_MUTATION_FLAG_PATHS:
        present, value = _get_nested(packet, path_parts)
        if not present:
            continue
        if value is True or str(value).strip().lower() in _MUTATION_FLAG_TRUE_VALUES:
            issues.append(
                PacketValidationIssue(
                    code="active_mutation_flag",
                    message="Active mutation flags are not allowed in inactive reviewer packets.",
                    path="$" + "".join(f".{part}" for part in path_parts),
                )
            )
    return issues


def _get_nested(value: Mapping[str, Any], path_parts: tuple[str, ...]) -> tuple[bool, Any]:
    current: Any = value
    for part in path_parts:
        if not isinstance(current, Mapping) or part not in current:
            return False, None
        current = current[part]
    return True, current


def _iter_strings(value: Any, path: str = "$") -> Iterable[tuple[str, str]]:
    if isinstance(value, str):
        yield path, value
        return
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_key = str(key).replace("'", "")
            yield from _iter_strings(child, f"{path}.{child_key}")
        return
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        for index, child in enumerate(value):
            yield from _iter_strings(child, f"{path}[{index}]")
