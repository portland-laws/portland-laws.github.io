import json
import unittest
from pathlib import Path

from ppd.contracts.pdf_metadata import (
    PdfCheckboxHint,
    PdfFeeTableHint,
    PdfFieldKind,
    PdfFormField,
    PdfNormalizedDocumentMetadata,
    PdfPageText,
    PdfSignatureHint,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "pdf_normalized_document_metadata.json"


def build_metadata(item: dict) -> PdfNormalizedDocumentMetadata:
    return PdfNormalizedDocumentMetadata(
        document_id=item["documentId"],
        source_url=item["sourceUrl"],
        canonical_url=item["canonicalUrl"],
        title=item["title"],
        page_count=int(item["pageCount"]),
        captured_at=item["capturedAt"],
        extraction_mode=item["extractionMode"],
        page_text=tuple(
            PdfPageText(
                id=page["id"],
                page_number=int(page["pageNumber"]),
                text=page["text"],
                text_hash=page["textHash"],
            )
            for page in item["pageText"]
        ),
        form_fields=tuple(
            PdfFormField(
                id=field["id"],
                label=field["label"],
                kind=PdfFieldKind(field["kind"]),
                page_number=int(field["pageNumber"]),
                required=bool(field["required"]),
                evidence_text=field["evidenceText"],
                options=tuple(field.get("options", ())),
            )
            for field in item["formFields"]
        ),
        checkbox_hints=tuple(
            PdfCheckboxHint(
                id=hint["id"],
                label=hint["label"],
                page_number=int(hint["pageNumber"]),
                checked_by_default=bool(hint.get("checkedByDefault", False)),
                evidence_text=hint["evidenceText"],
            )
            for hint in item["checkboxHints"]
        ),
        signature_hints=tuple(
            PdfSignatureHint(
                id=hint["id"],
                label=hint["label"],
                page_number=int(hint["pageNumber"]),
                required=bool(hint["required"]),
                signer_role=hint["signerRole"],
                evidence_text=hint["evidenceText"],
            )
            for hint in item["signatureHints"]
        ),
        fee_table_hints=tuple(
            PdfFeeTableHint(
                id=hint["id"],
                page_number=int(hint["pageNumber"]),
                caption=hint["caption"],
                headers=tuple(hint["headers"]),
                row_count=int(hint["rowCount"]),
                evidence_text=hint["evidenceText"],
            )
            for hint in item["feeTableHints"]
        ),
        warnings=tuple(item["warnings"]),
        live_download_performed=bool(item["liveDownloadPerformed"]),
    )


class PdfNormalizedDocumentMetadataTests(unittest.TestCase):
    def load_fixture(self) -> dict:
        return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_pdf_metadata_fixture_validates(self) -> None:
        fixture = self.load_fixture()
        documents = [build_metadata(item) for item in fixture["documents"]]
        self.assertGreaterEqual(len(documents), 1)
        for document in documents:
            self.assertFalse(document.validate())
            self.assertFalse(document.live_download_performed)

    def test_fixture_covers_pdf_extraction_hints(self) -> None:
        document = build_metadata(self.load_fixture()["documents"][0])
        self.assertGreaterEqual(len(document.page_text), 1)
        self.assertGreaterEqual(len(document.form_fields), 1)
        self.assertGreaterEqual(len(document.checkbox_hints), 1)
        self.assertGreaterEqual(len(document.signature_hints), 1)
        self.assertGreaterEqual(len(document.fee_table_hints), 1)


if __name__ == "__main__":
    unittest.main()
