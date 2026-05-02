from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "end_to_end"
    / "archival_logic_playwright_handoff_scenario.json"
)

SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
FORBIDDEN_ACTIONS = {
    "upload_official_document",
    "submit_application",
    "certify_statement",
    "pay_fee",
    "cancel_request",
    "schedule_inspection",
    "mfa",
    "captcha",
}
FORBIDDEN_MARKERS = (
    "ppd/data/private",
    "ppd/data/raw",
    "auth-state",
    "storage-state",
    "trace.zip",
    ".har",
    "cookie",
    "screenshot",
    "raw browser state",
)


class ArchivalLogicPlaywrightHandoffScenarioTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_scenario_is_fixture_only_and_links_archival_inputs(self) -> None:
        self.assertEqual("archival_logic_playwright_handoff_scenario", self.fixture["fixtureKind"])
        boundary = self.fixture["boundary"]
        self.assertTrue(boundary["fixtureOnly"])
        self.assertFalse(boundary["networkAccess"])
        self.assertFalse(boundary["liveBrowserStarted"])
        self.assertFalse(boundary["authenticatedAutomation"])
        self.assertFalse(boundary["rawBrowserStateStored"])
        self.assertFalse(boundary["officialDevhubActionsAllowed"])

        for evidence in self.fixture["archiveEvidence"]:
            self.assertTrue(evidence["sourceUrl"].startswith("https://www.portland.gov/ppd/"))
            self.assertTrue(evidence["archiveManifestId"])
            self.assertTrue(evidence["processorHandoffId"].startswith("handoff-ppd-"))
            self.assertTrue(evidence["canonicalDocumentId"].startswith("doc-ppd-"))
            self.assertRegex(evidence["contentHashPlaceholder"], SHA256_RE)
            self.assertTrue(evidence["citation"]["locator"])
            self.assertTrue(evidence["citation"]["paraphrase"])

    def test_requirement_guardrail_and_playwright_nodes_are_connected(self) -> None:
        node_ids = known_node_ids(self.fixture)
        evidence_ids = {item["evidenceId"] for item in self.fixture["archiveEvidence"]}

        for requirement in self.fixture["requirementNodes"]:
            self.assertTrue(set(requirement["sourceEvidenceIds"]).issubset(evidence_ids))
            self.assertIn("required(", requirement["formalPredicate"])
            self.assertIn("OBLIGATED", requirement["obligation"])

        for guardrail in self.fixture["guardrailNodes"]:
            self.assertTrue(set(guardrail["sourceEvidenceIds"]).issubset(evidence_ids))
            if guardrail["nodeType"] == "exact_confirmation_gate":
                self.assertEqual("refuse", guardrail["defaultOutcome"])
                self.assertTrue(FORBIDDEN_ACTIONS.issubset(set(guardrail["blocksActions"])))
                self.assertTrue(guardrail["requiresExactConfirmation"])
                self.assertFalse(guardrail["exactConfirmationPresent"])

        for action in self.fixture["playwrightDraftPlan"]["actions"]:
            self.assertIn(action["linkedRequirementNodeId"], node_ids)
            self.assertIn(action["linkedGuardrailNodeId"], node_ids)
            self.assertEqual("reversible_draft_edit", action["actionClass"])
            self.assertFalse(action["executesInFixture"])
            self.assertGreaterEqual(action["selector"]["confidence"], 0.9)
            self.assertTrue(action["afterValue"].startswith("[REDACTED_USER_SUPPLIED_"))

    def test_handoff_edges_reference_known_nodes_or_refused_action_ids(self) -> None:
        node_ids = known_node_ids(self.fixture)
        refused = set(self.fixture["refusedOfficialActions"])

        for edge in self.fixture["handoffEdges"]:
            self.assertIn(edge["from"], node_ids)
            self.assertIn(edge["to"], node_ids | refused)
            self.assertIn(
                edge["edgeType"],
                {
                    "evidence_supports_requirement",
                    "evidence_supports_guardrail",
                    "requirement_enables_reversible_preview",
                    "guardrail_blocks_official_action_by_default",
                },
            )

    def test_no_private_runtime_or_official_action_surface_is_allowed(self) -> None:
        serialized = json.dumps(self.fixture, sort_keys=True).lower()
        for marker in FORBIDDEN_MARKERS:
            self.assertNotIn(marker, serialized)
        self.assertTrue(FORBIDDEN_ACTIONS.issubset(set(self.fixture["refusedOfficialActions"])))
        self.assertEqual("preview_only", self.fixture["playwrightDraftPlan"]["mode"])


def known_node_ids(fixture: dict[str, Any]) -> set[str]:
    ids = {item["evidenceId"] for item in fixture["archiveEvidence"]}
    ids.update(item["nodeId"] for item in fixture["requirementNodes"])
    ids.update(item["nodeId"] for item in fixture["guardrailNodes"])
    ids.update(item["actionId"] for item in fixture["playwrightDraftPlan"]["actions"])
    return ids


if __name__ == "__main__":
    unittest.main()
