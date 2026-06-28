from __future__ import annotations

from pathlib import Path

import pytest

from ppd.devhub.read_only_pilot import (
    build_read_only_pilot_evidence_packet,
    load_operator_go_no_go_packet,
    validate_read_only_pilot_evidence_packet,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "devhub_read_only_pilot"


def _evidence() -> dict[str, object]:
    operator_packet = load_operator_go_no_go_packet(FIXTURE_DIR / "operator_go_no_go_packet.json")
    return build_read_only_pilot_evidence_packet(operator_packet).to_dict()


def test_fixture_first_dry_run_builds_commit_safe_evidence_packet() -> None:
    evidence = _evidence()

    assert evidence["source_operator_packet_id"] == "operator-go-no-go-devhub-read-only-pilot-20260528"
    assert evidence["execution_mode"] == "fixture_first_devhub_read_only_pilot_dry_run"
    assert evidence["devhub_launched"] is False
    assert evidence["browser_artifacts_stored"] is False
    assert evidence["live_session_deferred"] is True
    assert len(evidence["synthetic_operator_acknowledgements"]) == 4
    assert len(evidence["redacted_surface_ids"]) == 4
    assert all(surface_id.startswith("devhub-surface-redacted-") for surface_id in evidence["redacted_surface_ids"])
    assert "DevHub Home" not in " ".join(evidence["redacted_surface_ids"])
    assert evidence["read_only_observation_objectives"]
    assert evidence["abort_decision_examples"]
    assert evidence["go_no_go_links"]
    assert evidence["abort_decisions"]
    assert evidence["disabled_consequential_controls"]
    assert evidence["journal_event_ids"]
    assert evidence["deferred_live_session_prerequisites"]
    assert validate_read_only_pilot_evidence_packet(evidence) == []


def test_fixture_first_dry_run_rejects_missing_acknowledgement() -> None:
    operator_packet = load_operator_go_no_go_packet(FIXTURE_DIR / "operator_go_no_go_packet.json")
    operator_packet["operator_acknowledgements"]["no_private_values"] = False

    with pytest.raises(ValueError, match="no_private_values"):
        build_read_only_pilot_evidence_packet(operator_packet)


def test_packet_validator_flags_live_or_artifact_state() -> None:
    evidence = _evidence()
    evidence["devhub_launched"] = True
    evidence["browser_artifacts_stored"] = True

    errors = validate_read_only_pilot_evidence_packet(evidence)

    assert "devhub_launched must be false" in errors
    assert "browser_artifacts_stored must be false" in errors


@pytest.mark.parametrize(
    ("field_name", "field_value", "expected"),
    [
        ("credentials", "example-password", "contains forbidden credential/session/artifact/private field"),
        ("automated_login", True, "contains forbidden credential/session/artifact/private field"),
        ("mfa_code", "000000", "contains forbidden credential/session/artifact/private field"),
        ("captcha_solution", "solved", "contains forbidden credential/session/artifact/private field"),
        ("screenshot_path", "/tmp/devhub.png", "contains forbidden credential/session/artifact/private field"),
        ("trace_path", "/tmp/trace.zip", "contains forbidden credential/session/artifact/private field"),
        ("har_path", "/tmp/devhub.har", "contains forbidden credential/session/artifact/private field"),
        ("cookies", {"session": "redacted"}, "contains forbidden credential/session/artifact/private field"),
        ("auth_state", {"storage": "redacted"}, "contains forbidden credential/session/artifact/private field"),
        ("private_field_value", "1234 SE Example St", "contains forbidden credential/session/artifact/private field"),
        ("official_actions_completed", {"submission": True}, "claims official action completion"),
    ],
)
def test_packet_validator_rejects_private_automation_artifact_and_completion_fields(
    field_name: str,
    field_value: object,
    expected: str,
) -> None:
    evidence = _evidence()
    evidence[field_name] = field_value

    errors = validate_read_only_pilot_evidence_packet(evidence)

    assert any(expected in error for error in errors)


@pytest.mark.parametrize(
    "claim",
    [
        "The pilot used automated login.",
        "The worker completed MFA automatically.",
        "The worker solved CAPTCHA.",
        "The pilot completed account creation.",
        "The packet stored screenshots, traces, HAR, cookies, auth state, and private values.",
        "The operator uploaded, submitted, certified, paid, scheduled, and canceled official actions.",
    ],
)
def test_packet_validator_rejects_forbidden_evidence_text_claims(claim: str) -> None:
    evidence = _evidence()
    evidence["unsafe_claim"] = claim

    errors = validate_read_only_pilot_evidence_packet(evidence)

    assert any("contains prohibited DevHub pilot evidence content" in error for error in errors)


def test_packet_validator_rejects_missing_go_no_go_links() -> None:
    evidence = _evidence()
    evidence.pop("go_no_go_links")

    errors = validate_read_only_pilot_evidence_packet(evidence)

    assert "go_no_go_links must include the source operator go/no-go packet" in errors


def test_packet_validator_rejects_unconsumed_go_no_go_link() -> None:
    evidence = _evidence()
    links = evidence["go_no_go_links"]
    assert isinstance(links, list)
    links[0]["consumed"] = False

    errors = validate_read_only_pilot_evidence_packet(evidence)

    assert "go_no_go_links[0].consumed must be true" in errors


def test_packet_validator_rejects_missing_abort_decisions() -> None:
    evidence = _evidence()
    evidence["abort_decisions"] = []

    errors = validate_read_only_pilot_evidence_packet(evidence)

    assert "abort_decisions must be non-empty" in errors


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
def test_packet_validator_rejects_enabled_consequential_controls(control_id: str, expected: str) -> None:
    evidence = _evidence()
    controls = evidence["disabled_consequential_controls"]
    assert isinstance(controls, list)
    for control in controls:
        if control["control_id"] == control_id:
            control["enabled"] = True

    errors = validate_read_only_pilot_evidence_packet(evidence)

    assert expected in errors
