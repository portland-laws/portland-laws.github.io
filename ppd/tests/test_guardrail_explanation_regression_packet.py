from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from ppd.guardrails.explanation_regression_packet import (
    build_explanation_packet,
    require_valid_explanation_packet,
    validate_explanation_packet,
)


FIXTURES = Path(__file__).parent / "fixtures" / "guardrail_explanations"


def _packet() -> dict:
    return build_explanation_packet(
        FIXTURES / "guardrail_recompilation_rehearsal_packet.json",
        FIXTURES / "process_model_impact_rehearsal_packet.json",
        FIXTURES / "agent_safe_action_regression_matrix.json",
    )


def _codes(packet: dict) -> set[str]:
    return {finding.code for finding in validate_explanation_packet(packet)}


def test_fixture_first_guardrail_explanations_match_regression_packet() -> None:
    packet = _packet()
    expected = json.loads((FIXTURES / "expected_guardrail_explanation_packet.json").read_text())

    assert packet == expected
    assert packet["uses_llm"] is False
    assert packet["promotes_active_guardrails"] is False

    classes = {item["action_class"] for item in packet["explanations"]}
    assert classes == {
        "allowed_read_only",
        "reversible_draft_limit",
        "exact_confirmation_checkpoint",
        "manual_handoff",
        "refused_consequential_action",
    }
    assert all(item["citations"] for item in packet["explanations"])
    assert validate_explanation_packet(packet) == []
    require_valid_explanation_packet(packet)


def test_rejects_uncited_explanation_claims() -> None:
    packet = _packet()
    packet["explanations"][0]["citations"] = []

    assert "uncited_explanation_claim" in _codes(packet)


def test_rejects_unknown_predicate_and_process_ids() -> None:
    packet = _packet()
    packet["explanations"][0]["predicate_ids"] = ["gr-unknown"]
    packet["explanations"][1]["process_ids"] = ["pm-unknown"]

    codes = _codes(packet)
    assert "unknown_predicate_id" in codes
    assert "unknown_process_id" in codes


def test_rejects_stale_current_evidence_without_acknowledgement() -> None:
    packet = _packet()
    packet["explanations"][0]["evidence_freshness"] = "stale_current"

    assert "stale_current_evidence_without_acknowledgement" in _codes(packet)

    packet["explanations"][0]["stale_current_acknowledgement"] = True
    assert "stale_current_evidence_without_acknowledgement" not in _codes(packet)


def test_rejects_private_case_facts() -> None:
    packet = _packet()
    packet["explanations"][0]["private_case_fact"] = "homeowner phone 503-555-1212"

    assert "private_case_fact" in _codes(packet)


def test_rejects_live_llm_or_consumer_execution_claims() -> None:
    packet = _packet()
    packet["live_llm_execution"] = True
    packet["explanations"][0]["explanation"] += " I called the live LLM to verify this."

    assert "live_llm_or_consumer_execution_claim" in _codes(packet)


def test_rejects_legal_or_permitting_outcome_guarantees() -> None:
    packet = _packet()
    packet["explanations"][0]["explanation"] += " This guarantees the permit will be approved."

    assert "legal_or_permitting_outcome_guarantee" in _codes(packet)


def test_rejects_missing_refusal_explanations() -> None:
    packet = _packet()
    refusal = next(item for item in packet["explanations"] if item["action_class"] == "refused_consequential_action")
    refusal["explanation"] = "Treat this as a consequential action."

    assert "missing_refusal_explanation" in _codes(packet)


def test_rejects_active_guardrail_mutation_flags() -> None:
    packet = _packet()
    packet["active_guardrail_mutation"] = True
    packet["promotes_active_guardrails"] = True

    codes = _codes(packet)
    assert "active_guardrail_mutation_flag" in codes


def test_require_valid_explanation_packet_reports_details() -> None:
    packet = deepcopy(_packet())
    packet["explanations"][0]["citations"] = []

    with pytest.raises(ValueError, match="uncited_explanation_claim"):
        require_valid_explanation_packet(packet)
