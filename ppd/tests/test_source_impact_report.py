from __future__ import annotations

import json
from pathlib import Path

from ppd.extraction.source_impact_report import (
    NOT_CURRENT_RECOMMENDATION_STATUS,
    changed_hash_impact_index,
    validate_blocked_before_current,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "source_impact" / "stale_or_changed_sources.json"


def load_fixture() -> dict[str, object]:
    with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def test_stale_or_changed_source_fixture_maps_hashes_to_impacted_contract_ids() -> None:
    report = load_fixture()

    index = changed_hash_impact_index(report)

    assert sorted(index) == [
        "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
    ]
    assert index["sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"].affected_requirement_ids == (
        "req-devhub-application-dynamic-questions",
        "req-devhub-application-save-draft",
        "req-devhub-application-certification-gate",
    )
    assert index["sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"].affected_process_ids == (
        "process-document-preparation",
        "process-upload-staging",
    )
    assert index["sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"].affected_guardrail_bundle_ids == (
        "guardrail-financial-action-stop",
        "guardrail-fee-notice-readonly-review",
    )


def test_impacted_sources_block_readiness_before_recommendations_are_current() -> None:
    report = load_fixture()

    validate_blocked_before_current(report)
    for impact in changed_hash_impact_index(report).values():
        assert impact.recommendation_status == NOT_CURRENT_RECOMMENDATION_STATUS
        assert impact.recommendation_is_current is False
        assert all(status.startswith("blocked_") for status in impact.blocked_readiness_statuses)
