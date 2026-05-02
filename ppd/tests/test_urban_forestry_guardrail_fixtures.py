"""Fixture-only guardrail coverage for the Urban Forestry permit workflow."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "guardrails"
    / "urban_forestry_permit_workflow.json"
)


class UrbanForestryGuardrailFixtureTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = _load_fixture()
        self.compiled = _compile_fixture_guardrails(self.fixture)

    def test_missing_facts_are_reported_from_fixture_inventory(self) -> None:
        self.assertEqual(
            self.compiled["missingFacts"],
            self.fixture["expectedCompilerOutput"]["missingFacts"],
        )
        self.assertEqual(
            self.compiled["missingFacts"],
            ["fact_tree_species", "fact_tree_diameter", "fact_work_reason"],
        )

    def test_required_document_groups_distinguish_satisfied_and_missing_groups(self) -> None:
        expected = self.fixture["expectedCompilerOutput"]
        self.assertEqual(
            self.compiled["satisfiedDocumentGroups"],
            expected["satisfiedDocumentGroups"],
        )
        self.assertEqual(
            self.compiled["missingDocumentGroups"],
            expected["missingDocumentGroups"],
        )

    def test_payment_correction_inspection_and_finalization_actions_stop_without_confirmation(self) -> None:
        expected_stop_points = {
            "gate_pay_fees",
            "gate_upload_corrections",
            "gate_schedule_inspection",
            "gate_finalize_permit",
        }
        self.assertEqual(set(self.compiled["stopPoints"]), expected_stop_points)
        self.assertEqual(
            self.compiled["allowedActions"],
            self.fixture["expectedCompilerOutput"]["allowedActions"],
        )

    def test_every_stop_point_is_source_backed_and_explicit_confirmation_gated(self) -> None:
        process = self.fixture["permitProcess"]
        source_ids = {source["id"] for source in process["authoritySources"]}
        stop_gates = [gate for gate in process["actionGates"] if gate["stopPoint"]]

        self.assertGreaterEqual(len(stop_gates), 5)
        for gate in stop_gates:
            self.assertIn(gate["sourceId"], source_ids)
            self.assertTrue(gate["requiresExactConfirmation"])
            self.assertIn(gate["classification"], {"consequential", "financial"})


def _load_fixture() -> dict[str, Any]:
    with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
        data = json.load(fixture_file)
    if data.get("fixtureId") != "urban_forestry_permit_guardrails":
        raise AssertionError("unexpected Urban Forestry guardrail fixture id")
    return data


def _compile_fixture_guardrails(fixture: dict[str, Any]) -> dict[str, list[str]]:
    process = fixture["permitProcess"]
    user_case = fixture["userCase"]
    known_facts = user_case["knownFacts"]
    available_documents = set(user_case["availableDocuments"])
    requested_actions = set(user_case["requestedActions"])
    exact_confirmations = set(user_case["exactConfirmations"])

    missing_facts = [
        fact["id"]
        for fact in process["requiredFacts"]
        if not known_facts.get(fact["predicate"], False)
    ]

    missing_document_groups: list[str] = []
    satisfied_document_groups: list[str] = []
    for group in process["requiredDocumentGroups"]:
        document_ids = set(group["documentIds"])
        if group["requirement"] == "at_least_one" and document_ids.intersection(available_documents):
            satisfied_document_groups.append(group["id"])
            continue
        if group["requirement"] == "required_when_removal_requested" and not document_ids.intersection(available_documents):
            missing_document_groups.append(group["id"])
            continue
        if not document_ids.issubset(available_documents):
            missing_document_groups.append(group["id"])
        else:
            satisfied_document_groups.append(group["id"])

    stop_points: list[str] = []
    allowed_actions: list[str] = []
    for action in user_case["requestedActions"]:
        matching_gate = _gate_for_action(process["actionGates"], action)
        if matching_gate is None:
            allowed_actions.append(action)
            continue
        if matching_gate["stopPoint"] and matching_gate["id"] not in exact_confirmations:
            stop_points.append(matching_gate["id"])
        else:
            allowed_actions.append(action)

    return {
        "missingFacts": missing_facts,
        "missingDocumentGroups": missing_document_groups,
        "satisfiedDocumentGroups": satisfied_document_groups,
        "stopPoints": stop_points,
        "allowedActions": allowed_actions,
    }


def _gate_for_action(action_gates: list[dict[str, Any]], action: str) -> dict[str, Any] | None:
    for gate in action_gates:
        if gate["action"] == action:
            return gate
    return None


if __name__ == "__main__":
    unittest.main()
