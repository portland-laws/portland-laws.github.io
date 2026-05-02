from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "processor_archive"
    / "processor_archive_integration_manifest.json"
)

SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
FORBIDDEN_MARKERS = (
    "ppd/data/private",
    "ppd/data/raw",
    "auth-state",
    "storage-state",
    "trace.zip",
    ".har",
    "raw_http_body_path",
    "download_path",
)
REQUIRED_SKIPPED_ARTIFACTS = {
    "raw_http_body",
    "downloaded_document_bytes",
    "browser_trace",
    "screenshot",
    "private_devhub_state",
}
FORBIDDEN_ACTIONS = {
    "crawl_network",
    "download_documents",
    "store_raw_bodies",
    "read_private_devhub_data",
    "launch_browser",
    "authenticate",
    "upload",
    "submit",
    "pay",
    "certify",
    "cancel",
    "schedule_inspection",
}


class ProcessorArchiveIntegrationManifestTest(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_manifest_declares_fixture_only_processor_boundary(self) -> None:
        self.assertEqual("processor_archive_integration_manifest", self.manifest["fixtureKind"])
        self.assertEqual(1, self.manifest["schemaVersion"])
        self.assertTrue(self.manifest["manifestOnly"])
        self.assertFalse(self.manifest["networkAccess"])
        self.assertFalse(self.manifest["downloadedDocumentsIncluded"])
        self.assertFalse(self.manifest["rawBodiesIncluded"])
        self.assertFalse(self.manifest["privateDevhubArtifactsIncluded"])
        self.assertEqual("ipfs_datasets_py", self.manifest["processorSuite"]["submodulePath"])
        self.assertEqual("ipfs_datasets_py.processor", self.manifest["processorSuite"]["processorPackage"])

    def test_records_map_public_sources_to_archive_and_processor_handoff_ids(self) -> None:
        records = self.manifest["records"]
        self.assertGreaterEqual(len(records), 2)
        seen_handoffs: set[str] = set()
        seen_documents: set[str] = set()

        for record in records:
            self.assertTrue(record["sourceUrl"].startswith("https://www.portland.gov/ppd/"))
            self.assertTrue(record["canonicalUrl"].startswith("https://www.portland.gov/ppd/"))
            self.assertRegex(record["contentHashPlaceholder"], SHA256_RE)
            self.assertTrue(record["sourceEvidenceId"].startswith("src-ppd-"))
            self.assertTrue(record["canonicalDocumentId"].startswith("doc-ppd-"))
            self.assertTrue(record["processorArchiveRecordId"].startswith("archive-ppd-"))
            self.assertTrue(record["processorHandoffId"].startswith("handoff-ppd-"))
            self.assertTrue(record["processorHandoffId"].endswith("formal-logic"))
            self.assertIn("etag", record["httpCachePlaceholder"])
            self.assertTrue(record["httpCachePlaceholder"]["lastModified"].endswith("Z"))
            self.assertTrue(REQUIRED_SKIPPED_ARTIFACTS.issubset(set(record["skippedArtifacts"])))
            seen_handoffs.add(record["processorHandoffId"])
            seen_documents.add(record["canonicalDocumentId"])

        self.assertEqual(len(records), len(seen_handoffs))
        self.assertEqual(len(records), len(seen_documents))

    def test_manifest_rejects_private_raw_or_consequential_artifact_surface(self) -> None:
        serialized = json.dumps(self.manifest, sort_keys=True).lower()
        for marker in FORBIDDEN_MARKERS:
            self.assertNotIn(marker, serialized)
        self.assertTrue(FORBIDDEN_ACTIONS.issubset(set(self.manifest["forbiddenActions"])))

    def test_negative_mutation_missing_handoff_or_private_path_fails_local_validator(self) -> None:
        broken = json.loads(json.dumps(self.manifest))
        broken["records"][0]["processorHandoffId"] = ""
        broken["records"][1]["privatePath"] = "ppd/data/private/devhub-auth-state.json"

        errors = validate_manifest_shape(broken)

        self.assertIn("records[0].processorHandoffId is required", errors)
        self.assertIn("private/runtime marker present", errors)


def validate_manifest_shape(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    serialized = json.dumps(manifest, sort_keys=True).lower()
    if any(marker in serialized for marker in FORBIDDEN_MARKERS):
        errors.append("private/runtime marker present")
    for index, record in enumerate(manifest.get("records", [])):
        if not record.get("processorHandoffId"):
            errors.append(f"records[{index}].processorHandoffId is required")
        if not str(record.get("contentHashPlaceholder", "")).startswith("sha256:"):
            errors.append(f"records[{index}].contentHashPlaceholder must be sha256")
    return errors


if __name__ == "__main__":
    unittest.main()
