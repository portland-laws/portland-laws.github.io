from __future__ import annotations

import unittest

from ppd.daemon.malformed_python_diagnostics import (
    classify_syntax_first_retry_stop,
    malformed_python_signatures,
)


class MalformedPythonDiagnosticsTest(unittest.TestCase):
    def test_confidence_one_repeats_as_syntax_first_retry_stop(self) -> None:
        target = "Task checkbox-80: malformed Python syntax diagnostic"
        current = {
            "target_task": target,
            "validation_results": [
                {
                    "stderr": "failed py_compile: line 146 elif confidence 1: ^ SyntaxError: invalid syntax",
                }
            ],
        }
        prior = [
            {
                "target_task": target,
                "validation_results": [
                    {
                        "stderr": "failed py_compile: line 151 elif confidence 1.0: ^ SyntaxError: invalid syntax",
                    }
                ],
            }
        ]

        classification = classify_syntax_first_retry_stop(
            target_task=target,
            current_proposal=current,
            recent_failures=prior,
        )

        self.assertTrue(classification["syntax_first_retry_stop"])
        self.assertEqual(classification["repeat_count"], 2)
        self.assertIn("malformed-comparison:confidence-missing-operator", classification["signatures"])

    def test_numeric_return_followed_by_type_is_detected(self) -> None:
        signatures = malformed_python_signatures(
            {
                "validation_results": [
                    {
                        "stderr": "failed py_compile: line 259 return 0.0 list[str]: ^ SyntaxError: invalid syntax",
                    }
                ]
            }
        )

        self.assertIn("malformed-return:numeric-value-followed-by-type", signatures)

    def test_other_target_failures_do_not_trigger_stop(self) -> None:
        target = "Task checkbox-80: malformed Python syntax diagnostic"
        current = {
            "target_task": target,
            "validation_results": [
                {
                    "stderr": "failed py_compile: line 146 elif confidence 1: ^ SyntaxError: invalid syntax",
                }
            ],
        }
        prior = [
            {
                "target_task": "Task checkbox-81: different task",
                "validation_results": [
                    {
                        "stderr": "failed py_compile: line 151 elif confidence 1.0: ^ SyntaxError: invalid syntax",
                    }
                ],
            }
        ]

        classification = classify_syntax_first_retry_stop(
            target_task=target,
            current_proposal=current,
            recent_failures=prior,
        )

        self.assertFalse(classification["syntax_first_retry_stop"])
        self.assertEqual(classification["repeat_count"], 1)

    def test_plain_syntax_error_without_known_signature_does_not_match(self) -> None:
        classification = classify_syntax_first_retry_stop(
            target_task="Task checkbox-80: malformed Python syntax diagnostic",
            current_proposal={
                "validation_results": [
                    {
                        "stderr": "failed py_compile: line 85 return { ^ SyntaxError: '{' was never closed",
                    }
                ]
            },
            recent_failures=[],
        )

        self.assertFalse(classification["syntax_first_retry_stop"])
        self.assertEqual(classification["signatures"], [])


if __name__ == "__main__":
    unittest.main()
