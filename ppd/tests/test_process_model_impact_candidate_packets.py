from __future__ import annotations

import json
import unittest
from pathlib import Path

from ppd.logic.process_model_impact_candidate_packets import (
    validate_process_model_impact_candidate_packet,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "process_model_impact_candidate_packets.json"


class ProcessModelImpactCandidatePacketValidationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_valid_candidate_packet_is_review_only(self) -> None:
        result = validate_process_model_impact_candidate_packet(self.fixture["valid_packet"])

        self.assertTrue(result.ok)
        self.assertEqual((), result.issue_codes())

    def test_invalid_candidate_packets_are_rejected_with_expected_codes(self) -> None:
        for example in self.fixture["invalid_packets"]:
            with self.subTest(example["name"]):
                result = validate_process_model_impact_candidate_packet(example["packet"])

                self.assertFalse(result.ok)
                self.assertIn(example["expected_code"], result.issue_codes())

    def test_rejects_changed_requirement_without_matching_regenerated_link(self) -> None:
        packet = dict(self.fixture["valid_packet"])
        packet["changed_requirement_ids"] = ["req-upload-single-pdf", "req-new-doc-rule"]

        result = validate_process_model_impact_candidate_packet(packet)

        self.assertFalse(result.ok)
        self.assertIn("missing_regenerated_requirement_link", result.issue_codes())


if __name__ == "__main__":
    unittest.main()
