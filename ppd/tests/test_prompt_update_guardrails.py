from __future__ import annotations

import pytest

from ppd.prompt_update_guardrails import (
    assert_agent_prompt_update_candidate_safe,
    validate_agent_prompt_update_candidate,
)


def valid_packet() -> dict:
    return {
        "candidate_id": "prompt-candidate-fixture",
        "summary": "Clarify missing-information behavior for cited PP&D process facts.",
        "prompt_changes": [
            {
                "section": "missing_information",
                "change": "Ask for missing, stale, ambiguous, or conflicting facts before drafting.",
                "source_evidence_ids": ["source-ppd-plan-guardrail-bundle"],
            }
        ],
        "refusal_changes": [
            {
                "section": "consequential_actions",
                "change": "Refuse final submission, upload, scheduling, cancellation, certification, or payment without attended confirmation.",
                "citations": ["source-ppd-plan-non-negotiable-boundaries"],
            }
        ],
        "regression_rerun_expectations": [
            {
                "suite": "ppd.prompt_update_guardrails",
                "expected_result": "unsafe candidate packets are rejected before prompt adoption",
            }
        ],
        "reviewer_owners": ["ppd-guardrails-reviewer"],
        "controls": [
            {"name": "draft_fill", "classification": "reversible", "enabled": True},
            {"name": "submit_application", "classification": "consequential", "enabled": False},
        ],
        "active_prompt_mutation": False,
        "release_state_mutation": False,
    }


def violation_codes(packet: dict) -> set[str]:
    return {violation.code for violation in validate_agent_prompt_update_candidate(packet)}


def test_valid_packet_has_no_violations() -> None:
    packet = valid_packet()

    assert validate_agent_prompt_update_candidate(packet) == []
    assert_agent_prompt_update_candidate_safe(packet)


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("private_case_facts", {"synthetic_fact": "fixture-only applicant value"}, "private_case_facts"),
        ("notes", "fixture came from /home/example/private-case.json", "local_private_path"),
        ("execution_notes", "Ran live DevHub session successfully", "live_execution_claim"),
        ("claims", "The permit will be approved after this change.", "outcome_guarantee"),
        ("active_prompt_mutation", True, "active_prompt_or_release_state_mutation"),
        ("release_state_mutation", True, "active_prompt_or_release_state_mutation"),
    ],
)
def test_rejects_disallowed_packet_content(field: str, value: object, code: str) -> None:
    packet = valid_packet()
    packet[field] = value

    assert code in violation_codes(packet)


def test_rejects_uncited_prompt_changes() -> None:
    packet = valid_packet()
    packet["prompt_changes"] = [{"section": "missing_information", "change": "Change without evidence."}]

    assert "uncited_prompt_or_refusal_change" in violation_codes(packet)


def test_rejects_uncited_refusal_changes() -> None:
    packet = valid_packet()
    packet["refusal_changes"] = [{"section": "payments", "change": "Change without evidence."}]

    assert "uncited_prompt_or_refusal_change" in violation_codes(packet)


def test_rejects_missing_regression_expectations() -> None:
    packet = valid_packet()
    packet.pop("regression_rerun_expectations")

    assert "missing_regression_rerun_expectations" in violation_codes(packet)


def test_rejects_incomplete_regression_expectations() -> None:
    packet = valid_packet()
    packet["regression_rerun_expectations"] = [{"suite": "ppd.prompt_update_guardrails"}]

    assert "missing_regression_rerun_expectations" in violation_codes(packet)


def test_rejects_missing_reviewer_owners() -> None:
    packet = valid_packet()
    packet["reviewer_owners"] = []

    assert "missing_reviewer_owners" in violation_codes(packet)


def test_rejects_enabled_consequential_controls_by_classification() -> None:
    packet = valid_packet()
    packet["controls"] = [{"name": "submit_application", "classification": "consequential", "enabled": True}]

    assert "enabled_consequential_control" in violation_codes(packet)


def test_rejects_enabled_consequential_controls_by_action_name() -> None:
    packet = valid_packet()
    packet["controls"] = [{"name": "schedule_inspection", "classification": "reversible", "enabled": True}]

    assert "enabled_consequential_control" in violation_codes(packet)


def test_assert_helper_raises_with_violation_details() -> None:
    packet = valid_packet()
    packet["notes"] = "The crawler execution completed against production."

    with pytest.raises(ValueError, match="live_execution_claim"):
        assert_agent_prompt_update_candidate_safe(packet)
