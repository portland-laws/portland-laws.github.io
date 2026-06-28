import json
from pathlib import Path


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "devhub_attended_handoff_packet"
    / "reversible_draft_read_only_review_packet.json"
)

FORBIDDEN_KEY_FRAGMENTS = (
    "password",
    "credential",
    "cookie",
    "auth_state",
    "storage_state",
    "session_state",
    "screenshot",
    "trace",
    "har",
    "private_page_value",
    "payment_detail",
    "token",
    "secret",
)

FORBIDDEN_VALUE_MARKERS = (
    "BEGIN PRIVATE",
    "COOKIE=",
    "Set-Cookie",
    "Authorization:",
    "Bearer ",
    ".zip",
    ".har",
    "trace.zip",
    "storageState",
)


def load_packet():
    with FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def walk_values(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from walk_values(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_values(child)
    elif isinstance(value, (str, int, float, bool)) or value is None:
        yield str(value)


def test_attended_handoff_packet_declares_fixture_only_safe_workflow():
    packet = load_packet()

    assert packet["fixture_only"] is True
    assert packet["workflow"]["surface"] == "DevHub"
    assert packet["workflow"]["workflow_type"] == "reversible_devhub_draft_or_read_only_review"
    assert set(packet["workflow"]["allowed_modes"]) == {"read_only_review", "reversible_draft"}
    assert "official_submission" in packet["workflow"]["prohibited_modes"]
    assert "payment" in packet["workflow"]["prohibited_modes"]


def test_manual_login_prerequisites_and_attendance_are_explicit():
    packet = load_packet()
    prerequisites = packet["manual_login_prerequisites"]
    attendance = packet["attendance_requirement"]

    assert prerequisites["start_url"] == "https://devhub.portlandoregon.gov"
    assert prerequisites["browser_requirement"] == "user_visible_browser"
    assert prerequisites["credential_handling"] == "user_enters_portlandoregon_gov_credentials_manually"
    assert prerequisites["mfa_or_captcha_handling"] == "user_completes_any_mfa_captcha_or_security_prompt_manually"
    assert prerequisites["worker_must_not_request_credentials"] is True
    assert prerequisites["worker_must_not_store_credentials"] is True
    assert prerequisites["worker_must_not_store_session_state"] is True
    assert attendance["requires_user_present"] is True
    assert attendance["pause_when_user_absent"] is True
    assert attendance["handoff_before_consequential_control"] is True


def test_selector_confidence_evidence_and_preview_text_are_present_without_private_artifacts():
    packet = load_packet()
    selector_evidence = packet["selector_confidence_evidence"]
    observations = selector_evidence["selector_observations"]

    assert selector_evidence["minimum_confidence_for_draft"] >= 0.9
    assert selector_evidence["minimum_confidence_for_read_only"] >= 0.85
    assert len(observations) >= 3
    for observation in observations:
        assert observation["selector_kind"]
        assert observation["selector"]
        assert observation["confidence"] >= 0.86
        assert observation["evidence"]
        assert observation["private_value_included"] is False

    excluded = set(selector_evidence["evidence_artifacts_excluded"])
    assert {"screenshots", "traces", "har_data", "private_page_values"}.issubset(excluded)
    assert packet["preview_text"]["title"]
    assert "stop before upload" in packet["preview_text"]["body"]
    assert "no credentials" in packet["preview_text"]["redaction_note"]


def test_exact_confirmation_checkpoints_and_blocked_official_controls_are_complete():
    packet = load_packet()

    checkpoints = packet["exact_confirmation_checkpoints"]
    checkpoint_targets = {checkpoint["required_before"] for checkpoint in checkpoints}
    assert "opening_account_scoped_review_surface" in checkpoint_targets
    assert "filling_or_editing_reversible_draft_fields" in checkpoint_targets
    assert "any_control_that_could_affect_an_official_record" in checkpoint_targets
    assert all(checkpoint["requires_exact_user_confirmation"] is True for checkpoint in checkpoints)

    blocked_controls = "\n".join(control["control"] for control in packet["blocked_official_controls"])
    for expected in (
        "Submit permit request",
        "Certify acknowledgement",
        "Upload correction or attachment to official record",
        "Purchase permit or submit payment",
        "Schedule, cancel, or reschedule inspection",
        "Cancel, withdraw, extend, or reactivate request",
        "Account creation or account security changes",
    ):
        assert expected in blocked_controls


def test_redaction_guarantees_exclude_session_private_and_capture_artifacts():
    packet = load_packet()
    guarantees = packet["redaction_guarantees"]

    for guarantee in (
        "exclude_credentials",
        "exclude_cookies",
        "exclude_auth_state",
        "exclude_screenshots",
        "exclude_traces",
        "exclude_har_data",
        "exclude_private_page_values",
        "exclude_payment_details",
        "exclude_local_private_file_paths",
    ):
        assert guarantees[guarantee] is True

    serialized_values = list(walk_values(packet))
    for value in serialized_values:
        lowered = value.lower()
        assert not any(fragment in lowered and "exclude_" not in lowered for fragment in FORBIDDEN_KEY_FRAGMENTS)
        assert not any(marker.lower() in lowered for marker in FORBIDDEN_VALUE_MARKERS)
