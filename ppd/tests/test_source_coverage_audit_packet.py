from __future__ import annotations

import copy
from pathlib import Path

import pytest

from ppd.source_anchor_matrix import ORIGINAL_PUBLIC_SOURCE_ANCHORS
from ppd.source_coverage_audit_packet import (
    SourceCoverageAuditPacketError,
    load_audit_packet,
    source_ids_by_anchor,
    validate_audit_packet,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "source_coverage_audit_packet.json"


def test_source_coverage_audit_packet_covers_all_official_anchors() -> None:
    packet = load_audit_packet(FIXTURE_PATH)

    official_urls = {row["canonical_url"] for row in packet["officialAnchors"]}
    registry_urls = {row["canonical_url"] for row in packet["sourceRegistryRecords"]}
    audit_urls = {row["canonical_url"] for row in packet["auditRows"]}

    assert official_urls == set(ORIGINAL_PUBLIC_SOURCE_ANCHORS)
    assert registry_urls == official_urls
    assert audit_urls == official_urls


def test_source_coverage_audit_packet_links_registry_to_downstream_controls() -> None:
    packet = load_audit_packet(FIXTURE_PATH)
    source_map = source_ids_by_anchor(packet)
    links_by_source = {row["source_id"]: row for row in packet["downstreamLinks"]}

    assert source_map["https://www.portland.gov/ppd/documents/how-pay-fees/download"] == "ppd-how-pay-fees-pdf"
    assert links_by_source["ppd-how-pay-fees-pdf"]["guardrail_bundle_ids"] == ["guardrail-financial-actions"]
    assert links_by_source["ppd-submit-plans-online-single-pdf"]["requirement_ids"] == ["req-single-pdf-plan-set"]


def test_source_coverage_audit_packet_records_all_skip_reason_categories() -> None:
    packet = load_audit_packet(FIXTURE_PATH)

    reasons = {row["reason"] for row in packet["skippedUrls"]}

    assert reasons == {
        "outside_allowlist",
        "unsupported_scheme",
        "private_authenticated",
        "disallowed_by_robots_or_policy",
        "raw_download_not_permitted",
        "too_large",
        "unsupported_content_type",
    }
    assert all(row["raw_body_stored"] is False for row in packet["skippedUrls"])


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (lambda packet: packet.update({"liveCrawlingUsed": True}), "liveCrawlingUsed must be false"),
        (lambda packet: packet.update({"rawBodiesPersisted": True}), "rawBodiesPersisted must be false"),
        (lambda packet: packet["officialAnchors"].pop(), "officialAnchors missing URLs"),
        (lambda packet: packet["sourceRegistryRecords"].pop(), "sourceRegistryRecords missing official anchors"),
        (lambda packet: packet["sourceRegistryRecords"][0].update({"owning_surface": ""}), "owning_surface is required"),
        (lambda packet: packet["sourceRegistryRecords"][0].update({"crawl_frequency": "eventually"}), "crawl_frequency is not an allowed freshness cadence"),
        (lambda packet: packet["skippedUrls"].pop(), "skippedUrls missing reason coverage"),
        (lambda packet: packet["downstreamLinks"][0].update({"guardrail_bundle_ids": []}), "guardrail_bundle_ids must be a non-empty list"),
        (lambda packet: packet["auditRows"][0].update({"raw_body_stored": True}), "raw_body_stored must be false"),
        (lambda packet: packet.update({"raw_html": "raw page body"}), "raw_html must not contain private, raw, or authenticated content"),
    ],
)
def test_source_coverage_audit_packet_rejects_unsafe_or_incomplete_mutations(mutation, expected: str) -> None:
    packet = copy.deepcopy(load_audit_packet(FIXTURE_PATH))
    mutation(packet)

    with pytest.raises(SourceCoverageAuditPacketError) as exc_info:
        validate_audit_packet(packet)

    assert expected in str(exc_info.value)
