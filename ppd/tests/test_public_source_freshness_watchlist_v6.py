from __future__ import annotations

from pathlib import Path

import pytest

from ppd.agent_readiness.public_source_freshness_watchlist_v6 import (
    OFFLINE_VALIDATION_COMMANDS,
    PACKET_VERSION,
    build_watchlist_from_files,
    validate_watchlist,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "public_source_freshness_watchlist_v6"
REGISTRY_FIXTURE = FIXTURE_DIR / "committed_public_source_registry_v6.json"
PRIOR_REFRESH_FIXTURE = FIXTURE_DIR / "prior_refresh_fixture_references_v6.json"


def test_builds_fixture_first_public_source_freshness_watchlist_v6() -> None:
    packet = build_watchlist_from_files(REGISTRY_FIXTURE, PRIOR_REFRESH_FIXTURE)

    assert packet["packet_version"] == PACKET_VERSION
    assert packet["fixture_first"] is True
    assert packet["source_boundaries"] == {
        "live_crawl": False,
        "document_download": False,
        "raw_body_storage": False,
        "devhub_opened": False,
        "private_documents_read": False,
        "official_action_taken": False,
        "legal_or_permitting_guarantee": False,
    }
    assert packet["offline_validation_commands"] == OFFLINE_VALIDATION_COMMANDS
    assert packet["freshness_thresholds_days"]["daily"] == 2
    assert packet["freshness_thresholds_days"]["weekly"] == 14


def test_watchlist_rows_include_thresholds_holds_references_and_reviewer_escalations() -> None:
    packet = build_watchlist_from_files(REGISTRY_FIXTURE, PRIOR_REFRESH_FIXTURE)
    rows = packet["watchlist_rows"]

    assert [row["rank"] for row in rows] == [1, 2, 3, 4]
    assert [row["source_id"] for row in rows] == [
        "ppd-devhub-faq-placeholder",
        "ppd-submit-plans-online-placeholder",
        "ppd-fee-payment-guide-placeholder",
        "ppd-forms-index-placeholder",
    ]

    devhub = rows[0]
    assert devhub["freshness_threshold"]["as_of_date"] == "2026-06-01"
    assert devhub["freshness_threshold"]["threshold_days"] == 2
    assert devhub["freshness_threshold"]["days_since_last_seen"] == 24
    assert devhub["stale_source_hold_trigger"]["triggered"] is True
    assert "dated_freshness_threshold_exceeded" in devhub["stale_source_hold_trigger"]["reasons"]
    assert "prior_refresh_fixture_stale_source_hold" in devhub["stale_source_hold_trigger"]["reasons"]
    assert devhub["affected_requirement_ids"] == [
        "requirement-devhub-account-scoped-services",
        "requirement-devhub-corrections-upload-gate",
        "requirement-devhub-fee-payment-gate",
    ]
    assert devhub["affected_guardrail_bundle_ids"] == [
        "guardrail-building-permit-application",
        "guardrail-fee-payment",
        "guardrail-inspection-scheduling",
    ]
    assert devhub["reviewer_escalation"]["reviewer_owner"] == "devhub-public-guidance-reviewer"
    assert devhub["no_raw_body_capture_policy"] == "metadata_normalized_text_checksums_and_citations_only"
    assert "defer any crawl" in devhub["crawl_deferral_note"]


def test_policy_reminders_and_validation_commands_are_offline_only() -> None:
    packet = build_watchlist_from_files(REGISTRY_FIXTURE, PRIOR_REFRESH_FIXTURE)

    command_text = " ".join(" ".join(command) for command in packet["offline_validation_commands"])
    assert "curl" not in command_text
    assert "playwright" not in command_text.lower()
    assert "devhub" not in command_text.lower()
    assert "Do not commit raw HTML" in packet["no_raw_body_capture_policy_reminders"][1]
    assert "does not authorize a crawl" in packet["crawl_deferral_notes"][0]
    assert "legal_or_permitting_guarantee" in packet["prohibited_actions"]


def test_validator_rejects_live_boundary_claims() -> None:
    packet = build_watchlist_from_files(REGISTRY_FIXTURE, PRIOR_REFRESH_FIXTURE)
    packet["source_boundaries"]["live_crawl"] = True

    with pytest.raises(ValueError, match="live_crawl"):
        validate_watchlist(packet)


def test_rejects_raw_body_in_fixture() -> None:
    registry = REGISTRY_FIXTURE.read_text(encoding="utf-8")
    bad_path = FIXTURE_DIR / "_not_written_bad_fixture.json"
    assert not bad_path.exists()
    assert "raw_body" not in registry
