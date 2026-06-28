import copy
import json
from pathlib import Path

import pytest

from ppd.logic.inactive_guardrail_recompile_reviewer_packet import (
    OFFLINE_VALIDATION_COMMANDS,
    PACKET_VERSION,
    REQUIRED_NON_EMPTY_SECTIONS,
    SYNTHETIC_ROW_TYPE,
    ReviewerPacketError,
    assert_valid_reviewer_packet,
    build_reviewer_packet,
    validate_reviewer_packet,
)


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "inactive_guardrail_recompile_reviewer_packet_v1"
    / "synthetic_impact_plan_rows.json"
)


def _fixture_rows():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _valid_packet():
    return build_reviewer_packet(_fixture_rows())


def _messages(packet):
    return [finding.render() for finding in validate_reviewer_packet(packet)]


def test_build_reviewer_packet_from_synthetic_rows_only():
    packet = _valid_packet()

    assert packet["packet_version"] == PACKET_VERSION
    assert packet["input_policy"]["accepted_source_type"] == SYNTHETIC_ROW_TYPE
    assert packet["input_policy"]["fixture_first"] is True
    assert packet["input_policy"]["offline_only"] is True
    assert "recompile_active_guardrails" in packet["input_policy"]["forbidden_actions"]
    assert "open_devhub" in packet["input_policy"]["forbidden_actions"]
    assert packet["validation_commands"] == OFFLINE_VALIDATION_COMMANDS
    assert validate_reviewer_packet(packet) == []
    assert_valid_reviewer_packet(packet)


def test_packet_records_dispositions_notes_stale_blocks_routing_rollbacks_and_impact_refs():
    packet = _valid_packet()

    assert [row["row_id"] for row in packet["impact_plan_references"]] == [
        "synthetic-impact-001",
        "synthetic-impact-002",
        "synthetic-impact-003",
    ]

    dispositions = packet["reviewer_disposition_rows"]
    assert [row["row_id"] for row in dispositions] == [
        "synthetic-impact-001",
        "synthetic-impact-002",
        "synthetic-impact-003",
    ]
    assert dispositions[0]["route"] == "approve"
    assert dispositions[1]["route"] == "hold"
    assert dispositions[1]["blocked_by_stale_source_dependency"] is True
    assert dispositions[2]["route"] == "reject"

    assert len(packet["predicate_change_review_notes"]) == 4
    assert len(packet["explanation_template_review_notes"]) == 3
    assert packet["blocked_stale_source_dependencies"] == [
        {
            "row_id": "synthetic-impact-002",
            "guardrail_bundle_id": "inactive-bundle-fee-payment-v0",
            "inactive_guardrail_id": "inactive-guardrail-payment-submit-stop",
            "stale_source_dependency": "synthetic-source-fee-payment-guide",
            "block_reason": "source freshness must be reviewed before inactive recompile disposition can be approved",
            "route": "hold",
        }
    ]
    assert packet["approval_hold_reject_routing"] == {
        "approve": ["synthetic-impact-001"],
        "hold": ["synthetic-impact-002"],
        "reject": ["synthetic-impact-003"],
    }
    assert [note["rollback_scope"] for note in packet["rollback_notes"]] == [
        "review_packet_only_no_guardrail_state_changed",
        "review_packet_only_no_guardrail_state_changed",
        "review_packet_only_no_guardrail_state_changed",
    ]


def test_rejects_live_or_non_synthetic_rows():
    rows = _fixture_rows()
    rows[0]["source_type"] = "public_html"

    with pytest.raises(ReviewerPacketError, match="unsupported source_type"):
        build_reviewer_packet(rows)


def test_rejects_empty_input_and_invalid_recommendation():
    with pytest.raises(ReviewerPacketError, match="at least one"):
        build_reviewer_packet([])

    rows = _fixture_rows()
    rows[0]["reviewer_recommendation"] = "promote"
    with pytest.raises(ReviewerPacketError, match="invalid reviewer_recommendation"):
        build_reviewer_packet(rows)


@pytest.mark.parametrize("section", REQUIRED_NON_EMPTY_SECTIONS)
def test_validation_rejects_missing_required_reviewer_packet_sections(section):
    packet = _valid_packet()
    packet[section] = []

    messages = _messages(packet)

    assert any(f"{section}: must be present and non-empty" in message for message in messages)


def test_validation_rejects_missing_impact_plan_references_for_review_rows_notes_blocks_and_rollbacks():
    packet = _valid_packet()
    packet["impact_plan_references"] = packet["impact_plan_references"][:1]

    messages = _messages(packet)

    assert any("reviewer_disposition_rows[1].row_id: must reference impact_plan_references" in message for message in messages)
    assert any("predicate_change_review_notes" in message and "must reference impact_plan_references" in message for message in messages)
    assert any("explanation_template_review_notes" in message and "must reference impact_plan_references" in message for message in messages)
    assert any("blocked_stale_source_dependencies[0].row_id: must reference impact_plan_references" in message for message in messages)
    assert any("rollback_notes[1].row_id: must reference impact_plan_references" in message for message in messages)


def test_validation_rejects_missing_approval_hold_reject_routing_for_disposition_rows():
    packet = _valid_packet()
    packet["approval_hold_reject_routing"] = {"approve": [], "hold": [], "reject": []}

    messages = _messages(packet)

    assert any("reviewer_disposition_rows[0].route: must be represented in approval_hold_reject_routing" in message for message in messages)
    assert any("reviewer_disposition_rows[1].route: must be represented in approval_hold_reject_routing" in message for message in messages)
    assert any("reviewer_disposition_rows[2].route: must be represented in approval_hold_reject_routing" in message for message in messages)


def test_validation_rejects_bad_routing_references_and_non_offline_commands():
    packet = _valid_packet()
    packet["approval_hold_reject_routing"]["approve"].append("missing-row")
    packet["validation_commands"] = [["python3", "live_crawl.py"]]

    messages = _messages(packet)

    assert any("approval_hold_reject_routing.approve[1]: must reference reviewer_disposition_rows" in message for message in messages)
    assert any("validation_commands: must exactly match offline reviewer packet commands" in message for message in messages)
    assert any("forbidden claim: live crawl" in message for message in messages)


def test_validation_rejects_private_raw_downloaded_artifacts_live_claims_and_devhub_claims():
    packet = _valid_packet()
    packet["private_artifact_path"] = "private/session/auth_state.json"
    packet["reviewer_disposition_rows"][0]["note"] = "Live crawl and scraped DevHub verified this row."
    packet["rollback_notes"][0]["raw_artifact"] = "downloaded artifact kept locally"

    messages = _messages(packet)

    assert any("forbidden artifact or live-operation key: private_artifact" in message for message in messages)
    assert any("forbidden artifact or live-operation key: raw_artifact" in message for message in messages)
    assert any("forbidden claim: live crawl" in message for message in messages)
    assert any("forbidden claim: scraped devhub" in message for message in messages)
    assert any("forbidden claim: downloaded artifact" in message for message in messages)


def test_validation_rejects_promotion_official_completion_guarantee_and_active_mutation_claims():
    packet = _valid_packet()
    packet["promotion_note"] = "Promote to production after review."
    packet["official_status"] = "Official action complete and final submission complete."
    packet["legal_note"] = "Guaranteed permit approval and legal advice."
    packet["mutate_active_guardrails"] = True
    packet["active_mutation_enabled"] = "yes"

    messages = _messages(packet)

    assert any("forbidden claim: promote to production" in message for message in messages)
    assert any("forbidden claim: official action complete" in message for message in messages)
    assert any("forbidden claim: final submission complete" in message for message in messages)
    assert any("forbidden claim: guaranteed permit" in message for message in messages)
    assert any("forbidden claim: legal advice" in message for message in messages)
    assert any("mutate_active_guardrails: active mutation or promotion flag must not be true" in message for message in messages)
    assert any("active_mutation_enabled: active mutation or promotion flag must not be true" in message for message in messages)


def test_assert_valid_reviewer_packet_raises_stable_error():
    packet = _valid_packet()
    broken = copy.deepcopy(packet)
    broken["reviewer_disposition_rows"] = []

    with pytest.raises(ReviewerPacketError, match="reviewer_disposition_rows: must be present and non-empty"):
        assert_valid_reviewer_packet(broken)
