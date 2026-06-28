from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from ppd.agent_readiness.downstream_requirement_reextraction_queue_v7 import (
    EXACT_OFFLINE_VALIDATION_COMMANDS,
    build_downstream_requirement_reextraction_queue_v7,
    build_downstream_requirement_reextraction_queue_v7_from_fixture,
    validate_downstream_requirement_reextraction_queue_v7,
)
from ppd.source_freshness_diff_v7 import build_source_freshness_diff_v7_from_paths

FIXTURES = Path(__file__).parent / "fixtures" / "source_freshness_diff_v7"
QUEUE_FIXTURES = Path(__file__).parent / "fixtures" / "downstream_requirement_reextraction_queue_v7"

REQUIRED_SECTIONS = (
    "work_packet_refs",
    "reextraction_queue_refs",
    "source_fixture_refs",
    "normalized_document_fixture_refs",
    "source_to_extraction_work_rows",
    "changed_section_placeholders",
    "extraction_prompt_rows",
    "source_evidence_anchor_placeholders",
    "source_evidence_continuity_checks",
    "citation_span_refresh_expectations",
    "requirement_family_hints",
    "candidate_requirement_node_placeholders",
    "candidate_requirement_add_rows",
    "candidate_requirement_update_rows",
    "candidate_requirement_deprecate_rows",
    "permit_type_mapping_placeholders",
    "process_stage_mapping_placeholders",
    "confidence_and_human_review_placeholders",
    "conflict_and_stale_evidence_review_flags",
    "unsupported_path_notes",
    "stale_citation_replacement_reminders",
    "stale_evidence_hold_carry_forward_rows",
    "reviewer_assignment_placeholders",
)


def _diff_packet() -> dict[str, Any]:
    return build_source_freshness_diff_v7_from_paths(
        FIXTURES / "processor_handoff_manifest_v7.json",
        FIXTURES / "prior_metadata_v7.json",
        FIXTURES / "current_metadata_v7.json",
    )


def _queue() -> dict[str, Any]:
    return build_downstream_requirement_reextraction_queue_v7(_diff_packet())


def test_builds_downstream_rows_from_source_freshness_diff_intake_v7_fixture() -> None:
    queue = _queue()

    assert queue["schema"] == "ppd.downstream_requirement_reextraction_queue.v7"
    assert queue["consumes_only"] == {"source_freshness_diff_intake_v7_fixtures": True}
    assert queue["boundaries"]["live_crawl_executed"] is False
    assert queue["boundaries"]["devhub_opened"] is False
    assert queue["boundaries"]["active_mutation"] is False
    assert queue["boundaries"]["official_action_completed"] is False
    assert queue["exact_offline_validation_commands"] == EXACT_OFFLINE_VALIDATION_COMMANDS

    changed_ids = {"ppd-submit-plans-online", "ppd-devhub-faq"}
    for section in REQUIRED_SECTIONS:
        if section == "source_fixture_refs":
            assert queue[section][0]["fixture_role"] == "source_freshness_diff_intake_v7"
        else:
            assert {row["source_id"] for row in queue[section]} == changed_ids


def test_builds_from_fixture_refs_without_live_crawl_or_downloads() -> None:
    queue = build_downstream_requirement_reextraction_queue_v7_from_fixture(QUEUE_FIXTURES / "fixture_refs.json")

    assert queue["source_fixture_refs"][0]["fixture_role"] == "source_freshness_diff_intake_v7"
    assert queue["boundaries"]["raw_artifacts_downloaded"] is False
    assert queue["boundaries"]["downloaded_documents_persisted"] is False
    assert queue["boundaries"]["private_session_or_auth_artifacts_created"] is False
    assert queue["boundaries"]["private_documents_read"] is False


def test_candidate_set_contains_work_packet_mapping_review_and_change_rows() -> None:
    queue = _queue()

    for row in queue["work_packet_refs"]:
        assert row["packet_status"] == "work_packet_reference_required_before_extraction"
        assert row["work_packet_ref_id"]
    for section, kind in (
        ("candidate_requirement_add_rows", "add"),
        ("candidate_requirement_update_rows", "update"),
        ("candidate_requirement_deprecate_rows", "deprecate"),
    ):
        for row in queue[section]:
            assert row["candidate_change_kind"] == kind
            assert row["candidate_status"] == "placeholder_pending_fixture_backed_reviewer_decision"
            assert row["active_mutation_allowed"] is False
    for row in queue["source_evidence_continuity_checks"]:
        assert row["continuity_check_required"] is True
        assert row["continuity_status"] == "pending_reviewer_trace_from_prior_to_current_fixture"
    for row in queue["permit_type_mapping_placeholders"]:
        assert row["mapping_status"] == "placeholder_pending_fixture_backed_permit_type_review"
        assert row["permit_type_placeholder"]
    for row in queue["process_stage_mapping_placeholders"]:
        assert row["mapping_status"] == "placeholder_pending_fixture_backed_process_stage_review"
        assert row["process_stage_placeholder"]
    for row in queue["conflict_and_stale_evidence_review_flags"]:
        assert row["conflict_review_required"] is True
        assert row["stale_evidence_review_required"] is True
        assert row["review_status"] == "pending_reviewer_disposition_before_release"


def test_work_rows_are_offline_only_and_review_queued() -> None:
    queue = _queue()

    for row in queue["source_to_extraction_work_rows"]:
        assert row["work_status"] == "queued_for_fixture_backed_reextraction_review"
        assert row["requires_live_crawl"] is False
        assert row["requires_devhub"] is False
        assert row["requires_private_document_access"] is False
        assert row["active_mutation_allowed"] is False
        assert row["official_action_completed"] is False


def test_required_reextraction_placeholders_are_present() -> None:
    queue = _queue()

    for row in queue["candidate_requirement_node_placeholders"]:
        assert row["requirement_node_type"] == "RequirementNode"
        assert row["node_status"] == "candidate_placeholder_pending_fixture_backed_extraction"
        assert row["formalization_status_placeholder"] == "not_formalized"
    for row in queue["confidence_and_human_review_placeholders"]:
        assert row["confidence_placeholder"] == "pending_fixture_backed_review"
        assert row["human_review_status_placeholder"] == "human_review_required_before_release"
    for row in queue["reviewer_assignment_placeholders"]:
        assert row["owner_placeholder"]
        assert row["assignment_status"] == "placeholder_unassigned"


@pytest.mark.parametrize("section", REQUIRED_SECTIONS)
def test_validator_rejects_missing_required_sections(section: str) -> None:
    queue = _queue()
    queue[section] = []

    with pytest.raises(ValueError, match=section):
        validate_downstream_requirement_reextraction_queue_v7(queue)


def test_validator_rejects_section_coverage_mismatch() -> None:
    queue = _queue()
    queue["citation_span_refresh_expectations"] = queue["citation_span_refresh_expectations"][:1]

    with pytest.raises(ValueError, match="citation_span_refresh_expectations"):
        validate_downstream_requirement_reextraction_queue_v7(queue)


@pytest.mark.parametrize(
    ("section", "field", "value", "message"),
    [
        ("source_to_extraction_work_rows", "requires_live_crawl", True, "forbidden live/private/mutating claim"),
        ("source_to_extraction_work_rows", "requires_devhub", True, "forbidden live/private/mutating claim"),
        ("source_to_extraction_work_rows", "active_mutation_allowed", True, "forbidden live/private/mutating claim"),
        ("source_to_extraction_work_rows", "official_action_completed", True, "forbidden live/private/mutating claim"),
        ("candidate_requirement_add_rows", "active_mutation_allowed", True, "forbidden live/private/mutating claim"),
    ],
)
def test_validator_rejects_live_or_mutating_claims(section: str, field: str, value: bool, message: str) -> None:
    queue = _queue()
    queue[section][0][field] = value

    with pytest.raises(ValueError, match=message):
        validate_downstream_requirement_reextraction_queue_v7(queue)


@pytest.mark.parametrize("field", ["raw_html_ref", "downloaded_document_path", "auth_state", "trace_path", "session_state_path"])
def test_validator_rejects_downloaded_raw_private_session_or_auth_artifacts(field: str) -> None:
    queue = _queue()
    queue["source_to_extraction_work_rows"][0][field] = "artifact.json"

    with pytest.raises(ValueError, match="forbidden artifact/private/session field"):
        validate_downstream_requirement_reextraction_queue_v7(queue)


def test_validator_rejects_validation_command_drift() -> None:
    queue = _queue()
    queue["exact_offline_validation_commands"] = [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]]

    with pytest.raises(ValueError, match="validation commands"):
        validate_downstream_requirement_reextraction_queue_v7(queue)


@pytest.mark.parametrize(
    ("section", "field", "replacement", "message"),
    [
        ("work_packet_refs", "work_packet_ref_id", "", "work_packet_ref_id"),
        ("source_evidence_continuity_checks", "continuity_check_required", False, "continuity checks"),
        ("source_evidence_continuity_checks", "prior_citation_placeholder_id", "", "prior_citation_placeholder_id"),
        ("candidate_requirement_node_placeholders", "formalization_status_placeholder", "", "formalization status placeholder"),
        ("candidate_requirement_add_rows", "candidate_change_kind", "update", "add candidate row"),
        ("candidate_requirement_update_rows", "candidate_change_kind", "add", "update candidate row"),
        ("candidate_requirement_deprecate_rows", "candidate_change_kind", "add", "deprecate candidate row"),
        ("permit_type_mapping_placeholders", "permit_type_placeholder", "", "permit_type_placeholder"),
        ("process_stage_mapping_placeholders", "process_stage_placeholder", "", "process_stage_placeholder"),
        ("conflict_and_stale_evidence_review_flags", "conflict_review_required", False, "conflict review flag"),
        ("conflict_and_stale_evidence_review_flags", "stale_evidence_review_required", False, "stale-evidence review flag"),
        ("reviewer_assignment_placeholders", "owner_placeholder", "", "owner_placeholder"),
    ],
)
def test_validator_rejects_missing_required_candidate_set_fields(
    section: str, field: str, replacement: object, message: str
) -> None:
    queue = _queue()
    queue[section][0][field] = replacement

    with pytest.raises(ValueError, match=message):
        validate_downstream_requirement_reextraction_queue_v7(queue)


def test_validator_rejects_legal_or_permitting_guarantees() -> None:
    queue = _queue()
    queue["legal_or_permitting_guarantees"] = ["guaranteed permit"]

    with pytest.raises(ValueError, match="legal or permitting guarantees"):
        validate_downstream_requirement_reextraction_queue_v7(queue)


@pytest.mark.parametrize("field", ["active_guardrail_mutation", "official_action_completed", "active_mutation"])
def test_validator_rejects_forbidden_boundary_claims(field: str) -> None:
    queue = _queue()
    queue["boundaries"] = deepcopy(queue["boundaries"])
    queue["boundaries"][field] = True

    with pytest.raises(ValueError, match="boundaries"):
        validate_downstream_requirement_reextraction_queue_v7(queue)


def test_builder_rejects_diff_without_required_requirement_placeholder() -> None:
    diff = _diff_packet()
    diff["affected_requirement_placeholders"] = diff["affected_requirement_placeholders"][:1]

    with pytest.raises(ValueError, match="affected_requirement_placeholders"):
        build_downstream_requirement_reextraction_queue_v7(diff)


def test_validator_rejects_reviewer_assignment_status_drift() -> None:
    queue = deepcopy(_queue())
    queue["reviewer_assignment_placeholders"][0]["assignment_status"] = "assigned"

    with pytest.raises(ValueError, match="placeholder"):
        validate_downstream_requirement_reextraction_queue_v7(queue)
