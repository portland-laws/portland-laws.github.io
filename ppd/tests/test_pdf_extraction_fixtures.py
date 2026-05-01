#!/usr/bin/env python3
"""Validate deterministic PP&D public PDF extraction fixture definitions."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


FIXTURE_PATH = Path(__file__).with_name("fixtures") / "pdf_extraction_fixtures.json"


class PdfExtractionFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_fixture_set_is_public_and_offline(self) -> None:
        policy = self.payload["source_policy"]
        self.assertTrue(policy["public_only"])
        self.assertTrue(policy["no_live_fetch_required"])
        self.assertTrue(policy["no_downloaded_documents"])
        self.assertTrue(policy["no_private_devhub_session"])
        self.assertEqual(policy["authoritative_discovery_source"], "https://www.portland.gov/ppd/applications-forms")

    def test_each_fixture_has_required_contract_fields(self) -> None:
        required_document_fields = set(self.payload["normalization_contract"]["required_document_fields"])
        required_expected_fields = set(self.payload["normalization_contract"]["required_expected_extraction_fields"])

        for fixture in self.payload["fixtures"]:
            with self.subTest(fixture_id=fixture.get("fixture_id")):
                self.assertLessEqual(required_document_fields, set(fixture))
                self.assertLessEqual(required_expected_fields, set(fixture["expected_extraction"]))
                self.assertEqual(fixture["source"]["expected_host"], "www.portland.gov")
                self.assertEqual(fixture["source"]["expected_content_type"], "application/pdf")
                self.assertEqual(fixture["source"]["public_access"], "unauthenticated")
                self.assertTrue(fixture["source"]["future_capture_required"])

    def test_fixture_coverage_includes_application_and_checklists(self) -> None:
        document_types = {fixture["document_type"] for fixture in self.payload["fixtures"]}
        families = {fixture["document_family"] for fixture in self.payload["fixtures"]}
        self.assertIn("application_pdf", document_types)
        self.assertIn("checklist_pdf", document_types)
        self.assertIn("public_ppd_application", families)
        self.assertIn("public_ppd_checklist", families)
        self.assertGreaterEqual(len(self.payload["fixtures"]), 3)

    def test_page_anchors_and_required_labels_have_page_provenance(self) -> None:
        for fixture in self.payload["fixtures"]:
            pages = {page["page_number"] for page in fixture["synthetic_pdf_text_pages"]}
            extraction = fixture["expected_extraction"]
            with self.subTest(fixture_id=fixture["fixture_id"]):
                self.assertTrue(extraction["page_anchors"])
                self.assertTrue(extraction["detected_sections"])
                self.assertTrue(extraction["required_data_labels"])
                for anchor in extraction["page_anchors"]:
                    self.assertIn(anchor["page_number"], pages)
                    self.assertTrue(anchor["expected_text"].strip())
                for signature in extraction["signature_blocks"]:
                    self.assertIn(signature["page_number"], pages)
                for group in extraction["checkbox_groups"]:
                    self.assertIn(group["page_number"], pages)

    def test_fixtures_do_not_embed_private_or_live_artifacts(self) -> None:
        raw = FIXTURE_PATH.read_text(encoding="utf-8").lower()
        forbidden_terms = [
            "devhub.portlandoregon.gov/login",
            "storage-state",
            "auth-state",
            "session cookie",
            "captcha",
            "mfa secret",
            "payment method",
            "downloaded_at"
        ]
        for term in forbidden_terms:
            with self.subTest(term=term):
                self.assertNotIn(term, raw)


if __name__ == "__main__":
    unittest.main()
