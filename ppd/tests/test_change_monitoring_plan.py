"""Validate the fixture-only PP&D change-monitoring plan."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from urllib.parse import urldefrag, urlparse


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "change_monitoring" / "change_monitoring_plan.json"
ALLOWED_RECRAWL_CADENCES = {"daily", "weekly", "monthly"}
REQUIRED_SKIPPED_ACTIONS = {
    "live_public_crawl": "fixture_only_no_network_access",
    "private_devhub_data_access": "private_devhub_data_not_authorized",
}


class ChangeMonitoringPlanFixtureTest(unittest.TestCase):
    def setUp(self) -> None:
        with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
            self.plan = json.load(fixture_file)

    def test_each_watched_source_has_canonical_url_provenance(self) -> None:
        watched_sources = self.plan.get("watchedSources", [])
        self.assertGreater(len(watched_sources), 0)

        seen_ids: set[str] = set()
        for source in watched_sources:
            source_id = source.get("id")
            self.assertIsInstance(source_id, str)
            self.assertNotIn(source_id, seen_ids)
            seen_ids.add(source_id)

            source_url = source.get("sourceUrl")
            canonical_url = source.get("canonicalUrl")
            self.assert_https_url(source_url, source_id, "sourceUrl")
            self.assert_https_url(canonical_url, source_id, "canonicalUrl")
            self.assertEqual(canonical_url, urldefrag(canonical_url)[0], source_id)
            self.assertNotIn("?", canonical_url, source_id)

            provenance = source.get("provenance")
            self.assertIsInstance(provenance, dict, source_id)
            self.assertEqual(canonical_url, source.get("canonicalUrl"), source_id)
            self.assert_non_empty_string(provenance.get("sourceEvidenceId"), source_id, "sourceEvidenceId")
            self.assert_non_empty_string(provenance.get("canonicalUrlBasis"), source_id, "canonicalUrlBasis")
            self.assert_utc_timestamp(provenance.get("verifiedAt"), source_id, "verifiedAt")

    def test_each_watched_source_has_hash_or_http_cache_placeholder(self) -> None:
        for source in self.plan.get("watchedSources", []):
            source_id = source.get("id")
            freshness = source.get("freshness")
            self.assertIsInstance(freshness, dict, source_id)

            content_hash = freshness.get("contentHashPlaceholder")
            cache_metadata = freshness.get("httpCacheMetadataPlaceholder")
            self.assertIsInstance(cache_metadata, dict, source_id)

            has_content_hash = isinstance(content_hash, str) and content_hash.startswith("sha256:")
            has_http_cache_placeholder = any(
                cache_metadata.get(field) is not None
                for field in ("etag", "lastModified", "cacheControl")
            )
            self.assertTrue(
                has_content_hash or has_http_cache_placeholder,
                f"{source_id} must include a content-hash or HTTP-cache metadata placeholder",
            )

    def test_each_watched_source_has_recrawl_cadence(self) -> None:
        for source in self.plan.get("watchedSources", []):
            source_id = source.get("id")
            cadence = source.get("recrawlCadence")
            self.assertIsInstance(cadence, dict, source_id)
            self.assertIn(cadence.get("frequency"), ALLOWED_RECRAWL_CADENCES, source_id)
            self.assert_non_empty_string(cadence.get("reason"), source_id, "recrawlCadence.reason")

    def test_each_watched_source_records_skipped_live_and_private_actions(self) -> None:
        for source in self.plan.get("watchedSources", []):
            source_id = source.get("id")
            skipped_actions = source.get("skippedActions")
            self.assertIsInstance(skipped_actions, list, source_id)
            observed = {
                item.get("action"): item.get("reasonCode")
                for item in skipped_actions
                if isinstance(item, dict)
            }
            self.assertEqual(REQUIRED_SKIPPED_ACTIONS, observed, source_id)

            for skipped_action in skipped_actions:
                self.assert_non_empty_string(skipped_action.get("reason"), source_id, "skipped action reason")

    def assert_https_url(self, value: object, source_id: object, field_name: str) -> None:
        self.assertIsInstance(value, str, f"{source_id} {field_name}")
        parsed = urlparse(value)
        self.assertEqual("https", parsed.scheme, f"{source_id} {field_name}")
        self.assertTrue(parsed.netloc, f"{source_id} {field_name}")

    def assert_non_empty_string(self, value: object, source_id: object, field_name: str) -> None:
        self.assertIsInstance(value, str, f"{source_id} {field_name}")
        self.assertTrue(value.strip(), f"{source_id} {field_name}")

    def assert_utc_timestamp(self, value: object, source_id: object, field_name: str) -> None:
        self.assert_non_empty_string(value, source_id, field_name)
        self.assertTrue(str(value).endswith("Z"), f"{source_id} {field_name}")


if __name__ == "__main__":
    unittest.main()
