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
    / "public_pdf_extraction_validation.json"
)

FORBIDDEN_KEYS = {
    "authState",
    "cookies",
    "downloadedDocument",
    "ocrOutputPath",
    "password",
    "privateSession",
    "rawBody",
    "rawBytes",
    "rawPdf",
    "sessionState",
    "tracePath",
}

FORBIDDEN_FRAGMENTS = (
    "/data/private/",
    "/data/raw/",
    "devhub.portlandoregon.gov/secure",
    "storage_state",
    "trace.zip",
)


class PublicPdfExtractionFixturesTest(unittest.TestCase):
    def setUp(self) -> None:
        with FIXTURE_PATH.open("r", encoding="utf-8") as handle:
            self.fixture = json.load(handle)

    def test_fixture_has_public_source_hash_and_skip_reasons(self) -> None:
        source = self.fixture["sourceDocument"]
        parsed = urlparse(source["sourceUrl"])

        self.assertTrue(self.fixture["fixtureOnly"])
        self.assertEqual("https", parsed.scheme)
        self.assertEqual("www.portland.gov", parsed.netloc)
        self.assertEqual("application/pdf", source["contentType"])
        self.assertIn("checksum", source)
        self.assertTrue(source["checksum"].startswith("sha256:"))
        self.assertTrue(source["skippedRawByteReason"])
        self.assertTrue(source["skippedOcrOutputReason"])

    def test_page_anchors_and_fields_are_source_linked_and_redacted(self) -> None:
        anchors = {anchor["anchorId"]: anchor for anchor in self.fixture["pageAnchors"]}

        self.assertGreaterEqual(len(anchors), 1)
        for anchor in anchors.values():
            self.assertIsInstance(anchor["pageNumber"], int)
            self.assertGreater(anchor["pageNumber"], 0)
            self.assertIn("#page=", anchor["sourceUrl"])
            self.assertTrue(anchor["sourceUrl"].startswith("https://www.portland.gov/ppd/"))
            self.assertTrue(anchor["snippet"].strip())

        for field in self.fixture["extractedFields"]:
            self.assertIn(field["pageAnchorId"], anchors)
            self.assertTrue(field["sourceUrl"].startswith("https://www.portland.gov/ppd/"))
            self.assertEqual("placeholder_only", field["valuePolicy"])
            self.assertTrue(field["redactedValue"].startswith("[REDACTED:"))
            self.assertTrue(field["redactedValue"].endswith("]"))

    def test_storage_policy_rejects_raw_or_private_artifacts(self) -> None:
        policy = self.fixture["storagePolicy"]

        self.assertFalse(policy["storesRawPdfBytes"])
        self.assertFalse(policy["storesDownloadedDocument"])
        self.assertFalse(policy["storesFullOcrOutput"])
        self.assertFalse(policy["storesPrivateDevhubArtifacts"])
        self.assertTrue(policy["storesRedactedFixtureValuesOnly"])
        _assert_no_forbidden_artifacts(self, self.fixture, allow_rejection_payloads=True)

    def test_rejection_cases_cover_raw_body_private_devhub_and_ocr_output(self) -> None:
        reasons = {case["expectedReason"] for case in self.fixture["rejectionCases"]}

        self.assertIn("raw PDF bodies are not allowed", reasons)
        self.assertIn("private DevHub artifacts are not allowed", reasons)
        self.assertIn("raw OCR output paths are not allowed", reasons)
        for case in self.fixture["rejectionCases"]:
            payload = case["payload"]
            self.assertTrue(_payload_contains_forbidden_marker(payload), case["caseId"])


def _assert_no_forbidden_artifacts(
    test_case: unittest.TestCase,
    value: Any,
    *,
    allow_rejection_payloads: bool = False,
    path: str = "root",
) -> None:
    if allow_rejection_payloads and path.startswith("root.rejectionCases["):
        return
    if isinstance(value, dict):
        for key, child in value.items():
            test_case.assertNotIn(key, FORBIDDEN_KEYS, f"forbidden key at {path}.{key}")
            _assert_no_forbidden_artifacts(
                test_case,
                child,
                allow_rejection_payloads=allow_rejection_payloads,
                path=f"{path}.{key}",
            )
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_no_forbidden_artifacts(
                test_case,
                child,
                allow_rejection_payloads=allow_rejection_payloads,
                path=f"{path}[{index}]",
            )
    elif isinstance(value, str):
        lowered = value.lower()
        for fragment in FORBIDDEN_FRAGMENTS:
            test_case.assertNotIn(fragment, lowered, f"forbidden fragment at {path}")


def _payload_contains_forbidden_marker(value: Any) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_KEYS or _payload_contains_forbidden_marker(child):
                return True
        return False
    if isinstance(value, list):
        return any(_payload_contains_forbidden_marker(item) for item in value)
    if isinstance(value, str):
        lowered = value.lower()
        return any(fragment in lowered for fragment in FORBIDDEN_FRAGMENTS)
    return False


if __name__ == "__main__":
    unittest.main()
