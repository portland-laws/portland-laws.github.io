from __future__ import annotations

import copy
import json
from pathlib import Path

from ppd.crawler.public_recrawl_plan import (
    assert_public_recrawl_batch_plan_is_safe,
    validate_public_recrawl_batch_plan,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "public_recrawl_plan"


def load_valid_plan() -> dict:
    return json.loads((FIXTURE_DIR / "valid_plan.json").read_text(encoding="utf-8"))


def issue_codes(plan: dict) -> set[str]:
    return {issue.code for issue in validate_public_recrawl_batch_plan(plan)}


def test_valid_public_recrawl_plan_has_no_issues() -> None:
    plan = load_valid_plan()

    assert validate_public_recrawl_batch_plan(plan) == []
    assert_public_recrawl_batch_plan_is_safe(plan)


def test_rejects_live_network_flags() -> None:
    plan = load_valid_plan()
    plan["live_network"] = True

    assert "live_network_flag" in issue_codes(plan)


def test_rejects_private_or_authenticated_urls() -> None:
    plan = load_valid_plan()
    plan["targets"][0]["url"] = "https://devhub.portlandoregon.gov/account/dashboard?token=secret"

    assert "private_or_authenticated_url" in issue_codes(plan)


def test_rejects_outside_allowlist_hosts() -> None:
    plan = load_valid_plan()
    plan["targets"][0]["url"] = "https://example.com/ppd"

    assert "outside_allowlist_host" in issue_codes(plan)


def test_rejects_missing_robots_evidence() -> None:
    plan = load_valid_plan()
    del plan["targets"][0]["robots_evidence"]

    assert "missing_robots_evidence" in issue_codes(plan)


def test_rejects_missing_policy_evidence() -> None:
    plan = load_valid_plan()
    del plan["targets"][0]["policy_evidence"]

    assert "missing_policy_evidence" in issue_codes(plan)


def test_rejects_unbounded_rate_limits() -> None:
    plan = load_valid_plan()
    plan["rate_limit"] = {"min_delay_seconds": 0}

    assert "unbounded_rate_limit" in issue_codes(plan)


def test_rejects_raw_body_persistence_at_plan_or_target_level() -> None:
    plan = load_valid_plan()
    plan["persist_raw_body"] = True
    target_plan = load_valid_plan()
    target_plan["targets"][0]["store_raw_body"] = True

    assert "raw_body_persistence" in issue_codes(plan)
    assert "raw_body_persistence" in issue_codes(target_plan)


def test_rejects_downloaded_document_paths_at_plan_or_target_level() -> None:
    plan = load_valid_plan()
    plan["downloaded_document_path"] = "/tmp/ppd/raw.pdf"
    target_plan = load_valid_plan()
    target_plan["targets"][0]["document_paths"] = ["/tmp/ppd/form.pdf"]

    assert "downloaded_document_path" in issue_codes(plan)
    assert "downloaded_document_path" in issue_codes(target_plan)


def test_rejects_missing_dry_run_only_status() -> None:
    plan = load_valid_plan()
    del plan["dry_run_only"]

    assert "missing_dry_run_only" in issue_codes(plan)


def test_reports_all_required_rejections_together() -> None:
    plan = copy.deepcopy(load_valid_plan())
    plan.update(
        {
            "live_network": True,
            "dry_run_only": False,
            "rate_limit": {},
            "persist_raw_body": True,
            "downloaded_document_path": "/tmp/raw.pdf",
        }
    )
    plan["targets"][0] = {"url": "https://example.com/login?token=secret"}

    codes = issue_codes(plan)

    assert {
        "live_network_flag",
        "private_or_authenticated_url",
        "outside_allowlist_host",
        "missing_robots_evidence",
        "missing_policy_evidence",
        "unbounded_rate_limit",
        "raw_body_persistence",
        "downloaded_document_path",
        "missing_dry_run_only",
    }.issubset(codes)
