from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pytest

from ppd.agent_readiness.inactive_release_candidate_manifest_v1 import (
    EXACT_OFFLINE_VALIDATION_COMMANDS,
    InactiveReleaseCandidateManifestV1Error,
    assert_valid_inactive_release_candidate_manifest_v1,
    build_inactive_release_candidate_manifest_v1,
    build_inactive_release_candidate_manifest_v1_from_file,
    load_json_object,
    validate_inactive_release_candidate_manifest_v1,
)

FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "inactive_release_candidate_manifest_v1"
    / "synthetic_approved_delta_references_v1.json"
)


def _manifest() -> dict[str, Any]:
    return build_inactive_release_candidate_manifest_v1_from_file(FIXTURE)


def test_builds_inactive_release_candidate_manifest_from_synthetic_approved_deltas() -> None:
    manifest = _manifest()

    assert manifest["packet_type"] == "ppd.inactive_release_candidate_manifest.v1"
    assert manifest["mode"] == "fixture_first_inactive_release_candidate_manifest_only"
    assert manifest["candidate_status"] == "inactive_pending_reviewer_signoff"
    assert manifest["fixture_only"] is True
    assert manifest["candidate_only"] is True
    assert manifest["metadata_only"] is True
    assert manifest["inactive_candidate_summary"] == {
        "summary_id": "inactive-summary:inactive-release-candidate-manifest-20260531-1011-fixture-v1",
        "source_delta_count": 1,
        "requirement_delta_count": 1,
        "process_delta_count": 1,
        "guardrail_delta_count": 1,
        "agent_gap_analysis_delta_count": 1,
        "release_activation_enabled": False,
        "release_promotion_enabled": False,
    }
    assert manifest["exact_offline_validation_commands"] == EXACT_OFFLINE_VALIDATION_COMMANDS
    assert_valid_inactive_release_candidate_manifest_v1(manifest)


def test_manifest_packages_all_delta_reference_types_with_immutable_evidence() -> None:
    manifest = _manifest()

    assert manifest["immutable_evidence_ids"] == [
        "ev:ppd-fixture:agent-gap-missing-license-fact:sha256:5555555555555555555555555555555555555555555555555555555555555555",
        "ev:ppd-fixture:guardrail-exact-confirmation-gate:sha256:4444444444444444444444444444444444444444444444444444444444444444",
        "ev:ppd-fixture:process-upload-staging-stage:sha256:3333333333333333333333333333333333333333333333333333333333333333",
        "ev:ppd-fixture:requirement-save-draft-precondition:sha256:2222222222222222222222222222222222222222222222222222222222222222",
        "ev:ppd-fixture:source-devhub-application-guide:sha256:1111111111111111111111111111111111111111111111111111111111111111",
    ]
    assert set(manifest["delta_references"]) == {
        "source_delta_refs",
        "requirement_delta_refs",
        "process_delta_refs",
        "guardrail_delta_refs",
        "agent_gap_analysis_delta_refs",
    }
    for rows in manifest["delta_references"].values():
        assert rows[0]["candidate_status"] == "inactive_reference_only"
        assert rows[0]["active_mutation"] is False
        assert rows[0]["source_evidence_ids"]


def test_manifest_includes_migration_rollback_notes_and_unsigned_signoff_placeholders() -> None:
    manifest = _manifest()

    assert manifest["migration_notes"][0]["note_id"] == "migration-note-fixture-first-inactive-only"
    assert manifest["migration_notes"][0]["requires_manual_review_before_any_future_activation"] is True
    assert manifest["rollback_notes"][0]["note_id"] == "rollback-note-discard-inactive-candidate-only"
    assert manifest["rollback_notes"][0]["requires_manual_review_before_any_future_activation"] is True
    roles = {placeholder["role"] for placeholder in manifest["reviewer_signoff_placeholders"]}
    assert roles == {
        "source_registry_reviewer",
        "requirement_reviewer",
        "process_model_reviewer",
        "guardrail_reviewer",
        "agent_gap_analysis_reviewer",
        "release_manager",
    }
    for placeholder in manifest["reviewer_signoff_placeholders"]:
        assert placeholder["reviewer"] == ""
        assert placeholder["reviewed_at"] == ""
        assert placeholder["decision"] == "pending_manual_review"
        assert placeholder["notes"] == ""


def test_rejects_unapproved_synthetic_delta_references() -> None:
    packet = copy.deepcopy(load_json_object(FIXTURE))
    packet["source_delta_refs"][0]["approval_status"] = "pending"

    with pytest.raises(InactiveReleaseCandidateManifestV1Error, match="approval_status"):
        build_inactive_release_candidate_manifest_v1(packet)


def test_rejects_non_immutable_evidence_ids() -> None:
    packet = copy.deepcopy(load_json_object(FIXTURE))
    packet["requirement_delta_refs"][0]["source_evidence_ids"] = ["requirement:mutable-local-id"]

    with pytest.raises(InactiveReleaseCandidateManifestV1Error, match="immutable evidence id"):
        build_inactive_release_candidate_manifest_v1(packet)


@pytest.mark.parametrize(
    "section",
    [
        "source_delta_refs",
        "requirement_delta_refs",
        "process_delta_refs",
        "guardrail_delta_refs",
        "agent_gap_analysis_delta_refs",
    ],
)
def test_rejects_missing_delta_reference_sections(section: str) -> None:
    manifest = _manifest()
    manifest["delta_references"][section] = []

    result = validate_inactive_release_candidate_manifest_v1(manifest)

    assert not result.valid
    assert f"delta_references.{section} must be a non-empty list" in "; ".join(result.problems)


def test_rejects_missing_migration_notes_rollback_notes_and_validation_commands() -> None:
    manifest = _manifest()
    manifest["migration_notes"] = []
    manifest["rollback_notes"] = []
    manifest["exact_offline_validation_commands"] = []

    result = validate_inactive_release_candidate_manifest_v1(manifest)

    problems = "; ".join(result.problems)
    assert not result.valid
    assert "migration_notes must be a non-empty list" in problems
    assert "rollback_notes must be a non-empty list" in problems
    assert "exact_offline_validation_commands must match" in problems


def test_rejects_signed_or_decided_reviewer_placeholders() -> None:
    manifest = _manifest()
    manifest["reviewer_signoff_placeholders"][0]["reviewer"] = "fixture reviewer"
    manifest["reviewer_signoff_placeholders"][0]["decision"] = "approved"

    result = validate_inactive_release_candidate_manifest_v1(manifest)

    problems = "; ".join(result.problems)
    assert not result.valid
    assert "decision must be pending_manual_review" in problems
    assert "must remain an unsigned reviewer placeholder" in problems


@pytest.mark.parametrize(
    "flag",
    [
        "active_source_mutation",
        "active_requirement_mutation",
        "active_process_mutation",
        "active_guardrail_mutation",
        "active_agent_gap_analysis_mutation",
        "active_prompt_mutation",
        "active_contract_mutation",
        "active_archive_mutation",
        "active_document_mutation",
        "active_devhub_surface_mutation",
        "active_surface_mutation",
        "active_crawler_mutation",
        "active_daemon_state_mutation",
    ],
)
def test_rejects_side_effect_boundary_mutation_flags(flag: str) -> None:
    manifest = _manifest()
    manifest["side_effect_boundaries"][flag] = True

    result = validate_inactive_release_candidate_manifest_v1(manifest)

    assert not result.valid
    assert f"side_effect_boundaries.{flag} must be false" in "; ".join(result.problems)


@pytest.mark.parametrize(
    ("key", "value", "expected"),
    [
        ("browser_state_path", "state.json", "must not include private"),
        ("raw_crawl_output", "raw html", "must not include private"),
        ("downloaded_document_path", "permit.pdf", "must not include private"),
        ("live_note", "live crawl completed", "must not claim live execution"),
        ("promotion_note", "release promoted", "must not claim live execution"),
        ("action_note", "submit permit", "must not include official-action language"),
    ],
)
def test_rejects_private_artifacts_live_claims_promotion_claims_and_official_action_language(
    key: str, value: Any, expected: str
) -> None:
    manifest = _manifest()
    manifest[key] = value

    result = validate_inactive_release_candidate_manifest_v1(manifest)

    assert not result.valid
    assert expected in "; ".join(result.problems)
