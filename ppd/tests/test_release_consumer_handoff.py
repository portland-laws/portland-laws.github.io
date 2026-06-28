from __future__ import annotations

from pathlib import Path

import pytest

from ppd.release_consumer_handoff import HandoffPacketError, compile_handoff_packet_from_path

FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "release_consumer_handoff"
    / "agent_release_consumer_handoff_packet.json"
)


def test_release_consumer_handoff_packet_compiles_from_fixture() -> None:
    packet = compile_handoff_packet_from_path(FIXTURE_PATH)

    assert packet["packet_id"] == "release-consumer-handoff-fixture-20260529"
    assert packet["release_id"] == "supervisor-20260529-415"
    assert packet["source_mode"] == "fixture_first"
    assert packet["validation_summary"]["required_input_sections_consumed"] == [
        "guardrail_consumer_integration_checklist",
        "agent_consumer_regression_rerun_plan",
        "post_promotion_smoke_test_plan",
        "release_notes_candidate",
    ]
    assert packet["validation_summary"]["live_execution"] is False
    assert packet["validation_summary"]["private_case_file_access"] is False
    assert packet["validation_summary"]["llm_consumer_invocation"] is False


def test_release_consumer_handoff_packet_contains_required_consumer_outputs() -> None:
    packet = compile_handoff_packet_from_path(FIXTURE_PATH)

    assert len(packet["readiness_notes"]) >= 3
    assert len(packet["expected_safe_action_envelopes"]) == 3
    assert len(packet["missing_information_prompt_reminders"]) >= 3
    assert len(packet["refusal_examples"]) >= 3
    assert len(packet["reviewer_owners"]) >= 3

    blocked_actions = {
        action
        for envelope in packet["expected_safe_action_envelopes"]
        for action in envelope["blocked_actions"]
    }
    assert "submit permit request" in blocked_actions
    assert "certify acknowledgement" in blocked_actions
    assert "upload correction to official record" in blocked_actions
    assert "schedule inspection" in blocked_actions
    assert "enter payment details" in blocked_actions
    assert "submit payment" in blocked_actions


def test_release_consumer_handoff_outputs_are_cited() -> None:
    packet = compile_handoff_packet_from_path(FIXTURE_PATH)
    citation_ids = set(packet["citations"])

    for section_name in (
        "readiness_notes",
        "expected_safe_action_envelopes",
        "missing_information_prompt_reminders",
        "refusal_examples",
        "reviewer_owners",
    ):
        for item in packet[section_name]:
            assert item["citation_ids"]
            assert set(item["citation_ids"]).issubset(citation_ids)
            assert item["source_input_ids"]


def test_release_consumer_handoff_attests_no_live_or_private_execution() -> None:
    packet = compile_handoff_packet_from_path(FIXTURE_PATH)
    attestations = {item["attestation_id"]: item for item in packet["attestations"]}

    assert attestations["fixture_first_inputs_only"]["status"] == "attested"
    assert attestations["no_llm_consumers_invoked"]["status"] == "attested"
    assert attestations["no_live_agent_execution"]["status"] == "attested"
    assert attestations["no_private_case_files_read"]["status"] == "attested"


def test_release_consumer_handoff_rejects_missing_attestation() -> None:
    import json

    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    fixture["attestations"]["no_live_agent_execution"] = False

    with pytest.raises(HandoffPacketError, match="no_live_agent_execution"):
        from ppd.release_consumer_handoff import compile_handoff_packet

        compile_handoff_packet(fixture)
