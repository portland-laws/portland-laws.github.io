import json
import tempfile
import unittest
from pathlib import Path

from ppd.crawler.public_dry_run import FetchResponse, run_public_crawl_dry_run


class PublicCrawlDryRunTests(unittest.TestCase):
    def write_manifest(self, directory: Path, urls: list[str]) -> Path:
        seeds = [{"id": f"seed-{index}", "url": url} for index, url in enumerate(urls, start=1)]
        path = directory / "seeds.json"
        path.write_text(json.dumps({"seeds": seeds}), encoding="utf-8")
        return path

    def fetcher_for(self, calls: list[str]):
        def fetch(url: str) -> FetchResponse:
            calls.append(url)
            if url.endswith("/robots.txt"):
                return FetchResponse(
                    url=url,
                    status_code=200,
                    content_type="text/plain",
                    body=b"User-agent: *\nAllow: /ppd\n",
                )
            body = b"<html><head><title>PPD Fixture</title></head><body>Public page</body></html>"
            return FetchResponse(url=url, status_code=200, content_type="text/html; charset=utf-8", body=body)

        return fetch

    def test_fetches_only_tiny_seed_set_after_robots_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            calls: list[str] = []
            manifest = self.write_manifest(
                Path(temp),
                [
                    "https://www.portland.gov/ppd",
                    "https://www.portland.gov/ppd/permits",
                    "https://www.portland.gov/ppd/residential-permits",
                ],
            )
            report = run_public_crawl_dry_run(
                seed_manifest_path=manifest,
                max_seed_fetches=3,
                fetcher=self.fetcher_for(calls),
            )
            self.assertEqual(report.max_seed_fetches, 2)
            self.assertEqual(report.attempted_seed_count, 2)
            self.assertEqual(report.fetched_seed_count, 2)
            self.assertEqual(report.items[0].title, "PPD Fixture")
            self.assertEqual(calls[0], "https://www.portland.gov/robots.txt")
            self.assertEqual(calls[1:], ["https://www.portland.gov/ppd", "https://www.portland.gov/ppd/permits"])

    def test_robots_disallow_prevents_seed_fetch(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            calls: list[str] = []
            manifest = self.write_manifest(Path(temp), ["https://www.portland.gov/ppd"])

            def fetch(url: str) -> FetchResponse:
                calls.append(url)
                if url.endswith("/robots.txt"):
                    return FetchResponse(
                        url=url,
                        status_code=200,
                        content_type="text/plain",
                        body=b"User-agent: *\nDisallow: /ppd\n",
                    )
                raise AssertionError("seed URL must not be fetched when robots disallow it")

            report = run_public_crawl_dry_run(seed_manifest_path=manifest, fetcher=fetch)
            self.assertEqual(report.fetched_seed_count, 0)
            self.assertEqual(report.skipped_seed_count, 1)
            self.assertEqual(report.items[0].reason_code, "robots_disallowed")
            self.assertEqual(calls, ["https://www.portland.gov/robots.txt"])

    def test_policy_disallow_prevents_robots_and_seed_fetch(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            calls: list[str] = []
            manifest = self.write_manifest(Path(temp), ["https://devhub.portlandoregon.gov/my-permits/payment"])
            report = run_public_crawl_dry_run(seed_manifest_path=manifest, fetcher=self.fetcher_for(calls))
            self.assertEqual(report.fetched_seed_count, 0)
            self.assertEqual(report.items[0].reason_code, "private_or_authenticated")
            self.assertEqual(calls, [])

    def test_inline_robots_fixture_avoids_robots_fetch(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            calls: list[str] = []
            manifest = self.write_manifest(Path(temp), ["https://www.portland.gov/ppd"])
            report = run_public_crawl_dry_run(
                seed_manifest_path=manifest,
                fetcher=self.fetcher_for(calls),
                robots_text_by_host={"www.portland.gov": "User-agent: *\nAllow: /ppd\n"},
            )
            self.assertEqual(report.fetched_seed_count, 1)
            self.assertEqual(calls, ["https://www.portland.gov/ppd"])


if __name__ == "__main__":
    unittest.main()
