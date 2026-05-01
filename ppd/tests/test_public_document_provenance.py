"""Fixture tests for public document provenance validation."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from ppd.contracts.public_document_provenance import (
    assert_public_document_provenance,
    validate_public_document_provenance,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "public_document_provenance"


class PublicDocumentProvenanceTest(unittest.TestCase):
    def test_accepts_html_and_pdf_records_tied_to_source_index(self) -> None:
        fixture = _load_fixture("valid_public_document_provenance.json")

        findings = validate_public_document_provenance(
            fixture["normalized_documents"],
            fixture["source_index_records"],
        )

        self.assertEqual([], findings)
        assert_public_document_provenance(
            fixture["normalized_documents"],
            fixture["source_index_records"],
        )

    def test_rejects_missing_and_mismatched_provenance(self) -> None:
        fixture = _load_fixture("invalid_public_document_provenance.json")

        findings = validate_public_document_provenance(
            fixture["normalized_documents"],
            fixture["source_index_records"],
        )
        finding_reasons = {finding.reason for finding in findings}

        self.assertIn("normalized document canonical URL must match source-index canonical URL", finding_reasons)
        self.assertIn("normalized document retrieval timestamp must match source-index timestamp", finding_reasons)
        self.assertIn("normalized document checksum must match source-index content hash", finding_reasons)
        self.assertIn("source-index entry 'missing-source-index-entry' was not found", finding_reasons)
        self.assertIn("normalized document must include retrieval timestamp", finding_reasons)

        with self.assertRaises(ValueError):
            assert_public_document_provenance(
                fixture["normalized_documents"],
                fixture["source_index_records"],
            )


def _load_fixture(name: str) -> dict[str, object]:
    with (FIXTURE_DIR / name).open("r", encoding="utf-8") as fixture_file:
        loaded = json.load(fixture_file)
    if not isinstance(loaded, dict):
        raise TypeError(f"fixture {name} must contain a JSON object")
    return loaded


if __name__ == "__main__":
    unittest.main()
