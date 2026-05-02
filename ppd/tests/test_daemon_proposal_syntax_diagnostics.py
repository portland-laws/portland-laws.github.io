"""Tests for PP&D daemon proposal syntax diagnostics."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from ppd.daemon.proposal_syntax_diagnostics import (
    DIAGNOSTIC_KIND,
    MALFORMED_COMPARISON_SYNTAX,
    RETRY_SCOPE,
    classify_fixture_payload,
    classify_repeated_malformed_comparison_syntax,
    is_malformed_python_comparison_syntax,
)


class ProposalSyntaxDiagnosticsTests(unittest.TestCase):
    def fixture_path(self) -> Path:
        return Path(__file__).parent / "fixtures" / "daemon" / "repeated_malformed_comparison_syntax.json"

    def load_fixture(self) -> dict:
        with self.fixture_path().open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def test_fixture_classifies_same_task_repetition_as_retry_stop(self) -> None:
        payload = self.load_fixture()
        diagnostic = classify_fixture_payload(payload)
        expected = payload["expected"]

        self.assertEqual(DIAGNOSTIC_KIND, diagnostic["kind"])
        self.assertEqual(expected["kind"], diagnostic["kind"])
        self.assertEqual(MALFORMED_COMPARISON_SYNTAX, diagnostic["syntax_family"])
        self.assertEqual(expected["syntax_family"], diagnostic["syntax_family"])
        self.assertEqual(RETRY_SCOPE, diagnostic["retry_scope"])
        self.assertEqual(expected["retry_scope"], diagnostic["retry_scope"])
        self.assertTrue(diagnostic["should_stop_retry"])
        self.assertEqual(expected["matched_repetitions"], diagnostic["matched_repetitions"])
        self.assertEqual(expected["matched_fragments"], diagnostic["matched_fragments"])

    def test_other_tasks_do_not_count_toward_retry_stop(self) -> None:
        payload = self.load_fixture()
        diagnostic = classify_repeated_malformed_comparison_syntax(
            payload["failures"],
            "checkbox-79",
            minimum_repetitions=2,
        )

        self.assertFalse(diagnostic["should_stop_retry"])
        self.assertEqual(1, diagnostic["matched_repetitions"])

    def test_requires_syntax_error_marker(self) -> None:
        self.assertFalse(
            is_malformed_python_comparison_syntax(
                {
                    "task_id": "checkbox-80",
                    "validation": "Rejected by semantic validator near confidence 1",
                }
            )
        )


if __name__ == "__main__":
    unittest.main()
