"""Validate the formal-logic planner guardrail bundle fixture.

The fixture is intentionally synthetic and redacted. It links one extracted
PP&D requirement, one missing user fact, one stop gate, and one reversible
Playwright draft-preview action without launching a browser or touching DevHub.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "formal_logic"
    / "planner_guardrail_bundle.json"
)

FORBIDDEN_PLAYWRIGHT_ACTIONS = {
    "upload_official_document",
    "submit_application",
    "certify_statement",
    "pay_fee",
    "cancel_request",
    "schedule_inspection",
    "mfa",
    "captcha",
    "account_creation",
    "password_recovery",
}


class FormalLogicPlannerGuardrailBundleTest(unittest.TestCase):
    def load_fixture(self) -> dict[str, Any]:
        with FIXTURE_PATH.open(encoding="utf-8") as handle:
            data = json.load(handle)
        self.assertIsInstance(data, dict)
        return data

    def test_bundle_maps_requirement_fact_gate_and_draft_action(self) -> None:
        data = self.load_fixture()

        requirement = data["extractedRequirement"]
        missing_fact = data["missingUserFact"]
        stop_gate = data["stopGate"]
        action = data["playwrightDraftAction"]
        evidence_ids = {item["id"] for item in data["sourceEvidence"]}

        self.assertEqual(requirement["requirementId"], "req-single-pdf-process-address")
        self.assertEqual(missing_fact["linkedRequirementId"], requirement["requirementId"])
        self.assertEqual(action["linkedRequirementId"], requirement["requirementId"])
        self.assertEqual(action["linkedMissingFactId"], missing_fact["factId"])

        self.assertIsNone(missing_fact["knownValue"])
        self.assertEqual(stop_gate["defaultDecision"], "stop")
        self.assertTrue(stop_gate["requiresExactUserConfirmation"])
        self.assertFalse(stop_gate["exactUserConfirmationPresent"])

        self.assertEqual(action["actionClass"], "reversible_draft_edit")
        self.assertEqual(action["mode"], "preview_only")
        self.assertFalse(action["executesInFixture"])
        self.assertFalse(action["forbiddenAction"])
        self.assertEqual(action["beforeValue"], "[REDACTED_EMPTY]")
        self.assertEqual(action["afterValue"], "[REDACTED_USER_SUPPLIED_ADDRESS]")
        self.assertNotIn(action["actionId"], FORBIDDEN_PLAYWRIGHT_ACTIONS)

        selector_basis = action["selectorBasis"]
        self.assertEqual(selector_basis["role"], "textbox")
        self.assertEqual(selector_basis["accessibleName"], "Project site address")
        self.assertEqual(selector_basis["labelText"], "Project site address")
        self.assertEqual(selector_basis["nearbyHeading"], "Project information")

        for key in ("evidenceIds",):
            self.assertTrue(set(requirement[key]).issubset(evidence_ids))
            self.assertTrue(set(missing_fact[key]).issubset(evidence_ids))
            self.assertTrue(set(stop_gate[key]).issubset(evidence_ids))
            self.assertTrue(set(action[key]).issubset(evidence_ids))

    def test_formal_logic_rules_are_agent_guardrails(self) -> None:
        data = self.load_fixture()
        logic_bundle = data["formalLogicPlannerBundle"]

        self.assertEqual(logic_bundle["bundleType"], "agent_guardrail_bundle")
        self.assertIn("missing_user_fact(project.site_address)", logic_bundle["predicate"])
        self.assertIn("OBLIGATED(agent, ask_user", logic_bundle["deonticRule"])
        self.assertIn("PROHIBITED(agent, submit_application", logic_bundle["stopRule"])
        self.assertIn("PERMITTED(agent, preview_fill", logic_bundle["draftPermission"])
        self.assertIn("stop_before_consequential_actions", logic_bundle["plannerOutcome"])

    def test_stop_gate_blocks_forbidden_action_classes_without_confirmation(self) -> None:
        data = self.load_fixture()
        stop_gate = data["stopGate"]

        self.assertIn("consequential", stop_gate["blockedActionClasses"])
        self.assertIn("financial", stop_gate["blockedActionClasses"])
        self.assertTrue(FORBIDDEN_PLAYWRIGHT_ACTIONS.intersection(stop_gate["blockedActions"]))
        self.assertFalse(stop_gate["exactUserConfirmationPresent"])


if __name__ == "__main__":
    unittest.main()
