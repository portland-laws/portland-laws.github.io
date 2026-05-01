import json
import unittest
from pathlib import Path

from ppd.logic import GuardrailCompilerError, compile_requirement_fixture


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "requirement_extraction"
    / "ppd_public_guidance_requirement_fixture.json"
)


class GuardrailCompilerTests(unittest.TestCase):
    def load_fixture(self):
        return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_compiles_fixture_requirements_to_guardrails(self):
        compiled = compile_requirement_fixture(self.load_fixture())

        self.assertEqual(compiled.fixture_id, "ppd_public_guidance_requirement_fixture_v1")
        self.assertEqual(len(compiled.guardrails), 7)
        self.assertFalse(compiled.validate())

        requirement_ids = {guardrail.requirement_id for guardrail in compiled.guardrails}
        self.assertIn("req-stop-before-submission-obligation", requirement_ids)
        self.assertIn("req-fee-payment-action-gate", requirement_ids)

    def test_preserves_source_support_map(self):
        compiled = compile_requirement_fixture(self.load_fixture())

        for guardrail in compiled.guardrails:
            self.assertIn(guardrail.requirement_id, compiled.support_map)
            evidence = compiled.support_map[guardrail.requirement_id]
            self.assertGreaterEqual(len(evidence), 1)
            self.assertTrue(evidence[0].source_url.startswith("https://www.portland.gov/"))
            self.assertTrue(evidence[0].anchor_id)

    def test_compiles_confirmation_gates_as_prohibitions(self):
        compiled = compile_requirement_fixture(self.load_fixture())
        by_id = {guardrail.requirement_id: guardrail for guardrail in compiled.guardrails}

        submission = by_id["req-stop-before-submission-obligation"]
        payment = by_id["req-fee-payment-action-gate"]

        self.assertIsNotNone(submission.deontic_rule)
        self.assertIsNotNone(payment.deontic_rule)
        self.assertEqual(submission.deontic_rule.modality, "obligated")
        self.assertEqual(payment.deontic_rule.modality, "prohibited_without_confirmation")
        self.assertEqual(payment.temporal_rule.relation, "before")
        self.assertEqual(payment.temporal_rule.trigger, "pay_fee")

    def test_rejects_missing_evidence(self):
        fixture = self.load_fixture()
        fixture["expected_requirements"][0]["evidence"] = []

        with self.assertRaises(GuardrailCompilerError):
            compile_requirement_fixture(fixture)


if __name__ == "__main__":
    unittest.main()
