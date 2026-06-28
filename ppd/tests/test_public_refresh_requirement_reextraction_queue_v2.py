from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from ppd.agent_readiness.public_refresh_requirement_reextraction_queue_v2 import (
    EXACT_OFFLINE_VALIDATION_COMMANDS,
    build_public_refresh_requirement_reextraction_queue_v2,
    build_queue_from_fixture,
    load_synthetic_normalized_document_extraction_readiness_rows,
    validate_public_refresh_requirement_reextraction_queue_v2,
)

FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "public_refresh_requirement_reextraction_queue_v2"
    / "synthetic_normalized_document_extraction_readiness_rows.json"
)


def _valid_row() -> dict[str, object]:
    return dict(load_synthetic_normalized_document_extraction_readiness_rows(FIXTURE_PATH)[0])


def test_builds_fixture_first_public_refresh_requirement_reextraction_queue_v2() -> None:
    queue = build_queue_from_fixture(FIXTURE_PATH)

    assert queue["queue_version"] == "public-refresh-requirement-reextraction-queue-v2"
    assert queue["mode"] == "fixture_first_offline_review_only"
    assert queue["input_contract"] == "synthetic_normalized_document_extraction_readiness_rows_only"
    assert queue["input_row_count"] == 1
    assert queue["candidate_count"] == 1
    assert queue["readiness_packet_refs"] == ["normalized-extraction-readiness::ppd-devhub-faq"]
    assert queue["affected_requirement_ids"] == ["pending-requirement-devhub-account-service-review"]
    assert queue["affected_process_model_ids"] == ["process-devhub-account-setup", "process-online-permit-application"]
    assert queue["affected_guardrail_bundle_ids"] == ["guardrail-devhub-attended-login", "guardrail-online-permit-application"]
    assert queue["exact_offline_validation_commands"] == [list(command) for command in EXACT_OFFLINE_VALIDATION_COMMANDS]
    assert queue["attestations"]["fixture_first"] is True
    assert queue["attestations"]["no_live_extraction"] is True
    assert queue["attestations"]["no_devhub_access"] is True
    assert queue["attestations"]["no_active_requirement_mutation"] is True

    candidate = queue["requirement_reextraction_candidates"][0]
    assert candidate["candidate_requirement_update"]["requirement_node_update_placeholder"] is True
    assert candidate["candidate_requirement_update"]["requirement_id"] == "pending-requirement-devhub-account-service-review"
    assert candidate["candidate_requirement_update"]["activation_allowed"] is False
    assert candidate["human_review_status"] == "needs_human_review"
    assert candidate["formalization_hold"] == "hold_until_source_evidence_reviewed"
    assert candidate["stale_evidence"] is True
    assert candidate["conflicting_evidence"] is False
    assert candidate["mutates_active_requirements"] is False
    assert candidate["mutates_active_process_models"] is False
    assert candidate["mutates_active_guardrails"] is False
    assert candidate["active_mutation"] is False


def test_rejects_empty_requirement_reextraction_rows() -> None:
    with pytest.raises(ValueError, match="at least one requirement re-extraction readiness row"):
        build_public_refresh_requirement_reextraction_queue_v2([])


@pytest.mark.parametrize(
    "missing_key",
    [
        "readiness_packet_ref",
        "normalized_document_id_placeholder",
        "candidate_requirement_id",
        "candidate_requirement_type",
        "candidate_requirement_action",
        "candidate_requirement_object",
        "affected_process_model_ids",
        "affected_guardrail_bundle_ids",
        "source_evidence_placeholder_mappings",
        "human_review_status",
        "formalization_hold",
        "stale_evidence",
        "conflicting_evidence",
        "rollback_note",
        "reviewer_note",
    ],
)
def test_rejects_missing_required_reextraction_metadata(missing_key: str) -> None:
    row = _valid_row()
    row.pop(missing_key)

    with pytest.raises(ValueError, match=missing_key):
        build_public_refresh_requirement_reextraction_queue_v2([row])


@pytest.mark.parametrize(
    "flag",
    [
        "live_extraction",
        "live_crawl",
        "document_download",
        "raw_output_stored",
        "devhub_opened",
        "active_requirement_mutation",
        "active_process_model_mutation",
        "active_guardrail_mutation",
        "active_mutation",
        "official_action_completed",
        "legal_or_permitting_guarantee",
    ],
)
def test_rejects_active_external_or_official_action_flags(flag: str) -> None:
    row = _valid_row()
    row[flag] = True

    with pytest.raises(ValueError, match=flag):
        build_public_refresh_requirement_reextraction_queue_v2([row])


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
        build_public_refresh_requirement_reextraction_queue_v2([row])


@pytest.mark.parametrize(
    "claim",
    [
        "live extraction completed",
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
    row["reviewer_note"] = claim

    with pytest.raises(ValueError, match="prohibited claim phrase"):
        build_public_refresh_requirement_reextraction_queue_v2([row])


@pytest.mark.parametrize(
    "queue_key",
    [
        "readiness_packet_refs",
        "affected_requirement_ids",
        "affected_process_model_ids",
        "affected_guardrail_bundle_ids",
        "requirement_reextraction_candidates",
        "source_evidence_placeholder_mappings",
        "human_review_statuses",
        "formalization_holds",
        "stale_or_conflicting_evidence_flags",
        "rollback_notes",
    ],
)
def test_queue_validator_rejects_missing_output_sections(queue_key: str) -> None:
    queue = build_queue_from_fixture(FIXTURE_PATH)
    queue[queue_key] = []

    with pytest.raises(ValueError, match=queue_key):
        validate_public_refresh_requirement_reextraction_queue_v2(queue)


def test_queue_validator_rejects_missing_validation_commands() -> None:
    queue = build_queue_from_fixture(FIXTURE_PATH)
    queue["exact_offline_validation_commands"] = []

    with pytest.raises(ValueError, match="exact offline validation commands"):
        validate_public_refresh_requirement_reextraction_queue_v2(queue)


@pytest.mark.parametrize(
    ("nested_key", "expected"),
    [
        ("requirement_node_update_placeholder", "requirement_node_update_placeholder"),
        ("requirement_id", "requirement_id"),
        ("requirement_type", "requirement_type"),
        ("action", "action"),
        ("object", "object"),
    ],
)
def test_queue_validator_rejects_missing_candidate_requirement_update_placeholders(
    nested_key: str,
    expected: str,
) -> None:
    queue = build_queue_from_fixture(FIXTURE_PATH)
    update = queue["requirement_reextraction_candidates"][0]["candidate_requirement_update"]
    update.pop(nested_key)

    with pytest.raises(ValueError, match=expected):
        validate_public_refresh_requirement_reextraction_queue_v2(queue)


@pytest.mark.parametrize(
    "candidate_key",
    [
        "normalized_document_id_placeholder",
        "affected_process_model_ids",
        "affected_guardrail_bundle_ids",
        "source_evidence_placeholder_mappings",
        "human_review_status",
        "formalization_hold",
        "stale_evidence",
        "conflicting_evidence",
        "rollback_note",
    ],
)
def test_queue_validator_rejects_missing_candidate_review_controls(candidate_key: str) -> None:
    queue = build_queue_from_fixture(FIXTURE_PATH)
    queue["requirement_reextraction_candidates"][0].pop(candidate_key)

    with pytest.raises(ValueError, match=candidate_key):
        validate_public_refresh_requirement_reextraction_queue_v2(queue)


@pytest.mark.parametrize(
    "mapping_key",
    [
        "source_evidence_id_placeholder",
        "citation_span_placeholder",
    ],
)
def test_queue_validator_rejects_missing_source_evidence_placeholder_mapping_fields(mapping_key: str) -> None:
    queue = build_queue_from_fixture(FIXTURE_PATH)
    queue["source_evidence_placeholder_mappings"][0].pop(mapping_key)

    with pytest.raises(ValueError, match=mapping_key):
        validate_public_refresh_requirement_reextraction_queue_v2(queue)


def test_queue_validator_rejects_candidate_mutation_claims_after_build() -> None:
    queue = build_queue_from_fixture(FIXTURE_PATH)
    mutated_queue = deepcopy(queue)
    mutated_queue["requirement_reextraction_candidates"][0]["mutates_active_guardrails"] = True

    with pytest.raises(ValueError, match="mutates_active_guardrails"):
        validate_public_refresh_requirement_reextraction_queue_v2(mutated_queue)


def test_queue_validator_rejects_active_mutation_flag_after_build() -> None:
    queue = build_queue_from_fixture(FIXTURE_PATH)
    mutated_queue = deepcopy(queue)
    mutated_queue["requirement_reextraction_candidates"][0]["active_mutation"] = True

    with pytest.raises(ValueError, match="active_mutation"):
        validate_public_refresh_requirement_reextraction_queue_v2(mutated_queue)


def test_queue_validator_rejects_candidate_requirement_update_activation_after_build() -> None:
    queue = build_queue_from_fixture(FIXTURE_PATH)
    mutated_queue = deepcopy(queue)
    mutated_queue["requirement_reextraction_candidates"][0]["candidate_requirement_update"]["activation_allowed"] = True

    with pytest.raises(ValueError, match="activation_allowed"):
        validate_public_refresh_requirement_reextraction_queue_v2(mutated_queue)


def test_rejects_non_placeholder_requirement_and_evidence_identifiers() -> None:
    row = _valid_row()
    row["candidate_requirement_id"] = "requirement-active-001"

    with pytest.raises(ValueError, match="candidate_requirement_id"):
        build_public_refresh_requirement_reextraction_queue_v2([row])

    evidence_row = _valid_row()
    mappings = list(evidence_row["source_evidence_placeholder_mappings"])
    mappings[0] = dict(mappings[0])
    mappings[0]["source_evidence_id_placeholder"] = "evidence-active-001"
    evidence_row["source_evidence_placeholder_mappings"] = mappings

    with pytest.raises(ValueError, match="source_evidence_id_placeholder"):
        build_public_refresh_requirement_reextraction_queue_v2([evidence_row])
