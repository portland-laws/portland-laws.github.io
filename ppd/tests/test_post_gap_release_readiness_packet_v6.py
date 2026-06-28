import copy
from pathlib import Path

from ppd.agent_readiness.post_gap_release_readiness_packet_v6 import (
    EXACT_OFFLINE_VALIDATION_COMMANDS,
    assert_valid_post_gap_release_readiness_packet_v6,
    build_post_gap_release_readiness_packet_v6_from_fixture,
    validate_post_gap_release_readiness_packet_v6,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "post_gap_release_readiness_v6"
REPLAY_FIXTURE = FIXTURE_DIR / "post_gap_agent_readiness_replay_v6.json"


def _valid_packet():
    return build_post_gap_release_readiness_packet_v6_from_fixture(REPLAY_FIXTURE)


def _problem_text(packet):
    return "\n".join(validate_post_gap_release_readiness_packet_v6(packet).problems)


def test_post_gap_release_readiness_packet_v6_builds_from_replay_fixture_only():
    packet = _valid_packet()

    assert packet["packet_type"] == "ppd.post_gap_release_readiness_packet.v6"
    assert packet["fixture_first"] is True
    assert packet["post_gap_readiness_replay_fixtures_only"] is True
    assert packet["consumes_only"] == {
        "post_gap_agent_readiness_replay_v6_fixtures": True,
        "replay_packet_version": "post_gap_agent_readiness_replay_v6",
    }
    assert packet["source_fixture_refs"] == [
        {
            "fixture_role": "post_gap_agent_readiness_replay_v6",
            "path": REPLAY_FIXTURE.as_posix(),
        }
    ]

    decision = packet["reviewer_go_no_go_rows"][0]
    assert decision["recommendation"] == "NO_GO"
    assert decision["activation_allowed"] is False
    assert decision["manual_reviewer_final_decision_required"] is True

    hold_types = {row["hold_type"] for row in packet["unresolved_hold_inventory"]}
    assert {"missing_fact", "stale_evidence"}.issubset(hold_types)
    assert any(row["source_prompt_id"] == "q01_property_address" for row in packet["unresolved_hold_inventory"])
    assert any(row.get("evidence_id") == "ev_stale_fee_table" for row in packet["unresolved_hold_inventory"])

    assert packet["reversible_draft_readiness_summaries"] == [
        {
            "summary_id": "draft_preview-req_draft",
            "request_id": "req_draft",
            "route": "reversible_local_draft_preview",
            "ready_for_reviewer_preview_only": True,
            "official_action_allowed": False,
        }
    ]
    assert packet["local_pdf_preview_readiness_summaries"] == [
        {
            "summary_id": "pdf_preview-req_pdf",
            "request_id": "req_pdf",
            "route": "local_pdf_preview_only",
            "ready_for_reviewer_preview_only": True,
            "official_action_allowed": False,
        }
    ]
    assert packet["refused_consequential_action_summaries"][0]["request_id"] == "req_official_record_change"
    assert packet["refused_financial_action_summaries"][0]["request_id"] == "req_financial_commitment"
    assert all(row["official_action_completed"] is False for row in packet["refused_consequential_action_summaries"])
    assert all(row["official_action_completed"] is False for row in packet["refused_financial_action_summaries"])

    journal_events = {row["journal_event"] for row in packet["journal_dry_run_coverage_refs"]}
    assert "offline_validation_commands_reported" in journal_events
    assert "route_selected" in journal_events
    assert all(row["dry_run_only"] is True for row in packet["journal_dry_run_coverage_refs"])

    citation_urls = {row["url"] for row in packet["citation_coverage_notes"]}
    assert "fixture://post_gap_agent_readiness_v6/residential_checklist_stub.pdf" in citation_urls
    assert "fixture://post_gap_agent_readiness_v6/stale_fee_table.html" in citation_urls
    assert all(row["fixture_citation_only"] is True for row in packet["citation_coverage_notes"])

    assert packet["rollback_owner_placeholders"] == [
        {
            "placeholder_id": "rollback-owner-post-gap-release-readiness-v6",
            "owner": "REVIEWER_TBD",
            "assignment_required_before": "release_signoff",
            "active_state_changed": False,
        }
    ]
    assert {row["notification_status"] for row in packet["agent_notification_rows"]} == {"draft_note_only"}
    assert all(row["send_or_submit_allowed"] is False for row in packet["agent_notification_rows"])


def test_post_gap_release_readiness_packet_v6_keeps_boundary_flags_and_commands_offline():
    packet = _valid_packet()

    assert packet["offline_validation_commands"] == EXACT_OFFLINE_VALIDATION_COMMANDS
    flattened = " ".join(part for command in packet["offline_validation_commands"] for part in command).lower()
    for forbidden in ["curl", "wget", "playwright", "devhub", "captcha", "mfa"]:
        assert forbidden not in flattened

    for flag in [
        "active_guardrail_mutation",
        "active_release_state_mutation",
        "active_mutation",
        "activation_executed",
        "opens_devhub",
        "reads_private_documents",
        "uploads",
        "submits",
        "certifies",
        "pays",
        "schedules",
        "legal_or_permitting_guarantee",
    ]:
        assert packet[flag] is False

    assert_valid_post_gap_release_readiness_packet_v6(packet)
    result = validate_post_gap_release_readiness_packet_v6(packet)
    assert result.valid is True
    assert result.problems == ()


def test_post_gap_release_readiness_packet_v6_rejects_missing_required_sections():
    required_fields = [
        "source_fixture_refs",
        "reviewer_go_no_go_rows",
        "unresolved_hold_inventory",
        "reversible_draft_readiness_summaries",
        "local_pdf_preview_readiness_summaries",
        "refused_consequential_action_summaries",
        "refused_financial_action_summaries",
        "journal_dry_run_coverage_refs",
        "citation_coverage_notes",
        "rollback_owner_placeholders",
        "agent_notification_rows",
        "offline_validation_commands",
    ]

    for field in required_fields:
        packet = _valid_packet()
        packet[field] = []
        problems = _problem_text(packet)
        assert f"{field} must be a non-empty list" in problems


def test_post_gap_release_readiness_packet_v6_rejects_missing_replay_reference_details():
    packet = _valid_packet()
    packet["source_fixture_refs"] = [{"fixture_role": "wrong", "path": "fixture.json"}]
    packet["consumes_only"] = {"post_gap_agent_readiness_replay_v6_fixtures": False}

    problems = _problem_text(packet)

    assert "source_fixture_refs must include post_gap_agent_readiness_replay_v6 fixture path" in problems
    assert "consumes_only must require post-gap agent readiness replay v6 fixtures" in problems


def test_post_gap_release_readiness_packet_v6_rejects_malformed_required_rows():
    packet = _valid_packet()
    packet["reviewer_go_no_go_rows"][0]["activation_allowed"] = True
    packet["unresolved_hold_inventory"] = [packet["unresolved_hold_inventory"][0]]
    packet["unresolved_hold_inventory"][0]["release_blocked"] = False
    packet["reversible_draft_readiness_summaries"][0]["official_action_allowed"] = True
    packet["local_pdf_preview_readiness_summaries"][0]["ready_for_reviewer_preview_only"] = False
    packet["refused_consequential_action_summaries"][0]["official_action_completed"] = True
    packet["refused_financial_action_summaries"][0]["manual_handoff_required"] = False
    packet["journal_dry_run_coverage_refs"][0]["dry_run_only"] = False
    packet["citation_coverage_notes"][0]["fixture_citation_only"] = False
    packet["rollback_owner_placeholders"][0]["owner"] = "release-bot"
    packet["agent_notification_rows"][0]["send_or_submit_allowed"] = True

    problems = _problem_text(packet)

    assert "reviewer_go_no_go_rows[0].activation_allowed must be false" in problems
    assert "unresolved_hold_inventory must include a stale_evidence hold" in problems
    assert "unresolved_hold_inventory[0].release_blocked must be true" in problems
    assert "reversible_draft_readiness_summaries[0].official_action_allowed must be false" in problems
    assert "local_pdf_preview_readiness_summaries[0].ready_for_reviewer_preview_only must be true" in problems
    assert "refused_consequential_action_summaries[0].official_action_completed must be false" in problems
    assert "refused_financial_action_summaries[0].manual_handoff_required must be true" in problems
    assert "journal_dry_run_coverage_refs[0].dry_run_only must be true" in problems
    assert "citation_coverage_notes[0].fixture_citation_only must be true" in problems
    assert "rollback_owner_placeholders[0].owner must be REVIEWER_TBD" in problems
    assert "agent_notification_rows[0].send_or_submit_allowed must be false" in problems


def test_post_gap_release_readiness_packet_v6_rejects_forbidden_claims_and_artifacts():
    forbidden_cases = [
        ({"operator_note": "live activation enabled for release"}, "live_activation_claim"),
        ({"artifact_ref": "/home/example/.cache/devhub/auth_state.json"}, "private/session/auth artifact"),
        ({"session_note": "session cookie abc123"}, "private_session_auth_artifact"),
        ({"completion_note": "submitted permit and official action completed"}, "official_action_completion_claim"),
        ({"guarantee_note": "permit guaranteed after this packet"}, "legal_or_permitting_guarantee"),
        ({"nested": {"active_mutation": True}}, "active mutation flag is not allowed"),
        ({"mutation_note": "active mutation enabled"}, "active_mutation_flag"),
    ]

    for injected, expected in forbidden_cases:
        packet = _valid_packet()
        packet["unsafe_fixture_probe"] = copy.deepcopy(injected)
        assert expected in _problem_text(packet)


def test_post_gap_release_readiness_packet_v6_rejects_live_and_action_flags():
    for flag in [
        "active_guardrail_mutation",
        "active_release_state_mutation",
        "active_mutation",
        "activation_executed",
        "opens_devhub",
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
        problems = _problem_text(packet)
        assert f"{flag} must be false" in problems
