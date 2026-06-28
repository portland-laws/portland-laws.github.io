from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from ppd.crawler.public_source_refresh_batch_packet import (
    FORBIDDEN_OPERATIONS,
    SourceRefreshBatchInputs,
    build_public_source_refresh_batch_packet,
    validate_public_source_refresh_batch_inputs,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "public_source_refresh_batch"


def test_builds_ordered_allowlisted_metadata_only_batch_packet() -> None:
    packet = build_public_source_refresh_batch_packet(
        SourceRefreshBatchInputs(
            runbook_candidate_path=FIXTURE_DIR / "source_refresh_runbook_candidate.json",
            coverage_gap_packet_path=FIXTURE_DIR / "source_registry_coverage_gap_packet.json",
            freshness_badge_packet_path=FIXTURE_DIR / "source_freshness_badge_packet.json",
        )
    )

    assert packet["packet_type"] == "ppd_public_source_refresh_batch_packet"
    assert packet["packet_version"] == "1.1"
    assert packet["fixture_first"] is True
    assert packet["side_effect_boundary"] == {
        "network_io_allowed": False,
        "processor_invocation_allowed": False,
        "downloads_allowed": False,
        "schedule_mutation_allowed": False,
        "registry_mutation_allowed": False,
        "raw_body_persistence_allowed": False,
    }

    manifests = packet["batch_manifests"]
    assert [manifest["batch_order"] for manifest in manifests] == [1, 2, 3]
    assert [manifest["source_id"] for manifest in manifests] == [
        "ppd-online-tools-overview",
        "ppd-devhub-faqs",
        "ppd-submit-plans-online",
    ]
    assert packet["blocked_sources"] == []

    for manifest in manifests:
        assert manifest["allowlist_decision"]["allowed"] is True
        assert manifest["robots_policy"]["evidence_ref"]
        assert manifest["policy_evidence"]["evidence_ref"]
        assert manifest["rate_limit_window"]["evidence_ref"]
        assert manifest["expected_metadata_only_delta"]["metadata_only"] is True
        assert manifest["expected_metadata_only_delta"]["registry_mutation_allowed"] is False
        assert manifest["expected_metadata_only_delta"]["schedule_mutation_allowed"] is False
        assert manifest["reviewer_owner_fields"] == {
            "primary_reviewer": "ppd_public_sources_reviewer",
            "backup_reviewer": "ppd_guardrails_reviewer",
            "review_queue": "source-refresh-metadata-only",
        }
        assert manifest["abort_criteria"] == packet["abort_criteria"]
        assert manifest["forbidden_operations"] == list(FORBIDDEN_OPERATIONS)


def test_rejects_non_allowlisted_sources_instead_of_admitting_blocked_batch_entries() -> None:
    with pytest.raises(ValueError, match="outside_allowlist"):
        build_public_source_refresh_batch_packet(
            SourceRefreshBatchInputs(
                runbook_candidate_path=FIXTURE_DIR / "source_refresh_runbook_candidate_with_blocked_source.json",
                coverage_gap_packet_path=FIXTURE_DIR / "source_registry_coverage_gap_packet.json",
                freshness_badge_packet_path=FIXTURE_DIR / "source_freshness_badge_packet.json",
            )
        )


def test_rejects_missing_evidence_owners_abort_criteria_and_rate_limit_windows() -> None:
    runbook = _valid_runbook()
    runbook.pop("reviewer_owner_fields")
    runbook["abort_criteria"] = []
    source = runbook["candidate_sources"][0]
    source["robots_policy"] = {}
    source.pop("policy_evidence")
    source.pop("rate_limit_window")

    errors = validate_public_source_refresh_batch_inputs(runbook)

    assert "reviewer_owner_fields_missing" in errors
    assert "abort_criteria_missing" in errors
    assert "ppd-online-tools-overview:robots_policy_evidence_missing" in errors
    assert "ppd-online-tools-overview:policy_evidence_evidence_missing" in errors
    assert "ppd-online-tools-overview:rate_limit_window_evidence_missing" in errors


def test_rejects_private_authenticated_download_raw_archive_live_execution_and_mutation_claims() -> None:
    runbook = _valid_runbook()
    source = runbook["candidate_sources"][0]
    source.update(
        {
            "canonical_url": "https://devhub.portlandoregon.gov/account/download",
            "source_type": "devhub_authenticated",
            "privacy_classification": "account_scoped",
            "raw_body_ref": "raw-body:not-allowed",
            "archive_artifact_ref": "warc:not-allowed",
            "download_ref": "download:not-allowed",
            "live_fetch_allowed": True,
            "processor_policy": "execute_processor",
            "processor_invocation_allowed": True,
            "schedule_mutation_allowed": True,
            "registry_mutation_allowed": True,
        }
    )

    errors = validate_public_source_refresh_batch_inputs(runbook)

    assert "ppd-online-tools-overview:private_or_authenticated_target" in errors
    assert "ppd-online-tools-overview:private_or_authenticated_source_type" in errors
    assert "ppd-online-tools-overview:private_or_authenticated_privacy_classification" in errors
    assert "ppd-online-tools-overview:download_target_reference" in errors
    assert "ppd-online-tools-overview:forbidden_reference:raw_body_ref" in errors
    assert "ppd-online-tools-overview:forbidden_reference:archive_artifact_ref" in errors
    assert "ppd-online-tools-overview:forbidden_reference:download_ref" in errors
    assert "ppd-online-tools-overview:processor_execution_claim" in errors
    assert "ppd-online-tools-overview:live_fetch_or_processor_execution:live_fetch_allowed" in errors
    assert "ppd-online-tools-overview:live_fetch_or_processor_execution:processor_invocation_allowed" in errors
    assert "ppd-online-tools-overview:active_schedule_or_registry_mutation:schedule_mutation_allowed" in errors
    assert "ppd-online-tools-overview:active_schedule_or_registry_mutation:registry_mutation_allowed" in errors


def _valid_runbook() -> dict[str, object]:
    return deepcopy(json.loads((FIXTURE_DIR / "source_refresh_runbook_candidate.json").read_text(encoding="utf-8")))
