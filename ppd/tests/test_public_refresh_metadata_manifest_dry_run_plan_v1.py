from __future__ import annotations

import json
from pathlib import Path

import pytest

from ppd.validation.public_refresh_metadata_manifest_dry_run_plan_v1 import (
    PublicRefreshMetadataManifestDryRunPlanV1Error,
    collect_public_refresh_metadata_manifest_dry_run_plan_v1_issues,
    validate_public_refresh_metadata_manifest_dry_run_plan_v1,
)

FIXTURES = Path(__file__).parent / "fixtures" / "public_refresh_metadata_manifest_dry_run_plan_v1"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_accepts_commit_safe_public_dry_run_plan() -> None:
    validate_public_refresh_metadata_manifest_dry_run_plan_v1(_load("valid.json"))


@pytest.mark.parametrize(
    ("field", "expected_code"),
    [
        ("preflight_checklist_references", "missing_preflight_checklist_references"),
        ("source_registry_placeholder_rows", "missing_source_registry_placeholder_rows"),
        ("archive_manifest_placeholder_rows", "missing_archive_manifest_placeholder_rows"),
        ("redirect_chain_placeholders", "missing_redirect_chain_placeholders"),
        ("http_status_placeholders", "missing_http_status_placeholders"),
        ("content_type_expectations", "missing_content_type_expectations"),
        ("content_hash_placeholder_policy", "missing_content_hash_placeholder_policy"),
        ("freshness_status_impacts", "missing_freshness_status_impacts"),
        ("skipped_reason_handling", "missing_skipped_reason_handling"),
        ("reviewer_holds", "missing_reviewer_holds"),
        ("rollback_notes", "missing_rollback_notes"),
        ("validation_commands", "missing_validation_commands"),
    ],
)
def test_rejects_missing_required_public_dry_run_sections(field: str, expected_code: str) -> None:
    plan = _load("valid.json")
    plan.pop(field)

    issues = collect_public_refresh_metadata_manifest_dry_run_plan_v1_issues(plan)

    assert expected_code in {issue.code for issue in issues}


def test_rejects_archive_rows_without_required_metadata_placeholders() -> None:
    plan = _load("valid.json")
    plan["archive_manifest_placeholder_rows"] = [
        {
            "source_id": "ppd-public-tools",
            "canonical_url": "https://www.portland.gov/ppd/how-use-online-permitting-tools",
            "no_raw_body_persisted": False,
        }
    ]

    issues = collect_public_refresh_metadata_manifest_dry_run_plan_v1_issues(plan)
    codes = {issue.code for issue in issues}

    assert "missing_redirect_chain" in codes
    assert "missing_http_status" in codes
    assert "missing_content_type" in codes
    assert "missing_content_hash" in codes
    assert "missing_skipped_reason" in codes
    assert "raw_body_persistence_not_blocked" in codes


def test_rejects_disallowed_claims_artifacts_and_mutation_flags() -> None:
    plan = _load("valid.json")
    plan["notes"] = [
        "Live crawl completed against DevHub verified account state.",
        "Source Registry promoted to active current source.",
        "Official action completed and permit issued.",
        "This guarantees approval and is legally sufficient.",
        "raw/downloaded/devhub_session.har",
    ]
    plan["execution_flags"] = {
        "live_crawl": True,
        "promote_archive_manifest": True,
        "submit": True,
        "upload": True,
    }

    with pytest.raises(PublicRefreshMetadataManifestDryRunPlanV1Error) as raised:
        validate_public_refresh_metadata_manifest_dry_run_plan_v1(plan)

    codes = {issue.code for issue in raised.value.issues}
    assert "live_crawl_or_devhub_claim" in codes
    assert "active_source_or_archive_promotion_claim" in codes
    assert "official_action_completion_claim" in codes
    assert "legal_or_permitting_guarantee" in codes
    assert "private_raw_or_downloaded_artifact_ref" in codes
    assert "private_raw_or_downloaded_artifact_path" in codes
    assert "active_mutation_flag" in codes
