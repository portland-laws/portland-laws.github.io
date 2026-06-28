from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from ppd.extraction.requirement_reextraction_work_packet_v6 import (
    build_work_packet_from_fixture,
    expected_offline_validation_commands,
    validate_work_packet,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "requirement_reextraction_batch_plan_v6"
BATCH_PLAN = FIXTURE_DIR / "batch_plan_v6.json"


def _packet() -> dict:
    return build_work_packet_from_fixture(BATCH_PLAN)


def _expect_invalid(packet: dict, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        validate_work_packet(packet)


def test_builds_fixture_only_work_packet_from_batch_plan_v6_fixture() -> None:
    packet = _packet()

    assert packet["packet_version"] == 6
    assert packet["fixture_only"] is True
    assert packet["source_batch_plan_id"] == "requirement-reextraction-batch-plan-v6-fixture"
    assert packet["source_batch_plan_version"] == 6
    assert packet["validation_commands"] == expected_offline_validation_commands()
    assert all(value is False for value in packet["live_access"].values())
    assert len(packet["process_packets"]) == 2


def test_stages_per_process_inputs_without_raw_bodies_or_live_fetches() -> None:
    packet = _packet()

    for process_packet in packet["process_packets"]:
        assert process_packet["inactive_guardrail_status"] == "unchanged"
        assert process_packet["reviewer_comparison_prompt"]
        for extraction_input in process_packet["extraction_inputs"]:
            assert extraction_input["raw_body_ref"] is None
            assert extraction_input["requires_live_fetch"] is False
            assert extraction_input["normalized_text_fixture_ref"].startswith(
                "ppd/tests/fixtures/requirement_reextraction_batch_plan_v6/"
            )
        for target in process_packet["source_span_refresh_targets"]:
            assert target["requires_live_fetch"] is False
            assert target["current_citation_span"]


def test_preserves_old_vs_new_placeholders_and_reviewer_prompt_context() -> None:
    packet = _packet()
    building_packet = packet["process_packets"][0]

    placeholders = building_packet["requirement_placeholders"]
    assert placeholders[0]["old_requirement_placeholder"].startswith("OLD_REQUIREMENT_PLACEHOLDER:")
    assert placeholders[0]["new_requirement_placeholder"].startswith("NEW_REQUIREMENT_PLACEHOLDER:")
    assert placeholders[0]["comparison_status"] == "pending_fixture_review"
    assert "req-plan-review-upload-separate-pdfs" in building_packet["reviewer_comparison_prompt"]
    assert "evidence-single-pdf-separate-documents" in building_packet["reviewer_comparison_prompt"]


def test_propagates_human_review_holds_and_keeps_inactive_guardrails_unchanged() -> None:
    packet = _packet()
    building_packet = packet["process_packets"][0]
    trade_packet = packet["process_packets"][1]

    assert building_packet["human_review_hold"] is True
    assert "process_marked_for_human_review" in building_packet["human_review_hold_reasons"]
    assert "req-plan-review-upload-separate-pdfs:placeholder_human_review_hold" in building_packet[
        "human_review_hold_reasons"
    ]
    assert trade_packet["human_review_hold"] is False
    assert trade_packet["human_review_hold_reasons"] == []
    assert building_packet["inactive_guardrail_status"] == "unchanged"
    assert trade_packet["inactive_guardrail_status"] == "unchanged"


def test_work_packet_validator_accepts_generated_packet() -> None:
    validate_work_packet(_packet())


def test_validator_rejects_missing_batch_plan_references_and_validation_commands() -> None:
    for key, message in (
        ("source_batch_plan_id", "source_batch_plan_id"),
        ("source_batch_plan_version", "batch plan v6"),
        ("validation_commands", "validation commands"),
    ):
        packet = _packet()
        packet.pop(key)
        _expect_invalid(packet, message)


def test_validator_rejects_missing_required_per_process_rows() -> None:
    required_rows = (
        ("extraction_inputs", "extraction inputs"),
        ("source_span_refresh_targets", "source-span refresh targets"),
        ("requirement_placeholders", "old-vs-new requirement placeholders"),
        ("reviewer_comparison_prompt", "reviewer_comparison_prompt"),
        ("human_review_hold", "human-review hold"),
        ("human_review_hold_reasons", "human-review hold reasons"),
        ("inactive_guardrail_status", "inactive guardrail status"),
    )
    for key, message in required_rows:
        packet = _packet()
        packet["process_packets"][0].pop(key)
        _expect_invalid(packet, message)


def test_validator_rejects_missing_source_span_and_placeholder_detail() -> None:
    packet = _packet()
    packet["process_packets"][0]["source_span_refresh_targets"][0].pop("current_citation_span")
    _expect_invalid(packet, "cited source spans")

    packet = _packet()
    packet["process_packets"][0]["requirement_placeholders"][0].pop("old_requirement_placeholder")
    _expect_invalid(packet, "old_requirement_placeholder")

    packet = _packet()
    packet["process_packets"][0]["requirement_placeholders"][0].pop("new_requirement_placeholder")
    _expect_invalid(packet, "new_requirement_placeholder")


def test_validator_rejects_broken_hold_propagation_and_guardrail_activation() -> None:
    packet = _packet()
    packet["process_packets"][0]["human_review_hold_reasons"] = []
    _expect_invalid(packet, "human-review holds")

    packet = _packet()
    packet["process_packets"][0]["inactive_guardrail_status"] = "activated"
    _expect_invalid(packet, "inactive guardrail status")


def test_validator_rejects_live_raw_private_official_guarantee_and_mutation_claims() -> None:
    unsafe_cases = (
        ({"live_crawl_completed": True}, "forbidden"),
        ({"downloaded_artifacts": ["permit.pdf"]}, "forbidden"),
        ({"raw_crawl_artifacts": ["page.html"]}, "forbidden"),
        ({"auth_state": "storage-state.json"}, "forbidden"),
        ({"official_action_completed": True}, "forbidden"),
        ({"legal_guarantee": "permit approval guaranteed"}, "forbidden"),
        ({"active_mutation": True}, "forbidden"),
    )
    for unsafe_payload, message in unsafe_cases:
        packet = _packet()
        packet["process_packets"][0].update(deepcopy(unsafe_payload))
        _expect_invalid(packet, message)


def test_validator_rejects_live_fetch_and_raw_body_references() -> None:
    packet = _packet()
    packet["process_packets"][0]["extraction_inputs"][0]["requires_live_fetch"] = True
    _expect_invalid(packet, "live fetch")

    packet = _packet()
    packet["process_packets"][0]["extraction_inputs"][0]["raw_body_ref"] = "raw/page.html"
    _expect_invalid(packet, "raw bodies")

    packet = _packet()
    packet["process_packets"][0]["source_span_refresh_targets"][0]["requires_live_fetch"] = True
    _expect_invalid(packet, "live fetch")
