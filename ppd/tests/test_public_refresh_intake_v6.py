from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from ppd.crawler.public_refresh_intake_v6 import (
    SCHEMA_VERSION,
    normalize_manifest_row,
    normalize_manifest_rows,
    processor_handoff_id_for,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "public_refresh_intake_v6"


def load_fixture_rows() -> list[dict[str, Any]]:
    return json.loads((FIXTURE_DIR / "synthetic_dry_run_manifest_rows.json").read_text(encoding="utf-8"))


def fixture_row() -> dict[str, Any]:
    return deepcopy(load_fixture_rows()[0])


def test_v6_intake_normalizes_fixture_rows_without_raw_bodies() -> None:
    intake = normalize_manifest_rows(load_fixture_rows(), source="unit_fixture")
    data = intake.to_dict()

    assert data["schema_version"] == SCHEMA_VERSION
    assert data["source"] == "unit_fixture"
    assert len(data["rows"]) == 3

    first = data["rows"][0]
    assert first["dry_run_plan_ref"] == {
        "plan_id": "public-refresh-dry-run-execution-plan-v6-fixture",
        "schema_version": "ppd.public_refresh_dry_run_execution_plan.v6",
    }
    assert first["source_url"] == "https://www.portland.gov/ppd/how-use-online-permitting-tools"
    assert first["canonical_url"] == "https://www.portland.gov/ppd/how-use-online-permitting-tools"
    assert first["source_group"] == "ppd_public_html"
    assert first["http_metadata"] == {
        "status_code": None,
        "content_type": None,
        "etag": None,
        "last_modified": None,
        "redirect_chain": [],
    }
    assert first["content_hash"] == {"algorithm": "sha256", "value": None, "placeholder": True}
    assert first["processor_handoff_id"] == processor_handoff_id_for(first["canonical_url"], first["source_group"])
    assert first["skipped_reason"] == "synthetic_dry_run_no_fetch"
    assert first["no_raw_body_asserted"] is True
    assert first["no_raw_body_persisted"] is False
    assert first["citation_refresh_candidates"] == [
        {
            "citation_id": "ppd-online-tools-overview",
            "canonical_url": "https://www.portland.gov/ppd/how-use-online-permitting-tools",
            "reason": "public_guidance_refresh",
        }
    ]
    assert first["freshness_status_delta"] == {
        "previous_status": "fresh",
        "current_status": "synthetic_dry_run_unverified",
        "changed": True,
    }


@pytest.mark.parametrize(
    ("field", "message"),
    [
        ("dry_run_plan_ref", "dry_run_plan_ref must be an object"),
        ("source_url", "source_url must be a non-empty string"),
        ("canonical_url", "canonical_url must be a non-empty string"),
        ("source_group", "source_group must be a non-empty string"),
        ("http_metadata", "http_metadata must be an object"),
        ("content_hash", "content_hash must be an explicit placeholder object"),
        ("processor_handoff_id", "processor_handoff_id must be a non-empty string"),
        ("skipped_reason", "skipped_reason must be a non-empty string"),
        ("no_raw_body_asserted", "no_raw_body_asserted must be true"),
        ("no_raw_body_persisted", "no_raw_body_persisted must be false"),
        ("citation_refresh_candidates", "citation_refresh_candidates must be a non-empty list"),
        ("freshness_status_delta", "freshness_status_delta must be an object"),
    ],
)
def test_v6_intake_rejects_missing_required_safety_fields(field: str, message: str) -> None:
    row = fixture_row()
    row.pop(field)

    with pytest.raises(ValueError, match=message):
        normalize_manifest_row(row)


@pytest.mark.parametrize("field", ["status_code", "content_type", "etag", "last_modified", "redirect_chain"])
def test_v6_intake_rejects_missing_http_metadata_placeholders(field: str) -> None:
    row = fixture_row()
    row["http_metadata"].pop(field)

    with pytest.raises(ValueError, match="http_metadata missing placeholder fields"):
        normalize_manifest_row(row)


def test_v6_intake_rejects_non_synthetic_or_live_rows() -> None:
    row = fixture_row()
    row["dry_run"] = False

    with pytest.raises(ValueError, match="synthetic=true and dry_run=true"):
        normalize_manifest_row(row)


def test_v6_intake_rejects_live_crawl_execution_claims() -> None:
    row = fixture_row()
    row["live_crawl_performed"] = True

    with pytest.raises(ValueError, match="live crawl execution claims"):
        normalize_manifest_row(row)


@pytest.mark.parametrize("artifact_key", ["raw_body", "download_path", "raw_crawl_artifact", "session_path", "auth_state_path"])
def test_v6_intake_rejects_raw_downloaded_private_session_or_auth_artifacts(artifact_key: str) -> None:
    row = fixture_row()
    row[artifact_key] = "not-commit-safe"

    with pytest.raises(ValueError, match="raw/private artifacts"):
        normalize_manifest_row(row)


def test_v6_intake_rejects_real_content_hashes_for_dry_run_rows() -> None:
    row = fixture_row()
    row["content_hash"] = {"algorithm": "sha256", "value": "0123456789abcdef", "placeholder": True}

    with pytest.raises(ValueError, match="content-hash placeholder"):
        normalize_manifest_row(row)


def test_v6_intake_rejects_unknown_skip_reason() -> None:
    row = fixture_row()
    row["skipped_reason"] = "opened_devhub"

    with pytest.raises(ValueError, match="unsupported skipped_reason"):
        normalize_manifest_row(row)


def test_v6_intake_rejects_missing_no_raw_body_assertions() -> None:
    row = fixture_row()
    row["no_raw_body_asserted"] = False

    with pytest.raises(ValueError, match="no_raw_body_asserted must be true"):
        normalize_manifest_row(row)


def test_v6_intake_rejects_missing_citation_refresh_candidates() -> None:
    row = fixture_row()
    row["citation_refresh_candidates"] = []

    with pytest.raises(ValueError, match="citation_refresh_candidates must be a non-empty list"):
        normalize_manifest_row(row)


def test_v6_intake_rejects_invalid_freshness_status_delta() -> None:
    row = fixture_row()
    row["freshness_status_delta"] = {
        "previous_status": "fresh",
        "current_status": "synthetic_dry_run_unverified",
        "changed": False,
    }

    with pytest.raises(ValueError, match="freshness_status_delta.changed"):
        normalize_manifest_row(row)


@pytest.mark.parametrize(
    "claim",
    [
        {"official_action_completed": True},
        {"summary": "official action completed during refresh"},
        {"summary": "legal guarantee for permit approval"},
        {"summary": "permitting guarantee was produced"},
    ],
)
def test_v6_intake_rejects_official_completion_legal_or_permitting_guarantee_claims(claim: dict[str, Any]) -> None:
    row = fixture_row()
    row.update(claim)

    with pytest.raises(ValueError, match="official-action completion claims|prohibited claim text"):
        normalize_manifest_row(row)


@pytest.mark.parametrize("flag", ["active_mutation", "mutation_enabled", "execute_mutations", "write_enabled"])
def test_v6_intake_rejects_active_mutation_flags(flag: str) -> None:
    row = fixture_row()
    row[flag] = True

    with pytest.raises(ValueError, match="active mutation flags"):
        normalize_manifest_row(row)


def test_v6_intake_rejects_private_session_auth_url_fields() -> None:
    row = fixture_row()
    row["source_url"] = "https://www.portland.gov/ppd/how-use-online-permitting-tools?session=private"

    with pytest.raises(ValueError, match="private/session/auth query fields"):
        normalize_manifest_row(row)
