from __future__ import annotations

import unittest
from pathlib import Path

from ppd.crawler.source_registry_schedule_update_candidate_packet import (
    assert_valid_source_registry_schedule_update_candidate_packet,
    validate_source_registry_schedule_update_candidate_packet_file,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "source_registry_schedule_update_candidate_packet"


class SourceRegistryScheduleUpdateCandidatePacketTest(unittest.TestCase):
    def test_accepts_metadata_only_cited_candidate_packet(self) -> None:
        errors = validate_source_registry_schedule_update_candidate_packet_file(FIXTURE_DIR / "valid.json")
        self.assertEqual([], errors)

    def test_rejects_unsafe_candidate_packet_claims(self) -> None:
        errors = validate_source_registry_schedule_update_candidate_packet_file(FIXTURE_DIR / "invalid.json")
        joined = "\n".join(errors)
        expected_markers = (
            "affected_source_ids_missing",
            "reviewer_owners_missing",
            "abort_criteria_missing",
            "uncited_source_adjustment",
            "outside_allowlist",
            "private_or_authenticated_url",
            "private_or_authenticated_source_type",
            "private_or_authenticated_privacy_classification",
            "raw_body_download_or_archive_reference",
            "live_crawl_or_processor_execution_claim",
            "legal_or_permitting_outcome_guarantee",
            "active_registry_or_schedule_mutation_flag",
        )
        for marker in expected_markers:
            self.assertIn(marker, joined)

    def test_assertion_helper_raises_value_error_with_errors(self) -> None:
        with self.assertRaisesRegex(ValueError, "failed validation"):
            assert_valid_source_registry_schedule_update_candidate_packet(
                {
                    "reviewer_owners": {},
                    "abort_criteria": [],
                    "source_adjustments": [],
                }
            )


if __name__ == "__main__":
    unittest.main()
