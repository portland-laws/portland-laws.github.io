from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ppd.crawler.processor_handoff_rehearsal_packet import (
    ProcessorHandoffRehearsalPacketError,
    build_processor_handoff_manifest_rehearsal_packet,
    require_valid_processor_handoff_manifest_rehearsal_packet,
    validate_processor_handoff_manifest_rehearsal_packet,
)
from ppd.source_registry_coverage_gap_packet import build_public_source_registry_coverage_gap_packet


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "public_source_registry_coverage_gap_packet" / "input.json"


def _fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _coverage_packet() -> dict:
    fixture = _fixture()
    return build_public_source_registry_coverage_gap_packet(
        fixture["official_source_anchors"],
        fixture["public_source_recrawl_dry_run_command_plan"],
        fixture["source_evidence_freshness_badges"],
        generated_at="2026-05-29T00:00:00Z",
    )


def _packet() -> dict:
    fixture = _fixture()
    return build_processor_handoff_manifest_rehearsal_packet(
        _coverage_packet(),
        fixture["public_source_recrawl_dry_run_command_plan"],
        generated_at="2026-05-29T01:20:00Z",
    )


def test_builds_fixture_first_processor_handoff_manifest_rehearsal_packet() -> None:
    packet = _packet()
    result = validate_processor_handoff_manifest_rehearsal_packet(packet)

    assert result.valid is True
    assert packet["fixtureFirst"] is True
    assert packet["metadataOnly"] is True
    assert packet["processorInvocationAllowed"] is False
    assert packet["processorInvoked"] is False
    assert packet["archiveArtifactWritesAllowed"] is False
    assert packet["archiveArtifactWritten"] is False
    assert packet["rawBodiesPersisted"] is False
    assert packet["rehearsalSummary"]["coveredSourceCount"] == 4
    assert packet["rehearsalSummary"]["expectedManifestCount"] == 4


def test_rehearsal_contains_prerequisites_expected_manifests_policy_notes_attestations_and_aborts() -> None:
    packet = _packet()

    prerequisites = packet["syntheticProcessorPrerequisites"]
    manifests = packet["expectedMetadataOnlyArchiveManifests"]
    attestations = packet["noRawBodyAttestations"]
    abort_ids = {row["abort_id"] for row in packet["abortConditions"]}

    assert {row["source_id"] for row in prerequisites} == {
        "ppd-public-landing",
        "ppd-online-permitting-tools",
        "devhub-public-portal",
        "ppd-devhub-faq",
    }
    assert all(row["processorInvocationAllowed"] is False for row in prerequisites)
    assert all(row["archiveArtifactWritesAllowed"] is False for row in prerequisites)
    assert all(row["no_raw_body_persisted"] is True for row in prerequisites)
    assert all(row["archive_artifact_ref"] is None for row in manifests)
    assert all(row["no_raw_body_persisted"] is True for row in manifests)
    assert all(row["metadata_only"] is True for row in manifests)
    assert all(row["raw_body_persisted"] is False for row in attestations)
    assert packet["processorPolicyVersionNotes"]["requires_separate_live_approval"] is True
    assert "processor-invocation-requested" in abort_ids
    assert "archive-artifact-write-requested" in abort_ids
    assert "raw-body-persistence-requested" in abort_ids
    assert any(abort_id.startswith("coverage-gap-") for abort_id in abort_ids)


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (lambda packet: packet.update({"processorInvoked": True}), "processorInvoked must be false"),
        (lambda packet: packet.update({"archiveArtifactWritten": True}), "archiveArtifactWritten must be false"),
        (lambda packet: packet.update({"rawBodiesPersisted": True}), "rawBodiesPersisted must be false"),
        (lambda packet: packet["syntheticProcessorPrerequisites"][0].update({"source_evidence_ids": []}), "source_evidence_ids must cite at least one evidence id"),
        (lambda packet: packet["syntheticProcessorPrerequisites"][0].update({"processorInvocationAllowed": True}), "processorInvocationAllowed must be false"),
        (lambda packet: packet["expectedMetadataOnlyArchiveManifests"][0].pop("content_hash"), "content_hash is required"),
        (lambda packet: packet["expectedMetadataOnlyArchiveManifests"][0].update({"archive_artifact_ref": "archive-artifacts/public.warc"}), "archive_artifact_ref must be empty"),
        (lambda packet: packet["expectedMetadataOnlyArchiveManifests"][0].update({"no_raw_body_persisted": False}), "no_raw_body_persisted must be true"),
        (lambda packet: packet["noRawBodyAttestations"][0].update({"raw_body_persisted": True}), "raw_body_persisted must be false"),
        (lambda packet: packet["abortConditions"].clear(), "abortConditions must include"),
        (lambda packet: packet["processorPolicyVersionNotes"].update({"processor_version": ""}), "processor_version is required"),
        (lambda packet: packet.update({"debug": "warc://public-crawl/archive"}), "forbidden raw, archive"),
    ],
)
def test_rehearsal_packet_rejects_unsafe_or_incomplete_mutations(mutation, expected: str) -> None:
    packet = copy.deepcopy(_packet())
    mutation(packet)

    with pytest.raises(ProcessorHandoffRehearsalPacketError) as exc_info:
        require_valid_processor_handoff_manifest_rehearsal_packet(packet)

    assert expected in str(exc_info.value)


def test_builder_rejects_invalid_recrawl_dry_run_command_plan() -> None:
    fixture = _fixture()
    dry_run_plan = copy.deepcopy(fixture["public_source_recrawl_dry_run_command_plan"])
    dry_run_plan["run_processor"] = True

    with pytest.raises(ProcessorHandoffRehearsalPacketError) as exc_info:
        build_processor_handoff_manifest_rehearsal_packet(
            _coverage_packet(),
            dry_run_plan,
            generated_at="2026-05-29T01:20:00Z",
        )

    assert "invalid recrawl dry-run command plan" in str(exc_info.value)
    assert "live_fetch_or_processor_execution" in str(exc_info.value)
