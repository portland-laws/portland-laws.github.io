"""Fixture-first public refresh metadata manifest dry-run plan v1.

This module intentionally consumes synthetic checklist rows only. It plans the
metadata placeholders a future public refresh would update, but it does not
crawl, download, open DevHub, persist raw bodies, promote sources, or perform
any official action.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

PLAN_VERSION = "public-refresh-metadata-manifest-dry-run-plan-v1"
OFFLINE_VALIDATION_COMMANDS = [
    ["python3", "-m", "py_compile", "ppd/crawler/public_refresh_metadata_manifest_dry_run_plan_v1.py"],
    ["python3", "-m", "py_compile", "ppd/tests/test_public_refresh_metadata_manifest_dry_run_plan_v1.py"],
    ["python3", "-m", "pytest", "ppd/tests/test_public_refresh_metadata_manifest_dry_run_plan_v1.py"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]
PROHIBITED_ACTIONS = [
    "live_crawl",
    "download_document",
    "store_raw_body",
    "open_devhub",
    "promote_source",
    "official_action",
]
REQUIRED_ROW_FIELDS = {
    "seed_id",
    "seed_url",
    "source_type",
    "owning_surface",
    "allowlist_policy",
    "robots_policy",
    "crawl_frequency",
    "processor_policy",
    "privacy_classification",
    "expected_content_type",
    "content_hash_policy",
    "freshness_status_impact",
    "reviewer_hold",
    "rollback_note",
}


@dataclass(frozen=True)
class SyntheticChecklistRow:
    """A committed synthetic row used to plan manifest metadata only."""

    seed_id: str
    seed_url: str
    source_type: str
    owning_surface: str
    allowlist_policy: str
    robots_policy: str
    crawl_frequency: str
    processor_policy: str
    privacy_classification: str
    expected_content_type: str
    content_hash_policy: str
    freshness_status_impact: str
    reviewer_hold: bool
    rollback_note: str
    skipped_reason: str | None = None
    canonical_url_placeholder: str | None = None

    @classmethod
    def from_mapping(cls, row: dict[str, Any]) -> "SyntheticChecklistRow":
        missing = sorted(REQUIRED_ROW_FIELDS.difference(row))
        if missing:
            raise ValueError(f"synthetic checklist row missing required fields: {missing}")
        return cls(
            seed_id=str(row["seed_id"]),
            seed_url=str(row["seed_url"]),
            source_type=str(row["source_type"]),
            owning_surface=str(row["owning_surface"]),
            allowlist_policy=str(row["allowlist_policy"]),
            robots_policy=str(row["robots_policy"]),
            crawl_frequency=str(row["crawl_frequency"]),
            processor_policy=str(row["processor_policy"]),
            privacy_classification=str(row["privacy_classification"]),
            expected_content_type=str(row["expected_content_type"]),
            content_hash_policy=str(row["content_hash_policy"]),
            freshness_status_impact=str(row["freshness_status_impact"]),
            reviewer_hold=bool(row["reviewer_hold"]),
            rollback_note=str(row["rollback_note"]),
            skipped_reason=_optional_string(row.get("skipped_reason")),
            canonical_url_placeholder=_optional_string(row.get("canonical_url_placeholder")),
        )


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def load_fixture_rows(path: Path) -> list[SyntheticChecklistRow]:
    """Load synthetic checklist rows from a committed JSON fixture."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("fixture root must be an object")
    if payload.get("fixture_kind") != "synthetic_public_refresh_preflight_checklist_v1":
        raise ValueError("fixture_kind must identify the synthetic checklist contract")
    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("fixture rows must be a non-empty list")
    return [SyntheticChecklistRow.from_mapping(row) for row in rows]


def build_dry_run_plan(rows: list[SyntheticChecklistRow]) -> dict[str, Any]:
    """Map synthetic seed candidates to expected metadata placeholder updates."""

    source_registry_updates = []
    archive_manifest_updates = []
    skipped_seed_ids = []
    reviewer_holds = []
    rollback_notes = []

    for row in rows:
        canonical_url = row.canonical_url_placeholder or f"placeholder:canonical:{row.seed_id}"
        freshness_status = _freshness_status_for(row)
        source_registry_updates.append(
            {
                "source_id": f"source:{row.seed_id}",
                "canonical_url": canonical_url,
                "source_type": row.source_type,
                "owning_surface": row.owning_surface,
                "allowlist_policy": row.allowlist_policy,
                "robots_policy": row.robots_policy,
                "crawl_frequency": row.crawl_frequency,
                "processor_policy": row.processor_policy,
                "privacy_classification": row.privacy_classification,
                "last_seen_at": "placeholder:not-captured-in-offline-dry-run",
                "freshness_status": freshness_status,
                "freshness_status_impact": row.freshness_status_impact,
                "reviewer_hold": row.reviewer_hold,
                "skipped_reason": row.skipped_reason,
            }
        )
        archive_manifest_updates.append(
            {
                "manifest_id": f"archive-placeholder:{row.seed_id}",
                "source_id": f"source:{row.seed_id}",
                "canonical_url": canonical_url,
                "requested_url": row.seed_url,
                "redirect_chain": [
                    {
                        "from": row.seed_url,
                        "to": canonical_url,
                        "status": "placeholder:not-requested",
                    }
                ],
                "http_status": "placeholder:not-requested",
                "content_type": row.expected_content_type,
                "content_hash": _content_hash_placeholder(row),
                "capture_started_at": "placeholder:not-captured-in-offline-dry-run",
                "capture_finished_at": "placeholder:not-captured-in-offline-dry-run",
                "processor_name": "placeholder:processor-not-invoked",
                "processor_version": "placeholder:processor-not-invoked",
                "archive_artifact_ref": "placeholder:no-archive-artifact-created",
                "normalized_document_id": "placeholder:not-normalized-in-dry-run",
                "skipped_reason": row.skipped_reason,
                "no_raw_body_persisted": True,
            }
        )
        if row.skipped_reason:
            skipped_seed_ids.append(row.seed_id)
        if row.reviewer_hold:
            reviewer_holds.append(
                {
                    "seed_id": row.seed_id,
                    "reason": "synthetic checklist requires reviewer hold before any future promotion",
                }
            )
        rollback_notes.append({"seed_id": row.seed_id, "note": row.rollback_note})

    plan = {
        "plan_version": PLAN_VERSION,
        "mode": "fixture_first_offline_dry_run",
        "input_contract": "synthetic_public_refresh_preflight_checklist_v1",
        "source_registry_placeholder_updates": source_registry_updates,
        "archive_manifest_placeholder_updates": archive_manifest_updates,
        "skipped_seed_ids": skipped_seed_ids,
        "reviewer_holds": reviewer_holds,
        "rollback_notes": rollback_notes,
        "prohibited_actions": PROHIBITED_ACTIONS,
        "offline_validation_commands": OFFLINE_VALIDATION_COMMANDS,
        "side_effects": {
            "live_crawling": False,
            "document_downloads": False,
            "raw_body_storage": False,
            "devhub_opened": False,
            "source_promotion": False,
            "official_actions": False,
        },
    }
    validate_dry_run_plan(plan)
    return plan


def _freshness_status_for(row: SyntheticChecklistRow) -> str:
    if row.skipped_reason:
        return "placeholder:skipped-no-refresh"
    if row.reviewer_hold:
        return "placeholder:review-held"
    return "placeholder:refresh-needed"


def _content_hash_placeholder(row: SyntheticChecklistRow) -> str:
    if row.skipped_reason:
        return "placeholder:not-computed-skipped"
    if row.content_hash_policy == "metadata_placeholder_only":
        return "placeholder:not-computed-no-body"
    return f"placeholder:{row.content_hash_policy}"


def validate_dry_run_plan(plan: dict[str, Any]) -> None:
    """Validate that the plan remains offline and placeholder-only."""

    if plan.get("plan_version") != PLAN_VERSION:
        raise ValueError("unexpected plan version")
    if plan.get("mode") != "fixture_first_offline_dry_run":
        raise ValueError("plan mode must remain fixture-first offline dry-run")
    if plan.get("prohibited_actions") != PROHIBITED_ACTIONS:
        raise ValueError("prohibited actions changed")
    if plan.get("offline_validation_commands") != OFFLINE_VALIDATION_COMMANDS:
        raise ValueError("offline validation commands changed")
    side_effects = plan.get("side_effects")
    if not isinstance(side_effects, dict) or any(bool(value) for value in side_effects.values()):
        raise ValueError("dry-run plan must not enable side effects")
    for manifest in plan.get("archive_manifest_placeholder_updates", []):
        if manifest.get("no_raw_body_persisted") is not True:
            raise ValueError("archive manifest placeholders must forbid raw body persistence")
        if not str(manifest.get("http_status", "")).startswith("placeholder:"):
            raise ValueError("http_status must remain a placeholder")
        if not str(manifest.get("content_hash", "")).startswith("placeholder:"):
            raise ValueError("content_hash must remain a placeholder")
        if manifest.get("archive_artifact_ref") != "placeholder:no-archive-artifact-created":
            raise ValueError("archive artifacts must not be created by this dry run")
