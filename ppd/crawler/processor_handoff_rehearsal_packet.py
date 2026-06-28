"""Fixture-first processor handoff manifest rehearsal packets.

This module consumes a validated public source registry coverage gap packet and
public-source recrawl dry-run command plan. It emits synthetic processor
handoff prerequisites, expected metadata-only archive manifest fields,
processor policy/version notes, no-raw-body attestations, and abort conditions
without invoking processors or writing archive artifacts.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from ppd.crawler.public_source_recrawl_dry_run_command_plan import (
    validate_public_source_recrawl_dry_run_command_plan,
)
from ppd.source_registry_coverage_gap_packet import (
    require_valid_public_source_registry_coverage_gap_packet,
)


PACKET_TYPE = "ppd_processor_handoff_manifest_rehearsal_packet"
SCHEMA_VERSION = 1
MODE = "fixture_first_processor_handoff_manifest_rehearsal"

_FORBIDDEN_TRUE_KEYS = {
    "archiveArtifactWritten",
    "archive_artifact_written",
    "documentsDownloaded",
    "executeProcessor",
    "fetchLive",
    "liveCrawlingUsed",
    "liveFetchUsed",
    "processorInvoked",
    "processor_invoked",
    "rawBodiesPersisted",
    "rawBodyPersisted",
    "raw_body_persisted",
    "writeArchiveArtifact",
}

_FORBIDDEN_VALUE_MARKERS = (
    "auth_state",
    "cookies.json",
    "credential",
    "downloaded_documents",
    "localstorage.json",
    "password",
    "raw_body",
    "raw_html",
    "response_body",
    "session_cookie",
    "storage_state",
    "trace.zip",
    "warc://",
)

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


@dataclass(frozen=True)
class ProcessorHandoffRehearsalValidationResult:
    """Validation result for processor handoff rehearsal packets."""

    valid: bool
    errors: tuple[str, ...]


class ProcessorHandoffRehearsalPacketError(ValueError):
    """Raised when a rehearsal packet is unsafe or incomplete."""


def build_processor_handoff_manifest_rehearsal_packet(
    public_source_registry_coverage_gap_packet: Mapping[str, Any],
    public_source_recrawl_dry_run_command_plan: Mapping[str, Any],
    *,
    generated_at: str,
    processor_name: str = "ipfs_datasets_py.web_archive_processor",
    processor_version: str = "fixture-rehearsal-no-execution",
) -> dict[str, Any]:
    """Build a deterministic processor handoff rehearsal packet from fixtures."""

    coverage_packet = deepcopy(dict(public_source_registry_coverage_gap_packet))
    require_valid_public_source_registry_coverage_gap_packet(coverage_packet)

    dry_run_plan = deepcopy(dict(public_source_recrawl_dry_run_command_plan))
    dry_run_issues = validate_public_source_recrawl_dry_run_command_plan(dry_run_plan)
    if dry_run_issues:
        detail = "; ".join(f"{issue.code}: {issue.message}" for issue in dry_run_issues)
        raise ProcessorHandoffRehearsalPacketError("invalid recrawl dry-run command plan: " + detail)

    targets_by_url = _targets_by_url(dry_run_plan)
    covered_sources = list(coverage_packet.get("citedCoveredAnchors", []))
    prerequisite_rows = [
        _processor_prerequisite(row, targets_by_url, dry_run_plan)
        for row in covered_sources
        if isinstance(row, Mapping)
    ]
    manifest_rows = [
        _expected_archive_manifest(row, processor_name, processor_version)
        for row in prerequisite_rows
    ]
    missing_abort_rows = [
        {
            "abort_id": "coverage-gap-" + _stable_token(_text(row.get("source_id"), _text(row.get("canonical_url")))),
            "source_id": _text(row.get("source_id")),
            "canonical_url": _text(row.get("canonical_url")),
            "condition": _text(row.get("missing_reason"), "source is not ready for processor handoff"),
            "source_evidence_ids": _text_list(row.get("source_evidence_ids")),
        }
        for row in coverage_packet.get("missingAnchors", [])
        if isinstance(row, Mapping)
    ]

    packet = {
        "schemaVersion": SCHEMA_VERSION,
        "packetType": PACKET_TYPE,
        "mode": MODE,
        "generatedAt": generated_at,
        "fixtureFirst": True,
        "metadataOnly": True,
        "processorInvocationAllowed": False,
        "processorInvoked": False,
        "archiveArtifactWritesAllowed": False,
        "archiveArtifactWritten": False,
        "rawBodiesPersisted": False,
        "inputPacketRefs": {
            "coverageGapPacketType": _text(coverage_packet.get("packetType")),
            "coverageGapSourceMode": _text(coverage_packet.get("sourceMode")),
            "recrawlDryRunMode": _text(dry_run_plan.get("mode"), "public_source_recrawl_dry_run_command_plan"),
        },
        "processorPolicyVersionNotes": {
            "processor_name": processor_name,
            "processor_version": processor_version,
            "policy": "metadata_only_prerequisite_rehearsal_before_processor_invocation",
            "version_note": "Synthetic fixture packet only; processor versions are expected metadata fields, not executed code.",
            "requires_separate_live_approval": True,
        },
        "syntheticProcessorPrerequisites": prerequisite_rows,
        "expectedMetadataOnlyArchiveManifests": manifest_rows,
        "noRawBodyAttestations": _no_raw_body_attestations(prerequisite_rows),
        "abortConditions": _abort_conditions(dry_run_plan, missing_abort_rows),
        "rehearsalSummary": {
            "coveredSourceCount": len(prerequisite_rows),
            "expectedManifestCount": len(manifest_rows),
            "coverageGapAbortCount": len(missing_abort_rows),
            "processorInvoked": False,
            "archiveArtifactWritten": False,
            "rawBodiesPersisted": False,
        },
    }

    require_valid_processor_handoff_manifest_rehearsal_packet(packet)
    return packet


def validate_processor_handoff_manifest_rehearsal_packet(
    packet: Mapping[str, Any],
) -> ProcessorHandoffRehearsalValidationResult:
    """Validate a fixture-first processor handoff rehearsal packet."""

    errors: list[str] = []
    _collect_forbidden_content(packet, "$", errors)

    if packet.get("schemaVersion") != SCHEMA_VERSION:
        errors.append("schemaVersion must be 1")
    if packet.get("packetType") != PACKET_TYPE:
        errors.append("packetType must be " + PACKET_TYPE)
    if packet.get("mode") != MODE:
        errors.append("mode must be " + MODE)
    if not str(packet.get("generatedAt", "")).endswith("Z"):
        errors.append("generatedAt must be an ISO UTC timestamp ending in Z")

    for key in ("fixtureFirst", "metadataOnly"):
        if packet.get(key) is not True:
            errors.append(f"{key} must be true")
    for key in (
        "processorInvocationAllowed",
        "processorInvoked",
        "archiveArtifactWritesAllowed",
        "archiveArtifactWritten",
        "rawBodiesPersisted",
    ):
        if packet.get(key) is not False:
            errors.append(f"{key} must be false")

    prerequisites = _require_list(packet.get("syntheticProcessorPrerequisites"), "syntheticProcessorPrerequisites", errors)
    manifests = _require_list(packet.get("expectedMetadataOnlyArchiveManifests"), "expectedMetadataOnlyArchiveManifests", errors)
    attestations = _require_list(packet.get("noRawBodyAttestations"), "noRawBodyAttestations", errors)
    aborts = _require_list(packet.get("abortConditions"), "abortConditions", errors)

    _validate_prerequisites(prerequisites, errors)
    _validate_expected_manifests(manifests, errors)
    _validate_attestations(attestations, errors)
    _validate_abort_conditions(aborts, errors)
    _validate_policy_notes(packet.get("processorPolicyVersionNotes"), errors)

    if not prerequisites:
        errors.append("syntheticProcessorPrerequisites must include at least one covered source")
    if len(manifests) != len(prerequisites):
        errors.append("expectedMetadataOnlyArchiveManifests must match syntheticProcessorPrerequisites count")
    if len(attestations) != len(prerequisites):
        errors.append("noRawBodyAttestations must match syntheticProcessorPrerequisites count")
    if not aborts:
        errors.append("abortConditions must include dry-run and coverage-gap abort gates")

    summary = packet.get("rehearsalSummary")
    if not isinstance(summary, Mapping):
        errors.append("rehearsalSummary must be an object")
    else:
        expected_counts = {
            "coveredSourceCount": len(prerequisites),
            "expectedManifestCount": len(manifests),
        }
        for key, expected in expected_counts.items():
            if summary.get(key) != expected:
                errors.append(f"rehearsalSummary.{key} must be {expected}")
        for key in ("processorInvoked", "archiveArtifactWritten", "rawBodiesPersisted"):
            if summary.get(key) is not False:
                errors.append(f"rehearsalSummary.{key} must be false")

    return ProcessorHandoffRehearsalValidationResult(valid=not errors, errors=tuple(errors))


def require_valid_processor_handoff_manifest_rehearsal_packet(packet: Mapping[str, Any]) -> None:
    """Raise when a processor handoff rehearsal packet is unsafe."""

    result = validate_processor_handoff_manifest_rehearsal_packet(packet)
    if not result.valid:
        raise ProcessorHandoffRehearsalPacketError("; ".join(result.errors))


def _processor_prerequisite(row: Mapping[str, Any], targets_by_url: Mapping[str, Mapping[str, Any]], plan: Mapping[str, Any]) -> dict[str, Any]:
    canonical_url = _text(row.get("canonical_url"))
    source_id = _text(row.get("source_id"))
    target = targets_by_url.get(canonical_url, {})
    return {
        "prerequisite_id": "processor-prereq-" + _stable_token(source_id or canonical_url),
        "source_id": source_id,
        "canonical_url": canonical_url,
        "requested_url": _text(target.get("url"), canonical_url),
        "source_evidence_ids": _text_list(row.get("source_evidence_ids")),
        "robots_evidence_id": _text(plan.get("robots_txt_evidence") or plan.get("robots_evidence")),
        "policy_evidence_id": _text(plan.get("policy_evidence")),
        "rate_limit_note": _text(plan.get("rate_limit_notes"), "metadata-only rehearsal does not open a network connection"),
        "processor_input_kind": "metadata_only_synthetic_prerequisite",
        "processorInvocationAllowed": False,
        "archiveArtifactWritesAllowed": False,
        "no_raw_body_persisted": True,
    }


def _expected_archive_manifest(row: Mapping[str, Any], processor_name: str, processor_version: str) -> dict[str, Any]:
    source_id = _text(row.get("source_id"))
    canonical_url = _text(row.get("canonical_url"))
    return {
        "manifest_id": "archive-manifest-rehearsal-" + _stable_token(source_id or canonical_url),
        "source_id": source_id,
        "canonical_url": canonical_url,
        "requested_url": _text(row.get("requested_url"), canonical_url),
        "redirect_chain": [],
        "http_status": "expected_metadata_only_not_fetched",
        "content_type": "expected_metadata_only_pending_capture",
        "content_hash": "expected_metadata_only_pending_capture",
        "capture_started_at": None,
        "capture_finished_at": None,
        "processor_name": processor_name,
        "processor_version": processor_version,
        "archive_artifact_ref": None,
        "normalized_document_id": "expected-normalized-document-" + _stable_token(source_id or canonical_url),
        "skipped_reason": "rehearsal_only_processor_not_invoked",
        "no_raw_body_persisted": True,
        "metadata_only": True,
    }


def _no_raw_body_attestations(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "attestation_id": "no-raw-body-" + _stable_token(_text(row.get("source_id"), _text(row.get("canonical_url")))),
            "source_id": _text(row.get("source_id")),
            "canonical_url": _text(row.get("canonical_url")),
            "raw_body_persisted": False,
            "archive_artifact_written": False,
            "attestation": "Only metadata-only expected manifest fields are rehearsed; no raw response body or archive artifact exists.",
        }
        for row in rows
    ]


def _abort_conditions(plan: Mapping[str, Any], coverage_gap_aborts: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    aborts: list[dict[str, Any]] = []
    raw_plan_aborts = plan.get("abort_conditions") or []
    if isinstance(raw_plan_aborts, str):
        raw_plan_aborts = [raw_plan_aborts]
    if isinstance(raw_plan_aborts, Sequence):
        for index, condition in enumerate(raw_plan_aborts, start=1):
            text = _text(condition)
            if text:
                aborts.append(
                    {
                        "abort_id": f"recrawl-dry-run-abort-{index:02d}",
                        "condition": text,
                        "source": "public_source_recrawl_dry_run_command_plan",
                    }
                )
    aborts.extend(dict(row) for row in coverage_gap_aborts)
    aborts.extend(
        [
            {
                "abort_id": "processor-invocation-requested",
                "condition": "Abort if any step would invoke ipfs_datasets_py or another processor from this rehearsal packet.",
                "source": "processor_handoff_policy",
            },
            {
                "abort_id": "archive-artifact-write-requested",
                "condition": "Abort if any step would write WARC, archive, downloaded document, or normalized document artifacts.",
                "source": "processor_handoff_policy",
            },
            {
                "abort_id": "raw-body-persistence-requested",
                "condition": "Abort if any field contains raw HTML, response bodies, screenshots, traces, credentials, cookies, or session state.",
                "source": "processor_handoff_policy",
            },
        ]
    )
    return aborts


def _validate_prerequisites(rows: Sequence[Any], errors: list[str]) -> None:
    for index, row in enumerate(rows):
        prefix = f"syntheticProcessorPrerequisites[{index}]"
        if not isinstance(row, Mapping):
            errors.append(prefix + " must be an object")
            continue
        for key in ("prerequisite_id", "source_id", "canonical_url", "requested_url", "robots_evidence_id", "policy_evidence_id", "rate_limit_note"):
            if not _text(row.get(key)):
                errors.append(f"{prefix}.{key} is required")
        if not _text_list(row.get("source_evidence_ids")):
            errors.append(f"{prefix}.source_evidence_ids must cite at least one evidence id")
        if row.get("processorInvocationAllowed") is not False:
            errors.append(f"{prefix}.processorInvocationAllowed must be false")
        if row.get("archiveArtifactWritesAllowed") is not False:
            errors.append(f"{prefix}.archiveArtifactWritesAllowed must be false")
        if row.get("no_raw_body_persisted") is not True:
            errors.append(f"{prefix}.no_raw_body_persisted must be true")


def _validate_expected_manifests(rows: Sequence[Any], errors: list[str]) -> None:
    seen: set[str] = set()
    for index, row in enumerate(rows):
        prefix = f"expectedMetadataOnlyArchiveManifests[{index}]"
        if not isinstance(row, Mapping):
            errors.append(prefix + " must be an object")
            continue
        for key in _REQUIRED_ARCHIVE_MANIFEST_FIELDS:
            if key not in row:
                errors.append(f"{prefix}.{key} is required")
        manifest_id = _text(row.get("manifest_id"))
        if not manifest_id:
            errors.append(f"{prefix}.manifest_id is required")
        elif manifest_id in seen:
            errors.append(f"{prefix}.manifest_id must be unique")
        seen.add(manifest_id)
        for key in ("source_id", "canonical_url", "requested_url", "processor_name", "processor_version", "normalized_document_id", "skipped_reason"):
            if not _text(row.get(key)):
                errors.append(f"{prefix}.{key} is required")
        if row.get("archive_artifact_ref") not in (None, ""):
            errors.append(f"{prefix}.archive_artifact_ref must be empty for rehearsal packets")
        if row.get("no_raw_body_persisted") is not True:
            errors.append(f"{prefix}.no_raw_body_persisted must be true")
        if row.get("metadata_only") is not True:
            errors.append(f"{prefix}.metadata_only must be true")


def _validate_attestations(rows: Sequence[Any], errors: list[str]) -> None:
    for index, row in enumerate(rows):
        prefix = f"noRawBodyAttestations[{index}]"
        if not isinstance(row, Mapping):
            errors.append(prefix + " must be an object")
            continue
        for key in ("attestation_id", "source_id", "canonical_url", "attestation"):
            if not _text(row.get(key)):
                errors.append(f"{prefix}.{key} is required")
        if row.get("raw_body_persisted") is not False:
            errors.append(f"{prefix}.raw_body_persisted must be false")
        if row.get("archive_artifact_written") is not False:
            errors.append(f"{prefix}.archive_artifact_written must be false")


def _validate_abort_conditions(rows: Sequence[Any], errors: list[str]) -> None:
    for index, row in enumerate(rows):
        prefix = f"abortConditions[{index}]"
        if not isinstance(row, Mapping):
            errors.append(prefix + " must be an object")
            continue
        if not _text(row.get("abort_id")):
            errors.append(f"{prefix}.abort_id is required")
        if not _text(row.get("condition")):
            errors.append(f"{prefix}.condition is required")


def _validate_policy_notes(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("processorPolicyVersionNotes must be an object")
        return
    for key in ("processor_name", "processor_version", "policy", "version_note"):
        if not _text(value.get(key)):
            errors.append(f"processorPolicyVersionNotes.{key} is required")
    if value.get("requires_separate_live_approval") is not True:
        errors.append("processorPolicyVersionNotes.requires_separate_live_approval must be true")


def _collect_forbidden_content(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if key_text in _FORBIDDEN_TRUE_KEYS and child not in (None, "", [], {}, False):
                errors.append(f"{path}.{key_text} must be false or empty in processor handoff rehearsals")
            _collect_forbidden_content(child, f"{path}.{key_text}", errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _collect_forbidden_content(child, f"{path}[{index}]", errors)
    elif isinstance(value, str):
        lower_value = value.lower()
        for marker in _FORBIDDEN_VALUE_MARKERS:
            if marker in lower_value:
                errors.append(f"{path} contains forbidden raw, archive, private, or authenticated marker {marker}")


def _targets_by_url(plan: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    raw_targets = plan.get("targets") or plan.get("sources") or []
    if isinstance(raw_targets, Mapping):
        raw_targets = [raw_targets]
    targets: dict[str, Mapping[str, Any]] = {}
    if isinstance(raw_targets, Sequence) and not isinstance(raw_targets, (str, bytes)):
        for item in raw_targets:
            if isinstance(item, str):
                targets[item.strip()] = {"url": item.strip()}
            elif isinstance(item, Mapping):
                url = _text(item.get("url") or item.get("target"))
                if url:
                    targets[url] = item
    return targets


def _require_list(value: Any, field: str, errors: list[str]) -> list[Any]:
    if not isinstance(value, list):
        errors.append(f"{field} must be a list")
        return []
    return value


def _text_list(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [_text(item) for item in value if _text(item)]


def _stable_token(value: str) -> str:
    lowered = value.strip().lower()
    chars = [character if character.isalnum() else "-" for character in lowered]
    return "-".join(part for part in "".join(chars).split("-") if part) or "unknown"


def _text(value: Any, default: str = "") -> str:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else default
    return default


__all__ = [
    "PACKET_TYPE",
    "ProcessorHandoffRehearsalPacketError",
    "ProcessorHandoffRehearsalValidationResult",
    "build_processor_handoff_manifest_rehearsal_packet",
    "require_valid_processor_handoff_manifest_rehearsal_packet",
    "validate_processor_handoff_manifest_rehearsal_packet",
]
