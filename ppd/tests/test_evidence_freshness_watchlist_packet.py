from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ppd.evidence_freshness_watchlist_packet import (
    PACKET_TYPE,
    EvidenceFreshnessWatchlistPacketError,
    assert_valid_evidence_freshness_watchlist_packet,
    build_evidence_freshness_watchlist_packet,
    validate_evidence_freshness_watchlist_packet,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "evidence_freshness_watchlist_packet" / "input_packets.json"


def _inputs() -> dict[str, dict]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _packet() -> dict:
    inputs = _inputs()
    return build_evidence_freshness_watchlist_packet(
        inputs["source_registry_schedule_update_candidate"],
        inputs["public_source_refresh_operator_dry_run_transcript"],
        inputs["requirement_guardrail_traceability_review_packet"],
        generated_at="2026-05-29T00:00:00Z",
    )


def test_builds_fixture_first_ppd_evidence_freshness_watchlist_packet() -> None:
    packet = _packet()

    assert packet["packet_type"] == PACKET_TYPE
    assert packet["packet_mode"] == "offline_review_only_no_active_mutation"
    assert packet["fixture_first"] is True
    assert validate_evidence_freshness_watchlist_packet(packet).valid is True
    assert_valid_evidence_freshness_watchlist_packet(packet)


def test_consumes_required_packets_into_cited_watchlist_source_impacts() -> None:
    packet = _packet()

    assert set(packet["consumed_packets"]) == {
        "source_registry_schedule_update_candidate",
        "public_source_refresh_operator_dry_run_transcript",
        "requirement_guardrail_traceability_review_packet",
    }
    assert all(row["packet_id"] for row in packet["consumed_packets"].values())
    assert all(row["source_evidence_ids"] for row in packet["consumed_packets"].values())

    assert {row["source_id"] for row in packet["watchlist_sources"]} == {
        "ppd-devhub-faq",
        "ppd-submit-plans-online",
    }
    for row in packet["watchlist_sources"]:
        assert row["source_evidence_ids"]
        assert row["affected_requirement_ids"] == packet["affected_requirement_ids"]
        assert row["affected_guardrail_ids"] == packet["affected_guardrail_ids"]
        assert row["next_offline_review_triggers"] == packet["next_offline_review_triggers"]

    assert set(packet["affected_requirement_ids"]) == {
        "REQ-DEVHUB-UPLOAD-GATE-002",
        "REQ-SINGLE-PDF-FILE-RULE-001",
    }
    assert set(packet["affected_guardrail_ids"]) == {
        "GR-DEVHUB-UPLOAD-EXACT-CONFIRMATION",
        "GR-SINGLE-PDF-FILE-PREP-CHECK",
    }


def test_records_next_offline_review_triggers_reviewer_owners_and_attestations() -> None:
    packet = _packet()

    trigger_ids = {row["trigger_id"] for row in packet["next_offline_review_triggers"]}
    assert "schedule-candidate-1" in trigger_ids
    assert "operator-dry-run-checkpoint-1" in trigger_ids
    assert "traceability-blocked-action-1" in trigger_ids
    assert all(row["source_evidence_ids"] for row in packet["next_offline_review_triggers"])

    assert packet["reviewer_owner_fields"] == {
        "primary_reviewer": "ppd-source-reviewer",
        "source_registry_owner": "ppd-source-registry-review",
        "refresh_operator_owner": "ppd-source-refresh-owner",
        "traceability_owner": "ppd-traceability-reviewer",
        "watchlist_owner": "ppd-evidence-freshness-watchlist-owner",
    }
    for key in (
        "no_fetch",
        "no_processor",
        "no_registry_mutation",
        "no_guardrail_mutation",
        "no_requirement_mutation",
        "no_devhub_execution",
        "fixture_first_inputs_only",
    ):
        assert packet["attestations"][key] is True
    assert all(value is False for value in packet["active_mutation_effects"].values())


def test_validator_rejects_uncited_watchlist_missing_triggers_and_mutation_effects() -> None:
    broken = copy.deepcopy(_packet())
    broken["watchlist_sources"][0]["source_evidence_ids"] = []
    broken["watchlist_sources"][0]["next_offline_review_triggers"] = []
    broken["affected_guardrail_ids"] = []
    broken["active_mutation_effects"]["guardrails_mutated"] = True

    result = validate_evidence_freshness_watchlist_packet(broken)
    codes = set(result.codes())

    assert result.valid is False
    assert "uncited_watchlist_source" in codes
    assert "missing_next_offline_review_triggers" in codes
    assert "missing_affected_guardrail_ids" in codes
    assert "active_mutation_effect_enabled" in codes
    with pytest.raises(EvidenceFreshnessWatchlistPacketError):
        assert_valid_evidence_freshness_watchlist_packet(broken)


def test_validator_rejects_missing_consumed_packet_owner_attestation_live_claims_and_raw_refs() -> None:
    broken = copy.deepcopy(_packet())
    broken["consumed_packets"].pop("public_source_refresh_operator_dry_run_transcript")
    broken["reviewer_owner_fields"]["watchlist_owner"] = ""
    broken["attestations"]["no_fetch"] = False
    broken["review_notes"] = "The live crawler ran, the processor invoked, and approval is guaranteed."
    broken["raw_body_ref"] = "raw_crawl/output/body.html"
    broken["apply_registry_update"] = True

    result = validate_evidence_freshness_watchlist_packet(broken)
    codes = set(result.codes())

    assert result.valid is False
    assert "missing_consumed_packet" in codes
    assert "missing_reviewer_owner" in codes
    assert "missing_no_mutation_attestation" in codes
    assert "live_execution_claim" in codes
    assert "legal_or_permitting_outcome_guarantee" in codes
    assert "raw_or_private_artifact_reference" in codes
    assert "active_mutation_flag_present" in codes
