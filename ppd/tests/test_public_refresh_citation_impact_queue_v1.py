from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from ppd.agent_readiness.public_refresh_citation_impact_queue_v1 import (
    EXACT_OFFLINE_VALIDATION_COMMANDS,
    build_public_refresh_citation_impact_queue,
    build_queue_from_fixture,
    load_synthetic_metadata_manifest_dry_run_plan_rows,
    validate_public_refresh_citation_impact_queue,
)

FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "public_refresh_citation_impact_queue_v1"
    / "synthetic_metadata_manifest_dry_run_plan.json"
)


def _valid_row() -> dict[str, object]:
    return dict(load_synthetic_metadata_manifest_dry_run_plan_rows(FIXTURE_PATH)[0])


def test_builds_fixture_first_public_refresh_citation_impact_queue() -> None:
    queue = build_queue_from_fixture(FIXTURE_PATH)

    assert queue["queue_version"] == "public-refresh-citation-impact-queue-v1"
    assert queue["mode"] == "fixture_first_offline_review_only"
    assert queue["input_row_count"] == 1
    assert queue["candidate_count"] == 1
    assert queue["metadata_dry_run_reference_ids"] == ["metadata-dry-run-ref-001"]
    assert queue["exact_offline_validation_commands"] == [list(command) for command in EXACT_OFFLINE_VALIDATION_COMMANDS]
    assert queue["attestations"]["no_live_crawling"] is True
    assert queue["attestations"]["no_devhub_access"] is True
    assert queue["attestations"]["no_active_requirement_mutation"] is True
    assert queue["attestations"]["no_legal_or_permitting_guarantees"] is True

    candidate = queue["citation_span_refresh_candidates"][0]
    assert candidate["metadata_dry_run_reference_id"] == "metadata-dry-run-ref-001"
    assert candidate["citation_span_ids"] == ["span-devhub-faq-001"]
    assert candidate["affected_requirement_ids"] == ["requirement-devhub-account-service-review"]
    assert candidate["affected_process_model_ids"] == ["process-devhub-account-setup"]
    assert candidate["affected_guardrail_bundle_ids"] == ["guardrail-devhub-attended-login"]
    assert candidate["requires_live_crawl"] is False
    assert candidate["opens_devhub"] is False
    assert candidate["mutates_active_requirements"] is False
    assert candidate["official_action_completed"] is False


def test_rejects_empty_queue_without_citation_span_refresh_candidates() -> None:
    with pytest.raises(ValueError, match="at least one citation-span refresh candidate"):
        build_public_refresh_citation_impact_queue([])


@pytest.mark.parametrize(
    "missing_key, match",
    [
        ("metadata_dry_run_reference_id", "metadata_dry_run_reference_id"),
        ("citation_span_ids", "citation_span_ids"),
        ("affected_requirement_ids", "affected_requirement_ids"),
        ("affected_process_model_ids", "affected_process_model_ids"),
        ("affected_guardrail_bundle_ids", "affected_guardrail_bundle_ids"),
        ("stale_source_hold_impact", "stale_source_hold_impact"),
        ("extraction_confidence_placeholder", "extraction_confidence_placeholder"),
        ("human_review_route", "human_review_route"),
        ("rollback_note", "rollback_note"),
    ],
)
def test_rejects_missing_required_review_metadata(missing_key: str, match: str) -> None:
    row = _valid_row()
    row.pop(missing_key)

    with pytest.raises(ValueError, match=match):
        build_public_refresh_citation_impact_queue([row])


@pytest.mark.parametrize(
    "flag",
    [
        "live_extraction",
        "live_crawl",
        "document_download",
        "raw_output_stored",
        "devhub_opened",
        "active_mutation",
        "active_requirement_mutation",
        "active_process_model_mutation",
        "active_guardrail_mutation",
        "official_action_completed",
        "legal_or_permitting_guarantee",
    ],
)
def test_rejects_active_or_external_action_flags(flag: str) -> None:
    row = _valid_row()
    row[flag] = True

    with pytest.raises(ValueError, match=flag):
        build_public_refresh_citation_impact_queue([row])


@pytest.mark.parametrize(
    "key",
    [
        "private_artifact",
        "raw_output",
        "downloaded_document",
        "downloaded_pdf",
        "raw_crawl_output",
        "session_state",
        "browser_trace",
        "local_path",
    ],
)
def test_rejects_private_raw_downloaded_or_runtime_artifact_keys(key: str) -> None:
    row = _valid_row()
    row[key] = "not allowed"

    with pytest.raises(ValueError, match="runtime, raw-output, downloaded, or private key"):
        build_public_refresh_citation_impact_queue([row])


@pytest.mark.parametrize(
    "claim",
    [
        "live crawl completed",
        "DevHub opened",
        "active requirement mutation",
        "active process model mutation",
        "active guardrail mutation",
        "official action completed",
        "permit guaranteed",
        "legal advice",
        "raw output stored",
        "downloaded document",
    ],
)
def test_rejects_prohibited_claim_text(claim: str) -> None:
    row = _valid_row()
    row["dry_run_evidence"] = claim

    with pytest.raises(ValueError, match="prohibited claim phrase"):
        build_public_refresh_citation_impact_queue([row])


@pytest.mark.parametrize(
    "queue_key, match",
    [
        ("metadata_dry_run_reference_ids", "metadata dry-run reference ids"),
        ("citation_span_refresh_candidates", "citation-span refresh candidates"),
        ("affected_requirement_ids", "affected requirement identifiers"),
        ("affected_process_model_ids", "affected process-model identifiers"),
        ("affected_guardrail_bundle_ids", "affected guardrail identifiers"),
        ("stale_source_hold_impacts", "stale-source hold impacts"),
        ("human_review_routes", "human-review routing"),
        ("rollback_notes", "rollback notes"),
    ],
)
def test_queue_validator_rejects_missing_output_sections(queue_key: str, match: str) -> None:
    queue = build_queue_from_fixture(FIXTURE_PATH)
    queue[queue_key] = []

    with pytest.raises(ValueError, match=match):
        validate_public_refresh_citation_impact_queue(queue)


def test_queue_validator_rejects_missing_validation_commands() -> None:
    queue = build_queue_from_fixture(FIXTURE_PATH)
    queue["exact_offline_validation_commands"] = []

    with pytest.raises(ValueError, match="exact offline validation commands"):
        validate_public_refresh_citation_impact_queue(queue)


def test_queue_validator_rejects_candidate_mutation_claims_after_build() -> None:
    queue = build_queue_from_fixture(FIXTURE_PATH)
    mutated_queue = deepcopy(queue)
    mutated_queue["citation_span_refresh_candidates"][0]["mutates_active_guardrails"] = True

    with pytest.raises(ValueError, match="mutates_active_guardrails"):
        validate_public_refresh_citation_impact_queue(mutated_queue)
