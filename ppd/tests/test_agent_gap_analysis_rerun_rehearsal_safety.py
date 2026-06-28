from __future__ import annotations

from copy import deepcopy

from ppd.agent_gap_analysis_rerun_rehearsal import (
    REQUIRED_BLOCKED_ACTION_DOMAINS,
    assert_valid_gap_analysis_rerun_rehearsal_packet,
    validate_gap_analysis_rerun_rehearsal_packet,
)


def _blocked_action(domain: str) -> dict:
    return {
        "case_id": "synthetic-case-001",
        "process_id": "synthetic-process",
        "action_id": f"{domain}_requires_attended_confirmation",
        "blocked": True,
        "requires_attendance": True,
        "requires_exact_confirmation": True,
        "reason_code": "fixture_gap_analysis_blocks_consequential_action",
        "source_evidence_ids": ["ppd-devhub-guide#guardrails"],
    }


def _valid_packet() -> dict:
    return {
        "packet_id": "fixture-first-user-gap-analysis-rerun-rehearsal",
        "packet_status": "fixture_only_no_private_files_no_devhub_no_agent_consumers",
        "execution_boundaries": {
            "calls_llm": False,
            "launches_devhub": False,
            "uses_authenticated_session": False,
            "reads_private_files": False,
            "runs_agent_consumers": False,
            "writes_private_artifacts": False,
        },
        "synthetic_case_deltas": [
            {
                "case_id": "synthetic-case-001",
                "process_id": "synthetic-process",
                "source_evidence_ids": ["ppd-apply-guide#required-facts"],
            }
        ],
        "missing_fact_prompts": [
            {
                "case_id": "synthetic-case-001",
                "process_id": "synthetic-process",
                "prompt_id": "synthetic-case-001.missing_fact_prompt",
                "prompt": "Please confirm the fixture-only contractor license status before rerun.",
                "source_evidence_ids": ["ppd-apply-guide#required-facts"],
            }
        ],
        "stale_conflicting_evidence_notes": [],
        "blocked_action_expectations": [_blocked_action(domain) for domain in sorted(REQUIRED_BLOCKED_ACTION_DOMAINS)],
        "next_safe_action_candidates": [
            {
                "case_id": "synthetic-case-001",
                "process_id": "synthetic-process",
                "action_id": "ask_cited_missing_fact_prompt",
                "requires_devhub": False,
                "reads_private_files": False,
                "runs_agent_consumer": False,
                "source_evidence_ids": ["ppd-apply-guide#required-facts"],
            }
        ],
    }


def test_valid_user_gap_analysis_rerun_rehearsal_packet_passes() -> None:
    packet = _valid_packet()

    assert validate_gap_analysis_rerun_rehearsal_packet(packet) == []
    assert_valid_gap_analysis_rerun_rehearsal_packet(packet)


def test_user_gap_analysis_rerun_rehearsal_rejects_private_live_uncited_and_guaranteed_content() -> None:
    packet = _valid_packet()
    packet["private_case_facts"] = {"property_address": "redacted private address"}
    packet["local_preview_path"] = "/home/example/private/devhub/session/state.json"
    packet["execution_boundaries"]["launches_devhub"] = True
    packet["missing_fact_prompts"][0]["source_evidence_ids"] = []
    packet["next_safe_action_candidates"][0]["description"] = "The permit will be approved after this rerun."

    codes = {issue.code for issue in validate_gap_analysis_rerun_rehearsal_packet(packet)}

    assert "private_case_fact_present" in codes
    assert "private_value_present" in codes
    assert "live_execution_claim" in codes
    assert "unsafe_execution_boundary" in codes
    assert "uncited_rehearsal_row" in codes
    assert "outcome_guarantee_present" in codes


def test_user_gap_analysis_rerun_rehearsal_rejects_missing_blocked_expectations_and_enabled_controls() -> None:
    packet = _valid_packet()
    packet["blocked_action_expectations"] = [_blocked_action("submission")]
    packet["ui_controls"] = [
        {"control_id": "upload_plans", "label": "Upload plans", "enabled": True},
        {"control_id": "submit_payment", "label": "Submit payment", "disabled": False},
    ]

    codes = {issue.code for issue in validate_gap_analysis_rerun_rehearsal_packet(packet)}

    assert "missing_blocked_action_expectation" in codes
    assert "enabled_consequential_control" in codes


def test_user_gap_analysis_rerun_rehearsal_rejects_uncited_action_expectations() -> None:
    packet = deepcopy(_valid_packet())
    packet["blocked_action_expectations"][0]["source_evidence_ids"] = []
    packet["next_safe_action_candidates"][0]["source_evidence_ids"] = []

    codes = {issue.code for issue in validate_gap_analysis_rerun_rehearsal_packet(packet)}

    assert "uncited_rehearsal_row" in codes
