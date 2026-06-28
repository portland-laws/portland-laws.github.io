"""Validation for correction-upload boundary packets.

Correction uploads are consequential DevHub workflows. Boundary packets for this
stage may describe cited public requirements and safe attended next steps, but
must not claim official completion, carry private artifacts, or direct an agent
toward irreversible actions.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath, PureWindowsPath
from typing import Any, Mapping, Sequence


PRIVATE_CONTENT_KEYS = {
    "document_content",
    "document_contents",
    "file_content",
    "file_contents",
    "private_document_content",
    "private_document_contents",
    "raw_document",
    "raw_documents",
    "upload_bytes",
    "upload_content",
}

BROWSER_STATE_KEYS = {
    "browser_state",
    "storage_state",
    "cookies",
    "cookie",
    "local_storage",
    "session_storage",
    "indexed_db",
    "auth_state",
    "session_state",
    "playwright_state",
}

CAPTURE_ARTIFACT_KEYS = {
    "screenshot",
    "screenshots",
    "screenshot_path",
    "screenshot_paths",
    "trace",
    "traces",
    "trace_path",
    "trace_paths",
    "har",
    "har_path",
    "har_paths",
    "network_har",
}

OFFICIAL_COMPLETION_PHRASES = (
    "uploaded to the official record",
    "upload completed",
    "official upload complete",
    "correction upload complete",
    "corrections uploaded",
    "submitted corrections",
    "submission complete",
    "officially submitted",
    "certified and submitted",
    "i certify",
    "certification complete",
    "acknowledgement certified",
)

UNSAFE_ACTION_PHRASES = (
    "click submit",
    "select submit",
    "press submit",
    "submit corrections",
    "submit the corrections",
    "final submit",
    "complete upload",
    "finish upload",
    "confirm upload",
    "certify",
    "accept acknowledgement",
    "acknowledge and submit",
    "pay fee",
    "submit payment",
    "schedule inspection",
    "cancel permit",
    "withdraw permit",
)

SAFE_NEXT_ACTION_PHRASES = (
    "review",
    "ask user",
    "request user",
    "manual handoff",
    "attended handoff",
    "collect citation",
    "cite source",
    "stage draft",
    "prepare draft",
    "validate",
    "compare",
)

PRIVATE_PATH_MARKERS = (
    "/home/",
    "/users/",
    "/var/folders/",
    "/tmp/",
    "/private/",
    "c:/users/",
    "c:\\users\\",
    "\\users\\",
)


@dataclass(frozen=True)
class BoundaryViolation:
    """A deterministic validation failure for a correction-upload packet."""

    code: str
    message: str
    path: str


@dataclass(frozen=True)
class BoundaryValidationResult:
    """Validation result for a correction-upload boundary packet."""

    ok: bool
    violations: tuple[BoundaryViolation, ...]


def validate_correction_upload_boundary_packet(
    packet: Mapping[str, Any],
) -> BoundaryValidationResult:
    """Validate that a correction-upload packet is commit-safe and non-final.

    The packet is expected to be plain JSON-like data. This function deliberately
    treats unknown fields conservatively when they contain private artifacts,
    browser state, official completion claims, or unsafe next actions.
    """

    violations: list[BoundaryViolation] = []
    _walk_packet(packet, "$", violations)
    _validate_correction_requirements(packet, violations)
    _validate_next_actions(packet, violations)
    return BoundaryValidationResult(ok=not violations, violations=tuple(violations))


def assert_correction_upload_boundary_packet(packet: Mapping[str, Any]) -> None:
    """Raise ValueError if a correction-upload packet violates boundaries."""

    result = validate_correction_upload_boundary_packet(packet)
    if result.ok:
        return
    details = "; ".join(
        f"{violation.code} at {violation.path}: {violation.message}"
        for violation in result.violations
    )
    raise ValueError(details)


def _walk_packet(value: Any, path: str, violations: list[BoundaryViolation]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            key_lower = key_text.lower()
            child_path = f"{path}.{key_text}"
            _validate_key(key_lower, child_path, violations)
            _walk_packet(child, child_path, violations)
        return

    if isinstance(value, list | tuple):
        for index, child in enumerate(value):
            _walk_packet(child, f"{path}[{index}]", violations)
        return

    if isinstance(value, str):
        _validate_text(value, path, violations)


def _validate_key(key_lower: str, path: str, violations: list[BoundaryViolation]) -> None:
    if key_lower in PRIVATE_CONTENT_KEYS:
        violations.append(
            BoundaryViolation(
                "private_document_content",
                "private document contents are not allowed in correction-upload boundary packets",
                path,
            )
        )
    if key_lower in BROWSER_STATE_KEYS:
        violations.append(
            BoundaryViolation(
                "browser_state",
                "browser/session state is not allowed in correction-upload boundary packets",
                path,
            )
        )
    if key_lower in CAPTURE_ARTIFACT_KEYS:
        violations.append(
            BoundaryViolation(
                "browser_capture_artifact",
                "screenshots, traces, and HAR artifacts are not allowed in correction-upload boundary packets",
                path,
            )
        )


def _validate_text(text: str, path: str, violations: list[BoundaryViolation]) -> None:
    normalized = " ".join(text.lower().split())
    for phrase in OFFICIAL_COMPLETION_PHRASES:
        if phrase in normalized:
            violations.append(
                BoundaryViolation(
                    "official_completion_claim",
                    "packet must not claim official upload completion, certification, or submission",
                    path,
                )
            )
            break

    if _looks_like_private_path(text):
        violations.append(
            BoundaryViolation(
                "local_private_path",
                "local private paths are not allowed in correction-upload boundary packets",
                path,
            )
        )


def _looks_like_private_path(text: str) -> bool:
    normalized = text.strip().lower()
    if any(marker in normalized for marker in PRIVATE_PATH_MARKERS):
        return True
    if PurePosixPath(text).is_absolute() and not normalized.startswith("/ppd/tests/fixtures/"):
        return True
    return PureWindowsPath(text).drive != ""


def _validate_correction_requirements(
    packet: Mapping[str, Any], violations: list[BoundaryViolation]
) -> None:
    requirements = packet.get("correction_requirements", ())
    if requirements is None:
        return
    if not isinstance(requirements, Sequence) or isinstance(requirements, str | bytes):
        violations.append(
            BoundaryViolation(
                "invalid_correction_requirements",
                "correction_requirements must be a list of cited requirement objects",
                "$.correction_requirements",
            )
        )
        return

    for index, requirement in enumerate(requirements):
        path = f"$.correction_requirements[{index}]"
        if not isinstance(requirement, Mapping):
            violations.append(
                BoundaryViolation(
                    "invalid_correction_requirement",
                    "each correction requirement must be an object with source evidence",
                    path,
                )
            )
            continue
        evidence = requirement.get("source_evidence_ids") or requirement.get("citations")
        if not _has_nonempty_strings(evidence):
            violations.append(
                BoundaryViolation(
                    "uncited_correction_requirement",
                    "correction requirements must include at least one source evidence id or citation",
                    path,
                )
            )


def _validate_next_actions(
    packet: Mapping[str, Any], violations: list[BoundaryViolation]
) -> None:
    next_actions = packet.get("next_actions") or packet.get("next_safe_actions") or ()
    if isinstance(next_actions, str):
        candidates: Sequence[Any] = (next_actions,)
    elif isinstance(next_actions, Sequence):
        candidates = next_actions
    else:
        violations.append(
            BoundaryViolation(
                "invalid_next_actions",
                "next actions must be a string or list of strings/objects",
                "$.next_actions",
            )
        )
        return

    for index, action in enumerate(candidates):
        path = f"$.next_actions[{index}]"
        text = _action_text(action)
        if not text:
            continue
        normalized = " ".join(text.lower().split())
        if any(phrase in normalized for phrase in UNSAFE_ACTION_PHRASES):
            violations.append(
                BoundaryViolation(
                    "unsafe_next_action",
                    "next actions must not direct upload, submission, certification, payment, scheduling, cancellation, or withdrawal",
                    path,
                )
            )
            continue
        if not any(phrase in normalized for phrase in SAFE_NEXT_ACTION_PHRASES):
            violations.append(
                BoundaryViolation(
                    "unbounded_next_action",
                    "next actions must be limited to review, citation, validation, draft staging, or attended handoff",
                    path,
                )
            )


def _action_text(action: Any) -> str:
    if isinstance(action, str):
        return action
    if isinstance(action, Mapping):
        pieces = [
            str(action.get(name, ""))
            for name in ("label", "action", "description", "instruction")
        ]
        return " ".join(piece for piece in pieces if piece)
    return ""


def _has_nonempty_strings(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Sequence) and not isinstance(value, bytes):
        return any(isinstance(item, str) and bool(item.strip()) for item in value)
    return False
