from __future__ import annotations

import copy
from pathlib import Path

from ppd.agent_readiness.public_refresh_authorization_packet_v7 import (
    EXACT_OFFLINE_VALIDATION_COMMANDS,
    VALIDATION_COMMANDS,
    assert_valid_public_refresh_authorization_packet_v7,
    build_public_refresh_authorization_packet_v7_from_fixture,
    validate_public_refresh_authorization_packet_v7,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "public_refresh_authorization_packet_v7"
SOURCE_FIXTURE = FIXTURE_DIR / "source_fixture.json"


def _valid_packet():
    return build_public_refresh_authorization_packet_v7_from_fixture(SOURCE_FIXTURE)


def _problem_text(packet):
    return "\n".join(validate_public_refresh_authorization_packet_v7(packet).problems)


def test_public_refresh_authorization_packet_v7_consumes_only_watchlist_v6_fixtures():
    packet = _valid_packet()

    assert packet["packet_type"] == "ppd.public_refresh_authorization_packet.v7"
    assert packet["mode"] == "fixture_first_public_refresh_authorization_packet_v7"
    assert packet["consumes_only"] == {"public_source_freshness_watchlist_v6_fixtures": True}
    assert {row["fixture_role"] for row in packet["source_fixture_refs"]} == {"public_source_freshness_watchlist_v6"}
    assert packet["boundaries"]["live_crawl_executed"] is False
    assert packet["boundaries"]["documents_downloaded"] is False
    assert packet["boundaries"]["raw_bodies_persisted"] is False
    assert packet["boundaries"]["devhub_opened"] is False
    assert packet["boundaries"]["private_documents_read"] is False
    assert packet["boundaries"]["active_mutation"] is False


def test_public_refresh_authorization_packet_v7_assembles_reviewer_and_precondition_rows():
    packet = _valid_packet()

    expected_sources = [
        "ppd-devhub-faq-placeholder",
        "ppd-submit-plans-online-placeholder",
        "ppd-fee-payment-guide-placeholder",
        "ppd-forms-index-placeholder",
    ]
    assert [row["source_id"] for row in packet["human_reviewer_go_no_go_rows"]] == expected_sources
    assert all(row["default_decision"] == "no_go_hold" for row in packet["human_reviewer_go_no_go_rows"])
    assert all(row["go_allowed"] is False for row in packet["human_reviewer_go_no_go_rows"])
    assert all(row["human_reviewer_required"] is True for row in packet["human_reviewer_go_no_go_rows"])
    assert all(row["must_resolve_before_currentness_claim"] is True for row in packet["source_freshness_preconditions"])
    assert all(row["live_crawl_authorized"] is False for row in packet["source_freshness_preconditions"])


def test_public_refresh_authorization_packet_v7_carries_allowlist_raw_citation_and_rollback_rows():
    packet = _valid_packet()

    assert all(row["robots_check_required"] is True for row in packet["crawl_scope_allowlist_reminders"])
    assert all(row["policy_check_required"] is True for row in packet["crawl_scope_allowlist_reminders"])
    assert all(row["devhub_authenticated_scope_allowed"] is False for row in packet["crawl_scope_allowlist_reminders"])
    assert all(row["private_or_raw_artifact_scope_allowed"] is False for row in packet["crawl_scope_allowlist_reminders"])
    assert all(row["raw_artifact_ref_allowed"] is False for row in packet["raw_artifact_prohibition_notes"])
    assert all(row["no_raw_body_persisted_required"] is True for row in packet["raw_artifact_prohibition_notes"])
    assert all(row["agent_currentness_claims_blocked"] is True for row in packet["citation_repair_hold_carry_forward_rows"])
    assert all(row["consequential_action_claims_blocked"] is True for row in packet["citation_repair_hold_carry_forward_rows"])
    assert all(row["rollback_ready_before_future_refresh"] is True for row in packet["rollback_readiness_references"])


def test_public_refresh_authorization_packet_v7_uses_exact_offline_validation_commands_only():
    packet = _valid_packet()

    assert packet["exact_offline_validation_commands"] == EXACT_OFFLINE_VALIDATION_COMMANDS
    assert packet["validation_commands"] == VALIDATION_COMMANDS
    flattened = " ".join(part for command in packet["exact_offline_validation_commands"] for part in command).lower()
    for forbidden in ["curl", "wget", "playwright", "devhub", "captcha", "mfa"]:
        assert forbidden not in flattened
    assert_valid_public_refresh_authorization_packet_v7(packet)
    assert validate_public_refresh_authorization_packet_v7(packet).valid is True


def test_public_refresh_authorization_packet_v7_rejects_missing_sections_and_unsafe_flags():
    for field in [
        "source_fixture_refs",
        "human_reviewer_go_no_go_rows",
        "source_freshness_preconditions",
        "crawl_scope_allowlist_reminders",
        "raw_artifact_prohibition_notes",
        "citation_repair_hold_carry_forward_rows",
        "rollback_readiness_references",
    ]:
        packet = _valid_packet()
        packet[field] = []
        assert f"{field} must be a non-empty list" in _problem_text(packet)

    packet = _valid_packet()
    packet["boundaries"]["live_crawl_executed"] = True
    assert "boundaries must deny live crawling" in _problem_text(packet)

    packet = _valid_packet()
    packet["human_reviewer_go_no_go_rows"][0]["go_allowed"] = True
    assert "must default to no_go_hold with go_allowed false" in _problem_text(packet)

    packet = _valid_packet()
    packet["crawl_scope_allowlist_reminders"][0]["devhub_authenticated_scope_allowed"] = True
    assert "must exclude DevHub authenticated" in _problem_text(packet)

    packet = _valid_packet()
    packet["unsafe_probe"] = copy.deepcopy({"session_cookie": "abc"})
    assert "must not contain private" in _problem_text(packet)

    packet = _valid_packet()
    packet["source_fixture_refs"].append({"fixture_role": "post_promotion_smoke_replay_v6", "path": "fixture://blocked"})
    assert "source_fixture_refs must include only public_source_freshness_watchlist_v6 roles" in _problem_text(packet)
