import copy
import json
from pathlib import Path

import pytest

from ppd.validation.guardrail_explanation_audit_packet import (
    finding_codes,
    require_valid_guardrail_explanation_audit_packet,
    validate_guardrail_explanation_audit_packet,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "guardrails" / "explanation_audit_packet.json"
EXPECTED_STATES = {
    "allowed_local_preview",
    "missing_fact",
    "refused_action",
    "manual_handoff",
    "stale_evidence",
    "unresolved_review",
}
FORBIDDEN_SIDE_EFFECTS = {
    "launch_devhub",
    "read_private_files",
    "create_auth_state",
    "create_trace",
    "download_documents",
    "submit_application",
    "upload_documents",
    "pay_fee",
    "certify_or_attest",
}


def load_packet():
    with FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def test_explanation_audit_packet_is_fixture_first():
    packet = load_packet()

    assert packet["devhub_launch_required"] is False
    assert packet["private_file_access_required"] is False
    assert packet["live_crawl_required"] is False
    assert set(packet["forbidden_side_effects"]) == FORBIDDEN_SIDE_EFFECTS
    assert packet["synthetic_case"]["case_id"].startswith("synthetic-")


def test_explanation_audit_packet_covers_required_states():
    packet = load_packet()
    outcomes = packet["sampled_outcomes"]

    assert {outcome["state"] for outcome in outcomes} == EXPECTED_STATES
    assert len(outcomes) == len(EXPECTED_STATES)


def test_each_sampled_outcome_has_cited_user_facing_explanation():
    packet = load_packet()

    for outcome in packet["sampled_outcomes"]:
        explanation = outcome.get("user_facing_explanation", "")
        citations = outcome.get("citations", [])

        assert explanation.strip(), outcome["state"]
        assert citations, outcome["state"]
        for citation in citations:
            assert citation.get("source_id", "").startswith("fixture."), outcome["state"]
            assert citation.get("supports", "").strip(), outcome["state"]


def test_refused_action_and_preview_explanations_preserve_guardrails():
    packet = load_packet()
    by_state = {outcome["state"]: outcome for outcome in packet["sampled_outcomes"]}

    allowed = by_state["allowed_local_preview"]["user_facing_explanation"].lower()
    refused = by_state["refused_action"]["user_facing_explanation"].lower()

    assert "not open devhub" in allowed
    assert "submit" in refused
    assert "upload" in refused
    assert "pay" in refused
    assert "certify" in refused


def test_valid_explanation_audit_packet_passes_policy_validation():
    packet = load_packet()

    findings = validate_guardrail_explanation_audit_packet(packet)

    assert findings == []
    require_valid_guardrail_explanation_audit_packet(packet)


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    [
        ("uncited_explanation", "uncited_explanation_text"),
        ("private_value", "private_value"),
        ("stale_guardrail_input", "stale_guardrail_input"),
        ("missing_refused_action_explanation", "missing_refused_action_explanation"),
        ("missing_manual_handoff_rationale", "missing_manual_handoff_rationale"),
        ("agent_executable_consequential_language", "agent_executable_consequential_language"),
    ],
)
def test_explanation_audit_packet_rejects_policy_mutations(mutation, expected_code):
    packet = load_packet()
    mutated = mutate_packet(packet, mutation)

    findings = validate_guardrail_explanation_audit_packet(mutated)

    assert expected_code in finding_codes(findings)
    with pytest.raises(ValueError):
        require_valid_guardrail_explanation_audit_packet(mutated)


def mutate_packet(packet, mutation):
    packet = copy.deepcopy(packet)
    by_state = {outcome["state"]: outcome for outcome in packet["sampled_outcomes"]}

    if mutation == "uncited_explanation":
        by_state["missing_fact"]["citations"] = []
    elif mutation == "private_value":
        packet["synthetic_case"]["payment_card_number"] = "PRIVATE_VALUE_4111111111111111"
    elif mutation == "stale_guardrail_input":
        packet["guardrail_inputs"]["source_snapshot_date"] = "2026-04-01"
    elif mutation == "missing_refused_action_explanation":
        by_state["refused_action"]["user_facing_explanation"] = "A permit application submission action was requested."
    elif mutation == "missing_manual_handoff_rationale":
        by_state["manual_handoff"].pop("handoff_reason", None)
        by_state["manual_handoff"].pop("manual_handoff_rationale", None)
    elif mutation == "agent_executable_consequential_language":
        by_state["allowed_local_preview"]["user_facing_explanation"] = "I will upload the documents and submit the application for you."
    else:
        raise AssertionError(f"unknown mutation: {mutation}")

    return packet
