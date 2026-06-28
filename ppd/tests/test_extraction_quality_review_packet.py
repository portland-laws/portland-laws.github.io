from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from ppd.validation.extraction_quality_review_packet import require_extraction_quality_review_packet, validate_extraction_quality_review_packet


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "extraction_quality_review" / "quality_packet.json"


class ExtractionQualityReviewPacketTest(unittest.TestCase):
    def setUp(self) -> None:
        self.packet = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_fixture_packet_is_valid(self) -> None:
        result = validate_extraction_quality_review_packet(self.packet)
        self.assertTrue(result.ok, [finding.code for finding in result.findings])
        require_extraction_quality_review_packet(self.packet)

    def test_requires_html_pdf_and_form_samples(self) -> None:
        packet = copy.deepcopy(self.packet)
        packet["documentRecords"] = [record for record in packet["documentRecords"] if record["document_type"] != "form"]
        result = validate_extraction_quality_review_packet(packet)
        self.assertIn("missing_document_type_sample", {finding.code for finding in result.findings})

    def test_low_confidence_records_need_review_routing(self) -> None:
        packet = copy.deepcopy(self.packet)
        form_record = packet["documentRecords"][2]
        form_record["humanReviewStatus"] = "fixture_reviewed"
        form_record.pop("reviewQueue")
        result = validate_extraction_quality_review_packet(packet)
        self.assertIn("low_confidence_without_review_route", {finding.code for finding in result.findings})

    def test_rejects_unordered_headings(self) -> None:
        packet = copy.deepcopy(self.packet)
        packet["documentRecords"][0]["headings"] = [
            {"sourceOrder": 2, "text": "Upload plans"},
            {"sourceOrder": 1, "text": "Prepare files"},
        ]
        result = validate_extraction_quality_review_packet(packet)
        self.assertIn("unordered_headings", {finding.code for finding in result.findings})

    def test_rejects_raw_document_body_or_private_artifacts(self) -> None:
        packet = copy.deepcopy(self.packet)
        packet["documentRecords"][0]["raw_html"] = "raw fixture body should not be committed"
        packet["documentRecords"][1]["notes"] = "trace.zip from /devhub/traces/ must not appear"
        result = validate_extraction_quality_review_packet(packet)
        codes = {finding.code for finding in result.findings}
        self.assertIn("raw_document_body_present", codes)
        self.assertIn("private_value_present", codes)


if __name__ == "__main__":
    unittest.main()
