from __future__ import annotations

import json
from pathlib import Path

import pytest

from ppd.inactive_public_refresh_archive_preview import (
    OFFLINE_VALIDATION_COMMANDS,
    build_inactive_public_refresh_archive_patch_preview,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "inactive_public_refresh_archive_preview"


def _load_fixture(name: str):
    with (FIXTURE_DIR / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_builds_inactive_source_registry_and_archive_manifest_preview() -> None:
    preview = build_inactive_public_refresh_archive_patch_preview(
        _load_fixture("reviewer_disposition_packet_rows.json"),
        _load_fixture("metadata_manifest_dry_run_plan_rows.json"),
    )

    assert preview["preview_version"] == "inactive_public_refresh_archive_patch_preview_v1"
    assert preview["mode"] == "fixture_first_offline_only"
    assert preview["official_action"] is False
    assert preview["live_crawl"] is False
    assert preview["download_documents"] is False
    assert preview["store_raw_bodies"] is False
    assert preview["open_devhub"] is False
    assert preview["promote_active_records"] is False
    assert preview["offline_validation_commands"] == OFFLINE_VALIDATION_COMMANDS

    registry_rows = preview["source_registry_patch_preview"]
    archive_rows = preview["archive_manifest_patch_preview"]
    assert [row["source_id"] for row in registry_rows] == [
        "ppd-bds-permits",
        "ppd-notice-archive",
        "ppd-retired-feed",
    ]
    assert len(archive_rows) == 3

    permit_row = registry_rows[0]
    assert permit_row["patch_state"] == "inactive_preview_only"
    assert permit_row["registry_target"] == "SourceRegistry"
    assert permit_row["expected_canonical_url_change"] is True
    assert permit_row["expected_canonical_url"] == "https://www.portland.gov/ppd/permits"
    assert permit_row["skipped_reason"] is None
    assert "No active record changed" in permit_row["rollback_note"]

    held_row = registry_rows[1]
    assert held_row["reviewer_hold"] is True
    assert held_row["skipped_reason"] == "needs_second_reviewer"

    skipped_row = registry_rows[2]
    assert skipped_row["skipped_reason"] == "manifest_marked_retired"

    archive_permit_row = archive_rows[0]
    assert archive_permit_row["registry_target"] == "ArchiveManifest"
    assert archive_permit_row["redirect_chain_placeholder"] == ["offline:not-requested"]
    assert archive_permit_row["http_status_placeholder"] == "not_requested_offline"
    assert archive_permit_row["content_type_expectation"] == "text/html"


def test_rejects_raw_or_live_artifact_fields() -> None:
    with pytest.raises(ValueError, match="forbidden live/raw fields"):
        build_inactive_public_refresh_archive_patch_preview(
            [{"source_id": "bad", "disposition": "accept", "raw_body": ""}],
            [{"source_id": "bad", "expected_canonical_url": "https://example.test"}],
        )
