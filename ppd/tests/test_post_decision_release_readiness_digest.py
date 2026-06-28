from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from ppd.post_decision_release_readiness_digest import (
    PACKET_TYPE,
    PostDecisionReleaseReadinessDigestError,
    build_post_decision_release_readiness_digest,
    load_fixture,
    validate_digest,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "post_decision_release_readiness_digest" / "input_packets.json"


def test_builds_metadata_only_post_decision_release_readiness_digest() -> None:
    fixture = load_fixture(FIXTURE_PATH)

    digest = build_post_decision_release_readiness_digest(fixture)

    assert digest["packet_type"] == PACKET_TYPE
    assert digest["fixture_first"] is True
    assert digest["metadata_only"] is True
    assert digest["live_actions_performed"] is False
    assert digest["private_artifacts_included"] is False
    assert digest["release_status"] == "blocked"
    assert {item["input_role"] for item in digest["inputs_consumed"]} == {
        "public_source_registry_promotion_decision",
        "guardrail_activation_decision",
        "source_freshness_drift_digest",
        "devhub_read_only_pilot_readiness_reconciliation",
    }
    assert all(
        item.get("decision_link_id")
        for item in digest["inputs_consumed"]
        if item["input_role"].endswith("_decision")
    )
    assert all(
        item.get("reconciliation_link_id")
        for item in digest["inputs_consumed"]
        if item["input_role"].endswith("_reconciliation")
    )
    assert {blocker["source_packet"] for blocker in digest["remaining_blockers"]} == {
        "source_registry",
        "guardrail_activation",
        "source_freshness",
        "devhub_read_only_pilot",
    }
    assert all(capability["allowed_now"] is True for capability in digest["approved_offline_only_capabilities"])
    assert all(capability["requires_live_network"] is False for capability in digest["approved_offline_only_capabilities"])
    assert all(action["deferred"] is True and action["allowed_now"] is False for action in digest["deferred_live_actions"])
    assert all(claim["citation_ids"] for claim in digest["readiness_claims"])
    assert {ref["source_packet_id"] for ref in digest["rollback_references"]} == {
        packet["packet_id"] for packet in fixture["inputs"].values()
    }
    assert digest["safety_summary"]["source_registry_mutation_allowed"] is False
    assert digest["safety_summary"]["live_guardrail_enforcement_allowed"] is False
    assert digest["safety_summary"]["live_network_crawl_allowed"] is False
    assert digest["safety_summary"]["authenticated_devhub_automation_allowed"] is False
    assert validate_digest(digest) == []


def test_digest_rejects_private_or_live_artifact_fields() -> None:
    fixture = load_fixture(FIXTURE_PATH)
    digest = build_post_decision_release_readiness_digest(fixture)
    digest["reviewer_prompts"][0]["storage_state"] = "storage_state/private.json"

    errors = validate_digest(digest)

    assert any("forbidden private artifact" in error or "forbidden private artifact text" in error for error in errors)


def test_build_requires_all_four_post_decision_inputs() -> None:
    fixture = load_fixture(FIXTURE_PATH)
    del fixture["inputs"]["source_freshness_drift_digest"]

    with pytest.raises(PostDecisionReleaseReadinessDigestError, match="missing required inputs"):
        build_post_decision_release_readiness_digest(fixture)


def test_build_rejects_missing_decision_or_reconciliation_links() -> None:
    fixture = load_fixture(FIXTURE_PATH)
    del fixture["inputs"]["guardrail_activation_decision"]["decision_link_id"]
    del fixture["inputs"]["devhub_read_only_pilot_readiness_reconciliation"]["reconciliation_link_id"]

    with pytest.raises(PostDecisionReleaseReadinessDigestError) as excinfo:
        build_post_decision_release_readiness_digest(fixture)

    message = str(excinfo.value)
    assert "guardrail_activation_decision missing decision_link_id" in message
    assert "devhub_read_only_pilot_readiness_reconciliation missing reconciliation_link_id" in message


def test_digest_rejects_uncited_readiness_claims() -> None:
    fixture = load_fixture(FIXTURE_PATH)
    digest = build_post_decision_release_readiness_digest(fixture)
    digest["readiness_claims"][0]["citation_ids"] = []

    errors = validate_digest(digest)

    assert "$.readiness_claims[0] has uncited readiness claim" in errors


def test_build_rejects_raw_crawl_download_and_archive_references() -> None:
    fixture = load_fixture(FIXTURE_PATH)
    packet = fixture["inputs"]["source_freshness_drift_digest"]
    packet["raw_crawl_output"] = "raw-crawl/body.html"
    packet["archive_artifact_ref"] = "captures/raw.warc"
    packet["downloaded_document_path"] = "/home/example/Downloads/form.pdf"

    with pytest.raises(PostDecisionReleaseReadinessDigestError) as excinfo:
        build_post_decision_release_readiness_digest(fixture)

    message = str(excinfo.value)
    assert "raw_crawl_output uses forbidden private artifact field" in message
    assert "archive_artifact_ref uses forbidden private artifact field" in message
    assert "downloaded_document_path uses forbidden private artifact field" in message


def test_build_rejects_live_network_or_devhub_execution_claims() -> None:
    fixture = load_fixture(FIXTURE_PATH)
    fixture["inputs"]["source_freshness_drift_digest"]["live_network_called"] = True
    fixture["inputs"]["devhub_read_only_pilot_readiness_reconciliation"]["devhub_execution_performed"] = True

    with pytest.raises(PostDecisionReleaseReadinessDigestError) as excinfo:
        build_post_decision_release_readiness_digest(fixture)

    message = str(excinfo.value)
    assert "live_network_called claims live network or DevHub execution" in message
    assert "devhub_execution_performed claims live network or DevHub execution" in message


def test_digest_rejects_production_ready_labels_while_blockers_remain() -> None:
    fixture = load_fixture(FIXTURE_PATH)
    digest = build_post_decision_release_readiness_digest(fixture)
    digest["release_status"] = "production-ready"

    errors = validate_digest(digest)

    assert "release_status must not be production-ready while blockers remain" in errors


def test_digest_rejects_enabled_consequential_capabilities() -> None:
    fixture = load_fixture(FIXTURE_PATH)
    digest = build_post_decision_release_readiness_digest(fixture)
    digest["approved_offline_only_capabilities"].append(
        {
            "capability_id": "devhub.payment_submission_upload_enabled",
            "summary": "Enable payment, upload, scheduling, cancellation, submission, and certification actions.",
            "allowed_now": True,
            "requires_live_network": False,
        }
    )

    errors = validate_digest(digest)

    assert any("enables a consequential capability" in error for error in errors)


def test_digest_rejects_absent_rollback_reference_for_consumed_packet() -> None:
    fixture = load_fixture(FIXTURE_PATH)
    digest = build_post_decision_release_readiness_digest(fixture)
    missing_packet_id = fixture["inputs"]["source_freshness_drift_digest"]["packet_id"]
    digest["rollback_references"] = [
        ref for ref in digest["rollback_references"] if ref["source_packet_id"] != missing_packet_id
    ]

    errors = validate_digest(digest)

    assert f"rollback_references missing source packet {missing_packet_id}" in errors


def test_digest_rejects_enabled_consequential_capability_even_without_original_fixture_mutation() -> None:
    fixture = load_fixture(FIXTURE_PATH)
    digest = build_post_decision_release_readiness_digest(deepcopy(fixture))
    digest["approved_offline_only_capabilities"][0] = {
        "capability_id": "offline.certification",
        "summary": "Certification is enabled.",
        "allowed_now": True,
        "requires_live_network": False,
    }

    errors = validate_digest(digest)

    assert "approved_offline_only_capabilities[0] enables a consequential capability" in errors
