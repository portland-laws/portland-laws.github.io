"""Tests for live public crawl preflight reports."""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from ppd.crawler.live_public_preflight import (
    MAX_TIMEOUT_SECONDS,
    TINY_SEED_FETCH_LIMIT,
    bounded_timeout_seconds,
    build_live_public_preflight_report,
    main,
)


class LivePublicPreflightTests(unittest.TestCase):
    def write_manifest(self, directory: Path, urls: list[str]) -> Path:
        path = directory / "seeds.json"
        path.write_text(
            json.dumps({"seeds": [{"id": f"seed-{index}", "url": url} for index, url in enumerate(urls, start=1)]}),
            encoding="utf-8",
        )
        return path

    def test_reports_only_tiny_allowlisted_robot_allowed_seed_urls(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            manifest = self.write_manifest(
                Path(temp),
                [
                    "https://www.portland.gov/ppd",
                    "https://www.portland.gov/ppd/permits",
                    "https://www.portland.gov/ppd/residential-permits",
                ],
            )
            report = build_live_public_preflight_report(
                seed_manifest_path=manifest,
                robots_text_by_host={"www.portland.gov": "User-agent: *\nAllow: /ppd\n"},
                seed_limit=99,
                timeout_seconds=7,
            )
            self.assertEqual(report.seed_limit, TINY_SEED_FETCH_LIMIT)
            self.assertEqual(report.timeout_seconds, 7)
            self.assertEqual(report.eligible_count, 2)
            self.assertTrue(all(item.no_persist for item in report.items))
            self.assertEqual([item.reason_code for item in report.items], ["allowed", "allowed"])

    def test_missing_robots_text_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            manifest = self.write_manifest(Path(temp), ["https://www.portland.gov/ppd"])
            report = build_live_public_preflight_report(seed_manifest_path=manifest)
            self.assertEqual(report.eligible_count, 0)
            self.assertEqual(report.items[0].reason_code, "robots_required")

    def test_private_or_persisting_seed_is_not_eligible(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            manifest = self.write_manifest(Path(temp), ["https://devhub.portlandoregon.gov/my-permits/payment"])
            private_report = build_live_public_preflight_report(
                seed_manifest_path=manifest,
                robots_text_by_host={"devhub.portlandoregon.gov": "User-agent: *\nAllow: /\n"},
            )
            self.assertFalse(private_report.items[0].eligible)
            self.assertEqual(private_report.items[0].reason_code, "private_or_authenticated")

            persist_report = build_live_public_preflight_report(
                seed_manifest_path=manifest,
                robots_text_by_host={"devhub.portlandoregon.gov": "User-agent: *\nAllow: /\n"},
                no_persist=False,
            )
            self.assertFalse(persist_report.items[0].eligible)
            self.assertEqual(persist_report.items[0].reason_code, "persist_not_allowed")

    def test_timeout_is_bounded_and_command_prints_json(self) -> None:
        self.assertEqual(bounded_timeout_seconds(999), MAX_TIMEOUT_SECONDS)
        with tempfile.TemporaryDirectory() as temp:
            manifest = self.write_manifest(Path(temp), ["https://www.portland.gov/ppd"])
            output = io.StringIO()
            with redirect_stdout(output):
                code = main(
                    [
                        "--seed-manifest",
                        str(manifest),
                        "--robots-json",
                        json.dumps({"www.portland.gov": "User-agent: *\nAllow: /ppd\n"}),
                    ]
                )
            self.assertEqual(code, 0)
            parsed = json.loads(output.getvalue())
            self.assertEqual(parsed["mode"], "live_public_crawl_preflight")


if __name__ == "__main__":
    unittest.main()
