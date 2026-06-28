"""Fixture-first SourceRegistry schedule update candidate packets.

This module turns already-materialized PP&D fixture packets into proposed
crawl-frequency and monitoring-priority adjustments. It is metadata-only: it
never fetches URLs, invokes processors, downloads documents, mutates source
registries, or activates schedules.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Mapping, Sequence
from urllib.parse import urlparse

from ppd.crawler.source_refresh_runbook_validation import validate_source_refresh_runbook_candidate
from ppd.source_freshness.source_freshness_drift_escalation_packet import (
    require_valid_source_freshness_drift_escalation_packet,
)


PACKET_TYPE = "ppd_source_registry_schedule_update_candidate_packet"
PACKET_VERSION = "1.0"

_ALLOWED_PUBLIC_HOSTS = {
    "www.portland.gov",
    "portland.gov",
    "devhub.portlandoregon.gov",
    "www.portlandoregon.gov",
    "portlandoregon.gov",
    "www.portlandmaps.com",
    "portlandmaps.com",
}

_ALLOWED_CITATION_ARTIFACT_TYPES = {
    "source_freshness_badge_packet",
    "public_source_refresh_intake_evidence_packet",
    "source_registry_update_candidate_packet",
    "source_freshness_drift_escalation_packet",
    "source_refresh_runbook_candidate",
}

_ALLOWED_FREQUENCIES = {"daily", "weekly", "monthly", "manual_review_before_recrawl"}
_ALLOWED_PRIORITIES = {"high", "medium", "low", "manual_review"}

_FORBIDDEN_TRUE_KEYS = {
    "activearchivemanifestmutation",
    "activeregistrymutation",
    "activeschedulemutation",
    "activesourceregistrymutation",
    "documentsdownloaded",
    "downloadeddocuments",
    "fetchurls",
    "livecrawlclaimed",
    "livecrawlexecuted",
    "livefetchused",
    "livenetworkinvoked",
    "networkioallowed",
    "processorclaim",
    "processorexecuted",
    "processorinvoked",
    "processorinvocationallowed",
    "rawbodiespersisted",
    "rawbodypersisted",
    "registrymutationactive",
    "registrymutationallowed",
    "registryupdated",
    "schedulemutated",
    "schedulemutationactive",
    "schedulemutationallowed",
    "scheduleupdated",
    "sourceregistrymutated",
}

_FORBIDDEN_VALUE_MARKERS = (
    "auth_state",
    "credential",
    "cookies.json",
    "downloaded_documents",
    "downloaded-documents",
    "localstorage.json",
    "password",
    "processor_output",
    "processor-output",
    "raw-crawl",
    "raw_crawl",
    "session_cookie",
    "storage_state",
    "trace.zip",
    "warc://",
    ".warc",
    "/downloads/",
    "/raw/",
)

_PRIVATE_URL_MARKERS = (
    "/account",
    "/admin",
    "/auth",
    "/case/",
    "/cases/",
    "/dashboard",
    "/login",
    "/my/",
    "/payment",
    "/private",
    "/session",
    "/signin",
    "/sign-in",
    "access_token=",
    "auth=",
    "password=",
    "session=",
    "token=",
)

_RAW_DOWNLOAD_ARCHIVE_URL_MARKERS = (
    "/archive/",
    "/download",
    "/downloads/",
    "/raw/",
    ".har",
    ".warc",
    "warc://",
)


@dataclass(frozen=True)
class SourceRegistryScheduleUpdateCandidateValidationResult:
    """Validation result for SourceRegistry schedule update candidates."""

    valid: bool
    errors: tuple[str, ...]


class SourceRegistryScheduleUpdateCandidatePacketError(ValueError):
    """Raised when a schedule update candidate is unsafe or incomplete."""


def build_source_registry_schedule_update_candidate_packet(
    source_freshness_drift_escalation_packet: Mapping[str, Any],
    public_source_refresh_intake_evidence_packet: Mapping[str, Any],
    source_refresh_runbook_candidate: Mapping[str, Any],
    *,
    packet_id: str = "fixture-source-registry-schedule-update-candidate-001",
    generated_at: str = "2026-05-29T00:00:00Z",
) -> dict[str, Any]:
    """Build a cited, metadata-only schedule update candidate from fixtures."""

    _reject_forbidden_artifacts(source_freshness_drift_escalation_packet)
    _reject_forbidden_artifacts(public_source_refresh_intake_evidence_packet)
    _reject_forbidden_artifacts(source_refresh_runbook_candidate)
    require_valid_source_freshness_drift_escalation_packet(source_freshness_drift_escalation_packet)
    runbook_findings = validate_source_refresh_runbook_candidate(source_refresh_runbook_candidate)
    if runbook_findings:
        codes = ", ".join(finding.code for finding in runbook_findings)
        raise SourceRegistryScheduleUpdateCandidatePacketError("invalid source refresh runbook candidate: " + codes)

    categories = _sequence(source_freshness_drift_escalation_packet.get("stale_source_categories"))
    intake_by_source = _index_intake(public_source_refresh_intake_evidence_packet)
    abort_criteria = _abort_criteria(source_refresh_runbook_candidate)
    abort_ids = [row["abort_criterion_id"] for row in abort_criteria]

    adjustments = []
    reviewer_owner_fields = []
    attestations = []
    affected_source_ids = []

    for category in categories:
        if not isinstance(category, Mapping):
            continue
        source_id = _text(category.get("source_id"))
        if not source_id:
            continue
        affected_source_ids.append(source_id)
        owner = _text(category.get("reviewer_owner"), "ppd-source-reviewer")
        intake = intake_by_source.get(source_id, {})
        citations = _adjustment_citations(source_id, category, intake, source_refresh_runbook_candidate)
        frequency = _proposed_frequency(category)
        priority = _monitoring_priority(category, frequency)
        attestation_id = "no-active-registry-schedule-mutation-" + _stable_token(source_id)

        adjustments.append(
            {
                "adjustment_id": "schedule-adjustment-" + _stable_token(source_id, frequency, priority),
                "source_id": source_id,
                "affected_source_ids": [source_id],
                "canonical_url": _first_text(category.get("canonical_url"), intake.get("canonical_url")),
                "proposed_crawl_frequency": frequency,
                "proposed_monitoring_priority": priority,
                "adjustment_status": "proposed_only_requires_reviewer_approval",
                "rationale": _rationale(category, frequency, priority),
                "reviewer_owner": owner,
                "citation_ids": [citation["citation_id"] for citation in citations],
                "citations": citations,
                "abort_criterion_ids": abort_ids,
                "no_active_registry_schedule_mutation_attestation_id": attestation_id,
            }
        )
        reviewer_owner_fields.append(
            {
                "source_id": source_id,
                "reviewer_owner": owner,
                "owner_field_source": "source_freshness_drift_escalation_packet.stale_source_categories.reviewer_owner",
                "citation_ids": [citation["citation_id"] for citation in citations],
            }
        )
        attestations.append(
            {
                "attestation_id": attestation_id,
                "source_id": source_id,
                "canonical_url": _first_text(category.get("canonical_url"), intake.get("canonical_url")),
                "active_source_registry_mutation": False,
                "source_registry_mutated": False,
                "active_schedule_mutation": False,
                "schedule_mutated": False,
                "live_network_invoked": False,
                "fetch_urls": False,
                "processor_invoked": False,
                "documents_downloaded": False,
                "raw_body_persisted": False,
                "citation_ids": [citation["citation_id"] for citation in citations],
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
        "fetch_urls": False,
        "processor_invoked": False,
        "documents_downloaded": False,
        "raw_bodies_persisted": False,
        "source_registry_mutated": False,
        "schedule_mutated": False,
        "active_source_registry_mutation": False,
        "active_schedule_mutation": False,
        "input_packet_refs": {
            "source_freshness_drift_escalation_packet_id": _text(source_freshness_drift_escalation_packet.get("packet_id")),
            "public_source_refresh_intake_evidence_packet_id": _text(public_source_refresh_intake_evidence_packet.get("packet_id")),
            "source_refresh_runbook_candidate_id": _first_text(
                source_refresh_runbook_candidate.get("runbook_id"),
                source_refresh_runbook_candidate.get("packet_id"),
                "source-refresh-runbook-candidate",
            ),
        },
        "affected_source_ids": sorted(set(affected_source_ids)),
        "proposed_schedule_adjustments": adjustments,
        "reviewer_owner_fields": reviewer_owner_fields,
        "abort_criteria": abort_criteria,
        "no_active_registry_schedule_mutation_attestations": attestations,
        "candidate_summary": {
            "affected_source_count": len(set(affected_source_ids)),
            "proposed_adjustment_count": len(adjustments),
            "reviewer_owner_field_count": len(reviewer_owner_fields),
            "abort_criterion_count": len(abort_criteria),
            "attestation_count": len(attestations),
            "requires_separate_reviewer_approval": True,
            "source_registry_mutated": False,
            "schedule_mutated": False,
        },
    }
    require_valid_source_registry_schedule_update_candidate_packet(packet)
    return packet


def validate_source_registry_schedule_update_candidate_packet(
    packet: Mapping[str, Any],
) -> SourceRegistryScheduleUpdateCandidateValidationResult:
    """Validate a schedule update candidate without side effects."""

    errors: list[str] = []
    if not isinstance(packet, Mapping):
        return SourceRegistryScheduleUpdateCandidateValidationResult(False, ("packet must be an object",))
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
        "fetch_urls",
        "processor_invoked",
        "documents_downloaded",
        "raw_bodies_persisted",
        "source_registry_mutated",
        "schedule_mutated",
        "active_source_registry_mutation",
        "active_schedule_mutation",
    ):
        if packet.get(key) is not False:
            errors.append(key + " must be false")

    affected_source_ids = set(_text_list(packet.get("affected_source_ids")))
    adjustments = _sequence(packet.get("proposed_schedule_adjustments"))
    owners = _sequence(packet.get("reviewer_owner_fields"))
    aborts = _sequence(packet.get("abort_criteria"))
    attestations = _sequence(packet.get("no_active_registry_schedule_mutation_attestations"))

    if not affected_source_ids:
        errors.append("affected_source_ids must not be empty")
    if not adjustments:
        errors.append("proposed_schedule_adjustments must not be empty")
    if not owners:
        errors.append("reviewer_owner_fields must not be empty")
    if not aborts:
        errors.append("abort_criteria must not be empty")
    if not attestations:
        errors.append("no_active_registry_schedule_mutation_attestations must not be empty")

    citation_ids: set[str] = set()
    adjustment_source_ids: set[str] = set()
    abort_ids = {_text(row.get("abort_criterion_id")) for row in aborts if isinstance(row, Mapping)}
    attestation_ids = {_text(row.get("attestation_id")) for row in attestations if isinstance(row, Mapping)}

    for index, adjustment in enumerate(adjustments):
        prefix = "proposed_schedule_adjustments[" + str(index) + "]"
        if not isinstance(adjustment, Mapping):
            errors.append(prefix + " must be an object")
            continue
        source_id = _text(adjustment.get("source_id"))
        if source_id:
            adjustment_source_ids.add(source_id)
        if source_id not in affected_source_ids:
            errors.append(prefix + ".source_id must be listed in affected_source_ids")
        if source_id not in set(_text_list(adjustment.get("affected_source_ids"))):
            errors.append(prefix + ".affected_source_ids must include source_id")
        url_error = _public_url_error(_text(adjustment.get("canonical_url")))
        if url_error:
            errors.append(prefix + ".canonical_url " + url_error)
        if adjustment.get("proposed_crawl_frequency") not in _ALLOWED_FREQUENCIES:
            errors.append(prefix + ".proposed_crawl_frequency is invalid")
        if adjustment.get("proposed_monitoring_priority") not in _ALLOWED_PRIORITIES:
            errors.append(prefix + ".proposed_monitoring_priority is invalid")
        if not _text(adjustment.get("reviewer_owner")):
            errors.append(prefix + ".reviewer_owner is required")
        if not _text(adjustment.get("rationale")):
            errors.append(prefix + ".rationale is required")
        cited_abort_ids = set(_text_list(adjustment.get("abort_criterion_ids")))
        if not cited_abort_ids:
            errors.append(prefix + ".abort_criterion_ids must not be empty")
        elif not cited_abort_ids.issubset(abort_ids):
            errors.append(prefix + ".abort_criterion_ids must reference packet abort criteria")
        attestation_id = _text(adjustment.get("no_active_registry_schedule_mutation_attestation_id"))
        if not attestation_id:
            errors.append(prefix + ".no_active_registry_schedule_mutation_attestation_id is required")
        elif attestation_id not in attestation_ids:
            errors.append(prefix + ".no_active_registry_schedule_mutation_attestation_id must reference packet attestations")
        citations = _sequence(adjustment.get("citations"))
        if not citations:
            errors.append(prefix + ".citations must not be empty")
        for citation_index, citation in enumerate(citations):
            citation_prefix = prefix + ".citations[" + str(citation_index) + "]"
            if not isinstance(citation, Mapping):
                errors.append(citation_prefix + " must be an object")
                continue
            citation_id = _text(citation.get("citation_id"))
            artifact_type = _text(citation.get("artifact_type"))
            if not citation_id or not artifact_type:
                errors.append(citation_prefix + " require citation_id and artifact_type")
            else:
                citation_ids.add(citation_id)
            if artifact_type and artifact_type not in _ALLOWED_CITATION_ARTIFACT_TYPES:
                errors.append(citation_prefix + ".artifact_type is not an allowed fixture artifact")
            cited_source = _text(citation.get("source_id"))
            if cited_source and source_id and cited_source != source_id:
                errors.append(citation_prefix + ".source_id must match adjustment source_id")

    if affected_source_ids and adjustment_source_ids != affected_source_ids:
        errors.append("proposed_schedule_adjustments must cover every affected source")

    owner_source_ids = set()
    for index, owner in enumerate(owners):
        prefix = "reviewer_owner_fields[" + str(index) + "]"
        if not isinstance(owner, Mapping):
            errors.append(prefix + " must be an object")
            continue
        source_id = _text(owner.get("source_id"))
        if source_id:
            owner_source_ids.add(source_id)
        if source_id not in affected_source_ids:
            errors.append(prefix + ".source_id must be listed in affected_source_ids")
        if not _text(owner.get("reviewer_owner")):
            errors.append(prefix + ".reviewer_owner is required")
        owner_citations = set(_text_list(owner.get("citation_ids")))
        if not owner_citations:
            errors.append(prefix + ".citation_ids must not be empty")
        elif citation_ids and not owner_citations.issubset(citation_ids):
            errors.append(prefix + ".citation_ids must reference adjustment citations")
    if affected_source_ids and owner_source_ids != affected_source_ids:
        errors.append("reviewer_owner_fields must cover every affected source")

    for index, abort in enumerate(aborts):
        prefix = "abort_criteria[" + str(index) + "]"
        if not isinstance(abort, Mapping):
            errors.append(prefix + " must be an object")
            continue
        if not _text(abort.get("abort_criterion_id")):
            errors.append(prefix + ".abort_criterion_id is required")
        if not _text(abort.get("description")):
            errors.append(prefix + ".description is required")
        if not _text(abort.get("source")):
            errors.append(prefix + ".source is required")

    attestation_source_ids = set()
    for index, attestation in enumerate(attestations):
        prefix = "no_active_registry_schedule_mutation_attestations[" + str(index) + "]"
        if not isinstance(attestation, Mapping):
            errors.append(prefix + " must be an object")
            continue
        source_id = _text(attestation.get("source_id"))
        if source_id:
            attestation_source_ids.add(source_id)
        if source_id not in affected_source_ids:
            errors.append(prefix + ".source_id must be listed in affected_source_ids")
        url_error = _public_url_error(_text(attestation.get("canonical_url")))
        if url_error:
            errors.append(prefix + ".canonical_url " + url_error)
        for key in (
            "active_source_registry_mutation",
            "source_registry_mutated",
            "active_schedule_mutation",
            "schedule_mutated",
            "live_network_invoked",
            "fetch_urls",
            "processor_invoked",
            "documents_downloaded",
            "raw_body_persisted",
        ):
            if attestation.get(key) is not False:
                errors.append(prefix + "." + key + " must be false")
        attestation_citations = set(_text_list(attestation.get("citation_ids")))
        if not attestation_citations:
            errors.append(prefix + ".citation_ids must not be empty")
        elif citation_ids and not attestation_citations.issubset(citation_ids):
            errors.append(prefix + ".citation_ids must reference adjustment citations")
    if affected_source_ids and attestation_source_ids != affected_source_ids:
        errors.append("no_active_registry_schedule_mutation_attestations must cover every affected source")

    summary = packet.get("candidate_summary") if isinstance(packet.get("candidate_summary"), Mapping) else {}
    if summary.get("requires_separate_reviewer_approval") is not True:
        errors.append("candidate_summary.requires_separate_reviewer_approval must be true")
    if summary.get("source_registry_mutated") is not False:
        errors.append("candidate_summary.source_registry_mutated must be false")
    if summary.get("schedule_mutated") is not False:
        errors.append("candidate_summary.schedule_mutated must be false")

    try:
        _reject_forbidden_artifacts(packet)
    except SourceRegistryScheduleUpdateCandidatePacketError as exc:
        errors.append(str(exc))
    return SourceRegistryScheduleUpdateCandidateValidationResult(not errors, tuple(errors))


def require_valid_source_registry_schedule_update_candidate_packet(packet: Mapping[str, Any]) -> None:
    """Raise if a schedule update candidate packet is invalid or unsafe."""

    result = validate_source_registry_schedule_update_candidate_packet(packet)
    if not result.valid:
        raise SourceRegistryScheduleUpdateCandidatePacketError("; ".join(result.errors))


def _index_intake(packet: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    indexed = {}
    for row in _sequence(packet.get("synthetic_reviewer_evidence")):
        if isinstance(row, Mapping):
            source_id = _text(row.get("source_id"))
            if source_id:
                indexed[source_id] = row
    return indexed


def _adjustment_citations(
    source_id: str,
    category: Mapping[str, Any],
    intake: Mapping[str, Any],
    runbook: Mapping[str, Any],
) -> list[dict[str, str]]:
    citations = []
    for citation in _sequence(category.get("citations")):
        if isinstance(citation, Mapping):
            citation_id = _text(citation.get("citation_id"))
            artifact_type = _text(citation.get("artifact_type"))
            if citation_id and artifact_type:
                citations.append(
                    {
                        "citation_id": citation_id,
                        "artifact_type": artifact_type,
                        "source_id": source_id,
                        "field_path": _text(citation.get("field_path"), "source_freshness_drift_escalation_packet.stale_source_categories"),
                        "evidence_id": _text(citation.get("evidence_id"), source_id),
                    }
                )
    if intake:
        citations.append(
            {
                "citation_id": "schedule-intake-" + _stable_token(source_id),
                "artifact_type": "public_source_refresh_intake_evidence_packet",
                "source_id": source_id,
                "field_path": "synthetic_reviewer_evidence[source_id=" + source_id + "]",
                "evidence_id": _text(intake.get("evidence_id"), source_id),
            }
        )
    citations.append(
        {
            "citation_id": "schedule-runbook-" + _stable_token(source_id),
            "artifact_type": "source_refresh_runbook_candidate",
            "source_id": source_id,
            "field_path": "source_refresh_runbook_candidate",
            "evidence_id": _first_text(runbook.get("runbook_id"), runbook.get("packet_id"), "source-refresh-runbook-candidate"),
        }
    )
    citations.append(
        {
            "citation_id": "schedule-drift-escalation-" + _stable_token(source_id),
            "artifact_type": "source_freshness_drift_escalation_packet",
            "source_id": source_id,
            "field_path": "stale_source_categories[source_id=" + source_id + "]",
            "evidence_id": _text(category.get("category_id"), source_id),
        }
    )
    return citations


def _proposed_frequency(category: Mapping[str, Any]) -> str:
    reasons = " ".join(_text_list(category.get("category_reasons"))).lower()
    primary = _text(category.get("stale_source_category")).lower()
    if "review_due_daily" in reasons or "metadata_changed" in reasons or primary == "registry_metadata_changed":
        return "daily"
    if "review_due_weekly" in reasons or "forms" in _text(category.get("source_id")).lower():
        return "weekly"
    if "skipped" in reasons or "incomplete" in primary:
        return "manual_review_before_recrawl"
    return "weekly"


def _monitoring_priority(category: Mapping[str, Any], frequency: str) -> str:
    primary = _text(category.get("stale_source_category")).lower()
    if frequency == "daily" or primary == "registry_metadata_changed":
        return "high"
    if frequency == "manual_review_before_recrawl":
        return "manual_review"
    if frequency == "weekly":
        return "medium"
    return "low"


def _rationale(category: Mapping[str, Any], frequency: str, priority: str) -> str:
    reason_text = ", ".join(_text_list(category.get("category_reasons")))
    if not reason_text:
        reason_text = _text(category.get("stale_source_category"), "stale source escalation")
    return "Propose " + frequency + " crawl-frequency and " + priority + " monitoring priority from cited drift escalation reasons: " + reason_text


def _abort_criteria(runbook: Mapping[str, Any]) -> list[dict[str, str]]:
    rows = []
    seen = set()
    raw_conditions = runbook.get("abort_conditions") or []
    if isinstance(raw_conditions, Mapping):
        raw_conditions = list(raw_conditions.values())
    for index, item in enumerate(_sequence(raw_conditions)):
        if isinstance(item, Mapping):
            description = _first_text(item.get("description"), item.get("reason"), item.get("abort"))
            base_id = _first_text(item.get("abort_criterion_id"), item.get("condition_id"), item.get("id"), "runbook-abort-" + str(index + 1))
        else:
            description = _text(item)
            base_id = description or "runbook-abort-" + str(index + 1)
        if not description:
            continue
        criterion_id = "abort-" + _stable_token(base_id)
        if criterion_id not in seen:
            rows.append({"abort_criterion_id": criterion_id, "description": description, "source": "source_refresh_runbook_candidate.abort_conditions"})
            seen.add(criterion_id)
    fixed = [
        "abort if a proposed schedule update requires active registry mutation",
        "abort if a proposed schedule update requires active schedule mutation",
        "abort if reviewer approval is missing or ambiguous",
    ]
    for description in fixed:
        criterion_id = "abort-" + _stable_token(description)
        if criterion_id not in seen:
            rows.append({"abort_criterion_id": criterion_id, "description": description, "source": "schedule_update_candidate_guardrail"})
            seen.add(criterion_id)
    return rows


def _reject_forbidden_artifacts(value: Any, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized_key = _normalize_key(str(key))
            if normalized_key in _FORBIDDEN_TRUE_KEYS and child is True:
                raise SourceRegistryScheduleUpdateCandidatePacketError(str(key) + " must be false")
            _reject_forbidden_artifacts(child, path + "." + str(key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_forbidden_artifacts(child, path + "[" + str(index) + "]")
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in _FORBIDDEN_VALUE_MARKERS):
            raise SourceRegistryScheduleUpdateCandidatePacketError("forbidden raw, download, archive, processor, or private artifact reference at " + path)
        url_error = _public_url_error(value)
        if url_error:
            raise SourceRegistryScheduleUpdateCandidatePacketError(url_error + " at " + path)


def _public_url_error(value: str) -> str:
    text = _text(value)
    if not text or "://" not in text:
        return ""
    parsed = urlparse(text)
    scheme = parsed.scheme.lower()
    host = (parsed.hostname or "").lower()
    path_and_query = (parsed.path + ("?" + parsed.query if parsed.query else "")).lower()
    if scheme != "https":
        return "non-allowlisted or private/authenticated URL"
    if host not in _ALLOWED_PUBLIC_HOSTS:
        return "non-allowlisted or private/authenticated URL"
    if any(marker in path_and_query for marker in _PRIVATE_URL_MARKERS):
        return "forbidden private or authenticated URL"
    if any(marker in path_and_query for marker in _RAW_DOWNLOAD_ARCHIVE_URL_MARKERS):
        return "forbidden raw, download, archive, processor, or private artifact reference"
    return ""


def _sequence(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return []


def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text or default


def _first_text(*values: Any) -> str:
    for value in values:
        text = _text(value)
        if text:
            return text
    return ""


def _text_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return sorted({_text(item) for item in value if _text(item)})


def _stable_token(*parts: str) -> str:
    return sha256("|".join(parts).encode("utf-8")).hexdigest()[:12]


def _normalize_key(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


__all__ = [
    "PACKET_TYPE",
    "PACKET_VERSION",
    "SourceRegistryScheduleUpdateCandidatePacketError",
    "SourceRegistryScheduleUpdateCandidateValidationResult",
    "build_source_registry_schedule_update_candidate_packet",
    "require_valid_source_registry_schedule_update_candidate_packet",
    "validate_source_registry_schedule_update_candidate_packet",
]
