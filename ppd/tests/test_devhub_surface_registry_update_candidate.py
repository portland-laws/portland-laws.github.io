from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from ppd.devhub.surface_registry_update_candidate import (
    REQUIRED_PACKET_TYPE,
    assert_valid_surface_registry_update_candidate_packet,
    build_surface_registry_update_candidate_packet,
    load_json_packet,
    validate_surface_registry_update_candidate_packet,
)


FIXTURES = Path(__file__).parent / "fixtures"
DRIFT_REVIEW = FIXTURES / "devhub_observed_surface_drift_review" / "observed_surface_drift_review_packet.json"
READINESS_RECONCILIATION = FIXTURES / "devhub" / "read_only_pilot_reconciliation_packet.json"
CANDIDATE_PACKET = FIXTURES / "devhub_surface_registry_update_candidate" / "surface_registry_update_candidate_packet.json"


def _drift_review() -> dict[str, object]:
    return load_json_packet(DRIFT_REVIEW)


def _readiness_reconciliation() -> dict[str, object]:
    return load_json_packet(READINESS_RECONCILIATION)


def _candidate_packet() -> dict[str, object]:
    return load_json_packet(CANDIDATE_PACKET)


def _mutated_candidate_packet(field: str, value: object) -> dict[str, object]:
    packet = deepcopy(_candidate_packet())
    candidates = packet["registry_update_candidates"]
    assert isinstance(candidates, list)
    first = candidates[0]
    assert isinstance(first, dict)
    first[field] = value
    return packet


def test_surface_registry_update_candidate_fixture_is_valid() -> None:
    packet = _candidate_packet()
    errors = validate_surface_registry_update_candidate_packet(packet)
    assert packet["packet_type"] == REQUIRED_PACKET_TYPE
    assert packet["launches_devhub"] is False
    assert packet["stores_browser_artifacts"] is False
    assert errors == ()
    assert_valid_surface_registry_update_candidate_packet(packet)


def test_builder_consumes_drift_review_and_readiness_reconciliation_without_launching_devhub() -> None:
    packet = build_surface_registry_update_candidate_packet(_drift_review(), _readiness_reconciliation())
    assert packet == _candidate_packet()
    assert packet["source_packets"]["observed_surface_drift_review"]["consumed"] is True
    assert packet["source_packets"]["read_only_pilot_readiness_reconciliation"]["consumed"] is True
    assert packet["launches_devhub"] is False
    assert packet["launches_playwright"] is False
    assert packet["stores_browser_artifacts"] is False


def test_candidates_record_only_redacted_surface_metadata_and_disabled_controls() -> None:
    packet = _candidate_packet()
    candidates = packet["registry_update_candidates"]
    assert isinstance(candidates, list)
    for candidate in candidates:
        assert isinstance(candidate, dict)
        assert str(candidate["route_pattern"]).startswith("/")
        assert str(candidate["redacted_heading"]).startswith("[REDACTED_HEADING:")
        labels = candidate["redacted_labels"]
        assert isinstance(labels, list)
        assert all(str(label).startswith("[REDACTED_LABEL:") for label in labels)
        delta = candidate["selector_confidence_delta"]
        assert isinstance(delta, dict)
        assert delta["upgrade_requested"] is False
        assert delta["proposed_confidence"] == "attended_review_required"
        controls = candidate["disabled_consequential_controls"]
        assert isinstance(controls, list)
        assert all(str(control).startswith("disabled:") for control in controls)


def test_candidate_rejects_selector_confidence_upgrade_request() -> None:
    packet = _candidate_packet()
    candidates = packet["registry_update_candidates"]
    assert isinstance(candidates, list)
    first = candidates[0]
    assert isinstance(first, dict)
    delta = first["selector_confidence_delta"]
    assert isinstance(delta, dict)
    delta["upgrade_requested"] = True
    errors = validate_surface_registry_update_candidate_packet(packet)
    assert any("upgrade_requested must be false" in error for error in errors)


def test_candidate_rejects_browser_artifacts_and_auth_state() -> None:
    unsafe_fields = {
        "screenshots": ["/tmp/devhub.png"],
        "trace_path": "/tmp/trace.zip",
        "har_file": "/tmp/devhub.har",
        "cookies": [{"name": "session", "value": "secret"}],
        "auth_state": {"storage": "present"},
    }
    for field, value in unsafe_fields.items():
        errors = validate_surface_registry_update_candidate_packet(_mutated_candidate_packet(field, value))
        assert any("must not include browser artifacts" in error for error in errors), field


def test_candidate_rejects_private_values_and_credential_prompts() -> None:
    unsafe_fields = {
        "credential_prompt": "enter password",
        "private_values": {"permit_number": "private"},
        "raw_authenticated_text": "private page text",
        "payment_details": {"card": "private"},
    }
    for field, value in unsafe_fields.items():
        errors = validate_surface_registry_update_candidate_packet(_mutated_candidate_packet(field, value))
        assert any("must not include credentials, prompts, or private values" in error for error in errors), field


def test_candidate_rejects_automated_login_mfa_captcha_and_account_creation_claims() -> None:
    unsafe_fields = {
        "automated_login": True,
        "automated_mfa": True,
        "automated_captcha": True,
        "automated_account_creation": True,
    }
    for field, value in unsafe_fields.items():
        errors = validate_surface_registry_update_candidate_packet(_mutated_candidate_packet(field, value))
        assert any("must not claim automated login, MFA, CAPTCHA, or account creation" in error for error in errors), field


def test_candidate_rejects_official_completion_and_enabled_consequential_controls() -> None:
    unsafe_fields = {
        "official_actions_completed": ["submitted permit request"],
        "enabled_upload_controls": ["upload correction"],
        "enabled_submission_controls": ["submit application"],
        "enabled_payment_controls": ["pay fee"],
        "enabled_scheduling_controls": ["schedule inspection"],
        "enabled_cancellation_controls": ["cancel permit"],
        "enabled_certification_controls": ["certify acknowledgement"],
        "control": "enabled:submit",
    }
    for field, value in unsafe_fields.items():
        errors = validate_surface_registry_update_candidate_packet(_mutated_candidate_packet(field, value))
        assert any(
            "must not claim official action completion" in error or "must not enable consequential controls" in error
            for error in errors
        ), field


def test_candidate_rejects_enabled_control_in_disabled_control_list() -> None:
    packet = _candidate_packet()
    candidates = packet["registry_update_candidates"]
    assert isinstance(candidates, list)
    first = candidates[0]
    assert isinstance(first, dict)
    controls = first["disabled_consequential_controls"]
    assert isinstance(controls, list)
    controls.append("enabled:payment")
    errors = validate_surface_registry_update_candidate_packet(packet)
    assert any("must not enable consequential controls" in error for error in errors)


def test_builder_rejects_reconciliation_that_stores_browser_artifacts() -> None:
    reconciliation = _readiness_reconciliation()
    reconciliation["stores_browser_artifacts"] = True
    try:
        build_surface_registry_update_candidate_packet(_drift_review(), reconciliation)
    except AssertionError as exc:
        assert "must not store browser artifacts" in str(exc)
    else:
        raise AssertionError("expected browser artifact reconciliation to be rejected")
