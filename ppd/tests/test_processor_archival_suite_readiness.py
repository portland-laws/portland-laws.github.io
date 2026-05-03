from __future__ import annotations

import json
import unittest
from pathlib import Path


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "processor" / "archival_suite_readiness.json"
FORBIDDEN_MARKERS = (
    "ppd/data/private",
    "auth-state",
    "storage-state",
    "trace.zip",
    ".har",
    "cookie",
    "password",
    "token",
)


class ProcessorArchivalSuiteReadinessTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_fixture_targets_processor_metadata_only_handoff(self) -> None:
        self.assertEqual("processor_archival_suite_readiness", self.fixture["fixtureKind"])
        suite = self.fixture["processorSuite"]
        self.assertEqual("ipfs_datasets_py", suite["submodule"])
        self.assertEqual("processor", suite["module"])
        self.assertEqual("public_source_archival_metadata_only", suite["handoffMode"])
        self.assertTrue(suite["contentHashPlaceholdersOnly"])

    def test_public_sources_have_processor_handoff_ids_and_citations(self) -> None:
        for source in self.fixture["publicSources"]:
            self.assertTrue(source["sourceUrl"].startswith("https://www.portland.gov/ppd/"))
            self.assertTrue(source["canonicalDocumentId"].startswith("ppd-public-"))
            self.assertTrue(source["contentHashPlaceholder"].startswith("sha256:[PUBLIC_ARCHIVE_HASH_PLACEHOLDER_"))
            self.assertTrue(source["processorHandoffId"].startswith("processor-handoff-ppd-"))
            self.assertTrue(source["extractionBatchId"].startswith("extract-batch-"))
            self.assertTrue(source["citation"]["locator"])
            self.assertTrue(source["citation"]["paraphrase"])

    def test_extraction_batches_are_source_linked_without_raw_bodies(self) -> None:
        evidence_ids = {source["sourceEvidenceId"] for source in self.fixture["publicSources"]}
        for batch in self.fixture["extractionBatches"]:
            self.assertTrue(set(batch["requiresSourceEvidenceIds"]).issubset(evidence_ids))
            self.assertIn(batch["outputContract"], {"formal_requirement_nodes", "draft_playwright_planning_hints"})
            self.assertFalse(batch["rawBodyAvailableToAgent"])

    def test_boundary_refuses_live_crawl_and_private_artifacts(self) -> None:
        boundary = self.fixture["boundary"]
        self.assertTrue(boundary["fixtureOnly"])
        self.assertFalse(boundary["liveCrawlRequested"])
        self.assertFalse(boundary["rawBodyStored"])
        self.assertFalse(boundary["downloadedDocumentStored"])
        self.assertFalse(boundary["privateDevhubDataStored"])
        outcome = self.fixture["plannerOutcome"]
        self.assertFalse(outcome["mayRunLiveCrawl"])
        self.assertTrue(outcome["mayUseProcessorHandoffMetadata"])
        self.assertTrue(outcome["mayExtractRequirementNodes"])
        self.assertFalse(outcome["mayPlanAuthenticatedDevhubActions"])

        serialized = json.dumps(self.fixture, sort_keys=True).lower()
        for marker in FORBIDDEN_MARKERS:
            self.assertNotIn(marker, serialized)


if __name__ == "__main__":
    unittest.main()
