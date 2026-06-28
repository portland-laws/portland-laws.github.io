from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ppd.requirement_guardrail_traceability_review_packet import (
    PACKET_TYPE,
    TraceabilityReviewPacketError,
    assert_valid_requirement_guardrail_traceability_review_packet,
    build_requirement_guardrail_traceability_review_packet,
    validate_requirement_guardrail_traceability_review_packet,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "requirement_guardrail_traceability_review" / "input_packets.json"


def _inputs() -> dict[str, dict]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _packet() -> dict:
    inputs = _inputs()
    return build_requirement_guardrail_traceability_review_packet(
        inputs["requirement_rerun_work_queue_packet"],
        inputs["process_model_impact_review_packet"],
        inputs["guardrail_bundle_update_candidate_packet"],
        inputs["guardrail_explanation_regression_packet"],
        inputs["agent_prompt_regression_dry_run_packet"],
        generated_at="2026-05-29T00:00:00Z",
    )


def test_builds_fixture_first_requirement_to_guardrail_traceability_review_packet() -> None:
    packet = _packet()

    assert packet["packet_type"] == PACKET_TYPE
    assert packet["fixture_first"] is True
    assert validate_requirement_guardrail_traceability_review_packet(packet).valid is True
    assert_valid_requirement_guardrail_traceability_review_packet(packet)


def test_consumes_all_required_packets_and_emits_cited_links_prompts_and_blocks() -> None:
    packet = _packet()

    assert set(packet["consumed_packets"]) == {
        "requirement_rerun_work_queue_packet",
        "process_model_impact_review_packet",
        "guardrail_bundle_update_candidate_packet",
        "guardrail_explanation_regression_packet",
        "agent_prompt_regression_dry_run_packet",
    }
    assert all(row["packet_id"] for row in packet["consumed_packets"].values())
    assert all(row["source_evidence_ids"] for row in packet["consumed_packets"].values())

    links = packet["requirement_to_process_to_guardrail_links"]
    assert {link["requirement_id"] for link in links} == {
        "REQ-DEVHUB-UPLOAD-GATE-002",
        "REQ-SINGLE-PDF-FILE-RULE-001",
    }
    assert all(link["process_ids"] for link in links)
    assert all(link["guardrail_ids"] for link in links)
    assert all(link["source_evidence_ids"] for link in links)

    prompt_impacts = packet["missing_fact_prompt_impacts"]
    assert {row["prompt_id"] for row in prompt_impacts} == {
        "prompt.require-project-address",
        "prompt.require-plan-file-readiness",
    }
    assert all(row["requires_active_prompt_mutation"] is False for row in prompt_impacts)

    blocked_actions = packet["blocked_action_carryovers"]
    assert {row["action_id"] for row in blocked_actions} == {
        "submit_permit_application",
        "upload_to_official_record",
    }
    assert all(row["blocked"] is True for row in blocked_actions)
    assert all(row["source_evidence_ids"] for row in blocked_actions)


def test_records_reviewer_owners_and_no_active_mutation_attestations() -> None:
    packet = _packet()

    assert packet["reviewer_owner_fields"] == {
        "requirement_owner": "ppd-requirement-reviewer",
        "process_owner": "ppd-process-reviewer",
        "guardrail_owner": "ppd-guardrail-reviewer",
        "prompt_owner": "ppd-agent-prompt-reviewer",
        "traceability_review_owner": "ppd-traceability-reviewer",
    }
    for key in (
        "no_active_requirement_mutation",
        "no_active_process_mutation",
        "no_active_guardrail_mutation",
        "no_active_prompt_mutation",
        "no_active_release_state_mutation",
        "no_live_crawl",
        "no_devhub_execution",
        "no_processor_invocation",
        "no_llm_execution",
        "fixture_first_inputs_only",
    ):
        assert packet["attestations"][key] is True
    assert all(value is False for value in packet["active_mutation_effects"].values())


def test_validator_rejects_uncited_links_missing_prompt_impact_and_mutation_effect() -> None:
    packet = _packet()
    broken = copy.deepcopy(packet)
    broken["requirement_to_process_to_guardrail_links"][0]["source_evidence_ids"] = []
    broken["missing_fact_prompt_impacts"] = []
    broken["active_mutation_effects"]["guardrails_mutated"] = True

    result = validate_requirement_guardrail_traceability_review_packet(broken)

    assert result.valid is False
    assert "uncited_traceability_link" in result.codes()
    assert "uncited_requirement_link" in result.codes()
    assert "uncited_process_link" in result.codes()
    assert "uncited_guardrail_link" in result.codes()
    assert "missing_prompt_impacts" in result.codes()
    assert "active_mutation_effect_enabled" in result.codes()
    with pytest.raises(TraceabilityReviewPacketError):
        assert_valid_requirement_guardrail_traceability_review_packet(broken)


def test_validator_rejects_missing_blocked_actions_and_missing_reviewer_owners() -> None:
    packet = _packet()
    broken = copy.deepcopy(packet)
    broken["blocked_action_carryovers"] = []
    broken["reviewer_owner_fields"]["prompt_owner"] = ""

    result = validate_requirement_guardrail_traceability_review_packet(broken)

    assert result.valid is False
    assert "missing_blocked_action_carryovers" in result.codes()
    assert "missing_reviewer_owner" in result.codes()


def test_validator_rejects_uncited_prompt_links_private_facts_live_claims_guarantees_and_enabled_controls() -> None:
    packet = _packet()
    broken = copy.deepcopy(packet)
    broken["missing_fact_prompt_impacts"][0]["source_evidence_ids"] = []
    broken["private_case_facts"] = {"property_address": "123 Private Review Ave"}
    broken["review_notes"] = "The live LLM queried DevHub, ran the crawler, and invoked the processor. Approval is guaranteed."
    broken["consequential_controls"] = {"submit_permit_application_enabled": True}
    broken["release_state_mutation_enabled"] = True
    broken["attestations"]["no_active_release_state_mutation"] = False
    broken["active_mutation_effects"]["release_state_mutated"] = True

    result = validate_requirement_guardrail_traceability_review_packet(broken)
    codes = set(result.codes())

    assert result.valid is False
    assert "uncited_prompt_link" in codes
    assert "uncited_prompt_impact" in codes
    assert "private_case_fact_present" in codes
    assert "live_execution_claim" in codes
    assert "legal_or_permitting_outcome_guarantee" in codes
    assert "consequential_control_enabled" in codes
    assert "active_mutation_flag_present" in codes
    assert "missing_no_mutation_attestation" in codes
    assert "active_mutation_effect_enabled" in codes
