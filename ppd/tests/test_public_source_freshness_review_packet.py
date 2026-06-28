from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ppd.source_freshness.public_source_freshness_review_packet import (
    build_public_source_freshness_review_packet,
    validate_public_source_freshness_review_packet,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "public_source_freshness_review_packet" / "input.json"
GENERATED_AT = "2026-05-28T23:05:00Z"


def load_inputs() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def build_packet() -> dict:
    inputs = load_inputs()
    return build_public_source_freshness_review_packet(
        inputs["public_source_monitoring_schedule_candidate"],
        inputs["post_release_audit_findings_packet"],
        generated_at=GENERATED_AT,
    )


def test_builds_reviewer_owned_public_source_freshness_decisions() -> None:
    packet = build_packet()

    result = validate_public_source_freshness_review_packet(packet)

    assert result.valid is True
    assert packet["packet_type"] == "ppd.public_source_freshness_review_packet.v1"
    assert packet["mode"] == "fixture_first_public_source_freshness_review"
    assert packet["execution_policy"] == {
        "network_allowed": False,
        "network_invoked": False,
        "fetch_urls": False,
        "download_documents": False,
        "persist_raw_body": False,
        "schedule_mutation_allowed": False,
        "live_schedule_mutated": False,
    }
    assert packet["source_ids"] == ["ppd-devhub-faq", "ppd-submit-plans-online"]
    assert packet["post_release_audit_finding_ids"] == ["finding-devhub-attended", "finding-payment-gate"]
    assert packet["schedule_mutation_outcome"]["writes_live_schedule"] is False


def test_decisions_preserve_source_ids_cadence_notes_prerequisites_and_defer_reasons() -> None:
    packet = build_packet()
    decisions = {decision["source_id"]: decision for decision in packet["reviewer_owned_source_freshness_decisions"]}

    devhub = decisions["ppd-devhub-faq"]
    single_pdf = decisions["ppd-submit-plans-online"]

    assert devhub["reviewer_owner"] == "ppd-devhub-guidance-reviewer"
    assert devhub["source_ids_confirmed"] == ["ppd-devhub-faq"]
    assert devhub["cadence_note"]["candidate_cadence"] == "daily"
    assert devhub["cadence_note"]["reviewer_owned"] is True
    assert devhub["stale_source_acknowledgement"] == {
        "acknowledgement_id": "stale-source-ack-ppd-devhub-faq",
        "acknowledgement_status": "acknowledged_for_review_only",
        "does_not_refresh_source": True,
        "requires_reviewer_decision_before_use": True,
    }
    assert devhub["prerequisite_robots_policy_evidence_ids"] == [
        "policy-prereq-ppd-public-metadata-only-20260528",
        "robots-prereq-portland-gov-20260528",
    ]
    assert "post-release-audit-not-production-ready" in devhub["defer_reason_ids"]
    assert "schedule-candidate-abort-conditions-require-review" in devhub["defer_reason_ids"]
    assert single_pdf["cadence_note"]["candidate_cadence"] == "weekly"
    assert single_pdf["reviewer_owner"] == "ppd-file-standards-reviewer"


def test_builder_rejects_schedule_candidate_that_fetches_urls() -> None:
    inputs = load_inputs()
    schedule_candidate = copy.deepcopy(inputs["public_source_monitoring_schedule_candidate"])
    schedule_candidate["execution_policy"]["fetch_urls"] = True

    with pytest.raises(ValueError, match="invalid public source monitoring schedule candidate"):
        build_public_source_freshness_review_packet(
            schedule_candidate,
            inputs["post_release_audit_findings_packet"],
            generated_at=GENERATED_AT,
        )


def test_builder_rejects_private_audit_artifacts() -> None:
    inputs = load_inputs()
    audit_packet = copy.deepcopy(inputs["post_release_audit_findings_packet"])
    audit_packet["session_state"] = "private-devhub-session.json"

    with pytest.raises(ValueError, match="invalid_post_release_audit_findings_packet"):
        build_public_source_freshness_review_packet(
            inputs["public_source_monitoring_schedule_candidate"],
            audit_packet,
            generated_at=GENERATED_AT,
        )


def test_validation_rejects_missing_prerequisite_evidence() -> None:
    packet = build_packet()
    packet["reviewer_owned_source_freshness_decisions"][0]["prerequisite_robots_policy_evidence_ids"] = []

    result = validate_public_source_freshness_review_packet(packet)

    assert result.valid is False
    assert (
        "reviewer_owned_source_freshness_decisions[0].prerequisite_robots_policy_evidence_ids must be non-empty"
        in result.errors
    )


def test_validation_rejects_decisions_without_defer_reasons() -> None:
    packet = build_packet()
    packet["reviewer_owned_source_freshness_decisions"][0]["defer_reason_ids"] = []

    result = validate_public_source_freshness_review_packet(packet)

    assert result.valid is False
    assert "reviewer_owned_source_freshness_decisions[0].defer_reason_ids must be non-empty" in result.errors


def test_validation_rejects_live_schedule_mutation_claims() -> None:
    packet = build_packet()
    packet["schedule_mutation_outcome"]["writes_live_schedule"] = True

    result = validate_public_source_freshness_review_packet(packet)

    assert result.valid is False
    assert "schedule_mutation_outcome.writes_live_schedule must be false" in result.errors
    assert any("writes_live_schedule must not be true" in error for error in result.errors)
