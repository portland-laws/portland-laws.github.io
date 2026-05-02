"""Synthetic self-test for the repeated no-accepted-patch guardrail."""

from __future__ import annotations

import unittest

from repeated_no_patch_guardrail import build_recovery_prompt, should_apply_guardrail


class RepeatedNoPatchGuardrailTest(unittest.TestCase):
    def test_waits_until_four_consecutive_failed_rounds(self) -> None:
        recent_results = [
            {"applied": False, "failure_kind": "syntax_preflight", "changed_files": ["ppd/daemon/a.py"]},
            {"applied": False, "failure_kind": "empty_proposal", "changed_files": []},
            {"applied": False, "failure_kind": "validation_failed", "changed_files": ["ppd/daemon/b.py"]},
        ]

        self.assertFalse(should_apply_guardrail(recent_results))
        self.assertEqual(build_recovery_prompt("target", recent_results), "")

    def test_four_failed_rounds_require_narrow_fixture_first_json_replacements(self) -> None:
        recent_results = [
            {"applied": False, "failure_kind": "syntax_preflight", "changed_files": ["ppd/daemon/a.py"]},
            {"applied": False, "failure_kind": "syntax_preflight", "changed_files": ["ppd/daemon/a.py"]},
            {"applied": False, "failure_kind": "empty_proposal", "changed_files": []},
            {"applied": False, "failure_kind": "validation_failed", "changed_files": ["ppd/tests/test_a.py"]},
        ]

        prompt = build_recovery_prompt("Task checkbox-71", recent_results)

        self.assertIn("complete file replacements", prompt)
        self.assertIn("one narrow fixture-first file set", prompt)
        self.assertIn("exactly one JSON object", prompt)
        self.assertIn("Do not run or propose live DevHub sessions", prompt)
        self.assertIn("Do not perform broad contract rewrites", prompt)
        self.assertIn("Do not create private DevHub session files", prompt)
        self.assertIn("Do not", prompt)
        self.assertIn("synthetic self-test", prompt)

    def test_accepted_round_resets_consecutive_count(self) -> None:
        recent_results = [
            {"applied": False, "failure_kind": "syntax_preflight"},
            {"applied": True, "changed_files": ["ppd/daemon/ok.py"]},
            {"applied": False, "failure_kind": "syntax_preflight"},
            {"applied": False, "failure_kind": "syntax_preflight"},
            {"applied": False, "failure_kind": "syntax_preflight"},
        ]

        self.assertFalse(should_apply_guardrail(recent_results))


if __name__ == "__main__":
    unittest.main()
