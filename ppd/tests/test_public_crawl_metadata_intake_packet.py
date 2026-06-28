from __future__ import annotations

import json
import unittest
from pathlib import Path

from ppd.crawler.public_crawl_metadata_intake_packet import (
    assert_public_crawl_metadata_intake_packet,
    build_public_crawl_metadata_intake_packet,
    validate_public_crawl_metadata_intake_packet,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "public_crawl_metadata_intake"


class PublicCrawlMetadataIntakePacketTests(unittest.TestCase):
    def _load(self, name: str) -> dict[str, object]:
        return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))

    def test_fixture_packet_consumes_promotion_manifest(self) -> None:
        promotion_manifest = self._load("promotion_manifest.json")
        packet = self._load("metadata_intake_packet.json")

        summary = assert_public_crawl_metadata_intake_packet(packet, promotion_manifest)

        self.assertEqual(summary.packet_id, "fixture-public-crawl-metadata-intake-001")
        self.assertEqual(summary.promotion_manifest_id, promotion_manifest["manifest_id"])
        self.assertEqual(summary.selected_target_count, 2)
        self.assertEqual(summary.skipped_target_count, 1)
        self.assertEqual(summary.expected_archive_manifest_count, 2)

    def test_builder_records_operator_acknowledgement_and_attestations(self) -> None:
        promotion_manifest = self._load("promotion_manifest.json")

        packet = build_public_crawl_metadata_intake_packet(
            promotion_manifest,
            selected_source_ids=["ppd-landing", "ppd-apply-permits"],
        )

        errors = validate_public_crawl_metadata_intake_packet(packet, promotion_manifest)
        self.assertEqual(errors, [])
        acknowledgement = packet["synthetic_operator_acknowledgement"]
        self.assertEqual(acknowledgement["operator_id"], "synthetic-operator-fixture")
        self.assertTrue(acknowledgement["acknowledged_fixture_only_dry_run"])
        self.assertTrue(acknowledgement["acknowledged_no_live_authority"])
        self.assertEqual(
            sorted(packet["expected_archive_manifest_ids"]),
            ["archive-manifest-expected-ppd-apply-permits", "archive-manifest-expected-ppd-landing"],
        )
        for attestation in packet["no_raw_body_attestations"]:
            self.assertTrue(attestation["no_raw_body_persisted"])
            self.assertFalse(attestation["raw_body_persisted"])
            self.assertFalse(attestation["downloaded_documents"])
            self.assertFalse(attestation["live_network_invoked"])

    def test_rejects_raw_body_or_live_execution_claims(self) -> None:
        promotion_manifest = self._load("promotion_manifest.json")
        packet = self._load("metadata_intake_packet.json")
        packet["live_network_invoked"] = True
        packet["selected_allowlisted_targets"][0]["raw_body"] = "not allowed"

        errors = validate_public_crawl_metadata_intake_packet(packet, promotion_manifest)

        self.assertIn("live_network_invoked must be false", errors)
        self.assertTrue(any("raw_body" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
