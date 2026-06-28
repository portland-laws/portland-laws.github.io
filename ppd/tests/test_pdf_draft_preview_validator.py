from __future__ import annotations

from pathlib import Path
import unittest

from ppd.pdf.draft_preview_validator import validate_pdf_draft_preview


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "pdf_draft_preview"
PDF_FIXTURE = FIXTURE_DIR / "synthetic_permit_draft.pdf"
FORM_FIXTURE = FIXTURE_DIR / "synthetic_permit_draft_form.json"


class DraftPreviewValidatorTest(unittest.TestCase):
    def test_accepts_known_synthetic_draft_fields(self) -> None:
        result = validate_pdf_draft_preview(
            PDF_FIXTURE,
            FORM_FIXTURE,
            {
                "project_address": "1234 SW Test Ave",
                "permit_type": "Residential Alteration",
                "owner_occupied": True,
                "work_start_date": "2026-06-01",
            },
        )

        self.assertTrue(result.ok, result.errors)
        self.assertEqual(result.document_id, "synthetic-ppd-permit-draft")
        self.assertEqual(result.errors, ())
        self.assertEqual(len(result.field_previews), 4)

    def test_rejects_unknown_fields(self) -> None:
        result = validate_pdf_draft_preview(
            PDF_FIXTURE,
            FORM_FIXTURE,
            {"unlisted_private_field": "value"},
        )

        self.assertFalse(result.ok)
        self.assertIn("unknown draft field: unlisted_private_field", result.errors)

    def test_rejects_consequential_fixture_fields(self) -> None:
        result = validate_pdf_draft_preview(
            PDF_FIXTURE,
            FORM_FIXTURE,
            {"applicant_signature": "Synthetic Person"},
        )

        self.assertFalse(result.ok)
        self.assertIn("field is not draftable in local preview: applicant_signature", result.errors)

    def test_rejects_invalid_choice_and_date_values(self) -> None:
        result = validate_pdf_draft_preview(
            PDF_FIXTURE,
            FORM_FIXTURE,
            {
                "permit_type": "Unsupported Permit",
                "work_start_date": "06/01/2026",
            },
        )

        self.assertFalse(result.ok)
        self.assertIn("choice field permit_type received unsupported option: Unsupported Permit", result.errors)
        self.assertIn("date field work_start_date requires YYYY-MM-DD", result.errors)


if __name__ == "__main__":
    unittest.main()
