from __future__ import annotations

import unittest

from ppd.daemon.syntax_retry_guidance import (
    build_syntax_retry_guidance,
    has_syntax_failure,
    render_syntax_retry_prompt,
)


class SyntaxRetryGuidanceTest(unittest.TestCase):
    def test_detects_python_syntax_preflight_failure(self) -> None:
        errors = [
            "Syntax preflight failed; python3 -m py_compile ppd/tests/example.py: SyntaxError: unterminated string literal",
        ]

        self.assertTrue(has_syntax_failure(errors))
        guidance = build_syntax_retry_guidance(errors)

        self.assertTrue(guidance.should_narrow)
        self.assertEqual(guidance.max_files, 2)
        self.assertIn("python3 -m py_compile ", guidance.required_preflight)

    def test_detects_typescript_parse_failures(self) -> None:
        for marker in ("TS1005", "TS1109", "TS1128"):
            with self.subTest(marker=marker):
                self.assertTrue(has_syntax_failure([f"TypeScript failed with {marker}"]))

    def test_non_syntax_validation_does_not_force_syntax_retry(self) -> None:
        guidance = build_syntax_retry_guidance(["Validation failed; file edits were rolled back."])

        self.assertFalse(guidance.should_narrow)
        self.assertEqual(guidance.required_preflight, ())
        self.assertEqual(guidance.prompt_bullets, ())

    def test_rendered_prompt_blocks_broad_or_live_retry_scope(self) -> None:
        prompt = render_syntax_retry_prompt(["py_compile failed with invalid syntax"])

        self.assertIn("Maximum replacement files: 2", prompt)
        self.assertIn("complete file replacements", prompt)
        self.assertIn("Do not rewrite broad fixture contracts", prompt)
        self.assertIn("Do not launch Playwright", prompt)
        self.assertIn("touch live DevHub", prompt)
        self.assertIn("automate MFA", prompt)
        self.assertIn("automate CAPTCHA", prompt)


if __name__ == "__main__":
    unittest.main()
