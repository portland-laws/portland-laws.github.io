from __future__ import annotations

import copy
from pathlib import Path

import pytest

from ppd.agent_readiness.public_refresh_agent_gap_analysis_replay_packet_v1 import (
    EXACT_OFFLINE_VALIDATION_COMMANDS,
    build_public_refresh_agent_gap_analysis_replay_packet_v1,
    build_public_refresh_agent_gap_analysis_replay_packet_v1_from_file,
    validate_public_refresh_agent_gap_analysis_replay_packet_v1,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "public_refresh_agent_gap_analysis_replay_packet_v1" / "synthetic_rows.json"


def valid_packet() -> dict:
    return build_public_refresh_agent_gap_analysis_replay_packet_v1_from_file(FIXTURE_PATH)


def test_build_public_refresh_agent_gap_analysis_replay_packet_from_fixture() -> None:
    packet = valid_packet()

    assert packet["packet_type"] == "ppd.public_refresh_agent_gap_analysis_replay_packet.v1"
    assert packet["packet_version"] == "v1"
    assert packet["execution_mode"] == "offline_fixture_only"
    assert packet["non_mutation_flags"] == {
        "fixture_first": True,
        "uses_synthetic_rows_only": True,
        "live_extraction_performed": False,
        "live_crawling_performed": False,
        "documents_downloaded": False,
        "devhub_opened": False,
        "active_agent_api_mutated": False,
        "active_case_records_mutated": False,
        "active_process_models_mutated": False,
        "active_guardrails_mutated": False,
        "official_actions_performed": False,
    }
    assert packet["exact_offline_validation_commands"] == EXACT_OFFLINE_VALIDATION_COMMANDS

    cases = packet["user_gap_analysis_replay_expectations"]
    assert len(cases) == 2
    first = cases[0]
    assert first["source_rows"] == {
        "inactive_process_model_delta_plan_row_id": "pm-delta-001",
        "inactive_guardrail_recompile_plan_row_id": "gr-recompile-001",
    }
    assert first["user_gap_analysis_expectation"]["expected_status"] == "held_for_reviewer_gap_analysis_replay"
    assert first["missing_fact_deltas"]
    assert first["missing_document_deltas"]
    assert first["stale_evidence_outcomes"]
    assert first["conflicting_evidence_outcomes"]
    assert first["blocked_action_checks"][0]["expected_decision"] == "blocked"
    assert first["next_safe_action_deltas"]
    assert first["source_evidence_placeholders"]
    assert first["reviewer_hold"]["status"] == "held_for_manual_review"
    assert "no active agent API" in first["rollback_note"]["note"]

    summary = packet["source_evidence_placeholder_summary"]
    assert summary["all_replay_cases_have_source_evidence_placeholders"] is True
    assert "src-placeholder-intake-001" in summary["placeholder_ids"]
    assert packet["reviewer_holds"]
    assert packet["rollback_notes"]
    assert validate_public_refresh_agent_gap_analysis_replay_packet_v1(packet) == []


def test_rejects_non_synthetic_process_rows() -> None:
    fixture = {
        "inactive_process_model_delta_plan_rows": [
            {
                "row_type": "inactive_process_model_delta_plan_row",
                "row_id": "pm-delta-bad",
                "synthetic": False,
                "state": "inactive",
                "process_model_id": "public-refresh-intake",
                "source_evidence_placeholder_ids": ["src-placeholder"],
            }
        ],
        "inactive_guardrail_recompile_plan_rows": [
            {
                "row_type": "inactive_guardrail_recompile_plan_row",
                "row_id": "gr-recompile-001",
                "synthetic": True,
                "state": "inactive",
                "process_model_id": "public-refresh-intake",
                "source_evidence_placeholder_ids": ["src-placeholder"],
            }
        ],
    }

    with pytest.raises(ValueError, match="must be synthetic"):
        build_public_refresh_agent_gap_analysis_replay_packet_v1(fixture)


def test_rejects_missing_guardrail_recompile_reference_during_build() -> None:
    fixture = {
        "inactive_process_model_delta_plan_rows": [
            {
                "row_type": "inactive_process_model_delta_plan_row",
                "row_id": "pm-delta-001",
                "synthetic": True,
                "state": "inactive",
                "process_model_id": "public-refresh-intake",
                "source_evidence_placeholder_ids": ["src-placeholder"],
            }
        ],
        "inactive_guardrail_recompile_plan_rows": [
            {
                "row_type": "inactive_guardrail_recompile_plan_row",
                "row_id": "gr-recompile-001",
                "synthetic": True,
                "state": "inactive",
                "process_model_id": "other-process",
                "source_evidence_placeholder_ids": ["src-placeholder"],
            }
        ],
    }

    with pytest.raises(ValueError, match="missing inactive guardrail recompile row"):
        build_public_refresh_agent_gap_analysis_replay_packet_v1(fixture)


@pytest.mark.parametrize(
    ("field_name", "field_value", "expected_fragment"),
    [
        ("note", "live crawl completed", "live extraction/crawl"),
        ("note", "live extraction performed", "live extraction/crawl"),
        ("note", "DevHub opened", "DevHub access"),
        ("note", "active agent API mutated", "active mutation"),
        ("note", "active case record mutated", "active mutation"),
        ("note", "document downloaded", "download"),
        ("note", "raw crawl output", "download"),
        ("note", "application submitted", "official-action"),
        ("note", "certification completed", "official-action"),
        ("note", "permit guaranteed", "guarantee"),
        ("session_state", "state/session-state.json", "private"),
        ("downloaded_document", "artifact/downloaded-document.pdf", "private"),
        ("raw_body", "artifact/raw-body.html", "private"),
    ],
)
def test_rejects_live_private_devhub_mutation_official_and_guarantee_claims(
    field_name: str,
    field_value: str,
    expected_fragment: str,
) -> None:
    fixture = {
        "inactive_process_model_delta_plan_rows": [
            {
                "row_type": "inactive_process_model_delta_plan_row",
                "row_id": "pm-delta-001",
                "synthetic": True,
                "state": "inactive",
                "process_model_id": "public-refresh-intake",
                "source_evidence_placeholder_ids": ["src-placeholder"],
                field_name: field_value,
            }
        ],
        "inactive_guardrail_recompile_plan_rows": [
            {
                "row_type": "inactive_guardrail_recompile_plan_row",
                "row_id": "gr-recompile-001",
                "synthetic": True,
                "state": "inactive",
                "process_model_id": "public-refresh-intake",
                "source_evidence_placeholder_ids": ["src-placeholder"],
            }
        ],
    }

    with pytest.raises(ValueError, match=expected_fragment):
        build_public_refresh_agent_gap_analysis_replay_packet_v1(fixture)


@pytest.mark.parametrize(
    ("path", "expected_fragment"),
    [
        (("source_row_refs", "inactive_process_model_delta_plan_row_ids"), "process_model_delta_plan_row_ids"),
        (("source_row_refs", "inactive_guardrail_recompile_plan_row_ids"), "guardrail_recompile_plan_row_ids"),
        (("user_gap_analysis_replay_expectations",), "user_gap_analysis_replay_expectations must be a non-empty list"),
        (("user_gap_analysis_replay_expectations", 0, "source_rows", "inactive_process_model_delta_plan_row_id"), "inactive_process_model_delta_plan_row_id is required"),
        (("user_gap_analysis_replay_expectations", 0, "source_rows", "inactive_guardrail_recompile_plan_row_id"), "inactive_guardrail_recompile_plan_row_id is required"),
        (("user_gap_analysis_replay_expectations", 0, "user_gap_analysis_expectation"), "user_gap_analysis_expectation"),
        (("user_gap_analysis_replay_expectations", 0, "missing_fact_deltas"), "missing_fact_deltas must be a non-empty list"),
        (("user_gap_analysis_replay_expectations", 0, "missing_document_deltas"), "missing_document_deltas must be a non-empty list"),
        (("user_gap_analysis_replay_expectations", 0, "stale_evidence_outcomes"), "stale_evidence_outcomes must be a non-empty list"),
        (("user_gap_analysis_replay_expectations", 0, "conflicting_evidence_outcomes"), "conflicting_evidence_outcomes must be a non-empty list"),
        (("user_gap_analysis_replay_expectations", 0, "blocked_action_checks"), "blocked_action_checks must be a non-empty list"),
        (("user_gap_analysis_replay_expectations", 0, "next_safe_action_deltas"), "next_safe_action_deltas must be a non-empty list"),
        (("user_gap_analysis_replay_expectations", 0, "source_evidence_placeholders"), "source_evidence_placeholders must be a non-empty list"),
        (("user_gap_analysis_replay_expectations", 0, "reviewer_hold"), "reviewer_hold must be held_for_manual_review"),
        (("user_gap_analysis_replay_expectations", 0, "rollback_note"), "rollback_note.note is required"),
        (("source_evidence_placeholder_summary", "placeholder_ids"), "source_evidence_placeholder_summary.placeholder_ids"),
        (("reviewer_holds",), "reviewer_holds must be a non-empty list"),
        (("rollback_notes",), "rollback_notes must be a non-empty list"),
        (("exact_offline_validation_commands",), "exact_offline_validation_commands"),
    ],
)
def test_validator_rejects_missing_required_replay_packet_sections(path: tuple, expected_fragment: str) -> None:
    packet = valid_packet()
    _replace_path(packet, path, [] if path[-1] != "user_gap_analysis_expectation" else {})

    problems = validate_public_refresh_agent_gap_analysis_replay_packet_v1(packet)

    assert any(expected_fragment in problem for problem in problems)


def test_validator_rejects_blocked_action_checks_missing_required_action_classes() -> None:
    packet = valid_packet()
    packet["user_gap_analysis_replay_expectations"][0]["blocked_action_checks"][0]["blocked_action_classes"] = ["submit"]

    problems = validate_public_refresh_agent_gap_analysis_replay_packet_v1(packet)

    assert any("blocked action classes" in problem and "upload" in problem for problem in problems)


def test_validator_rejects_active_mutation_flags() -> None:
    packet = valid_packet()
    packet["non_mutation_flags"] = copy.deepcopy(packet["non_mutation_flags"])
    packet["non_mutation_flags"]["active_agent_api_mutated"] = True

    problems = validate_public_refresh_agent_gap_analysis_replay_packet_v1(packet)

    assert any("non_mutation_flags" in problem for problem in problems)
    assert any("active mutation flags" in problem for problem in problems)


def _replace_path(packet: dict, path: tuple, value: object) -> None:
    cursor = packet
    for part in path[:-1]:
        cursor = cursor[part]
    cursor[path[-1]] = value
