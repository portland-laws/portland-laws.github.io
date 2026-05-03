from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ppd.crawler.live_public_scrape import (
    LivePublicScrapePolicy,
    run_live_public_scrape,
)
from ppd.crawler.public_dry_run import FetchResponse


class LivePublicScrapeTest(unittest.TestCase):
    def test_live_scrape_refuses_without_explicit_live_flag(self) -> None:
        result = run_live_public_scrape(policy=LivePublicScrapePolicy())

        self.assertFalse(result.allowed)
        self.assertEqual("refused_by_policy", result.status)
        self.assertIn("allow_live_network=True", result.errors[0])

    def test_live_scrape_uses_public_dry_run_without_raw_persistence(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            manifest = Path(tempdir) / "seeds.json"
            manifest.write_text(
                '{"seeds":[{"id":"ppd-home","url":"https://www.portland.gov/ppd"}]}',
                encoding="utf-8",
            )
            calls: list[str] = []

            def fetch(url: str) -> FetchResponse:
                calls.append(url)
                if url.endswith("/robots.txt"):
                    return FetchResponse(
                        url=url,
                        status_code=200,
                        content_type="text/plain",
                        body=b"User-agent: *\nAllow: /ppd\n",
                    )
                return FetchResponse(
                    url=url,
                    status_code=200,
                    content_type="text/html",
                    body=b"<html><head><title>PPD Live Fixture</title></head><body>Public</body></html>",
                )

            result = run_live_public_scrape(
                seed_manifest_path=manifest,
                policy=LivePublicScrapePolicy(allow_live_network=True, max_seed_fetches=1),
                fetcher=fetch,
            )

        self.assertTrue(result.allowed)
        self.assertEqual("completed", result.status)
        self.assertFalse(result.raw_outputs_persisted)
        self.assertFalse(result.downloaded_documents_persisted)
        self.assertIsNotNone(result.report)
        assert result.report is not None
        self.assertEqual(1, result.report.fetched_seed_count)
        self.assertEqual("PPD Live Fixture", result.report.items[0].title)
        self.assertEqual(["https://www.portland.gov/robots.txt", "https://www.portland.gov/ppd"], calls)


if __name__ == "__main__":
    unittest.main()
