from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "gap_resolution"
    / "user_gap_resolution_scenario.json"
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


class UserGapResolutionScenarioTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_boundary_refuses_autonomous_completion_while_gaps_remain(self) -> None:
        boundary = self.fixture["planningBoundary"]
        self.assertEqual("user_gap_resolution_scenario", self.fixture["fixtureKind"])
        self.assertTrue(boundary["fixtureOnly"])
        self.assertFalse(boundary["networkAccess"])
        self.assertFalse(boundary["liveDevhubAccess"])
        self.assertFalse(boundary["storesPrivateValues"])
        self.assertFalse(boundary["autonomousCompletionAllowed"])

        outcome = self.fixture["plannerOutcome"]
        self.assertFalse(outcome["autonomousCompletionAllowed"])
        self.assertEqual("ask_source_linked_questions", outcome["nextAgentAction"])
        self.assertEqual("preview_reversible_draft_fields_only", outcome["afterUserAnswers"])
        self.assertTrue(outcome["requiresHumanReview"])

    def test_questions_are_source_linked_to_missing_facts_and_placeholders(self) -> None:
        evidence_ids = {item["sourceEvidenceId"] for item in self.fixture["sourceEvidence"]}
        gap_ids = {item["factId"] for item in self.fixture["userCaseFacts"]}
        gap_ids.update(item["placeholderId"] for item in self.fixture["documentPlaceholders"])

        for question in self.fixture["questions"]:
            self.assertTrue(question["questionText"].endswith("?"))
            self.assertTrue(set(question["sourceEvidenceIds"]).issubset(evidence_ids))
            self.assertTrue(set(question["linkedGapIds"]).issubset(gap_ids))
            self.assertIn(
                question["allowedUseAfterAnswer"],
                {"preview_reversible_draft_fill_only", "record_placeholder_status_only"},
            )

    def test_stale_evidence_and_missing_documents_create_stop_gates(self) -> None:
        stale_evidence = [item for item in self.fixture["sourceEvidence"] if item["stale"]]
        self.assertTrue(stale_evidence)

        placeholders = self.fixture["documentPlaceholders"]
        self.assertTrue(any(item["evidenceStale"] for item in placeholders))
        self.assertTrue(all(item["blocksAutonomousCompletion"] for item in placeholders))

        gates = {gate["gateId"]: gate for gate in self.fixture["stopGates"]}
        self.assertEqual("human_review", gates["gate-stale-document-evidence"]["defaultOutcome"])
        self.assertTrue(gates["gate-stale-document-evidence"]["blocksAutonomousCompletion"])
        self.assertIn("stale_evidence(src-ppd-public-checklist)", gates["gate-stale-document-evidence"]["blockedWhen"])

    def test_forbidden_official_actions_are_refused_and_private_values_are_absent(self) -> None:
        official_gate = next(gate for gate in self.fixture["stopGates"] if gate["gateId"] == "gate-official-actions")
        self.assertEqual("refuse", official_gate["defaultOutcome"])
        self.assertTrue(FORBIDDEN_ACTIONS.issubset(set(official_gate["blockedActions"])))

        serialized = json.dumps(self.fixture, sort_keys=True).lower()
        for marker in FORBIDDEN_MARKERS:
            self.assertNotIn(marker, serialized)
        self.assertEqual([], find_unredacted_private_values(self.fixture))


def find_unredacted_private_values(value: Any, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in {"knownvalue", "rawvalue", "privatevalue"}:
                findings.append(f"{path}.{key}")
            findings.extend(find_unredacted_private_values(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(find_unredacted_private_values(child, f"{path}[{index}]"))
    elif isinstance(value, str) and "real user" in value.lower():
        findings.append(path)
    return findings


if __name__ == "__main__":
    unittest.main()
