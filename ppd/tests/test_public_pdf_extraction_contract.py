from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "public_pdf_extraction"
    / "residential_building_permit_application_extract.json"
)


class PublicPdfExtractionContractTest(unittest.TestCase):
    def load_fixture(self) -> dict[str, Any]:
        with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
            data = json.load(fixture_file)
        self.assertIsInstance(data, dict)
        return data

    def test_fixture_records_public_pdf_extraction_contract(self) -> None:
        data = self.load_fixture()

        self.assertEqual(data["schemaVersion"], 1)
        self.assertTrue(data["fixtureOnly"])
        self.assertIn("public_pdf_extraction", str(FIXTURE_PATH))

        source = data["source"]
        parsed_source_url = urlparse(source["sourceUrl"])
        self.assertEqual(parsed_source_url.scheme, "https")
        self.assertEqual(parsed_source_url.netloc, "www.portland.gov")
        self.assertEqual(source["access"], "public")
        self.assertEqual(source["retrievalMode"], "metadata_and_text_snippet_fixture_only")

        metadata = data["documentMetadata"]
        self.assertEqual(metadata["contentType"], "application/pdf")
        self.assertIsInstance(metadata["pageCount"], int)
        self.assertGreater(metadata["pageCount"], 0)
        self.assertFalse(metadata["rawPdfBytesStored"])
        self.assertFalse(metadata["downloadedDocumentStored"])
        self.assertIsNone(metadata["localDocumentPath"])

        self.assertGreaterEqual(len(data["pageAnchors"]), 1)
        self.assertGreaterEqual(len(data["requiredDocumentLabels"]), 1)
        self.assertGreaterEqual(len(data["signatureOrAcknowledgmentMarkers"]), 1)
        self.assertGreaterEqual(len(data["extractedTextSnippets"]), 1)

    def test_anchors_labels_markers_and_snippets_are_cross_referenced(self) -> None:
        data = self.load_fixture()
        page_count = data["documentMetadata"]["pageCount"]
        anchor_ids = {anchor["anchorId"] for anchor in data["pageAnchors"]}
        snippet_ids = {snippet["snippetId"] for snippet in data["extractedTextSnippets"]}

        self.assertEqual(len(anchor_ids), len(data["pageAnchors"]))
        self.assertEqual(len(snippet_ids), len(data["extractedTextSnippets"]))

        for anchor in data["pageAnchors"]:
            self.assertIsInstance(anchor["pageNumber"], int)
            self.assertGreaterEqual(anchor["pageNumber"], 1)
            self.assertLessEqual(anchor["pageNumber"], page_count)
            self.assertTrue(anchor["label"].strip())

        for label in data["requiredDocumentLabels"]:
            self.assertIn(label["anchorId"], anchor_ids)
            self.assertIn(label["snippetEvidenceId"], snippet_ids)
            self.assertTrue(label["label"].strip())
            self.assertGreaterEqual(label["pageNumber"], 1)
            self.assertLessEqual(label["pageNumber"], page_count)

        marker_types = set()
        for marker in data["signatureOrAcknowledgmentMarkers"]:
            marker_types.add(marker["markerType"])
            self.assertIn(marker["markerType"], {"signature", "acknowledgment"})
            self.assertIn(marker["anchorId"], anchor_ids)
            self.assertIn(marker["snippetEvidenceId"], snippet_ids)
            self.assertGreaterEqual(marker["pageNumber"], 1)
            self.assertLessEqual(marker["pageNumber"], page_count)

        self.assertIn("signature", marker_types)
        self.assertIn("acknowledgment", marker_types)

        for snippet in data["extractedTextSnippets"]:
            self.assertIn(snippet["anchorId"], anchor_ids)
            self.assertGreaterEqual(snippet["pageNumber"], 1)
            self.assertLessEqual(snippet["pageNumber"], page_count)
            self.assertTrue(snippet["text"].strip())
            self.assertLessEqual(len(snippet["text"]), 280)

    def test_fixture_contains_no_raw_pdf_bytes_or_private_artifact_paths(self) -> None:
        data = self.load_fixture()
        storage_policy = data["storagePolicy"]

        self.assertFalse(storage_policy["storesRawPdfBytes"])
        self.assertFalse(storage_policy["storesDownloadedDocument"])
        self.assertTrue(storage_policy["storesExtractedTextOnly"])
        self.assertFalse(storage_policy["containsPrivateDevhubData"])
        self.assertFalse(storage_policy["containsAuthenticationState"])
        self.assertFalse(storage_policy["containsBrowserTrace"])

        forbidden_keys = {
            "authState",
            "browserTrace",
            "credentials",
            "downloadPath",
            "localPdfPath",
            "password",
            "pdfBytes",
            "privateSession",
            "rawBytes",
            "rawPdf",
            "sessionState",
            "tracePath",
        }
        forbidden_fragments = (
            "/data/private/",
            "/data/raw/",
            "/devhub/private/",
            "/ipfs_datasets_py/.daemon/",
            "/private/",
            "/raw/",
            "base64,",
            "browser-trace",
            "storage_state",
            "trace.zip",
        )

        def walk(value: Any, path: str = "root") -> None:
            if isinstance(value, dict):
                for key, child in value.items():
                    self.assertNotIn(key, forbidden_keys, f"forbidden key at {path}.{key}")
                    walk(child, f"{path}.{key}")
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    walk(child, f"{path}[{index}]")
            elif isinstance(value, str):
                lowered = value.lower()
                for fragment in forbidden_fragments:
                    self.assertNotIn(fragment, lowered, f"forbidden fragment at {path}")

        walk(data)


if __name__ == "__main__":
    unittest.main()
