"""Fixture-first source freshness drift escalation packets.

This module consumes already-materialized fixture packets: source freshness
badges, public source refresh intake evidence, and SourceRegistry update
candidates. It emits reviewer escalation metadata only. It never fetches URLs,
invokes processors, downloads documents, or mutates source registries.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Mapping, Sequence
from urllib.parse import urlparse


PACKET_TYPE = "ppd_source_freshness_drift_escalation_packet"
PACKET_VERSION = "1.0"

_ALLOWED_PUBLIC_HOSTS = {
    "www.portland.gov",
    "portland.gov",
    "devhub.portlandoregon.gov",
    "www.portlandoregon.gov",
    "www.portlandmaps.com",
    "portlandmaps.com",
}

_ALLOWED_CITATION_ARTIFACT_TYPES = {
    "source_freshness_badge_packet",
    "public_source_refresh_intake_evidence_packet",
    "source_registry_update_candidate_packet",
}

_FORBIDDEN_TRUE_KEYS = {
    "activearchivemanifestmutation",
    "activeartifactmutation",
    "activeregistrymutation",
    "activesourceregistrymutation",
    "activesourceregistrymutationflag",
    "activesourceregistrymutationflags",
    "archivemanifestmutationallowed",
    "archivemanifestupdated",
    "archiveartifactwritten",
    "documentsdownloaded",
    "downloadeddocuments",
    "fetchurls",
    "livecrawlclaimed",
    "livecrawlexecuted",
    "livecrawlinvoked",
    "livecrawlrun",
    "livefetchused",
    "livefreshnessrefreshperformed",
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
    "/permit/private",
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

_OUTCOME_GUARANTEE_MARKERS = (
    "approval is guaranteed",
    "approved automatically",
    "guarantee approval",
    "guaranteed approval",
    "guaranteed legal outcome",
    "guarantees legal outcome",
    "legally compliant",
    "permit will be approved",
    "permitting outcome guarantee",
    "will be legally sufficient",
)

_STALE_BADGE_STATUSES = {
    "expired",
    "metadata_changed",
    "needs_review",
    "review_due_daily",
    "review_due_weekly",
    "stale",
    "unknown",
}


@dataclass(frozen=True)
class SourceFreshnessDriftEscalationValidationResult:
    """Validation result for drift escalation packets."""

    valid: bool
    errors: tuple[str, ...]


class SourceFreshnessDriftEscalationPacketError(ValueError):
    """Raised when a drift escalation packet is unsafe or incomplete."""


def build_source_freshness_drift_escalation_packet(
    source_freshness_badge_packet: Mapping[str, Any],
    public_source_refresh_intake_evidence_packet: Mapping[str, Any],
    source_registry_update_candidate_packet: Mapping[str, Any],
    *,
    packet_id: str = "fixture-source-freshness-drift-escalation-001",
    generated_at: str = "2026-05-29T00:00:00Z",
) -> dict[str, Any]:
    """Build a cited stale-source escalation packet from fixture packets."""

    _reject_forbidden_artifacts(source_freshness_badge_packet)
    _reject_forbidden_artifacts(public_source_refresh_intake_evidence_packet)
    _reject_forbidden_artifacts(source_registry_update_candidate_packet)
    _require_no_live_refresh_inputs(public_source_refresh_intake_evidence_packet, source_registry_update_candidate_packet)

    badge_rows = _index_badges(source_freshness_badge_packet)
    intake_rows = _index_intake_evidence(public_source_refresh_intake_evidence_packet)
    attestation_rows = _index_attestations(public_source_refresh_intake_evidence_packet)
    candidate_rows = _index_registry_candidates(source_registry_update_candidate_packet)

    source_ids = sorted(set(badge_rows) | set(intake_rows) | set(candidate_rows))
    categories = []
    assignments = []
    rerun_triggers = []
    no_live_refresh_attestations = []

    for source_id in source_ids:
        badge = badge_rows.get(source_id, {})
        intake = intake_rows.get(source_id, {})
        candidate = candidate_rows.get(source_id, {})
        owner = _reviewer_owner(badge, intake, candidate)
        citations = _citations(source_id, badge, intake, candidate)
        stale_reasons = _stale_reasons(badge, intake, candidate)

        categories.append(
            {
                "category_id": "stale-source-category-" + _stable_token(source_id),
                "source_id": source_id,
                "canonical_url": _first_text(candidate.get("canonical_url"), intake.get("canonical_url"), badge.get("canonical_url")),
                "stale_source_category": _primary_category(stale_reasons),
                "category_reasons": stale_reasons,
                "citations": citations,
                "reviewer_owner": owner,
                "escalation_status": "requires_reviewer_triage_before_requirement_rerun",
            }
        )
        assignments.append(
            {
                "assignment_id": "stale-source-owner-" + _stable_token(source_id, owner),
                "source_id": source_id,
                "reviewer_owner": owner,
                "assignment_basis": "intake_reviewer_owner_fields_or_source_badge_default",
                "citation_ids": [citation["citation_id"] for citation in citations],
            }
        )
        rerun_triggers.extend(_rerun_triggers(source_id, candidate, citations, owner))
        no_live_refresh_attestations.append(_no_live_refresh_attestation(source_id, intake, attestation_rows.get(source_id), citations))

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
        "input_packet_refs": {
            "source_freshness_badge_packet_type": _text(source_freshness_badge_packet.get("packet_type")),
            "public_source_refresh_intake_evidence_packet_type": _text(public_source_refresh_intake_evidence_packet.get("packet_type")),
            "source_registry_update_candidate_packet_id": _text(source_registry_update_candidate_packet.get("packet_id")),
        },
        "stale_source_categories": categories,
        "reviewer_owner_assignments": assignments,
        "expected_requirement_rerun_triggers": rerun_triggers,
        "no_live_refresh_attestations": no_live_refresh_attestations,
        "escalation_summary": {
            "source_count": len(source_ids),
            "stale_source_category_count": len(categories),
            "reviewer_owner_assignment_count": len(assignments),
            "requirement_rerun_trigger_count": len(rerun_triggers),
            "no_live_refresh_attestation_count": len(no_live_refresh_attestations),
            "live_refresh_used": False,
            "source_registry_mutated": False,
        },
    }
    require_valid_source_freshness_drift_escalation_packet(packet)
    return packet


def validate_source_freshness_drift_escalation_packet(packet: Mapping[str, Any]) -> SourceFreshnessDriftEscalationValidationResult:
    """Validate a drift escalation packet without side effects."""

    errors: list[str] = []
    if packet.get("packet_type") != PACKET_TYPE:
        errors.append("packet_type must be " + PACKET_TYPE)
    if packet.get("packet_version") != PACKET_VERSION:
        errors.append("packet_version must be " + PACKET_VERSION)
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
    ):
        if packet.get(key) is not False:
            errors.append(key + " must be false")

    categories = _sequence(packet.get("stale_source_categories"))
    assignments = _sequence(packet.get("reviewer_owner_assignments"))
    triggers = _sequence(packet.get("expected_requirement_rerun_triggers"))
    attestations = _sequence(packet.get("no_live_refresh_attestations"))
    if not categories:
        errors.append("stale_source_categories must not be empty")
    if not assignments:
        errors.append("reviewer_owner_assignments must not be empty")
    if not triggers:
        errors.append("expected_requirement_rerun_triggers must not be empty")
    if not attestations:
        errors.append("no_live_refresh_attestations must not be empty")

    source_ids = {_text(row.get("source_id")) for row in categories if isinstance(row, Mapping)}
    assignment_sources = {_text(row.get("source_id")) for row in assignments if isinstance(row, Mapping)}
    attestation_sources = {_text(row.get("source_id")) for row in attestations if isinstance(row, Mapping)}
    if source_ids != assignment_sources:
        errors.append("reviewer_owner_assignments must cover every stale source category")
    if source_ids != attestation_sources:
        errors.append("no_live_refresh_attestations must cover every stale source category")

    citation_ids: set[str] = set()
    for index, category in enumerate(categories):
        if not isinstance(category, Mapping):
            errors.append(f"stale_source_categories[{index}] must be an object")
            continue
        prefix = f"stale_source_categories[{index}]"
        source_id = _text(category.get("source_id"))
        if not source_id:
            errors.append(prefix + ".source_id is required")
        url_error = _public_url_error(_text(category.get("canonical_url")))
        if url_error:
            errors.append(prefix + ".canonical_url " + url_error)
        if not _text(category.get("stale_source_category")):
            errors.append(prefix + ".stale_source_category is required")
        if not _text(category.get("reviewer_owner")):
            errors.append(prefix + ".reviewer_owner is required")
        citations = _sequence(category.get("citations"))
        if not citations:
            errors.append(prefix + ".citations must not be empty")
        for citation_index, citation in enumerate(citations):
            citation_prefix = f"{prefix}.citations[{citation_index}]"
            if not isinstance(citation, Mapping):
                errors.append(citation_prefix + " must be an object")
                continue
            citation_id = _text(citation.get("citation_id"))
            artifact_type = _text(citation.get("artifact_type"))
            if citation_id:
                citation_ids.add(citation_id)
            if not citation_id or not artifact_type:
                errors.append(citation_prefix + " require citation_id and artifact_type")
            if artifact_type and artifact_type not in _ALLOWED_CITATION_ARTIFACT_TYPES:
                errors.append(citation_prefix + ".artifact_type is not an allowed fixture artifact")
            if source_id and _text(citation.get("source_id")) != source_id:
                errors.append(citation_prefix + ".source_id must match stale source category")

    for index, assignment in enumerate(assignments):
        if not isinstance(assignment, Mapping):
            errors.append(f"reviewer_owner_assignments[{index}] must be an object")
            continue
        if not _text(assignment.get("reviewer_owner")):
            errors.append(f"reviewer_owner_assignments[{index}].reviewer_owner is required")
        assignment_citations = _text_list(assignment.get("citation_ids"))
        if not assignment_citations:
            errors.append(f"reviewer_owner_assignments[{index}].citation_ids must not be empty")
        elif not set(assignment_citations).issubset(citation_ids):
            errors.append(f"reviewer_owner_assignments[{index}].citation_ids must reference category citations")

    source_specific_trigger_count = 0
    for index, trigger in enumerate(triggers):
        if not isinstance(trigger, Mapping):
            errors.append(f"expected_requirement_rerun_triggers[{index}] must be an object")
            continue
        prefix = f"expected_requirement_rerun_triggers[{index}]"
        source_id = _text(trigger.get("source_id"))
        if not _text(trigger.get("trigger_id")):
            errors.append(prefix + ".trigger_id is required")
        if source_id and source_id != "packet":
            source_specific_trigger_count += 1
            if source_id not in source_ids:
                errors.append(prefix + ".source_id must match a stale source category")
        if not _text(trigger.get("reviewer_owner")):
            errors.append(prefix + ".reviewer_owner is required")
        if "rerun" not in _text(trigger.get("expected_rerun_action")).lower():
            errors.append(prefix + ".expected_rerun_action must identify a rerun trigger")
        trigger_citations = _sequence(trigger.get("citations"))
        if not trigger_citations:
            errors.append(prefix + ".citations must not be empty")
        if not (
            _text_list(trigger.get("affected_requirement_ids"))
            or _text_list(trigger.get("affected_process_model_ids"))
            or _text_list(trigger.get("affected_guardrail_bundle_ids"))
        ):
            errors.append(prefix + " must identify affected downstream ids")
    if triggers and source_specific_trigger_count == 0:
        errors.append("expected_requirement_rerun_triggers must include at least one source-specific rerun trigger")

    for index, attestation in enumerate(attestations):
        if not isinstance(attestation, Mapping):
            errors.append(f"no_live_refresh_attestations[{index}] must be an object")
            continue
        prefix = f"no_live_refresh_attestations[{index}]"
        if not _text(attestation.get("source_id")):
            errors.append(prefix + ".source_id is required")
        url_error = _public_url_error(_text(attestation.get("canonical_url")))
        if url_error:
            errors.append(prefix + ".canonical_url " + url_error)
        for key in ("live_network_invoked", "fetch_urls", "processor_invoked", "documents_downloaded", "raw_body_persisted", "source_registry_mutated"):
            if attestation.get(key) is not False:
                errors.append(prefix + "." + key + " must be false")
        attestation_citations = _text_list(attestation.get("citation_ids"))
        if not attestation_citations:
            errors.append(prefix + ".citation_ids must not be empty")
        elif not set(attestation_citations).issubset(citation_ids):
            errors.append(prefix + ".citation_ids must reference category citations")

    summary = packet.get("escalation_summary") if isinstance(packet.get("escalation_summary"), Mapping) else {}
    if summary.get("live_refresh_used") is not False:
        errors.append("escalation_summary.live_refresh_used must be false")
    if summary.get("source_registry_mutated") is not False:
        errors.append("escalation_summary.source_registry_mutated must be false")

    try:
        _reject_forbidden_artifacts(packet)
    except SourceFreshnessDriftEscalationPacketError as exc:
        errors.append(str(exc))
    return SourceFreshnessDriftEscalationValidationResult(valid=not errors, errors=tuple(errors))


def require_valid_source_freshness_drift_escalation_packet(packet: Mapping[str, Any]) -> None:
    """Raise if the packet is invalid or unsafe."""

    result = validate_source_freshness_drift_escalation_packet(packet)
    if not result.valid:
        raise SourceFreshnessDriftEscalationPacketError("; ".join(result.errors))


def _index_badges(packet: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    rows = packet.get("freshness_badges") or packet.get("badges") or packet.get("source_evidence_freshness_badges")
    indexed: dict[str, dict[str, Any]] = {}
    for row in _sequence(rows):
        if isinstance(row, Mapping):
            source_id = _text(row.get("source_id"))
            if source_id:
                indexed[source_id] = dict(row)
    if not indexed:
        raise SourceFreshnessDriftEscalationPacketError("source freshness badge packet must include freshness_badges")
    return indexed


def _index_intake_evidence(packet: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in _sequence(packet.get("synthetic_reviewer_evidence")):
        if isinstance(row, Mapping):
            source_id = _text(row.get("source_id"))
            if source_id:
                indexed[source_id] = dict(row)
    if not indexed:
        raise SourceFreshnessDriftEscalationPacketError("public source refresh intake evidence packet must include synthetic_reviewer_evidence")
    return indexed


def _index_attestations(packet: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in _sequence(packet.get("no_live_refresh_attestations") or packet.get("no_raw_body_attestations")):
        if isinstance(row, Mapping):
            source_id = _text(row.get("source_id"))
            if source_id:
                indexed[source_id] = dict(row)
    return indexed


def _index_registry_candidates(packet: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in _sequence(packet.get("source_registry_update_candidates")):
        if isinstance(row, Mapping):
            source_id = _text(row.get("source_id"))
            if source_id:
                indexed[source_id] = dict(row)
    if not indexed:
        raise SourceFreshnessDriftEscalationPacketError("source registry update candidate packet must include source_registry_update_candidates")
    return indexed


def _require_no_live_refresh_inputs(intake_packet: Mapping[str, Any], candidate_packet: Mapping[str, Any]) -> None:
    for packet_name, packet in (("public source refresh intake evidence packet", intake_packet), ("source registry update candidate packet", candidate_packet)):
        for key in ("live_network_invoked", "fetch_urls", "processor_invoked", "processor_executed", "documents_downloaded", "raw_bodies_persisted"):
            if packet.get(key) is True:
                raise SourceFreshnessDriftEscalationPacketError(packet_name + " must not claim " + key)
        for key in ("registry_updated", "source_registry_mutated", "live_registry_edited", "active_source_registry_mutation_flags"):
            if packet.get(key) is True:
                raise SourceFreshnessDriftEscalationPacketError(packet_name + " must not claim registry mutation")


def _reviewer_owner(badge: Mapping[str, Any], intake: Mapping[str, Any], candidate: Mapping[str, Any]) -> str:
    fields = intake.get("synthetic_reviewer_evidence_fields") if isinstance(intake.get("synthetic_reviewer_evidence_fields"), Mapping) else {}
    owners = fields.get("reviewer_owner_fields") if isinstance(fields.get("reviewer_owner_fields"), Mapping) else {}
    return _first_text(
        owners.get("primary_reviewer_owner"),
        owners.get("source_reviewer_owner"),
        intake.get("reviewer_owner"),
        badge.get("reviewer_owner"),
        candidate.get("reviewer_owner"),
        "ppd-source-reviewer",
    )


def _citations(source_id: str, badge: Mapping[str, Any], intake: Mapping[str, Any], candidate: Mapping[str, Any]) -> list[dict[str, str]]:
    citations = []
    if badge:
        citations.append(
            {
                "citation_id": "badge-" + _stable_token(source_id),
                "artifact_type": "source_freshness_badge_packet",
                "source_id": source_id,
                "field_path": "freshness_badges[source_id=" + source_id + "]",
                "evidence_id": _first_text(badge.get("badge_id"), badge.get("evidence_id"), source_id),
            }
        )
    if intake:
        citations.append(
            {
                "citation_id": "intake-" + _stable_token(source_id),
                "artifact_type": "public_source_refresh_intake_evidence_packet",
                "source_id": source_id,
                "field_path": "synthetic_reviewer_evidence[source_id=" + source_id + "]",
                "evidence_id": _first_text(intake.get("evidence_id"), source_id),
            }
        )
    if candidate:
        citations.append(
            {
                "citation_id": "registry-candidate-" + _stable_token(source_id),
                "artifact_type": "source_registry_update_candidate_packet",
                "source_id": source_id,
                "field_path": "source_registry_update_candidates[source_id=" + source_id + "]",
                "evidence_id": _first_text(candidate.get("review_evidence_id"), candidate.get("candidate_id"), source_id),
            }
        )
    return citations


def _stale_reasons(badge: Mapping[str, Any], intake: Mapping[str, Any], candidate: Mapping[str, Any]) -> list[str]:
    reasons = []
    freshness_status = _text(badge.get("freshness_status") or badge.get("badge_state"))
    if freshness_status.lower() in _STALE_BADGE_STATUSES or "stale" in freshness_status.lower() or "review_due" in freshness_status.lower():
        reasons.append("freshness_badge_" + freshness_status.lower())
    changed_fields = _sequence(candidate.get("changed_fields"))
    if changed_fields:
        reasons.append("registry_update_candidate_changed_fields")
    proposed_fields = candidate.get("proposed_fields") if isinstance(candidate.get("proposed_fields"), Mapping) else {}
    if _text(proposed_fields.get("freshness_status")).lower() in _STALE_BADGE_STATUSES:
        reasons.append("proposed_registry_freshness_" + _text(proposed_fields.get("freshness_status")).lower())
    fields = intake.get("synthetic_reviewer_evidence_fields") if isinstance(intake.get("synthetic_reviewer_evidence_fields"), Mapping) else {}
    skipped = _text(fields.get("skipped_target_reason_slot"))
    if skipped:
        reasons.append("intake_skipped_target_reason_" + skipped)
    if not reasons:
        reasons.append("reviewer_escalation_requested_by_fixture_inputs")
    return sorted(set(reasons))


def _primary_category(reasons: Sequence[str]) -> str:
    for prefix, category in (
        ("registry_update_candidate_changed_fields", "registry_metadata_changed"),
        ("freshness_badge", "freshness_badge_stale_or_review_due"),
        ("intake_skipped_target_reason", "refresh_intake_skipped_or_incomplete"),
    ):
        if any(reason.startswith(prefix) for reason in reasons):
            return category
    return "reviewer_escalation_required"


def _rerun_triggers(source_id: str, candidate: Mapping[str, Any], citations: Sequence[Mapping[str, str]], owner: str) -> list[dict[str, Any]]:
    links = candidate.get("downstream_invalidation_links") if isinstance(candidate.get("downstream_invalidation_links"), Mapping) else {}
    requirement_ids = _text_list(links.get("requirement_ids"))
    process_model_ids = _text_list(links.get("process_model_ids"))
    guardrail_bundle_ids = _text_list(links.get("guardrail_bundle_ids"))
    if not requirement_ids and not process_model_ids and not guardrail_bundle_ids:
        return []
    return [
        {
            "trigger_id": "requirement-rerun-trigger-" + _stable_token(source_id),
            "source_id": source_id,
            "trigger_type": "source_registry_candidate_downstream_invalidation_links",
            "affected_requirement_ids": requirement_ids,
            "affected_process_model_ids": process_model_ids,
            "affected_guardrail_bundle_ids": guardrail_bundle_ids,
            "expected_rerun_action": "rerun_requirement_and_guardrail_validation_after_reviewer_accepts_source_refresh",
            "reviewer_owner": owner,
            "citations": [dict(citation) for citation in citations],
        }
    ]


def _no_live_refresh_attestation(
    source_id: str,
    intake: Mapping[str, Any],
    upstream_attestation: Mapping[str, Any] | None,
    citations: Sequence[Mapping[str, str]],
) -> dict[str, Any]:
    attestation = upstream_attestation or {}
    return {
        "attestation_id": "no-live-refresh-" + _stable_token(source_id),
        "source_id": source_id,
        "canonical_url": _first_text(intake.get("canonical_url"), attestation.get("canonical_url")),
        "live_network_invoked": False,
        "fetch_urls": False,
        "processor_invoked": False,
        "documents_downloaded": False,
        "raw_body_persisted": False,
        "source_registry_mutated": False,
        "upstream_attestation_id": _text(attestation.get("attestation_id")),
        "citation_ids": [citation["citation_id"] for citation in citations],
    }


def _reject_forbidden_artifacts(value: Any, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized_key = _normalize_key(str(key))
            if normalized_key in _FORBIDDEN_TRUE_KEYS and child is True:
                raise SourceFreshnessDriftEscalationPacketError(str(key) + " must be false")
            _reject_forbidden_artifacts(child, path + "." + str(key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_forbidden_artifacts(child, path + "[" + str(index) + "]")
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in _FORBIDDEN_VALUE_MARKERS):
            raise SourceFreshnessDriftEscalationPacketError("forbidden raw, download, archive, processor, or private artifact reference at " + path)
        if any(marker in lowered for marker in _OUTCOME_GUARANTEE_MARKERS):
            raise SourceFreshnessDriftEscalationPacketError("legal or permitting outcome guarantees are not allowed at " + path)
        url_error = _public_url_error(value)
        if url_error:
            raise SourceFreshnessDriftEscalationPacketError(url_error + " at " + path)


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


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


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
    "SourceFreshnessDriftEscalationPacketError",
    "SourceFreshnessDriftEscalationValidationResult",
    "build_source_freshness_drift_escalation_packet",
    "require_valid_source_freshness_drift_escalation_packet",
    "validate_source_freshness_drift_escalation_packet",
]
