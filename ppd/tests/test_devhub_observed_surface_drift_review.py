from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from ppd.devhub.observed_surface_drift_review import (
    REQUIRED_PACKET_TYPE,
    assert_valid_observed_surface_drift_review,
    build_observed_surface_drift_review_packet,
    load_json_packet,
    validate_observed_surface_drift_review,
)


FIXTURES = Path(__file__).parent / "fixtures"
PILOT_EVIDENCE = FIXTURES / "devhub" / "read_only_pilot_result_intake.json"
SURFACE_SNAPSHOTS = FIXTURES / "devhub_observed_surface_drift_review" / "synthetic_surface_registry_snapshots.json"
REVIEW_PACKET = FIXTURES / "devhub_observed_surface_drift_review" / "observed_surface_drift_review_packet.json"


def _pilot() -> dict[str, object]:
    return load_json_packet(PILOT_EVIDENCE)


def _snapshots() -> dict[str, object]:
    return load_json_packet(SURFACE_SNAPSHOTS)


def _packet() -> dict[str, object]:
    return load_json_packet(REVIEW_PACKET)


def test_fixture_first_review_packet_is_valid() -> None:
    packet = _packet()
    result = validate_observed_surface_drift_review(packet)
    assert packet["packet_type"] == REQUIRED_PACKET_TYPE
    assert packet["launches_devhub"] is False
    assert result.ok is True
    assert result.errors == ()


def test_builder_consumes_pilot_evidence_and_surface_snapshots_without_launching_devhub() -> None:
    packet = build_observed_surface_drift_review_packet(_pilot(), _snapshots())
    assert packet == _packet()
    assert packet["launches_devhub"] is False
    assert_valid_observed_surface_drift_review(packet)


def test_review_packet_keeps_only_redacted_headings_and_labels() -> None:
    packet = _packet()
    surfaces = packet["observed_surfaces"]
    assert isinstance(surfaces, list)
    for surface in surfaces:
        assert isinstance(surface, dict)
        assert set(surface) == {
            "surface_id",
            "route_pattern",
            "redacted_heading",
            "redacted_labels",
            "read_only_status_category",
            "selector_confidence_notes",
            "manual_handoff_prompts",
            "disabled_consequential_controls",
        }
        assert str(surface["redacted_heading"]).startswith("[REDACTED_HEADING:")
        labels = surface["redacted_labels"]
        assert isinstance(labels, list)
        assert all(str(label).startswith("[REDACTED_LABEL:") for label in labels)


@pytest.mark.parametrize(
    "forbidden_key",
    [
        "raw_dom",
        "screenshot_path",
        "trace_file",
        "har_file",
        "auth_state",
        "cookie_jar",
        "private_value",
        "credential_prompt",
        "automated_login",
        "automated_mfa",
        "automated_captcha",
        "automated_account_creation",
        "official_action_completed",
        "enabled_upload_controls",
        "enabled_submission_controls",
        "enabled_payment_controls",
        "enabled_scheduling_controls",
        "enabled_cancellation_controls",
        "enabled_certification_controls",
        "value",
    ],
)
def test_review_packet_rejects_private_session_and_action_fields(forbidden_key: str) -> None:
    packet = _packet()
    surfaces = packet["observed_surfaces"]
    assert isinstance(surfaces, list)
    first = surfaces[0]
    assert isinstance(first, dict)
    first[forbidden_key] = "unsafe"
    result = validate_observed_surface_drift_review(packet)
    assert result.ok is False
    assert any(forbidden_key in error for error in result.errors)


@pytest.mark.parametrize(
    "unsafe_text",
    [
        "screenshot saved for the reviewed page",
        "trace file retained for selector debugging",
        "HAR captured during observed drift review",
        "cookie copied from browser context",
        "auth state file reused",
        "private value was observed",
        "credential prompt asks for the password",
        "automated login completed",
        "MFA was completed by automation",
        "automated CAPTCHA solved",
        "automated account creation completed",
        "official action completed",
        "application was submitted",
        "enabled upload control",
        "payment button is enabled",
        "scheduling controls are enabled",
        "cancel control is enabled",
        "certification action enabled",
    ],
)
def test_review_packet_rejects_unsafe_text_claims(unsafe_text: str) -> None:
    packet = _packet()
    surfaces = packet["observed_surfaces"]
    assert isinstance(surfaces, list)
    first = surfaces[0]
    assert isinstance(first, dict)
    first["manual_handoff_prompts"] = [unsafe_text]
    result = validate_observed_surface_drift_review(packet)
    assert result.ok is False
    assert any("prohibited live/session/action content" in error for error in result.errors)


def test_review_packet_rejects_unredacted_heading_or_label_text() -> None:
    packet = _packet()
    surfaces = packet["observed_surfaces"]
    assert isinstance(surfaces, list)
    first = surfaces[0]
    assert isinstance(first, dict)
    first["redacted_heading"] = "My Permits for Jane Example"
    first["redacted_labels"] = ["Permit number 1234"]
    result = validate_observed_surface_drift_review(packet)
    assert result.ok is False
    assert any("redacted_heading must be a redacted token" in error for error in result.errors)
    assert any("redacted_labels[0] must be a redacted token" in error for error in result.errors)


def test_review_packet_requires_disabled_consequential_controls() -> None:
    packet = _packet()
    surfaces = packet["observed_surfaces"]
    assert isinstance(surfaces, list)
    first = surfaces[0]
    assert isinstance(first, dict)
    first["disabled_consequential_controls"] = ["submit_application"]
    result = validate_observed_surface_drift_review(packet)
    assert result.ok is False
    assert any("entries must start with disabled:" in error for error in result.errors)


def test_review_packet_rejects_selector_upgrade_without_evidence() -> None:
    packet = _packet()
    surfaces = packet["observed_surfaces"]
    assert isinstance(surfaces, list)
    first = surfaces[0]
    assert isinstance(first, dict)
    first["selector_confidence_notes"] = ["selector upgraded to high confidence"]
    result = validate_observed_surface_drift_review(packet)
    assert result.ok is False
    assert any("selector upgrade without evidence" in error for error in result.errors)


def test_review_packet_allows_selector_upgrade_with_explicit_evidence_reference() -> None:
    packet = _packet()
    surfaces = packet["observed_surfaces"]
    assert isinstance(surfaces, list)
    first = surfaces[0]
    assert isinstance(first, dict)
    first["selector_confidence_notes"] = ["selector upgraded after redacted landmark comparison evidence:fixture-selector-review-1"]
    result = validate_observed_surface_drift_review(packet)
    assert result.ok is True


def test_builder_rejects_pilot_evidence_that_claims_browser_artifacts() -> None:
    pilot = _pilot()
    pilot["screenshots_captured"] = True
    with pytest.raises(AssertionError, match="screenshots_captured must be false"):
        build_observed_surface_drift_review_packet(pilot, _snapshots())


def test_builder_rejects_surface_snapshots_that_launch_devhub() -> None:
    snapshots = deepcopy(_snapshots())
    snapshots["launches_devhub"] = True
    with pytest.raises(AssertionError, match="must not launch DevHub"):
        build_observed_surface_drift_review_packet(_pilot(), snapshots)
