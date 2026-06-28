"""Validation for DevHub surface registry reviewer approval packets.

The validator is intentionally fixture-friendly and side-effect free. It checks a
plain mapping before a surface registry reviewer packet can be accepted for a
DevHub surface update.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import PurePosixPath, PureWindowsPath
from typing import Any, Iterable, Mapping, Sequence


PRIVATE_VALUE_KEYS = {
    "access_token",
    "auth_header",
    "authorization",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "csrf",
    "id_token",
    "jwt",
    "password",
    "private_value",
    "raw_authenticated_value",
    "refresh_token",
    "secret",
    "session_cookie",
    "session_token",
    "token",
}

PRIVATE_ARTIFACT_KEYS = {
    "auth_state",
    "auth_storage",
    "browser_session",
    "downloaded_private_document",
    "har",
    "har_path",
    "local_private_path",
    "raw_crawl_output",
    "screenshot",
    "screenshot_path",
    "session_artifact",
    "session_file",
    "storage_state",
    "storage_state_path",
    "trace",
    "trace_path",
}

CONSEQUENTIAL_CONTROL_TERMS = (
    "submit",
    "certify",
    "upload",
    "payment",
    "pay",
    "purchase",
    "schedule",
    "cancel",
    "withdraw",
    "reactivate",
    "extension",
)

LOCAL_PRIVATE_PATH_PATTERNS = (
    re.compile(r"^~(?:/|$)"),
    re.compile(r"^file://", re.IGNORECASE),
    re.compile(r"^/(?:home|Users|var/folders|private|tmp|mnt|media)/"),
    re.compile(r"^[A-Za-z]:\\(?:Users|Documents and Settings|Temp|Windows\\Temp)\\", re.IGNORECASE),
)

ARTIFACT_PATH_SUFFIXES = (
    ".har",
    ".trace",
    ".trace.zip",
    ".webm",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".zip",
)

REDACTED_VALUES = {"", "[redacted]", "", "redacted", None}


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    path: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "path": self.path, "message": self.message}


class SurfaceRegistryApprovalPacketError(ValueError):
    """Raised when an approval packet fails validation."""

    def __init__(self, issues: Sequence[ValidationIssue]) -> None:
        self.issues = tuple(issues)
        summary = "; ".join(f"{issue.code} at {issue.path}" for issue in self.issues)
        super().__init__(summary)


def validate_surface_registry_approval_packet(packet: Mapping[str, Any]) -> list[ValidationIssue]:
    """Return validation issues for a DevHub surface approval packet.

    A valid packet is redacted, fixture-safe, human-reviewed, rollback-aware,
    and does not claim live browser execution or active registry mutation.
    """

    issues: list[ValidationIssue] = []
    if not isinstance(packet, Mapping):
        return [ValidationIssue("packet_not_mapping", "$", "approval packet must be a mapping")]

    issues.extend(_scan_private_values(packet))
    issues.extend(_validate_reviewer_signoffs(packet))
    issues.extend(_validate_redaction_attestation(packet))
    issues.extend(_validate_rollback_notes(packet))
    issues.extend(_validate_selector_delta_citations(packet))
    issues.extend(_validate_consequential_controls(packet))
    issues.extend(_validate_execution_and_mutation_flags(packet))
    return issues


def assert_valid_surface_registry_approval_packet(packet: Mapping[str, Any]) -> None:
    """Raise SurfaceRegistryApprovalPacketError when a packet is unsafe."""

    issues = validate_surface_registry_approval_packet(packet)
    if issues:
        raise SurfaceRegistryApprovalPacketError(issues)


def load_surface_registry_approval_packet(path: str) -> dict[str, Any]:
    """Load a packet JSON file without resolving or writing any artifacts."""

    with open(path, "r", encoding="utf-8") as handle:
        loaded = json.load(handle)
    if not isinstance(loaded, dict):
        raise ValueError("approval packet JSON must contain an object")
    return loaded


def validate_surface_registry_approval_packet_json(path: str) -> list[ValidationIssue]:
    return validate_surface_registry_approval_packet(load_surface_registry_approval_packet(path))


def _scan_private_values(value: Any, path: str = "$", key_hint: str = "") -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if isinstance(value, Mapping):
        for raw_key, nested_value in value.items():
            key = str(raw_key)
            key_path = f"{path}.{key}"
            normalized = _normalize_key(key)
            if normalized in PRIVATE_VALUE_KEYS and nested_value not in REDACTED_VALUES:
                issues.append(ValidationIssue("raw_authenticated_value", key_path, "authenticated values must be omitted or redacted"))
            if normalized in PRIVATE_ARTIFACT_KEYS and nested_value not in REDACTED_VALUES:
                issues.append(ValidationIssue("private_session_artifact", key_path, "private session artifacts must not be included"))
            issues.extend(_scan_private_values(nested_value, key_path, normalized))
        return issues

    if isinstance(value, list):
        for index, item in enumerate(value):
            issues.extend(_scan_private_values(item, f"{path}[{index}]", key_hint))
        return issues

    if isinstance(value, str):
        lowered = value.lower()
        if _looks_like_local_private_path(value):
            issues.append(ValidationIssue("local_private_path", path, "local private filesystem paths are not allowed"))
        if _looks_like_artifact_path(lowered, key_hint):
            issues.append(ValidationIssue("browser_artifact_path", path, "screenshots, traces, HAR files, and stored browser state paths are not allowed"))
        if key_hint in PRIVATE_VALUE_KEYS and value.strip().lower() not in REDACTED_VALUES:
            issues.append(ValidationIssue("raw_authenticated_value", path, "authenticated values must be omitted or redacted"))
    return issues


def _validate_reviewer_signoffs(packet: Mapping[str, Any]) -> list[ValidationIssue]:
    signoffs = packet.get("reviewer_signoffs")
    if not isinstance(signoffs, list) or not signoffs:
        return [ValidationIssue("missing_reviewer_signoff", "$.reviewer_signoffs", "at least one reviewer signoff is required")]

    issues: list[ValidationIssue] = []
    for index, signoff in enumerate(signoffs):
        path = f"$.reviewer_signoffs[{index}]"
        if not isinstance(signoff, Mapping):
            issues.append(ValidationIssue("missing_reviewer_signoff", path, "reviewer signoff must be an object"))
            continue
        if not signoff.get("reviewer_id"):
            issues.append(ValidationIssue("missing_reviewer_signoff", f"{path}.reviewer_id", "reviewer_id is required"))
        if signoff.get("approved") is not True:
            issues.append(ValidationIssue("missing_reviewer_signoff", f"{path}.approved", "reviewer must explicitly approve the packet"))
        if not signoff.get("signed_at"):
            issues.append(ValidationIssue("missing_reviewer_signoff", f"{path}.signed_at", "signed_at is required"))
    return issues


def _validate_redaction_attestation(packet: Mapping[str, Any]) -> list[ValidationIssue]:
    attestation = packet.get("redaction_attestation")
    if not isinstance(attestation, Mapping):
        return [ValidationIssue("missing_redaction_attestation", "$.redaction_attestation", "redaction attestation is required")]
    if attestation.get("private_values_removed") is not True:
        return [ValidationIssue("missing_redaction_attestation", "$.redaction_attestation.private_values_removed", "private value removal must be attested")]
    if attestation.get("browser_artifacts_removed") is not True:
        return [ValidationIssue("missing_redaction_attestation", "$.redaction_attestation.browser_artifacts_removed", "browser artifact removal must be attested")]
    return []


def _validate_rollback_notes(packet: Mapping[str, Any]) -> list[ValidationIssue]:
    notes = packet.get("rollback_notes")
    if not isinstance(notes, str) or not notes.strip():
        return [ValidationIssue("missing_rollback_notes", "$.rollback_notes", "rollback notes are required")]
    return []


def _validate_selector_delta_citations(packet: Mapping[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    deltas = packet.get("selector_deltas", [])
    if deltas in (None, []):
        return issues
    if not isinstance(deltas, list):
        return [ValidationIssue("selector_delta_not_list", "$.selector_deltas", "selector_deltas must be a list")]
    for index, delta in enumerate(deltas):
        path = f"$.selector_deltas[{index}]"
        if not isinstance(delta, Mapping):
            issues.append(ValidationIssue("uncited_selector_delta_approval", path, "selector delta must be an object with source citations"))
            continue
        citations = delta.get("source_citations") or delta.get("citations")
        if not _non_empty_string_list(citations):
            issues.append(ValidationIssue("uncited_selector_delta_approval", path, "selector delta approvals require source citations"))
    return issues


def _validate_consequential_controls(packet: Mapping[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    controls = packet.get("controls", [])
    if controls in (None, []):
        return issues
    if not isinstance(controls, list):
        return [ValidationIssue("controls_not_list", "$.controls", "controls must be a list")]
    for index, control in enumerate(controls):
        path = f"$.controls[{index}]"
        if not isinstance(control, Mapping):
            continue
        enabled = control.get("enabled") is True
        action = str(control.get("action", control.get("name", ""))).lower()
        classification = str(control.get("classification", control.get("risk", ""))).lower()
        if enabled and (classification in {"consequential", "financial"} or any(term in action for term in CONSEQUENTIAL_CONTROL_TERMS)):
            issues.append(ValidationIssue("enabled_consequential_control", path, "consequential controls must not be enabled in approval packets"))
    return issues


def _validate_execution_and_mutation_flags(packet: Mapping[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if packet.get("live_browser_execution") is True:
        issues.append(ValidationIssue("live_browser_execution_claim", "$.live_browser_execution", "approval packets must be fixture-only and cannot claim live browser execution"))
    if packet.get("browser_execution_claim") in {"live", "executed", "authenticated_live"}:
        issues.append(ValidationIssue("live_browser_execution_claim", "$.browser_execution_claim", "live browser execution claims are not allowed"))
    if packet.get("surface_registry_mutation_enabled") is True:
        issues.append(ValidationIssue("active_surface_registry_mutation_flag", "$.surface_registry_mutation_enabled", "surface registry mutation must be disabled during review"))
    mutation = packet.get("mutation")
    if isinstance(mutation, Mapping) and mutation.get("enabled") is True:
        issues.append(ValidationIssue("active_surface_registry_mutation_flag", "$.mutation.enabled", "surface registry mutation must be disabled during review"))
    return issues


def _normalize_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", key.strip().lower()).strip("_")


def _looks_like_local_private_path(value: str) -> bool:
    stripped = value.strip()
    return any(pattern.search(stripped) for pattern in LOCAL_PRIVATE_PATH_PATTERNS)


def _looks_like_artifact_path(lowered_value: str, key_hint: str) -> bool:
    artifact_hint = key_hint in PRIVATE_ARTIFACT_KEYS or any(term in key_hint for term in ("screenshot", "trace", "har", "storage_state", "auth_state"))
    if artifact_hint:
        return True
    try:
        name = PurePosixPath(lowered_value).name or PureWindowsPath(lowered_value).name
    except ValueError:
        name = lowered_value
    return name.endswith(ARTIFACT_PATH_SUFFIXES) and any(term in lowered_value for term in ("screenshot", "trace", "har", "auth", "storage", "session"))


def _non_empty_string_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item.strip() for item in value)


def issue_codes(issues: Iterable[ValidationIssue]) -> set[str]:
    return {issue.code for issue in issues}
