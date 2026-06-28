from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ppd.crawler.processor_handoff_rehearsal_packet import build_processor_handoff_manifest_rehearsal_packet
from ppd.crawler.public_source_refresh_batch_packet import (
    SourceRefreshBatchInputs,
    build_public_source_refresh_batch_packet,
)
from ppd.crawler.public_source_refresh_intake_evidence_packet import (
    PublicSourceRefreshIntakeEvidencePacketError,
    build_public_source_refresh_intake_evidence_packet,
    require_valid_public_source_refresh_intake_evidence_packet,
    validate_public_source_refresh_intake_evidence_packet,
)
from ppd.source_registry_coverage_gap_packet import build_public_source_registry_coverage_gap_packet


REFRESH_FIXTURE_DIR = Path(__file__).parent / "fixtures" / "public_source_refresh_batch"
HANDOFF_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "public_source_registry_coverage_gap_packet" / "input.json"


def _refresh_batch_packet() -> dict:
    return build_public_source_refresh_batch_packet(
        SourceRefreshBatchInputs(
            runbook_candidate_path=REFRESH_FIXTURE_DIR / "source_refresh_runbook_candidate.json",
            coverage_gap_packet_path=REFRESH_FIXTURE_DIR / "source_registry_coverage_gap_packet.json",
            freshness_badge_packet_path=REFRESH_FIXTURE_DIR / "source_freshness_badge_packet.json",
        )
    )


def _processor_handoff_packet() -> dict:
    fixture = json.loads(HANDOFF_FIXTURE_PATH.read_text(encoding="utf-8"))
    coverage_packet = build_public_source_registry_coverage_gap_packet(
        fixture["official_source_anchors"],
        fixture["public_source_recrawl_dry_run_command_plan"],
        fixture["source_evidence_freshness_badges"],
        generated_at="2026-05-29T00:00:00Z",
    )
    return build_processor_handoff_manifest_rehearsal_packet(
        coverage_packet,
        fixture["public_source_recrawl_dry_run_command_plan"],
        generated_at="2026-05-29T01:20:00Z",
    )


def _packet() -> dict:
    return build_public_source_refresh_intake_evidence_packet(
        _refresh_batch_packet(),
        _processor_handoff_packet(),
        generated_at="2026-05-29T02:00:00Z",
    )


def test_builds_fixture_first_refresh_intake_evidence_packet() -> None:
    packet = _packet()
    result = validate_public_source_refresh_intake_evidence_packet(packet)

    assert result.valid is True
    assert packet["packet_type"] == "ppd_public_source_refresh_intake_evidence_packet"
    assert packet["fixture_first"] is True
    assert packet["metadata_only"] is True
    assert packet["live_network_invoked"] is False
    assert packet["processor_invoked"] is False
    assert packet["raw_bodies_persisted"] is False
    assert packet["archive_manifest_updated"] is False
    assert packet["archive_manifest_mutation_allowed"] is False
    assert packet["registry_updated"] is False
    assert packet["schedule_updated"] is False
    assert packet["intake_summary"]["reviewer_evidence_count"] == 3


def test_packet_contains_reviewer_evidence_manifest_checks_skipped_slots_attestations_and_rollback_notes() -> None:
    packet = _packet()

    reviewer_rows = packet["synthetic_reviewer_evidence"]
    manifest_checks = packet["manifest_expectation_checks"]
    skipped_slots = packet["skipped_target_reason_slots"]
    attestations = packet["no_raw_body_attestations"]
    rollback_notes = packet["rollback_notes"]

    assert {row["source_id"] for row in reviewer_rows} == {
        "ppd-online-tools-overview",
        "ppd-devhub-faqs",
        "ppd-submit-plans-online",
    }
    assert len(manifest_checks) == len(reviewer_rows)
    assert len(attestations) == len(reviewer_rows)
    assert all(check["archive_manifest_update_allowed"] is False for check in manifest_checks)
    assert all(check["archive_manifest_mutation_allowed"] is False for check in manifest_checks)
    assert all(check["raw_body_persistence_allowed"] is False for check in manifest_checks)
    assert all(check["archive_artifact_ref_empty"] is True for check in manifest_checks)
    assert all(check["no_raw_body_persisted"] is True for check in manifest_checks)
    assert all("content_hash" in check["content_hash_expectation_fields"] for check in manifest_checks)
    assert all(attestation["no_raw_body_persisted"] is True for attestation in attestations)
    assert all(attestation["raw_body_persisted"] is False for attestation in attestations)
    assert all(attestation["processor_invoked"] is False for attestation in attestations)
    assert all(attestation["live_network_invoked"] is False for attestation in attestations)
    assert all(slot["skipped_target_reason_slot"] for slot in skipped_slots)
    assert any(slot["skipped_target_reason_slot"] == "processor_handoff_rehearsal_source_not_selected_in_refresh_batch" for slot in skipped_slots)
    assert any(slot["skipped_target_reason_slot"] == "processor_handoff_rehearsal_missing_for_refresh_batch_target" for slot in skipped_slots)
    assert {note["rollback_required"] for note in rollback_notes} == {False}


def test_reviewer_rows_reference_attestations_manifest_checks_skipped_slots_and_rollback_notes() -> None:
    packet = _packet()
    attestation_ids = {row["attestation_id"] for row in packet["no_raw_body_attestations"]}
    check_ids = {row["check_id"] for row in packet["manifest_expectation_checks"]}
    rollback_ids = {row["rollback_note_id"] for row in packet["rollback_notes"]}
    skipped_sources = {row["source_id"] for row in packet["skipped_target_reason_slots"]}

    for row in packet["synthetic_reviewer_evidence"]:
        fields = row["synthetic_reviewer_evidence_fields"]
        assert fields["refresh_reason"]
        assert "content_hash" in fields["expected_metadata_fields"]
        assert "expected_content_hash_field" in fields["content_hash_expectation_fields"]
        assert fields["skipped_target_reason_slot"]
        assert row["source_id"] in skipped_sources
        assert fields["no_raw_body_attestation_id"] in attestation_ids
        assert fields["manifest_expectation_check"]["check_id"] in check_ids
        assert set(fields["rollback_note_ids"]).issubset(rollback_ids)


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (lambda packet: packet.update({"live_network_invoked": True}), "live_network_invoked must be false"),
        (lambda packet: packet.update({"processor_invoked": True}), "processor_invoked must be false"),
        (lambda packet: packet.update({"archive_manifest_updated": True}), "archive_manifest_updated must be false"),
        (lambda packet: packet.update({"archive_manifest_mutation_allowed": True}), "archive_manifest_mutation_allowed must be false"),
        (lambda packet: packet.update({"active_archive_manifest_mutation": True}), "active_archive_manifest_mutation must be false"),
        (lambda packet: packet["synthetic_reviewer_evidence"][0].update({"source_id": ""}), "synthetic_reviewer_evidence[0].source_id is required"),
        (lambda packet: packet["synthetic_reviewer_evidence"][0]["synthetic_reviewer_evidence_fields"].update({"expected_metadata_fields": ["freshness_status"]}), "expected_metadata_fields must include content_hash"),
        (lambda packet: packet["synthetic_reviewer_evidence"][0]["synthetic_reviewer_evidence_fields"].update({"content_hash_expectation_fields": ["content_hash"]}), "content_hash_expectation_fields must include"),
        (lambda packet: packet["synthetic_reviewer_evidence"][0]["synthetic_reviewer_evidence_fields"].update({"skipped_target_reason_slot": ""}), "skipped_target_reason_slot is required"),
        (lambda packet: packet["synthetic_reviewer_evidence"][0]["synthetic_reviewer_evidence_fields"].update({"no_raw_body_attestation_id": "missing"}), "no_raw_body_attestation_id must reference"),
        (lambda packet: packet["synthetic_reviewer_evidence"][0]["synthetic_reviewer_evidence_fields"].update({"rollback_note_ids": ["missing"]}), "rollback_note_ids must reference rollback_notes"),
        (lambda packet: packet["manifest_expectation_checks"][0].update({"source_id": ""}), "manifest_expectation_checks[0].source_id is required"),
        (lambda packet: packet["manifest_expectation_checks"][0].update({"content_hash_expectation_fields": []}), "content_hash_expectation_fields must include"),
        (lambda packet: packet["manifest_expectation_checks"][0].update({"archive_manifest_update_allowed": True}), "archive_manifest_update_allowed must be false"),
        (lambda packet: packet["manifest_expectation_checks"][0].update({"archive_manifest_mutation_allowed": True}), "archive_manifest_mutation_allowed must be false"),
        (lambda packet: packet["manifest_expectation_checks"][0].update({"archive_artifact_ref_empty": False}), "archive_artifact_ref_empty must be true"),
        (lambda packet: packet["manifest_expectation_checks"][0].update({"skipped_reason": ""}), "skipped_reason is required"),
        (lambda packet: packet["skipped_target_reason_slots"][0].update({"source_id": ""}), "skipped_target_reason_slots[0].source_id is required"),
        (lambda packet: packet["skipped_target_reason_slots"][0].update({"skipped_target_reason_slot": ""}), "skipped_target_reason_slot is required"),
        (lambda packet: packet["no_raw_body_attestations"].pop(), "no_raw_body_attestations must match"),
        (lambda packet: packet["no_raw_body_attestations"][0].update({"source_id": ""}), "no_raw_body_attestations[0].source_id is required"),
        (lambda packet: packet["no_raw_body_attestations"][0].update({"raw_body_persisted": True}), "raw_body_persisted must be false"),
        (lambda packet: packet.update({"rollback_notes": []}), "rollback_notes must not be empty"),
        (lambda packet: packet["rollback_notes"][0].update({"rollback_required": True}), "rollback_required must be false"),
        (lambda packet: packet.update({"debug": "warc://not-allowed"}), "forbidden private, archive, raw, download"),
        (lambda packet: packet.update({"raw_path": "/tmp/ppd/raw/crawl/page.html"}), "forbidden private, archive, raw, download"),
        (lambda packet: packet.update({"download_path": "/tmp/ppd/downloads/source.pdf"}), "forbidden private, archive, raw, download"),
        (lambda packet: packet.update({"processor_output_path": "/tmp/ppd/processor_outputs/doc.json"}), "forbidden private, archive, raw, download"),
        (lambda packet: packet.update({"liveCrawlPerformed": True}), "liveCrawlPerformed must be false"),
        (lambda packet: packet.update({"processorExecuted": True}), "processorExecuted must be false"),
    ],
)
def test_intake_evidence_packet_rejects_unsafe_or_incomplete_mutations(mutation, expected: str) -> None:
    packet = copy.deepcopy(_packet())
    mutation(packet)

    with pytest.raises(PublicSourceRefreshIntakeEvidencePacketError) as exc_info:
        require_valid_public_source_refresh_intake_evidence_packet(packet)

    assert expected in str(exc_info.value)


def test_builder_rejects_refresh_batch_with_side_effect_authority() -> None:
    refresh_batch = _refresh_batch_packet()
    refresh_batch["side_effect_boundary"]["network_io_allowed"] = True

    with pytest.raises(PublicSourceRefreshIntakeEvidencePacketError) as exc_info:
        build_public_source_refresh_intake_evidence_packet(
            refresh_batch,
            _processor_handoff_packet(),
            generated_at="2026-05-29T02:00:00Z",
        )

    assert "network_io_allowed must be false" in str(exc_info.value)
