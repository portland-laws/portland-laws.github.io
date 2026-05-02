"""Fixture tests for solar permit guardrail compiler behavior.

These tests stay fixture-only. They validate the expected compiler output for a
solar permit workflow without opening DevHub, uploading documents, scheduling
inspections, or attempting payment.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "guardrails" / "solar_permit_workflow_guardrails.json"


class SolarPermitGuardrailFixtureTests(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
            cls.fixture = json.load(fixture_file)

    def test_fixture_is_redacted_and_source_backed(self) -> None:
        process = self.fixture["process"]
        self.assertEqual(process["id"], "solar-permit-workflow")
        self.assertEqual(process["permitType"], "solar_permit")

        for evidence in process["evidence"]:
            self.assertTrue(evidence["sourceUrl"].startswith("https://www.portland.gov/ppd"))
            self.assertTrue(evidence["retrievedAt"].endswith("Z"))
            self.assertNotIn("rawBody", evidence)
            self.assertNotIn("html", evidence)
            self.assertNotIn("screenshot", evidence)

        serialized = json.dumps(self.fixture, sort_keys=True).lower()
        forbidden_fragments = (
            "password",
            "authorization",
            "bearer ",
            "cookie",
            "storage_state",
            "auth_state",
            "trace.zip",
            "screenshot.png",
            "ppd/data/private",
        )
        for fragment in forbidden_fragments:
            self.assertNotIn(fragment, serialized)

    def test_missing_facts_are_reported_before_submission(self) -> None:
        result = _compile_fixture_case(self.fixture, "missing_facts")
        self.assertEqual(result["caseId"], "missing_facts")
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["missingFacts"], ["property_identifier", "contractor_license_number"])
        self.assertIn("submit_application", result["blockedActions"])
        self.assertIn("ask_user_for_missing_facts", result["allowedActions"])

    def test_required_document_groups_block_incomplete_package(self) -> None:
        result = _compile_fixture_case(self.fixture, "missing_required_document_groups")
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(
            result["missingDocumentGroups"],
            ["solar_plans", "structural_roof_documentation"],
        )
        self.assertIn("upload_application_package", result["blockedActions"])
        self.assertIn("submit_application", result["blockedActions"])

    def test_payment_stop_point_requires_exact_confirmation(self) -> None:
        result = _compile_fixture_case(self.fixture, "payment_due_no_confirmation")
        self.assertEqual(result["status"], "stop_for_confirmation")
        self.assertEqual(result["stopPoints"], ["pay_fees"])
        self.assertIn("pay_fees", result["blockedActions"])
        self.assertIn("exact_user_confirmation_required", result["reasons"])

    def test_correction_upload_stop_point_requires_exact_confirmation(self) -> None:
        result = _compile_fixture_case(self.fixture, "correction_upload_ready_no_confirmation")
        self.assertEqual(result["status"], "stop_for_confirmation")
        self.assertEqual(result["stopPoints"], ["upload_corrections"])
        self.assertIn("upload_corrections", result["blockedActions"])
        self.assertIn("produce_correction_upload_preview", result["allowedActions"])

    def test_inspection_scheduling_stop_point_requires_exact_confirmation(self) -> None:
        result = _compile_fixture_case(self.fixture, "inspection_ready_no_confirmation")
        self.assertEqual(result["status"], "stop_for_confirmation")
        self.assertEqual(result["stopPoints"], ["schedule_inspection"])
        self.assertIn("schedule_inspection", result["blockedActions"])
        self.assertIn("produce_inspection_scheduling_preview", result["allowedActions"])


def _compile_fixture_case(fixture: dict[str, Any], case_id: str) -> dict[str, Any]:
    process = fixture["process"]
    case = _case_by_id(fixture, case_id)
    known_facts = set(case.get("knownFacts", []))
    uploaded_groups = set(case.get("uploadedDocumentGroups", []))
    confirmations = set(case.get("exactConfirmations", []))
    workflow_state = case["workflowState"]

    missing_facts = [
        fact["id"]
        for fact in process["requiredFacts"]
        if fact["required"] and fact["id"] not in known_facts
    ]
    missing_document_groups = [
        group["id"]
        for group in process["requiredDocumentGroups"]
        if group["required"] and group["id"] not in uploaded_groups
    ]

    blocked_actions: list[str] = []
    allowed_actions: list[str] = []
    stop_points: list[str] = []
    reasons: list[str] = []

    if missing_facts:
        blocked_actions.append("submit_application")
        allowed_actions.append("ask_user_for_missing_facts")
    if missing_document_groups:
        blocked_actions.extend(["upload_application_package", "submit_application"])
        allowed_actions.append("ask_user_for_missing_documents")

    for gate in process["actionGates"]:
        action = gate["action"]
        if gate["workflowState"] != workflow_state:
            continue
        if gate["requiresExactConfirmation"] and action not in confirmations:
            stop_points.append(action)
            blocked_actions.append(action)
            reasons.append("exact_user_confirmation_required")
            preview_action = gate.get("previewAction")
            if preview_action:
                allowed_actions.append(preview_action)

    if stop_points:
        status = "stop_for_confirmation"
    elif missing_facts or missing_document_groups:
        status = "blocked"
    else:
        status = "ready_for_draft_review"

    return {
        "caseId": case_id,
        "status": status,
        "missingFacts": missing_facts,
        "missingDocumentGroups": missing_document_groups,
        "stopPoints": _dedupe(stop_points),
        "blockedActions": _dedupe(blocked_actions),
        "allowedActions": _dedupe(allowed_actions),
        "reasons": _dedupe(reasons),
    }


def _case_by_id(fixture: dict[str, Any], case_id: str) -> dict[str, Any]:
    for case in fixture["cases"]:
        if case["id"] == case_id:
            return case
    raise AssertionError(f"fixture case not found: {case_id}")


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


if __name__ == "__main__":
    unittest.main()
