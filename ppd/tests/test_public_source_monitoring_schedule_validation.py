from __future__ import annotations

import pytest

from ppd.validation.public_source_monitoring_schedule import (
    assert_valid_schedule_candidate,
    validate_schedule_candidate,
)


def issue_codes(candidate: dict) -> set[str]:
    return {issue.code for issue in validate_schedule_candidate(candidate)}


def valid_candidate() -> dict:
    return {
        "source_url": "https://www.portland.gov/ppd/public-notices",
        "robots_txt_checked": True,
        "source_policy_reviewed": True,
        "reviewer_owners": ["ppd-reviewer"],
        "abort_conditions": ["robots policy changes", "authentication wall appears"],
        "enabled": False,
    }


def test_accepts_minimal_public_allowlisted_candidate() -> None:
    assert validate_schedule_candidate(valid_candidate()) == []
    assert_valid_schedule_candidate(valid_candidate())


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost:8000/public-notices",
        "https://127.0.0.1/public-notices",
        "https://10.0.0.5/public-notices",
        "https://user:pass@www.portland.gov/public-notices",
        "file:///tmp/source.html",
        "https://www.portland.gov/public-notices?token=secret",
    ],
)
def test_rejects_private_or_authenticated_urls(url: str) -> None:
    candidate = valid_candidate()
    candidate["source_url"] = url
    assert "private_or_authenticated_url" in issue_codes(candidate)


def test_rejects_non_allowlisted_hosts() -> None:
    candidate = valid_candidate()
    candidate["source_url"] = "https://example.com/portland/public-notices"
    assert "non_allowlisted_host" in issue_codes(candidate)


@pytest.mark.parametrize(
    "url",
    [
        "https://www.portland.gov/public-notices/download/report",
        "https://www.portland.gov/public-notices/archive/2025",
        "https://www.portland.gov/public-notices/raw/body",
        "https://www.portland.gov/public-notices/report.pdf",
        "https://www.portland.gov/public-notices/export/results.zip",
    ],
)
def test_rejects_raw_body_download_archive_and_artifact_paths(url: str) -> None:
    candidate = valid_candidate()
    candidate["source_url"] = url
    assert "raw_body_download_or_archive_path" in issue_codes(candidate)


def test_rejects_missing_robots_or_policy_prerequisites() -> None:
    candidate = valid_candidate()
    candidate["robots_txt_checked"] = False
    candidate["source_policy_reviewed"] = False
    codes = issue_codes(candidate)
    assert "missing_robots_prerequisite" in codes
    assert "missing_policy_prerequisite" in codes


def test_rejects_live_network_execution_claims() -> None:
    candidate = valid_candidate()
    candidate["live_network_execution"] = True
    assert "live_network_execution_claim" in issue_codes(candidate)


def test_rejects_missing_reviewer_owners() -> None:
    candidate = valid_candidate()
    candidate["reviewer_owners"] = []
    assert "missing_reviewer_owners" in issue_codes(candidate)


def test_rejects_missing_abort_conditions() -> None:
    candidate = valid_candidate()
    candidate["abort_conditions"] = []
    assert "missing_abort_conditions" in issue_codes(candidate)


def test_rejects_active_schedule_mutation_flags() -> None:
    candidate = valid_candidate()
    candidate["cron_enabled"] = "true"
    assert "active_schedule_mutation" in issue_codes(candidate)


def test_assert_valid_raises_with_codes() -> None:
    candidate = valid_candidate()
    candidate["enabled"] = True
    with pytest.raises(ValueError, match="active_schedule_mutation"):
        assert_valid_schedule_candidate(candidate)
