from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from ppd.devhub.read_only_pilot_operator_go_no_go import (
    REQUIRED_PACKET_ID,
    assert_valid_go_no_go_packet,
    load_go_no_go_packet,
    validate_go_no_go_packet,
)
from ppd.devhub.read_only_pilot_operator_checklist import load_operator_checklist
from ppd.devhub.read_only_pilot_reconciliation import load_reconciliation_packet
from ppd.devhub.read_only_pilot_result_intake import load_pilot_result_intake
from ppd.post_decision_release_readiness_digest import build_post_decision_release_readiness_digest, load_fixture
from ppd.release_gate_status import load_release_gate_status_packet


FIXTURE_DIR = Path(__file__).parent / "fixtures"
PACKET_PATH = FIXTURE_DIR / "devhub" / "read_only_pilot_operator_go_no_go_packet.json"
RECONCILIATION_PATH = FIXTURE_DIR / "devhub" / "read_only_pilot_reconciliation_packet.json"
OPERATOR_CHECKLIST_PATH = FIXTURE_DIR / "devhub" / "read_only_pilot_operator_checklist.json"
PILOT_RESULT_INTAKE_PATH = FIXTURE_DIR / "devhub" / "read_only_pilot_result_intake.json"
RELEASE_GATE_STATUS_PATH = FIXTURE_DIR / "release_gate_status" / "status_packet.json"
POST_DECISION_INPUTS_PATH = FIXTURE_DIR / "post_decision_release_readiness_digest" / "input_packets.json"


def _inputs() -> tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object], dict[str, object], dict[str, object]]:
    return (
        load_go_no_go_packet(PACKET_PATH),
        load_reconciliation_packet(RECONCILIATION_PATH),
        build_post_decision_release_readiness_digest(load_fixture(POST_DECISION_INPUTS_PATH)),
        load_operator_checklist(OPERATOR_CHECKLIST_PATH),
        load_pilot_result_intake(PILOT_RESULT_INTAKE_PATH),
        load_release_gate_status_packet(RELEASE_GATE_STATUS_PATH),
    )


def _errors(packet: dict[str, object]) -> tuple[str, ...]:
    _, reconciliation, digest, operator_checklist, pilot_result_intake, release_gate_status = _inputs()
    return validate_go_no_go_packet(
        packet,
        reconciliation,
        digest,
        operator_checklist,
        pilot_result_intake,
        release_gate_status,
    ).errors


def test_operator_go_no_go_fixture_is_valid() -> None:
    packet, reconciliation, digest, operator_checklist, pilot_result_intake, release_gate_status = _inputs()

    result = validate_go_no_go_packet(
        packet,
        reconciliation,
        digest,
        operator_checklist,
        pilot_result_intake,
        release_gate_status,
    )

    assert result.packet_id == REQUIRED_PACKET_ID
    assert result.ok is True
    assert result.errors == ()
    assert_valid_go_no_go_packet(
        packet,
        reconciliation,
        digest,
        operator_checklist,
        pilot_result_intake,
        release_gate_status,
    )


def test_operator_go_no_go_consumes_required_source_packets() -> None:
    packet, _, _, _, _, _ = _inputs()
    packet["source_packets"]["devhub_read_only_pilot_readiness_reconciliation"]["consumed"] = False

    errors = _errors(packet)

    assert "source_packets.devhub_read_only_pilot_readiness_reconciliation.consumed must be true" in errors


def test_operator_go_no_go_does_not_launch_devhub_or_playwright() -> None:
    packet, _, _, _, _, _ = _inputs()
    packet["launches_devhub"] = True
    packet["launches_playwright"] = True

    errors = _errors(packet)

    assert "launches_devhub must be false" in errors
    assert "launches_playwright must be false" in errors


def test_operator_go_no_go_requires_complete_redaction_checklist() -> None:
    packet, _, _, _, _, _ = _inputs()
    packet["redaction_checklist"] = [
        item for item in packet["redaction_checklist"] if item["item_id"] != "no_har_files"
    ]

    errors = _errors(packet)

    assert "redaction_checklist missing: no_har_files" in errors


def test_operator_go_no_go_requires_abort_trigger_coverage() -> None:
    packet, _, _, _, _, _ = _inputs()
    packet["abort_triggers"] = [
        {
            "trigger_id": "abort-too-narrow",
            "trigger": "Abort on credential handling only.",
            "operator_response": "Stop.",
            "journal_event_type": "refused action",
            "records_only_redacted_metadata": True,
            "continues_session": False,
        }
    ]

    errors = _errors(packet)

    assert "abort_triggers missing required term: mfa" in errors
    assert "abort_triggers missing required term: upload" in errors
    assert "abort_triggers missing required term: auth state" in errors


def test_operator_go_no_go_requires_manual_login_boundaries() -> None:
    packet, _, _, _, _, _ = _inputs()
    packet["manual_login_boundaries"][0]["automated"] = True

    errors = _errors(packet)

    assert "manual_login_boundaries[0].automated must be false" in errors


def test_operator_go_no_go_rejects_enabled_consequential_control() -> None:
    packet, _, _, _, _, _ = _inputs()
    packet["disabled_consequential_controls"][0]["enabled"] = True

    errors = _errors(packet)

    assert "disabled_consequential_controls.upload.enabled must be false" in errors


@pytest.mark.parametrize(
    ("control_id", "expected"),
    [
        ("upload", "disabled_consequential_controls.upload.enabled must be false"),
        ("submission", "disabled_consequential_controls.submission.enabled must be false"),
        ("payment", "disabled_consequential_controls.payment.enabled must be false"),
        ("scheduling", "disabled_consequential_controls.scheduling.enabled must be false"),
        ("cancellation", "disabled_consequential_controls.cancellation.enabled must be false"),
        ("certification", "disabled_consequential_controls.certification.enabled must be false"),
    ],
)
def test_operator_go_no_go_rejects_each_enabled_consequential_control(control_id: str, expected: str) -> None:
    packet, _, _, _, _, _ = _inputs()
    for control in packet["disabled_consequential_controls"]:
        if control["control_id"] == control_id:
            control["enabled"] = True

    errors = _errors(packet)

    assert expected in errors


def test_operator_go_no_go_rejects_private_or_browser_artifact_content() -> None:
    packet, _, _, _, _, _ = _inputs()
    packet = deepcopy(packet)
    packet["journal_event_templates"][0]["screenshot_path"] = "redacted-token-only"

    errors = _errors(packet)

    assert any("forbidden private/session field" in error for error in errors)


@pytest.mark.parametrize(
    ("claim", "expected_fragment"),
    [
        ("The operator collected credentials before the pilot.", "credential collection claim"),
        ("The worker performed automated login for the user.", "automated login claim"),
        ("The worker completed MFA automatically.", "automated mfa claim"),
        ("The worker solved CAPTCHA automatically.", "automated captcha claim"),
        ("The pilot completed account creation.", "account creation claim"),
        ("The pilot saved screenshots, traces, HAR, cookies, auth state, and private values.", "browser artifact claim"),
        ("The pilot completed upload, submission, certification, payment, scheduling, and cancellation.", "official action completion claim"),
    ],
)
def test_operator_go_no_go_rejects_forbidden_pilot_claims(claim: str, expected_fragment: str) -> None:
    packet, _, _, _, _, _ = _inputs()
    packet["pilot_claims"] = [{"claim_id": "unsafe-claim", "claim": claim}]

    errors = _errors(packet)

    assert any(expected_fragment in error for error in errors)


@pytest.mark.parametrize(
    "field_name",
    [
        "official_action_completed",
        "official_actions_completed",
        "completed_official_action",
        "action_completed",
        "official_completion",
        "completion_claim",
    ],
)
def test_operator_go_no_go_rejects_official_action_completion_fields(field_name: str) -> None:
    packet, _, _, _, _, _ = _inputs()
    packet[field_name] = {"upload": True}

    errors = _errors(packet)

    assert any("claims official action completion" in error for error in errors)


def test_operator_go_no_go_assertion_has_stable_failure() -> None:
    packet, reconciliation, digest, operator_checklist, pilot_result_intake, release_gate_status = _inputs()
    packet["official_actions_enabled"] = True

    with pytest.raises(AssertionError, match="official_actions_enabled must be false"):
        assert_valid_go_no_go_packet(
            packet,
            reconciliation,
            digest,
            operator_checklist,
            pilot_result_intake,
            release_gate_status,
        )
