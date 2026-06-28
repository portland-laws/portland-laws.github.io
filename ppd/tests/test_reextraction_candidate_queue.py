from copy import deepcopy
from pathlib import Path
import unittest

from ppd.extraction.reextraction_candidate_queue import (
    OFFLINE_VALIDATION_COMMANDS,
    ReextractionCandidateQueueV1Error,
    build_reextraction_candidate_queue,
    load_json_fixture,
    queue_from_fixture_paths,
    validate_reextraction_candidate_queue_v1,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "reextraction_candidate_queue_v1"
REVIEWER_ROWS = FIXTURE_DIR / "synthetic_stale_readiness_reviewer_dispositions.json"
MONITORING_PLACEHOLDERS = FIXTURE_DIR / "public_monitoring_placeholders.json"


class ReextractionCandidateQueueTest(unittest.TestCase):
    def test_fixture_queue_lists_only_source_backed_queueable_candidates(self) -> None:
        queue = queue_from_fixture_paths(REVIEWER_ROWS, MONITORING_PLACEHOLDERS)

        self.assertEqual(queue["queue_version"], "reextraction_candidate_queue_v1")
        self.assertEqual(
            queue["candidate_requirement_ids"],
            [
                "REQ-DEVHUB-PUBLIC-ACCOUNT-001",
                "REQ-FEE-PAYMENT-003",
                "REQ-SINGLE-PDF-002",
            ],
        )
        self.assertEqual(len(queue["candidates"]), 3)
        self.assertEqual(
            {row["skip_reason"] for row in queue["skipped_rows"]},
            {"requirement_is_not_source_backed", "reviewer_disposition_not_queueable"},
        )

    def test_queue_is_side_effect_free_and_offline_only(self) -> None:
        queue = queue_from_fixture_paths(REVIEWER_ROWS, MONITORING_PLACEHOLDERS)

        self.assertEqual(
            queue["side_effects"],
            {
                "live_extraction_performed": False,
                "crawler_or_download_performed": False,
                "devhub_opened": False,
                "active_requirements_mutated": False,
                "private_files_written": False,
            },
        )
        self.assertEqual(queue["offline_validation_commands"], OFFLINE_VALIDATION_COMMANDS)
        for command in queue["offline_validation_commands"]:
            self.assertIsInstance(command, list)
            self.assertTrue(command)
            self.assertNotIn("playwright", command)
            self.assertNotIn("crawl", " ".join(command).lower())

    def test_candidates_include_review_routing_citations_confidence_and_blockers(self) -> None:
        queue = queue_from_fixture_paths(REVIEWER_ROWS, MONITORING_PLACEHOLDERS)
        candidates = {candidate["requirement_id"]: candidate for candidate in queue["candidates"]}

        signin = candidates["REQ-DEVHUB-PUBLIC-ACCOUNT-001"]
        self.assertIn(
            "refresh account sign-in citation span before updating requirement text",
            signin["citation_placeholder_needs"],
        )
        self.assertIn(
            "public sign-in guide placeholder needs a fresh cited span",
            signin["citation_placeholder_needs"],
        )
        self.assertIn(
            "prior extraction confidence was medium because DevHub wording was summarized",
            signin["extraction_confidence_notes"],
        )
        self.assertEqual(
            signin["human_review_routing"]["review_queue"],
            "public_guidance_requirement_review",
        )
        self.assertTrue(
            signin["human_review_routing"]["requires_human_before_requirement_mutation"]
        )
        self.assertIn(
            "public monitoring placeholder reports stale freshness",
            signin["blocked_stale_source_dependencies"],
        )

        single_pdf = candidates["REQ-SINGLE-PDF-002"]
        self.assertIn(
            "citation span must be refreshed from public placeholder before any extraction update",
            single_pdf["citation_placeholder_needs"],
        )
        self.assertIn(
            "public monitoring placeholder reports unknown freshness",
            single_pdf["blocked_stale_source_dependencies"],
        )

        fee = candidates["REQ-FEE-PAYMENT-003"]
        self.assertIn(
            "fee payment public placeholder has no current verified hash in fixture",
            fee["blocked_stale_source_dependencies"],
        )
        self.assertIn(
            "source freshness must be resolved for SRC-FEE-PAYMENT-GUIDE",
            fee["blocked_stale_source_dependencies"],
        )
        self.assertEqual(
            fee["human_review_routing"]["review_queue"],
            "financial_action_gate_review",
        )

    def test_builder_rejects_non_synthetic_rows_and_missing_placeholders(self) -> None:
        reviewer_rows = load_json_fixture(REVIEWER_ROWS)
        monitoring_placeholders = load_json_fixture(MONITORING_PLACEHOLDERS)
        reviewer_rows.append(
            {
                "row_kind": "live_reviewer_disposition",
                "requirement_id": "REQ-LIVE-ROW-006",
                "source_id": "SRC-DEVHUB-FAQ",
                "source_evidence_ids": ["EVID-LIVE"],
                "reviewer_disposition": "stale_requires_reextraction",
            }
        )
        reviewer_rows.append(
            {
                "row_kind": "synthetic_stale_readiness_reviewer_disposition",
                "requirement_id": "REQ-MISSING-PLACEHOLDER-007",
                "source_id": "SRC-NOT-IN-MONITORING-PLACEHOLDERS",
                "source_evidence_ids": ["EVID-MISSING-PLACEHOLDER"],
                "reviewer_disposition": "stale_requires_reextraction",
                "citation_placeholder_needs": ["refresh cited public span"],
                "extraction_confidence_notes": ["prior extraction confidence requires review"],
                "blocked_stale_source_dependencies": ["source freshness unresolved"],
                "human_review_routing": {
                    "review_queue": "public_guidance_requirement_review",
                    "reason": "missing placeholder cannot proceed",
                    "requires_human_before_requirement_mutation": True,
                },
            }
        )

        queue = build_reextraction_candidate_queue(reviewer_rows, monitoring_placeholders)

        skipped = {row["requirement_id"]: row["skip_reason"] for row in queue["skipped_rows"]}
        self.assertEqual(
            skipped["REQ-LIVE-ROW-006"],
            "not_a_synthetic_stale_readiness_reviewer_row",
        )
        self.assertEqual(
            skipped["REQ-MISSING-PLACEHOLDER-007"],
            "missing_public_monitoring_placeholder",
        )

    def test_builder_rejects_missing_candidate_completeness_fields(self) -> None:
        base_row = load_json_fixture(REVIEWER_ROWS)[0]
        monitoring_placeholders = load_json_fixture(MONITORING_PLACEHOLDERS)
        field_expectations = {
            "reviewer_disposition": "missing_reviewer_disposition",
            "requirement_id": "missing_requirement_id",
            "citation_placeholder_needs": "missing_citation_placeholder_needs",
            "extraction_confidence_notes": "missing_extraction_confidence_notes",
            "blocked_stale_source_dependencies": "missing_blocked_stale_source_dependencies",
            "human_review_routing": "missing_human_review_routing",
        }

        for field, expected_reason in field_expectations.items():
            row = deepcopy(base_row)
            row.pop(field, None)
            queue = build_reextraction_candidate_queue([row], monitoring_placeholders)
            self.assertEqual(queue["candidates"], [])
            self.assertEqual(queue["skipped_rows"][0]["skip_reason"], expected_reason)

    def test_builder_rejects_private_live_guarantee_release_and_mutation_claims(self) -> None:
        base_row = load_json_fixture(REVIEWER_ROWS)[0]
        monitoring_placeholders = load_json_fixture(MONITORING_PLACEHOLDERS)
        unsafe_rows = []
        for requirement_id, unsafe_patch in (
            ("REQ-RAW-ARTIFACT", {"raw_artifact_ref": "raw crawl body"}),
            ("REQ-LIVE-CLAIM", {"stale_reason": "live crawl completed for this source"}),
            ("REQ-LEGAL-GUARANTEE", {"stale_reason": "permit approval guaranteed after update"}),
            ("REQ-RELEASE-PROMOTION", {"stale_reason": "release promoted to current corpus"}),
            ("REQ-ACTIVE-MUTATION", {"active_requirements_mutated": True}),
        ):
            row = deepcopy(base_row)
            row["requirement_id"] = requirement_id
            row.update(unsafe_patch)
            unsafe_rows.append(row)

        queue = build_reextraction_candidate_queue(unsafe_rows, monitoring_placeholders)

        self.assertEqual(queue["candidates"], [])
        self.assertEqual(
            {row["skip_reason"] for row in queue["skipped_rows"]},
            {"unsafe_private_live_mutating_or_overclaiming_row"},
        )

    def test_queue_validator_rejects_missing_validation_commands_and_candidate_ids(self) -> None:
        queue = queue_from_fixture_paths(REVIEWER_ROWS, MONITORING_PLACEHOLDERS)
        queue_without_commands = deepcopy(queue)
        queue_without_commands.pop("offline_validation_commands")
        with self.assertRaisesRegex(ReextractionCandidateQueueV1Error, "missing_validation_commands"):
            validate_reextraction_candidate_queue_v1(queue_without_commands)

        queue_without_ids = deepcopy(queue)
        queue_without_ids.pop("candidate_requirement_ids")
        with self.assertRaisesRegex(ReextractionCandidateQueueV1Error, "missing_candidate_requirement_ids"):
            validate_reextraction_candidate_queue_v1(queue_without_ids)

    def test_queue_validator_rejects_missing_public_monitoring_reference_and_active_flags(self) -> None:
        queue = queue_from_fixture_paths(REVIEWER_ROWS, MONITORING_PLACEHOLDERS)
        broken_queue = deepcopy(queue)
        broken_queue["candidates"][0].pop("monitoring_placeholder")
        broken_queue["side_effects"]["active_requirements_mutated"] = True

        with self.assertRaisesRegex(ReextractionCandidateQueueV1Error, "missing_public_monitoring_placeholder_reference"):
            validate_reextraction_candidate_queue_v1(broken_queue)


if __name__ == "__main__":
    unittest.main()
