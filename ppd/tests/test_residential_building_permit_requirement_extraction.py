"""Fixture validation for residential building permit requirement extraction."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "requirements"
    / "residential_building_permit_requirements.json"
)


class ResidentialBuildingPermitRequirementExtractionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = _load_fixture()
        cls.requirements = cls.fixture["requirements"]

    def test_fixture_metadata_targets_residential_building_permit(self) -> None:
        self.assertEqual(
            self.fixture["fixture_id"],
            "residential_building_permit_requirement_extraction_v1",
        )
        self.assertEqual(self.fixture["permit_process_id"], "residential_building_permit")
        self.assertTrue(self.fixture["generated_at"].endswith("Z"))
        self.assertTrue(self.requirements)

    def test_requirement_ids_are_unique_and_source_backed(self) -> None:
        requirement_ids = [req["requirement_id"] for req in self.requirements]
        self.assertEqual(len(requirement_ids), len(set(requirement_ids)))

        for req in self.requirements:
            with self.subTest(requirement_id=req["requirement_id"]):
                self.assertIn(
                    req["type"],
                    {
                        "obligation",
                        "prohibition",
                        "permission",
                        "precondition",
                        "exception",
                        "deadline",
                        "dependency",
                        "action_gate",
                    },
                )
                self.assertIn(
                    req["formalization_status"],
                    {"ready_for_guardrail", "needs_human_review", "draft"},
                )
                self.assertGreaterEqual(req["confidence"], 0.7)
                self.assertLessEqual(req["confidence"], 1.0)
                self.assertIsInstance(req["conditions"], list)
                self.assertTrue(req["deadline_or_temporal_scope"].strip())
                self.assertTrue(req["evidence"], "every extracted requirement needs evidence")
                for evidence in req["evidence"]:
                    self.assertTrue(evidence["source_id"].strip())
                    self.assertTrue(evidence["canonical_url"].startswith("https://www.portland.gov/"))
                    self.assertTrue(evidence["section"].strip())
                    self.assertTrue(evidence["quote"].strip())

    def test_eligibility_requirements_cover_property_scope_and_roles(self) -> None:
        eligibility = _by_category(self.requirements, "eligibility")
        joined = _joined_text(eligibility)

        self.assertGreaterEqual(len(eligibility), 2)
        self.assertIn("property", joined)
        self.assertIn("zoning", joined)
        self.assertIn("residential project scope", joined)
        self.assertIn("owner", joined)
        self.assertIn("contractor", joined)
        self.assertTrue(all(req["type"] == "precondition" for req in eligibility))

    def test_submittal_package_requirements_include_application_plans_and_single_pdf(self) -> None:
        submittal = _by_category(self.requirements, "submittal_package")
        joined = _joined_text(submittal)

        self.assertGreaterEqual(len(submittal), 4)
        self.assertIn("completed residential building permit application", joined)
        self.assertIn("building plans", joined)
        self.assertIn("site plan", joined)
        self.assertIn("supporting calculations", joined)
        self.assertIn("single pdf process", joined)
        self.assertIn("one searchable pdf", joined)
        self.assertTrue(
            any(req["formalization_status"] == "ready_for_guardrail" for req in submittal)
        )

    def test_plan_review_requirements_cover_prescreen_and_technical_review(self) -> None:
        review = _by_category(self.requirements, "plan_review_stage")
        joined = _joined_text(review)

        self.assertGreaterEqual(len(review), 2)
        self.assertIn("prescreen", joined)
        self.assertIn("completeness", joined)
        self.assertIn("technical", joined)
        self.assertIn("review groups", joined)
        self.assertTrue(all(req["type"] == "dependency" for req in review))

    def test_corrections_include_response_obligation_and_official_upload_gate(self) -> None:
        corrections = _by_category(self.requirements, "corrections")
        joined = _joined_text(corrections)

        self.assertGreaterEqual(len(corrections), 2)
        self.assertIn("checksheets", joined)
        self.assertIn("corrected plans", joined)
        self.assertTrue(
            any("official upload" in req["object"].lower() for req in corrections),
            "correction requirements must name the official upload stop point",
        )
        self.assertTrue(
            any(req.get("requires_explicit_confirmation") is True for req in corrections),
            "official correction upload needs explicit user confirmation",
        )
        self.assertTrue(
            any(req.get("confirmation_action") == "official_correction_upload" for req in corrections)
        )

    def test_inspections_include_required_inspection_obligation_and_scheduling_gate(self) -> None:
        inspections = _by_category(self.requirements, "inspections")
        joined = _joined_text(inspections)

        self.assertGreaterEqual(len(inspections), 2)
        self.assertIn("required residential building inspections", joined)
        self.assertIn("after permit issuance", joined)
        self.assertIn("inspection scheduling request", joined)
        self.assertTrue(
            any(req.get("confirmation_action") == "schedule_inspection" for req in inspections)
        )

    def test_expiration_and_reactivation_requirements_are_temporal(self) -> None:
        expiration = _by_category(self.requirements, "expiration_reactivation")
        joined = _joined_text(expiration)

        self.assertGreaterEqual(len(expiration), 2)
        self.assertIn("expiration", joined)
        self.assertIn("reactivation", joined)
        self.assertTrue(any(req["type"] == "deadline" for req in expiration))
        self.assertTrue(any(req["type"] == "permission" for req in expiration))
        self.assertTrue(
            all("expire" in req["deadline_or_temporal_scope"].lower() or "expiration" in req["deadline_or_temporal_scope"].lower() for req in expiration)
        )

    def test_explicit_confirmation_gates_cover_submission_payment_corrections_and_inspections(self) -> None:
        gates = [
            req
            for req in self.requirements
            if req["type"] == "action_gate" or req.get("requires_explicit_confirmation") is True
        ]
        gate_actions = {req.get("confirmation_action") for req in gates}

        self.assertTrue(all(req.get("requires_explicit_confirmation") is True for req in gates))
        self.assertTrue(all(req["subject"] == "agent" for req in gates))
        self.assertTrue(all(req["action"] == "stop_before" for req in gates))
        self.assertSetEqual(
            gate_actions,
            {
                "official_correction_upload",
                "schedule_inspection",
                "submit_application",
                "pay_fees",
            },
        )
        self.assertTrue(any("official submission" in req["object"].lower() for req in gates))
        self.assertTrue(any("fee payment" in req["object"].lower() for req in gates))


def _load_fixture() -> dict[str, Any]:
    with FIXTURE_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise AssertionError("residential building permit requirement fixture must be an object")
    if "requirements" not in data or not isinstance(data["requirements"], list):
        raise AssertionError("residential building permit fixture requires a requirements list")
    return data


def _by_category(requirements: list[dict[str, Any]], category: str) -> list[dict[str, Any]]:
    return [req for req in requirements if req["category"] == category]


def _joined_text(requirements: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for req in requirements:
        parts.extend(
            [
                req.get("requirement_id", ""),
                req.get("category", ""),
                req.get("type", ""),
                req.get("subject", ""),
                req.get("action", ""),
                req.get("object", ""),
                req.get("deadline_or_temporal_scope", ""),
                req.get("confirmation_action", ""),
            ]
        )
        parts.extend(req.get("conditions", []))
        for evidence in req.get("evidence", []):
            parts.extend(
                [
                    evidence.get("source_id", ""),
                    evidence.get("canonical_url", ""),
                    evidence.get("section", ""),
                    evidence.get("quote", ""),
                ]
            )
    return " ".join(parts).lower()


if __name__ == "__main__":
    unittest.main()
