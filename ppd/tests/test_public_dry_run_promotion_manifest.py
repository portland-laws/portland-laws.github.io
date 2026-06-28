from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from ppd.crawler.public_dry_run_promotion_manifest import (
    REQUIRED_ABORT_CONDITIONS,
    assert_public_dry_run_promotion_manifest,
    validate_public_dry_run_promotion_manifest,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "public_dry_run_promotion_manifest" / "valid_manifest.json"


class PublicDryRunPromotionManifestTest(unittest.TestCase):
    def load_manifest(self) -> dict:
        return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def assert_rejects(self, manifest: dict, expected: str) -> None:
        errors = validate_public_dry_run_promotion_manifest(manifest)
        self.assertTrue(errors, "manifest should be rejected")
        self.assertIn(expected, "; ".join(errors))

    def test_valid_manifest_passes_and_stays_dry_run_only(self) -> None:
        summary = assert_public_dry_run_promotion_manifest(self.load_manifest())

        self.assertEqual(summary.manifest_id, "fixture-public-dry-run-promotion-2026-05-28")
        self.assertEqual(summary.target_count, 2)
        self.assertFalse(summary.ready_for_live_execution)

    def test_rejects_private_authenticated_or_non_allowlisted_urls(self) -> None:
        private_path = self.load_manifest()
        private_path["promotion_targets"][0]["canonical_url"] = "https://devhub.portlandoregon.gov/secure/applications/123"
        self.assert_rejects(private_path, "must not reference private or authenticated paths")

        credentialed = self.load_manifest()
        credentialed["promotion_targets"][0]["canonical_url"] = "https://user:pass@www.portland.gov/ppd"
        self.assert_rejects(credentialed, "must not include credentials")

        outside_host = self.load_manifest()
        outside_host["promotion_targets"][0]["canonical_url"] = "https://example.com/ppd"
        self.assert_rejects(outside_host, "host must be allowlisted")

        auth_query = self.load_manifest()
        auth_query["promotion_targets"][0]["canonical_url"] = "https://www.portland.gov/ppd?token=secret"
        self.assert_rejects(auth_query, "query must not contain authentication material")

    def test_rejects_raw_body_download_archive_paths_and_live_claims(self) -> None:
        manifest = self.load_manifest()
        manifest["promotion_targets"][0]["raw_body"] = "raw body"
        manifest["promotion_targets"][1]["download_path"] = "/tmp/downloaded.pdf"
        manifest["archive_path"] = "captures/raw.warc"
        manifest["live_network_invoked"] = True
        manifest["real_crawl_performed"] = True
        manifest["real_download_performed"] = True

        errors = "; ".join(validate_public_dry_run_promotion_manifest(manifest))
        self.assertIn("raw_body must not include raw bodies", errors)
        self.assertIn("download_path must not include raw bodies", errors)
        self.assertIn("archive_path must not include raw bodies", errors)
        self.assertIn("live_network_invoked must be false", errors)
        self.assertIn("real_crawl_performed must be false", errors)
        self.assertIn("real_download_performed must be false", errors)

    def test_rejects_missing_prerequisites_processor_handoff_and_abort_conditions(self) -> None:
        manifest = self.load_manifest()
        manifest["robots_policy_prerequisites"][0]["robots_status"] = "missing"
        manifest["robots_policy_prerequisites"][1].pop("policy_status")
        manifest["processor_handoff_intent"] = []
        manifest["abort_conditions"] = [
            item for item in manifest["abort_conditions"] if item["condition_id"] not in REQUIRED_ABORT_CONDITIONS
        ]

        errors = "; ".join(validate_public_dry_run_promotion_manifest(manifest))
        self.assertIn("robots_status must be explicitly allowed", errors)
        self.assertIn("policy_status must be explicitly approved", errors)
        self.assertIn("processor_handoff_intent must have one row per promotion target", errors)
        self.assertIn("abort_conditions missing private_or_authenticated_url", errors)

    def test_mutation_does_not_share_nested_fixture_state(self) -> None:
        first = self.load_manifest()
        second = copy.deepcopy(first)
        second["promotion_targets"][0]["canonical_url"] = "https://example.com/not-allowed"

        self.assertEqual(validate_public_dry_run_promotion_manifest(first), [])
        self.assert_rejects(second, "host must be allowlisted")


if __name__ == "__main__":
    unittest.main()
