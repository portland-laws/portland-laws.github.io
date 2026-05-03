"""Fixture-only regression coverage for daemon Python syntax preflight.

These tests preserve the PP&D repair boundary by compiling committed string
fixtures only. They do not import or modify DevHub implementation code, open
browser sessions, crawl public sources, or read private artifacts.
"""

from __future__ import annotations

import ast
import json
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "daemon" / "syntax_preflight_malformed_python_fragments.json"


class SyntaxPreflightMalformedFragmentTests(unittest.TestCase):
    def test_malformed_python_fragments_fail_parser_preflight(self) -> None:
        fixture = _load_fixture()
        self.assertEqual(fixture["schemaVersion"], 1)
        self.assertEqual(fixture["fixtureKind"], "syntax_preflight_malformed_python_fragments")

        fragment_ids = {fragment["id"] for fragment in fixture["fragments"]}
        self.assertIn("draft_readiness_if_confidence_none", fragment_ids)

        for fragment in fixture["fragments"]:
            with self.subTest(fragment=fragment["id"]):
                self.assertEqual(fragment["language"], "python")
                self.assertEqual(fragment["expectedFailureKind"], "syntax_preflight")

                with self.assertRaises(SyntaxError) as raised:
                    ast.parse(fragment["fragment"], filename=f"")

                message = str(raised.exception)
                expected_text = fragment["expectedMessageContains"]
                self.assertIn(expected_text, message)

    def test_fixture_contains_no_devhub_or_live_artifact_paths(self) -> None:
        fixture_text = FIXTURE_PATH.read_text(encoding="utf-8").lower()
        forbidden_markers = (
            "ppd/data/private",
            "storage_state",
            "auth_state",
            "trace.zip",
            "screenshots/",
            "downloads/",
            "devhub/session",
            "devhub/sessions",
            "raw_crawl",
            "crawl_output",
        )
        for marker in forbidden_markers:
            with self.subTest(marker=marker):
                self.assertNotIn(marker, fixture_text)


def _load_fixture() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
