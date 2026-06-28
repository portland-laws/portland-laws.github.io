from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ppd.crawler.archive_manifest_promotion_readiness_packet import (
    ArchiveManifestPromotionReadinessPacketError,
    build_archive_manifest_promotion_readiness_packet,
    require_valid_archive_manifest_promotion_readiness_packet,
    validate_archive_manifest_promotion_readiness_packet,
)

_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "archive_manifest_promotion_readiness" / "input_packets.json"


def _inputs() -> dict[str, object]:
    return json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))


def _packet() -> dict[str, object]:
    fixture = _inputs()
    return build_archive_manifest_promotion_readiness_packet(
        fixture["processor_handoff_manifest_rehearsal_packet"],
        fixture["public_recrawl_metadata_intake_reconciliation_packet"],
        generated_at="2026-05-29T03:00:00Z",
    )


def test_builds_fixture_first_archive_manifest_promotion_readiness_packet() -> None:
    packet = _packet()
    result = validate_archive_manifest_promotion_readiness_packet(packet)

    assert result.valid is True, result.errors
    assert packet["fixtureFirst"] is True
    assert packet["metadataOnly"] is True
    assert packet["manifestPromotionAllowed"] is False
    assert packet["manifestPromotionPerformed"] is False
    assert packet["archiveArtifactWritten"] is False
    assert packet["processorInvoked"] is False
    assert packet["readinessSummary"]["readyForManifestPromotion"] is False
    assert packet["readinessSummary"]["manifestReadinessCheckCount"] == 2
    assert packet["readinessSummary"]["expectedNormalizedDocumentReferenceCount"] == 2
    assert packet["readinessSummary"]["checksumFreshnessConsistencyNoteCount"] == 2


def test_packet_contains_normalized_document_refs_consistency_notes_attestations_and_review_checkpoints() -> None:
    packet = _packet()

    source_ids = {row["source_id"] for row in packet["syntheticMetadataOnlyManifestReadinessChecks"]}
    assert source_ids == {"source-portland-ppd", "source-devhub-faqs"}
    assert all(row["metadataOnly"] is True for row in packet["syntheticMetadataOnlyManifestReadinessChecks"])
    assert all(row["manifestPromotionAllowed"] is False for row in packet["syntheticMetadataOnlyManifestReadinessChecks"])
    assert all(row["archiveArtifactWritten"] is False for row in packet["syntheticMetadataOnlyManifestReadinessChecks"])
    assert all(row["normalized_document_id"].startswith("expected-normalized-document-") for row in packet["expectedNormalizedDocumentReferences"])
    assert all(row["reviewRequired"] is True for row in packet["checksumFreshnessConsistencyNotes"])
    assert all(row["noPayloadPersisted"] is True for row in packet["noRawBodyAttestations"])
    assert all(row["required_before_manifest_promotion"] is True for row in packet["reviewerCheckpoints"])
    assert any(row["source_id"] == "source-devhub-faqs" for row in packet["reviewerCheckpoints"])


def test_abort_notes_block_live_fetch_processor_archive_write_and_manifest_promotion() -> None:
    packet = _packet()
    joined = "\n".join(row["note"] for row in packet["abortNotes"])

    assert "live fetch" in joined
    assert "processor" in joined
    assert "archive" in joined
    assert "promote a manifest" in joined
    assert all(row["abortBeforeManifestPromotion"] is True for row in packet["abortNotes"])
    assert all(row["processorInvocationAllowed"] is False for row in packet["abortNotes"])
    assert all(row["archiveArtifactWriteAllowed"] is False for row in packet["abortNotes"])
    assert all(row["manifestPromotionAllowed"] is False for row in packet["abortNotes"])


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (lambda packet: packet.update({"manifestPromotionAllowed": True}), "manifestPromotionAllowed"),
        (lambda packet: packet.update({"manifestPromotionPerformed": True}), "manifestPromotionPerformed"),
        (lambda packet: packet.update({"archiveArtifactWritten": True}), "archiveArtifactWritten"),
        (lambda packet: packet["syntheticMetadataOnlyManifestReadinessChecks"][0].update({"manifestPromotionAllowed": True}), "manifestPromotionAllowed"),
        (lambda packet: packet["expectedNormalizedDocumentReferences"][0].update({"archive_artifact_ref_present": True}), "archive_artifact_ref_present"),
        (lambda packet: packet["checksumFreshnessConsistencyNotes"][0].update({"reviewRequired": False}), "reviewRequired"),
        (lambda packet: packet["noRawBodyAttestations"][0].update({"processorInvoked": True}), "processorInvoked"),
        (lambda packet: packet["reviewerCheckpoints"][0].update({"humanReviewRequired": False}), "humanReviewRequired"),
        (lambda packet: packet["abortNotes"].clear(), "abortNotes must include"),
        (lambda packet: packet.update({"debug_ref": "warc://archive/object"}), "forbidden private, raw, or artifact"),
        (lambda packet: packet["syntheticMetadataOnlyManifestReadinessChecks"][0].update({"canonical_url": "https://example.com/ppd"}), "HTTPS allowlisted public URL"),
    ],
)

def test_rejects_unsafe_or_incomplete_archive_manifest_promotion_readiness_mutations(mutation, expected: str) -> None:
    packet = copy.deepcopy(_packet())
    mutation(packet)

    with pytest.raises(ArchiveManifestPromotionReadinessPacketError) as exc_info:
        require_valid_archive_manifest_promotion_readiness_packet(packet)

    assert expected in str(exc_info.value)


def test_builder_rejects_non_fixture_or_promoting_inputs() -> None:
    fixture = _inputs()
    handoff = copy.deepcopy(fixture["processor_handoff_manifest_rehearsal_packet"])
    reconciliation = copy.deepcopy(fixture["public_recrawl_metadata_intake_reconciliation_packet"])
    reconciliation["archiveArtifactWritten"] = True

    with pytest.raises(ArchiveManifestPromotionReadinessPacketError) as exc_info:
        build_archive_manifest_promotion_readiness_packet(
            handoff,
            reconciliation,
            generated_at="2026-05-29T03:00:00Z",
        )

    assert "archiveArtifactWritten must be false" in str(exc_info.value)
