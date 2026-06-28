from __future__ import annotations

import copy
from pathlib import Path

from ppd.agent_readiness.public_source_recrawl_preflight_queue_v7 import (
    EXACT_OFFLINE_VALIDATION_COMMANDS,
    VALIDATION_COMMANDS,
    assert_valid_public_source_recrawl_preflight_queue_v7,
    build_public_source_recrawl_preflight_queue_v7_from_fixture,
    validate_public_source_recrawl_preflight_queue_v7,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "public_source_recrawl_preflight_queue_v7"
SOURCE_FIXTURE = FIXTURE_DIR / "source_fixture.json"


def _valid_packet():
    return build_public_source_recrawl_preflight_queue_v7_from_fixture(SOURCE_FIXTURE)


def _problem_text(packet):
    return "\n".join(validate_public_source_recrawl_preflight_queue_v7(packet).problems)


def test_public_source_recrawl_preflight_queue_v7_consumes_only_authorization_allowlist_and_robots_fixtures():
    packet = _valid_packet()

    assert packet["packet_type"] == "ppd.public_source_recrawl_preflight_queue.v7"
    assert packet["mode"] == "fixture_first_public_source_recrawl_preflight_queue_v7"
    assert packet["consumes_only"] == {
        "public_refresh_authorization_packet_v7_fixtures": True,
        "committed_allowlist_fixtures": True,
        "committed_robots_policy_fixtures": True,
    }
    assert {row["fixture_role"] for row in packet["source_fixture_refs"]} == {
        "public_refresh_authorization_packet_v7",
        "committed_allowlist",
        "committed_robots_policy",
    }
    assert packet["boundaries"]["live_crawl_executed"] is False
    assert packet["boundaries"]["network_requests_performed"] is False
    assert packet["boundaries"]["documents_downloaded"] is False
    assert packet["boundaries"]["raw_bodies_persisted"] is False
    assert packet["boundaries"]["devhub_opened"] is False
    assert packet["boundaries"]["active_mutation"] is False


def test_public_source_recrawl_preflight_queue_v7_assembles_queue_redirect_skip_and_policy_rows():
    packet = _valid_packet()

    assert [row["source_id"] for row in packet["canonical_url_queue_rows"]] == [
        "ppd-devhub-faq-placeholder",
        "ppd-submit-plans-online-placeholder",
    ]
    assert all(row["request_method"] == "GET" for row in packet["canonical_url_queue_rows"])
    assert all(row["metadata_only"] is True for row in packet["canonical_url_queue_rows"])
    assert all(row["no_raw_body_persisted"] is True for row in packet["canonical_url_queue_rows"])
    assert all(row["live_network_invoked"] is False for row in packet["canonical_url_queue_rows"])
    assert all(row["raw_download_invoked"] is False for row in packet["canonical_url_queue_rows"])

    skip_by_source = {row["source_id"]: row["skip_reason"] for row in packet["skip_reason_rows"]}
    assert skip_by_source == {
        "ppd-fee-payment-guide-placeholder": "robots_policy_disallowed",
        "ppd-forms-index-placeholder": "source_not_stale_in_authorization_fixture",
    }
    assert len(packet["redirect_expectation_placeholders"]) == packet["authorization_source_count"]
    assert all(row["live_redirect_resolution_performed"] is False for row in packet["redirect_expectation_placeholders"])
    assert all(row["final_url_must_remain_official_public_anchor"] is True for row in packet["redirect_expectation_placeholders"])

    decisions = {row["source_id"]: row for row in packet["host_policy_decisions"]}
    assert decisions["ppd-devhub-faq-placeholder"]["decision"] == "allowed"
    assert decisions["ppd-submit-plans-online-placeholder"]["decision"] == "allowed"
    assert decisions["ppd-fee-payment-guide-placeholder"]["robots_allowed"] is False


def test_public_source_recrawl_preflight_queue_v7_rate_limits_and_processor_handoff_are_offline_only():
    packet = _valid_packet()

    assert packet["rate_limit_reminders"] == [
        {
            "rate_limit_reminder_id": "rate-limit::www.portland.gov",
            "host": "www.portland.gov",
            "crawl_delay_seconds": 2,
            "reminder": "Honor committed robots-policy crawl delay and operator-approved rate limits before any future live public recrawl.",
            "live_crawl_authorized": False,
        }
    ]
    notes = {row["source_id"]: row for row in packet["processor_handoff_eligibility_notes"]}
    assert notes["ppd-devhub-faq-placeholder"]["processor_handoff_eligible"] is True
    assert notes["ppd-submit-plans-online-placeholder"]["processor_handoff_eligible"] is True
    assert notes["ppd-fee-payment-guide-placeholder"]["processor_handoff_eligible"] is False
    assert notes["ppd-forms-index-placeholder"]["processor_handoff_eligible"] is False
    assert all(row["metadata_only_manifest_required"] is True for row in notes.values())
    assert all(row["raw_artifact_ref_allowed"] is False for row in notes.values())
    assert all(row["requires_separate_operator_approval_before_live_processor_run"] is True for row in notes.values())


def test_public_source_recrawl_preflight_queue_v7_uses_exact_offline_validation_commands_only():
    packet = _valid_packet()

    assert packet["exact_offline_validation_commands"] == EXACT_OFFLINE_VALIDATION_COMMANDS
    assert packet["validation_commands"] == VALIDATION_COMMANDS
    flattened = " ".join(part for command in packet["exact_offline_validation_commands"] for part in command).lower()
    for forbidden in ["curl", "wget", "playwright", "devhub", "captcha", "mfa"]:
        assert forbidden not in flattened
    assert_valid_public_source_recrawl_preflight_queue_v7(packet)
    assert validate_public_source_recrawl_preflight_queue_v7(packet).valid is True


def test_public_source_recrawl_preflight_queue_v7_rejects_missing_sections_and_unsafe_flags():
    for field in [
        "canonical_url_queue_rows",
        "redirect_expectation_placeholders",
        "skip_reason_rows",
        "host_policy_decisions",
        "rate_limit_reminders",
        "processor_handoff_eligibility_notes",
    ]:
        packet = _valid_packet()
        packet[field] = []
        assert f"{field} must be a non-empty list" in _problem_text(packet)

    packet = _valid_packet()
    packet["boundaries"]["live_crawl_executed"] = True
    assert "boundaries must deny live crawl" in _problem_text(packet)

    packet = _valid_packet()
    packet["canonical_url_queue_rows"][0]["request_method"] = "POST"
    packet["canonical_url_queue_rows"][0]["live_network_invoked"] = True
    packet["redirect_expectation_placeholders"][0]["live_redirect_resolution_performed"] = True
    packet["skip_reason_rows"][0]["processor_handoff_allowed"] = True
    packet["rate_limit_reminders"][0]["live_crawl_authorized"] = True
    errors = _problem_text(packet)
    assert "canonical_url_queue_rows[0].request_method must be GET" in errors
    assert "canonical_url_queue_rows[0].live_network_invoked must be false" in errors
    assert "redirect_expectation_placeholders[0].live_redirect_resolution_performed must be false" in errors
    assert "skip_reason_rows[0] must deny metadata capture and processor handoff" in errors
    assert "rate_limit_reminders[0].live_crawl_authorized must be false" in errors

    packet = _valid_packet()
    packet["unsafe_note"] = "live crawl completed and opened DevHub"
    assert "must not claim live crawl" in _problem_text(packet)

    packet = _valid_packet()
    packet["source_fixture_refs"] = copy.deepcopy(packet["source_fixture_refs"][:2])
    assert "source_fixture_refs must include only" in _problem_text(packet)
