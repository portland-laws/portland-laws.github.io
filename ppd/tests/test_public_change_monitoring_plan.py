"""Validate the fixture-only public PP&D change-monitoring plan."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from urllib.parse import urlparse


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "change_monitoring"
    / "public_ppd_change_monitoring_plan.json"
)


class PublicChangeMonitoringPlanTest(unittest.TestCase):
    def setUp(self) -> None:
        with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
            self.plan = json.load(fixture_file)

    def test_plan_is_fixture_only_without_live_collection_artifacts(self) -> None:
        self.assertEqual(self.plan["schemaVersion"], 1)
        self.assertTrue(self.plan["fixtureOnly"])
        self.assertFalse(self.plan["networkAccessAllowed"])
        self.assertFalse(self.plan["rawCrawlOutputAllowed"])
        self.assertFalse(self.plan["downloadedDocumentsAllowed"])

        serialized = json.dumps(self.plan, sort_keys=True).lower()
        forbidden_fragments = (
            "ppd/data/raw",
            "ppd/data/private",
            "storage_state",
            "auth_state",
            "trace.zip",
            "screenshots/",
            "downloads/",
            "raw_body",
            "response_body",
        )
        for fragment in forbidden_fragments:
            self.assertNotIn(fragment, serialized)

    def test_plan_lists_one_high_change_guidance_page_and_one_low_change_artifact(self) -> None:
        artifacts = self.plan["monitoredArtifacts"]
        self.assertEqual(len(artifacts), 2)

        high_change = [item for item in artifacts if item["changeLikelihood"] == "high"]
        low_change = [item for item in artifacts if item["changeLikelihood"] == "low"]
        self.assertEqual(len(high_change), 1)
        self.assertEqual(len(low_change), 1)
        self.assertEqual(high_change[0]["artifactType"], "public_guidance_page")
        self.assertEqual(low_change[0]["artifactType"], "public_pdf_or_form_artifact")

    def test_artifacts_have_public_urls_cadence_hashes_headers_and_categories(self) -> None:
        allowed_hosts = set(self.plan["scope"]["allowedHosts"])
        allowed_categories = {category["id"] for category in self.plan["changeReportCategories"]}
        self.assertGreaterEqual(len(allowed_categories), 5)

        for artifact in self.plan["monitoredArtifacts"]:
            parsed_source = urlparse(artifact["sourceUrl"])
            parsed_canonical = urlparse(artifact["canonicalUrl"])
            self.assertEqual(parsed_source.scheme, "https")
            self.assertEqual(parsed_canonical.scheme, "https")
            self.assertIn(parsed_source.netloc, allowed_hosts)
            self.assertIn(parsed_canonical.netloc, allowed_hosts)
            self.assertIn(
                artifact["recrawlCadence"],
                {"daily", "weekly", "monthly", "monthly_unless_linked_page_changed"},
            )
            self.assertGreaterEqual(len(artifact["hashFields"]), 2)
            self.assertGreaterEqual(len(artifact["headerFields"]), 3)
            self.assertIn("etag", artifact["headerFields"])
            self.assertIn("last-modified", artifact["headerFields"])
            self.assertGreaterEqual(len(artifact["reportCategories"]), 2)
            self.assertTrue(set(artifact["reportCategories"]).issubset(allowed_categories))
            self.assertIn("do not", artifact["storedEvidencePolicy"].lower())


if __name__ == "__main__":
    unittest.main()
