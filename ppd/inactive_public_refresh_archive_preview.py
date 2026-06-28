"""Fixture-first inactive public refresh archive patch preview v1.

This module intentionally consumes only synthetic reviewer disposition packet rows and
metadata manifest dry-run plan rows. It never crawls, downloads, stores raw bodies,
opens DevHub, promotes active records, or performs official actions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

OFFLINE_VALIDATION_COMMANDS = [
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
    ["python3", "-m", "pytest", "ppd/tests/test_inactive_public_refresh_archive_preview.py"],
]

_FORBIDDEN_INPUT_KEYS = {
    "raw_body",
    "body",
    "html",
    "pdf_bytes",
    "downloaded_document",
    "devhub_session",
    "auth_state",
    "trace_path",
}


@dataclass(frozen=True)
class PreviewInputs:
    reviewer_disposition_packet_rows: list[dict[str, Any]]
    metadata_manifest_dry_run_plan_rows: list[dict[str, Any]]


def build_inactive_public_refresh_archive_patch_preview(
    reviewer_disposition_packet_rows: Iterable[dict[str, Any]],
    metadata_manifest_dry_run_plan_rows: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    """Build an inactive patch preview from synthetic fixture rows only."""

    reviewer_rows = [_copy_and_validate_row(row, "reviewer") for row in reviewer_disposition_packet_rows]
    manifest_rows = [_copy_and_validate_row(row, "manifest") for row in metadata_manifest_dry_run_plan_rows]

    reviewer_by_source_id = {str(row["source_id"]): row for row in reviewer_rows}
    source_registry_preview: list[dict[str, Any]] = []
    archive_manifest_preview: list[dict[str, Any]] = []

    for plan_row in sorted(manifest_rows, key=lambda item: str(item["source_id"])):
        source_id = str(plan_row["source_id"])
        reviewer_row = reviewer_by_source_id.get(source_id, {})
        disposition = str(reviewer_row.get("disposition", "unreviewed"))
        reviewer_hold = bool(reviewer_row.get("reviewer_hold", False))
        skipped_reason = _skipped_reason(plan_row, reviewer_row, disposition, reviewer_hold)
        expected_canonical_url = str(
            plan_row.get("expected_canonical_url")
            or plan_row.get("candidate_url")
            or plan_row.get("current_canonical_url")
            or ""
        )

        source_registry_preview.append(
            {
                "source_id": source_id,
                "patch_state": "inactive_preview_only",
                "registry_target": "SourceRegistry",
                "current_canonical_url": plan_row.get("current_canonical_url"),
                "expected_canonical_url": expected_canonical_url,
                "expected_canonical_url_change": expected_canonical_url != plan_row.get("current_canonical_url"),
                "reviewer_disposition": disposition,
                "reviewer_hold": reviewer_hold,
                "skipped_reason": skipped_reason,
                "rollback_note": _rollback_note(source_id, skipped_reason),
            }
        )

        archive_manifest_preview.append(
            {
                "source_id": source_id,
                "patch_state": "inactive_preview_only",
                "registry_target": "ArchiveManifest",
                "archive_key": plan_row.get("archive_key"),
                "expected_canonical_url": expected_canonical_url,
                "redirect_chain_placeholder": list(plan_row.get("redirect_chain_placeholder", [])),
                "http_status_placeholder": plan_row.get("http_status_placeholder", "not_requested_offline"),
                "content_type_expectation": plan_row.get("content_type_expectation", "unknown_offline"),
                "reviewer_disposition": disposition,
                "reviewer_hold": reviewer_hold,
                "skipped_reason": skipped_reason,
                "rollback_note": _rollback_note(source_id, skipped_reason),
            }
        )

    return {
        "preview_version": "inactive_public_refresh_archive_patch_preview_v1",
        "mode": "fixture_first_offline_only",
        "official_action": False,
        "live_crawl": False,
        "download_documents": False,
        "store_raw_bodies": False,
        "open_devhub": False,
        "promote_active_records": False,
        "source_registry_patch_preview": source_registry_preview,
        "archive_manifest_patch_preview": archive_manifest_preview,
        "offline_validation_commands": OFFLINE_VALIDATION_COMMANDS,
    }


def _copy_and_validate_row(row: dict[str, Any], row_kind: str) -> dict[str, Any]:
    copied = dict(row)
    forbidden = sorted(_FORBIDDEN_INPUT_KEYS.intersection(copied))
    if forbidden:
        raise ValueError(f"{row_kind} row contains forbidden live/raw fields: {', '.join(forbidden)}")
    if "source_id" not in copied:
        raise ValueError(f"{row_kind} row is missing source_id")
    return copied


def _skipped_reason(plan_row: dict[str, Any], reviewer_row: dict[str, Any], disposition: str, reviewer_hold: bool) -> str | None:
    if reviewer_hold:
        return str(reviewer_row.get("hold_reason") or "reviewer_hold")
    if disposition in {"reject", "rejected"}:
        return str(reviewer_row.get("skipped_reason") or "reviewer_rejected")
    if plan_row.get("skipped_reason"):
        return str(plan_row["skipped_reason"])
    if disposition == "skip":
        return str(reviewer_row.get("skipped_reason") or "reviewer_skipped")
    return None


def _rollback_note(source_id: str, skipped_reason: str | None) -> str:
    if skipped_reason:
        return f"No active record changed for {source_id}; discard inactive preview row to roll back skipped item."
    return f"No active record changed for {source_id}; discard inactive preview row to roll back."
