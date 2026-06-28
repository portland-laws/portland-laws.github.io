"""Fixture-first public source change impact triage.

This module intentionally performs offline packet normalization only. It does not
fetch URLs, run crawls, mutate active guardrail bundles, or mutate monitoring
schedules. Validation is fail-closed so public source change packets cannot
promote uncited or unknown impact claims into review queues.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import parse_qsl, urlparse

_ALLOWED_PUBLIC_HOSTS = {
    "www.portland.gov",
    "portland.gov",
    "devhub.portlandoregon.gov",
    "www.portlandoregon.gov",
    "www.portlandmaps.com",
    "portlandmaps.com",
}

_PRIVATE_PATH_MARKERS = (
    "/login",
    "/signin",
    "/sign-in",
    "/register",
    "/account",
    "/accounts",
    "/profile",
    "/my-permits",
    "/mypermits",
    "/my-requests",
    "/dashboard",
    "/admin",
    "/payment",
    "/checkout",
    "/upload",
    "/corrections",
)

_PRIVATE_QUERY_MARKERS = {
    "access_token",
    "auth",
    "authorization",
    "code",
    "cookie",
    "jwt",
    "key",
    "password",
    "session",
    "sessionid",
    "sid",
    "signature",
    "state",
    "token",
}

_RAW_REFERENCE_KEYS = {
    "archive_ref",
    "archive_url",
    "body",
    "body_html",
    "body_text",
    "content",
    "dom",
    "download_ref",
    "download_url",
    "html",
    "inner_html",
    "outer_html",
    "page_body",
    "raw",
    "raw_body",
    "raw_content",
    "raw_html",
    "response_body",
    "text",
    "warc_ref",
}

_PRIVATE_ARTIFACT_KEYS = {
    "auth_state",
    "archive_path",
    "download_path",
    "downloaded_path",
    "file_path",
    "filesystem_path",
    "har_path",
    "local_file",
    "local_path",
    "pdf_path",
    "screenshot_path",
    "session_state",
    "trace_path",
    "warc_path",
}

_LIVE_ACTION_KEYS = {
    "crawl_attempted",
    "crawl_claimed",
    "fetch_attempted",
    "fetched_live",
    "live_crawl_performed",
    "live_fetch_performed",
    "network_action_performed",
    "network_actions_performed",
}

_ACTIVE_MUTATION_KEYS = {
    "active_bundle_mutation",
    "active_guardrail_bundle_mutation",
    "active_guardrail_bundles_mutated",
    "apply_schedule_update",
    "auto_promote_guardrails",
    "bundle_mutation_requested",
    "guardrail_bundle_mutated",
    "guardrail_mutation_requested",
    "monitoring_schedule_mutated",
    "schedule_mutation_requested",
}

_REVIEW_REQUIRED_FRESHNESS = {"stale", "unknown", "needs_review"}
_PREREQUISITE_LINK_KEYS = {
    "source_registry",
    "requirement_index",
    "process_model_index",
    "guardrail_bundle_index",
    "reviewer_roster",
}


@dataclass(frozen=True)
class PublicSourceChangeImpact:
    """Offline impact record for a cited public source."""

    source_id: str
    cited_source_ids: tuple[str, ...]
    affected_requirement_ids: tuple[str, ...]
    affected_process_ids: tuple[str, ...]
    affected_guardrail_bundle_ids: tuple[str, ...]
    reviewer_owners: tuple[str, ...]
    stale_source_acknowledgements: tuple[str, ...]
    offline_triage_decision: str
    decision_reasons: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "cited_source_ids": list(self.cited_source_ids),
            "affected_requirement_ids": list(self.affected_requirement_ids),
            "affected_process_ids": list(self.affected_process_ids),
            "affected_guardrail_bundle_ids": list(self.affected_guardrail_bundle_ids),
            "reviewer_owners": list(self.reviewer_owners),
            "stale_source_acknowledgements": list(self.stale_source_acknowledgements),
            "offline_triage_decision": self.offline_triage_decision,
            "decision_reasons": list(self.decision_reasons),
        }


@dataclass(frozen=True)
class PublicSourceChangeImpactTriageViolation:
    """A deterministic validation failure for a triage packet."""

    code: str
    message: str
    location: str


class PublicSourceChangeImpactTriageValidationError(ValueError):
    """Raised when a public source change impact triage packet is unsafe."""

    def __init__(self, violations: Sequence[PublicSourceChangeImpactTriageViolation]) -> None:
        self.violations = tuple(violations)
        details = "; ".join(
            f"{violation.location}: {violation.code}: {violation.message}"
            for violation in self.violations
        )
        super().__init__(details)


def load_triage_packet(path: Path) -> dict[str, Any]:
    """Load a fixture packet from disk without resolving or fetching URLs."""

    with path.open("r", encoding="utf-8") as handle:
        packet = json.load(handle)
    if not isinstance(packet, dict):
        raise ValueError("public source change triage packet must be a JSON object")
    return packet


def validate_public_source_change_impact_triage_packet(packet: Mapping[str, Any]) -> None:
    """Reject unsafe or incomplete public source change impact triage packets."""

    violations = list(public_source_change_impact_triage_violations(packet))
    if violations:
        raise PublicSourceChangeImpactTriageValidationError(violations)


def public_source_change_impact_triage_violations(
    packet: Mapping[str, Any],
) -> tuple[PublicSourceChangeImpactTriageViolation, ...]:
    """Return triage packet validation failures without raising."""

    if not isinstance(packet, Mapping):
        return (
            PublicSourceChangeImpactTriageViolation(
                code="invalid_packet",
                message="triage packet must be a JSON object",
                location="$",
            ),
        )

    violations: list[PublicSourceChangeImpactTriageViolation] = []
    _scan_for_forbidden_claims(packet, "$", violations)

    prerequisite_links = _validate_prerequisite_links(packet, violations)
    traceability_entries = _entries_or_violation(
        packet,
        "public_source_to_guardrail_traceability_audit",
        "traceability",
        violations,
    )
    freshness_entries = _entries_or_violation(
        packet,
        "public_source_freshness_review",
        "sources",
        violations,
    )
    schedule_entries = _entries_or_violation(
        packet,
        "public_source_monitoring_schedule_candidate",
        "candidates",
        violations,
    )

    source_registry = _string_set_from_mapping(prerequisite_links, "source_registry")
    requirement_index = _string_set_from_mapping(prerequisite_links, "requirement_index")
    process_index = _string_set_from_mapping(prerequisite_links, "process_model_index")
    guardrail_index = _string_set_from_mapping(prerequisite_links, "guardrail_bundle_index")
    reviewer_roster = _string_set_from_mapping(prerequisite_links, "reviewer_roster")

    source_ids = _source_ids_from_entries(
        traceability_entries + freshness_entries + schedule_entries,
        violations,
    )
    _validate_known_ids(source_ids, source_registry, "unknown_source_id", "source_id", violations)

    for index, entry in enumerate(traceability_entries):
        location = f"$.public_source_to_guardrail_traceability_audit.traceability[{index}]"
        _validate_traceability_entry(
            entry,
            location,
            source_registry,
            requirement_index,
            process_index,
            guardrail_index,
            reviewer_roster,
            violations,
        )

    for index, entry in enumerate(freshness_entries):
        location = f"$.public_source_freshness_review.sources[{index}]"
        _validate_freshness_entry(entry, location, reviewer_roster, violations)

    for index, entry in enumerate(schedule_entries):
        location = f"$.public_source_monitoring_schedule_candidate.candidates[{index}]"
        _validate_schedule_entry(entry, location, reviewer_roster, violations)

    return tuple(violations)


def triage_public_source_changes(packet: Mapping[str, Any]) -> dict[str, Any]:
    """Build deterministic offline source change impact triage output."""

    validate_public_source_change_impact_triage_packet(packet)

    traceability_entries = _entries(
        packet,
        "public_source_to_guardrail_traceability_audit",
        "traceability",
    )
    freshness_entries = _entries(
        packet,
        "public_source_freshness_review",
        "sources",
    )
    schedule_entries = _entries(
        packet,
        "public_source_monitoring_schedule_candidate",
        "candidates",
    )

    traceability_by_source = _index_by_source(traceability_entries)
    freshness_by_source = _index_by_source(freshness_entries)
    schedule_by_source = _index_by_source(schedule_entries)

    source_ids = sorted(
        set(traceability_by_source) | set(freshness_by_source) | set(schedule_by_source)
    )
    impacts = [
        _build_impact(
            source_id,
            traceability_by_source.get(source_id, {}),
            freshness_by_source.get(source_id, {}),
            schedule_by_source.get(source_id, {}),
        )
        for source_id in source_ids
    ]

    return {
        "packet_type": "public_source_change_impact_triage",
        "mode": "fixture_first_offline",
        "network_actions_performed": False,
        "active_guardrail_bundles_mutated": False,
        "monitoring_schedule_mutated": False,
        "impact_records": [impact.as_dict() for impact in impacts],
    }


def _build_impact(
    source_id: str,
    traceability: Mapping[str, Any],
    freshness: Mapping[str, Any],
    schedule: Mapping[str, Any],
) -> PublicSourceChangeImpact:
    cited_source_ids = _sorted_unique([source_id, *_string_list(traceability, "source_evidence_ids")])
    affected_requirement_ids = _sorted_unique(_string_list(traceability, "requirement_ids"))
    affected_process_ids = _sorted_unique(_string_list(traceability, "process_ids"))
    affected_guardrail_bundle_ids = _sorted_unique(
        _string_list(traceability, "guardrail_bundle_ids")
    )

    reviewer_owners = _sorted_unique(
        [
            _string_value(traceability, "reviewer_owner"),
            _string_value(freshness, "acknowledgement_owner"),
            _string_value(schedule, "proposed_reviewer_owner"),
        ]
    )

    stale_acknowledgements: list[str] = []
    freshness_status = _string_value(freshness, "freshness_status")
    acknowledgement_required = bool(freshness.get("acknowledgement_required", False))
    if freshness_status in _REVIEW_REQUIRED_FRESHNESS or acknowledgement_required:
        owner = _string_value(freshness, "acknowledgement_owner") or "unassigned"
        reason = _string_value(freshness, "stale_reason") or freshness_status or "freshness review required"
        stale_acknowledgements.append(f"{source_id}:{owner}:{reason}")

    decision, reasons = _offline_decision(
        affected_requirement_ids=affected_requirement_ids,
        affected_guardrail_bundle_ids=affected_guardrail_bundle_ids,
        freshness_status=freshness_status,
        change_signal=_string_value(schedule, "change_signal"),
        reviewer_owners=reviewer_owners,
        stale_acknowledgements=stale_acknowledgements,
    )

    return PublicSourceChangeImpact(
        source_id=source_id,
        cited_source_ids=tuple(cited_source_ids),
        affected_requirement_ids=tuple(affected_requirement_ids),
        affected_process_ids=tuple(affected_process_ids),
        affected_guardrail_bundle_ids=tuple(affected_guardrail_bundle_ids),
        reviewer_owners=tuple(reviewer_owners),
        stale_source_acknowledgements=tuple(stale_acknowledgements),
        offline_triage_decision=decision,
        decision_reasons=tuple(reasons),
    )


def _offline_decision(
    *,
    affected_requirement_ids: list[str],
    affected_guardrail_bundle_ids: list[str],
    freshness_status: str,
    change_signal: str,
    reviewer_owners: list[str],
    stale_acknowledgements: list[str],
) -> tuple[str, list[str]]:
    reasons: list[str] = []

    if change_signal in {"content_hash_changed", "manual_change_notice", "structure_changed"}:
        reasons.append(f"change_signal:{change_signal}")
    if affected_requirement_ids:
        reasons.append("requirements_affected")
    if affected_guardrail_bundle_ids:
        reasons.append("guardrail_bundles_affected_without_mutation")
    if freshness_status in _REVIEW_REQUIRED_FRESHNESS:
        reasons.append(f"freshness_status:{freshness_status}")
    if stale_acknowledgements:
        reasons.append("stale_source_acknowledgement_required")
    if not reviewer_owners:
        reasons.append("reviewer_owner_missing")

    if affected_guardrail_bundle_ids and (change_signal or stale_acknowledgements):
        return "offline_review_required_before_guardrail_update", reasons
    if affected_requirement_ids and (change_signal or stale_acknowledgements):
        return "offline_requirement_review_required", reasons
    if stale_acknowledgements:
        return "stale_source_acknowledgement_required", reasons
    if change_signal in {"no_change", "schedule_only"} and not reasons:
        return "no_impact_detected", ["fixture_indicates_no_change"]
    if not reasons:
        return "monitor_without_bundle_mutation", ["no_requirement_or_guardrail_impact_in_fixture"]
    return "offline_triage_required", reasons


def _validate_prerequisite_links(
    packet: Mapping[str, Any],
    violations: list[PublicSourceChangeImpactTriageViolation],
) -> Mapping[str, Any]:
    prerequisite_links = packet.get("prerequisite_links")
    if not isinstance(prerequisite_links, Mapping):
        violations.append(
            PublicSourceChangeImpactTriageViolation(
                code="missing_prerequisite_links",
                message="triage packet must include prerequisite_links for known IDs and reviewer owners",
                location="$.prerequisite_links",
            )
        )
        return {}

    for key in sorted(_PREREQUISITE_LINK_KEYS):
        if not _as_string_list(prerequisite_links.get(key)):
            violations.append(
                PublicSourceChangeImpactTriageViolation(
                    code="missing_prerequisite_link",
                    message=f"prerequisite_links.{key} must list known prerequisite IDs",
                    location=f"$.prerequisite_links.{key}",
                )
            )
    return prerequisite_links


def _validate_traceability_entry(
    entry: Mapping[str, Any],
    location: str,
    source_registry: set[str],
    requirement_index: set[str],
    process_index: set[str],
    guardrail_index: set[str],
    reviewer_roster: set[str],
    violations: list[PublicSourceChangeImpactTriageViolation],
) -> None:
    source_id = _string_value(entry, "source_id")
    source_evidence_ids = set(_string_list(entry, "source_evidence_ids"))
    cited_source_ids = {source_id, *source_evidence_ids}

    _validate_known_ids(source_evidence_ids, source_registry, "unknown_source_id", "source_evidence_ids", violations, location)
    _validate_known_ids(set(_string_list(entry, "requirement_ids")), requirement_index, "unknown_requirement_id", "requirement_ids", violations, location)
    _validate_known_ids(set(_string_list(entry, "process_ids")), process_index, "unknown_process_id", "process_ids", violations, location)
    _validate_known_ids(set(_string_list(entry, "guardrail_bundle_ids")), guardrail_index, "unknown_guardrail_bundle_id", "guardrail_bundle_ids", violations, location)

    reviewer_owner = _string_value(entry, "reviewer_owner")
    if not reviewer_owner:
        violations.append(
            PublicSourceChangeImpactTriageViolation(
                code="missing_reviewer_owner",
                message="traceability entries must name a reviewer owner",
                location=f"{location}.reviewer_owner",
            )
        )
    elif reviewer_owner not in reviewer_roster:
        violations.append(
            PublicSourceChangeImpactTriageViolation(
                code="unknown_reviewer_owner",
                message=f"reviewer owner {reviewer_owner!r} is not in prerequisite_links.reviewer_roster",
                location=f"{location}.reviewer_owner",
            )
        )

    affected_ids = set(_string_list(entry, "requirement_ids"))
    affected_ids.update(_string_list(entry, "process_ids"))
    affected_ids.update(_string_list(entry, "guardrail_bundle_ids"))
    citation_map = entry.get("affected_id_citations")
    if affected_ids and not isinstance(citation_map, Mapping):
        violations.append(
            PublicSourceChangeImpactTriageViolation(
                code="affected_ids_without_citations",
                message="affected requirement, process, and guardrail IDs must cite public source evidence",
                location=f"{location}.affected_id_citations",
            )
        )
        return

    if isinstance(citation_map, Mapping):
        for affected_id in sorted(affected_ids):
            cited_ids = set(_as_string_list(citation_map.get(affected_id)))
            if not cited_ids:
                violations.append(
                    PublicSourceChangeImpactTriageViolation(
                        code="affected_id_without_citation",
                        message=f"affected ID {affected_id!r} has no source citation",
                        location=f"{location}.affected_id_citations.{affected_id}",
                    )
                )
                continue
            unknown_citations = cited_ids - cited_source_ids
            if unknown_citations:
                violations.append(
                    PublicSourceChangeImpactTriageViolation(
                        code="unknown_citation_source_id",
                        message=f"affected ID {affected_id!r} cites unknown source evidence IDs: {', '.join(sorted(unknown_citations))}",
                        location=f"{location}.affected_id_citations.{affected_id}",
                    )
                )


def _validate_freshness_entry(
    entry: Mapping[str, Any],
    location: str,
    reviewer_roster: set[str],
    violations: list[PublicSourceChangeImpactTriageViolation],
) -> None:
    freshness_status = _string_value(entry, "freshness_status")
    acknowledgement_required = bool(entry.get("acknowledgement_required", False))
    acknowledgement_owner = _string_value(entry, "acknowledgement_owner")
    acknowledgement_note = _string_value(entry, "stale_acknowledgement") or _string_value(entry, "stale_reason")

    if freshness_status in _REVIEW_REQUIRED_FRESHNESS:
        if not acknowledgement_required or not acknowledgement_owner or not acknowledgement_note:
            violations.append(
                PublicSourceChangeImpactTriageViolation(
                    code="stale_current_claim_without_acknowledgement",
                    message="stale, unknown, and needs_review freshness claims require acknowledgement_required, acknowledgement_owner, and acknowledgement text",
                    location=location,
                )
            )
    if acknowledgement_required and not acknowledgement_owner:
        violations.append(
            PublicSourceChangeImpactTriageViolation(
                code="missing_reviewer_owner",
                message="freshness acknowledgement must name a reviewer owner",
                location=f"{location}.acknowledgement_owner",
            )
        )
    if acknowledgement_owner and acknowledgement_owner not in reviewer_roster:
        violations.append(
            PublicSourceChangeImpactTriageViolation(
                code="unknown_reviewer_owner",
                message=f"acknowledgement owner {acknowledgement_owner!r} is not in prerequisite_links.reviewer_roster",
                location=f"{location}.acknowledgement_owner",
            )
        )


def _validate_schedule_entry(
    entry: Mapping[str, Any],
    location: str,
    reviewer_roster: set[str],
    violations: list[PublicSourceChangeImpactTriageViolation],
) -> None:
    owner = _string_value(entry, "proposed_reviewer_owner")
    if not owner:
        violations.append(
            PublicSourceChangeImpactTriageViolation(
                code="missing_reviewer_owner",
                message="schedule candidates must name a proposed reviewer owner",
                location=f"{location}.proposed_reviewer_owner",
            )
        )
    elif owner not in reviewer_roster:
        violations.append(
            PublicSourceChangeImpactTriageViolation(
                code="unknown_reviewer_owner",
                message=f"proposed reviewer owner {owner!r} is not in prerequisite_links.reviewer_roster",
                location=f"{location}.proposed_reviewer_owner",
            )
        )


def _validate_known_ids(
    ids: set[str],
    known_ids: set[str],
    code: str,
    field_name: str,
    violations: list[PublicSourceChangeImpactTriageViolation],
    location: str = "$",
) -> None:
    for unknown_id in sorted(ids - known_ids):
        violations.append(
            PublicSourceChangeImpactTriageViolation(
                code=code,
                message=f"{field_name} references unknown ID {unknown_id!r}",
                location=f"{location}.{field_name}",
            )
        )


def _entries(packet: Mapping[str, Any], section: str, entry_key: str) -> list[Mapping[str, Any]]:
    raw_section = packet.get(section)
    if not isinstance(raw_section, Mapping):
        raise ValueError(f"missing object section: {section}")
    raw_entries = raw_section.get(entry_key)
    if not isinstance(raw_entries, list):
        raise ValueError(f"missing list {section}.{entry_key}")
    entries: list[Mapping[str, Any]] = []
    for raw_entry in raw_entries:
        if not isinstance(raw_entry, Mapping):
            raise ValueError(f"entries in {section}.{entry_key} must be objects")
        entries.append(raw_entry)
    return entries


def _entries_or_violation(
    packet: Mapping[str, Any],
    section: str,
    entry_key: str,
    violations: list[PublicSourceChangeImpactTriageViolation],
) -> list[Mapping[str, Any]]:
    try:
        return _entries(packet, section, entry_key)
    except ValueError as exc:
        violations.append(
            PublicSourceChangeImpactTriageViolation(
                code="missing_required_section",
                message=str(exc),
                location=f"$.{section}.{entry_key}",
            )
        )
        return []


def _index_by_source(entries: list[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    indexed: dict[str, Mapping[str, Any]] = {}
    for entry in entries:
        source_id = _string_value(entry, "source_id")
        if not source_id:
            raise ValueError("triage entries require source_id")
        indexed[source_id] = entry
    return indexed


def _source_ids_from_entries(
    entries: Iterable[Mapping[str, Any]],
    violations: list[PublicSourceChangeImpactTriageViolation],
) -> set[str]:
    source_ids: set[str] = set()
    for entry in entries:
        source_id = _string_value(entry, "source_id")
        if not source_id:
            violations.append(
                PublicSourceChangeImpactTriageViolation(
                    code="missing_source_id",
                    message="triage entries require source_id",
                    location="$",
                )
            )
        else:
            source_ids.add(source_id)
    return source_ids


def _scan_for_forbidden_claims(
    value: Any,
    location: str,
    violations: list[PublicSourceChangeImpactTriageViolation],
) -> None:
    if isinstance(value, Mapping):
        for raw_key, child in value.items():
            key = str(raw_key)
            key_lower = key.lower()
            child_location = f"{location}.{key}"

            if key_lower in _RAW_REFERENCE_KEYS and child not in (None, "", []):
                violations.append(
                    PublicSourceChangeImpactTriageViolation(
                        code="raw_body_download_or_archive_reference",
                        message="triage packets must not include raw body, download, or archive references",
                        location=child_location,
                    )
                )
            if key_lower in _PRIVATE_ARTIFACT_KEYS and child not in (None, "", []):
                violations.append(
                    PublicSourceChangeImpactTriageViolation(
                        code="private_or_downloaded_artifact_reference",
                        message="triage packets must not include private artifacts or downloaded paths",
                        location=child_location,
                    )
                )
            if key_lower in _LIVE_ACTION_KEYS and bool(child):
                violations.append(
                    PublicSourceChangeImpactTriageViolation(
                        code="live_fetch_or_crawl_claim",
                        message="triage packets must be fixture-first and must not claim live fetches or crawls",
                        location=child_location,
                    )
                )
            if key_lower in _ACTIVE_MUTATION_KEYS and bool(child):
                violations.append(
                    PublicSourceChangeImpactTriageViolation(
                        code="active_bundle_or_schedule_mutation_flag",
                        message="triage packets must not set active bundle or monitoring schedule mutation flags",
                        location=child_location,
                    )
                )
            if isinstance(child, str):
                if key_lower.endswith("url") and _is_private_or_authenticated_url(child):
                    violations.append(
                        PublicSourceChangeImpactTriageViolation(
                            code="private_or_authenticated_url",
                            message="URLs in triage packets must be public and unauthenticated",
                            location=child_location,
                        )
                    )
                if _looks_like_private_path(child):
                    violations.append(
                        PublicSourceChangeImpactTriageViolation(
                            code="private_or_downloaded_artifact_reference",
                            message="triage packets must not include downloaded files or private artifact paths",
                            location=child_location,
                        )
                    )
            _scan_for_forbidden_claims(child, child_location, violations)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _scan_for_forbidden_claims(child, f"{location}[{index}]", violations)


def _is_private_or_authenticated_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return True
    if parsed.username or parsed.password:
        return True
    host = (parsed.hostname or "").lower()
    if host not in _ALLOWED_PUBLIC_HOSTS:
        return True
    path = parsed.path.lower().rstrip("/")
    if any(marker in path for marker in _PRIVATE_PATH_MARKERS):
        return True
    query_keys = {key.lower() for key, _value in parse_qsl(parsed.query, keep_blank_values=True)}
    return bool(query_keys & _PRIVATE_QUERY_MARKERS)


def _looks_like_private_path(value: str) -> bool:
    lowered = value.lower()
    return lowered.startswith(("file://", "~/", "/home/", "/users/", "/tmp/", "/var/tmp/")) or ".daemon" in lowered or "/downloads/" in lowered or "\\downloads\\" in lowered


def _string_list(entry: Mapping[str, Any], key: str) -> list[str]:
    raw_value = entry.get(key, [])
    if raw_value is None:
        return []
    if not isinstance(raw_value, list):
        raise ValueError(f"{key} must be a list")
    return [item for item in raw_value if isinstance(item, str) and item]


def _as_string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, Iterable) and not isinstance(value, (bytes, Mapping)):
        return [item for item in value if isinstance(item, str) and item]
    return []


def _string_value(entry: Mapping[str, Any], key: str) -> str:
    raw_value = entry.get(key, "")
    return raw_value if isinstance(raw_value, str) else ""


def _string_set_from_mapping(entry: Mapping[str, Any], key: str) -> set[str]:
    return set(_as_string_list(entry.get(key)))


def _sorted_unique(values: list[str]) -> list[str]:
    return sorted({value for value in values if value})


__all__ = [
    "PublicSourceChangeImpactTriageValidationError",
    "PublicSourceChangeImpactTriageViolation",
    "load_triage_packet",
    "public_source_change_impact_triage_violations",
    "triage_public_source_changes",
    "validate_public_source_change_impact_triage_packet",
]
