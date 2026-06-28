from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping, Sequence
from urllib.parse import urlsplit

from ppd.crawler.processor_handoff_rehearsal_packet import PACKET_TYPE as HANDOFF_PACKET_TYPE
from ppd.crawler.public_recrawl_metadata_intake_reconciliation_packet import PACKET_TYPE as RECONCILIATION_PACKET_TYPE

PACKET_TYPE = "ppd_archive_manifest_promotion_readiness_packet"
SCHEMA_VERSION = 1
MODE = "fixture_first_archive_manifest_promotion_readiness"

_ALLOWED_HOSTS = {
    "www.portland.gov",
    "devhub.portlandoregon.gov",
    "www.portlandoregon.gov",
    "www.portlandmaps.com",
}
_PRIVATE_TARGET_MARKERS = (
    "/account",
    "/admin",
    "/api/private",
    "/dashboard",
    "/login",
    "/my-permits",
    "/private",
    "/signin",
    "/sign-in",
    "/user/",
    "auth=",
    "session=",
    "token=",
)
_FORBIDDEN_TRUE_KEYS = {
    "activeRegistryMutated",
    "activeRegistryWriteAllowed",
    "activeRegistryWritesAllowed",
    "archiveArtifactWritten",
    "archiveArtifactWritesAllowed",
    "archivePromotionAllowed",
    "archivePromotionPerformed",
    "documentsDownloaded",
    "downloadedDocuments",
    "fetchedLive",
    "liveFetchUsed",
    "liveNetworkUsed",
    "manifestPromoted",
    "manifestPromotionAllowed",
    "manifestPromotionPerformed",
    "processorInvoked",
    "rawBodiesPersisted",
    "rawBodyPersisted",
    "registryMutationAllowed",
}
_FORBIDDEN_VALUE_MARKERS = (
    "auth_state",
    "bearer ",
    "cookies.json",
    "credential",
    "download_ref",
    "download_url",
    "downloaded_document",
    "downloaded_documents",
    "file://",
    "localstorage.json",
    "password",
    "raw body",
    "raw_body",
    "raw_html",
    "response_body",
    "s3://",
    "session_cookie",
    "storage_state",
    "trace.zip",
    "warc://",
)


@dataclass(frozen=True)
class ArchiveManifestPromotionReadinessValidationResult:
    valid: bool
    errors: tuple[str, ...]


class ArchiveManifestPromotionReadinessPacketError(ValueError):
    pass


def build_archive_manifest_promotion_readiness_packet(
    processor_handoff_manifest_rehearsal_packet: Mapping[str, Any],
    public_recrawl_metadata_intake_reconciliation_packet: Mapping[str, Any],
    *,
    generated_at: str,
) -> dict[str, Any]:
    handoff_packet = deepcopy(dict(processor_handoff_manifest_rehearsal_packet))
    reconciliation_packet = deepcopy(dict(public_recrawl_metadata_intake_reconciliation_packet))
    _require_consumable_input_packets(handoff_packet, reconciliation_packet)

    manifests_by_id = {
        _text(row.get("manifest_id")): row
        for row in _sequence(handoff_packet.get("expectedMetadataOnlyArchiveManifests"))
        if isinstance(row, Mapping) and _text(row.get("manifest_id"))
    }
    handoff_attestations_by_source = {
        _text(row.get("source_id")): row
        for row in _sequence(handoff_packet.get("noRawBodyAttestations"))
        if isinstance(row, Mapping) and _text(row.get("source_id"))
    }
    reconciliation_attestations_by_source = {
        _text(row.get("source_id")): row
        for row in _sequence(reconciliation_packet.get("syntheticMetadataOnlyIntakeRows"))
        if isinstance(row, Mapping) and _text(row.get("source_id"))
    }

    checks: list[dict[str, Any]] = []
    document_refs: list[dict[str, Any]] = []
    consistency_notes: list[dict[str, Any]] = []
    attestations: list[dict[str, Any]] = []

    for intake in _sequence(reconciliation_packet.get("syntheticMetadataOnlyIntakeRows")):
        if not isinstance(intake, Mapping):
            continue
        source_id = _text(intake.get("source_id"))
        canonical_url = _text(intake.get("canonical_url"))
        manifest_id = _text(intake.get("expected_manifest_id"))
        manifest = manifests_by_id.get(manifest_id, {})
        normalized_document_id = _text(
            intake.get("normalized_document_id"),
            _text(manifest.get("normalized_document_id")),
        )
        expected_content_hash = _text(manifest.get("content_hash"), "expected_metadata_only_pending_capture")
        freshness_badge_id = _text(intake.get("freshness_badge_id"), "freshness-review-required")
        check_id = "manifest-readiness-" + _stable_token(source_id or manifest_id or canonical_url)

        checks.append(
            {
                "check_id": check_id,
                "source_id": source_id,
                "canonical_url": canonical_url,
                "expected_manifest_id": manifest_id,
                "normalized_document_id": normalized_document_id,
                "readiness_status": "blocked_fixture_only_pending_reviewer_checkpoint",
                "metadataOnly": True,
                "fixtureSynthetic": True,
                "manifestPromotionAllowed": False,
                "manifestPromotionPerformed": False,
                "archiveArtifactWritten": False,
                "processorInvoked": False,
                "noPayloadPersisted": True,
            }
        )
        document_refs.append(
            {
                "document_ref_id": "normalized-document-ref-" + _stable_token(normalized_document_id),
                "source_id": source_id,
                "canonical_url": canonical_url,
                "expected_manifest_id": manifest_id,
                "normalized_document_id": normalized_document_id,
                "document_reference_status": "expected_metadata_only_reference",
                "archive_artifact_ref_present": False,
                "metadataOnly": True,
            }
        )
        consistency_notes.append(
            {
                "note_id": "checksum-freshness-" + _stable_token(source_id or manifest_id or canonical_url),
                "source_id": source_id,
                "expected_manifest_id": manifest_id,
                "expected_content_hash": expected_content_hash,
                "freshness_badge_id": freshness_badge_id,
                "freshness_status": "requires_reviewer_confirmation_before_promotion",
                "consistency_status": "metadata_only_pending_capture_consistency_check",
                "reviewRequired": True,
                "manifestPromotionAllowed": False,
            }
        )
        handoff_attestation = handoff_attestations_by_source.get(source_id, {})
        reconciliation_attestation = reconciliation_attestations_by_source.get(source_id, {})
        attestations.append(
            {
                "attestation_id": "archive-promotion-no-payload-" + _stable_token(source_id or manifest_id),
                "source_id": source_id,
                "expected_manifest_id": manifest_id,
                "handoff_attestation_present": bool(handoff_attestation),
                "reconciliation_intake_attestation_present": bool(reconciliation_attestation),
                "noPayloadPersisted": True,
                "archiveArtifactWritten": False,
                "manifestPromotionPerformed": False,
                "processorInvoked": False,
            }
        )

    reviewer_checkpoints = _reviewer_checkpoints(reconciliation_packet, checks)
    abort_notes = _abort_notes(handoff_packet, reconciliation_packet)
    packet = {
        "schemaVersion": SCHEMA_VERSION,
        "packetType": PACKET_TYPE,
        "mode": MODE,
        "generatedAt": generated_at,
        "fixtureFirst": True,
        "metadataOnly": True,
        "liveNetworkUsed": False,
        "fetchedLive": False,
        "processorInvoked": False,
        "archiveArtifactWritten": False,
        "rawBodiesPersisted": False,
        "documentsDownloaded": False,
        "activeRegistryMutated": False,
        "manifestPromotionAllowed": False,
        "manifestPromotionPerformed": False,
        "inputPacketRefs": {
            "processorHandoffPacketType": _text(handoff_packet.get("packetType")),
            "processorHandoffMode": _text(handoff_packet.get("mode")),
            "publicRecrawlMetadataIntakeReconciliationPacketType": _text(reconciliation_packet.get("packetType")),
            "publicRecrawlMetadataIntakeReconciliationMode": _text(reconciliation_packet.get("mode")),
        },
        "syntheticMetadataOnlyManifestReadinessChecks": checks,
        "expectedNormalizedDocumentReferences": document_refs,
        "checksumFreshnessConsistencyNotes": consistency_notes,
        "noRawBodyAttestations": attestations,
        "reviewerCheckpoints": reviewer_checkpoints,
        "abortNotes": abort_notes,
        "readinessSummary": {
            "manifestReadinessCheckCount": len(checks),
            "expectedNormalizedDocumentReferenceCount": len(document_refs),
            "checksumFreshnessConsistencyNoteCount": len(consistency_notes),
            "noRawBodyAttestationCount": len(attestations),
            "reviewerCheckpointCount": len(reviewer_checkpoints),
            "abortNoteCount": len(abort_notes),
            "readyForManifestPromotion": False,
            "manifestPromotionPerformed": False,
            "archiveArtifactWritten": False,
            "processorInvoked": False,
        },
    }
    require_valid_archive_manifest_promotion_readiness_packet(packet)
    return packet


def validate_archive_manifest_promotion_readiness_packet(
    packet: Mapping[str, Any],
) -> ArchiveManifestPromotionReadinessValidationResult:
    errors: list[str] = []
    _collect_forbidden_content(packet, "$", errors)
    _collect_url_like_values(packet, "$", errors)

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
        "liveNetworkUsed",
        "fetchedLive",
        "processorInvoked",
        "archiveArtifactWritten",
        "rawBodiesPersisted",
        "documentsDownloaded",
        "activeRegistryMutated",
        "manifestPromotionAllowed",
        "manifestPromotionPerformed",
    ):
        if packet.get(key) is not False:
            errors.append(f"{key} must be false")

    checks = _require_list(packet.get("syntheticMetadataOnlyManifestReadinessChecks"), "syntheticMetadataOnlyManifestReadinessChecks", errors)
    refs = _require_list(packet.get("expectedNormalizedDocumentReferences"), "expectedNormalizedDocumentReferences", errors)
    notes = _require_list(packet.get("checksumFreshnessConsistencyNotes"), "checksumFreshnessConsistencyNotes", errors)
    attestations = _require_list(packet.get("noRawBodyAttestations"), "noRawBodyAttestations", errors)
    checkpoints = _require_list(packet.get("reviewerCheckpoints"), "reviewerCheckpoints", errors)
    aborts = _require_list(packet.get("abortNotes"), "abortNotes", errors)

    check_manifest_ids = _validate_checks(checks, errors)
    ref_manifest_ids = _validate_document_refs(refs, errors)
    note_manifest_ids = _validate_consistency_notes(notes, errors)
    attestation_manifest_ids = _validate_attestations(attestations, errors)
    _validate_reviewer_checkpoints(checkpoints, errors)
    _validate_abort_notes(aborts, errors)

    if not checks:
        errors.append("syntheticMetadataOnlyManifestReadinessChecks must include at least one check")
    if check_manifest_ids != ref_manifest_ids:
        errors.append("expectedNormalizedDocumentReferences must match manifest readiness checks")
    if check_manifest_ids != note_manifest_ids:
        errors.append("checksumFreshnessConsistencyNotes must match manifest readiness checks")
    if check_manifest_ids != attestation_manifest_ids:
        errors.append("noRawBodyAttestations must match manifest readiness checks")
    if not checkpoints:
        errors.append("reviewerCheckpoints must include at least one checkpoint")
    if not aborts:
        errors.append("abortNotes must include promotion abort notes")
    _validate_abort_note_coverage(aborts, errors)

    summary = packet.get("readinessSummary")
    if not isinstance(summary, Mapping):
        errors.append("readinessSummary must be an object")
    else:
        expected_counts = {
            "manifestReadinessCheckCount": len(checks),
            "expectedNormalizedDocumentReferenceCount": len(refs),
            "checksumFreshnessConsistencyNoteCount": len(notes),
            "noRawBodyAttestationCount": len(attestations),
            "reviewerCheckpointCount": len(checkpoints),
            "abortNoteCount": len(aborts),
        }
        for key, expected in expected_counts.items():
            if summary.get(key) != expected:
                errors.append(f"readinessSummary.{key} must be {expected}")
        for key in ("readyForManifestPromotion", "manifestPromotionPerformed", "archiveArtifactWritten", "processorInvoked"):
            if summary.get(key) is not False:
                errors.append(f"readinessSummary.{key} must be false")

    return ArchiveManifestPromotionReadinessValidationResult(valid=not errors, errors=tuple(errors))


def require_valid_archive_manifest_promotion_readiness_packet(packet: Mapping[str, Any]) -> None:
    result = validate_archive_manifest_promotion_readiness_packet(packet)
    if not result.valid:
        raise ArchiveManifestPromotionReadinessPacketError("; ".join(result.errors))


def _require_consumable_input_packets(handoff_packet: Mapping[str, Any], reconciliation_packet: Mapping[str, Any]) -> None:
    errors: list[str] = []
    if handoff_packet.get("packetType") != HANDOFF_PACKET_TYPE:
        errors.append("processor handoff input packetType must be " + HANDOFF_PACKET_TYPE)
    if reconciliation_packet.get("packetType") != RECONCILIATION_PACKET_TYPE:
        errors.append("reconciliation input packetType must be " + RECONCILIATION_PACKET_TYPE)
    for packet_name, packet in (("processor handoff", handoff_packet), ("reconciliation", reconciliation_packet)):
        if packet.get("fixtureFirst") is not True:
            errors.append(packet_name + " packet must be fixtureFirst")
        if packet.get("metadataOnly") is not True:
            errors.append(packet_name + " packet must be metadataOnly")
        for key in ("processorInvoked", "archiveArtifactWritten"):
            if packet.get(key) is not False:
                errors.append(packet_name + "." + key + " must be false")
    if not _sequence(handoff_packet.get("expectedMetadataOnlyArchiveManifests")):
        errors.append("processor handoff packet must include expectedMetadataOnlyArchiveManifests")
    if not _sequence(reconciliation_packet.get("syntheticMetadataOnlyIntakeRows")):
        errors.append("reconciliation packet must include syntheticMetadataOnlyIntakeRows")
    if errors:
        raise ArchiveManifestPromotionReadinessPacketError("; ".join(errors))


def _reviewer_checkpoints(reconciliation_packet: Mapping[str, Any], checks: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for queue in _sequence(reconciliation_packet.get("changedSourceReviewQueues")):
        if not isinstance(queue, Mapping):
            continue
        source_id = _text(queue.get("source_id"))
        rows.append(
            {
                "checkpoint_id": "reviewer-checkpoint-" + _stable_token(source_id or _text(queue.get("queue_id"))),
                "source_id": source_id,
                "canonical_url": _text(queue.get("canonical_url")),
                "reviewer_owner": _text(queue.get("reviewer_owner")),
                "checkpoint_reason": _text(queue.get("queue_reason"), "changed_source_review_required"),
                "required_before_manifest_promotion": True,
                "humanReviewRequired": True,
                "manifestPromotionAllowed": False,
            }
        )
    checked_sources = {_text(row.get("source_id")) for row in rows}
    for check in checks:
        source_id = _text(check.get("source_id"))
        if source_id and source_id not in checked_sources:
            rows.append(
                {
                    "checkpoint_id": "reviewer-checkpoint-manifest-" + _stable_token(source_id),
                    "source_id": source_id,
                    "canonical_url": _text(check.get("canonical_url")),
                    "reviewer_owner": "archive-manifest-reviewer",
                    "checkpoint_reason": "confirm_expected_manifest_reference_before_promotion",
                    "required_before_manifest_promotion": True,
                    "humanReviewRequired": True,
                    "manifestPromotionAllowed": False,
                }
            )
    return rows


def _abort_notes(handoff_packet: Mapping[str, Any], reconciliation_packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, abort in enumerate(_sequence(handoff_packet.get("abortConditions")), start=1):
        if isinstance(abort, Mapping):
            rows.append(
                {
                    "abort_id": _text(abort.get("abort_id"), f"processor-handoff-abort-{index:02d}"),
                    "source": "processor_handoff_manifest_rehearsal_packet",
                    "note": _text(abort.get("condition"), "Processor handoff rehearsal abort condition."),
                    "abortBeforeManifestPromotion": True,
                    "processorInvocationAllowed": False,
                    "archiveArtifactWriteAllowed": False,
                    "manifestPromotionAllowed": False,
                }
            )
    for index, abort in enumerate(_sequence(reconciliation_packet.get("abortNotes")), start=1):
        if isinstance(abort, Mapping):
            rows.append(
                {
                    "abort_id": _text(abort.get("abort_id"), f"reconciliation-abort-{index:02d}"),
                    "source": "public_recrawl_metadata_intake_reconciliation_packet",
                    "note": _text(abort.get("note"), "Public recrawl metadata intake reconciliation abort condition."),
                    "abortBeforeManifestPromotion": True,
                    "processorInvocationAllowed": False,
                    "archiveArtifactWriteAllowed": False,
                    "manifestPromotionAllowed": False,
                }
            )
    rows.append(
        {
            "abort_id": "manifest-promotion-requested-from-fixture-readiness",
            "source": "archive_manifest_promotion_readiness_policy",
            "note": "Abort if this fixture readiness packet is used to promote a manifest, write an archive artifact, invoke a processor, mutate a registry, or use live fetch.",
            "abortBeforeManifestPromotion": True,
            "processorInvocationAllowed": False,
            "archiveArtifactWriteAllowed": False,
            "manifestPromotionAllowed": False,
        }
    )
    return rows


def _validate_checks(rows: Sequence[Any], errors: list[str]) -> set[str]:
    manifest_ids: set[str] = set()
    seen: set[str] = set()
    for index, row in enumerate(rows):
        prefix = f"syntheticMetadataOnlyManifestReadinessChecks[{index}]"
        if not isinstance(row, Mapping):
            errors.append(prefix + " must be an object")
            continue
        for key in ("check_id", "source_id", "canonical_url", "expected_manifest_id", "normalized_document_id", "readiness_status"):
            if not _text(row.get(key)):
                errors.append(f"{prefix}.{key} is required")
        check_id = _text(row.get("check_id"))
        if check_id in seen:
            errors.append(f"{prefix}.check_id must be unique")
        seen.add(check_id)
        manifest_id = _text(row.get("expected_manifest_id"))
        if manifest_id:
            manifest_ids.add(manifest_id)
        _validate_public_url(_text(row.get("canonical_url")), prefix + ".canonical_url", errors)
        for key in ("metadataOnly", "fixtureSynthetic", "noPayloadPersisted"):
            if row.get(key) is not True:
                errors.append(f"{prefix}.{key} must be true")
        for key in ("manifestPromotionAllowed", "manifestPromotionPerformed", "archiveArtifactWritten", "processorInvoked"):
            if row.get(key) is not False:
                errors.append(f"{prefix}.{key} must be false")
    return manifest_ids


def _validate_document_refs(rows: Sequence[Any], errors: list[str]) -> set[str]:
    manifest_ids: set[str] = set()
    for index, row in enumerate(rows):
        prefix = f"expectedNormalizedDocumentReferences[{index}]"
        if not isinstance(row, Mapping):
            errors.append(prefix + " must be an object")
            continue
        for key in ("document_ref_id", "source_id", "canonical_url", "expected_manifest_id", "normalized_document_id", "document_reference_status"):
            if not _text(row.get(key)):
                errors.append(f"{prefix}.{key} is required")
        manifest_id = _text(row.get("expected_manifest_id"))
        if manifest_id:
            manifest_ids.add(manifest_id)
        _validate_public_url(_text(row.get("canonical_url")), prefix + ".canonical_url", errors)
        if row.get("archive_artifact_ref_present") is not False:
            errors.append(f"{prefix}.archive_artifact_ref_present must be false")
        if row.get("metadataOnly") is not True:
            errors.append(f"{prefix}.metadataOnly must be true")
    return manifest_ids


def _validate_consistency_notes(rows: Sequence[Any], errors: list[str]) -> set[str]:
    manifest_ids: set[str] = set()
    for index, row in enumerate(rows):
        prefix = f"checksumFreshnessConsistencyNotes[{index}]"
        if not isinstance(row, Mapping):
            errors.append(prefix + " must be an object")
            continue
        for key in ("note_id", "source_id", "expected_manifest_id", "expected_content_hash", "freshness_status", "consistency_status"):
            if not _text(row.get(key)):
                errors.append(f"{prefix}.{key} is required")
        manifest_id = _text(row.get("expected_manifest_id"))
        if manifest_id:
            manifest_ids.add(manifest_id)
        if row.get("reviewRequired") is not True:
            errors.append(f"{prefix}.reviewRequired must be true")
        if row.get("manifestPromotionAllowed") is not False:
            errors.append(f"{prefix}.manifestPromotionAllowed must be false")
    return manifest_ids


def _validate_attestations(rows: Sequence[Any], errors: list[str]) -> set[str]:
    manifest_ids: set[str] = set()
    for index, row in enumerate(rows):
        prefix = f"noRawBodyAttestations[{index}]"
        if not isinstance(row, Mapping):
            errors.append(prefix + " must be an object")
            continue
        for key in ("attestation_id", "source_id", "expected_manifest_id"):
            if not _text(row.get(key)):
                errors.append(f"{prefix}.{key} is required")
        manifest_id = _text(row.get("expected_manifest_id"))
        if manifest_id:
            manifest_ids.add(manifest_id)
        if row.get("noPayloadPersisted") is not True:
            errors.append(f"{prefix}.noPayloadPersisted must be true")
        for key in ("archiveArtifactWritten", "manifestPromotionPerformed", "processorInvoked"):
            if row.get(key) is not False:
                errors.append(f"{prefix}.{key} must be false")
    return manifest_ids


def _validate_reviewer_checkpoints(rows: Sequence[Any], errors: list[str]) -> None:
    for index, row in enumerate(rows):
        prefix = f"reviewerCheckpoints[{index}]"
        if not isinstance(row, Mapping):
            errors.append(prefix + " must be an object")
            continue
        for key in ("checkpoint_id", "source_id", "canonical_url", "reviewer_owner", "checkpoint_reason"):
            if not _text(row.get(key)):
                errors.append(f"{prefix}.{key} is required")
        _validate_public_url(_text(row.get("canonical_url")), prefix + ".canonical_url", errors)
        if row.get("required_before_manifest_promotion") is not True:
            errors.append(f"{prefix}.required_before_manifest_promotion must be true")
        if row.get("humanReviewRequired") is not True:
            errors.append(f"{prefix}.humanReviewRequired must be true")
        if row.get("manifestPromotionAllowed") is not False:
            errors.append(f"{prefix}.manifestPromotionAllowed must be false")


def _validate_abort_notes(rows: Sequence[Any], errors: list[str]) -> None:
    for index, row in enumerate(rows):
        prefix = f"abortNotes[{index}]"
        if not isinstance(row, Mapping):
            errors.append(prefix + " must be an object")
            continue
        for key in ("abort_id", "note"):
            if not _text(row.get(key)):
                errors.append(f"{prefix}.{key} is required")
        if row.get("abortBeforeManifestPromotion") is not True:
            errors.append(f"{prefix}.abortBeforeManifestPromotion must be true")
        for key in ("processorInvocationAllowed", "archiveArtifactWriteAllowed", "manifestPromotionAllowed"):
            if row.get(key) is not False:
                errors.append(f"{prefix}.{key} must be false")


def _validate_abort_note_coverage(rows: Sequence[Any], errors: list[str]) -> None:
    combined = " ".join(
        " ".join(_text(row.get(key)) for key in ("abort_id", "note", "source"))
        for row in rows
        if isinstance(row, Mapping)
    ).lower()
    required = {
        "manifest": "abortNotes must include a manifest promotion abort note",
        "archive": "abortNotes must include an archive write abort note",
        "processor": "abortNotes must include a processor invocation abort note",
        "live fetch": "abortNotes must include a live fetch abort note",
    }
    for marker, message in required.items():
        if marker not in combined:
            errors.append(message)


def _require_list(value: Any, field: str, errors: list[str]) -> list[Any]:
    if not isinstance(value, list):
        errors.append(f"{field} must be a list")
        return []
    return value


def _collect_forbidden_content(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if key_text in _FORBIDDEN_TRUE_KEYS and child not in (None, "", [], {}, False):
                errors.append(f"{path}.{key_text} must be false or empty")
            _collect_forbidden_content(child, f"{path}.{key_text}", errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _collect_forbidden_content(child, f"{path}[{index}]", errors)
    elif isinstance(value, str):
        lower_value = value.lower()
        for marker in _FORBIDDEN_VALUE_MARKERS:
            if marker in lower_value:
                errors.append(f"{path} contains forbidden private, raw, or artifact marker {marker}")


def _collect_url_like_values(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            _collect_url_like_values(child, f"{path}.{key}", errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _collect_url_like_values(child, f"{path}[{index}]", errors)
    elif isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith(("http://", "https://")):
            _validate_public_url(stripped, path, errors)


def _validate_public_url(url: str, path: str, errors: list[str]) -> None:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.netloc.lower() not in _ALLOWED_HOSTS:
        errors.append(path + " must be an HTTPS allowlisted public URL")
    combined = (parsed.path + "?" + parsed.query).lower()
    if any(marker in combined for marker in _PRIVATE_TARGET_MARKERS):
        errors.append(path + " must not be private or authenticated")


def _sequence(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []


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
    "ArchiveManifestPromotionReadinessPacketError",
    "ArchiveManifestPromotionReadinessValidationResult",
    "build_archive_manifest_promotion_readiness_packet",
    "require_valid_archive_manifest_promotion_readiness_packet",
    "validate_archive_manifest_promotion_readiness_packet",
]
