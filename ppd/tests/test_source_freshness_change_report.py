"""Fixture-only tests for the source freshness change report renderer."""

from __future__ import annotations

import json
import py_compile
import unittest
from pathlib import Path

from ppd.extraction.source_freshness_change_report import (
    SourceFreshnessChangeReportError,
    render_source_freshness_change_report,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "source_freshness" / "change_report_renderer.json"
MODULE_PATH = Path(__file__).parents[1] / "extraction" / "source_freshness_change_report.py"


class SourceFreshnessChangeReportTests(unittest.TestCase):
    def load_fixture(self) -> dict:
        with FIXTURE_PATH.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def test_module_is_syntax_valid_before_renderer_validation(self) -> None:
        py_compile.compile(str(MODULE_PATH), doraise=True)

    def test_renders_summary_after_classifier_passes(self) -> None:
        report = render_source_freshness_change_report(self.load_fixture())

        self.assertEqual(report["schemaVersion"], 1)
        self.assertEqual(report["sourceFreshnessClassifier"]["status"], "passed")
        self.assertEqual(report["summary"]["changedRequirementCount"], 2)
        self.assertEqual(report["summary"]["newLinkCount"], 1)
        self.assertEqual(report["summary"]["removedLinkCount"], 1)
        self.assertEqual(report["summary"]["affectedPermitProcessFixtureCount"], 2)
        self.assertEqual(report["summary"]["citationReferenceCount"], 2)

    def test_report_preserves_changed_requirements_links_fixtures_and_citations(self) -> None:
        report = render_source_freshness_change_report(self.load_fixture())

        requirement_ids = {item["requirementId"] for item in report["changedRequirements"]}
        linked_urls = {item["linkedUrl"] for item in report["linkChanges"]}
        fixture_paths = {item["fixturePath"] for item in report["affectedPermitProcessFixtures"]}
        citation_ids = {item["citationId"] for item in report["citationReferences"]}

        self.assertEqual(requirement_ids, {"single-pdf-plan-package", "trade-plan-review-correction-upload"})
        self.assertIn("https://www.portland.gov/ppd/forms/single-pdf-process-checklist", linked_urls)
        self.assertIn("https://www.portland.gov/ppd/old-correction-upload-guide", linked_urls)
        self.assertEqual(
            fixture_paths,
            {
                "ppd/tests/fixtures/permit_processes/single_pdf_process.json",
                "ppd/tests/fixtures/permit_processes/trade_permit_with_plan_review.json",
            },
        )
        self.assertEqual(citation_ids, {"citation-single-pdf-process", "citation-correction-upload"})

    def test_refuses_to_render_before_classifier_passes(self) -> None:
        fixture = self.load_fixture()
        fixture["sourceFreshnessClassifier"] = {
            "status": "failed",
            "taskPassed": False,
            "fixturePath": "ppd/tests/fixtures/source_freshness/four_records.json",
        }

        with self.assertRaisesRegex(SourceFreshnessChangeReportError, "classifier must pass"):
            render_source_freshness_change_report(fixture)

    def test_rejects_private_or_raw_artifacts(self) -> None:
        fixture = self.load_fixture()
        fixture["linkChanges"][0]["tracePath"] = "ppd/data/private/devhub/session/trace.zip"

        with self.assertRaisesRegex(SourceFreshnessChangeReportError, "private or raw artifact"):
            render_source_freshness_change_report(fixture)

    def test_rejects_unknown_citation_references(self) -> None:
        fixture = self.load_fixture()
        fixture["changedRequirements"][0]["citationIds"] = ["missing-citation"]

        with self.assertRaisesRegex(SourceFreshnessChangeReportError, "unknown ids"):
            render_source_freshness_change_report(fixture)


if __name__ == "__main__":
    unittest.main()
