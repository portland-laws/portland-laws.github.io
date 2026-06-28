from pathlib import Path

import pytest

from ppd.devhub.dry_run_transcript import (
    DryRunTranscriptError,
    validate_transcript,
    validate_transcript_file,
)


FIXTURES = Path(__file__).parent / "fixtures" / "devhub_dry_run"


def _valid_transcript() -> dict:
    return {
        "transcript_version": "devhub-attended-dry-run-v1",
        "session_mode": "attended_dry_run",
        "created_at": "2026-05-14T00:00:00Z",
        "browser_launched": False,
        "auth_state_saved": False,
        "authenticated_evidence_captured": False,
        "artifacts": [],
        "review_controls": [],
        "redaction_attestation": {
            "attested": True,
            "automation_login_mfa_captcha_absent": True,
            "credential_prompts_absent": True,
            "credentials_absent": True,
            "cookies_absent": True,
            "auth_state_absent": True,
            "screenshots_absent": True,
            "traces_absent": True,
            "har_absent": True,
            "private_field_values_redacted": True,
            "consequential_controls_absent": True,
            "live_authenticated_evidence_captured": False,
        },
        "events": [
            {
                "event_type": "manual_handoff_plan",
                "performed_by": "plan",
                "surface": "devhub_public",
                "requires_attendance": True,
                "browser_action": False,
                "description": "Human opens DevHub and completes any login, MFA, or CAPTCHA prompts outside the validator.",
            },
            {
                "event_type": "attended_preflight_check",
                "performed_by": "validator",
                "surface": "devhub_authenticated_home",
                "requires_attendance": True,
                "browser_action": False,
                "description": "Validator checks only the committed transcript shape and does not launch a browser.",
            },
        ],
    }


def test_valid_attended_dry_run_transcript_passes() -> None:
    result = validate_transcript_file(FIXTURES / "valid_attended_transcript.json")

    assert result.event_count == 2
    assert result.surfaces == ("devhub_authenticated_home", "devhub_public")
    assert result.warnings == ("no artifacts recorded",)


def test_rejects_browser_actions() -> None:
    with pytest.raises(DryRunTranscriptError, match="forbidden browser or consequential event"):
        validate_transcript_file(FIXTURES / "invalid_browser_action_transcript.json")


def test_rejects_screenshots_and_persisted_artifacts() -> None:
    with pytest.raises(DryRunTranscriptError, match="forbidden artifact kind"):
        validate_transcript_file(FIXTURES / "invalid_artifact_transcript.json")


def test_rejects_saved_auth_state_even_without_path() -> None:
    transcript = _valid_transcript()
    transcript["auth_state_saved"] = True

    with pytest.raises(DryRunTranscriptError, match="auth_state_saved must be false"):
        validate_transcript(transcript)


def test_rejects_private_fields_anywhere_in_transcript() -> None:
    transcript = _valid_transcript()
    transcript["events"][0]["credentials"] = {"username": "redacted"}

    with pytest.raises(DryRunTranscriptError, match="forbidden private field"):
        validate_transcript(transcript)


def test_rejects_playwright_launch_markers() -> None:
    transcript = _valid_transcript()
    transcript["browser_launched"] = True

    with pytest.raises(DryRunTranscriptError, match="browser_launched must be false"):
        validate_transcript(transcript)


def test_rejects_missing_redaction_attestation() -> None:
    transcript = _valid_transcript()
    del transcript["redaction_attestation"]

    with pytest.raises(DryRunTranscriptError, match="redaction_attestation must be present"):
        validate_transcript(transcript)


def test_rejects_incomplete_redaction_attestation() -> None:
    transcript = _valid_transcript()
    transcript["redaction_attestation"]["cookies_absent"] = False

    with pytest.raises(DryRunTranscriptError, match="redaction_attestation.cookies_absent must be true"):
        validate_transcript(transcript)


def test_rejects_automated_login_mfa_captcha_and_credential_prompts() -> None:
    for event_type in ("automated_login", "mfa_automation", "captcha_automation", "credential_prompt"):
        transcript = _valid_transcript()
        transcript["events"][0]["event_type"] = event_type

        with pytest.raises(DryRunTranscriptError, match="forbidden browser or consequential event"):
            validate_transcript(transcript)


def test_rejects_cookies_auth_state_screenshots_traces_and_har_fields() -> None:
    for field_name in ("cookies", "auth_state_path", "screenshot_path", "trace_path", "har_path"):
        transcript = _valid_transcript()
        transcript["events"][0][field_name] = "redacted"

        with pytest.raises(DryRunTranscriptError, match="forbidden private field"):
            validate_transcript(transcript)


def test_rejects_private_field_values() -> None:
    transcript = _valid_transcript()
    transcript["events"][0]["field_value"] = "123 private street"

    with pytest.raises(DryRunTranscriptError, match="forbidden private field"):
        validate_transcript(transcript)


def test_rejects_consequential_review_controls() -> None:
    transcript = _valid_transcript()
    transcript["review_controls"] = [
        {
            "control_id": "submit_application",
            "classification": "consequential_official",
            "label": "Submit application",
        }
    ]

    with pytest.raises(DryRunTranscriptError, match="forbidden consequential control"):
        validate_transcript(transcript)


def test_rejects_live_authenticated_evidence_claims() -> None:
    transcript = _valid_transcript()
    transcript["authenticated_evidence_captured"] = True

    with pytest.raises(DryRunTranscriptError, match="authenticated_evidence_captured must be false"):
        validate_transcript(transcript)

    transcript = _valid_transcript()
    transcript["redaction_attestation"]["live_authenticated_evidence_captured"] = True

    with pytest.raises(DryRunTranscriptError, match="must deny live authenticated evidence capture"):
        validate_transcript(transcript)

    transcript = _valid_transcript()
    transcript["notes"] = ["live authenticated evidence was captured"]

    with pytest.raises(DryRunTranscriptError, match="forbidden live authenticated evidence claim"):
        validate_transcript(transcript)
