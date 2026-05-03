from __future__ import annotations

import json
import unittest
from pathlib import Path


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "formal_logic" / "formal_logic_export_bundle.json"
OFFICIAL_ACTIONS = {
    "upload_official_document",
    "submit_application",
    "pay_fee",
    "certify_statement",
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


class FormalLogicExportBundleTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_requirement_nodes_export_to_obligations_with_source_evidence(self) -> None:
        self.assertEqual("formal_logic_export_bundle", self.fixture["fixtureKind"])
        requirement_ids = {node["requirementId"] for node in self.fixture["requirementNodes"]}
        for node in self.fixture["requirementNodes"]:
            self.assertTrue(node["predicate"])
            self.assertTrue(node["sourceEvidenceIds"])
        for obligation in self.fixture["obligations"]:
            self.assertIn(obligation["requirementId"], requirement_ids)
            self.assertTrue(obligation["logic"])
            self.assertTrue(obligation["sourceEvidenceIds"])

    def test_prerequisites_and_stop_gates_fail_closed(self) -> None:
        for prerequisite in self.fixture["prerequisites"]:
            self.assertTrue(prerequisite["predicate"])
            self.assertEqual("ask_user", prerequisite["defaultOutcomeWhenMissing"])

        gates = {gate["gateId"]: gate for gate in self.fixture["stopGates"]}
        self.assertEqual("ask_user", gates["gate-missing-required-input"]["defaultOutcome"])
        self.assertEqual("refuse", gates["gate-exact-confirmation"]["defaultOutcome"])
        self.assertTrue(OFFICIAL_ACTIONS.issubset(set(gates["gate-exact-confirmation"]["blocksActions"])))

    def test_exact_confirmation_predicates_are_absent_by_default(self) -> None:
        predicates = {item["actionId"]: item for item in self.fixture["exactConfirmationPredicates"]}
        self.assertEqual(OFFICIAL_ACTIONS, set(predicates))
        for item in predicates.values():
            self.assertTrue(item["logic"].startswith("exact_confirmation("))
            self.assertFalse(item["present"])

    def test_boundary_and_export_outcome_are_fixture_only(self) -> None:
        boundary = self.fixture["boundary"]
        self.assertTrue(boundary["fixtureOnly"])
        self.assertFalse(boundary["liveDevhubAccess"])
        self.assertFalse(boundary["officialActionAllowed"])
        self.assertFalse(boundary["privateArtifactStored"])

        outcome = self.fixture["exportOutcome"]
        self.assertTrue(outcome["mayAssistDraftPreparation"])
        self.assertTrue(outcome["mayAskUserForMissingFacts"])
        self.assertFalse(outcome["mayPerformOfficialActions"])
        self.assertEqual("fail_closed", outcome["defaultPolicy"])

        serialized = json.dumps(self.fixture, sort_keys=True).lower()
        for marker in FORBIDDEN_MARKERS:
            self.assertNotIn(marker, serialized)


if __name__ == "__main__":
    unittest.main()
