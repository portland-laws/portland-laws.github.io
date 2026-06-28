"""Fixture-first public metadata manifest dry-run v5.

This module consumes only public refresh preflight packet v5 fixtures and assembles
synthetic ArchiveManifest rows. It does not crawl live sites, download documents,
store raw bodies, open DevHub, or make legal or permitting guarantees.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from ppd.public_refresh.public_refresh_preflight_packet_v5 import (
    PACKET_VERSION as PREFLIGHT_PACKET_VERSION,
    assert_valid_preflight_packet,
)

DRY_RUN_VERSION = "public-metadata-manifest-dry-run-v5"
MODE = "fixture-first-offline-public-metadata-manifest-dry-run"

VALIDATION_COMMANDS = [
    ["python3", "-m", "py_compile", "ppd/public_refresh/public_metadata_manifest_dry_run_v5.py"],
    ["python3", "-m", "py_compile", "ppd/tests/test_public_metadata_manifest_dry_run_v5.py"],
    ["python3", "-m", "pytest", "ppd/tests/test_public_metadata_manifest_dry_run_v5.py"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]

PROHIBITED_ACTIONS = [
    "live_crawl",
    "download_document",
    "store_raw_body",
    "open_devhub",
    "persist_private_session",
    "promote_archive_manifest",
    "legal_or_permitting_guarantee",
]

READY_STATE = "metadata_manifest_candidate_ready"

REQUIRED_TOP_LEVEL_FIELDS = (
    "dry_run_version",
    "mode",
    "input_packet_version",
    "offline_only",
    "source_fixture_policy",
    "selected_public_sources",
    "synthetic_archive_manifest_rows",
    "redirect_chain_placeholder_policy",
    "http_status_placeholder_policy",
    "content_hash_placeholder_policy",
    "processor_placeholder_policy",
    "skipped_reasons",
    "no_raw_body_flags",
    "reviewer_holds",
    "rollback_notes",
    "prohibited_actions",
    "validation_commands",
)

FORBIDDEN_TEXT_MARKERS = (
    "live crawl completed",
    "live crawl ran",
    "live crawler ran",
    "crawled live",
    "live request completed",
    "raw body artifact",
    "raw body persisted",
    "raw html persisted",
    "raw response body",
    "raw crawl output",
    "downloaded document",
    "downloaded artifact",
    "download complete",
    "auth_state",
    "session_state",
    "authenticated session",
    "devhub session",
    "private artifact",
    "private case file",
    "cookie jar",
    "credential stored",
    "password stored",
    "trace.zip",
    "har file",
    "file://",
    "/home/",
    "legal guarantee",
    "permitting guarantee",
    "permit guaranteed",
    "guarantee permit",
    "approval guaranteed",
    "mutation enabled",
    "active mutation",
)

ACTIVE_MUTATION_KEYS = frozenset(
    {
        "active_mutation",
        "active_mutation_enabled",
        "active_mutation_flags",
        "mutates_sources",
        "mutates_registry",
        "mutates_guardrails",
        "mutates_release_state",
        "live_crawl_enabled",
        "download_enabled",
        "auth_enabled",
        "devhub_enabled",
        "release_activation_enabled",
        "official_action_enabled",
        "archive_promotion_enabled",
    }
)


class PublicMetadataManifestDryRunV5Error(ValueError):
    """Raised when a metadata manifest dry-run v5 cannot be assembled safely."""


class PublicMetadataManifestDryRunV5ValidationError(ValueError):
    """Raised when a metadata manifest dry-run v5 packet is incomplete or unsafe."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("public metadata manifest dry-run v5 rejected: " + "; ".join(errors))


def load_preflight_fixture(path: Path) -> dict[str, Any]:
    """Load a committed preflight packet fixture without performing network work."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise PublicMetadataManifestDryRunV5Error("preflight fixture must be a JSON object")
    return payload


def assemble_public_metadata_manifest_dry_run_v5(preflight_packet: Mapping[str, Any]) -> dict[str, Any]:
    """Assemble synthetic ArchiveManifest rows from a preflight packet v5 fixture."""

    if not isinstance(preflight_packet, dict):
        raise PublicMetadataManifestDryRunV5Error("preflight packet must be a JSON object")
    assert_valid_preflight_packet(preflight_packet)

    allowlist_rows = list(preflight_packet["allowlist_checks"])
    readiness_by_seed = _by_seed(preflight_packet["processor_handoff_readiness"])
    rate_limit_by_seed = _by_seed(preflight_packet["rate_limit_notes"])
    rollback_by_seed = {
        row["seed_id"]: row["rollback_note"]
        for row in preflight_packet["rollback_notes"]["candidate_level"]
    }
    reviewer_hold_by_seed = {
        row["seed_id"]: row
        for row in preflight_packet["reviewer_holds"]["candidate_holds"]
    }

    selected_sources: list[dict[str, Any]] = []
    manifest_rows: list[dict[str, Any]] = []
    skipped_reasons: list[dict[str, str]] = []

    for allowlist_row in allowlist_rows:
        seed_id = allowlist_row["seed_id"]
        readiness = readiness_by_seed[seed_id]
        reviewer_hold = reviewer_hold_by_seed.get(seed_id)
        skipped_reason = allowlist_row["skip_reason"]
        handoff_state = readiness["processor_handoff_state"]
        blocked = skipped_reason != "not_skipped" or reviewer_hold is not None or handoff_state != READY_STATE
        canonical_placeholder = f"placeholder:canonical-url:{seed_id}"
        requested_placeholder = f"placeholder:requested-url:{seed_id}"
        normalized_document_id = f"normalized-document-placeholder:{seed_id}"

        selected_sources.append(
            {
                "seed_id": seed_id,
                "source_registry_placeholder_id": allowlist_row["source_registry_placeholder_id"],
                "source_registry_ref": allowlist_row["source_registry_ref"],
                "owning_surface": allowlist_row["owning_surface"],
                "selection_state": "selected_for_synthetic_archive_manifest_row",
                "processor_handoff_state": handoff_state,
                "reviewer_hold": reviewer_hold is not None,
                "skipped_reason": skipped_reason,
                "crawl_frequency_label": rate_limit_by_seed[seed_id]["crawl_frequency_label"],
            }
        )

        row = {
            "manifest_id": f"archive-manifest-dry-run-v5:{seed_id}",
            "source_id": f"public-source-placeholder:{seed_id}",
            "source_registry_placeholder_id": allowlist_row["source_registry_placeholder_id"],
            "source_registry_ref": allowlist_row["source_registry_ref"],
            "canonical_url": canonical_placeholder,
            "requested_url": requested_placeholder,
            "redirect_chain": [
                {
                    "from": requested_placeholder,
                    "to": canonical_placeholder,
                    "status": "placeholder:not-requested",
                }
            ],
            "http_status": "placeholder:skipped-before-request" if blocked else "placeholder:not-requested",
            "content_type": "placeholder:not-fetched",
            "content_hash": "placeholder:not-computed-skipped-or-held" if blocked else "placeholder:not-computed-no-body",
            "capture_started_at": "placeholder:not-captured-offline-dry-run",
            "capture_finished_at": "placeholder:not-captured-offline-dry-run",
            "processor_name": "placeholder:processor-not-invoked",
            "processor_version": "placeholder:processor-not-invoked",
            "archive_artifact_ref": "placeholder:no-archive-artifact-created",
            "normalized_document_id": normalized_document_id,
            "normalized_document_ref": {
                "document_id": normalized_document_id,
                "document_ref": f"normalized-document-placeholder://public-refresh/{seed_id}",
                "normalization_state": "placeholder:not-normalized-offline-dry-run",
            },
            "skipped_reason": skipped_reason,
            "no_raw_body_persisted": True,
            "reviewer_hold": reviewer_hold is not None,
            "rollback_note": rollback_by_seed[seed_id],
        }
        manifest_rows.append(row)
        if skipped_reason != "not_skipped" or reviewer_hold is not None:
            skipped_reasons.append(
                {
                    "seed_id": seed_id,
                    "skipped_reason": skipped_reason,
                    "processor_handoff_state": handoff_state,
                    "reviewer_hold": str(reviewer_hold is not None).lower(),
                }
            )

    packet = {
        "dry_run_version": DRY_RUN_VERSION,
        "mode": MODE,
        "input_packet_version": PREFLIGHT_PACKET_VERSION,
        "offline_only": True,
        "source_fixture_policy": {
            "accepted_input": "public refresh preflight packet v5 fixture only",
            "live_crawl_permitted": False,
            "document_download_permitted": False,
            "raw_body_storage_permitted": False,
            "devhub_access_permitted": False,
            "legal_or_permitting_guarantees_permitted": False,
        },
        "selected_public_sources": selected_sources,
        "synthetic_archive_manifest_rows": manifest_rows,
        "redirect_chain_placeholder_policy": "placeholder:not-requested for every row; no network redirects observed",
        "http_status_placeholder_policy": "placeholder:not-requested or placeholder:skipped-before-request only",
        "content_hash_placeholder_policy": "placeholder:not-computed-no-body or placeholder:not-computed-skipped-or-held only",
        "processor_placeholder_policy": "processor name and version remain placeholder:processor-not-invoked",
        "skipped_reasons": skipped_reasons,
        "no_raw_body_flags": [
            {"manifest_id": row["manifest_id"], "no_raw_body_persisted": row["no_raw_body_persisted"]}
            for row in manifest_rows
        ],
        "reviewer_holds": preflight_packet["reviewer_holds"],
        "rollback_notes": preflight_packet["rollback_notes"],
        "prohibited_actions": PROHIBITED_ACTIONS,
        "validation_commands": VALIDATION_COMMANDS,
    }
    assert_valid_public_metadata_manifest_dry_run_v5(packet)
    return packet


def validate_public_metadata_manifest_dry_run_v5(packet: Mapping[str, Any]) -> list[str]:
    """Return fail-closed validation errors for public metadata manifest dry-run v5."""

    if not isinstance(packet, dict):
        return ["packet must be an object"]

    errors: list[str] = []
    for field in REQUIRED_TOP_LEVEL_FIELDS:
        if field not in packet or _missing(packet.get(field)):
            errors.append(f"missing packet.{field}")

    if packet.get("dry_run_version") != DRY_RUN_VERSION:
        errors.append(f"packet.dry_run_version must be {DRY_RUN_VERSION}")
    if packet.get("mode") != MODE:
        errors.append(f"packet.mode must be {MODE}")
    if packet.get("input_packet_version") != PREFLIGHT_PACKET_VERSION:
        errors.append(f"packet.input_packet_version must be {PREFLIGHT_PACKET_VERSION}")
    if packet.get("offline_only") is not True:
        errors.append("packet.offline_only must be true")
    if packet.get("validation_commands") != VALIDATION_COMMANDS:
        errors.append("missing validation_commands or commands are not exact offline validation commands")
    if packet.get("prohibited_actions") != PROHIBITED_ACTIONS:
        errors.append("packet.prohibited_actions must match the dry-run prohibited action list")

    _validate_source_fixture_policy(packet.get("source_fixture_policy"), errors)
    selected_seed_ids = _validate_selected_public_sources(packet.get("selected_public_sources"), errors)
    manifest_ids = _validate_manifest_rows(packet.get("synthetic_archive_manifest_rows"), selected_seed_ids, errors)
    _validate_placeholder_policy(packet.get("redirect_chain_placeholder_policy"), "redirect_chain_placeholder_policy", "placeholder:not-requested", errors)
    _validate_placeholder_policy(packet.get("http_status_placeholder_policy"), "http_status_placeholder_policy", "placeholder:not-requested", errors)
    _validate_placeholder_policy(packet.get("content_hash_placeholder_policy"), "content_hash_placeholder_policy", "placeholder:not-computed", errors)
    _validate_placeholder_policy(packet.get("processor_placeholder_policy"), "processor_placeholder_policy", "processor-not-invoked", errors)
    _validate_skipped_reasons(packet.get("skipped_reasons"), selected_seed_ids, errors)
    _validate_no_raw_body_flags(packet.get("no_raw_body_flags"), manifest_ids, errors)
    _validate_reviewer_holds(packet.get("reviewer_holds"), selected_seed_ids, errors)
    _validate_rollback_notes(packet.get("rollback_notes"), selected_seed_ids, errors)
    _scan_forbidden(packet, "packet", errors)
    return errors


def assert_valid_public_metadata_manifest_dry_run_v5(packet: Mapping[str, Any]) -> None:
    errors = validate_public_metadata_manifest_dry_run_v5(packet)
    if errors:
        raise PublicMetadataManifestDryRunV5ValidationError(errors)


def _by_seed(rows: Any) -> dict[str, Mapping[str, Any]]:
    by_seed: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        by_seed[row["seed_id"]] = row
    return by_seed


def _missing(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


def _require_string(row: Mapping[str, Any], field: str, path: str, errors: list[str]) -> str:
    value = row.get(field)
    if not isinstance(value, str) or not value:
        errors.append(f"missing {path}.{field}")
        return ""
    return value


def _validate_source_fixture_policy(value: Any, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append("packet.source_fixture_policy must be an object")
        return
    if value.get("accepted_input") != "public refresh preflight packet v5 fixture only":
        errors.append("packet.source_fixture_policy.accepted_input must name the preflight packet fixture-only input")
    for field in (
        "live_crawl_permitted",
        "document_download_permitted",
        "raw_body_storage_permitted",
        "devhub_access_permitted",
        "legal_or_permitting_guarantees_permitted",
    ):
        if value.get(field) is not False:
            errors.append(f"packet.source_fixture_policy.{field} must be false")


def _validate_selected_public_sources(value: Any, errors: list[str]) -> set[str]:
    seed_ids: set[str] = set()
    if not isinstance(value, list) or not value:
        errors.append("missing selected public sources")
        return seed_ids
    for index, row in enumerate(value):
        path = f"packet.selected_public_sources[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{path} must be an object")
            continue
        seed_id = _require_string(row, "seed_id", path, errors)
        if seed_id:
            seed_ids.add(seed_id)
        _require_string(row, "source_registry_placeholder_id", path, errors)
        source_registry_ref = _require_string(row, "source_registry_ref", path, errors)
        _require_string(row, "owning_surface", path, errors)
        _require_string(row, "selection_state", path, errors)
        _require_string(row, "processor_handoff_state", path, errors)
        _require_string(row, "skipped_reason", path, errors)
        _require_string(row, "crawl_frequency_label", path, errors)
        if source_registry_ref and not source_registry_ref.startswith("source-registry-placeholder://"):
            errors.append(f"{path}.source_registry_ref must be a source-registry-placeholder:// reference")
        if row.get("reviewer_hold") not in (True, False):
            errors.append(f"{path}.reviewer_hold must be boolean")
    return seed_ids


def _validate_manifest_rows(value: Any, expected_seed_ids: set[str], errors: list[str]) -> set[str]:
    manifest_ids: set[str] = set()
    if not isinstance(value, list) or not value:
        errors.append("missing synthetic ArchiveManifest rows")
        return manifest_ids
    found_seed_ids: set[str] = set()
    for index, row in enumerate(value):
        path = f"packet.synthetic_archive_manifest_rows[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{path} must be an object")
            continue
        manifest_id = _require_string(row, "manifest_id", path, errors)
        if manifest_id:
            manifest_ids.add(manifest_id)
        source_id = _require_string(row, "source_id", path, errors)
        _require_string(row, "source_registry_placeholder_id", path, errors)
        source_registry_ref = _require_string(row, "source_registry_ref", path, errors)
        _require_string(row, "canonical_url", path, errors)
        _require_string(row, "requested_url", path, errors)
        _validate_redirect_chain(row.get("redirect_chain"), path, errors)
        _require_placeholder_string(row, "http_status", path, "placeholder:", "missing redirect-chain or HTTP status placeholders", errors)
        _require_placeholder_string(row, "content_type", path, "placeholder:", "missing content-type placeholder", errors)
        _require_placeholder_string(row, "content_hash", path, "placeholder:not-computed", "missing content-hash placeholders", errors)
        _require_placeholder_string(row, "capture_started_at", path, "placeholder:", "missing capture timestamp placeholders", errors)
        _require_placeholder_string(row, "capture_finished_at", path, "placeholder:", "missing capture timestamp placeholders", errors)
        _require_placeholder_string(row, "processor_name", path, "placeholder:", "missing processor/version placeholders", errors)
        _require_placeholder_string(row, "processor_version", path, "placeholder:", "missing processor/version placeholders", errors)
        _require_string(row, "archive_artifact_ref", path, errors)
        normalized_id = _require_string(row, "normalized_document_id", path, errors)
        _validate_normalized_document_ref(row.get("normalized_document_ref"), normalized_id, path, errors)
        _require_string(row, "skipped_reason", path, errors)
        _require_string(row, "rollback_note", path, errors)
        if source_id.startswith("public-source-placeholder:"):
            found_seed_ids.add(source_id.removeprefix("public-source-placeholder:"))
        if source_registry_ref and not source_registry_ref.startswith("source-registry-placeholder://"):
            errors.append(f"{path}.source_registry_ref must be a source-registry-placeholder:// reference")
        if row.get("archive_artifact_ref") != "placeholder:no-archive-artifact-created":
            errors.append(f"{path}.archive_artifact_ref must not claim archive artifacts")
        if row.get("no_raw_body_persisted") is not True:
            errors.append(f"{path}.no_raw_body_persisted must be true")
        if row.get("reviewer_hold") not in (True, False):
            errors.append(f"{path}.reviewer_hold must be boolean")
    if expected_seed_ids and found_seed_ids != expected_seed_ids:
        errors.append("packet.synthetic_archive_manifest_rows must cover every selected public source seed_id")
    return manifest_ids


def _validate_redirect_chain(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, list) or not value:
        errors.append("missing redirect-chain or HTTP status placeholders")
        return
    for index, hop in enumerate(value):
        hop_path = f"{path}.redirect_chain[{index}]"
        if not isinstance(hop, dict):
            errors.append(f"{hop_path} must be an object")
            continue
        _require_placeholder_string(hop, "from", hop_path, "placeholder:", "missing redirect-chain or HTTP status placeholders", errors)
        _require_placeholder_string(hop, "to", hop_path, "placeholder:", "missing redirect-chain or HTTP status placeholders", errors)
        _require_placeholder_string(hop, "status", hop_path, "placeholder:", "missing redirect-chain or HTTP status placeholders", errors)


def _require_placeholder_string(
    row: Mapping[str, Any],
    field: str,
    path: str,
    prefix: str,
    missing_message: str,
    errors: list[str],
) -> str:
    value = row.get(field)
    if not isinstance(value, str) or not value:
        errors.append(f"missing {path}.{field}")
        return ""
    if not value.startswith(prefix):
        errors.append(f"{path}.{field} must remain a {prefix} placeholder")
    if "placeholder" not in value:
        errors.append(missing_message)
    return value


def _validate_normalized_document_ref(value: Any, normalized_id: str, path: str, errors: list[str]) -> None:
    ref_path = f"{path}.normalized_document_ref"
    if not isinstance(value, dict) or not value:
        errors.append("missing normalized document references")
        return
    document_id = _require_string(value, "document_id", ref_path, errors)
    document_ref = _require_string(value, "document_ref", ref_path, errors)
    _require_placeholder_string(value, "normalization_state", ref_path, "placeholder:", "missing normalized document references", errors)
    if normalized_id and document_id and document_id != normalized_id:
        errors.append(f"{ref_path}.document_id must match normalized_document_id")
    if document_ref and not document_ref.startswith("normalized-document-placeholder://"):
        errors.append(f"{ref_path}.document_ref must be normalized-document-placeholder://")


def _validate_placeholder_policy(value: Any, field: str, required_fragment: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value:
        errors.append(f"missing packet.{field}")
        return
    if required_fragment not in value:
        errors.append(f"packet.{field} must describe {required_fragment} placeholders")


def _validate_skipped_reasons(value: Any, expected_seed_ids: set[str], errors: list[str]) -> None:
    if not isinstance(value, list) or not value:
        errors.append("missing skipped reasons")
        return
    for index, row in enumerate(value):
        path = f"packet.skipped_reasons[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{path} must be an object")
            continue
        seed_id = _require_string(row, "seed_id", path, errors)
        _require_string(row, "skipped_reason", path, errors)
        _require_string(row, "processor_handoff_state", path, errors)
        _require_string(row, "reviewer_hold", path, errors)
        if seed_id and expected_seed_ids and seed_id not in expected_seed_ids:
            errors.append(f"{path}.seed_id must reference selected public sources")


def _validate_no_raw_body_flags(value: Any, expected_manifest_ids: set[str], errors: list[str]) -> None:
    if not isinstance(value, list) or not value:
        errors.append("missing no-raw-body flags")
        return
    found_manifest_ids: set[str] = set()
    for index, row in enumerate(value):
        path = f"packet.no_raw_body_flags[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{path} must be an object")
            continue
        manifest_id = _require_string(row, "manifest_id", path, errors)
        if manifest_id:
            found_manifest_ids.add(manifest_id)
        if row.get("no_raw_body_persisted") is not True:
            errors.append(f"{path}.no_raw_body_persisted must be true")
    if expected_manifest_ids and found_manifest_ids != expected_manifest_ids:
        errors.append("packet.no_raw_body_flags must cover every synthetic ArchiveManifest row")


def _validate_reviewer_holds(value: Any, expected_seed_ids: set[str], errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append("missing reviewer holds")
        return
    if not isinstance(value.get("mapping"), dict) or not value.get("mapping"):
        errors.append("packet.reviewer_holds.mapping must be non-empty")
    if not isinstance(value.get("routing"), dict) or not value.get("routing"):
        errors.append("packet.reviewer_holds.routing must be non-empty")
    rows = value.get("candidate_holds")
    if not isinstance(rows, list) or not rows:
        errors.append("missing reviewer holds")
        return
    for index, row in enumerate(rows):
        path = f"packet.reviewer_holds.candidate_holds[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{path} must be an object")
            continue
        seed_id = _require_string(row, "seed_id", path, errors)
        _require_string(row, "stale_source_hold_key", path, errors)
        _require_string(row, "hold_disposition", path, errors)
        _require_string(row, "reviewer_route", path, errors)
        if seed_id and expected_seed_ids and seed_id not in expected_seed_ids:
            errors.append(f"{path}.seed_id must reference selected public sources")


def _validate_rollback_notes(value: Any, expected_seed_ids: set[str], errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append("missing rollback notes")
        return
    if not isinstance(value.get("packet_level"), str) or not value.get("packet_level"):
        errors.append("missing packet.rollback_notes.packet_level")
    rows = value.get("candidate_level")
    if not isinstance(rows, list) or not rows:
        errors.append("missing rollback notes")
        return
    found_seed_ids: set[str] = set()
    for index, row in enumerate(rows):
        path = f"packet.rollback_notes.candidate_level[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{path} must be an object")
            continue
        seed_id = _require_string(row, "seed_id", path, errors)
        if seed_id:
            found_seed_ids.add(seed_id)
        _require_string(row, "rollback_note", path, errors)
    if expected_seed_ids and found_seed_ids != expected_seed_ids:
        errors.append("packet.rollback_notes.candidate_level must cover every selected public source seed_id")


def _scan_forbidden(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            lowered_key = str(key).lower()
            if lowered_key in ACTIVE_MUTATION_KEYS:
                if child is True or (isinstance(child, list) and child) or (isinstance(child, dict) and child):
                    errors.append(f"active mutation flag must be false, empty, or absent: {child_path}")
            _scan_forbidden(child, child_path, errors)
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            _scan_forbidden(child, f"{path}[{index}]", errors)
        return
    if isinstance(value, str):
        lowered = value.lower()
        for marker in FORBIDDEN_TEXT_MARKERS:
            if marker in lowered:
                errors.append(f"forbidden live, raw, downloaded, private, auth, guarantee, or mutation claim at {path}")
                break


def main() -> int:
    parser = argparse.ArgumentParser(description="Assemble fixture-first public metadata manifest dry-run v5.")
    parser.add_argument("preflight_packet", type=Path)
    args = parser.parse_args()
    packet = assemble_public_metadata_manifest_dry_run_v5(load_preflight_fixture(args.preflight_packet))
    print(json.dumps(packet, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
