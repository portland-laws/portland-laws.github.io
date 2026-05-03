from __future__ import annotations

import json
import unittest
from pathlib import Path


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "traceability" / "evidence_to_guardrail_trace_matrix.json"
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


class EvidenceToGuardrailTraceMatrixTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_processor_handoffs_link_to_requirement_nodes(self) -> None:
        self.assertEqual("evidence_to_guardrail_trace_matrix", self.fixture["fixtureKind"])
        handoffs = {item["processorHandoffId"]: item for item in self.fixture["processorHandoffs"]}
        self.assertEqual(2, len(handoffs))
        for handoff in handoffs.values():
            self.assertTrue(handoff["sourceEvidenceId"].startswith("src-"))
            self.assertTrue(handoff["canonicalDocumentId"].startswith("ppd-public-"))
            self.assertTrue(handoff["contentHashPlaceholder"].startswith("sha256:[PUBLIC_ARCHIVE_HASH_PLACEHOLDER_"))
            self.assertTrue(handoff["extractionBatchId"].startswith("extract-batch-"))

        for node in self.fixture["requirementNodes"]:
            self.assertTrue(node["requirementId"].startswith("req-"))
            self.assertTrue(set(node["processorHandoffIds"]).issubset(handoffs))
            self.assertIn(node["nodeType"], {"required_user_fact", "required_document_placeholder"})

    def test_trace_rows_connect_known_and_missing_facts_to_stop_gates(self) -> None:
        requirement_ids = {item["requirementId"] for item in self.fixture["requirementNodes"]}
        fact_ids = {item["factId"] for item in self.fixture["userFacts"]}
        missing_ids = {item["missingFactId"] for item in self.fixture["missingFacts"]}
        gate_ids = {item["gateId"] for item in self.fixture["stopGates"]}

        for fact in self.fixture["userFacts"]:
            self.assertIn(fact["requirementId"], requirement_ids)
            self.assertTrue(fact["redactedValue"].startswith("[REDACTED_"))
            self.assertEqual("user_document_store", fact["source"])

        for missing in self.fixture["missingFacts"]:
            self.assertIn(missing["requirementId"], requirement_ids)
            self.assertEqual("ask_user", missing["defaultOutcome"])
            self.assertTrue(missing["question"].endswith("?"))

        for row in self.fixture["traceRows"]:
            self.assertIn(row["requirementId"], requirement_ids)
            if row["userFactId"] is not None:
                self.assertIn(row["userFactId"], fact_ids)
            if row["missingFactId"] is not None:
                self.assertIn(row["missingFactId"], missing_ids)
            self.assertTrue(set(row["stopGateIds"]).issubset(gate_ids))

    def test_stop_gates_fail_closed_for_missing_and_exact_confirmation_requirements(self) -> None:
        missing_gate = next(item for item in self.fixture["stopGates"] if item["gateId"] == "gate-missing-required-fact")
        self.assertEqual("ask_user", missing_gate["defaultOutcome"])
        self.assertTrue(missing_gate["blocksOfficialAction"])
        self.assertIn("req-site-plan-document", missing_gate["blocksWhenRequirementIdsMissing"])

        exact_gate = next(item for item in self.fixture["stopGates"] if item["gateId"] == "gate-exact-confirmation-required")
        self.assertEqual("refuse", exact_gate["defaultOutcome"])
        self.assertTrue(exact_gate["requiresExactConfirmation"])
        self.assertFalse(exact_gate["exactConfirmationPresent"])
        self.assertTrue({"upload_official_document", "submit_application", "pay_fee", "certify_statement"}.issubset(exact_gate["blockedActions"]))

    def test_boundary_and_planner_remain_fixture_only(self) -> None:
        boundary = self.fixture["boundary"]
        self.assertTrue(boundary["fixtureOnly"])
        self.assertFalse(boundary["liveCrawlRequested"])
        self.assertFalse(boundary["liveDevhubAccess"])
        self.assertFalse(boundary["officialActionAllowed"])
        self.assertFalse(boundary["privateArtifactStored"])

        outcome = self.fixture["plannerOutcome"]
        self.assertTrue(outcome["mayUseKnownFactsForDraftPreview"])
        self.assertTrue(outcome["mustAskUserForMissingFacts"])
        self.assertFalse(outcome["mayPerformOfficialActions"])
        self.assertEqual("ask_user_for_missing_site_plan_metadata", outcome["nextAgentAction"])

        serialized = json.dumps(self.fixture, sort_keys=True).lower()
        for marker in FORBIDDEN_MARKERS:
            self.assertNotIn(marker, serialized)


if __name__ == "__main__":
    unittest.main()
