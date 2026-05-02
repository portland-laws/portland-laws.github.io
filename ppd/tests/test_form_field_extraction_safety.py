from __future__ import annotations

import json
from pathlib import Path
import unittest

from ppd.extraction.form_field_fixture_validation import (
    assert_form_field_extraction_fixture_safe,
    validate_form_field_extraction_fixture,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "form_field_extraction"


class FormFieldExtractionSafetyTest(unittest.TestCase):
    def load_fixture(self, name: str) -> dict:
        with (FIXTURE_DIR / name).open(encoding="utf-8") as fixture_file:
            return json.load(fixture_file)

    def test_valid_fixture_uses_cited_required_fields_and_redacted_metadata_only(self) -> None:
        fixture = self.load_fixture("permit_request_form_fields.json")

        findings = validate_form_field_extraction_fixture(fixture)

        self.assertEqual([], findings)
        assert_form_field_extraction_fixture_safe(fixture)

    def test_rejects_uncited_required_fields_and_unsafe_payloads(self) -> None:
        fixture = self.load_fixture("unsafe_form_field_extraction_fixture.json")

        findings = validate_form_field_extraction_fixture(fixture)
        reasons = [finding.reason for finding in findings]

        self.assertIn("required fields must cite source evidence", reasons)
        self.assertIn("required field citation must reference source evidence", reasons)
        self.assertIn("raw PDF bodies are not allowed in form-field fixtures", reasons)
        self.assertIn("downloaded document bytes are not allowed in form-field fixtures", reasons)
        self.assertIn("private user values are not allowed in form-field fixtures", reasons)
        self.assertIn(
            "fixtures must not instruct agents to submit, certify, upload, pay, cancel, or schedule inspections",
            reasons,
        )


if __name__ == "__main__":
    unittest.main()
