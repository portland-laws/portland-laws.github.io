from __future__ import annotations

import copy
from pathlib import Path

from ppd.agent_readiness.post_promotion_smoke_replay_v6 import (
    EXACT_OFFLINE_VALIDATION_COMMANDS,
    VALIDATION_COMMANDS,
    assert_valid_post_promotion_smoke_replay_v6,
    build_post_promotion_smoke_replay_v6_from_fixture,
    validate_post_promotion_smoke_replay_v6,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "post_promotion_smoke_replay_v6"
SOURCE_FIXTURE = FIXTURE_DIR / "source_fixture.json"


def _valid_packet():
    return build_post_promotion_smoke_replay_v6_from_fixture(SOURCE_FIXTURE)


def _problem_text(packet):
    return "\n".join(validate_post_promotion_smoke_replay_v6(packet).problems)


def test_post_promotion_smoke_replay_v6_builds_from_inactive_fixtures_only():
    packet = _valid_packet()

    assert packet["packet_type"] == "ppd.post_promotion_smoke_replay.v6"
    assert packet["mode"] == "fixture_first_post_promotion_smoke_replay_v6"
    assert packet["consumes_only"] == {
        "inactive_guardrail_promotion_rehearsal_v6_fixtures": True,
        "inactive_guardrail_placeholder_fixtures": True,
        "promotion_packet_type": "ppd.inactive_guardrail_promotion_rehearsal.v6",
        "promotion_packet_version": "v6",
    }
    assert {row["fixture_role"] for row in packet["source_fixture_refs"]} == {
        "inactive_guardrail_promotion_rehearsal_v6",
        "inactive_guardrail_placeholder_fixture",
    }
    assert packet["boundaries"]["fixture_first"] is True
    assert packet["boundaries"]["guardrails_activated"] is False
    assert packet["boundaries"]["devhub_opened"] is False
    assert packet["boundaries"]["live_crawling_enabled"] is False
    assert packet["boundaries"]["private_documents_read"] is False

    assert packet["inactive_guardrail_placeholder_checks"][0]["placeholder_status"] == "inactive_placeholder_only"
    assert packet["inactive_guardrail_placeholder_checks"][0]["activation_allowed"] is False
    assert packet["lookup_health_checks"][0]["lookup_status"] == "healthy_fixture_lookup"
    assert packet["lookup_health_checks"][0]["fixture_lookup_only"] is True
    assert all(row["unresolved_hold_visible"] is True for row in packet["unresolved_hold_display_checks"])
    assert all(row["blocks_agent_ready"] is True for row in packet["unresolved_hold_display_checks"])
    assert packet["stale_source_stop_gates"]
    assert all(row["stop_gate_triggered"] is True for row in packet["stale_source_stop_gates"])
    assert all(row["source_may_be_used_for_final_answer"] is False for row in packet["stale_source_stop_gates"])
    assert packet["exact_confirmation_checkpoint_checks"][0]["exact_confirmation_required"] is True
    assert packet["exact_confirmation_checkpoint_checks"][0]["checkpoint_executed"] is False

    refused_categories = {row["action_category"] for row in packet["refused_action_checks"]}
    assert refused_categories == {"consequential", "financial"}
    assert all(row["refused"] is True for row in packet["refused_action_checks"])
    assert all(row["official_action_completed"] is False for row in packet["refused_action_checks"])
    assert packet["reversible_draft_only_routing_checks"][0]["route"] == "reversible_draft_only"
    assert packet["reversible_draft_only_routing_checks"][0]["official_action_allowed"] is False
    assert packet["local_pdf_preview_routing_checks"][0]["route"] == "local_pdf_preview_only"
    assert packet["local_pdf_preview_routing_checks"][0]["upload_allowed"] is False
    assert packet["rollback_trigger_visibility_checks"][0]["rollback_trigger_visible"] is True
    assert packet["manual_handoff_reminders"]
    assert all(row["handoff_status"] == "pending_manual_handoff" for row in packet["manual_handoff_reminders"])

    expectation_ids = {row["expectation_id"] for row in packet["smoke_expectations"]}
    assert "lookup-health-check" in expectation_ids
    assert "exact-offline-validation-command-check" in expectation_ids


def test_post_promotion_smoke_replay_v6_keeps_exact_offline_commands_only():
    packet = _valid_packet()

    assert packet["exact_offline_validation_commands"] == EXACT_OFFLINE_VALIDATION_COMMANDS
    assert packet["validation_commands"] == VALIDATION_COMMANDS
    flattened = " ".join(part for command in packet["exact_offline_validation_commands"] for part in command).lower()
    for forbidden in ["curl", "wget", "playwright", "devhub", "captcha", "mfa"]:
        assert forbidden not in flattened

    assert_valid_post_promotion_smoke_replay_v6(packet)
    result = validate_post_promotion_smoke_replay_v6(packet)
    assert result.valid is True
    assert result.problems == ()


def test_post_promotion_smoke_replay_v6_rejects_missing_required_sections():
    for field in [
        "source_fixture_refs",
        "inactive_guardrail_placeholder_checks",
        "lookup_health_checks",
        "unresolved_hold_display_checks",
        "stale_source_stop_gates",
        "exact_confirmation_checkpoint_checks",
        "refused_action_checks",
        "reversible_draft_only_routing_checks",
        "local_pdf_preview_routing_checks",
        "rollback_trigger_visibility_checks",
        "manual_handoff_reminders",
        "smoke_expectations",
        "exact_offline_validation_commands",
        "validation_commands",
    ]:
        packet = _valid_packet()
        packet[field] = []
        assert f"{field} must be a non-empty list" in _problem_text(packet)


def test_post_promotion_smoke_replay_v6_rejects_malformed_smoke_rows():
    packet = _valid_packet()
    packet["lookup_health_checks"][0]["fixture_lookup_only"] = False
    packet["unresolved_hold_display_checks"][0]["unresolved_hold_visible"] = False
    packet["stale_source_stop_gates"][0]["stop_gate_triggered"] = False
    packet["exact_confirmation_checkpoint_checks"][0]["checkpoint_executed"] = True
    packet["refused_action_checks"][0]["refused"] = False
    packet["reversible_draft_only_routing_checks"][0]["official_action_allowed"] = True
    packet["local_pdf_preview_routing_checks"][0]["upload_allowed"] = True
    packet["rollback_trigger_visibility_checks"][0]["active_state_changed"] = True
    packet["manual_handoff_reminders"][0]["display_required"] = False

    problems = _problem_text(packet)

    assert "lookup_health_checks[0].fixture_lookup_only must be true" in problems
    assert "unresolved_hold_display_checks[0].unresolved_hold_visible must be true" in problems
    assert "stale_source_stop_gates[0].stop_gate_triggered must be true" in problems
    assert "exact_confirmation_checkpoint_checks[0].checkpoint_executed must be false" in problems
    assert "refused_action_checks[0].refused must be true" in problems
    assert "reversible_draft_only_routing_checks[0].official_action_allowed must be false" in problems
    assert "local_pdf_preview_routing_checks[0].upload_allowed must be false" in problems
    assert "rollback_trigger_visibility_checks[0].active_state_changed must be false" in problems
    assert "manual_handoff_reminders[0].display_required must be true" in problems


def test_post_promotion_smoke_replay_v6_rejects_live_action_flags_and_forbidden_claims():
    for flag in [
        "active_guardrail_mutation",
        "active_release_state_mutation",
        "active_mutation",
        "guardrails_activated",
        "promotion_executed",
        "activation_executed",
        "devhub_opened",
        "live_crawling_enabled",
        "private_documents_read",
        "uploads_performed",
        "submissions_performed",
        "certifications_performed",
        "payments_performed",
        "scheduling_performed",
        "legal_or_permitting_guarantees_made",
    ]:
        packet = _valid_packet()
        packet[flag] = True
        assert f"{flag} must not be true" in _problem_text(packet)

    forbidden_cases = [
        ({"operator_note": "guardrails activated for release"}, "prohibited activation"),
        ({"operator_note": "opened DevHub and submitted permit"}, "prohibited activation"),
        ({"credential_token": "abc"}, "must not contain private"),
        ({"guarantee_note": "permit guaranteed"}, "prohibited activation"),
    ]
    for injected, expected in forbidden_cases:
        packet = _valid_packet()
        packet["unsafe_fixture_probe"] = copy.deepcopy(injected)
        assert expected in _problem_text(packet)
