from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from ppd.agent_readiness.agent_gap_analysis_delta_packet_v1 import (
    EXACT_OFFLINE_VALIDATION_COMMANDS,
    PACKET_TYPE,
    assert_valid_agent_gap_analysis_delta_packet_v1,
    build_agent_gap_analysis_delta_packet_v1_from_file,
    validate_agent_gap_analysis_delta_packet_v1,
)


def _fixture_path() -> Path:
    return Path(__file__).parent / "fixtures" / "agent_gap_analysis_delta_packet_v1" / "synthetic_gap_delta_fixture.json"


def _valid_packet() -> dict[str, Any]:
    return build_agent_gap_analysis_delta_packet_v1_from_file(_fixture_path())


def test_builds_fixture_first_agent_gap_analysis_delta_packet_v1() -> None:
    packet = _valid_packet()

    assert packet["packet_type"] == PACKET_TYPE
    assert packet["mode"] == "offline_fixture_replay_only"
    assert packet["validation_commands"] == EXACT_OFFLINE_VALIDATION_COMMANDS
    assert validate_agent_gap_analysis_delta_packet_v1(packet) == []
    assert_valid_agent_gap_analysis_delta_packet_v1(packet)

    by_case = {result["case_id"]: result for result in packet["synthetic_replay_results"]}
    building = by_case["synthetic-building-plan-review-gap-case"]
    assert "permit_request_requires_plan_review" in building["changed_missing_facts"]
    assert "combined_drawing_plan_pdf" in building["changed_missing_documents"]
    assert "single_pdf_guidance_capture_is_older_than_fixture_baseline" in building["changed_stale_evidence"]
    assert "fixture_has_supporting_documents_combined_with_drawings" in building["changed_conflicting_evidence"]
    assert "exact_confirmation_required_for_certification_submission_or_upload" in building["required_confirmations"]
    assert building["blocked_actions"] == [
        {
            "action": "blocked_certification_submit_or_upload_action",
            "blocked": True,
            "requires_human_confirmation_before_unblock": True,
            "official_action_performed": False,
            "citation_references": ["citation-devhub-application-guide-acknowledgement"],
        }
    ]
    assert building["next_safe_actions"][0]["requires_live_crawl"] is False
    assert building["next_safe_actions"][0]["requires_devhub"] is False
    assert building["next_safe_actions"][0]["uploads"] is False
    assert building["next_safe_actions"][0]["submits"] is False
    assert building["reviewer_holds"][0]["status"] == "pending_human_review"

    trade = by_case["synthetic-trade-permit-gap-case"]
    assert "contractor_license_profile_status" in trade["changed_missing_facts"]
    assert "license_status_reference" in trade["changed_missing_documents"]
    assert "devhub_services_fixture_needs_freshness_review" in trade["changed_stale_evidence"]
    assert "devhub_trade_fixture_options_depend_on_license_profile" in trade["changed_conflicting_evidence"]
    assert "exact_confirmation_required_for_purchase_or_fee_payment" in trade["required_confirmations"]
    assert trade["offline_validation_commands"] == EXACT_OFFLINE_VALIDATION_COMMANDS


def test_rejects_missing_required_replay_rows() -> None:
    required_rows = (
        "changed_missing_facts",
        "changed_missing_documents",
        "changed_stale_evidence",
        "changed_conflicting_evidence",
        "required_confirmations",
        "blocked_actions",
        "next_safe_actions",
        "citation_references",
        "reviewer_holds",
    )

    for field in required_rows:
        packet = _valid_packet()
        packet["synthetic_replay_results"][0][field] = []

        errors = validate_agent_gap_analysis_delta_packet_v1(packet)

        assert any(f"{field} must contain at least one row" in error for error in errors)


def test_rejects_uncited_blocked_next_safe_and_reviewer_rows() -> None:
    packet = _valid_packet()
    result = packet["synthetic_replay_results"][0]
    result["blocked_actions"][0]["citation_references"] = []
    result["next_safe_actions"][0]["citation_references"] = []
    result["reviewer_holds"][0]["citation_references"] = []

    errors = validate_agent_gap_analysis_delta_packet_v1(packet)

    assert any("blocked_actions[0].citation_references" in error for error in errors)
    assert any("next_safe_actions[0].citation_references" in error for error in errors)
    assert any("reviewer_holds[0].citation_references" in error for error in errors)


def test_rejects_missing_validation_commands() -> None:
    packet = _valid_packet()
    packet["synthetic_replay_results"][0]["offline_validation_commands"] = []
    packet["validation_commands"] = []

    errors = validate_agent_gap_analysis_delta_packet_v1(packet)

    assert any("offline_validation_commands must contain only exact offline validation commands" in error for error in errors)
    assert "validation_commands must contain only the exact offline validation commands" in errors


def test_rejects_private_or_live_session_content() -> None:
    packet = _valid_packet()
    packet["synthetic_replay_results"][0]["auth_state"] = "cookie value"

    errors = validate_agent_gap_analysis_delta_packet_v1(packet)

    assert any("private-data key" in error for error in errors)
    assert any("private or live-session content" in error for error in errors)


def test_rejects_browser_raw_downloaded_artifacts_and_live_claims() -> None:
    packet = _valid_packet()
    result = packet["synthetic_replay_results"][0]
    result["browser_trace"] = "trace.zip"
    result["raw_crawl_output"] = "raw downloaded artifact"
    result["claim"] = "accessed DevHub during live crawl"

    errors = validate_agent_gap_analysis_delta_packet_v1(packet)

    assert any("private-data key" in error for error in errors)
    assert any("private or live-session content" in error for error in errors)
    assert any("live crawl or DevHub access claim" in error for error in errors)


def test_rejects_guarantees_completion_claims_and_active_mutation_flags() -> None:
    packet = _valid_packet()
    result = packet["synthetic_replay_results"][0]
    result["legal_note"] = "permit will be approved"
    result["completion_note"] = "official action completed"
    result["active_prompt_mutation"] = True

    errors = validate_agent_gap_analysis_delta_packet_v1(packet)

    assert any("legal or permitting guarantee" in error for error in errors)
    assert any("official-action completion claim" in error for error in errors)
    assert any("active mutation flag" in error for error in errors)


def test_rejects_next_safe_action_mutation_flags() -> None:
    packet = _valid_packet()
    action = deepcopy(packet["synthetic_replay_results"][0]["next_safe_actions"][0])
    action["requires_devhub"] = True
    action["uses_only_committed_fixtures"] = False
    packet["synthetic_replay_results"][0]["next_safe_actions"] = [action]

    errors = validate_agent_gap_analysis_delta_packet_v1(packet)

    assert any("requires_devhub must be false" in error for error in errors)
    assert any("uses_only_committed_fixtures must be true" in error for error in errors)
