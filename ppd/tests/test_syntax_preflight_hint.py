from __future__ import annotations

import unittest

from ppd.daemon.syntax_preflight_hint import build_syntax_preflight_next_action_hint


class SyntaxPreflightHintTest(unittest.TestCase):
    def test_py_compile_failure_names_single_python_file_before_domain_retry(self) -> None:
        hint = build_syntax_preflight_next_action_hint(
            "ppd/scrapers/broken_page.py",
            "SyntaxError: invalid syntax (broken_page.py, line 7)",
        )

        self.assertIn("Before any domain retry", hint)
        self.assertIn("replace only one syntactically failing Python file", hint)
        self.assertIn("ppd/scrapers/broken_page.py", hint)
        self.assertIn("py_compile detail: SyntaxError: invalid syntax", hint)

    def test_py_compile_failure_allows_single_daemon_repair_file(self) -> None:
        hint = build_syntax_preflight_next_action_hint(
            "ppd/daemon/repair_syntax_failure.py",
            "SyntaxError: expected ':' (repair_syntax_failure.py, line 12)",
        )

        self.assertIn("Before any domain retry", hint)
        self.assertIn("replace only one daemon repair file", hint)
        self.assertIn("ppd/daemon/repair_syntax_failure.py", hint)
        self.assertNotIn("domain retry first", hint)


if __name__ == "__main__":
    unittest.main()
