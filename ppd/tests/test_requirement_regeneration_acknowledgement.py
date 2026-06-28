from __future__ import annotations

import json
from pathlib import Path
import unittest

from ppd.extraction.requirement_regeneration_acknowledgement import (
    validate_reviewer_acknowledgement_packet,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "requirement_regeneration_acknowledgement"


class RequirementRegenerationAcknowledgementTests(unittest.TestCase):
    def load_packet(self, name: str) -> dict:
        return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))

    def issue_codes(self, packet: dict) -> set[str]:
        result = validate_reviewer_acknowledgement_packet(packet)
        return {issue.code for issue in result.issues}

    def test_valid_packet_is_accepted(self) -> None:
        packet = self.load_packet("valid_packet.json")
        result = validate_reviewer_acknowledgement_packet(packet)
        self.assertTrue(result.accepted)
        self.assertEqual((), result.issues)

    def test_rejects_missing_queue_links(self) -> None:
        packet = self.load_packet("valid_packet.json")
        packet.pop("queue_links")
        self.assertIn("missing_queue_links", self.issue_codes(packet))

    def test_rejects_uncited_affected_source_decision(self) -> None:
        packet = self.load_packet("valid_packet.json")
        packet["affected_source_decisions"][0]["citations"] = []
        self.assertIn("uncited_affected_source_decision", self.issue_codes(packet))

    def test_rejects_private_case_facts(self) -> None:
        packet = self.load_packet("valid_packet.json")
        packet["case_facts"] = {"permit_number": "private-fixture-value"}
        self.assertIn("private_case_facts_present", self.issue_codes(packet))

    def test_rejects_raw_document_or_crawl_references(self) -> None:
        packet = self.load_packet("valid_packet.json")
        packet["affected_source_decisions"][0]["raw_crawl_ref"] = "crawl://local/raw/devhub-page"
        self.assertIn("raw_document_or_crawl_reference_present", self.issue_codes(packet))

    def test_rejects_stale_source_accepted_without_acknowledgement(self) -> None:
        packet = self.load_packet("valid_packet.json")
        decision = packet["affected_source_decisions"][0]
        decision["freshness_status"] = "stale"
        decision["reviewer_acknowledged_stale_source"] = False
        self.assertIn(
            "stale_source_accepted_without_reviewer_acknowledgement",
            self.issue_codes(packet),
        )

    def test_rejects_missing_synthetic_fixture_requirements(self) -> None:
        packet = self.load_packet("valid_packet.json")
        packet["synthetic_fixture_requirements"] = []
        self.assertIn("missing_synthetic_fixture_requirements", self.issue_codes(packet))

    def test_rejects_downstream_activation_flags(self) -> None:
        packet = self.load_packet("valid_packet.json")
        packet["activate_downstream"] = True
        self.assertIn("downstream_activation_flag_present", self.issue_codes(packet))


if __name__ == "__main__":
    unittest.main()
