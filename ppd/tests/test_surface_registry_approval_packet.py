import json
from pathlib import Path

from ppd.surfaces.surface_registry_approval_packet import (
    issue_codes,
    validate_surface_registry_approval_packet,
)


FIXTURES = Path(__file__).parent / "fixtures" / "surface_registry_approval_packets"


def load_fixture(name: str):
    with (FIXTURES / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_valid_surface_registry_approval_packet_has_no_issues():
    packet = load_fixture("valid_devhub_surface_packet.json")

    issues = validate_surface_registry_approval_packet(packet)

    assert issues == []


def test_rejects_private_artifacts_and_missing_review_guards():
    packet = load_fixture("invalid_private_artifacts_packet.json")

    codes = issue_codes(validate_surface_registry_approval_packet(packet))

    assert "raw_authenticated_value" in codes
    assert "private_session_artifact" in codes
    assert "local_private_path" in codes
    assert "browser_artifact_path" in codes
    assert "uncited_selector_delta_approval" in codes
    assert "missing_reviewer_signoff" in codes
    assert "missing_redaction_attestation" in codes
    assert "missing_rollback_notes" in codes
    assert "enabled_consequential_control" in codes
    assert "live_browser_execution_claim" in codes
    assert "active_surface_registry_mutation_flag" in codes


def test_rejects_enabled_consequential_controls_even_when_classification_is_missing():
    packet = load_fixture("valid_devhub_surface_packet.json")
    packet["controls"] = [{"name": "submit permit request", "enabled": True}]

    codes = issue_codes(validate_surface_registry_approval_packet(packet))

    assert codes == {"enabled_consequential_control"}
