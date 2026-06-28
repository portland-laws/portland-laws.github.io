from pathlib import Path

import pytest

from ppd.file_preparation_compliance import (
    SyntheticDocumentMetadata,
    assert_metadata_compliant,
    evaluate_metadata,
    load_metadata_fixture,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "file_preparation" / "synthetic_document_metadata.json"


def test_fixture_metadata_is_compliant() -> None:
    records = load_metadata_fixture(FIXTURE_PATH)

    assert len(records) == 2
    assert evaluate_metadata(records) == []
    assert_metadata_compliant(records)


def test_downloaded_or_staged_metadata_is_rejected() -> None:
    records = [
        SyntheticDocumentMetadata(
            document_id="synthetic-bad-001",
            title="Bad synthetic placeholder",
            media_type="application/pdf",
            synthetic=True,
            downloaded=True,
            upload_staging=True,
            raw_pdf_persisted=True,
        )
    ]

    codes = {finding.code for finding in evaluate_metadata(records)}

    assert codes == {"downloaded_document", "raw_pdf_persisted", "upload_staging"}
    with pytest.raises(ValueError):
        assert_metadata_compliant(records)


def test_private_or_non_synthetic_metadata_is_rejected() -> None:
    records = [
        SyntheticDocumentMetadata(
            document_id="real-private-001",
            title="Private record",
            media_type="application/pdf",
            synthetic=False,
            private=True,
        )
    ]

    codes = {finding.code for finding in evaluate_metadata(records)}

    assert codes == {"not_synthetic", "private_metadata"}
