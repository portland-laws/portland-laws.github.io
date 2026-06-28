import json
from pathlib import Path

from ppd.devhub.read_only_pilot_evidence_review import (
    assert_read_only_pilot_evidence_packet,
    validate_read_only_pilot_evidence_packet,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "devhub_read_only_pilot_evidence_review"


def _load_fixture(name):
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_valid_read_only_pilot_evidence_packet_passes():
    packet = _load_fixture("valid_packet.json")

    assert validate_read_only_pilot_evidence_packet(packet) == []
    assert_read_only_pilot_evidence_packet(packet)


def test_unsafe_read_only_pilot_evidence_packet_rejects_required_risks():
    packet = _load_fixture("unsafe_packet.json")

    findings = validate_read_only_pilot_evidence_packet(packet)
    codes = {finding.code for finding in findings}

    assert "raw_authenticated_or_session_value" in codes
    assert "private_session_artifact" in codes
    assert "local_private_path" in codes
    assert "live_browser_execution_claim" in codes
    assert "missing_selector_confidence_notes" in codes
    assert "missing_redaction_attestation" in codes
    assert "missing_manual_handoff_checkpoints" in codes
    assert "enabled_consequential_control" in codes
    assert "active_surface_registry_mutation" in codes


def test_incomplete_safety_attestations_are_rejected():
    packet = _load_fixture("valid_packet.json")
    packet["redaction_attestation"]["no_private_session_artifacts"] = False
    packet["manual_handoff_checkpoints"][0]["status"] = "optional"
    packet["selector_confidence_notes"][0].pop("rationale")

    codes = {finding.code for finding in validate_read_only_pilot_evidence_packet(packet)}

    assert "failed_redaction_attestation" in codes
    assert "invalid_manual_handoff_checkpoint" in codes
    assert "incomplete_selector_confidence_note" in codes
