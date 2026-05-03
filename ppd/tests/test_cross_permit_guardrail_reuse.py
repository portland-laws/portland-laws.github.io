from __future__ import annotations

import json
import unittest
from pathlib import Path


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "guardrail_reuse"
    / "cross_permit_guardrail_reuse.json"
)

OFFICIAL_ACTIONS = {
    "submit_application",
    "upload_official_document",
    "certify_statement",
    "pay_fee",
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


class CrossPermitGuardrailReuseTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_shared_stop_gates_apply_to_both_permit_processes(self) -> None:
        self.assertEqual("cross_permit_guardrail_reuse", self.fixture["fixtureKind"])
        gate_ids = {gate["gateId"] for gate in self.fixture["commonStopGates"]}
        self.assertEqual(
            {"gate-missing-required-fact", "gate-exact-confirmation-for-official-action"},
            gate_ids,
        )
        for gate in self.fixture["commonStopGates"]:
            self.assertTrue(gate["reusableAcrossPermitTypes"])
            self.assertTrue(gate["blocksOfficialAction"])

        for binding in self.fixture["processBindings"]:
            self.assertEqual(gate_ids, set(binding["appliedStopGateIds"]))
            self.assertEqual(OFFICIAL_ACTIONS, set(binding["exactConfirmationActions"]))

    def test_process_specific_evidence_stays_bound_to_each_process(self) -> None:
        evidence = {item["sourceEvidenceId"]: item for item in self.fixture["sourceEvidence"]}
        self.assertEqual(2, len(self.fixture["processBindings"]))
        residential = next(
            item for item in self.fixture["processBindings"] if item["permitType"] == "residential_building_permit"
        )
        trade = next(
            item for item in self.fixture["processBindings"] if item["permitType"] == "trade_permit_with_plan_review"
        )

        self.assertTrue(all(source_id.startswith("src-residential") for source_id in residential["sourceEvidenceIds"]))
        self.assertTrue(all(source_id.startswith("src-trade") for source_id in trade["sourceEvidenceIds"]))
        self.assertTrue(set(residential["sourceEvidenceIds"]).isdisjoint(trade["sourceEvidenceIds"]))

        for binding in self.fixture["processBindings"]:
            for source_id in binding["sourceEvidenceIds"]:
                source = evidence[source_id]
                self.assertTrue(source["sourceUrl"].startswith("https://www.portland.gov/ppd/"))
                self.assertTrue(source["citation"]["locator"])
                self.assertTrue(source["citation"]["paraphrase"])

    def test_compiler_refuses_official_actions_without_exact_confirmation(self) -> None:
        outcome = self.fixture["guardrailCompilerOutcome"]
        self.assertTrue(outcome["sharedGateReuseAllowed"])
        self.assertFalse(outcome["processSpecificCitationMixingAllowed"])
        self.assertEqual("refuse_without_exact_confirmation", outcome["officialActionDefault"])
        self.assertEqual("ask_user_for_missing_process_specific_facts", outcome["nextAgentAction"])

    def test_fixture_is_offline_and_omits_private_artifacts(self) -> None:
        boundary = self.fixture["boundary"]
        self.assertTrue(boundary["fixtureOnly"])
        self.assertFalse(boundary["liveDevhubAccess"])
        self.assertFalse(boundary["browserLaunchRequested"])
        self.assertFalse(boundary["officialSubmissionAllowed"])
        self.assertFalse(boundary["privateArtifactStored"])

        serialized = json.dumps(self.fixture, sort_keys=True).lower()
        for marker in FORBIDDEN_MARKERS:
            self.assertNotIn(marker, serialized)


if __name__ == "__main__":
    unittest.main()
