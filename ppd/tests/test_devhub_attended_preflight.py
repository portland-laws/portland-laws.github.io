from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from ppd.devhub.attended_preflight import (
    load_attended_preflight_fixture,
    validate_attended_preflight_fixture,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub" / "attended_preflight_valid.json"


def _valid_fixture() -> dict:
    return load_attended_preflight_fixture(FIXTURE_PATH)


def test_fixture_only_attended_preflight_passes_without_browser_launch() -> None:
    result = validate_attended_preflight_fixture(_valid_fixture())

    assert result.preflight_passed is True
    assert result.browser_action_plan_allowed is True
    assert result.browser_launch_allowed is False
    assert result.issues == ()
    assert "devhub.dashboard.permit_requests" in result.matched_surfaces
    assert "devhub.application.review_checkpoint" in result.matched_surfaces
    assert "automated_login" in result.refused_action_policies
    assert "authenticated_session_capture" in result.refused_action_policies


def test_manual_login_handoff_is_required_before_plan_is_allowed() -> None:
    fixture = _valid_fixture()
    fixture["manual_login_handoff"] = {
        "required": False,
        "requires_user_attendance": False,
        "actor": "automation",
        "credential_storage": "allowed",
        "credential_prompt_capture": True,
        "session_state_storage": "allowed",
        "cookie_storage": "allowed",
        "automated_login": True,
        "account_creation_allowed": True,
    }

    result = validate_attended_preflight_fixture(fixture)

    assert result.preflight_passed is False
    assert result.browser_action_plan_allowed is False
    assert any("manual login handoff" in issue for issue in result.issues)
    assert any("credential storage" in issue for issue in result.issues)
    assert any("account creation" in issue for issue in result.issues)
    assert any("automated login" in issue for issue in result.issues)


def test_pilot_preflight_requires_all_sensitive_refusal_policies() -> None:
    fixture = _valid_fixture()
    fixture["refused_action_policies"] = {
        "mfa": {
            "decision": "handoff",
            "automate": True,
            "requires_user_handoff": False,
        }
    }

    result = validate_attended_preflight_fixture(fixture)

    assert result.preflight_passed is False
    assert result.browser_action_plan_allowed is False
    assert any("mfa policy must refuse automation" in issue for issue in result.issues)
    assert any("captcha policy must refuse automation" in issue for issue in result.issues)
    assert any("automated_login policy must refuse automation" in issue for issue in result.issues)
    assert any("auth_state policy must refuse automation" in issue for issue in result.issues)
    assert any("authenticated_session_capture policy must refuse automation" in issue for issue in result.issues)


def test_pilot_safety_assertions_reject_sensitive_capture_claims() -> None:
    fixture = _valid_fixture()
    fixture["pilot_safety_assertions"]["cookie_capture"] = True
    fixture["pilot_safety_assertions"].pop("har_capture")

    result = validate_attended_preflight_fixture(fixture)

    assert result.preflight_passed is False
    assert any("cookie_capture must be explicitly false" in issue for issue in result.issues)
    assert any("har_capture must be explicitly false" in issue for issue in result.issues)


def test_packet_text_rejects_automated_login_and_captured_session_claims() -> None:
    fixture = _valid_fixture()
    fixture["unsafe_notes"] = [
        "The login was automated for the pilot.",
        "The authenticated session was captured for reuse.",
    ]

    result = validate_attended_preflight_fixture(fixture)

    assert result.preflight_passed is False
    assert any("automated login is prohibited" in issue for issue in result.issues)
    assert any("authenticated session was captured" in issue for issue in result.issues)


def test_packet_rejects_private_artifact_and_private_value_claims() -> None:
    fixture = _valid_fixture()
    fixture["artifact_claims"] = {
        "cookies_captured": True,
        "auth_state_capture": True,
        "screenshot_capture": True,
        "trace_capture": True,
        "har_capture": True,
        "private_field_value_capture": True,
        "credential_prompt_capture": True,
    }

    result = validate_attended_preflight_fixture(fixture)

    assert result.preflight_passed is False
    assert any("cookie capture is prohibited" in issue for issue in result.issues)
    assert any("auth state capture is prohibited" in issue for issue in result.issues)
    assert any("screenshot capture is prohibited" in issue for issue in result.issues)
    assert any("trace capture is prohibited" in issue for issue in result.issues)
    assert any("HAR data capture is prohibited" in issue for issue in result.issues)
    assert any("private field values are prohibited" in issue for issue in result.issues)
    assert any("credential prompts are prohibited" in issue for issue in result.issues)


def test_surface_map_matching_is_required_for_planned_actions() -> None:
    fixture = _valid_fixture()
    fixture["candidate_browser_action_plan"]["actions"][0]["surface_id"] = "devhub.unknown.surface"

    result = validate_attended_preflight_fixture(fixture)

    assert result.preflight_passed is False
    assert result.browser_action_plan_allowed is False
    assert any("must match a known surface" in issue for issue in result.issues)


def test_selector_confidence_thresholds_block_low_confidence_surfaces_and_actions() -> None:
    fixture = _valid_fixture()
    fixture["surface_map"][0]["selector_confidence"] = 0.84
    fixture["candidate_browser_action_plan"]["actions"][1]["selector_confidence"] = 0.8

    result = validate_attended_preflight_fixture(fixture)

    assert result.preflight_passed is False
    assert result.browser_action_plan_allowed is False
    assert any("surface 'devhub.dashboard.permit_requests' selector confidence below threshold" in issue for issue in result.issues)
    assert any("planned action 'fixture-review-continue-button' selector confidence below threshold" in issue for issue in result.issues)


def test_exact_confirmation_checkpoint_must_exist_before_action_plan() -> None:
    fixture = _valid_fixture()
    fixture["exact_confirmation_checkpoints"] = []

    result = validate_attended_preflight_fixture(fixture)

    assert result.preflight_passed is False
    assert result.browser_action_plan_allowed is False
    assert any("at least one exact confirmation checkpoint is required" in issue for issue in result.issues)
    assert any("must reference an exact confirmation checkpoint" in issue for issue in result.issues)


def test_browser_launch_remains_blocked_even_if_fixture_requests_it() -> None:
    fixture = deepcopy(_valid_fixture())
    fixture["candidate_browser_action_plan"]["browser_launch_allowed"] = True

    result = validate_attended_preflight_fixture(fixture)

    assert result.preflight_passed is False
    assert result.browser_action_plan_allowed is False
    assert result.browser_launch_allowed is False
    assert any("must not allow browser launch" in issue for issue in result.issues)


def test_consequential_controls_are_rejected_even_inside_read_only_action() -> None:
    fixture = _valid_fixture()
    fixture["candidate_browser_action_plan"]["actions"][0]["controls"] = [
        {"kind": "submit", "automates": True}
    ]

    result = validate_attended_preflight_fixture(fixture)

    assert result.preflight_passed is False
    assert result.browser_action_plan_allowed is False
    assert any("must not automate consequential control 'submit'" in issue for issue in result.issues)
