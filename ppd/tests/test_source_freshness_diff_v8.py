from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from ppd.extraction.source_freshness_diff_v8 import (
    assemble_from_fixture_paths,
    assemble_source_freshness_diff_v8,
    validate_source_freshness_diff_v8_packet,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "source_freshness_diff_v8"
MANIFEST_FIXTURE = FIXTURE_DIR / "processor_handoff_dry_run_manifest_v8.json"
PRIOR_REGISTRY_FIXTURE = FIXTURE_DIR / "prior_source_registry_v8.json"


def _valid_intake() -> dict[str, Any]:
    return assemble_from_fixture_paths(MANIFEST_FIXTURE, PRIOR_REGISTRY_FIXTURE)


def test_source_freshness_diff_v8_assembles_expected_rows() -> None:
    intake = _valid_intake()

    assert intake["intake_version"] == "source_freshness_diff_v8"
    assert intake["processor_handoff_manifest_ref"] == "processor-handoff-dry-run-v8-fixture"
    assert intake["prior_source_registry_ref"] == "prior-source-registry-v8-fixture"
    assert intake["input_constraints"]["fixture_first"] is True
    assert intake["input_constraints"]["live_crawl_performed"] is False
    assert intake["input_constraints"]["raw_artifacts_downloaded"] is False
    assert intake["input_constraints"]["devhub_opened"] is False
    assert intake["input_constraints"]["private_documents_read"] is False
    assert intake["input_constraints"]["official_action_completed"] is False
    assert intake["input_constraints"]["legal_or_permitting_guarantees_made"] is False
    assert intake["input_constraints"]["active_mutation_flags"] is False

    changed_ids = {row["source_id"] for row in intake["changed_source_hash_rows"]}
    assert changed_ids == {"ppd-new-forms-index", "ppd-online-tools"}

    unchanged_ids = {row["source_id"] for row in intake["unchanged_source_rows"]}
    assert unchanged_ids == {"ppd-single-pdf"}

    added_links = {(row["source_id"], row["url"]) for row in intake["added_link_observations"]}
    assert added_links == {
        (
            "ppd-new-forms-index",
            "https://www.portland.gov/ppd/documents/sample-public-form/download",
        ),
        (
            "ppd-online-tools",
            "https://www.portland.gov/ppd/get-permit/apply-permits",
        ),
    }

    removed_links = {(row["source_id"], row["url"]) for row in intake["removed_link_observations"]}
    assert removed_links == {
        ("ppd-online-tools", "https://www.portland.gov/ppd/old-public-guide")
    }

    citation_refs = {row["citation_placeholder"] for row in intake["affected_citation_placeholders"]}
    assert "citation:ppd-online-tools:devhub-overview" in citation_refs
    assert "citation:ppd-new-forms-index:forms-index" in citation_refs
    assert "citation:ppd-payment-guide:fee-payment" in citation_refs

    candidate_refs = {
        row["candidate_ref"]
        for row in intake["downstream_requirement_reextraction_candidate_refs"]
    }
    assert "candidate:online-tools:devhub-services" in candidate_refs
    assert "candidate:forms-index:document-requirements" in candidate_refs
    assert "candidate:payment-guide:financial-action-gate" in candidate_refs

    hold_codes = {row["hold_code"] for row in intake["reviewer_hold_notes"]}
    assert hold_codes == {
        "new_source_in_dry_run_manifest_v8",
        "source_absent_from_dry_run_manifest_v8",
    }

    assert intake["offline_validation_commands"] == [
        ["python3", "-m", "py_compile", "ppd/extraction/source_freshness_diff_v8.py"],
        ["python3", "-m", "pytest", "ppd/tests/test_source_freshness_diff_v8.py"],
        ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
    ]


@pytest.mark.parametrize(
    "field, message",
    [
        ("processor_handoff_manifest_ref", "processor_handoff_manifest_ref"),
        ("prior_source_registry_ref", "prior_source_registry_ref"),
        ("changed_source_hash_rows", "changed-source hash rows"),
        ("unchanged_source_rows", "unchanged-source rows"),
        ("added_link_observations", "added link observations"),
        ("removed_link_observations", "removed link observations"),
        ("affected_citation_placeholders", "affected citation placeholders"),
        (
            "downstream_requirement_reextraction_candidate_refs",
            "downstream requirement re-extraction candidate references",
        ),
        ("reviewer_hold_notes", "reviewer hold notes"),
        ("offline_validation_commands", "validation commands"),
    ],
)
def test_source_freshness_diff_v8_rejects_missing_required_packet_fields(
    field: str,
    message: str,
) -> None:
    intake = _valid_intake()
    intake[field] = [] if isinstance(intake[field], list) else ""

    with pytest.raises(ValueError, match=message):
        validate_source_freshness_diff_v8_packet(intake)


def test_source_freshness_diff_v8_rejects_non_dry_run_manifest() -> None:
    manifest = {
        "manifest_version": "8",
        "manifest_id": "bad-non-dry-run",
        "dry_run": False,
        "sources": [],
    }
    registry = {"registry_version": "8", "registry_id": "registry", "sources": []}

    with pytest.raises(ValueError, match="dry_run"):
        assemble_source_freshness_diff_v8(manifest, registry)


def test_source_freshness_diff_v8_rejects_missing_manifest_reference() -> None:
    manifest = {
        "manifest_version": "8",
        "dry_run": True,
        "sources": [],
    }
    registry = {"registry_version": "8", "registry_id": "registry", "sources": []}

    with pytest.raises(ValueError, match="processor handoff manifest reference"):
        assemble_source_freshness_diff_v8(manifest, registry)


def test_source_freshness_diff_v8_rejects_missing_registry_reference() -> None:
    manifest = {
        "manifest_version": "8",
        "manifest_id": "manifest",
        "dry_run": True,
        "sources": [],
    }
    registry = {"registry_version": "8", "sources": []}

    with pytest.raises(ValueError, match="source registry reference"):
        assemble_source_freshness_diff_v8(manifest, registry)


@pytest.mark.parametrize(
    "field",
    [
        "archive_artifact_ref",
        "auth_state_path",
        "cookie_jar",
        "downloaded_document_path",
        "har_path",
        "private_artifact_ref",
        "raw_artifact_path",
        "raw_body_path",
        "screenshot_path",
        "session_artifact_ref",
        "session_storage",
        "trace_path",
    ],
)
def test_source_freshness_diff_v8_rejects_live_or_private_artifact_fields(field: str) -> None:
    manifest = {
        "manifest_version": "8",
        "manifest_id": "bad-live-artifact",
        "dry_run": True,
        "sources": [
            {
                "source_id": "bad-live-artifact",
                "canonical_url": "https://www.portland.gov/ppd",
                "content_hash": "sha256:bad",
                field: "/tmp/not-commit-safe",
            }
        ],
    }
    registry = {"registry_version": "8", "registry_id": "registry", "sources": []}

    with pytest.raises(ValueError, match="forbidden live artifact"):
        assemble_source_freshness_diff_v8(manifest, registry)


@pytest.mark.parametrize(
    "field",
    [
        "active_mutation_flags",
        "legal_or_permitting_guarantees_made",
        "live_crawl_performed",
        "official_action_completed",
        "official_action_completion_claimed",
        "private_documents_read",
        "raw_artifacts_downloaded",
        "uploads_or_submissions_performed",
    ],
)
def test_source_freshness_diff_v8_rejects_prohibited_claims_and_active_flags(field: str) -> None:
    intake = _valid_intake()
    intake["input_constraints"] = deepcopy(intake["input_constraints"])
    intake["input_constraints"][field] = True

    with pytest.raises(ValueError, match=field):
        validate_source_freshness_diff_v8_packet(intake)


def test_source_freshness_diff_v8_rejects_unapproved_validation_commands() -> None:
    intake = _valid_intake()
    intake["offline_validation_commands"] = [["python3", "-m", "pytest"]]

    with pytest.raises(ValueError, match="approved offline validation commands"):
        validate_source_freshness_diff_v8_packet(intake)
