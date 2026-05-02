"""Tests for validation-only PP&D source coverage gap reports."""

from __future__ import annotations

import json
from pathlib import Path
import unittest

from ppd.contracts.source_coverage_gap_report import (
    assert_source_coverage_gap_report,
    build_source_coverage_gap_report,
    validate_source_coverage_gap_report,
)


_FIXTURE_DIR = Path(__file__).parent / "fixtures" / "source_coverage_gap"


class SourceCoverageGapReportTest(unittest.TestCase):
    def test_reports_inventory_categories_without_process_fixtures(self) -> None:
        inventory = _load_json("source_inventory_permit_family_categories.json")
        fixture_index = _load_json("permit_process_fixture_index.json")

        report = build_source_coverage_gap_report(inventory, fixture_index)

        assert_source_coverage_gap_report(report)
        self.assertEqual(report["coverageStatus"], "gaps_found")
        self.assertEqual(report["summary"]["inventoryCategoryCount"], 7)
        self.assertEqual(report["summary"]["permitProcessFixtureCount"], 4)
        self.assertEqual(report["coveredPermitFamilies"], [
            "residential-building-permit",
            "single-pdf-process",
            "solar-permit",
            "trade-permit-with-plan-review",
        ])
        self.assertEqual(report["missingPermitFamilies"], [
            "demolition-permit",
            "sign-permit",
            "urban-forestry-permit",
        ])
        self.assertEqual(
            [category["category_id"] for category in report["missingCategories"]],
            [
                "demolition-permit-guidance",
                "sign-permit-guidance",
                "urban-forestry-permit-guidance",
            ],
        )
        self.assertEqual(report["validationErrors"], [])

    def test_fails_closed_for_unsafe_or_incomplete_inventory_entries(self) -> None:
        unsafe_inventory = {
            "categories": [
                {
                    "category_id": "private-devhub-example",
                    "permit_family": "private-family",
                    "canonical_url": "https://devhub.portlandoregon.gov/mypermits",
                    "authority_label": "DevHub private session",
                    "recrawl_cadence": "never",
                    "raw_body": "private",
                },
                {
                    "category_id": "missing-provenance",
                    "permit_family": "missing-provenance-family",
                    "canonical_url": "https://www.portland.gov/ppd/example"
                },
            ]
        }
        fixture_index = {"process_fixtures": []}

        report = build_source_coverage_gap_report(unsafe_inventory, fixture_index)

        self.assertEqual(report["coverageStatus"], "invalid")
        self.assertTrue(any("private or action-oriented DevHub path" in error for error in report["validationErrors"]))
        self.assertTrue(any("raw_body is not allowed" in error for error in report["validationErrors"]))
        self.assertTrue(any("missing authority_label" in error for error in report["validationErrors"]))
        self.assertTrue(any("missing recrawl_cadence" in error for error in report["validationErrors"]))
        self.assertEqual(validate_source_coverage_gap_report(report), [])


def _load_json(name: str) -> dict[str, object]:
    with (_FIXTURE_DIR / name).open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise AssertionError(f"fixture {name} must contain a JSON object")
    return data


if __name__ == "__main__":
    unittest.main()
