from __future__ import annotations

import unittest

from ppd.daemon.parser_clean_diagnostics import build_parser_clean_diagnostic


class ParserCleanDiagnosticTest(unittest.TestCase):
    def test_failure_mapping_accepts_raw_response_sequence(self) -> None:
        raw = "validation failed\nnot json\nval" * 20

        diagnostic = build_parser_clean_diagnostic(
            target_task="checkbox-196",
            raw_response=[raw, raw, raw],
            error="LLM response did not contain a JSON object",
        )

        self.assertEqual(diagnostic["target_task"], "checkbox-196")
        self.assertEqual(diagnostic["failure_kind"], "non_json_llm_output")
        self.assertIn("attempts=3", diagnostic["compact_raw_response_summary"])
        self.assertIn("repeated=true", diagnostic["compact_raw_response_summary"])
        self.assertIn("sha256=", diagnostic["compact_raw_response_summary"])
        self.assertNotIn(raw, diagnostic["compact_raw_response_summary"])
        self.assertLess(len(diagnostic["compact_raw_response_summary"]), len(raw))
        self.assertIn("JSON-only", diagnostic["next_action_hint"])

    def test_single_empty_response_is_compact(self) -> None:
        diagnostic = build_parser_clean_diagnostic(
            target_task="checkbox-196",
            raw_response="",
            error="parse error",
        )

        self.assertEqual(diagnostic["failure_kind"], "non_json_llm_output")
        self.assertIn("attempts=1", diagnostic["compact_raw_response_summary"])
        self.assertIn("snippet=''", diagnostic["compact_raw_response_summary"])


if __name__ == "__main__":
    unittest.main()
