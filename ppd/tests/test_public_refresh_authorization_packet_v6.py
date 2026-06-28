from __future__ import annotations

import copy
from pathlib import Path

from ppd.agent_readiness.public_refresh_authorization_packet_v6 import (
    ABORT_THRESHOLDS,
    EXACT_OFFLINE_VALIDATION_COMMANDS,
    VALIDATION_COMMANDS,
    assert_valid_public_refresh_authorization_packet_v6,
    build_public_refresh_authorization_packet_v6_from_fixture,
    validate_public_refresh_authorization_packet_v6,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "public_refresh_authorization_packet_v6"
SOURCE_FIXTURE = FIXTURE_DIR / "source_fixture.json"


def _valid_packet():
    return build_public_refresh_authorization_packet_v6_from_fixture(SOURCE_FIXTURE)


def _problem_text(packet):
    return "\n".join(validate_public_refresh_authorization_packet_v6(packet).problems)


def test_public_refresh_authorization_packet_v6_builds_from_fixture_inputs_only():
    packet = _valid_packet()

    assert packet["packet_type"] == "ppd.public_refresh_authorization_packet.v6"
    assert packet["mode"] == "fixture_first_public_refresh_authorization_packet_v6"
    assert packet["consumes_only"] == {
        "public_source_freshness_watchlist_v6_fixtures": True,
        "post_promotion_smoke_replay_v6_fixtures": True,
    }
    assert {row["fixture_role"] for row in packet["source_fixture_refs"]} == {
        "public_source_freshness_watchlist_v6",
        "post_promotion_smoke_replay_v6",
    }
    assert packet["boundaries"]["live_crawl_executed"] is False
    assert packet["boundaries"]["documents_downloaded"] is False
    assert packet["boundaries"]["raw_bodies_persisted"] is False
    assert packet["boundaries"]["devhub_opened"] is False
    assert packet["boundaries"]["private_documents_read"] is False
    assert packet["boundaries"]["active_mutation"] is False


def test_public_refresh_authorization_packet_v6_assembles_required_rows():
    packet = _valid_packet()

    assert [row["source_id"] for row in packet["live_crawl_deferral_criteria"]] == [
        "ppd-devhub-faq-placeholder",
        "ppd-submit-plans-online-placeholder",
        "ppd-fee-payment-guide-placeholder",
        "ppd-forms-index-placeholder",
    ]
    assert all(row["deferral_required"] is True for row in packet["live_crawl_deferral_criteria"])
    assert all(row["live_crawl_authorized"] is False for row in packet["live_crawl_deferral_criteria"])
    assert {row["group_id"] for row in packet["allowlisted_source_groups"]} == {
        "devhub_public_guidance",
        "file_preparation_and_upload_guidance",
        "fee_payment_public_guidance",
        "forms_index_and_public_forms",
    }
    assert all(row["robots_check_required"] is True for row in packet["robots_and_policy_preflight_checklist_rows"])
    assert all(row["policy_check_required"] is True for row in packet["robots_and_policy_preflight_checklist_rows"])
    assert all(row["preflight_completed"] is False for row in packet["robots_and_policy_preflight_checklist_rows"])
    assert all(row["crawl_authorized"] is False for row in packet["reviewer_authorization_placeholders"])
    assert all(row["authorization_status"] == "pending_manual_review" for row in packet["reviewer_authorization_placeholders"])


def test_public_refresh_authorization_packet_v6_keeps_processor_and_abort_boundaries():
    packet = _valid_packet()

    assert packet["abort_thresholds"] == ABORT_THRESHOLDS
    assert all(row["no_raw_body_persisted_required"] is True for row in packet["processor_handoff_manifest_expectations"])
    assert all(row["raw_artifact_ref_allowed"] is False for row in packet["processor_handoff_manifest_expectations"])
    assert all("no_raw_body_persisted" in row["expected_manifest_fields"] for row in packet["processor_handoff_manifest_expectations"])
    assert "Do not commit raw HTML" in packet["no_raw_body_persistence_reminders"][1]
    assert packet["processor_handoff_smoke_refs"]


def test_public_refresh_authorization_packet_v6_uses_exact_offline_validation_commands_only():
    packet = _valid_packet()

    assert packet["exact_offline_validation_commands"] == EXACT_OFFLINE_VALIDATION_COMMANDS
    assert packet["validation_commands"] == VALIDATION_COMMANDS
    flattened = " ".join(part for command in packet["exact_offline_validation_commands"] for part in command).lower()
    for forbidden in ["curl", "wget", "playwright", "devhub", "captcha", "mfa"]:
        assert forbidden not in flattened
    assert_valid_public_refresh_authorization_packet_v6(packet)
    assert validate_public_refresh_authorization_packet_v6(packet).valid is True


def test_public_refresh_authorization_packet_v6_rejects_missing_sections_and_unsafe_flags():
    for field in [
        "source_fixture_refs",
        "live_crawl_deferral_criteria",
        "allowlisted_source_groups",
        "robots_and_policy_preflight_checklist_rows",
        "no_raw_body_persistence_reminders",
        "processor_handoff_manifest_expectations",
        "reviewer_authorization_placeholders",
        "processor_handoff_smoke_refs",
    ]:
        packet = _valid_packet()
        packet[field] = []
        assert f"{field} must be a non-empty list" in _problem_text(packet)

    packet = _valid_packet()
    packet["boundaries"]["live_crawl_executed"] = True
    assert "boundaries must deny live crawling" in _problem_text(packet)

    packet = _valid_packet()
    packet["live_crawl_deferral_criteria"][0]["live_crawl_authorized"] = True
    assert "live_crawl_deferral_criteria[0].live_crawl_authorized must be false" in _problem_text(packet)

    packet = _valid_packet()
    packet["processor_handoff_manifest_expectations"][0]["raw_artifact_ref_allowed"] = True
    assert "processor_handoff_manifest_expectations[0] must not allow raw artifact refs or executed handoff" in _problem_text(packet)

    packet = _valid_packet()
    packet["unsafe_probe"] = copy.deepcopy({"session_cookie": "abc"})
    assert "must not contain private" in _problem_text(packet)
