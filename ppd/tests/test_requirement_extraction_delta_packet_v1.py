from __future__ import annotations

from pathlib import Path
import unittest

from ppd.requirement_extraction_delta_packet_v1 import (
    build_requirement_extraction_delta_packet_v1,
    load_changed_document_rows,
)


class RequirementExtractionDeltaPacketV1Test(unittest.TestCase):
    def fixture_path(self) -> Path:
        return Path(__file__).parent / "fixtures" / "requirement_extraction_delta_packet_v1" / "changed_documents.json"

    def test_builds_fixture_first_delta_packet(self) -> None:
        rows = load_changed_document_rows(self.fixture_path())
        packet = build_requirement_extraction_delta_packet_v1(rows)

        self.assertEqual(packet["packet_version"], "requirement_extraction_delta_packet_v1")
        self.assertEqual(packet["source_mode"], "synthetic_fixture_only")
        self.assertEqual(packet["changed_document_count"], 3)
        self.assertEqual(len(packet["requirement_candidates"]), 4)
        self.assertEqual(len(packet["source_evidence_refs"]), 3)
        self.assertEqual(len(packet["confidence_rows"]), 4)
        self.assertEqual(len(packet["human_review_rows"]), 4)
        self.assertEqual(len(packet["stale_evidence_impacts"]), 2)

    def test_packet_declares_no_live_or_mutating_side_effects(self) -> None:
        rows = load_changed_document_rows(self.fixture_path())
        packet = build_requirement_extraction_delta_packet_v1(rows)

        self.assertEqual(
            packet["side_effects"],
            {
                "live_sources_extracted": False,
                "ocr_ran": False,
                "documents_downloaded": False,
                "devhub_opened": False,
                "active_requirements_mutated": False,
            },
        )
        for impact in packet["stale_evidence_impacts"]:
            self.assertFalse(impact["mutates_active_requirements"])

    def test_candidates_are_review_only_and_confidence_is_bounded(self) -> None:
        rows = load_changed_document_rows(self.fixture_path())
        packet = build_requirement_extraction_delta_packet_v1(rows)

        operations = {candidate["operation"] for candidate in packet["requirement_candidates"]}
        self.assertEqual(operations, {"add", "change", "remove"})
        for candidate in packet["requirement_candidates"]:
            self.assertEqual(candidate["formalization_status"], "candidate_only")
            self.assertIn(candidate["human_review_status"], {"ready_for_review", "needs_human_review", "blocked"})
        for row in packet["confidence_rows"]:
            self.assertGreaterEqual(row["confidence"], 0.0)
            self.assertLessEqual(row["confidence"], 1.0)

    def test_validation_commands_are_exact_offline_commands(self) -> None:
        rows = load_changed_document_rows(self.fixture_path())
        packet = build_requirement_extraction_delta_packet_v1(rows)

        self.assertIn(["python3", "-m", "unittest", "ppd.tests.test_requirement_extraction_delta_packet_v1"], packet["validation_commands"])
        self.assertIn(["python3", "ppd/daemon/ppd_daemon.py", "--self-test"], packet["validation_commands"])
        for command in packet["validation_commands"]:
            self.assertIsInstance(command, list)
            self.assertEqual(command[0], "python3")


if __name__ == "__main__":
    unittest.main()
