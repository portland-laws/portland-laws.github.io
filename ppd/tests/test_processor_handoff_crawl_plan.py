"""Fixture-only validation for PP&D crawl-plan processor handoff metadata.

This test intentionally validates only committed fixture metadata. It must not
perform network access, import ipfs_datasets_py processor modules, or invoke any
processor code.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from urllib.parse import urlparse


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "crawler" / "processor_handoff_crawl_plan.json"
EXPECTED_BACKEND_ROOT = "ipfs_datasets_py/ipfs_datasets_py/processors"
ALLOWED_HOSTS = {
    "www.portland.gov",
    "devhub.portlandoregon.gov",
    "www.portlandoregon.gov",
    "www.portlandmaps.com",
}
ALLOWED_METADATA_KINDS = {"backend_directory", "python_module"}
ALLOWED_HANDOFF_MODE = "manifest_only"


class ProcessorHandoffCrawlPlanTest(unittest.TestCase):
    def test_each_planned_public_fetch_maps_to_existing_backend_metadata(self) -> None:
        plan = self._load_fixture()
        repo_root = Path(__file__).resolve().parents[2]

        self.assertEqual(plan.get("schemaVersion"), 1)
        self.assertTrue(plan.get("fixtureOnly"))
        self.assertFalse(plan.get("networkAccess"))
        self.assertFalse(plan.get("processorInvocation"))
        self.assertEqual(plan.get("backendRoot"), EXPECTED_BACKEND_ROOT)

        planned_fetches = plan.get("plannedPublicFetches")
        self.assertIsInstance(planned_fetches, list)
        self.assertGreater(len(planned_fetches), 0)

        seen_ids: set[str] = set()
        for planned_fetch in planned_fetches:
            fetch_id = planned_fetch.get("id")
            self.assertIsInstance(fetch_id, str)
            self.assertNotEqual(fetch_id.strip(), "")
            self.assertNotIn(fetch_id, seen_ids)
            seen_ids.add(fetch_id)

            self._assert_public_fetch_policy(planned_fetch)
            self._assert_processor_handoff(planned_fetch, repo_root)

    def _load_fixture(self) -> dict[str, object]:
        with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
            loaded = json.load(fixture_file)
        self.assertIsInstance(loaded, dict)
        return loaded

    def _assert_public_fetch_policy(self, planned_fetch: dict[str, object]) -> None:
        self.assertEqual(planned_fetch.get("decision"), "fetch")

        source_url = planned_fetch.get("sourceUrl")
        canonical_url = planned_fetch.get("canonicalUrl")
        self.assertIsInstance(source_url, str)
        self.assertIsInstance(canonical_url, str)
        self.assertEqual(source_url, canonical_url)

        parsed = urlparse(source_url)
        self.assertEqual(parsed.scheme, "https")
        self.assertIn(parsed.netloc, ALLOWED_HOSTS)

        preflight = planned_fetch.get("policyPreflight")
        self.assertIsInstance(preflight, dict)
        self.assertIs(preflight.get("allowlisted"), True)
        self.assertIs(preflight.get("robotsAllowed"), True)
        self.assertIs(preflight.get("noPersist"), True)
        self.assertIsInstance(preflight.get("timeoutSeconds"), int)
        self.assertGreater(preflight.get("timeoutSeconds"), 0)

    def _assert_processor_handoff(self, planned_fetch: dict[str, object], repo_root: Path) -> None:
        handoff = planned_fetch.get("processorHandoff")
        self.assertIsInstance(handoff, dict)
        self.assertEqual(handoff.get("handoffMode"), ALLOWED_HANDOFF_MODE)
        self.assertIn(handoff.get("metadataKind"), ALLOWED_METADATA_KINDS)

        backend_path = handoff.get("backendPath")
        processor_name = handoff.get("processorName")
        processor_family = handoff.get("processorFamily")
        self.assertIsInstance(backend_path, str)
        self.assertIsInstance(processor_name, str)
        self.assertIsInstance(processor_family, str)
        self.assertTrue(backend_path.startswith(EXPECTED_BACKEND_ROOT + "/"))
        self.assertNotIn("..", Path(backend_path).parts)
        self.assertNotEqual(processor_name.strip(), "")
        self.assertNotEqual(processor_family.strip(), "")

        backend_metadata_path = repo_root / backend_path
        self.assertTrue(
            backend_metadata_path.exists(),
            f"planned fetch {planned_fetch.get('id')} maps to missing backend metadata {backend_path}",
        )

        if handoff.get("metadataKind") == "python_module":
            self.assertTrue(backend_metadata_path.is_file())
            self.assertEqual(backend_metadata_path.suffix, ".py")
        else:
            self.assertTrue(backend_metadata_path.is_dir())


if __name__ == "__main__":
    unittest.main()
