import json
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "formal_logic_guardrail_bundle"
    / "archived_single_pdf_requirement_bundle.json"
)


class FixtureOnlyFormalLogicGuardrailBundleTests(unittest.TestCase):
    def load_fixture(self) -> dict[str, Any]:
        return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_fixture_is_offline_public_and_non_mutating(self) -> None:
        fixture = self.load_fixture()
        policy = fixture["source_policy"]

        self.assertTrue(policy["fixture_only"])
        self.assertFalse(policy["live_crawl_required"])
        self.assertFalse(policy["authenticated_session_required"])
        self.assertFalse(policy["contains_private_user_data"])
        self.assertFalse(policy["mutates_active_guardrails"])
        self.assertEqual(fixture["privacy_classification"], "public_redacted_fixture")

    def test_requirement_set_translates_to_core_formal_logic_categories(self) -> None:
        fixture = self.load_fixture()
        requirements = fixture["archived_requirement_set"]["requirements"]
        requirement_types = {requirement["requirement_type"] for requirement in requirements}
        bundle = fixture["guardrail_bundle"]

        self.assertIn("obligation", requirement_types)
        self.assertIn("precondition", requirement_types)
        self.assertIn("action_gate", requirement_types)
        self.assertGreaterEqual(len(bundle["deterministic_predicates"]), 3)
        self.assertGreaterEqual(len(bundle["deontic_rules"]), 5)
        self.assertGreaterEqual(len(bundle["temporal_rules"]), 2)
        self.assertGreaterEqual(len(bundle["prerequisite_predicates"]), 2)
        self.assertGreaterEqual(len(bundle["stop_gate_predicates"]), 2)
        self.assertGreaterEqual(len(bundle["reversible_action_predicates"]), 3)
        self.assertGreaterEqual(len(bundle["exact_confirmation_predicates"]), 2)

    def test_all_requirements_and_rules_are_cited_to_archived_evidence(self) -> None:
        fixture = self.load_fixture()
        requirement_set = fixture["archived_requirement_set"]
        evidence_ids = set(requirement_set["source_evidence_ids"])
        requirement_ids = {requirement["requirement_id"] for requirement in requirement_set["requirements"]}

        for requirement in requirement_set["requirements"]:
            self.assertTrue(requirement["source_evidence_ids"])
            self.assertTrue(set(requirement["source_evidence_ids"]).issubset(evidence_ids))

        for rule in fixture["guardrail_bundle"]["deontic_rules"]:
            self.assertIn(rule["requirement_id"], requirement_ids)

        self.assertEqual(set(fixture["guardrail_bundle"]["source_evidence_ids"]), evidence_ids)

    def test_stop_gates_require_exact_confirmation_and_default_to_blocked(self) -> None:
        fixture = self.load_fixture()
        bundle = fixture["guardrail_bundle"]
        confirmations = {
            confirmation["predicate_id"]: confirmation
            for confirmation in bundle["exact_confirmation_predicates"]
        }

        for stop_gate in bundle["stop_gate_predicates"]:
            self.assertEqual(stop_gate["default_decision"], "blocked")
            confirmation_id = stop_gate["required_confirmation_predicate_id"]
            self.assertIn(confirmation_id, confirmations)
            confirmation = confirmations[confirmation_id]
            self.assertEqual(confirmation["confirmation_scope"], "one_action_one_case")
            self.assertTrue(confirmation["expires_after_action"])
            self.assertIn("now", confirmation["required_user_phrase_template"].lower())

    def test_reversible_actions_cannot_upload_submit_or_persist_private_paths(self) -> None:
        fixture = self.load_fixture()
        reversible_actions = fixture["guardrail_bundle"]["reversible_action_predicates"]

        for action in reversible_actions:
            self.assertEqual(action["classification"], "reversible_draft")
            self.assertTrue(action["allowed_without_confirmation"])
            self.assertNotIn(action["action"], {"official_upload", "submit_application", "submit_payment"})

        by_action = {action["action"]: action for action in reversible_actions}
        self.assertTrue(by_action["inventory_local_document_metadata"]["must_not_persist_private_paths"])
        self.assertTrue(by_action["draft_devhub_field_mapping"]["must_not_submit"])
        self.assertTrue(by_action["render_local_pdf_preview"]["must_not_upload"])


if __name__ == "__main__":
    unittest.main()
