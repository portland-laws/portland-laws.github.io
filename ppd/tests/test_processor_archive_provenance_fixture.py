"""Validate PP&D processor-archive provenance fixture continuity.

This fixture is intentionally deterministic. It links public crawl dry-run URLs
through processor handoff manifests, source-index records, and normalized
document provenance without invoking network or processor code.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "processor_archive" / "provenance_chain.json"
FORBIDDEN_KEYS = {
    "auth",
    "authState",
    "body",
    "cookies",
    "credentials",
    "html",
    "password",
    "rawBody",
    "rawHtml",
    "screenshot",
    "session",
    "storageState",
    "token",
    "trace",
}
FORBIDDEN_VALUE_PARTS = (
    "ppd/data/private",
    "ppd/data/raw",
    "storage_state",
    "trace.zip",
    "playwright-report",
    "downloaded_documents",
)


class ProcessorArchiveProvenanceFixtureTest(unittest.TestCase):
    def setUp(self) -> None:
        with FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
            self.fixture: dict[str, Any] = json.load(fixture_file)

    def test_fixture_is_manifest_only_and_offline(self) -> None:
        self.assertEqual(1, self.fixture["schemaVersion"])
        self.assertIs(False, self.fixture["networkAccess"])
        self.assertIs(False, self.fixture["processorInvocation"])
        self.assertIs(True, self.fixture["manifestOnly"])

    def test_public_dry_run_urls_link_to_handoff_source_index_and_normalized_docs(self) -> None:
        crawl_entries = self.fixture["publicCrawlDryRun"]["entries"]
        handoffs = self.fixture["processorHandoffManifests"]
        source_records = self.fixture["sourceIndexRecords"]
        normalized_docs = self.fixture["normalizedDocuments"]

        crawl_by_id = {entry["dryRunUrlId"]: entry for entry in crawl_entries}
        handoff_by_id = {handoff["archiveManifestId"]: handoff for handoff in handoffs}
        source_by_id = {record["sourceIndexId"]: record for record in source_records}

        self.assertEqual(len(crawl_entries), len(crawl_by_id))
        self.assertEqual(len(handoffs), len(handoff_by_id))
        self.assertEqual(len(source_records), len(source_by_id))
        self.assertGreaterEqual(len(normalized_docs), 1)

        for handoff in handoffs:
            crawl = crawl_by_id[handoff["dryRunUrlId"]]
            self.assertEqual("allow", crawl["decision"])
            self.assertEqual(crawl["url"], handoff["sourceUrl"])
            self.assertEqual(crawl["canonicalUrl"], handoff["canonicalUrl"])
            self.assertIs(True, handoff["manifestOnly"])
            self.assertIs(False, handoff["processorInvoked"])
            self.assertEqual("ipfs_datasets_py/ipfs_datasets_py/processors", handoff["processor"]["backendPath"])
            self.assertEqual("allow", handoff["policyDecision"]["decision"])
            self.assertIn("public_ppd_allowlisted", handoff["policyDecision"]["reasons"])
            self.assertIn("robots_allowed", handoff["policyDecision"]["reasons"])
            self.assertIn("no_persist_approved", handoff["policyDecision"]["reasons"])

        for record in source_records:
            handoff = handoff_by_id[record["archiveManifestId"]]
            self.assertEqual(handoff["sourceUrl"], record["sourceUrl"])
            self.assertEqual(handoff["canonicalUrl"], record["canonicalUrl"])
            self.assertEqual(handoff["contentHash"], record["contentHash"])
            self.assertEqual("dry_run_planned", record["crawlStatus"])

        for document in normalized_docs:
            source = source_by_id[document["sourceIndexId"]]
            provenance = document["provenance"]
            handoff = handoff_by_id[provenance["archiveManifestId"]]
            crawl = crawl_by_id[provenance["dryRunUrlId"]]
            self.assertEqual(source["sourceUrl"], document["sourceUrl"])
            self.assertEqual(source["canonicalUrl"], document["canonicalUrl"])
            self.assertEqual(source["contentHash"], provenance["contentHash"])
            self.assertEqual(handoff["sourceUrl"], document["sourceUrl"])
            self.assertEqual(crawl["url"], document["sourceUrl"])
            self.assertIs(False, provenance["normalizerInvoked"])
            self.assertGreaterEqual(len(provenance["sourceEvidenceIds"]), 1)
            section_evidence_ids = {section["sourceEvidenceId"] for section in document["sections"]}
            self.assertTrue(set(provenance["sourceEvidenceIds"]).issubset(section_evidence_ids))

    def test_fixture_contains_no_private_or_raw_artifacts(self) -> None:
        findings: list[str] = []
        self._walk_forbidden_values(self.fixture, "$", findings)
        self.assertEqual([], findings)

    def _walk_forbidden_values(self, value: Any, path: str, findings: list[str]) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = f"{path}.{key}"
                if key in FORBIDDEN_KEYS:
                    findings.append(f"{child_path} uses forbidden key")
                self._walk_forbidden_values(child, child_path, findings)
            return

        if isinstance(value, list):
            for index, child in enumerate(value):
                self._walk_forbidden_values(child, f"{path}[{index}]", findings)
            return

        if isinstance(value, str):
            normalized = value.replace("\\", "/")
            for forbidden_part in FORBIDDEN_VALUE_PARTS:
                if forbidden_part in normalized:
                    findings.append(f"{path} contains {forbidden_part}")


if __name__ == "__main__":
    unittest.main()
