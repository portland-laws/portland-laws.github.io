"""Deterministic validator for attended DevHub dry-run review packets.

The validator is intentionally side-effect free. It only accepts already-created
JSON transcript data and rejects records that imply browser automation, persisted
authentication state, screenshots, traces, HAR files, credentials, private
session artifacts, consequential controls, missing redaction attestations, or
claims that live authenticated evidence was captured.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


class DryRunTranscriptError(ValueError):
    """Raised when a DevHub dry-run transcript violates the safe contract."""


@dataclass(frozen=True)
class DryRunValidationResult:
    """Validated transcript summary safe to include in deterministic tests."""

    event_count: int
    surfaces: tuple[str, ...]
    warnings: tuple[str, ...] = ()


FORBIDDEN_ARTIFACT_KINDS = {
    "auth_state",
    "browser_context",
    "cookie_jar",
    "download",
    "har",
    "raw_crawl_output",
    "screenshot",
    "session_file",
    "storage_state",
    "trace",
    "video",
}

FORBIDDEN_EVENT_TYPES = {
    "automated_login",
    "browser_action",
    "browser_launch",
    "captcha",
    "captcha_automation",
    "certify",
    "click",
    "credential_prompt",
    "download",
    "enter_credentials",
    "fill",
    "launch_playwright",
    "login",
    "login_automation",
    "mfa",
    "mfa_automation",
    "payment",
    "press",
    "prompt_for_credentials",
    "save_auth_state",
    "schedule_inspection",
    "screenshot",
    "select_option",
    "solve_captcha",
    "submit",
    "trace",
    "upload",
}

FORBIDDEN_FIELD_NAMES = {
    "access_token",
    "auth_state_path",
    "captcha_solution",
    "cookie",
    "cookies",
    "credential",
    "credential_prompt",
    "credentials",
    "download_path",
    "field_value",
    "har_path",
    "local_private_path",
    "mfa_code",
    "password",
    "payment_details",
    "private_field_value",
    "private_file_path",
    "raw_field_value",
    "raw_page_html",
    "screenshot_path",
    "session_path",
    "storage_state_path",
    "trace_path",
    "video_path",
}

FORBIDDEN_CONTROL_CLASSES = {
    "certification",
    "consequential",
    "consequential_official",
    "financial",
    "official_submission",
    "payment",
    "unsupported_manual_handoff",
    "upload_to_official_record",
}

CONSEQUENTIAL_TERMS = (
    "cancel",
    "certif",
    "pay",
    "payment",
    "purchase",
    "schedule",
    "submit",
    "upload",
    "withdraw",
)

REQUIRED_REDACTION_TRUE_FIELDS = (
    "automation_login_mfa_captcha_absent",
    "credential_prompts_absent",
    "credentials_absent",
    "cookies_absent",
    "auth_state_absent",
    "screenshots_absent",
    "traces_absent",
    "har_absent",
    "private_field_values_redacted",
    "consequential_controls_absent",
)

ALLOWED_TOP_LEVEL_FIELDS = {
    "artifacts",
    "auth_state_saved",
    "authenticated_evidence_captured",
    "browser_launched",
    "created_at",
    "events",
    "notes",
    "redaction_attestation",
    "review_controls",
    "session_mode",
    "transcript_version",
}

REQUIRED_VERSION = "devhub-attended-dry-run-v1"
REQUIRED_SESSION_MODE = "attended_dry_run"


def load_transcript(path: str | Path) -> Mapping[str, Any]:
    """Load a transcript JSON file without touching browser/session state."""

    transcript_path = Path(path)
    with transcript_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise DryRunTranscriptError("transcript must be a JSON object")
    return data


def validate_transcript_file(path: str | Path) -> DryRunValidationResult:
    """Load and validate an attended DevHub dry-run transcript fixture."""

    return validate_transcript(load_transcript(path))


def validate_transcript(transcript: Mapping[str, Any]) -> DryRunValidationResult:
    """Validate a side-effect-free attended DevHub dry-run transcript."""

    _validate_top_level_shape(transcript)
    _validate_no_forbidden_fields(transcript, path="transcript")
    _validate_redaction_attestation(transcript.get("redaction_attestation"))

    artifacts = transcript.get("artifacts", [])
    events = transcript.get("events", [])
    review_controls = transcript.get("review_controls", [])
    assert isinstance(artifacts, list)
    assert isinstance(events, list)
    assert isinstance(review_controls, list)

    _validate_artifacts(artifacts)
    _validate_review_controls(review_controls)
    surfaces = _validate_events(events)

    warnings: list[str] = []
    if not artifacts:
        warnings.append("no artifacts recorded")

    return DryRunValidationResult(
        event_count=len(events),
        surfaces=tuple(sorted(surfaces)),
        warnings=tuple(warnings),
    )


def _validate_top_level_shape(transcript: Mapping[str, Any]) -> None:
    unknown = sorted(set(transcript) - ALLOWED_TOP_LEVEL_FIELDS)
    if unknown:
        raise DryRunTranscriptError(f"unknown top-level field(s): {', '.join(unknown)}")

    if transcript.get("transcript_version") != REQUIRED_VERSION:
        raise DryRunTranscriptError("transcript_version must be devhub-attended-dry-run-v1")
    if transcript.get("session_mode") != REQUIRED_SESSION_MODE:
        raise DryRunTranscriptError("session_mode must be attended_dry_run")
    if transcript.get("browser_launched") is not False:
        raise DryRunTranscriptError("browser_launched must be false for dry-run validation")
    if transcript.get("auth_state_saved") is not False:
        raise DryRunTranscriptError("auth_state_saved must be false for dry-run validation")
    if transcript.get("authenticated_evidence_captured") is not False:
        raise DryRunTranscriptError("authenticated_evidence_captured must be false for dry-run validation")

    events = transcript.get("events")
    if not isinstance(events, list) or not events:
        raise DryRunTranscriptError("events must be a non-empty array")

    artifacts = transcript.get("artifacts", [])
    if not isinstance(artifacts, list):
        raise DryRunTranscriptError("artifacts must be an array when present")

    review_controls = transcript.get("review_controls", [])
    if not isinstance(review_controls, list):
        raise DryRunTranscriptError("review_controls must be an array when present")

    if not isinstance(transcript.get("redaction_attestation"), Mapping):
        raise DryRunTranscriptError("redaction_attestation must be present")


def _validate_redaction_attestation(attestation: Any) -> None:
    if not isinstance(attestation, Mapping):
        raise DryRunTranscriptError("redaction_attestation must be present")

    if attestation.get("attested") is not True:
        raise DryRunTranscriptError("redaction_attestation.attested must be true")
    if attestation.get("live_authenticated_evidence_captured") is not False:
        raise DryRunTranscriptError("redaction_attestation must deny live authenticated evidence capture")

    for field in REQUIRED_REDACTION_TRUE_FIELDS:
        if attestation.get(field) is not True:
            raise DryRunTranscriptError(f"redaction_attestation.{field} must be true")


def _validate_artifacts(artifacts: Sequence[Any]) -> None:
    for index, artifact in enumerate(artifacts):
        if not isinstance(artifact, Mapping):
            raise DryRunTranscriptError(f"artifact {index} must be an object")
        kind = _normal_text(artifact.get("kind"))
        if kind in FORBIDDEN_ARTIFACT_KINDS:
            raise DryRunTranscriptError(f"forbidden artifact kind: {kind}")
        if artifact.get("persisted") is True:
            raise DryRunTranscriptError(f"artifact {index} must not be persisted")


def _validate_review_controls(review_controls: Sequence[Any]) -> None:
    for index, control in enumerate(review_controls):
        if not isinstance(control, Mapping):
            raise DryRunTranscriptError(f"review control {index} must be an object")
        classification = _normal_text(
            control.get("classification")
            or control.get("action_class")
            or control.get("control_class")
            or control.get("kind")
        )
        if classification in FORBIDDEN_CONTROL_CLASSES:
            raise DryRunTranscriptError(f"forbidden consequential control in review_controls[{index}]")
        if _looks_consequential(control):
            raise DryRunTranscriptError(f"forbidden consequential control in review_controls[{index}]")


def _validate_events(events: Sequence[Any]) -> set[str]:
    surfaces: set[str] = set()
    for index, event in enumerate(events):
        if not isinstance(event, Mapping):
            raise DryRunTranscriptError(f"event {index} must be an object")

        event_type = _normal_text(event.get("event_type"))
        if not event_type:
            raise DryRunTranscriptError(f"event {index} missing event_type")
        if event_type in FORBIDDEN_EVENT_TYPES:
            raise DryRunTranscriptError(f"forbidden browser or consequential event: {event_type}")
        if _event_claims_forbidden_automation(event):
            raise DryRunTranscriptError(f"forbidden browser or consequential event: {event_type}")

        if event.get("performed_by") not in {"human", "validator", "plan"}:
            raise DryRunTranscriptError(f"event {index} performed_by must be human, validator, or plan")
        if event.get("requires_attendance") is not True:
            raise DryRunTranscriptError(f"event {index} must require attendance")
        if event.get("browser_action") is not False:
            raise DryRunTranscriptError(f"event {index} browser_action must be false")

        surface = _normal_text(event.get("surface"))
        if not surface:
            raise DryRunTranscriptError(f"event {index} missing surface")
        surfaces.add(surface)

    return surfaces


def _validate_no_forbidden_fields(value: Any, path: str) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str):
                raise DryRunTranscriptError(f"{path} contains a non-string field name")
            normalized = _normal_text(key)
            if normalized in FORBIDDEN_FIELD_NAMES:
                raise DryRunTranscriptError(f"forbidden private field at {path}.{key}")
            _validate_no_forbidden_fields(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _validate_no_forbidden_fields(child, f"{path}[{index}]")
    elif isinstance(value, str):
        _validate_no_forbidden_claim(value, path)


def _event_claims_forbidden_automation(event: Mapping[str, Any]) -> bool:
    for key in ("automation_target", "action_class", "control_class", "classification"):
        normalized = _normal_text(event.get(key))
        if normalized in FORBIDDEN_EVENT_TYPES or normalized in FORBIDDEN_CONTROL_CLASSES:
            return True
    return _looks_consequential(event)


def _looks_consequential(value: Mapping[str, Any]) -> bool:
    text_parts: list[str] = []
    for key in ("control_id", "event_type", "label", "description", "name"):
        item = value.get(key)
        if isinstance(item, str):
            text_parts.append(_normal_text(item))
    text = " ".join(text_parts)
    return any(term in text for term in CONSEQUENTIAL_TERMS)


def _validate_no_forbidden_claim(value: str, path: str) -> None:
    normalized = _normal_text(value)
    forbidden_claims = (
        "captured_live_authenticated_evidence",
        "live_authenticated_evidence_captured",
        "live_authenticated_evidence_was_captured",
    )
    if any(claim in normalized for claim in forbidden_claims):
        raise DryRunTranscriptError(f"forbidden live authenticated evidence claim at {path}")


def _normal_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip().lower().replace("-", "_").replace(" ", "_")
