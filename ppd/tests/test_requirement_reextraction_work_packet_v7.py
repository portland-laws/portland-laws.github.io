from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from ppd.extraction.requirement_reextraction_work_packet_v7 import (
    EXACT_OFFLINE_VALIDATION_COMMANDS,
    build_work_packet_v7,
    build_work_packet_v7_from_fixture,
    validate_work_packet_v7,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "requirement_reextraction_work_packet_v7"
MANIFEST = FIXTURE_DIR / "input_manifest.json"


def _packet() -> dict[str, Any]:
    return build_work_packet_v7_from_fixture(MANIFEST)


def test_builds_fixture_first_work_packet_v7_from_downstream_queue_and_normalized_documents() -> None:
    packet = _packet()

    assert packet["schema"] == "ppd.requirement_reextraction_work_packet.v7"
    assert packet["mode"] == "fixture_first_requirement_reextraction_work_packet_v7"
    assert packet["consumes_only"] == {
        "downstream_requirement_reextraction_queue_v7_fixtures": True,
        "synthetic_normalized_document_fixtures": True,
    }
    assert packet["safety_boundaries"]["live_crawl_executed"] is False
    assert packet["safety_boundaries"]["devhub_opened"] is False
    assert packet["safety_boundaries"]["active_guardrail_mutation"] is False
    assert packet["exact_offline_validation_commands"] == EXACT_OFFLINE_VALIDATION_COMMANDS

    source_ids = {"ppd-submit-plans-online", "ppd-devhub-faq"}
    assert {row["source_id"] for row in packet["extraction_prompt_rows"]} == source_ids
    assert {row["source_id"] for row in packet["source_evidence_anchors"]} == source_ids
    assert {row["source_id"] for row in packet["candidate_requirement_node_placeholders"]} == source_ids
    assert {row["source_id"] for row in packet["confidence_and_human_review_placeholders"]} == source_ids
    assert {row["source_id"] for row in packet["unsupported_path_notes"]} == source_ids
    assert {row["source_id"] for row in packet["stale_citation_replacement_reminders"]} == source_ids


def test_prompt_rows_and_evidence_anchors_are_offline_fixture_only() -> None:
    packet = _packet()

    for row in packet["extraction_prompt_rows"]:
        assert "Use only synthetic normalized document fixture" in row["extraction_prompt"]
        assert row["raw_document_ref"] is None
        assert row["requires_live_access"] is False
        assert row["section_ids"]
    for row in packet["source_evidence_anchors"]:
        assert row["anchor_source"] == "synthetic_normalized_document_fixture"
        assert row["requires_live_access"] is False
        assert row["anchor_text"]


def test_candidate_requirement_nodes_are_inactive_placeholders_with_review_holds() -> None:
    packet = _packet()

    for row in packet["candidate_requirement_node_placeholders"]:
        assert row["requirement_id"].startswith("candidate-req-")
        assert row["source_evidence_ids"]
        assert row["confidence"] is None
        assert row["human_review_status"] == "pending_fixture_review"
        assert row["formalization_status"] == "inactive_placeholder_only"
        assert row["subject"].startswith("CANDIDATE_PLACEHOLDER:")

    for row in packet["confidence_and_human_review_placeholders"]:
        assert row["confidence"] is None
        assert row["confidence_basis"] == "placeholder_until_fixture_evidence_reviewed"
        assert row["human_review_status"] == "pending_fixture_review"


def test_unsupported_paths_and_stale_citation_replacement_are_reminder_only() -> None:
    packet = _packet()

    for row in packet["unsupported_path_notes"]:
        assert row["unsupported_path_status"] == "not_supported_by_this_offline_packet"
        assert "DevHub access" in row["unsupported_actions"]
        assert "guardrail activation" in row["unsupported_actions"]
    for row in packet["stale_citation_replacement_reminders"]:
        assert row["replacement_status"] == "reminder_only_pending_human_review"
        assert row["citation_placeholder_id"].startswith("citation-")
        assert row["hold_id"].startswith("stale-evidence-hold::")


def test_validator_accepts_generated_packet() -> None:
    validate_work_packet_v7(_packet())


def test_validator_rejects_missing_required_sections() -> None:
    packet = _packet()
    packet["source_evidence_anchors"] = []

    with pytest.raises(ValueError, match="source_evidence_anchors"):
        validate_work_packet_v7(packet)


def test_validator_rejects_section_coverage_mismatch() -> None:
    packet = _packet()
    packet["stale_citation_replacement_reminders"] = packet["stale_citation_replacement_reminders"][:1]

    with pytest.raises(ValueError, match="stale_citation_replacement_reminders"):
        validate_work_packet_v7(packet)


def test_validator_rejects_live_private_guardrail_or_validation_drift() -> None:
    unsafe_cases = (
        ("safety_boundaries", {"live_crawl_executed": True}, "safety boundaries"),
        ("exact_offline_validation_commands", [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]], "validation commands"),
    )
    for key, value, message in unsafe_cases:
        packet = _packet()
        if isinstance(packet[key], dict) and isinstance(value, dict):
            packet[key] = {**packet[key], **value}
        else:
            packet[key] = value
        with pytest.raises(ValueError, match=message):
            validate_work_packet_v7(packet)

    packet = _packet()
    packet["extraction_prompt_rows"][0]["requires_live_access"] = True
    with pytest.raises(ValueError, match="offline-only|forbidden"):
        validate_work_packet_v7(packet)

    packet = _packet()
    packet["source_fixture_refs"][0]["session_state_path"] = "state.json"
    with pytest.raises(ValueError, match="artifact/session"):
        validate_work_packet_v7(packet)


def test_builder_rejects_missing_normalized_document_fixture_for_queue_row() -> None:
    queue = json_fixture("downstream_queue_v7.json")
    documents = json_fixture("synthetic_normalized_documents.json")
    documents["documents"] = documents["documents"][:1]

    with pytest.raises(ValueError, match="missing synthetic normalized document fixture"):
        build_work_packet_v7(queue, documents)


def test_builder_rejects_downstream_queue_live_access_claim() -> None:
    queue = json_fixture("downstream_queue_v7.json")
    documents = json_fixture("synthetic_normalized_documents.json")
    queue["source_to_extraction_work_rows"] = deepcopy(queue["source_to_extraction_work_rows"])
    queue["source_to_extraction_work_rows"][0]["requires_live_crawl"] = True

    with pytest.raises(ValueError, match="offline-only|forbidden"):
        build_work_packet_v7(queue, documents)


def json_fixture(name: str) -> dict[str, Any]:
    import json

    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))
