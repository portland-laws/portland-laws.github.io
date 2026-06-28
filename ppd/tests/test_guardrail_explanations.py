from __future__ import annotations

import json
from pathlib import Path
import unittest

from ppd.logic.guardrail_explanations import render_guardrail_explanations


class GuardrailExplanationFixtureTest(unittest.TestCase):
    def setUp(self) -> None:
        fixture_path = Path(__file__).parent / "fixtures" / "guardrails" / "guardrail_explanation_fixture.json"
        self.fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        self.rendered = render_guardrail_explanations(self.fixture)

    def test_blocked_actions_are_cited_and_user_facing(self) -> None:
        blocked = self.rendered["blocked_actions"]
        self.assertEqual(2, len(blocked))
        self.assertIn("permit request submission", blocked[0]["explanation"])
        self.assertIn("requires attended user review", blocked[0]["explanation"])
        self.assertTrue(blocked[0]["citations"])
        self.assertIn("DevHub FAQs", blocked[0]["citations"][0])

    def test_missing_information_is_cited_and_actionable(self) -> None:
        missing = self.rendered["missing_information"]
        self.assertEqual(2, len(missing))
        self.assertIn("contractor license status", missing[0]["explanation"])
        self.assertIn("Please confirm", missing[0]["explanation"])
        self.assertTrue(missing[0]["citations"])

    def test_private_values_and_raw_authenticated_data_are_not_exposed(self) -> None:
        rendered_text = json.dumps(self.rendered, sort_keys=True)
        forbidden_fragments = [
            "PRIVATE-APP-4921",
            "123 Private Permit St",
            "PRIVATE-INVOICE-8842",
            "tok_private_8842",
            "PRIVATE-LIC-7711",
            "/home/user/private/plans.pdf",
            "Authenticated DevHub page showed",
            "Authenticated fee page contained",
            "Authenticated upload page listed",
        ]
        for fragment in forbidden_fragments:
            self.assertNotIn(fragment, rendered_text)

    def test_output_shape_is_stable_for_agents(self) -> None:
        self.assertEqual({"blocked_actions", "missing_information"}, set(self.rendered))
        for group in self.rendered.values():
            for explanation in group:
                self.assertEqual({"predicate_id", "explanation", "citations"}, set(explanation))
                self.assertIsInstance(explanation["predicate_id"], str)
                self.assertIsInstance(explanation["explanation"], str)
                self.assertIsInstance(explanation["citations"], list)


if __name__ == "__main__":
    unittest.main()
