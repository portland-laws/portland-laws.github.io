"""Fixture-only guardrail compiler tests for the demolition permit workflow."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "guardrails" / "demolition_permit_workflow.json"


FINANCIAL_ACTIONS = {"pay_fees", "enter_payment_details"}
CONSEQUENTIAL_ACTIONS = {
    "submit_application",
    "upload_corrections",
    "schedule_inspection",
    "finalize_or_close_permit",
}


class DemolitionPermitGuardrailCompilerTests(unittest.TestCase):
    def setUp(self) -> None:
        with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
            self.fixture: dict[str, Any] = json.load(fixture_file)
        self.compiled = _compile_guardrails(self.fixture)

    def test_missing_facts_are_derived_from_fixture_only(self) -> None:
        self.assertEqual(
            self.fixture["expectedCompilerOutput"]["missingFacts"],
            self.compiled["missingFacts"],
        )
        self.assertEqual(
            ["demolition_scope", "utility_disconnect_status", "asbestos_acknowledgment"],
            self.compiled["missingFacts"],
        )

    def test_required_document_groups_are_checked_by_group(self) -> None:
        self.assertEqual(
            self.fixture["expectedCompilerOutput"]["satisfiedDocumentGroups"],
            self.compiled["satisfiedDocumentGroups"],
        )
        self.assertEqual(
            self.fixture["expectedCompilerOutput"]["missingDocumentGroups"],
            self.compiled["missingDocumentGroups"],
        )
        self.assertEqual(["application_documents"], self.compiled["satisfiedDocumentGroups"])
        self.assertEqual(["hazardous_material_documents"], self.compiled["missingDocumentGroups"])

    def test_payment_stop_point_is_financial_and_requires_exact_confirmation(self) -> None:
        payment_gate = self.compiled["stopPointById"]["pay_demolition_fees"]
        self.assertEqual("financial", payment_gate["classification"])
        self.assertEqual("pay_fees", payment_gate["action"])
        self.assertTrue(payment_gate["requiresExactConfirmation"])
        self.assertTrue(payment_gate["stopPoint"])

    def test_correction_upload_stop_point_is_consequential(self) -> None:
        correction_gate = self.compiled["stopPointById"]["upload_demolition_corrections"]
        self.assertEqual("consequential", correction_gate["classification"])
        self.assertEqual("upload_corrections", correction_gate["action"])
        self.assertTrue(correction_gate["requiresExactConfirmation"])
        self.assertTrue(correction_gate["stopPoint"])

    def test_inspection_and_finalization_stop_points_are_consequential(self) -> None:
        for gate_id in ("schedule_demolition_inspection", "finalize_demolition_permit"):
            gate = self.compiled["stopPointById"][gate_id]
            self.assertEqual("consequential", gate["classification"])
            self.assertTrue(gate["requiresExactConfirmation"])
            self.assertTrue(gate["stopPoint"])

    def test_all_stop_points_are_source_backed_and_expected(self) -> None:
        self.assertEqual(
            self.fixture["expectedCompilerOutput"]["stopPoints"],
            self.compiled["stopPoints"],
        )
        source_ids = {source["id"] for source in self.fixture["process"]["authoritySources"]}
        for gate in self.compiled["stopPointById"].values():
            self.assertIn(gate["sourceId"], source_ids)

    def test_fixture_contains_no_private_or_live_automation_artifacts(self) -> None:
        serialized = json.dumps(self.fixture, sort_keys=True).lower()
        forbidden_tokens = (
            "password",
            "credential",
            "auth_state",
            "storage_state",
            "cookie",
            "trace.zip",
            "screenshot",
            "captcha",
            "mfa_secret",
            "ppd/data/private",
            "ppd/data/raw",
        )
        for token in forbidden_tokens:
            self.assertNotIn(token, serialized)


def _compile_guardrails(fixture: dict[str, Any]) -> dict[str, Any]:
    process = fixture["process"]
    user_case = fixture["userCase"]
    known_facts = set(user_case.get("knownFacts", {}).keys())
    documents = user_case.get("documents", [])
    document_types_by_group = _document_types_by_group(documents)

    missing_facts: list[str] = []
    for fact in process.get("requiredFacts", []):
        fact_id = fact["id"]
        if fact_id not in known_facts:
            missing_facts.append(fact_id)

    satisfied_groups: list[str] = []
    missing_groups: list[str] = []
    for group in process.get("documentGroups", []):
        if not group.get("required", False):
            continue
        group_id = group["id"]
        required_types = set(group.get("acceptedDocumentTypes", []))
        present_types = document_types_by_group.get(group_id, set())
        if required_types and required_types.issubset(present_types):
            satisfied_groups.append(group_id)
        else:
            missing_groups.append(group_id)

    stop_points: list[str] = []
    stop_point_by_id: dict[str, dict[str, Any]] = {}
    for gate in process.get("actionGates", []):
        action = gate.get("action")
        expected_classification = _classification_for_action(str(action))
        if gate.get("classification") != expected_classification:
            raise AssertionError(f"gate {gate.get('id')} has invalid classification")
        if gate.get("stopPoint") is True:
            gate_id = gate["id"]
            stop_points.append(gate_id)
            stop_point_by_id[gate_id] = gate

    return {
        "missingFacts": missing_facts,
        "satisfiedDocumentGroups": satisfied_groups,
        "missingDocumentGroups": missing_groups,
        "stopPoints": stop_points,
        "stopPointById": stop_point_by_id,
    }


def _document_types_by_group(documents: list[dict[str, Any]]) -> dict[str, set[str]]:
    grouped: dict[str, set[str]] = {}
    for document in documents:
        if document.get("redacted") is not True:
            raise AssertionError(f"document {document.get('id')} must be redacted")
        group_id = str(document.get("groupId", ""))
        document_type = str(document.get("documentType", ""))
        grouped.setdefault(group_id, set()).add(document_type)
    return grouped


def _classification_for_action(action: str) -> str:
    if action in FINANCIAL_ACTIONS:
        return "financial"
    if action in CONSEQUENTIAL_ACTIONS:
        return "consequential"
    return "read_only"


if __name__ == "__main__":
    unittest.main()
