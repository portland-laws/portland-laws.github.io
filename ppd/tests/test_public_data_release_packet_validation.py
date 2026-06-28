from pathlib import Path

from ppd.public_data_release_packet_validation import load_release_packet, validate_release_packet


FIXTURES = Path(__file__).parent / "fixtures" / "public_data_release_packets"


def _codes(packet_name):
    packet = load_release_packet(FIXTURES / packet_name)
    return {error.code for error in validate_release_packet(packet)}


def test_valid_dry_run_release_packet_passes_validation():
    assert _codes("valid_dry_run_packet.json") == set()


def test_invalid_release_packet_reports_all_blocking_guardrails():
    codes = _codes("invalid_dry_run_packet.json")

    assert "missing_prerequisite_packet_links" in codes
    assert "stale_source_version" in codes
    assert "stale_guardrail_version" in codes
    assert "uncited_operator_checklist_item" in codes
    assert "private_or_session_artifact" in codes
    assert "raw_crawl_output" in codes
    assert "consequential_action_readiness" in codes
    assert "missing_human_signoff" in codes
