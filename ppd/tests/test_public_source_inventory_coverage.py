from pathlib import Path

import pytest

from ppd.extraction.public_source_inventory_coverage import (
    REQUIRED_GUIDANCE_CATEGORIES,
    CoverageReportError,
    category_claims,
    load_coverage_report,
    validate_coverage_report,
)


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "public_source_inventory"
    / "permit_lifecycle_coverage_report.json"
)


def test_permit_lifecycle_coverage_report_has_required_categories() -> None:
    report = load_coverage_report(FIXTURE_PATH)
    claims = category_claims(report)

    assert set(claims) == set(REQUIRED_GUIDANCE_CATEGORIES)
    for category_id in REQUIRED_GUIDANCE_CATEGORIES:
        assert claims[category_id]


def test_permit_lifecycle_coverage_report_is_fixture_only() -> None:
    report = load_coverage_report(FIXTURE_PATH)

    assert report["sourceMode"] == "fixture_only_public_source_inventory"
    assert report["liveCrawlingUsed"] is False
    assert report["authenticatedAutomationUsed"] is False

    for category in report["categories"]:
        assert category["authorityLabel"]
        assert category["recommendedRecrawlCadence"] in {"weekly", "monthly", "quarterly"}
        for evidence in category["publicSourceEvidence"]:
            assert evidence["fixtureRef"].startswith("ppd/tests/fixtures/")
            assert evidence["sourceUrl"].startswith("https://")
            assert evidence["citation"]


def test_coverage_report_rejects_private_devhub_paths() -> None:
    report = load_coverage_report(FIXTURE_PATH)
    bad_report = dict(report)
    bad_categories = [dict(category) for category in report["categories"]]
    bad_evidence = dict(bad_categories[0]["publicSourceEvidence"][0])
    bad_evidence["sourceUrl"] = "https://devhub.portlandoregon.gov/dashboard/my-permits"
    bad_categories[0] = dict(bad_categories[0], publicSourceEvidence=[bad_evidence])
    bad_report["categories"] = bad_categories

    with pytest.raises(CoverageReportError):
        validate_coverage_report(bad_report)


def test_coverage_report_rejects_raw_response_body_fields() -> None:
    report = load_coverage_report(FIXTURE_PATH)
    bad_report = dict(report)
    bad_categories = [dict(category) for category in report["categories"]]
    bad_categories[0] = dict(bad_categories[0], rawBody="not allowed")
    bad_report["categories"] = bad_categories

    with pytest.raises(CoverageReportError):
        validate_coverage_report(bad_report)
