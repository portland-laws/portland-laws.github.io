from pathlib import Path

import pytest

from ppd.dry_run_crawl_plan_validation import (
    CrawlPlanValidationError,
    iter_dry_run_crawl_plan_issues,
    validate_dry_run_crawl_plan,
)

_FIXTURES = Path(__file__).parent / "fixtures" / "dry_run_crawl_plans"


def _valid_plan():
    return {
        "dry_run": True,
        "start_urls": ["https://www.portland.gov/ppd/permits"],
        "allowed_hosts": ["www.portland.gov", "devhub.portlandoregon.gov"],
        "rate_limit_policy": {"requests_per_second": 0.2},
        "freshness_policy": {"max_age_days": 30},
        "output_path": "ppd/tests/fixtures/dry_run_crawl_plans/normalized_index.json",
    }


def _codes(plan):
    return {issue.code for issue in iter_dry_run_crawl_plan_issues(plan)}


def test_valid_public_dry_run_plan_passes():
    validate_dry_run_crawl_plan(_valid_plan())


def test_rejects_private_authenticated_devhub_urls():
    plan = _valid_plan()
    plan["start_urls"] = ["https://devhub.portlandoregon.gov/login"]

    with pytest.raises(CrawlPlanValidationError) as exc_info:
        validate_dry_run_crawl_plan(plan)

    assert "private-devhub-url" in {issue.code for issue in exc_info.value.issues}


def test_rejects_over_broad_host_expansion():
    plan = _valid_plan()
    plan["allowed_hosts"] = ["*.portland.gov"]

    assert "over-broad-host-expansion" in _codes(plan)


def test_rejects_unsupported_url_schemes():
    plan = _valid_plan()
    plan["start_urls"] = ["file:///tmp/devhub.html", "ftp://www.portland.gov/pub/file.pdf"]

    assert "unsupported-url-scheme" in _codes(plan)


def test_rejects_missing_rate_limit_or_freshness_policy():
    plan = _valid_plan()
    del plan["rate_limit_policy"]
    del plan["freshness_policy"]

    assert {
        "missing-rate-limit-policy",
        "missing-freshness-policy",
    }.issubset(_codes(plan))


def test_rejects_raw_body_or_document_output_paths():
    plan = _valid_plan()
    plan["outputs"] = {
        "body_path": "ppd/tests/fixtures/dry_run_crawl_plans/raw/html/body.html",
        "document_path": "ppd/tests/fixtures/dry_run_crawl_plans/downloads/permit.pdf",
    }

    assert "raw-output-path" in _codes(plan)


def test_fixture_directory_reference_is_local_to_ppd_tests():
    assert _FIXTURES.parts[-3:] == ("tests", "fixtures", "dry_run_crawl_plans")
