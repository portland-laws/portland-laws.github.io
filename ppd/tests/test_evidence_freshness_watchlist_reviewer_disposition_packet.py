from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ppd.evidence_freshness_watchlist_reviewer_disposition_packet import (
    PACKET_TYPE,
    ReviewerDispositionPacketError,
    assert_valid_evidence_freshness_watchlist_reviewer_disposition_packet,
    build_evidence_freshness_watchlist_reviewer_disposition_packet,
    validate_evidence_freshness_watchlist_reviewer_disposition_packet,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "evidence_freshness_watchlist_reviewer_disposition_packet" / "input_packets.json"


def _inputs() -> dict[str, dict]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _packet() -> dict:
    inputs = _inputs()
    return build_evidence_freshness_watchlist_reviewer_disposition_packet(
        inputs["evidence_freshness_watchlist_packet"],
        inputs["release_acceptance_review_packet"],
        inputs["public_source_refresh_operator_dry_run_transcript"],
        generated_at="2026-05-29T00:00:00Z",
    )


def test_builds_fixture_first_reviewer_disposition_packet() -> None:
    packet = _packet()

    assert packet["packet_type"] == PACKET_TYPE
    assert packet["packet_mode"] == "offline_reviewer_disposition_only_no_active_mutation"
    assert packet["fixture_first"] is True
    assert validate_evidence_freshness_watchlist_reviewer_disposition_packet(packet).valid is True
    assert_valid_evidence_freshness_watchlist_reviewer_disposition_packet(packet)


def test_consumes_required_packets_with_cited_decisions_per_watchlist_item() -> None:
    packet = _packet()

    assert set(packet["consumed_packets"]) == {
        "evidence_freshness_watchlist_packet",
        "release_acceptance_review_packet",
        "public_source_refresh_operator_dry_run_transcript",
    }
    assert all(row["packet_id"] for row in packet["consumed_packets"].values())
    assert all(row["source_evidence_ids"] for row in packet["consumed_packets"].values())

    decisions = {row["source_id"]: row for row in packet["watchlist_item_dispositions"]}
    assert decisions["ppd-devhub-faq"]["decision"] == "escalate"
    assert decisions["ppd-submit-plans-online"]["decision"] == "defer"
    assert decisions["ppd-apply-permits"]["decision"] == "approve"
    assert decisions["ppd-submit-plans-online"]["matched_release_blocker_ids"] == ["blocker-submit-plans-cadence-signoff"]
    assert all(row["source_evidence_ids"] for row in decisions.values())


def test_records_offline_validation_commands_reviewer_owners_and_attestations() -> None:
    packet = _packet()

    assert ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"] in packet["next_offline_validation_commands"]
    assert ["python3", "-m", "unittest", "ppd.tests.test_evidence_freshness_watchlist_reviewer_disposition_packet"] in packet["next_offline_validation_commands"]
    assert packet["reviewer_owner_fields"] == {
        "primary_reviewer": "ppd-source-reviewer",
        "watchlist_owner": "ppd-evidence-freshness-watchlist-owner",
        "release_acceptance_owner": "ppd-source-registry-reviewer",
        "refresh_operator_owner": "ppd-source-refresh-owner",
        "disposition_owner": "ppd-evidence-freshness-disposition-owner",
    }
    for key in (
        "fixture_first_inputs_only",
        "no_fetch",
        "no_processor",
        "no_registry_mutation",
        "no_guardrail_mutation",
        "no_release_mutation",
    ):
        assert packet["attestations"][key] is True
    assert all(value is False for value in packet["active_mutation_effects"].values())


def test_validator_rejects_missing_citations_commands_owners_and_mutation_effects() -> None:
    broken = copy.deepcopy(_packet())
    broken["watchlist_item_dispositions"][0]["source_evidence_ids"] = []
    broken["watchlist_item_dispositions"][0]["next_offline_validation_commands"] = []
    broken["reviewer_owner_fields"]["disposition_owner"] = ""
    broken["attestations"]["no_release_mutation"] = False
    broken["active_mutation_effects"]["release_state_mutated"] = True

    result = validate_evidence_freshness_watchlist_reviewer_disposition_packet(broken)
    codes = set(result.codes())

    assert result.valid is False
    assert "uncited_decision" in codes
    assert "missing_offline_validation_commands" in codes
    assert "missing_reviewer_owner" in codes
    assert "missing_attestation" in codes
    assert "active_mutation_effect" in codes
    with pytest.raises(ReviewerDispositionPacketError):
        assert_valid_evidence_freshness_watchlist_reviewer_disposition_packet(broken)
