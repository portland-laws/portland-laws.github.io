"""Tests for supervisor repair diagnostic fixtures."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from ppd.daemon.supervisor_diagnostics import (
    classify_repeated_python_syntax_failures,
    is_python_syntax_failure,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "supervisor" / "repeated_python_syntax_errors.json"


class SupervisorDiagnosticsTests(unittest.TestCase):
    def test_repeated_python_syntax_errors_recommend_smaller_file_sets(self) -> None:
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        diagnostic = classify_repeated_python_syntax_failures(fixture["proposals"])
        self.assertEqual(diagnostic.kind, fixture["expected"]["kind"])
        self.assertIn(fixture["expected"]["recommendedActionContains"], diagnostic.recommended_action)

    def test_non_validation_failures_do_not_count_as_python_syntax_failures(self) -> None:
        self.assertFalse(is_python_syntax_failure({"failure_kind": "llm", "errors": ["SyntaxError in prompt text"]}))


if __name__ == "__main__":
    unittest.main()
