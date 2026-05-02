"""Tests for the checkbox-122 diagnostic validation fixture."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from ppd.daemon.checkbox_122_diagnostic_validation import (
    validate_checkbox_122_diagnostic,
)


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "daemon"
    / "checkbox_122_diagnostic.json"
)


class Checkbox122DiagnosticValidationTest(unittest.TestCase):
    def load_fixture(self) -> dict[str, object]:
        with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
            loaded = json.load(fixture_file)
        self.assertIsInstance(loaded, dict)
        return loaded

    def test_checkbox_122_diagnostic_reports_required_recovery_shape(self) -> None:
        fixture = self.load_fixture()

        errors = validate_checkbox_122_diagnostic(fixture)

        self.assertEqual([], errors)

    def test_checkbox_122_diagnostic_rejects_public_frontier_checkpoint_implementation(self) -> None:
        fixture = self.load_fixture()
        fixture["implementsPublicCrawlFrontierCheckpoint"] = True

        errors = validate_checkbox_122_diagnostic(fixture)

        self.assertIn("implementsPublicCrawlFrontierCheckpoint must be false", errors)

    def test_checkbox_122_diagnostic_rejects_broad_allowed_retry(self) -> None:
        fixture = self.load_fixture()
        fixture["allowedRetryShape"] = {
            "kind": "broad_rewrite",
            "maximumFiles": 4,
            "allowedScope": ["ppd/"],
        }

        errors = validate_checkbox_122_diagnostic(fixture)

        self.assertIn("allowedRetryShape.kind must be one_file_retry", errors)
        self.assertIn("allowedRetryShape.maximumFiles must be 1", errors)


if __name__ == "__main__":
    unittest.main()
