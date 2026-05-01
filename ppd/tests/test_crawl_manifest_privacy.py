"""Fixture-backed privacy validation for crawl session manifests."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from ppd.contracts.crawl_manifest_privacy import (
    assert_crawl_manifest_privacy,
    validate_crawl_manifest_privacy,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "crawl_manifest_privacy"


class CrawlManifestPrivacyValidationTest(unittest.TestCase):
    def test_accepts_safe_public_planning_manifest(self) -> None:
        manifest = _load_fixture("safe_public_planning_manifest.json")

        assert_crawl_manifest_privacy(manifest)
        self.assertEqual(validate_crawl_manifest_privacy(manifest), [])

    def test_rejects_private_and_raw_manifest_artifacts(self) -> None:
        manifest = _load_fixture("unsafe_private_artifacts_manifest.json")

        findings = validate_crawl_manifest_privacy(manifest)
        reasons = {finding.reason for finding in findings}

        self.assertIn("private DevHub session path is not allowed", reasons)
        self.assertIn("raw crawl output path is not allowed", reasons)
        self.assertIn("raw response body field is not allowed in crawl manifests", reasons)
        self.assertIn("credential field is not allowed in crawl manifests", reasons)
        self.assertIn("browser trace path is not allowed", reasons)
        self.assertIn("screenshot path is not allowed", reasons)
        self.assertIn("downloaded document path is not allowed", reasons)
        self.assertIn("downloaded document file path is not allowed", reasons)

        with self.assertRaisesRegex(ValueError, "crawl session manifest failed privacy validation"):
            assert_crawl_manifest_privacy(manifest)

    def test_all_findings_include_manifest_paths(self) -> None:
        manifest = _load_fixture("unsafe_private_artifacts_manifest.json")

        findings = validate_crawl_manifest_privacy(manifest)

        self.assertTrue(findings)
        for finding in findings:
            self.assertTrue(finding.path.startswith("$"))
            self.assertTrue(finding.reason)
            self.assertTrue(finding.value_preview)


def _load_fixture(name: str) -> object:
    with (FIXTURE_DIR / name).open("r", encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


if __name__ == "__main__":
    unittest.main()
