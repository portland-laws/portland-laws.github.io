"""Tests for fixture-only PP&D formal-logic contradiction validation."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from ppd.logic.contradictions import (
    HUMAN_REVIEW_STATUS,
    validate_contradiction_packet,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "logic" / "formal_contradiction_packet.json"


class FormalLogicContradictionTests(unittest.TestCase):
    def load_packet(self) -> dict:
        with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
            return json.load(fixture_file)

    def test_fixture_detects_contradiction_and_blocks_planning(self) -> None:
        packet = self.load_packet()

        result = validate_contradiction_packet(packet)

        self.assertTrue(result.valid, result.findings)
        self.assertTrue(result.human_review_required)
        self.assertEqual(packet["planning_status"], HUMAN_REVIEW_STATUS)
        self.assertEqual(result.blocked_predicates, ("plans_are_single_searchable_pdf(project)",))

    def test_validation_requires_both_provenance_chains(self) -> None:
        packet = self.load_packet()
        broken_packet = copy.deepcopy(packet)
        broken_packet["contradictions"][0]["provenance_chains"]["right"] = []

        result = validate_contradiction_packet(broken_packet)

        self.assertFalse(result.valid)
        self.assertTrue(
            any("both provenance chains" in finding.message for finding in result.findings),
            result.findings,
        )

    def test_validation_requires_affected_predicate_to_be_blocked(self) -> None:
        packet = self.load_packet()
        broken_packet = copy.deepcopy(packet)
        broken_packet["predicates"][0]["status"] = "available"

        result = validate_contradiction_packet(broken_packet)

        self.assertFalse(result.valid)
        self.assertTrue(
            any("affected predicate must be blocked" in finding.message for finding in result.findings),
            result.findings,
        )

    def test_validation_requires_human_review_before_agent_planning(self) -> None:
        packet = self.load_packet()
        broken_packet = copy.deepcopy(packet)
        broken_packet["planning_status"] = "planning_allowed"
        broken_packet["contradictions"][0]["planning_gate"] = "continue_planning"

        result = validate_contradiction_packet(broken_packet)

        self.assertFalse(result.valid)
        self.assertFalse(result.human_review_required)
        messages = " ".join(finding.message for finding in result.findings)
        self.assertIn("planning_status must be human_review_required", messages)
        self.assertIn("planning_gate must be blocked_until_human_review", messages)


if __name__ == "__main__":
    unittest.main()
