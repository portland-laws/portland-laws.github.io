import json
import unittest
from pathlib import Path

from ppd.formal_logic_guardrails import validate_guardrail_bundle


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "formal_logic_guardrails" / "bundles.json"


class FormalLogicGuardrailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def _case(self, name):
        for case in self.fixture["cases"]:
            if case["name"] == name:
                return case
        raise AssertionError(f"missing fixture case: {name}")

    def _codes_for(self, name):
        case = self._case(name)
        result = validate_guardrail_bundle(case["bundle"], case["plan"])
        return result.allowed, {failure.code for failure in result.failures}

    def test_current_cited_reversible_draft_is_allowed(self):
        allowed, codes = self._codes_for("safe_reversible_draft")
        self.assertTrue(allowed)
        self.assertEqual(set(), codes)

    def test_missing_citation_fails_closed(self):
        allowed, codes = self._codes_for("missing_citation")
        self.assertFalse(allowed)
        self.assertIn("missing_citation", codes)

    def test_stale_evidence_fails_closed(self):
        allowed, codes = self._codes_for("stale_evidence")
        self.assertFalse(allowed)
        self.assertIn("stale_evidence", codes)

    def test_private_value_requirement_fails_closed(self):
        allowed, codes = self._codes_for("private_value_required")
        self.assertFalse(allowed)
        self.assertIn("private_value_required", codes)

    def test_consequential_action_fails_closed(self):
        allowed, codes = self._codes_for("consequential_action")
        self.assertFalse(allowed)
        self.assertIn("consequential_action_blocked", codes)

    def test_financial_action_fails_closed(self):
        allowed, codes = self._codes_for("financial_action")
        self.assertFalse(allowed)
        self.assertIn("financial_action_blocked", codes)

    def test_unvalidated_bundle_fails_closed(self):
        allowed, codes = self._codes_for("unvalidated_bundle")
        self.assertFalse(allowed)
        self.assertIn("bundle_not_validated", codes)


if __name__ == "__main__":
    unittest.main()
