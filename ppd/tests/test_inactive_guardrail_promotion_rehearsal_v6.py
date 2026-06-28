from __future__ import annotations

import copy
from pathlib import Path

from ppd.agent_readiness.inactive_guardrail_promotion_rehearsal_v6 import (
    EXACT_OFFLINE_VALIDATION_COMMANDS,
    VALIDATION_COMMANDS,
    assert_valid_inactive_guardrail_promotion_rehearsal_v6,
    build_inactive_guardrail_promotion_rehearsal_v6_from_fixture,
    validate_inactive_guardrail_promotion_rehearsal_v6,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "inactive_guardrail_promotion_rehearsal_v6"
POST_GAP_PACKET_FIXTURE = FIXTURE_DIR / "post_gap_release_readiness_packet_v6.json"


def _valid_packet():
    return build_inactive_guardrail_promotion_rehearsal_v6_from_fixture(POST_GAP_PACKET_FIXTURE)


def _problem_text(packet):
    return "\n".join(validate_inactive_guardrail_promotion_rehearsal_v6(packet).problems)


def test_inactive_guardrail_promotion_rehearsal_v6_builds_from_post_gap_packet_fixture_only():
    packet = _valid_packet()

    assert packet["packet_type"] == "ppd.inactive_guardrail_promotion_rehearsal.v6"
    assert packet["fixture_first"] is True
    assert packet["inactive_candidate_only"] is True
    assert packet["post_gap_release_readiness_packet_v6_fixtures_only"] is True
    assert packet["consumes_only"] == {
        "post_gap_release_readiness_packet_v6_fixtures": True,
        "packet_type": "ppd.post_gap_release_readiness_packet.v6",
        "packet_version": "v6",
    }
    assert packet["source_fixture_refs"] == [
        {"fixture_role": "post_gap_release_readiness_packet_v6", "path": POST_GAP_PACKET_FIXTURE.as_posix()}
    ]

    rows = packet["inactive_promotion_candidate_rows"]
    assert len(rows) == 1
    assert rows[0]["candidate_status"] == "inactive_candidate_only"
    assert rows[0]["activation_allowed"] is False
    assert rows[0]["promotion_allowed"] is False
    assert rows[0]["source_unresolved_hold_count"] == 5
    assert rows[0]["source_fixture_citation_count"] == 2

    candidate_id = rows[0]["candidate_id"]
    assert packet["reviewer_controlled_signoff_placeholders"] == [
        {
            "placeholder_id": f"signoff::{candidate_id}",
            "candidate_id": candidate_id,
            "signoff_status": "pending_manual_review",
            "reviewer": "REVIEWER_TBD",
            "reviewed_at": "",
            "activation_allowed": False,
        }
    ]
    assert packet["source_freshness_clearance_prerequisites"][0]["all_sources_confirmed_fresh"] is False
    assert packet["source_freshness_clearance_prerequisites"][0]["activation_allowed"] is False
    assert {
        row["hold_type"] for row in packet["unresolved_hold_propagation_rows"]
    } == {"missing_fact", "stale_evidence"}
    assert all(row["promotion_blocked"] is True for row in packet["unresolved_hold_propagation_rows"])
    assert packet["rollback_checkpoint_rows"][0]["active_state_changed"] is False
    assert packet["post_promotion_smoke_replay_expectations"][0]["requires_separate_post_promotion_task"] is True
    assert "offline_validation_commands_reported" in packet["post_promotion_smoke_replay_expectations"][0]["expected_journal_events"]
    assert packet["agent_api_compatibility_reminders"][0]["preserve_missing_information_contract"] is True
    assert packet["agent_api_compatibility_reminders"][0]["preserve_refused_action_contract"] is True
    assert packet["agent_api_compatibility_reminders"][0]["active_api_change_allowed"] is False
    assert packet["monitoring_handoff_rows"][0]["handoff_status"] == "planned_not_started"


def test_inactive_guardrail_promotion_rehearsal_v6_keeps_boundary_flags_and_commands_offline():
    packet = _valid_packet()

    assert packet["offline_validation_commands"] == EXACT_OFFLINE_VALIDATION_COMMANDS
    assert packet["validation_commands"] == VALIDATION_COMMANDS
    flattened = " ".join(part for command in packet["offline_validation_commands"] for part in command).lower()
    for forbidden in ["curl", "wget", "playwright", "devhub", "captcha", "mfa"]:
        assert forbidden not in flattened

    for flag in [
        "active_guardrail_mutation",
        "active_guardrail_bundle_mutation",
        "active_prompt_mutation",
        "active_process_model_mutation",
        "active_requirement_mutation",
        "active_source_mutation",
        "active_devhub_surface_mutation",
        "active_release_state_mutation",
        "active_mutation",
        "guardrails_changed",
        "guardrail_bundles_changed",
        "promotion_executed",
        "activation_executed",
        "opens_devhub",
        "crawls_live_sites",
        "reads_private_documents",
        "uploads",
        "submits",
        "certifies",
        "pays",
        "schedules",
        "legal_or_permitting_guarantee",
    ]:
        assert packet[flag] is False

    assert_valid_inactive_guardrail_promotion_rehearsal_v6(packet)
    result = validate_inactive_guardrail_promotion_rehearsal_v6(packet)
    assert result.valid is True
    assert result.problems == ()


def test_inactive_guardrail_promotion_rehearsal_v6_rejects_missing_required_sections():
    for field in [
        "source_fixture_refs",
        "inactive_promotion_candidate_rows",
        "reviewer_controlled_signoff_placeholders",
        "source_freshness_clearance_prerequisites",
        "unresolved_hold_propagation_rows",
        "rollback_checkpoint_rows",
        "post_promotion_smoke_replay_expectations",
        "agent_api_compatibility_reminders",
        "monitoring_handoff_rows",
        "offline_validation_commands",
        "validation_commands",
    ]:
        packet = _valid_packet()
        packet[field] = []
        assert f"{field} must be a non-empty list" in _problem_text(packet)


def test_inactive_guardrail_promotion_rehearsal_v6_rejects_malformed_rows():
    packet = _valid_packet()
    packet["inactive_promotion_candidate_rows"][0]["candidate_status"] = "active"
    packet["inactive_promotion_candidate_rows"][0]["activation_allowed"] = True
    packet["inactive_promotion_candidate_rows"][0]["promotion_allowed"] = True
    packet["reviewer_controlled_signoff_placeholders"][0]["signoff_status"] = "approved"
    packet["source_freshness_clearance_prerequisites"][0]["all_sources_confirmed_fresh"] = True
    packet["unresolved_hold_propagation_rows"][0]["promotion_blocked"] = False
    packet["rollback_checkpoint_rows"][0]["active_state_changed"] = True
    packet["post_promotion_smoke_replay_expectations"][0]["requires_separate_post_promotion_task"] = False
    packet["agent_api_compatibility_reminders"][0]["active_api_change_allowed"] = True
    packet["monitoring_handoff_rows"][0]["handoff_status"] = "running"

    problems = _problem_text(packet)

    assert "inactive_promotion_candidate_rows[0].candidate_status must remain inactive_candidate_only" in problems
    assert "inactive_promotion_candidate_rows[0].activation_allowed must be false" in problems
    assert "inactive_promotion_candidate_rows[0].promotion_allowed must be false" in problems
    assert "reviewer_controlled_signoff_placeholders[0].signoff_status must be pending_manual_review" in problems
    assert "source_freshness_clearance_prerequisites[0].all_sources_confirmed_fresh must be false" in problems
    assert "unresolved_hold_propagation_rows[0].promotion_blocked must be true" in problems
    assert "rollback_checkpoint_rows[0].active_state_changed must be false" in problems
    assert "post_promotion_smoke_replay_expectations[0].requires_separate_post_promotion_task must be true" in problems
    assert "agent_api_compatibility_reminders[0].active_api_change_allowed must be false" in problems
    assert "monitoring_handoff_rows[0].handoff_status must be planned_not_started" in problems


def test_inactive_guardrail_promotion_rehearsal_v6_rejects_live_action_flags_and_forbidden_claims():
    for flag in [
        "active_guardrail_mutation",
        "active_release_state_mutation",
        "active_mutation",
        "promotion_executed",
        "activation_executed",
        "opens_devhub",
        "crawls_live_sites",
        "reads_private_documents",
        "uploads",
        "submits",
        "certifies",
        "pays",
        "schedules",
        "legal_or_permitting_guarantee",
    ]:
        packet = _valid_packet()
        packet[flag] = True
        assert f"{flag} must be false" in _problem_text(packet)

    forbidden_cases = [
        ({"operator_note": "guardrails activated for release"}, "must not claim live activation"),
        ({"operator_note": "opened DevHub and submitted permit"}, "must not claim live activation"),
        ({"credential_token": "abc"}, "must not include private"),
        ({"guarantee_note": "permit guaranteed"}, "must not claim live activation"),
    ]
    for injected, expected in forbidden_cases:
        packet = _valid_packet()
        packet["unsafe_fixture_probe"] = copy.deepcopy(injected)
        assert expected in _problem_text(packet)
