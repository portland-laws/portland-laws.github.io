"""Fixture-first source freshness diff intake v7.

This module only consumes committed dry-run processor handoff fixtures and
synthetic prior/current metadata fixtures. It does not crawl, download, open
DevHub, upload, submit, schedule, pay, certify, or make permitting guarantees.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

V7_SCHEMA = "ppd.source_freshness_diff.v7"
HANDOFF_SCHEMA = "ppd.processor_handoff_manifest.v7"
METADATA_SCHEMA = "ppd.synthetic_source_metadata.v7"

OFFLINE_VALIDATION_COMMANDS: list[list[str]] = [
    ["python3", "-m", "py_compile", "ppd/source_freshness_diff_v7.py"],
    ["python3", "-m", "pytest", "ppd/tests/test_source_freshness_diff_v7.py"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]

_FORBIDDEN_LIVE_FIELDS = {
    "raw_artifact_path",
    "raw_body_path",
    "download_path",
    "private_document_path",
    "devhub_session_path",
    "auth_state_path",
    "trace_path",
    "har_path",
    "screenshot_path",
    "upload_receipt_path",
    "crawl_artifact_path",
    "session_storage_path",
    "cookie_path",
    "credential_path",
}

_FORBIDDEN_TRUE_FLAGS = {
    "active_mutation",
    "active_mutation_enabled",
    "automation_mutations_enabled",
    "crawl_executed",
    "devhub_opened",
    "downloaded_raw_artifacts",
    "legal_or_permitting_guarantee_made",
    "live_crawl_executed",
    "live_processor_invoked",
    "mutation_enabled",
    "official_action_completed",
    "official_actions_performed",
    "payment_submitted",
    "permit_submitted",
    "private_documents_read",
    "raw_artifacts_downloaded",
    "schedule_submitted",
    "upload_submitted",
    "writes_enabled",
}

_REQUIRED_SOURCE_REFS = (
    "handoff_manifest_id",
    "prior_metadata_id",
    "current_metadata_id",
)

_REQUIRED_PACKET_LISTS = (
    "changed_source_rows",
    "unchanged_source_rows",
    "affected_citation_placeholders",
    "affected_requirement_placeholders",
    "downstream_reextraction_queue_suggestions",
    "stale_evidence_hold_updates",
    "reviewer_owner_placeholders",
)


@dataclass(frozen=True)
class SourceRecord:
    source_id: str
    canonical_url: str
    content_hash: str
    normalized_document_id: str
    title: str
    processor_name: str
    processor_version: str
    capture_finished_at: str


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def build_source_freshness_diff_v7(
    handoff_manifest: Mapping[str, Any],
    prior_metadata: Mapping[str, Any],
    current_metadata: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a deterministic source freshness diff from offline fixtures only."""

    _validate_handoff_manifest(handoff_manifest)
    _validate_metadata(prior_metadata, "prior_metadata")
    _validate_metadata(current_metadata, "current_metadata")

    handoff_sources = _handoff_source_ids(handoff_manifest)
    prior_sources = _records_by_id(prior_metadata)
    current_sources = _records_by_id(current_metadata)

    changed_rows: list[dict[str, Any]] = []
    unchanged_rows: list[dict[str, Any]] = []
    citation_placeholders: list[dict[str, Any]] = []
    requirement_placeholders: list[dict[str, Any]] = []
    queue_suggestions: list[dict[str, Any]] = []
    stale_holds: list[dict[str, Any]] = []
    reviewer_placeholders: list[dict[str, Any]] = []

    for source_id in sorted(handoff_sources):
        current = current_sources.get(source_id)
        if current is None:
            stale_holds.append(
                {
                    "source_id": source_id,
                    "hold_status": "hold_for_missing_current_metadata_fixture",
                    "reason": "dry_run_manifest_references_source_without_current_metadata_fixture",
                    "allowed_next_step": "add_or_correct_committed_fixture_metadata_only",
                }
            )
            continue

        prior = prior_sources.get(source_id)
        if prior is None:
            change_kind = "new_source"
        elif prior.content_hash != current.content_hash:
            change_kind = "content_hash_changed"
        elif prior.normalized_document_id != current.normalized_document_id:
            change_kind = "normalized_document_changed"
        else:
            unchanged_rows.append(_unchanged_row(current))
            continue

        row = _changed_row(current, prior, change_kind)
        changed_rows.append(row)
        citation_placeholders.append(_citation_placeholder(current, change_kind))
        requirement_placeholders.append(_requirement_placeholder(current, change_kind))
        queue_suggestions.append(_queue_suggestion(current, change_kind))
        stale_holds.append(_stale_hold(current, change_kind))
        reviewer_placeholders.append(_reviewer_placeholder(current, change_kind))

    packet = {
        "schema": V7_SCHEMA,
        "mode": "fixture_first_offline_only",
        "source": {
            "handoff_manifest_id": str(handoff_manifest.get("manifest_id", "")),
            "prior_metadata_id": str(prior_metadata.get("metadata_id", "")),
            "current_metadata_id": str(current_metadata.get("metadata_id", "")),
            "dry_run": True,
            "raw_artifacts_downloaded": False,
            "devhub_opened": False,
            "private_documents_read": False,
            "official_actions_performed": False,
        },
        "changed_source_rows": changed_rows,
        "unchanged_source_rows": unchanged_rows,
        "affected_citation_placeholders": citation_placeholders,
        "affected_requirement_placeholders": requirement_placeholders,
        "downstream_reextraction_queue_suggestions": queue_suggestions,
        "stale_evidence_hold_updates": stale_holds,
        "reviewer_owner_placeholders": reviewer_placeholders,
        "validation_commands": OFFLINE_VALIDATION_COMMANDS,
        "legal_or_permitting_guarantees": [],
        "active_mutation": False,
    }
    validate_source_freshness_diff_v7(packet)
    return packet


def build_source_freshness_diff_v7_from_paths(
    handoff_manifest_path: Path,
    prior_metadata_path: Path,
    current_metadata_path: Path,
) -> dict[str, Any]:
    return build_source_freshness_diff_v7(
        load_json(handoff_manifest_path),
        load_json(prior_metadata_path),
        load_json(current_metadata_path),
    )


def validate_source_freshness_diff_v7(packet: Mapping[str, Any]) -> None:
    """Reject incomplete or unsafe source freshness diff intake v7 packets."""

    if packet.get("schema") != V7_SCHEMA:
        raise ValueError("source freshness diff intake must use v7 schema")
    if packet.get("mode") != "fixture_first_offline_only":
        raise ValueError("source freshness diff intake must declare fixture-first offline-only mode")

    _reject_forbidden_live_fields(packet, "packet")
    _reject_forbidden_true_flags(packet, "packet")

    source = packet.get("source")
    if not isinstance(source, Mapping):
        raise ValueError("source freshness diff intake missing source references")
    for ref in _REQUIRED_SOURCE_REFS:
        if not _non_empty_text(source.get(ref)):
            raise ValueError(f"source freshness diff intake missing {ref}")
    if source.get("dry_run") is not True:
        raise ValueError("source freshness diff intake must remain a dry-run fixture")

    for key in _REQUIRED_PACKET_LISTS:
        rows = packet.get(key)
        if not isinstance(rows, list) or not rows:
            raise ValueError(f"source freshness diff intake missing {key}")
        for index, row in enumerate(rows):
            if not isinstance(row, Mapping):
                raise ValueError(f"{key}[{index}] must be an object")
            if not _non_empty_text(row.get("source_id")):
                raise ValueError(f"{key}[{index}] missing source_id")

    changed_ids = _source_ids(packet["changed_source_rows"], "changed_source_rows")
    unchanged_ids = _source_ids(packet["unchanged_source_rows"], "unchanged_source_rows")
    if changed_ids & unchanged_ids:
        raise ValueError("changed and unchanged source rows must not overlap")

    for key in (
        "affected_citation_placeholders",
        "affected_requirement_placeholders",
        "downstream_reextraction_queue_suggestions",
        "reviewer_owner_placeholders",
    ):
        ids = _source_ids(packet[key], key)
        if ids != changed_ids:
            raise ValueError(f"{key} must cover every changed source and only changed sources")

    hold_ids = _source_ids(packet["stale_evidence_hold_updates"], "stale_evidence_hold_updates")
    if not changed_ids.issubset(hold_ids):
        raise ValueError("stale_evidence_hold_updates must cover every changed source")

    for index, row in enumerate(packet["affected_citation_placeholders"]):
        if not _non_empty_text(row.get("placeholder_id")) or not _non_empty_text(row.get("status")):
            raise ValueError(f"affected_citation_placeholders[{index}] missing placeholder fields")
    for index, row in enumerate(packet["affected_requirement_placeholders"]):
        if not _non_empty_text(row.get("placeholder_id")) or not _non_empty_text(row.get("status")):
            raise ValueError(f"affected_requirement_placeholders[{index}] missing placeholder fields")
    for index, row in enumerate(packet["downstream_reextraction_queue_suggestions"]):
        if not _non_empty_text(row.get("queue_id")) or row.get("requires_live_crawl") is not False:
            raise ValueError(f"downstream_reextraction_queue_suggestions[{index}] must stay offline-only")
    for index, row in enumerate(packet["reviewer_owner_placeholders"]):
        if not _non_empty_text(row.get("owner_placeholder")):
            raise ValueError(f"reviewer_owner_placeholders[{index}] missing owner_placeholder")

    guarantees = packet.get("legal_or_permitting_guarantees", [])
    if guarantees not in ([], None):
        raise ValueError("legal or permitting guarantees are not allowed")
    _validate_commands(packet.get("validation_commands"))


def _validate_handoff_manifest(manifest: Mapping[str, Any]) -> None:
    if manifest.get("schema") != HANDOFF_SCHEMA:
        raise ValueError("handoff manifest must use processor handoff manifest v7 schema")
    if manifest.get("dry_run") is not True:
        raise ValueError("handoff manifest must be a dry-run fixture")
    _reject_forbidden_live_fields(manifest, "handoff_manifest")
    _reject_forbidden_true_flags(manifest, "handoff_manifest")


def _validate_metadata(metadata: Mapping[str, Any], label: str) -> None:
    if metadata.get("schema") != METADATA_SCHEMA:
        raise ValueError(f"{label} must use synthetic source metadata v7 schema")
    if metadata.get("synthetic") is not True:
        raise ValueError(f"{label} must be synthetic fixture metadata")
    _reject_forbidden_live_fields(metadata, label)
    _reject_forbidden_true_flags(metadata, label)


def _reject_forbidden_live_fields(value: Any, path: str) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in _FORBIDDEN_LIVE_FIELDS:
                raise ValueError(f"forbidden live artifact field at {path}.{key}")
            _reject_forbidden_live_fields(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_forbidden_live_fields(child, f"{path}[{index}]")


def _reject_forbidden_true_flags(value: Any, path: str) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if key_text in _FORBIDDEN_TRUE_FLAGS and child is True:
                raise ValueError(f"forbidden active/live/private/mutating claim at {path}.{key_text}")
            if key_text == "legal_or_permitting_guarantees" and child not in ([], None):
                raise ValueError(f"legal or permitting guarantees are not allowed at {path}.{key_text}")
            _reject_forbidden_true_flags(child, f"{path}.{key_text}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_forbidden_true_flags(child, f"{path}[{index}]")


def _handoff_source_ids(manifest: Mapping[str, Any]) -> set[str]:
    captures = manifest.get("captures", [])
    if not isinstance(captures, list) or not captures:
        raise ValueError("handoff manifest captures must be a non-empty list")
    source_ids: set[str] = set()
    for capture in captures:
        if not isinstance(capture, Mapping):
            raise ValueError("handoff manifest capture entries must be objects")
        if capture.get("no_raw_body_persisted") is not True:
            raise ValueError("dry-run captures must declare no_raw_body_persisted=true")
        source_id = str(capture.get("source_id", "")).strip()
        if not source_id:
            raise ValueError("dry-run capture missing source_id")
        source_ids.add(source_id)
    return source_ids


def _records_by_id(metadata: Mapping[str, Any]) -> dict[str, SourceRecord]:
    sources = metadata.get("sources", [])
    if not isinstance(sources, list):
        raise ValueError("metadata sources must be a list")
    records: dict[str, SourceRecord] = {}
    for source in sources:
        if not isinstance(source, Mapping):
            raise ValueError("metadata source entries must be objects")
        record = SourceRecord(
            source_id=_required(source, "source_id"),
            canonical_url=_required(source, "canonical_url"),
            content_hash=_required(source, "content_hash"),
            normalized_document_id=_required(source, "normalized_document_id"),
            title=str(source.get("title", "")),
            processor_name=str(source.get("processor_name", "fixture-processor")),
            processor_version=str(source.get("processor_version", "v7-fixture")),
            capture_finished_at=str(source.get("capture_finished_at", "")),
        )
        if record.source_id in records:
            raise ValueError(f"duplicate source_id in metadata: {record.source_id}")
        records[record.source_id] = record
    return records


def _required(source: Mapping[str, Any], field: str) -> str:
    value = str(source.get(field, "")).strip()
    if not value:
        raise ValueError(f"metadata source missing {field}")
    return value


def _changed_row(current: SourceRecord, prior: SourceRecord | None, change_kind: str) -> dict[str, Any]:
    return {
        "source_id": current.source_id,
        "canonical_url": current.canonical_url,
        "change_kind": change_kind,
        "prior_content_hash": prior.content_hash if prior else None,
        "current_content_hash": current.content_hash,
        "prior_normalized_document_id": prior.normalized_document_id if prior else None,
        "current_normalized_document_id": current.normalized_document_id,
        "title": current.title,
        "processor_name": current.processor_name,
        "processor_version": current.processor_version,
        "capture_finished_at": current.capture_finished_at,
    }


def _unchanged_row(current: SourceRecord) -> dict[str, Any]:
    return {
        "source_id": current.source_id,
        "canonical_url": current.canonical_url,
        "change_kind": "unchanged",
        "content_hash": current.content_hash,
        "normalized_document_id": current.normalized_document_id,
        "title": current.title,
    }


def _citation_placeholder(current: SourceRecord, change_kind: str) -> dict[str, str]:
    return {
        "source_id": current.source_id,
        "placeholder_id": f"citation-review:{current.source_id}",
        "status": "needs_fixture_backed_citation_review",
        "reason": change_kind,
    }


def _requirement_placeholder(current: SourceRecord, change_kind: str) -> dict[str, str]:
    return {
        "source_id": current.source_id,
        "placeholder_id": f"requirement-review:{current.source_id}",
        "status": "needs_requirement_reextraction_review",
        "reason": change_kind,
    }


def _queue_suggestion(current: SourceRecord, change_kind: str) -> dict[str, Any]:
    return {
        "queue_id": f"reextract:{current.source_id}",
        "source_id": current.source_id,
        "suggested_stage": "offline_reextraction_from_normalized_document_fixture",
        "priority": "normal" if change_kind == "new_source" else "high",
        "requires_live_crawl": False,
        "requires_devhub": False,
    }


def _stale_hold(current: SourceRecord, change_kind: str) -> dict[str, str]:
    return {
        "source_id": current.source_id,
        "hold_status": "hold_prior_evidence_until_reviewer_accepts_diff",
        "reason": change_kind,
        "release_condition": "reviewer_updates_citations_and_requirement_nodes_from_offline_fixtures",
    }


def _reviewer_placeholder(current: SourceRecord, change_kind: str) -> dict[str, str]:
    return {
        "source_id": current.source_id,
        "owner_placeholder": "ppd-reviewer-unassigned",
        "review_stage": "source_freshness_diff_v7",
        "reason": change_kind,
    }


def _source_ids(rows: Any, label: str) -> set[str]:
    if not isinstance(rows, list):
        raise ValueError(f"{label} must be a list")
    ids: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise ValueError(f"{label}[{index}] must be an object")
        source_id = str(row.get("source_id", "")).strip()
        if not source_id:
            raise ValueError(f"{label}[{index}] missing source_id")
        if source_id in ids:
            raise ValueError(f"{label} contains duplicate source_id: {source_id}")
        ids.add(source_id)
    return ids


def _validate_commands(value: Any) -> None:
    if not isinstance(value, list) or not value:
        raise ValueError("source freshness diff intake missing validation_commands")
    normalized: list[list[str]] = []
    for index, command in enumerate(value):
        if not isinstance(command, list) or not command:
            raise ValueError(f"validation_commands[{index}] must be a non-empty list")
        if not all(isinstance(part, str) and part for part in command):
            raise ValueError(f"validation_commands[{index}] must contain command strings")
        normalized.append(command)
    for required in OFFLINE_VALIDATION_COMMANDS:
        if required not in normalized:
            raise ValueError(f"validation_commands missing required offline command: {required}")


def _non_empty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())
