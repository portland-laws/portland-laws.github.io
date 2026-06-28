"""Fixture-first public source refresh intake evidence packets.

This module consumes an already-built public source refresh batch packet and an
already-built processor handoff rehearsal packet. It emits synthetic reviewer
intake evidence only. It does not fetch URLs, invoke processors, persist raw
responses, write archive artifacts, or update registry/archive manifests.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from ppd.crawler.processor_handoff_rehearsal_packet import (
    require_valid_processor_handoff_manifest_rehearsal_packet,
)


PACKET_TYPE = "ppd_public_source_refresh_intake_evidence_packet"
PACKET_VERSION = "1.0"

_REQUIRED_ARCHIVE_MANIFEST_FIELDS = (
    "manifest_id",
    "source_id",
    "canonical_url",
    "requested_url",
    "redirect_chain",
    "http_status",
    "content_type",
    "content_hash",
    "capture_started_at",
    "capture_finished_at",
    "processor_name",
    "processor_version",
    "archive_artifact_ref",
    "normalized_document_id",
    "skipped_reason",
    "no_raw_body_persisted",
)

_CONTENT_HASH_EXPECTATION_FIELDS = (
    "content_hash",
    "expected_content_hash_field",
)

_FORBIDDEN_TRUE_KEY_TOKENS = {
    "activearchivemanifestmutation",
    "activearchivemanifestmutationflag",
    "archivemanifestmutationallowed",
    "archivemanifestupdated",
    "archiveartifactwritten",
    "downloadeddocuments",
    "fetchurls",
    "livecrawlexecuted",
    "livecrawlperformed",
    "livecrawlingused",
    "livefetchused",
    "livenetworkinvoked",
    "networkioallowed",
    "processorexecuted",
    "processorinvoked",
    "processorinvocationallowed",
    "rawbodiespersisted",
    "rawbodypersisted",
    "rawbodypersistenceallowed",
    "realcrawlperformed",
    "realdownloadperformed",
    "registrymutationallowed",
    "schedulemutationallowed",
}

_FORBIDDEN_VALUE_MARKERS = (
    "auth_state",
    "cookies.json",
    "credential",
    "localstorage.json",
    "password",
    "session_cookie",
    "storage_state",
    "trace.zip",
    "warc://",
    ".warc",
    "/raw/",
    "raw_crawl",
    "raw-crawl",
    "rawcrawl",
    "crawl_output",
    "crawl-output",
    "crawloutput",
    "downloaded_documents",
    "downloaded-documents",
    "/downloads/",
    "archive_artifacts",
    "archive-artifacts",
    "archive_manifest_output",
    "processor_output",
    "processor-output",
    "processor_outputs",
    "processor-outputs",
)


@dataclass(frozen=True)
class PublicSourceRefreshIntakeEvidenceValidationResult:
    """Validation result for public source refresh intake evidence packets."""

    valid: bool
    errors: tuple[str, ...]


class PublicSourceRefreshIntakeEvidencePacketError(ValueError):
    """Raised when a refresh intake evidence packet is unsafe or incomplete."""


def build_public_source_refresh_intake_evidence_packet(
    public_source_refresh_batch_packet: Mapping[str, Any],
    processor_handoff_rehearsal_packet: Mapping[str, Any],
    *,
    packet_id: str = "fixture-public-source-refresh-intake-evidence-001",
    generated_at: str = "2026-05-29T00:00:00Z",
) -> dict[str, Any]:
    """Build a deterministic reviewer evidence packet from fixture packets."""

    _require_valid_refresh_batch_packet(public_source_refresh_batch_packet)
    require_valid_processor_handoff_manifest_rehearsal_packet(processor_handoff_rehearsal_packet)

    batch_manifests = _sequence(public_source_refresh_batch_packet.get("batch_manifests"))
    handoff_manifests = _sequence(processor_handoff_rehearsal_packet.get("expectedMetadataOnlyArchiveManifests"))
    handoff_attestations = _sequence(processor_handoff_rehearsal_packet.get("noRawBodyAttestations"))
    handoff_manifest_by_source = {
        _text(row.get("source_id")): row
        for row in handoff_manifests
        if isinstance(row, Mapping) and _text(row.get("source_id"))
    }
    handoff_attestation_by_source = {
        _text(row.get("source_id")): row
        for row in handoff_attestations
        if isinstance(row, Mapping) and _text(row.get("source_id"))
    }

    reviewer_rows = []
    no_raw_body_rows = []
    skipped_rows = []
    covered_sources: set[str] = set()

    for index, manifest in enumerate(batch_manifests, start=1):
        if not isinstance(manifest, Mapping):
            continue
        source_id = _text(manifest.get("source_id"))
        canonical_url = _text(manifest.get("canonical_url"))
        covered_sources.add(source_id)
        expected_manifest = handoff_manifest_by_source.get(source_id)
        expected_delta = manifest.get("expected_metadata_only_delta") if isinstance(manifest.get("expected_metadata_only_delta"), Mapping) else {}
        expected_fields = _expected_fields(expected_delta)
        manifest_check = _manifest_expectation_check(source_id, expected_manifest)
        skipped_reason = manifest_check["skipped_reason"]
        attestation_id = "intake-no-raw-body-" + _stable_token(source_id or canonical_url)

        reviewer_rows.append(
            {
                "evidence_id": "review-evidence-" + _stable_token(source_id or canonical_url),
                "batch_order": index,
                "source_id": source_id,
                "canonical_url": canonical_url,
                "synthetic_reviewer_evidence_fields": {
                    "owning_surface": _text(manifest.get("owning_surface")),
                    "source_type": _text(manifest.get("source_type")),
                    "refresh_reason": _text(manifest.get("refresh_reason")),
                    "reviewer_owner_fields": dict(manifest.get("reviewer_owner_fields", {})) if isinstance(manifest.get("reviewer_owner_fields"), Mapping) else {},
                    "expected_metadata_fields": expected_fields,
                    "content_hash_expectation_fields": list(_CONTENT_HASH_EXPECTATION_FIELDS),
                    "manifest_expectation_check": manifest_check,
                    "skipped_target_reason_slot": skipped_reason,
                    "no_raw_body_attestation_id": attestation_id,
                    "rollback_note_ids": [
                        "rollback-note-no-archive-manifest-update",
                        "rollback-note-no-registry-or-schedule-mutation",
                    ],
                },
            }
        )
        no_raw_body_rows.append(
            _intake_no_raw_body_attestation(
                attestation_id=attestation_id,
                source_id=source_id,
                canonical_url=canonical_url,
                upstream_attestation=handoff_attestation_by_source.get(source_id),
            )
        )
        skipped_rows.append(
            {
                "source_id": source_id,
                "canonical_url": canonical_url,
                "skipped_target_reason_slot": skipped_reason,
                "operator_note_required_before_live_run": True,
            }
        )

    for expected_manifest in handoff_manifests:
        if not isinstance(expected_manifest, Mapping):
            continue
        source_id = _text(expected_manifest.get("source_id"))
        if source_id in covered_sources:
            continue
        skipped_rows.append(
            {
                "source_id": source_id,
                "canonical_url": _text(expected_manifest.get("canonical_url")),
                "skipped_target_reason_slot": "processor_handoff_rehearsal_source_not_selected_in_refresh_batch",
                "operator_note_required_before_live_run": True,
            }
        )

    packet = {
        "packet_type": PACKET_TYPE,
        "packet_version": PACKET_VERSION,
        "packet_id": packet_id,
        "generated_at": generated_at,
        "fixture_first": True,
        "metadata_only": True,
        "live_network_invoked": False,
        "processor_invoked": False,
        "raw_bodies_persisted": False,
        "archive_manifest_updated": False,
        "archive_manifest_mutation_allowed": False,
        "registry_updated": False,
        "schedule_updated": False,
        "input_packet_refs": {
            "refresh_batch_packet_type": _text(public_source_refresh_batch_packet.get("packet_type")),
            "refresh_batch_packet_version": _text(public_source_refresh_batch_packet.get("packet_version")),
            "processor_handoff_packet_type": _text(processor_handoff_rehearsal_packet.get("packetType")),
            "processor_handoff_mode": _text(processor_handoff_rehearsal_packet.get("mode")),
        },
        "synthetic_reviewer_evidence": reviewer_rows,
        "manifest_expectation_checks": [row["synthetic_reviewer_evidence_fields"]["manifest_expectation_check"] for row in reviewer_rows],
        "skipped_target_reason_slots": skipped_rows,
        "no_raw_body_attestations": no_raw_body_rows,
        "rollback_notes": [
            {
                "rollback_note_id": "rollback-note-no-archive-manifest-update",
                "scope": "archive_manifest",
                "rollback_required": False,
                "reason": "No archive manifest write or mutation is performed by this fixture intake packet.",
            },
            {
                "rollback_note_id": "rollback-note-no-registry-or-schedule-mutation",
                "scope": "source_registry_and_refresh_schedule",
                "rollback_required": False,
                "reason": "No source registry or refresh schedule mutation is performed by this fixture intake packet.",
            },
            {
                "rollback_note_id": "rollback-note-discard-synthetic-evidence-only",
                "scope": "reviewer_evidence_packet",
                "rollback_required": False,
                "reason": "Synthetic reviewer evidence can be discarded without touching crawler, processor, archive, or registry state.",
            },
        ],
        "intake_summary": {
            "refresh_batch_target_count": len(batch_manifests),
            "reviewer_evidence_count": len(reviewer_rows),
            "manifest_expectation_check_count": len(reviewer_rows),
            "skipped_target_reason_slot_count": len(skipped_rows),
            "no_raw_body_attestation_count": len(no_raw_body_rows),
            "archive_manifest_updated": False,
            "archive_manifest_mutation_allowed": False,
        },
    }
    require_valid_public_source_refresh_intake_evidence_packet(packet)
    return packet


def validate_public_source_refresh_intake_evidence_packet(
    packet: Mapping[str, Any],
) -> PublicSourceRefreshIntakeEvidenceValidationResult:
    """Validate a public source refresh intake evidence packet."""

    errors: list[str] = []
    if not isinstance(packet, Mapping):
        return PublicSourceRefreshIntakeEvidenceValidationResult(False, ("packet must be an object",))

    _collect_forbidden_content(packet, "$", errors)

    if packet.get("packet_type") != PACKET_TYPE:
        errors.append("packet_type must be " + PACKET_TYPE)
    if packet.get("packet_version") != PACKET_VERSION:
        errors.append("packet_version must be " + PACKET_VERSION)
    if not _text(packet.get("packet_id")):
        errors.append("packet_id is required")
    if not _text(packet.get("generated_at")).endswith("Z"):
        errors.append("generated_at must be an ISO UTC timestamp ending in Z")
    for key in ("fixture_first", "metadata_only"):
        if packet.get(key) is not True:
            errors.append(key + " must be true")
    for key in (
        "live_network_invoked",
        "processor_invoked",
        "raw_bodies_persisted",
        "archive_manifest_updated",
        "archive_manifest_mutation_allowed",
        "registry_updated",
        "schedule_updated",
    ):
        if packet.get(key) is not False:
            errors.append(key + " must be false")

    evidence_rows = _require_list(packet.get("synthetic_reviewer_evidence"), "synthetic_reviewer_evidence", errors)
    manifest_checks = _require_list(packet.get("manifest_expectation_checks"), "manifest_expectation_checks", errors)
    skipped_slots = _require_list(packet.get("skipped_target_reason_slots"), "skipped_target_reason_slots", errors)
    attestations = _require_list(packet.get("no_raw_body_attestations"), "no_raw_body_attestations", errors)
    rollback_notes = _require_list(packet.get("rollback_notes"), "rollback_notes", errors)

    if not evidence_rows:
        errors.append("synthetic_reviewer_evidence must include at least one row")
    if len(manifest_checks) != len(evidence_rows):
        errors.append("manifest_expectation_checks must match synthetic_reviewer_evidence count")
    if len(attestations) != len(evidence_rows):
        errors.append("no_raw_body_attestations must match synthetic_reviewer_evidence count")
    if not rollback_notes:
        errors.append("rollback_notes must not be empty")

    attestation_ids = set()
    for index, row in enumerate(attestations):
        prefix = "no_raw_body_attestations[" + str(index) + "]"
        if not isinstance(row, Mapping):
            errors.append(prefix + " must be an object")
            continue
        attestation_id = _text(row.get("attestation_id"))
        if not attestation_id:
            errors.append(prefix + ".attestation_id is required")
        else:
            attestation_ids.add(attestation_id)
        if not _text(row.get("source_id")):
            errors.append(prefix + ".source_id is required")
        if not _text(row.get("canonical_url")):
            errors.append(prefix + ".canonical_url is required")
        if not _text(row.get("attestation")):
            errors.append(prefix + ".attestation is required")
        for key in ("no_raw_body_persisted", "metadata_only"):
            if row.get(key) is not True:
                errors.append(prefix + "." + key + " must be true")
        for key in ("raw_body_persisted", "processor_invoked", "live_network_invoked", "archive_artifact_written"):
            if row.get(key) is not False:
                errors.append(prefix + "." + key + " must be false")

    manifest_check_ids = set()
    for index, check in enumerate(manifest_checks):
        prefix = "manifest_expectation_checks[" + str(index) + "]"
        if not isinstance(check, Mapping):
            errors.append(prefix + " must be an object")
            continue
        check_id = _text(check.get("check_id"))
        if not check_id:
            errors.append(prefix + ".check_id is required")
        else:
            manifest_check_ids.add(check_id)
        if not _text(check.get("source_id")):
            errors.append(prefix + ".source_id is required")
        if check.get("required_manifest_fields") != list(_REQUIRED_ARCHIVE_MANIFEST_FIELDS):
            errors.append(prefix + ".required_manifest_fields must match archive manifest contract")
        if not _contains_all_text(check.get("content_hash_expectation_fields"), _CONTENT_HASH_EXPECTATION_FIELDS):
            errors.append(prefix + ".content_hash_expectation_fields must include content_hash and expected_content_hash_field")
        if check.get("archive_manifest_update_allowed") is not False:
            errors.append(prefix + ".archive_manifest_update_allowed must be false")
        if check.get("archive_manifest_mutation_allowed") is not False:
            errors.append(prefix + ".archive_manifest_mutation_allowed must be false")
        if check.get("raw_body_persistence_allowed") is not False:
            errors.append(prefix + ".raw_body_persistence_allowed must be false")
        if check.get("no_raw_body_persisted") is not True:
            errors.append(prefix + ".no_raw_body_persisted must be true")
        if check.get("archive_artifact_ref_empty") is not True:
            errors.append(prefix + ".archive_artifact_ref_empty must be true")
        if not _text(check.get("skipped_reason")):
            errors.append(prefix + ".skipped_reason is required")

    rollback_ids = set()
    for index, note in enumerate(rollback_notes):
        prefix = "rollback_notes[" + str(index) + "]"
        if not isinstance(note, Mapping):
            errors.append(prefix + " must be an object")
            continue
        rollback_id = _text(note.get("rollback_note_id"))
        if rollback_id:
            rollback_ids.add(rollback_id)
        for key in ("rollback_note_id", "scope", "reason"):
            if not _text(note.get(key)):
                errors.append(prefix + "." + key + " is required")
        if note.get("rollback_required") is not False:
            errors.append(prefix + ".rollback_required must be false")

    skipped_sources = set()
    for index, slot in enumerate(skipped_slots):
        prefix = "skipped_target_reason_slots[" + str(index) + "]"
        if not isinstance(slot, Mapping):
            errors.append(prefix + " must be an object")
            continue
        source_id = _text(slot.get("source_id"))
        if not source_id:
            errors.append(prefix + ".source_id is required")
        else:
            skipped_sources.add(source_id)
        if not _text(slot.get("skipped_target_reason_slot")):
            errors.append(prefix + ".skipped_target_reason_slot is required")
        if slot.get("operator_note_required_before_live_run") is not True:
            errors.append(prefix + ".operator_note_required_before_live_run must be true")

    for index, row in enumerate(evidence_rows):
        prefix = "synthetic_reviewer_evidence[" + str(index) + "]"
        if not isinstance(row, Mapping):
            errors.append(prefix + " must be an object")
            continue
        source_id = _text(row.get("source_id"))
        for key in ("evidence_id", "source_id", "canonical_url"):
            if not _text(row.get(key)):
                errors.append(prefix + "." + key + " is required")
        fields = row.get("synthetic_reviewer_evidence_fields")
        if not isinstance(fields, Mapping):
            errors.append(prefix + ".synthetic_reviewer_evidence_fields must be an object")
            continue
        if not _text(fields.get("refresh_reason")):
            errors.append(prefix + ".synthetic_reviewer_evidence_fields.refresh_reason is required")
        if not isinstance(fields.get("expected_metadata_fields"), list) or not fields.get("expected_metadata_fields"):
            errors.append(prefix + ".synthetic_reviewer_evidence_fields.expected_metadata_fields must not be empty")
        if not _contains_all_text(fields.get("content_hash_expectation_fields"), _CONTENT_HASH_EXPECTATION_FIELDS):
            errors.append(prefix + ".synthetic_reviewer_evidence_fields.content_hash_expectation_fields must include content_hash and expected_content_hash_field")
        if not _contains_text(fields.get("expected_metadata_fields"), "content_hash"):
            errors.append(prefix + ".synthetic_reviewer_evidence_fields.expected_metadata_fields must include content_hash")
        if not _text(fields.get("skipped_target_reason_slot")):
            errors.append(prefix + ".synthetic_reviewer_evidence_fields.skipped_target_reason_slot is required")
        if source_id and source_id not in skipped_sources:
            errors.append(prefix + ".source_id must have a skipped_target_reason_slot entry")
        attestation_id = _text(fields.get("no_raw_body_attestation_id"))
        if attestation_id not in attestation_ids:
            errors.append(prefix + ".synthetic_reviewer_evidence_fields.no_raw_body_attestation_id must reference an attestation")
        check = fields.get("manifest_expectation_check")
        if not isinstance(check, Mapping) or _text(check.get("check_id")) not in manifest_check_ids:
            errors.append(prefix + ".synthetic_reviewer_evidence_fields.manifest_expectation_check must reference a manifest check")
        rollback_note_refs = fields.get("rollback_note_ids")
        if not isinstance(rollback_note_refs, list) or not rollback_note_refs:
            errors.append(prefix + ".synthetic_reviewer_evidence_fields.rollback_note_ids must not be empty")
        else:
            for rollback_note_id in rollback_note_refs:
                if _text(rollback_note_id) not in rollback_ids:
                    errors.append(prefix + ".synthetic_reviewer_evidence_fields.rollback_note_ids must reference rollback_notes")

    summary = packet.get("intake_summary")
    if not isinstance(summary, Mapping):
        errors.append("intake_summary must be an object")
    else:
        expected_counts = {
            "reviewer_evidence_count": len(evidence_rows),
            "manifest_expectation_check_count": len(manifest_checks),
            "skipped_target_reason_slot_count": len(skipped_slots),
            "no_raw_body_attestation_count": len(attestations),
        }
        for key, expected in expected_counts.items():
            if summary.get(key) != expected:
                errors.append("intake_summary." + key + " must be " + str(expected))
        for key in ("archive_manifest_updated", "archive_manifest_mutation_allowed"):
            if summary.get(key) is not False:
                errors.append("intake_summary." + key + " must be false")

    return PublicSourceRefreshIntakeEvidenceValidationResult(valid=not errors, errors=tuple(dict.fromkeys(errors)))


def require_valid_public_source_refresh_intake_evidence_packet(packet: Mapping[str, Any]) -> None:
    """Raise when a public source refresh intake evidence packet is unsafe."""

    result = validate_public_source_refresh_intake_evidence_packet(packet)
    if not result.valid:
        raise PublicSourceRefreshIntakeEvidencePacketError("; ".join(result.errors))


def _require_valid_refresh_batch_packet(packet: Mapping[str, Any]) -> None:
    errors: list[str] = []
    if packet.get("packet_type") != "ppd_public_source_refresh_batch_packet":
        errors.append("refresh batch packet_type is invalid")
    if packet.get("fixture_first") is not True:
        errors.append("refresh batch must be fixture_first")
    side_effect_boundary = packet.get("side_effect_boundary")
    if not isinstance(side_effect_boundary, Mapping):
        errors.append("refresh batch side_effect_boundary is required")
    else:
        for key in (
            "network_io_allowed",
            "processor_invocation_allowed",
            "downloads_allowed",
            "schedule_mutation_allowed",
            "registry_mutation_allowed",
            "raw_body_persistence_allowed",
        ):
            if side_effect_boundary.get(key) is not False:
                errors.append("refresh batch side_effect_boundary." + key + " must be false")
    manifests = _sequence(packet.get("batch_manifests"))
    if not manifests:
        errors.append("refresh batch must include batch_manifests")
    for index, manifest in enumerate(manifests):
        prefix = "refresh batch batch_manifests[" + str(index) + "]"
        if not isinstance(manifest, Mapping):
            errors.append(prefix + " must be an object")
            continue
        for key in ("source_id", "canonical_url", "refresh_reason", "expected_metadata_only_delta"):
            if key not in manifest:
                errors.append(prefix + "." + key + " is required")
        if not _text(manifest.get("source_id")):
            errors.append(prefix + ".source_id is required")
        expected_delta = manifest.get("expected_metadata_only_delta")
        if isinstance(expected_delta, Mapping):
            if expected_delta.get("metadata_only") is not True:
                errors.append(prefix + ".expected_metadata_only_delta.metadata_only must be true")
            if not _contains_text(_expected_fields(expected_delta), "content_hash"):
                errors.append(prefix + ".expected_metadata_only_delta.expected_fields must include content_hash")
            for key in ("registry_mutation_allowed", "schedule_mutation_allowed"):
                if expected_delta.get(key) is not False:
                    errors.append(prefix + ".expected_metadata_only_delta." + key + " must be false")
    if errors:
        raise PublicSourceRefreshIntakeEvidencePacketError("invalid public source refresh batch packet: " + "; ".join(errors))


def _manifest_expectation_check(source_id: str, expected_manifest: Mapping[str, Any] | None) -> dict[str, Any]:
    missing_fields: list[str] = []
    if expected_manifest is None:
        missing_fields = list(_REQUIRED_ARCHIVE_MANIFEST_FIELDS)
        skipped_reason = "processor_handoff_rehearsal_missing_for_refresh_batch_target"
        archive_artifact_ref_empty = True
        no_raw_body_persisted = True
    else:
        for field in _REQUIRED_ARCHIVE_MANIFEST_FIELDS:
            if field not in expected_manifest:
                missing_fields.append(field)
        skipped_reason = _text(expected_manifest.get("skipped_reason"), "rehearsal_only_processor_not_invoked")
        archive_artifact_ref_empty = expected_manifest.get("archive_artifact_ref") in (None, "")
        no_raw_body_persisted = expected_manifest.get("no_raw_body_persisted") is True

    return {
        "check_id": "manifest-check-" + _stable_token(source_id),
        "source_id": source_id,
        "required_manifest_fields": list(_REQUIRED_ARCHIVE_MANIFEST_FIELDS),
        "content_hash_expectation_fields": list(_CONTENT_HASH_EXPECTATION_FIELDS),
        "missing_required_manifest_fields": missing_fields,
        "archive_artifact_ref_empty": archive_artifact_ref_empty,
        "no_raw_body_persisted": no_raw_body_persisted,
        "archive_manifest_update_allowed": False,
        "archive_manifest_mutation_allowed": False,
        "raw_body_persistence_allowed": False,
        "skipped_reason": skipped_reason,
    }


def _intake_no_raw_body_attestation(
    *,
    attestation_id: str,
    source_id: str,
    canonical_url: str,
    upstream_attestation: Mapping[str, Any] | None,
) -> dict[str, Any]:
    return {
        "attestation_id": attestation_id,
        "source_id": source_id,
        "canonical_url": canonical_url,
        "upstream_attestation_id": _text(upstream_attestation.get("attestation_id")) if isinstance(upstream_attestation, Mapping) else None,
        "metadata_only": True,
        "no_raw_body_persisted": True,
        "raw_body_persisted": False,
        "processor_invoked": False,
        "live_network_invoked": False,
        "archive_artifact_written": False,
        "attestation": "Reviewer intake uses fixture metadata only; no response body, processor output, archive artifact, or manifest mutation is present.",
    }


def _expected_fields(expected_delta: Any) -> list[str]:
    if not isinstance(expected_delta, Mapping):
        return ["content_hash", "review_packet_status"]
    fields = expected_delta.get("expected_fields")
    result: list[str] = []
    if isinstance(fields, Sequence) and not isinstance(fields, (str, bytes)):
        for row in fields:
            if isinstance(row, Mapping) and _text(row.get("field")):
                result.append(_text(row.get("field")))
            elif isinstance(row, str) and row.strip():
                result.append(row.strip())
    if "content_hash" not in result:
        result.insert(0, "content_hash")
    return result or ["content_hash", "review_packet_status"]


def _collect_forbidden_content(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if _normalized_key(key_text) in _FORBIDDEN_TRUE_KEY_TOKENS and child not in (None, "", [], {}, False):
                errors.append(path + "." + key_text + " must be false or empty in refresh intake evidence packets")
            _collect_forbidden_content(child, path + "." + key_text, errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _collect_forbidden_content(child, path + "[" + str(index) + "]", errors)
    elif isinstance(value, str):
        lower_value = value.lower()
        for marker in _FORBIDDEN_VALUE_MARKERS:
            if marker in lower_value:
                errors.append(path + " contains forbidden private, archive, raw, download, processor output, or authenticated marker " + marker)


def _contains_text(values: Any, expected: str) -> bool:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        return False
    return expected in {_text(value) for value in values}


def _contains_all_text(values: Any, expected_values: Sequence[str]) -> bool:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        return False
    present = {_text(value) for value in values}
    return all(expected in present for expected in expected_values)


def _normalized_key(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def _require_list(value: Any, field: str, errors: list[str]) -> list[Any]:
    if not isinstance(value, list):
        errors.append(field + " must be a list")
        return []
    return value


def _sequence(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return []


def _text(value: Any, default: str = "") -> str:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else default
    return default


def _stable_token(value: str) -> str:
    lowered = value.strip().lower()
    chars = [character if character.isalnum() else "-" for character in lowered]
    return "-".join(part for part in "".join(chars).split("-") if part) or "unknown"


__all__ = [
    "PACKET_TYPE",
    "PACKET_VERSION",
    "PublicSourceRefreshIntakeEvidencePacketError",
    "PublicSourceRefreshIntakeEvidenceValidationResult",
    "build_public_source_refresh_intake_evidence_packet",
    "require_valid_public_source_refresh_intake_evidence_packet",
    "validate_public_source_refresh_intake_evidence_packet",
]
