from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "agent_work_order"
    / "agent_autonomous_assistance_work_order.json"
)

FORBIDDEN_ACTIONS = {
    "upload_official_document",
    "submit_application",
    "certify_statement",
    "pay_fee",
    "cancel_request",
    "schedule_inspection",
}
FORBIDDEN_MARKERS = (
    "ppd/data/private",
    "auth-state",
    "storage-state",
    "trace.zip",
    ".har",
    "cookie",
    "password",
    "token",
)


class AgentAutonomousAssistanceWorkOrderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_work_order_boundary_is_fixture_only_and_redacted(self) -> None:
        boundary = self.fixture["executionBoundary"]
        self.assertEqual("agent_autonomous_assistance_work_order", self.fixture["fixtureKind"])
        self.assertTrue(boundary["fixtureOnly"])
        self.assertTrue(boundary["usesUserDocumentStoreFacts"])
        self.assertFalse(boundary["networkAccess"])
        self.assertFalse(boundary["liveDevhubAccess"])
        self.assertFalse(boundary["officialDevhubActionsAllowed"])
        self.assertTrue(boundary["storesOnlyRedactedValues"])

        serialized = json.dumps(self.fixture, sort_keys=True).lower()
        for marker in FORBIDDEN_MARKERS:
            self.assertNotIn(marker, serialized)
        self.assertEqual([], find_unredacted_values(self.fixture))

    def test_ordered_steps_compose_available_facts_gaps_and_stop_gates(self) -> None:
        fact_ids = {item["factId"] for item in self.fixture["userDocumentStoreFacts"]}
        gap_ids = {item["gapId"] for item in self.fixture["missingPpdFacts"]}
        gate_ids = {item["gateId"] for item in self.fixture["formalStopGates"]}
        steps = self.fixture["orderedSteps"]

        self.assertEqual([1, 2, 3, 4], [step["order"] for step in steps])
        self.assertEqual("read_user_document_store_facts", steps[0]["stepType"])
        self.assertEqual("ask_user_questions", steps[1]["stepType"])
        self.assertEqual("preview_reversible_draft_fields", steps[2]["stepType"])
        self.assertEqual("stop_before_official_devhub_actions", steps[3]["stepType"])

        self.assertTrue(set(steps[0]["inputs"]).issubset(fact_ids))
        self.assertTrue(set(steps[1]["inputs"]).issubset(gap_ids))
        self.assertTrue(set(steps[3]["inputs"]).issubset(gate_ids))
        self.assertFalse(steps[2]["allowedAutonomous"])
        self.assertEqual(["gap-project-site-address"], steps[2]["requiresResolvedGapIds"])

    def test_stop_gates_refuse_official_actions_and_completion(self) -> None:
        gates = {item["gateId"]: item for item in self.fixture["formalStopGates"]}
        self.assertTrue(gates["gate-missing-ppd-facts"]["blocksAutonomousCompletion"])
        self.assertIn("PROHIBITED", gates["gate-missing-ppd-facts"]["formalRule"])

        official_gate = gates["gate-official-devhub-actions"]
        self.assertEqual("refuse", official_gate["defaultOutcome"])
        self.assertTrue(FORBIDDEN_ACTIONS.issubset(set(official_gate["blocksActions"])))
        self.assertFalse(official_gate["exactConfirmationPresent"])

        outcome = self.fixture["plannerOutcome"]
        self.assertFalse(outcome["autonomousCompletionAllowed"])
        self.assertFalse(outcome["officialActionsAllowed"])
        self.assertTrue(outcome["safeWorkOrderReady"])

    def test_playwright_previews_are_draft_only_and_selector_confident(self) -> None:
        step_ids = {item["stepId"] for item in self.fixture["orderedSteps"]}
        for preview in self.fixture["draftOnlyPlaywrightPreviews"]:
            self.assertIn(preview["linkedStepId"], step_ids)
            self.assertEqual("reversible_draft_edit", preview["actionClass"])
            self.assertEqual("preview_only", preview["mode"])
            self.assertFalse(preview["executesInFixture"])
            self.assertTrue(preview["afterValue"].startswith("[REDACTED_"))
            self.assertGreaterEqual(preview["selector"]["confidence"], 0.9)
            self.assertTrue(preview["selector"]["accessibleName"])


def find_unredacted_values(value: Any, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in {"rawvalue", "privatevalue", "knownvalue"}:
                findings.append(f"{path}.{key}")
            findings.extend(find_unredacted_values(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(find_unredacted_values(child, f"{path}[{index}]"))
    elif isinstance(value, str) and "real user" in value.lower():
        findings.append(path)
    return findings


if __name__ == "__main__":
    unittest.main()
