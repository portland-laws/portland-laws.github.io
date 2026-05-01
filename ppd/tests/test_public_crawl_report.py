"""Tests for fixture-backed public crawl dry-run reports."""

from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from ppd.crawler.public_crawl_report import build_public_crawl_report, main

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "public_crawl_report" / "injected_responses.json"


class PublicCrawlReportTests(unittest.TestCase):
    def test_report_uses_injected_responses_and_excludes_raw_bodies(self) -> None:
        report = build_public_crawl_report(fixture_path=FIXTURE_PATH)
        self.assertEqual(report["mode"], "fixture_backed_public_crawl_report")
        self.assertEqual(report["fixture_id"], "public-crawl-report-injected-responses-v1")
        self.assertEqual(report["attempted_seed_count"], 2)
        self.assertEqual(report["fetched_seed_count"], 2)
        self.assertFalse(report["raw_output_persisted"])
        self.assertFalse(report["raw_response_bodies_included"])

        titles = [item["title"] for item in report["items"]]
        self.assertEqual(titles, ["Portland Permitting & Development", "Single PDF Process"])
        serialized = json.dumps(report, sort_keys=True).lower()
        self.assertNotIn("<html", serialized)
        self.assertNotIn("raw_body", serialized)
        self.assertNotIn("data/raw", serialized)

    def test_report_command_prints_json(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            code = main(["--fixture", str(FIXTURE_PATH)])
        self.assertEqual(code, 0)
        parsed = json.loads(output.getvalue())
        self.assertEqual(parsed["fetched_seed_count"], 2)


if __name__ == "__main__":
    unittest.main()
