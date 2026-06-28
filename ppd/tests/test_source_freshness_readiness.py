from __future__ import annotations

import json
from pathlib import Path

from ppd.logic.source_freshness_readiness import evaluate_source_freshness_readiness


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "source_freshness_readiness.json"


def _fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_source_freshness_readiness_allows_current_official_evidence() -> None:
    fixture = _fixture()
    result = evaluate_source_freshness_readiness(
        registry_records=fixture["registry_records"],
        change_monitor_records=fixture["change_monitor_records"],
        required_source_ids=["ppd-devhub-faq", "ppd-submit-plans-online"],
        as_of=fixture["as_of"],
        max_age_days=fixture["max_age_days"],
    )

    assert result == {
        "ready": True,
        "checked_source_ids": ["ppd-devhub-faq", "ppd-submit-plans-online"],
        "blocked_reasons": [],
        "missing_source_ids": [],
        "stale_source_ids": [],
        "hash_changed_source_ids": [],
    }


def test_source_freshness_readiness_blocks_stale_official_evidence() -> None:
    fixture = _fixture()
    result = evaluate_source_freshness_readiness(
        registry_records=fixture["registry_records"],
        change_monitor_records=fixture["change_monitor_records"],
        required_source_ids=["ppd-stale-fee-guide"],
        as_of=fixture["as_of"],
        max_age_days=fixture["max_age_days"],
    )

    assert result["ready"] is False
    assert result["blocked_reasons"] == ["stale_source_evidence"]
    assert result["stale_source_ids"] == ["ppd-stale-fee-guide"]


def test_source_freshness_readiness_blocks_missing_official_evidence() -> None:
    fixture = _fixture()
    result = evaluate_source_freshness_readiness(
        registry_records=fixture["registry_records"],
        change_monitor_records=fixture["change_monitor_records"],
        required_source_ids=["ppd-missing-official-guide"],
        as_of=fixture["as_of"],
        max_age_days=fixture["max_age_days"],
    )

    assert result["ready"] is False
    assert result["blocked_reasons"] == ["missing_source_evidence"]
    assert result["missing_source_ids"] == ["ppd-missing-official-guide"]


def test_source_freshness_readiness_blocks_hash_changed_official_evidence() -> None:
    fixture = _fixture()
    result = evaluate_source_freshness_readiness(
        registry_records=fixture["registry_records"],
        change_monitor_records=fixture["change_monitor_records"],
        required_source_ids=["ppd-apply-permits"],
        as_of=fixture["as_of"],
        max_age_days=fixture["max_age_days"],
    )

    assert result["ready"] is False
    assert result["blocked_reasons"] == ["hash_changed_source_evidence"]
    assert result["hash_changed_source_ids"] == ["ppd-apply-permits"]


def test_source_freshness_readiness_reports_combined_blockers_deterministically() -> None:
    fixture = _fixture()
    result = evaluate_source_freshness_readiness(
        registry_records=fixture["registry_records"],
        change_monitor_records=fixture["change_monitor_records"],
        required_source_ids=[
            "ppd-missing-official-guide",
            "ppd-stale-fee-guide",
            "ppd-apply-permits",
        ],
        as_of=fixture["as_of"],
        max_age_days=fixture["max_age_days"],
    )

    assert result["ready"] is False
    assert result["blocked_reasons"] == [
        "missing_source_evidence",
        "stale_source_evidence",
        "hash_changed_source_evidence",
    ]
    assert result["missing_source_ids"] == ["ppd-missing-official-guide"]
    assert result["stale_source_ids"] == ["ppd-stale-fee-guide"]
    assert result["hash_changed_source_ids"] == ["ppd-apply-permits"]
