from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from ppd.pdf.draft_preview_readiness_packet import (
    DraftPreviewReadinessPacketError,
    assert_valid_fixture_first_draft_preview_readiness_packet,
    build_fixture_first_draft_preview_readiness_packet_from_paths,
    validate_fixture_first_draft_preview_readiness_packet,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures"
DOCUMENT_METADATA_PATH = FIXTURE_DIR / "file_preparation" / "synthetic_document_metadata.json"
HANDOFF_CHECKLIST_PATH = FIXTURE_DIR / "user_handoff_checklist" / "user_handoff_checklist_packet.json"
PROMPT_CORPUS_PATH = FIXTURE_DIR / "agent_missing_information_prompt_corpus" / "corpus.json"
EXPECTED_PACKET_PATH = FIXTURE_DIR / "pdf_draft_preview_readiness_packet" / "expected_packet.json"


def _expected_packet() -> dict[str, object]:
    payload = json.loads(EXPECTED_PACKET_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _built_packet() -> dict[str, object]:
    return build_fixture_first_draft_preview_readiness_packet_from_paths(
        DOCUMENT_METADATA_PATH,
        HANDOFF_CHECKLIST_PATH,
        PROMPT_CORPUS_PATH,
    )


def test_expected_fixture_validates_as_preview_only_readiness_packet() -> None:
    packet = _expected_packet()

    assert validate_fixture_first_draft_preview_readiness_packet(packet) == ()
    assert_valid_fixture_first_draft_preview_readiness_packet(packet)
    assert packet["reads_private_pdfs"] is False
    assert packet["produces_filled_documents"] is False
    assert packet["writes_pdf_binary"] is False
    assert packet["output_attestations"]["official_submission_ready"] is False


def test_builder_consumes_existing_helper_outputs_into_readiness_packet() -> None:
    packet = _built_packet()

    assert validate_fixture_first_draft_preview_readiness_packet(packet) == ()
    assert packet["source_packets"]["file_preparation_compliance"]["consumed"] is True
    assert packet["source_packets"]["safe_next_action_user_handoff_checklist"]["consumed"] is True
    assert packet["source_packets"]["missing_information_prompt_regression_corpus"]["consumed"] is True
    assert {case["document_id"] for case in packet["synthetic_document_metadata_cases"]} == {
        "synthetic-permit-001",
        "synthetic-checklist-001",
    }
    assert {prompt["category"] for prompt in packet["required_missing_fact_prompts"]} == {
        "missing_fact_question",
        "stale_evidence_prompt",
        "manual_handoff_prompt",
    }
    assert packet["local_preview_only_notices"]
    assert packet["reviewer_checkpoints"]
    assert packet["upload_blocking_attestations"]


def test_readiness_packet_blocks_uploads_and_filled_document_outputs() -> None:
    packet = _built_packet()

    for attestation in packet["upload_blocking_attestations"]:
        assert attestation["blocked"] is True
        assert attestation["enabled"] is False
        assert attestation["requires_attended_user_confirmation"] is True
        assert attestation["citations"]

    output = packet["output_attestations"]
    assert output["metadata_only"] is True
    assert output["local_preview_only"] is True
    assert output["filled_document_created"] is False
    assert output["upload_staging_created"] is False
    assert output["private_pdf_read"] is False


def test_rejects_private_pdf_or_runtime_artifact_fields() -> None:
    packet = _built_packet()
    broken = deepcopy(packet)
    broken["local_pdf_path"] = "/home/example/private.pdf"

    errors = validate_fixture_first_draft_preview_readiness_packet(broken)

    assert any("forbidden private, PDF, or browser artifact key" in error for error in errors)
    assert any("forbidden private path" in error for error in errors)


def test_rejects_enabled_upload_or_official_submission_claims() -> None:
    packet = _built_packet()
    broken = deepcopy(packet)
    broken["upload_blocking_attestations"][0]["enabled"] = True
    broken["output_attestations"]["official_submission_ready"] = True

    errors = validate_fixture_first_draft_preview_readiness_packet(broken)

    assert "upload_blocking_attestations[0].enabled must be false" in errors
    assert "output_attestations.official_submission_ready must be false" in errors


def test_builder_rejects_non_compliant_document_metadata_fixture() -> None:
    bad_path = FIXTURE_DIR / "file_preparation" / "single_pdf_supporting_documents_case.json"

    with pytest.raises(DraftPreviewReadinessPacketError):
        build_fixture_first_draft_preview_readiness_packet_from_paths(
            bad_path,
            HANDOFF_CHECKLIST_PATH,
            PROMPT_CORPUS_PATH,
        )
