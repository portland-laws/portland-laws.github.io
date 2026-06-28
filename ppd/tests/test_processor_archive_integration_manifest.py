from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "processor_archive"
    / "processor_archive_integration_manifest.json"
)

SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
ALLOWED_HOSTS = {
    "www.portland.gov",
    "devhub.portlandoregon.gov",
}
FORBIDDEN_MARKERS = (
    "ppd/data/private",
    "ppd/data/raw",
    "auth-state",
    "storage-state",
    "trace.zip",
    ".har",
    "raw_http_body_path",
    "download_path",
    "rawCrawlOutputPath",
    "downloadedDocumentPath",
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
REQUIRED_PUBLIC_URLS = {
    "https://www.portland.gov/ppd",
    "https://www.portland.gov/ppd/how-use-online-permitting-tools",
    "https://devhub.portlandoregon.gov",
    "https://www.portland.gov/ppd/devhub-faqs",
    "https://www.portland.gov/ppd/devhub-sign-guide",
    "https://www.portland.gov/ppd/get-permit/apply-permits",
    "https://www.portland.gov/ppd/devhub-guide-submit-permit-application",
    "https://www.portland.gov/ppd/get-permit/submit-plans-online",
    "https://www.portland.gov/ppd/brochures-forms-handouts/permits-and-inspections-applications",
    "https://www.portland.gov/ppd/spp-file-naming-standards-preparing-pdfs",
    "https://www.portland.gov/ppd/documents/how-pay-fees/download",
}


class ProcessorArchiveIntegrationManifestTest(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_manifest_declares_fixture_only_processor_boundary(self) -> None:
        self.assertEqual("processor_archive_integration_manifest", self.manifest["fixtureKind"])
        self.assertEqual(1, self.manifest["schemaVersion"])
        self.assertTrue(self.manifest["manifestOnly"])
        self.assertFalse(self.manifest["networkAccess"])
        self.assertFalse(self.manifest["processorInvoked"])
        self.assertFalse(self.manifest["documentsDownloaded"])
        self.assertFalse(self.manifest["downloadedDocumentsIncluded"])
        self.assertFalse(self.manifest["rawBodiesIncluded"])
        self.assertFalse(self.manifest["privateDevhubArtifactsIncluded"])
        self.assertEqual("ipfs_datasets_py", self.manifest["processorSuite"]["submodulePath"])
        self.assertEqual("ipfs_datasets_py.processor", self.manifest["processorSuite"]["processorPackage"])
        self.assertEqual(
            "deferred_metadata_only_no_processor_invocation",
            self.manifest["processorSuite"]["handoffMode"],
        )

    def test_records_cover_public_source_anchors_without_fetching(self) -> None:
        records = self.manifest["records"]
        self.assertEqual(REQUIRED_PUBLIC_URLS, {record["sourceUrl"] for record in records})
        self.assertEqual(len(REQUIRED_PUBLIC_URLS), len(records))

        for record in records:
            parsed = urlparse(record["sourceUrl"])
            self.assertEqual("https", parsed.scheme)
            self.assertIn(parsed.netloc, ALLOWED_HOSTS)
            self.assertEqual(record["sourceUrl"], record["canonicalUrl"])
            self.assertIn(record["sourceType"], {"public_html", "public_pdf", "public_form", "devhub_public"})
            self.assertEqual("pending_live_preflight_before_any_fetch", record["robotsPolicyPlaceholder"])

    def test_records_map_public_sources_to_documents_hashes_and_handoff_ids(self) -> None:
        records = self.manifest["records"]
        seen_handoffs: set[str] = set()
        seen_documents: set[str] = set()
        seen_hashes: set[str] = set()

        for record in records:
            self.assertRegex(record["contentHashPlaceholder"], SHA256_RE)
            self.assertTrue(record["sourceEvidenceId"].startswith("src-"))
            self.assertTrue(record["canonicalDocumentId"].startswith("doc-"))
            self.assertTrue(record["processorArchiveRecordId"].startswith("archive-"))
            self.assertTrue(record["processorHandoffId"].startswith("handoff-"))
            self.assertTrue(record["processorHandoffId"].endswith("archive-manifest"))
            self.assertEqual(
                f"normalized_documents/{record['canonicalDocumentId']}.json",
                record["normalizedDocumentRef"],
            )
            self.assertEqual(
                f"metadata_only_archive_manifests/{record['processorArchiveRecordId']}.json",
                record["archiveArtifactRef"],
            )
            self.assertIn("etag", record["httpCachePlaceholder"])
            self.assertTrue(record["httpCachePlaceholder"]["lastModified"].endswith("Z"))
            self.assertTrue(REQUIRED_SKIPPED_ARTIFACTS.issubset(set(record["skippedArtifacts"])))
            seen_handoffs.add(record["processorHandoffId"])
            seen_documents.add(record["canonicalDocumentId"])
            seen_hashes.add(record["contentHashPlaceholder"])

        self.assertEqual(len(records), len(seen_handoffs))
        self.assertEqual(len(records), len(seen_documents))
        self.assertEqual(len(records), len(seen_hashes))

    def test_processor_inputs_are_metadata_only_and_non_invoking(self) -> None:
        for index, record in enumerate(self.manifest["records"]):
            processor_input = record["processorInput"]
            self.assertEqual("capture_url_metadata_only", processor_input["operation"])
            self.assertTrue(processor_input["metadataOnly"])
            self.assertFalse(processor_input["persistRawBody"])
            self.assertFalse(processor_input["downloadDocuments"])
            self.assertNotIn("body", processor_input, f"records[{index}] must not carry raw body data")
            self.assertNotIn("documentBytes", processor_input, f"records[{index}] must not carry document bytes")

    def test_manifest_rejects_private_raw_or_consequential_artifact_surface(self) -> None:
        serialized = json.dumps(self.manifest, sort_keys=True).lower()
        for marker in FORBIDDEN_MARKERS:
            self.assertNotIn(marker.lower(), serialized)
        self.assertTrue(FORBIDDEN_ACTIONS.issubset(set(self.manifest["forbiddenActions"])))

    def test_negative_mutation_missing_handoff_private_path_or_live_fetch_fails_local_validator(self) -> None:
        broken = json.loads(json.dumps(self.manifest))
        broken["records"][0]["processorHandoffId"] = ""
        broken["records"][1]["privatePath"] = "ppd/data/private/devhub-auth-state.json"
        broken["records"][2]["processorInput"]["persistRawBody"] = True
        broken["networkAccess"] = True

        errors = validate_manifest_shape(broken)

        self.assertIn("networkAccess must be false", errors)
        self.assertIn("records[0].processorHandoffId is required", errors)
        self.assertIn("private/runtime marker present", errors)
        self.assertIn("records[2].processorInput.persistRawBody must be false", errors)


def validate_manifest_shape(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    serialized = json.dumps(manifest, sort_keys=True).lower()
    if manifest.get("networkAccess") is not False:
        errors.append("networkAccess must be false")
    if manifest.get("documentsDownloaded") is not False:
        errors.append("documentsDownloaded must be false")
    if manifest.get("rawBodiesIncluded") is not False:
        errors.append("rawBodiesIncluded must be false")
    if any(marker.lower() in serialized for marker in FORBIDDEN_MARKERS):
        errors.append("private/runtime marker present")
    for index, record in enumerate(manifest.get("records", [])):
        if not record.get("processorHandoffId"):
            errors.append(f"records[{index}].processorHandoffId is required")
        if not SHA256_RE.match(str(record.get("contentHashPlaceholder", ""))):
            errors.append(f"records[{index}].contentHashPlaceholder must be sha256")
        processor_input = record.get("processorInput", {})
        if processor_input.get("metadataOnly") is not True:
            errors.append(f"records[{index}].processorInput.metadataOnly must be true")
        if processor_input.get("persistRawBody") is not False:
            errors.append(f"records[{index}].processorInput.persistRawBody must be false")
        if processor_input.get("downloadDocuments") is not False:
            errors.append(f"records[{index}].processorInput.downloadDocuments must be false")
    return errors


if __name__ == "__main__":
    unittest.main()
