"""Validate the public PP&D requirement-boundary fixture."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "requirement_boundary"
    / "public_permit_requirement_boundary.json"
)


class RequirementBoundaryFixtureTest(unittest.TestCase):
    def setUp(self) -> None:
        with FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
            self.fixture: dict[str, Any] = json.load(fixture_file)

    def test_fixture_separates_requirement_boundary_classes(self) -> None:
        boundary = self.fixture["requirementBoundary"]
        legal_requirements = boundary["legalProceduralRequirements"]
        ui_behaviors = boundary["operationalDevhubUiBehavior"]

        self.assertGreaterEqual(len(legal_requirements), 1)
        self.assertGreaterEqual(len(ui_behaviors), 1)
        self.assertTrue(
            all(
                item["boundaryClass"] == "legal_or_procedural_obligation"
                for item in legal_requirements
            )
        )
        self.assertTrue(
            all(
                item["boundaryClass"] == "operational_devhub_ui_behavior"
                for item in ui_behaviors
            )
        )

    def test_records_preserve_evidence_type_confidence_and_review_flags(self) -> None:
        evidence_ids = {item["id"] for item in self.fixture["sourceEvidence"]}
        records = self._boundary_records()
        seen_ids: set[str] = set()

        for record in records:
            record_id = record.get("requirementId") or record.get("behaviorId")
            self.assertIsInstance(record_id, str)
            self.assertNotEqual(record_id.strip(), "")
            self.assertNotIn(record_id, seen_ids)
            seen_ids.add(record_id)

            self.assertIn(record["requirementType"], self._allowed_requirement_types())
            self.assertIsInstance(record["confidence"], float)
            self.assertGreaterEqual(record["confidence"], 0.0)
            self.assertLessEqual(record["confidence"], 1.0)
            self.assertIsInstance(record["reviewNeeded"], bool)
            self.assertGreaterEqual(len(record["sourceEvidenceIds"]), 1)
            self.assertTrue(set(record["sourceEvidenceIds"]).issubset(evidence_ids))
            self.assertNotEqual(record["boundaryRationale"].strip(), "")

    def test_fixture_contains_no_private_or_consequential_automation_data(self) -> None:
        privacy = self.fixture["privacyAndSafety"]
        self.assertTrue(privacy["fixtureOnly"])
        for key, value in privacy.items():
            if key != "fixtureOnly":
                self.assertIs(value, False, key)

        serialized = json.dumps(self.fixture, sort_keys=True).lower()
        forbidden_fragments = (
            "password",
            "cookie",
            "storage_state",
            "auth_state",
            "trace.zip",
            "screenshot",
            "private/session",
            "mfa code",
            "captcha token",
            "payment card",
            "official submission",
            "official upload",
        )
        for fragment in forbidden_fragments:
            self.assertNotIn(fragment, serialized)

    def test_operational_behavior_is_not_misclassified_as_obligation(self) -> None:
        ui_behaviors = self.fixture["requirementBoundary"]["operationalDevhubUiBehavior"]
        for behavior in ui_behaviors:
            self.assertNotEqual(behavior["requirementType"], "obligation")
            self.assertIn("operational", behavior["boundaryClass"])

    def _boundary_records(self) -> list[dict[str, Any]]:
        boundary = self.fixture["requirementBoundary"]
        return [
            *boundary["legalProceduralRequirements"],
            *boundary["operationalDevhubUiBehavior"],
        ]

    @staticmethod
    def _allowed_requirement_types() -> set[str]:
        return {
            "obligation",
            "prohibition",
            "permission",
            "precondition",
            "exception",
            "deadline",
            "dependency",
            "action_gate",
        }


if __name__ == "__main__":
    unittest.main()
