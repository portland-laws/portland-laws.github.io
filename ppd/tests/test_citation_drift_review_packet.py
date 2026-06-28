"""Fixture-first tests for citation drift review packets."""

from __future__ import annotations

from copy import deepcopy
import json
import py_compile
import unittest
from pathlib import Path

from ppd.validation.citation_drift_review_packet import build_citation_drift_review_packet

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "citation_drift" / "review_packet.json"
MODULE_PATH = Path(__file__).parents[1] / "validation" / "citation_drift_review_packet.py"


class CitationDriftReviewPacketTests(unittest.TestCase):
    def load_fixture(self) -> dict:
        with FIXTURE_PATH.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def assert_rejected(self, fixture: dict, message: str) -> None:
        with self.assertRaisesRegex(ValueError, message):
            build_citation_drift_review_packet(fixture)

    def test_module_is_syntax_valid_before_packet_validation(self) -> None:
        py_compile.compile(str(MODULE_PATH), doraise=True)

    def test_packet_classifies_stale_missing_moved_and_unchanged_spans(self) -> None:
        packet = build_citation_drift_review_packet(self.load_fixture())

        self.assertEqual(packet["schema_version"], 1)
        self.assertEqual(packet["requirement_text_refresh_status"], "blocked_pending_human_review")
        self.assertIs(packet["requirement_text_refresh_allowed"], False)
        self.assertEqual(packet["summary"]["stale_count"], 1)
        self.assertEqual(packet["summary"]["missing_count"], 1)
        self.assertEqual(packet["summary"]["moved_count"], 1)
        self.assertEqual(packet["summary"]["unchanged_count"], 1)
        self.assertEqual(packet["summary"]["human_review_prompt_count"], 3)

        by_evidence = {
            item["evidence_id"]: item["status"]
            for item in packet["citation_drift_observations"]
        }
        self.assertEqual(by_evidence["EV-STALE-FILE-RULE"], "stale")
        self.assertEqual(by_evidence["EV-MISSING-DEADLINE"], "missing")
        self.assertEqual(by_evidence["EV-MOVED-UPLOAD"], "moved")
        self.assertEqual(by_evidence["EV-UNCHANGED-SINGLE-PDF"], "unchanged")

    def test_review_prompts_block_refresh_for_only_drifted_citations(self) -> None:
        packet = build_citation_drift_review_packet(self.load_fixture())

        prompt_evidence_ids = {prompt["evidence_id"] for prompt in packet["human_review_prompts"]}
        self.assertEqual(prompt_evidence_ids, {"EV-STALE-FILE-RULE", "EV-MISSING-DEADLINE", "EV-MOVED-UPLOAD"})
        for prompt in packet["human_review_prompts"]:
            self.assertEqual(prompt["prompt_type"], "human_citation_review_before_requirement_text_refresh")
            self.assertIs(prompt["blocks_requirement_text_refresh"], True)
            self.assertIn("before refreshing text", prompt["question"])

    def test_rejects_raw_document_bodies(self) -> None:
        fixture = self.load_fixture()
        fixture["changed_normalized_documents"][0]["raw_body"] = "raw page body"

        self.assert_rejected(fixture, "raw document body field")

    def test_rejects_invented_span_offsets(self) -> None:
        fixture = self.load_fixture()
        span = fixture["changed_normalized_documents"][0]["citation_spans"][0]
        span["start_offset"] = 22
        span["end_offset"] = 71

        self.assert_rejected(fixture, "invented span offsets")

    def test_rejects_missing_source_archive_or_document_identifiers(self) -> None:
        for field_name in ("document_id", "source_id", "archive_artifact_ref"):
            fixture = self.load_fixture()
            fixture["changed_normalized_documents"][0][field_name] = ""

            self.assert_rejected(fixture, f"{field_name} is required")

    def test_rejects_private_values_and_downloaded_document_paths(self) -> None:
        private_value_fixture = self.load_fixture()
        private_value_fixture["requirement_nodes"][0]["private_value"] = "permit applicant phone number"
        self.assert_rejected(private_value_fixture, "private value field")

        downloaded_path_fixture = self.load_fixture()
        downloaded_path_fixture["changed_normalized_documents"][0]["downloaded_document_path"] = "/home/person/Downloads/permit.pdf"
        self.assert_rejected(downloaded_path_fixture, "downloaded document path")

    def test_rejects_private_or_raw_artifact_references(self) -> None:
        fixture = self.load_fixture()
        fixture["changed_normalized_documents"][0]["raw_artifact_ref"] = "ppd/.daemon/private/session/trace.har"

        self.assert_rejected(fixture, "private or raw artifact")

    def test_rejects_unchanged_status_for_changed_hash_without_evidence(self) -> None:
        fixture = self.load_fixture()
        fixture["citation_drift_observations"] = [
            {
                "requirement_id": "REQ-FILE-NAMING",
                "evidence_id": "EV-STALE-FILE-RULE",
                "status": "unchanged",
            }
        ]

        self.assert_rejected(fixture, "unchanged status for changed hashes requires evidence")

    def test_allows_unchanged_status_for_changed_hash_with_review_evidence(self) -> None:
        fixture = self.load_fixture()
        fixture["citation_drift_observations"] = [
            {
                "requirement_id": "REQ-FILE-NAMING",
                "evidence_id": "EV-STALE-FILE-RULE",
                "status": "unchanged",
                "human_review_evidence_id": "HR-CITATION-REVIEW-001",
            }
        ]

        packet = build_citation_drift_review_packet(fixture)
        self.assertEqual(packet["summary"]["stale_count"], 1)

    def test_rejects_ready_formalization_before_human_review(self) -> None:
        fixture = self.load_fixture()
        requirement = deepcopy(fixture["requirement_nodes"][0])
        requirement["requirement_id"] = "REQ-PREMATURE-FORMALIZATION"
        requirement["human_review_status"] = "pending"
        requirement["formalization_status"] = "ready"
        fixture["requirement_nodes"].append(requirement)

        self.assert_rejected(fixture, "ready formalization before human review")


if __name__ == "__main__":
    unittest.main()
