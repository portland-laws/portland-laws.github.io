from __future__ import annotations

import json
from pathlib import Path

import pytest

from ppd.source_freshness.public_source_monitoring_schedule_candidate import (
    build_public_source_monitoring_schedule_candidate,
    validate_public_source_monitoring_schedule_candidate,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "public_source_monitoring_schedule_candidate" / "input.json"
GENERATED_AT = "2026-05-28T22:10:00Z"


def load_inputs() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def build_candidate() -> dict:
    inputs = load_inputs()
    return build_public_source_monitoring_schedule_candidate(
        inputs["source_freshness_drift_digest"],
        inputs["public_crawl_metadata_dry_run_intake"],
        inputs["safe_next_action_release_notes"],
        generated_at=GENERATED_AT,
    )


def test_builds_metadata_only_schedule_candidate_from_three_fixture_inputs() -> None:
    packet = build_candidate()

    assert validate_public_source_monitoring_schedule_candidate(packet).valid is True
    assert packet["packet_type"] == "ppd.public_source_monitoring_schedule_candidate.v1"
    assert packet["mode"] == "fixture_first_metadata_only_schedule_candidate"
    assert packet["execution_policy"] == {
        "network_allowed": False,
        "network_invoked": False,
        "fetch_urls": False,
        "download_documents": False,
        "persist_raw_body": False,
        "schedule_mutation_allowed": False,
        "live_schedule_mutated": False,
    }
    assert packet["allowlisted_source_ids"] == ["ppd-devhub-faq", "ppd-submit-plans-online"]
    assert packet["robots_policy_prerequisite_ids"] == [
        "policy-prereq-ppd-public-metadata-only-20260528",
        "robots-prereq-portland-gov-20260528",
    ]


def test_recommendations_include_cadence_reviewers_and_abort_conditions() -> None:
    packet = build_candidate()
    by_source = {item["source_id"]: item for item in packet["cadence_recommendations"]}

    assert by_source["ppd-devhub-faq"]["recommended_cadence"] == "daily"
    assert by_source["ppd-devhub-faq"]["reviewer_owner"] == "ppd-devhub-guidance-reviewer"
    assert by_source["ppd-submit-plans-online"]["recommended_cadence"] == "weekly"
    assert by_source["ppd-submit-plans-online"]["reviewer_owner"] == "ppd-file-standards-reviewer"
    assert by_source["ppd-devhub-faq"]["metadata_only"] is True
    assert "abort-if-live-fetch-requested" in by_source["ppd-devhub-faq"]["abort_condition_ids"]


def test_validation_rejects_live_schedule_mutation() -> None:
    packet = build_candidate()
    packet["execution_policy"]["schedule_mutation_allowed"] = True

    result = validate_public_source_monitoring_schedule_candidate(packet)

    assert result.valid is False
    assert "execution_policy.schedule_mutation_allowed must be false" in result.errors


def test_validation_rejects_missing_prerequisite_ids_on_recommendation() -> None:
    packet = build_candidate()
    packet["cadence_recommendations"][0]["robots_policy_prerequisite_ids"] = []

    result = validate_public_source_monitoring_schedule_candidate(packet)

    assert result.valid is False
    assert "cadence_recommendations[0].robots_policy_prerequisite_ids must be non-empty" in result.errors


def test_validation_rejects_raw_or_private_artifact_references() -> None:
    packet = build_candidate()
    packet["cadence_recommendations"][0]["raw_body_path"] = "ppd/local/raw/body.html"

    result = validate_public_source_monitoring_schedule_candidate(packet)

    assert result.valid is False
    assert any("raw_body_path is forbidden" in error for error in result.errors)


def test_builder_rejects_unsafe_intake_before_candidate_creation() -> None:
    inputs = load_inputs()
    inputs["public_crawl_metadata_dry_run_intake"]["requested_url"] = "https://devhub.portlandoregon.gov/account/my-permits?token=secret"

    with pytest.raises(ValueError, match="invalid public crawl metadata dry-run intake"):
        build_public_source_monitoring_schedule_candidate(
            inputs["source_freshness_drift_digest"],
            inputs["public_crawl_metadata_dry_run_intake"],
            inputs["safe_next_action_release_notes"],
            generated_at=GENERATED_AT,
        )
