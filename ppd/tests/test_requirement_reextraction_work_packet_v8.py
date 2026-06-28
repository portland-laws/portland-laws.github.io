from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from ppd.extraction.requirement_reextraction_work_packet_v8 import (
    assert_valid_requirement_reextraction_work_packet_v8,
    validate_requirement_reextraction_work_packet_v8,
)

_FIXTURE_DIR = Path(__file__).parent / "fixtures" / "requirement_reextraction_work_packet_v8"


def _valid_packet() -> dict:
    with (_FIXTURE_DIR / "valid_packet.json").open(encoding="utf-8") as fixture:
        return json.load(fixture)


def _messages(packet: dict) -> tuple[str, ...]:
    return validate_requirement_reextraction_work_packet_v8(packet).messages()


def test_valid_packet_fixture_passes() -> None:
    packet = _valid_packet()

    result = validate_requirement_reextraction_work_packet_v8(packet)

    assert result.valid is True
    assert result.findings == ()
    assert_valid_requirement_reextraction_work_packet_v8(packet)


def test_rejects_missing_queue_and_normalized_document_refs() -> None:
    packet = _valid_packet()
    packet.pop("reextraction_queue_ref")
    packet.pop("normalized_document_record_refs")

    messages = _messages(packet)

    assert any("reextraction_queue_ref" in message for message in messages)
    assert any("normalized_document_record_refs" in message for message in messages)


def test_rejects_missing_source_scoped_work_items() -> None:
    packet = _valid_packet()
    packet["source_scoped_extraction_work_items"] = []

    messages = _messages(packet)

    assert any("source_scoped_extraction_work_items" in message for message in messages)


def test_rejects_incomplete_work_item_inputs() -> None:
    packet = _valid_packet()
    packet["source_scoped_extraction_work_items"] = [
        {
            "source_id": "source:example"
        }
    ]

    messages = _messages(packet)

    assert any("normalized_document_record_ref" in message for message in messages)
    assert any("extraction_work_item_id" in message for message in messages)
    assert any("citation_span_inputs" in message for message in messages)
    assert any("requirement_type_expectations" in message for message in messages)
    assert any("confidence_placeholder" in message for message in messages)
    assert any("human_review_placeholder" in message for message in messages)


def test_rejects_unknown_requirement_type_expectations() -> None:
    packet = _valid_packet()
    packet["source_scoped_extraction_work_items"][0]["requirement_type_expectations"] = ["approval_prediction"]

    messages = _messages(packet)

    assert any("supported RequirementNode requirement_type" in message for message in messages)


def test_rejects_final_confidence_or_human_review_claims() -> None:
    packet = _valid_packet()
    item = packet["source_scoped_extraction_work_items"][0]
    item["confidence_placeholder"] = 0.99
    item["human_review_placeholder"] = "complete"

    messages = _messages(packet)

    assert any("confidence_placeholder" in message for message in messages)
    assert any("human_review_placeholder" in message for message in messages)


def test_rejects_missing_unsupported_paths_skipped_rows_and_validation_commands() -> None:
    packet = _valid_packet()
    packet["unsupported_path_notes"] = []
    packet["skipped_candidate_rows"] = []
    packet["validation_commands"] = []

    messages = _messages(packet)

    assert any("unsupported_path_notes" in message for message in messages)
    assert any("skipped_candidate_rows" in message for message in messages)
    assert any("validation_commands" in message for message in messages)


def test_rejects_live_crawl_execution_claims() -> None:
    packet = _valid_packet()
    packet["notes"] = "Live crawl executed for this packet."

    messages = _messages(packet)

    assert any("live crawl execution" in message for message in messages)


def test_rejects_downloaded_or_raw_crawl_artifacts() -> None:
    packet = _valid_packet()
    packet["raw_html"] = "raw crawl artifact"

    messages = _messages(packet)

    assert any("raw crawl" in message or "artifact" in message for message in messages)


def test_rejects_private_session_or_auth_artifacts() -> None:
    packet = _valid_packet()
    packet["storage_state"] = {"cookies": [{"name": "session", "value": "secret"}]}

    messages = _messages(packet)

    assert any("private, session, or auth" in message for message in messages)


def test_rejects_official_action_completion_claims() -> None:
    packet = _valid_packet()
    packet["completion_claim"] = "Permit submitted through DevHub."

    messages = _messages(packet)

    assert any("official-action completion" in message for message in messages)


def test_rejects_legal_or_permitting_guarantees() -> None:
    packet = _valid_packet()
    packet["guarantee"] = "Approval guaranteed after this extraction."

    messages = _messages(packet)

    assert any("legal or permitting guarantees" in message for message in messages)


def test_rejects_active_mutation_flags() -> None:
    packet = _valid_packet()
    packet["mutation_enabled"] = True

    messages = _messages(packet)

    assert any("active mutation flags" in message for message in messages)


def test_allows_explicitly_inactive_mutation_flags() -> None:
    packet = _valid_packet()
    for inactive_value in (False, None, "disabled", "inactive", "no"):
        candidate = deepcopy(packet)
        candidate["active_mutation_flags"] = inactive_value
        assert validate_requirement_reextraction_work_packet_v8(candidate).valid is True
