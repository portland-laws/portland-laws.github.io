from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pypdf import PdfReader
from reportlab.pdfgen import canvas

from ppd.pdf.draft_fill import PdfDraftFillRequest, fill_pdf_draft


class PdfDraftFillTest(unittest.TestCase):
    def test_real_pdf_draft_fill_writes_local_preview_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            source_pdf = Path(tempdir) / "source.pdf"
            output_pdf = Path(tempdir) / "filled.pdf"
            _write_form_pdf(source_pdf)

            result = fill_pdf_draft(
                PdfDraftFillRequest(
                    input_pdf=source_pdf,
                    output_pdf=output_pdf,
                    field_values={
                        "project_address": "1120 SW 5th Ave",
                        "description_of_work": "Interior alteration",
                    },
                    metadata={"/Title": "PPD draft preview"},
                )
            )

            reader = PdfReader(str(output_pdf))
            fields = {
                str(annotation.get_object().get("/T")): str(annotation.get_object().get("/V"))
                for page in reader.pages
                for annotation in page.get("/Annots", ())
            }
            output_exists = output_pdf.exists()

        self.assertTrue(result.ok)
        self.assertTrue(output_exists)
        self.assertEqual(("description_of_work", "project_address"), result.filled_fields)
        self.assertFalse(result.official_upload_performed)
        self.assertFalse(result.official_submission_performed)
        self.assertEqual("1120 SW 5th Ave", fields["project_address"])
        self.assertEqual("Interior alteration", fields["description_of_work"])

    def test_pdf_draft_fill_rejects_private_or_raw_output_path(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            source_pdf = Path(tempdir) / "source.pdf"
            _write_form_pdf(source_pdf)
            result = fill_pdf_draft(
                PdfDraftFillRequest(
                    input_pdf=source_pdf,
                    output_pdf=Path(tempdir) / "raw" / "filled.pdf",
                    field_values={"project_address": "1120 SW 5th Ave"},
                )
            )

        self.assertFalse(result.ok)
        self.assertEqual("refused", result.status)
        self.assertTrue(any("private, raw" in error for error in result.errors))


def _write_form_pdf(path: Path) -> None:
    packet = canvas.Canvas(str(path))
    packet.drawString(72, 740, "Project address")
    packet.acroForm.textfield(
        name="project_address",
        x=72,
        y=710,
        width=240,
        height=24,
        borderWidth=1,
    )
    packet.drawString(72, 670, "Description of work")
    packet.acroForm.textfield(
        name="description_of_work",
        x=72,
        y=640,
        width=300,
        height=24,
        borderWidth=1,
    )
    packet.save()


if __name__ == "__main__":
    unittest.main()
