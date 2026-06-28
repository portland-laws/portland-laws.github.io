from __future__ import annotations

import copy
import unittest
from pathlib import Path

from ppd.devhub.attended_evidence_validation import (
    assert_valid_attended_evidence_template,
    load_attended_evidence_template,
    validate_attended_evidence_template,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "devhub_attended_evidence"
VALID_TEMPLATE = FIXTURE_DIR / "valid_template.json"
INVALID_TEMPLATE = FIXTURE_DIR / "invalid_template.json"


class DevHubAttendedEvidenceValidationTest(unittest.TestCase):
    def test_valid_template_accepts_attended_redacted_evidence_shape(self) -> None:
        template = load_attended_evidence_template(VALID_TEMPLATE)

        result = validate_attended_evidence_template(template)

        self.assertTrue(result.ok, result.errors)
        self.assertEqual(result.errors, ())
        assert_valid_attended_evidence_template(template)

    def test_invalid_template_rejects_all_required_safety_failures(self) -> None:
        result = validate_attended_evidence_template(load_attended_evidence_template(INVALID_TEMPLATE))
        joined = "\n".join(result.errors)

        self.assertFalse(result.ok)
        self.assertIn("login must be attended by the user only", joined)
        self.assertIn("template must not claim login was automated", joined)
        self.assertIn("template must reject private values", joined)
        self.assertIn("template must include redaction attestation", joined)
        self.assertIn("template must include post-action hardening notes", joined)
        for field in ("auth_state", "cookies", "har_files", "screenshots", "storage_state"):
            self.assertIn(field, joined)
        for field in ("automated_login", "captcha_automation", "consequential_control_activation", "credential_capture", "mfa_automation"):
            self.assertIn(field, joined)

    def test_private_values_are_rejected_without_committing_private_fixture_data(self) -> None:
        template = copy.deepcopy(load_attended_evidence_template(VALID_TEMPLATE))
        template["evidence_fields"].append("operator contact person@example.test")

        result = validate_attended_evidence_template(template)

        self.assertFalse(result.ok)
        self.assertTrue(any("private value material" in error for error in result.errors))

    def test_missing_redaction_attestation_and_hardening_notes_are_rejected(self) -> None:
        template = copy.deepcopy(load_attended_evidence_template(VALID_TEMPLATE))
        template["redaction_attestation_present"] = False
        template["post_action_hardening_notes"] = ""

        result = validate_attended_evidence_template(template)

        self.assertFalse(result.ok)
        self.assertIn("template must include redaction attestation", result.errors)
        self.assertIn("template must include post-action hardening notes", result.errors)


if __name__ == "__main__":
    unittest.main()
