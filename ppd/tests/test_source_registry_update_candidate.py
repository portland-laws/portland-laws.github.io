from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

from ppd.source_registry_update_candidate import (
    build_candidate_packet,
    load_json_packet,
    validate_candidate_packet,
)


FIXTURES = Path(__file__).parent / "fixtures" / "source_registry_update_candidate"


class SourceRegistryUpdateCandidateTests(unittest.TestCase):
    def _candidate(self) -> dict:
        return build_candidate_packet(
            load_json_packet(FIXTURES / "public_source_registry_coverage_gap_packet.json"),
            load_json_packet(FIXTURES / "public_recrawl_post_intake_review_packet.json"),
        )

    def test_builds_metadata_only_candidate_from_public_packets(self) -> None:
        coverage_gap_packet = load_json_packet(FIXTURES / "public_source_registry_coverage_gap_packet.json")
        recrawl_review_packet = load_json_packet(FIXTURES / "public_recrawl_post_intake_review_packet.json")

        candidate = build_candidate_packet(coverage_gap_packet, recrawl_review_packet)

        self.assertEqual(candidate["packet_type"], "source_registry_update_candidate")
        self.assertTrue(candidate["fixture_first"])
        self.assertTrue(candidate["metadata_only"])
        self.assertFalse(candidate["promotes_registry_changes"])
        self.assertFalse(candidate["performs_source_fetch"])
        self.assertEqual(
            candidate["source_packet_ids"],
            [
                "public-source-registry-coverage-gap-fixture-20260529",
                "public-recrawl-post-intake-review-fixture-20260529",
            ],
        )
        validate_candidate_packet(candidate)

    def test_emits_expected_review_sections(self) -> None:
        candidate = self._candidate()

        diffs_by_source = {item["source_id"]: item for item in candidate["proposed_registry_row_diffs"]}
        self.assertEqual(diffs_by_source["ppd-devhub-faqs"]["operation"], "add_metadata_only_row")
        self.assertEqual(diffs_by_source["ppd-devhub-faqs"]["after"]["source_type"], "devhub_public")
        self.assertEqual(
            diffs_by_source["ppd-submit-plans-online"]["operation"],
            "update_metadata_only_row",
        )
        self.assertEqual(
            diffs_by_source["ppd-devhub-faqs"]["citation_ids"],
            candidate["source_packet_ids"],
        )

        skip_updates = {item["source_id"]: item for item in candidate["skip_reason_updates"]}
        self.assertEqual(skip_updates["ppd-outside-social-link"]["proposed_skip_reason"], "outside ppd source scope")

        freshness = {item["source_id"]: item for item in candidate["freshness_status_candidates"]}
        self.assertEqual(freshness["ppd-devhub-faqs"]["proposed_freshness_status"], "recrawl_candidate")
        self.assertEqual(
            freshness["ppd-submit-plans-online"]["proposed_freshness_status"],
            "stale_review_required",
        )

        rollback_sources = {item["source_id"] for item in candidate["rollback_notes"]}
        self.assertIn("ppd-devhub-faqs", rollback_sources)
        self.assertIn("ppd-submit-plans-online", rollback_sources)
        self.assertIn("ppd-outside-social-link", rollback_sources)

        owner_by_source = {item["source_id"]: item["reviewer_owner"] for item in candidate["reviewer_owners"]}
        self.assertEqual(owner_by_source["ppd-devhub-faqs"], "devhub-guidance-reviewer")
        self.assertEqual(owner_by_source["ppd-submit-plans-online"], "single-pdf-guidance-reviewer")

    def test_rejects_active_mutation_candidate_shape(self) -> None:
        candidate = self._candidate()
        candidate["promotes_registry_changes"] = True

        with self.assertRaises(ValueError):
            validate_candidate_packet(candidate)

    def test_rejects_uncited_registry_row_diff(self) -> None:
        candidate = self._candidate()
        candidate["proposed_registry_row_diffs"][0].pop("citation_ids")
        candidate["proposed_registry_row_diffs"][0].pop("source_packet_ids")

        with self.assertRaises(ValueError):
            validate_candidate_packet(candidate)

    def test_rejects_non_allowlisted_url(self) -> None:
        candidate = self._candidate()
        candidate["proposed_registry_row_diffs"][0]["canonical_url"] = "https://example.com/ppd"

        with self.assertRaises(ValueError):
            validate_candidate_packet(candidate)

    def test_rejects_private_devhub_target(self) -> None:
        candidate = self._candidate()
        candidate["proposed_registry_row_diffs"][0]["canonical_url"] = "https://devhub.portlandoregon.gov/secure/my-permits"

        with self.assertRaises(ValueError):
            validate_candidate_packet(candidate)

    def test_rejects_raw_crawl_download_or_archive_references(self) -> None:
        candidate = self._candidate()
        candidate["proposed_registry_row_diffs"][0]["raw_warc_path"] = "raw-archives/ppd.warc.gz"

        with self.assertRaises(ValueError):
            validate_candidate_packet(candidate)

    def test_rejects_live_fetch_claims(self) -> None:
        candidate = self._candidate()
        candidate["live_fetch"] = True

        with self.assertRaises(ValueError):
            validate_candidate_packet(candidate)

    def test_rejects_missing_rollback_notes(self) -> None:
        candidate = self._candidate()
        removed_source_id = candidate["proposed_registry_row_diffs"][0]["source_id"]
        candidate["rollback_notes"] = [
            item for item in candidate["rollback_notes"] if item["source_id"] != removed_source_id
        ]

        with self.assertRaises(ValueError):
            validate_candidate_packet(candidate)

    def test_rejects_missing_reviewer_owner(self) -> None:
        candidate = self._candidate()
        removed_source_id = candidate["proposed_registry_row_diffs"][0]["source_id"]
        candidate["reviewer_owners"] = [
            item for item in candidate["reviewer_owners"] if item["source_id"] != removed_source_id
        ]

        with self.assertRaises(ValueError):
            validate_candidate_packet(candidate)

    def test_rejects_nested_active_registry_mutation_flags(self) -> None:
        candidate = self._candidate()
        mutated = deepcopy(candidate)
        mutated["proposed_registry_row_diffs"][0]["after"]["active_registry_mutation_enabled"] = True

        with self.assertRaises(ValueError):
            validate_candidate_packet(mutated)


if __name__ == "__main__":
    unittest.main()
