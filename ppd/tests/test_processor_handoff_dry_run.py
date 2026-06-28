from __future__ import annotations

import json
import unittest
from pathlib import Path

from ppd.crawler.processor_handoff_dry_run import (
    build_processor_handoff_dry_run_packet,
    validate_processor_handoff_dry_run_packet,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "processor_handoff_dry_run" / "reviewed_recrawl_batch.json"


class ProcessorHandoffDryRunTests(unittest.TestCase):
    def load_fixture(self) -> dict:
        return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_builds_metadata_only_handoff_packet_from_reviewed_recrawl_fixture(self) -> None:
        packet = build_processor_handoff_dry_run_packet(
            self.load_fixture(),
            generated_at="2026-05-28T20:06:00Z",
        )

        self.assertEqual(packet["packetType"], "ppd_processor_handoff_dry_run")
        self.assertEqual(packet["executionPolicy"]["networkInvoked"], False)
        self.assertEqual(packet["executionPolicy"]["processorInvoked"], False)
        self.assertEqual(packet["executionPolicy"]["metadataOnly"], True)

        document = packet["documents"][0]
        processor_input = document["processorInput"]
        archive_manifest = document["archiveManifestMetadata"]
        normalized_ref = document["normalizedDocumentReference"]
        output_paths = document["metadataOnlyOutputPaths"]

        self.assertEqual(processor_input["processor"]["operation"], "capture_url_metadata_only")
        self.assertEqual(processor_input["processor"]["version"], "fixture-pinned-2026-05-28")
        self.assertEqual(processor_input["arguments"]["metadataOnly"], True)
        self.assertEqual(processor_input["arguments"]["persistRawBody"], False)
        self.assertEqual(processor_input["arguments"]["downloadDocuments"], False)
        self.assertEqual(archive_manifest["contentHash"], processor_input["arguments"]["expectedContentHash"])
        self.assertEqual(normalized_ref["contentHash"], archive_manifest["contentHash"])
        self.assertEqual(archive_manifest["processorVersion"], processor_input["processor"]["version"])
        self.assertTrue(archive_manifest["noRawBodyPersisted"])
        self.assertFalse(normalized_ref["contentPersisted"])
        self.assertEqual(archive_manifest["archiveArtifactRef"], output_paths["archiveManifestPath"])
        self.assertEqual(normalized_ref["outputPath"], output_paths["normalizedDocumentPath"])
        self.assertTrue(output_paths["archiveManifestPath"].startswith("metadata_outputs/"))

        self.assertEqual(validate_processor_handoff_dry_run_packet(packet), [])

    def test_rejects_live_execution_and_raw_artifact_fields(self) -> None:
        packet = build_processor_handoff_dry_run_packet(
            self.load_fixture(),
            generated_at="2026-05-28T20:06:00Z",
        )
        packet["executionPolicy"]["networkInvoked"] = True
        packet["documents"][0]["processorInput"]["arguments"]["raw_body"] = "not committed"

        errors = validate_processor_handoff_dry_run_packet(packet)

        self.assertIn("executionPolicy.networkInvoked must be false", errors)
        self.assertTrue(any("raw_body is not allowed" in error for error in errors))

    def test_rejects_private_devhub_handoff_urls(self) -> None:
        fixture = self.load_fixture()
        fixture["documents"][0]["canonicalUrl"] = "https://devhub.portlandoregon.gov/permits/123"

        with self.assertRaises(ValueError):
            build_processor_handoff_dry_run_packet(
                fixture,
                generated_at="2026-05-28T20:06:00Z",
            )


if __name__ == "__main__":
    unittest.main()
