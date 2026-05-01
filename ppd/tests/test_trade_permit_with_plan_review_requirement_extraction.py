"""Validate requirement extraction coverage for trade permits with plan review.

This test is fixture-only. It does not crawl Portland.gov, open DevHub,
authenticate, submit, upload, pay, or inspect private session artifacts.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import unittest


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "requirement_extraction"
    / "trade_permit_with_plan_review_requirements.json"
)

REQUIRED_TOP_LEVEL_KEYS = {
    "fixture_id",
    "process_id",
    "source_profile",
    "captured_at",
    "requirements",
    "coverage_expectations",
}

REQUIRED_REQUIREMENT_KEYS = {
    "requirement_id",
    "type",
    "category",
    "subject",
    "action",
    "object",
    "conditions",
    "deadline_or_temporal_scope",
    "evidence",
    "confidence",
    "formalization_status",
}

EXPECTED_CATEGORIES = {
    "eligibility_precondition",
    "upload_requirement",
    "fee_payment_checkpoint",
    "correction_path",
    "explicit_confirmation_gate",
}

CONFIRMATION_GATE_CATEGORIES = {
    "fee_payment_checkpoint",
    "explicit_confirmation_gate",
}

PRIVATE_ARTIFACT_MARKERS = (
    "ppd/data/private",
    "storage_state",
    "auth_state",
    "trace.zip",
    "playwright-report",
    "screenshot",
    "captcha",
    "mfa secret",
    "password",
    "cookie",
    "bearer ",
)


class TradePermitWithPlanReviewRequirementExtractionTest(unittest.TestCase):
    def setUp(self) -> None:
        with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
            self.fixture: dict[str, Any] = json.load(fixture_file)
        self.requirements: list[dict[str, Any]] = self.fixture["requirements"]

    def test_fixture_shape_is_complete(self) -> None:
        self.assertTrue(REQUIRED_TOP_LEVEL_KEYS.issubset(self.fixture))
        self.assertEqual("trade-permit-with-plan-review", self.fixture["process_id"])
        self.assertEqual("fixture_only_public_guidance_summary", self.fixture["source_profile"])
        self.assertTrue(self.fixture["captured_at"].endswith("Z"))
        self.assertGreaterEqual(len(self.requirements), 10)

        requirement_ids: set[str] = set()
        for requirement in self.requirements:
            self.assertTrue(REQUIRED_REQUIREMENT_KEYS.issubset(requirement), requirement)
            requirement_id = requirement["requirement_id"]
            self.assertNotIn(requirement_id, requirement_ids)
            requirement_ids.add(requirement_id)
            self.assertTrue(requirement_id.startswith("tpwpr-"))
            self.assertIsInstance(requirement["conditions"], list)
            self.assertGreaterEqual(len(requirement["conditions"]), 1)
            self.assertIsInstance(requirement["evidence"], list)
            self.assertGreaterEqual(len(requirement["evidence"]), 1)
            self.assertGreaterEqual(requirement["confidence"], 0.8)
            self.assertLessEqual(requirement["confidence"], 1.0)

    def test_required_categories_are_covered_at_expected_depth(self) -> None:
        categories = [requirement["category"] for requirement in self.requirements]
        self.assertTrue(EXPECTED_CATEGORIES.issubset(set(categories)))

        expectations = self.fixture["coverage_expectations"]
        for category, expected_count in expectations.items():
            with self.subTest(category=category):
                self.assertIn(category, EXPECTED_CATEGORIES)
                actual_count = categories.count(category)
                self.assertGreaterEqual(actual_count, expected_count)

    def test_eligibility_preconditions_are_explicit(self) -> None:
        eligibility_requirements = self._requirements_for("eligibility_precondition")
        combined_text = self._combined_text(eligibility_requirements)
        self.assertIn("devhub account", combined_text)
        self.assertIn("portlandoregon.gov credentials", combined_text)
        self.assertIn("trade permit with plan review", combined_text)
        self.assertIn("property", combined_text)
        self.assertIn("work description", combined_text)
        self.assertTrue(all(item["type"] == "precondition" for item in eligibility_requirements))

    def test_upload_requirements_name_documents_and_timing(self) -> None:
        upload_requirements = self._requirements_for("upload_requirement")
        combined_text = self._combined_text(upload_requirements)
        self.assertIn("application", combined_text)
        self.assertIn("supporting", combined_text)
        self.assertIn("plan", combined_text)
        self.assertIn("pdf", combined_text)
        self.assertIn("before", combined_text)
        self.assertTrue(all(item["type"] == "obligation" for item in upload_requirements))

    def test_fee_payment_checkpoints_are_financial_confirmation_gates(self) -> None:
        fee_requirements = self._requirements_for("fee_payment_checkpoint")
        combined_text = self._combined_text(fee_requirements)
        self.assertIn("payment", combined_text)
        self.assertIn("fee", combined_text)
        self.assertIn("stop_before", {item["action"] for item in fee_requirements})
        for requirement in fee_requirements:
            self.assertEqual("action_gate", requirement["type"])
            self.assertIs(requirement.get("requires_explicit_confirmation"), True)

    def test_correction_path_and_upload_gate_are_distinct(self) -> None:
        correction_requirements = self._requirements_for("correction_path")
        correction_gate_requirements = [
            item
            for item in self.requirements
            if item["requirement_id"] == "tpwpr-correction-upload-confirmation-gate"
        ]
        self.assertEqual(1, len(correction_gate_requirements))
        self.assertIn("checksheet", self._combined_text(correction_requirements))
        self.assertIn("correction", self._combined_text(correction_requirements))
        self.assertEqual("obligation", correction_requirements[0]["type"])
        self.assertEqual("action_gate", correction_gate_requirements[0]["type"])
        self.assertIs(correction_gate_requirements[0].get("requires_explicit_confirmation"), True)

    def test_explicit_confirmation_gates_cover_consequential_actions(self) -> None:
        gate_requirements = self._requirements_for("explicit_confirmation_gate")
        combined_text = self._combined_text(gate_requirements)
        self.assertIn("official correction upload", combined_text)
        self.assertIn("submission", combined_text)
        self.assertIn("certification", combined_text)
        for requirement in gate_requirements:
            self.assertEqual("action_gate", requirement["type"])
            self.assertEqual("agent", requirement["subject"])
            self.assertEqual("stop_before", requirement["action"])
            self.assertIs(requirement.get("requires_explicit_confirmation"), True)

    def test_evidence_is_source_backed_without_private_artifacts(self) -> None:
        serialized = json.dumps(self.fixture, sort_keys=True).lower()
        for marker in PRIVATE_ARTIFACT_MARKERS:
            self.assertNotIn(marker, serialized)

        for requirement in self.requirements:
            for evidence in requirement["evidence"]:
                self.assertIn("source_id", evidence)
                self.assertIn("url", evidence)
                self.assertIn("title", evidence)
                self.assertIn("quote", evidence)
                self.assertTrue(evidence["url"].startswith(("https://www.portland.gov/", "docs/")))
                self.assertNotIn("devhub.portlandoregon.gov/secure", evidence["url"])

    def test_confirmation_sensitive_categories_require_exact_gate_marker(self) -> None:
        for requirement in self.requirements:
            if requirement["category"] in CONFIRMATION_GATE_CATEGORIES:
                with self.subTest(requirement=requirement["requirement_id"]):
                    self.assertEqual("action_gate", requirement["type"])
                    self.assertEqual("agent", requirement["subject"])
                    self.assertEqual("stop_before", requirement["action"])
                    self.assertIs(requirement.get("requires_explicit_confirmation"), True)

    def _requirements_for(self, category: str) -> list[dict[str, Any]]:
        matches = [item for item in self.requirements if item["category"] == category]
        self.assertGreaterEqual(len(matches), 1, category)
        return matches

    @staticmethod
    def _combined_text(requirements: list[dict[str, Any]]) -> str:
        return json.dumps(requirements, sort_keys=True).lower()


if __name__ == "__main__":
    unittest.main()
