from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ppd.agent_safe_action_freshness_regression_packet import (
    build_safe_action_freshness_regression_packet,
    require_valid_safe_action_freshness_regression_packet,
    validate_safe_action_freshness_regression_packet,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "agent_safe_action_freshness_regression" / "source_packets.json"


def _fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _packet() -> dict:
    fixture = _fixture()
    return build_safe_action_freshness_regression_packet(
        fixture["safe_read_only_action_transcript_packet"],
        fixture["evidence_freshness_watchlist_reviewer_disposition_packet"],
        fixture["agent_prompt_regression_dry_run_packet"],
    )


def _codes(packet: dict) -> set[str]:
    return {issue.code for issue in validate_safe_action_freshness_regression_packet(packet)}


def test_builds_fixture_first_safe_action_freshness_regression_packet() -> None:
    packet = _packet()

    assert packet["packet_type"] == "ppd.safe_action_freshness_regression_packet.v1"
    assert packet["fixture_first"] is True
    assert packet["metadata_only"] is True
    assert packet["input_packet_refs"] == {
        "safe_read_only_action_transcript_packet_id": "safe-read-only-transcript-20260529-fixture",
        "evidence_freshness_watchlist_reviewer_disposition_packet_id": "freshness-watchlist-disposition-20260529-fixture",
        "agent_prompt_regression_dry_run_packet_id": "agent-prompt-regression-dry-run-20260529-fixture",
    }
    assert validate_safe_action_freshness_regression_packet(packet) == []
    require_valid_safe_action_freshness_regression_packet(packet)


def test_packet_contains_cited_stale_evidence_scenarios_and_expected_agent_behavior() -> None:
    packet = _packet()
    scenarios = packet["stale_evidence_user_scenarios"]

    assert [scenario["scenario_id"] for scenario in scenarios] == [
        "stale-devhub-submit-guide-upload-certification",
        "stale-fee-payment-guide",
    ]
    for scenario in scenarios:
        assert scenario["source_evidence_ids"]
        assert scenario["stale_evidence"]
        assert scenario["expected_missing_fact_prompts"] or scenario["expected_refusals"]
        assert scenario["blocked_action_explanations"]
        for prompt in scenario["expected_missing_fact_prompts"]:
            assert prompt["source_evidence_ids"]
            assert prompt["expected_status"] in {"missing", "stale"}
        for refusal in scenario["expected_refusals"]:
            assert refusal["source_evidence_ids"]
            assert "Refuse" in refusal["refusal"] or "cannot" in refusal["refusal"].lower()


def test_packet_carries_reviewer_owner_fields_and_no_mutation_attestations() -> None:
    packet = _packet()

    assert {owner["reviewer_owner_id"] for owner in packet["reviewer_owner_fields"]} >= {
        "ppd-safe-read-only-reviewer",
        "ppd-freshness-reviewer",
        "ppd-prompt-regression-reviewer",
    }
    for owner in packet["reviewer_owner_fields"]:
        assert owner["reviewer_role"]
        assert owner["reviewer_disposition"]
        assert owner["source_evidence_ids"]

    attestations = packet["attestations"]
    assert attestations["no_live_llm"] is True
    assert attestations["no_devhub"] is True
    assert attestations["no_prompt_mutation"] is True
    assert attestations["no_guardrail_mutation"] is True
    assert attestations["no_private_devhub_session_files"] is True


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    [
        (lambda packet: packet.__setitem__("fixture_first", False), "not_fixture_first_metadata_only"),
        (lambda packet: packet.__setitem__("reviewer_owner_fields", []), "missing_reviewer_owner_fields"),
        (lambda packet: packet["attestations"].__setitem__("no_live_llm", False), "missing_no_mutation_attestation"),
        (lambda packet: packet["stale_evidence_user_scenarios"][0].__setitem__("source_evidence_ids", []), "uncited_stale_scenario"),
        (lambda packet: packet["stale_evidence_user_scenarios"][0].__setitem__("blocked_action_explanations", []), "missing_blocked_action_explanations"),
        (lambda packet: packet.__setitem__("session_state", "auth_state/private.json"), "private_or_auth_field_present"),
    ],
)
def test_validation_rejects_unsafe_or_incomplete_packets(mutation: object, expected_code: str) -> None:
    packet = copy.deepcopy(_packet())
    mutation(packet)

    assert expected_code in _codes(packet)
