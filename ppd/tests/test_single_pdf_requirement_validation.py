"""Validate Single PDF Process requirement extraction fixtures."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from ppd.contracts.requirements import (
    ExtractedRequirementType,
    RequirementFormalizationStatus,
    fixture_from_dict,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "requirements" / "single_pdf_process_requirements.json"


class SinglePdfRequirementValidationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = fixture_from_dict(json.loads(FIXTURE_PATH.read_text(encoding="utf-8")))

    def test_single_pdf_requirements_are_valid(self) -> None:
        self.assertEqual([], self.fixture.validate())
        self.assertEqual("single-pdf-process", self.fixture.process_id)
        self.assertEqual("Single PDF Process", self.fixture.process_name)

    def test_required_extraction_dimensions_are_present(self) -> None:
        requirement_types = {requirement.type for requirement in self.fixture.requirements}
        self.assertIn(ExtractedRequirementType.OBLIGATION, requirement_types)
        self.assertIn(ExtractedRequirementType.PRECONDITION, requirement_types)
        self.assertIn(ExtractedRequirementType.DEADLINE, requirement_types)
        self.assertIn(ExtractedRequirementType.EXCEPTION, requirement_types)

    def test_confidence_evidence_and_formalization_are_populated(self) -> None:
        for requirement in self.fixture.requirements:
            self.assertGreaterEqual(requirement.confidence, 0.5)
            self.assertLessEqual(requirement.confidence, 1.0)
            self.assertTrue(requirement.evidence)
            self.assertIsInstance(requirement.formalization_status, RequirementFormalizationStatus)
            self.assertTrue(requirement.formalization_notes)
            for evidence in requirement.evidence:
                self.assertTrue(evidence.source_url.startswith("https://"))
                self.assertTrue(evidence.quote.strip())

    def test_deadlines_and_exceptions_have_required_context(self) -> None:
        deadlines = [
            requirement
            for requirement in self.fixture.requirements
            if requirement.type == ExtractedRequirementType.DEADLINE
        ]
        exceptions = [
            requirement
            for requirement in self.fixture.requirements
            if requirement.type == ExtractedRequirementType.EXCEPTION
        ]
        preconditions = [
            requirement
            for requirement in self.fixture.requirements
            if requirement.type == ExtractedRequirementType.PRECONDITION
        ]
        self.assertTrue(all(requirement.deadline_or_temporal_scope for requirement in deadlines))
        self.assertTrue(all(requirement.conditions for requirement in exceptions))
        self.assertTrue(all(requirement.conditions for requirement in preconditions))


if __name__ == "__main__":
    unittest.main()
