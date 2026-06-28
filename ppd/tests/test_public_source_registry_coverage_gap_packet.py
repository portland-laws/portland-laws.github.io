from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ppd.source_anchor_matrix import ORIGINAL_PUBLIC_SOURCE_ANCHORS
from ppd.source_registry_coverage_gap_packet import (
    PublicSourceRegistryCoverageGapPacketError,
    build_public_source_registry_coverage_gap_packet,
    require_valid_public_source_registry_coverage_gap_packet,
    validate_public_source_registry_coverage_gap_packet,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "public_source_registry_coverage_gap_packet" / "input.json"


def _fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _packet() -> dict:
    fixture = _fixture()
    return build_public_source_registry_coverage_gap_packet(
        fixture["official_source_anchors"],
        fixture["public_source_recrawl_dry_run_command_plan"],
        fixture["source_evidence_freshness_badges"],
        generated_at="2026-05-29T00:00:00Z",
    )


def test_builds_fixture_first_registry_coverage_gap_packet() -> None:
    packet = _packet()
    result = validate_public_source_registry_coverage_gap_packet(packet)

    assert result.valid is True
    assert packet["fixtureFirst"] is True
    assert packet["liveCrawlingUsed"] is False
    assert packet["documentsDownloaded"] is False
    assert packet["activeSourceRegistryMutated"] is False
    assert packet["rawBodiesPersisted"] is False
    assert packet["coverageSummary"]["officialAnchorCount"] == len(ORIGINAL_PUBLIC_SOURCE_ANCHORS)
    assert packet["coverageSummary"]["citedCoveredAnchorCount"] == 4
    assert packet["coverageSummary"]["missingAnchorCount"] == 8


def test_packet_reports_cited_covered_missing_skipped_stale_and_owner_rows() -> None:
    packet = _packet()

    covered_urls = {row["canonical_url"] for row in packet["citedCoveredAnchors"]}
    missing_urls = {row["canonical_url"] for row in packet["missingAnchors"]}
    skipped_reasons = {row["reason"] for row in packet["skippedSourceReasons"]}
    stale_urls = {row["canonical_url"] for row in packet["staleSourceNotes"]}
    owner_urls = {row["canonical_url"] for row in packet["reviewerOwnerAssignments"]}

    assert covered_urls == {
        "https://www.portland.gov/ppd",
        "https://www.portland.gov/ppd/how-use-online-permitting-tools",
        "https://devhub.portlandoregon.gov",
        "https://www.portland.gov/ppd/devhub-faqs",
    }
    assert covered_urls | missing_urls == set(ORIGINAL_PUBLIC_SOURCE_ANCHORS)
    assert skipped_reasons == {
        "outside_allowlist",
        "unsupported_scheme",
        "private_authenticated",
        "disallowed_by_robots_or_policy",
        "raw_download_not_permitted",
        "too_large",
        "unsupported_content_type",
    }
    assert "https://www.portland.gov/ppd/documents/how-pay-fees/download" in stale_urls
    assert owner_urls == set(ORIGINAL_PUBLIC_SOURCE_ANCHORS)
    assert all(row["raw_body_stored"] is False for row in packet["skippedSourceReasons"])


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (lambda packet: packet.update({"liveCrawlingUsed": True}), "liveCrawlingUsed must be false"),
        (lambda packet: packet.update({"documentsDownloaded": True}), "documentsDownloaded must be false"),
        (lambda packet: packet.update({"activeSourceRegistryMutated": True}), "activeSourceRegistryMutated must be false"),
        (lambda packet: packet.update({"liveFetchUsed": True}), "must not claim live fetch"),
        (lambda packet: packet.update({"raw_archive_ref": "warc://public-crawl/archive"}), "raw_archive_ref must not contain"),
        (lambda packet: packet["sourceRegistryMutation"].update({"registryEditStatus": "applied"}), "registryEditStatus must be not_applied"),
        (lambda packet: packet["sourceRegistryMutation"].update({"activeRegistryMutated": True}), "activeRegistryMutated must be false"),
        (lambda packet: packet["citedCoveredAnchors"][0].update({"source_evidence_ids": []}), "source_evidence_ids must cite at least one evidence id"),
        (lambda packet: packet["missingAnchors"][0].update({"source_evidence_ids": []}), "source_evidence_ids must cite at least one evidence id"),
        (lambda packet: packet["missingAnchors"][0].update({"reviewer_owner": ""}), "missingAnchors[0].reviewer_owner is required"),
        (lambda packet: packet["missingAnchors"][0].update({"missing_reason": ""}), "missingAnchors[0].missing_reason is required"),
        (lambda packet: packet["citedCoveredAnchors"][0].update({"canonical_url": "https://example.com/ppd"}), "canonical_url must be an official source anchor"),
        (lambda packet: packet["citedCoveredAnchors"][0].update({"canonical_url": "https://devhub.portlandoregon.gov/private/account"}), "must not be a private or authenticated target"),
        (lambda packet: packet["reviewerOwnerAssignments"].pop(), "reviewerOwnerAssignments must cover every official source anchor"),
        (lambda packet: packet.update({"skippedSourceReasons": []}), "skippedSourceReasons must include cited skip decisions"),
        (lambda packet: packet["skippedSourceReasons"][0].update({"reason": ""}), "reason is not an allowed skip reason"),
        (lambda packet: packet["skippedSourceReasons"][0].update({"cited_policy_evidence_id": ""}), "cited_policy_evidence_id is required"),
        (lambda packet: packet["skippedSourceReasons"][0].update({"raw_body_stored": True}), "raw_body_stored must be false"),
        (lambda packet: packet["staleSourceNotes"][0].update({"source_evidence_ids": []}), "source_evidence_ids must cite at least one evidence id"),
        (lambda packet: packet.update({"raw_html": "raw page body"}), "raw_html must not contain private"),
    ],
)
def test_packet_rejects_unsafe_or_incomplete_mutations(mutation, expected: str) -> None:
    packet = copy.deepcopy(_packet())
    mutation(packet)

    with pytest.raises(PublicSourceRegistryCoverageGapPacketError) as exc_info:
        require_valid_public_source_registry_coverage_gap_packet(packet)

    assert expected in str(exc_info.value)


def test_builder_rejects_invalid_dry_run_command_plan() -> None:
    fixture = _fixture()
    fixture["public_source_recrawl_dry_run_command_plan"].update({"live_fetch": True})

    with pytest.raises(PublicSourceRegistryCoverageGapPacketError) as exc_info:
        build_public_source_registry_coverage_gap_packet(
            fixture["official_source_anchors"],
            fixture["public_source_recrawl_dry_run_command_plan"],
            fixture["source_evidence_freshness_badges"],
            generated_at="2026-05-29T00:00:00Z",
        )

    assert "invalid dry-run command plan" in str(exc_info.value)
    assert "live_fetch_or_processor_execution" in str(exc_info.value)
