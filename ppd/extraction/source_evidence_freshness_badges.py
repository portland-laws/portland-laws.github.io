"""Build and validate cited source evidence freshness badge candidates.

This module is intentionally side-effect free. It consumes already-produced public
source change impact triage packets and public-source-to-guardrail traceability
audit packets, then emits a derived badge packet. It does not mutate source
registries, requirements, process models, guardrail bundles, or active artifacts.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

BADGE_STATES = {"current", "stale", "needs-review", "deferred"}

_DEFERRED_MARKERS = {"deferred", "blocked", "manual_handoff", "manual-handoff"}
_NEEDS_REVIEW_MARKERS = {
    "needs_review",
    "needs-review",
    "review_required",
    "human_review_required",
    "conflicting",
    "gap",
    "missing",
    "unmapped",
}
_STALE_MARKERS = {
    "changed",
    "stale",
    "removed",
    "hash_changed",
    "content_changed",
    "impact_detected",
}
_CURRENT_MARKERS = {"current", "unchanged", "verified", "traceable", "ok", "passed"}

_PUBLIC_HOSTS = {
    "www.portland.gov",
    "portland.gov",
    "devhub.portlandoregon.gov",
    "www.portlandoregon.gov",
    "portlandoregon.gov",
    "www.portlandmaps.com",
    "portlandmaps.com",
}
_PRIVATE_URL_MARKERS = (
    "/account",
    "/accounts",
    "/admin",
    "/applications",
    "/case/",
    "/cases/",
    "/dashboard",
    "/login",
    "/my/",
    "/permit/",
    "/permits/",
    "/private",
    "/profile",
    "/session",
    "/signin",
    "/sign-in",
    "/user",
)
_PRIVATE_OR_AUTH_VALUES = {
    "authenticated",
    "devhub_authenticated",
    "private",
    "restricted",
    "account_scoped",
    "account-scoped",
    "session",
}
_RAW_ARTIFACT_KEYS = {
    "archive_artifact_ref",
    "archive_path",
    "archive_ref",
    "crawl_output_path",
    "download_artifact_ref",
    "download_path",
    "download_ref",
    "har_path",
    "raw_archive_path",
    "raw_body",
    "raw_body_path",
    "raw_crawl_path",
    "raw_download_path",
    "raw_html",
    "raw_page_path",
    "raw_text",
    "screenshot_path",
    "storage_state",
    "trace_path",
    "warc_path",
}
_RAW_ARTIFACT_VALUE_MARKERS = (
    "archive://",
    "crawl://",
    "download://",
    ".har",
    ".trace",
    ".warc",
    "raw-crawl",
    "raw_crawl",
    "storage_state",
    "trace.zip",
)
_LIVE_FETCH_KEYS = {
    "fetch_claim",
    "fetched_at",
    "live_capture",
    "live_fetch",
    "live_fetch_claim",
    "live_fetch_performed",
    "live_fetched_at",
}
_LIVE_FETCH_MARKERS = (
    "browser fetched",
    "curl fetched",
    "fetched live",
    "live crawl",
    "live fetch",
    "live request",
    "performed live fetch",
    "requested live",
)
_ACTIVE_MUTATION_KEYS = {
    "active_artifact_mutation",
    "active_mutation",
    "mutates_active_artifact",
    "mutates_active_artifacts",
    "mutates_active_badges",
    "mutates_active_bundle",
    "mutates_active_bundles",
    "mutates_active_guardrails",
    "mutates_active_requirements",
    "mutates_guardrail_bundles",
    "mutates_process_models",
    "mutates_requirements",
    "mutates_source_registries",
    "replaces_active_artifact",
    "replaces_active_bundle",
    "writes_active_artifact",
}
_ACK_KEYS = (
    "stale_current_acknowledgement",
    "stale_source_acknowledgement",
    "current_despite_stale_acknowledgement",
    "human_acknowledgement",
)


@dataclass(frozen=True)
class SourceEvidenceFreshnessBadgeFinding:
    """A deterministic validation finding for a freshness badge packet."""

    code: str
    path: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "path": self.path, "message": self.message}


class SourceEvidenceFreshnessBadgePacketError(ValueError):
    """Raised when a source evidence freshness badge packet is unsafe."""


def build_source_evidence_freshness_badge_packet(
    triage_packet: dict[str, Any],
    traceability_audit_packet: dict[str, Any],
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Return a cited badge packet derived from public evidence packets.

    The output is deterministic for a fixed ``generated_at`` value. Input packets
    are deep-copied while indexing so callers can assert that no in-place mutation
    occurred.
    """

    generated_timestamp = generated_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    triage_snapshot = deepcopy(triage_packet)
    traceability_snapshot = deepcopy(traceability_audit_packet)

    triage_entries = _index_by_source_id(_extract_triage_entries(triage_snapshot))
    traceability_entries = _extract_traceability_entries(traceability_snapshot)

    candidates: list[dict[str, Any]] = []
    for trace_entry in traceability_entries:
        source_id = _text(trace_entry.get("source_id"))
        if not source_id:
            continue

        triage_entry = triage_entries.get(source_id, {})
        state = _classify_badge_state(triage_entry, trace_entry)
        guardrail_bundle_id = _first_text(
            trace_entry.get("guardrail_bundle_id"),
            trace_entry.get("bundle_id"),
            trace_entry.get("guardrail_id"),
        )
        candidate_id_parts = [source_id, guardrail_bundle_id or "unmapped", state]

        candidates.append(
            {
                "badge_candidate_id": "badge:" + ":".join(_slug(part) for part in candidate_id_parts),
                "badge_state": state,
                "source_id": source_id,
                "guardrail_bundle_id": guardrail_bundle_id,
                "requirement_ids": _sorted_texts(
                    trace_entry.get("requirement_ids")
                    or trace_entry.get("requirements")
                    or triage_entry.get("affected_requirement_ids")
                ),
                "affected_guardrail_bundle_ids": _sorted_texts(
                    triage_entry.get("affected_guardrail_bundle_ids")
                    or triage_entry.get("affected_guardrails")
                    or ([guardrail_bundle_id] if guardrail_bundle_id else [])
                ),
                "rationale": _rationale_for_state(state, triage_entry, trace_entry),
                "citations": _build_citations(source_id, triage_entry, trace_entry),
                "consumed_packet_refs": _packet_refs(triage_snapshot, traceability_snapshot),
            }
        )

    candidates.sort(
        key=lambda item: (
            item["source_id"],
            item.get("guardrail_bundle_id") or "",
            item["badge_state"],
        )
    )

    return {
        "packet_type": "source_evidence_freshness_badge_candidates",
        "packet_version": "1.0",
        "generated_at": generated_timestamp,
        "inputs": _packet_refs(triage_snapshot, traceability_snapshot),
        "badge_states": sorted(BADGE_STATES),
        "badge_candidates": candidates,
        "mutation_policy": {
            "mutates_requirements": False,
            "mutates_process_models": False,
            "mutates_guardrail_bundles": False,
            "mutates_source_registries": False,
        },
    }


def validate_source_evidence_freshness_badge_packet(
    packet: Mapping[str, Any],
    *,
    known_source_ids: Iterable[str] | None = None,
    known_requirement_ids: Iterable[str] | None = None,
    known_guardrail_bundle_ids: Iterable[str] | None = None,
) -> list[SourceEvidenceFreshnessBadgeFinding]:
    """Return validation findings for an unsafe badge packet.

    Validation is deterministic and side-effect free. Registry ID checks are
    enabled when the caller supplies known source, requirement, or guardrail IDs.
    """

    if not isinstance(packet, Mapping):
        return [
            SourceEvidenceFreshnessBadgeFinding(
                "packet_not_object",
                "$",
                "source evidence freshness badge packet must be an object",
            )
        ]

    findings: list[SourceEvidenceFreshnessBadgeFinding] = []
    source_ids = set(known_source_ids or [])
    requirement_ids = set(known_requirement_ids or [])
    guardrail_ids = set(known_guardrail_bundle_ids or [])

    for path, key, value in _walk_mapping(packet):
        normalized_key = _normalize_token(key)
        if normalized_key in _RAW_ARTIFACT_KEYS and _truthy_or_present(value):
            findings.append(
                SourceEvidenceFreshnessBadgeFinding(
                    "raw_artifact_reference",
                    path,
                    "badge packet must not commit raw crawl, download, archive, browser, or storage artifacts",
                )
            )
        if normalized_key in _LIVE_FETCH_KEYS and _truthy_or_present(value):
            findings.append(
                SourceEvidenceFreshnessBadgeFinding(
                    "live_fetch_claim",
                    path,
                    "badge packet must be derived from deterministic packet evidence, not live fetch claims",
                )
            )
        if normalized_key in _ACTIVE_MUTATION_KEYS and value is True:
            findings.append(
                SourceEvidenceFreshnessBadgeFinding(
                    "active_artifact_mutation",
                    path,
                    "badge packet must not set active artifact mutation flags",
                )
            )
        if normalized_key in {"source_type", "auth_scope", "privacy_classification", "visibility"}:
            value_text = _text(value)
            if value_text and _normalize_token(value_text) in _PRIVATE_OR_AUTH_VALUES:
                findings.append(
                    SourceEvidenceFreshnessBadgeFinding(
                        "private_or_authenticated_url",
                        path,
                        "badge packet evidence must not be private or authenticated",
                    )
                )
        if _looks_like_url_key(normalized_key):
            url_text = _text(value)
            if url_text and _url_is_private_or_authenticated(url_text):
                findings.append(
                    SourceEvidenceFreshnessBadgeFinding(
                        "private_or_authenticated_url",
                        path,
                        "badge packet evidence URL must be public and unauthenticated",
                    )
                )
            elif url_text and _url_is_raw_artifact_ref(url_text):
                findings.append(
                    SourceEvidenceFreshnessBadgeFinding(
                        "raw_artifact_reference",
                        path,
                        "badge packet URL field must not point at raw crawl, download, or archive artifacts",
                    )
                )
        if isinstance(value, str):
            lowered = value.casefold()
            if any(marker in lowered for marker in _RAW_ARTIFACT_VALUE_MARKERS):
                findings.append(
                    SourceEvidenceFreshnessBadgeFinding(
                        "raw_artifact_reference",
                        path,
                        "badge packet text must not reference raw crawl, download, archive, or browser artifacts",
                    )
                )
            if any(marker in lowered for marker in _LIVE_FETCH_MARKERS):
                findings.append(
                    SourceEvidenceFreshnessBadgeFinding(
                        "live_fetch_claim",
                        path,
                        "badge packet text must not claim live fetching or live crawling",
                    )
                )

    candidates = packet.get("badge_candidates")
    if not isinstance(candidates, list):
        findings.append(
            SourceEvidenceFreshnessBadgeFinding(
                "missing_badge_candidates",
                "$.badge_candidates",
                "badge packet must contain a badge_candidates list",
            )
        )
        return _dedupe_findings(findings)

    for index, candidate in enumerate(candidates):
        candidate_path = f"$.badge_candidates[{index}]"
        if not isinstance(candidate, Mapping):
            findings.append(
                SourceEvidenceFreshnessBadgeFinding(
                    "badge_candidate_not_object",
                    candidate_path,
                    "badge candidate must be an object",
                )
            )
            continue
        findings.extend(
            _validate_badge_candidate(
                candidate,
                candidate_path,
                source_ids=source_ids,
                requirement_ids=requirement_ids,
                guardrail_ids=guardrail_ids,
            )
        )

    return _dedupe_findings(findings)


def reject_source_evidence_freshness_badge_packet(
    packet: Mapping[str, Any],
    *,
    known_source_ids: Iterable[str] | None = None,
    known_requirement_ids: Iterable[str] | None = None,
    known_guardrail_bundle_ids: Iterable[str] | None = None,
) -> None:
    """Raise when a source evidence freshness badge packet has findings."""

    findings = validate_source_evidence_freshness_badge_packet(
        packet,
        known_source_ids=known_source_ids,
        known_requirement_ids=known_requirement_ids,
        known_guardrail_bundle_ids=known_guardrail_bundle_ids,
    )
    if findings:
        codes = ", ".join(finding.code for finding in findings)
        raise SourceEvidenceFreshnessBadgePacketError(codes)


def _validate_badge_candidate(
    candidate: Mapping[str, Any],
    path: str,
    *,
    source_ids: set[str],
    requirement_ids: set[str],
    guardrail_ids: set[str],
) -> list[SourceEvidenceFreshnessBadgeFinding]:
    findings: list[SourceEvidenceFreshnessBadgeFinding] = []
    badge_state = _text(candidate.get("badge_state") or candidate.get("decision"))

    if badge_state not in BADGE_STATES:
        findings.append(
            SourceEvidenceFreshnessBadgeFinding(
                "unknown_badge_state",
                f"{path}.badge_state",
                "badge_state must be one of the known source freshness badge states",
            )
        )

    citations = _citations(candidate)
    if not citations:
        findings.append(
            SourceEvidenceFreshnessBadgeFinding(
                "uncited_badge_decision",
                f"{path}.citations",
                "every badge decision must cite packet evidence",
            )
        )
    else:
        for citation_index, citation in enumerate(citations):
            citation_path = f"{path}.citations[{citation_index}]"
            if not _first_text(citation.get("canonical_url"), citation.get("url"), citation.get("evidence_ref")):
                findings.append(
                    SourceEvidenceFreshnessBadgeFinding(
                        "uncited_badge_decision",
                        citation_path,
                        "badge citation must include a public URL or evidence reference",
                    )
                )

    source_id = _text(candidate.get("source_id"))
    if source_ids and (not source_id or source_id not in source_ids):
        findings.append(
            SourceEvidenceFreshnessBadgeFinding(
                "unknown_source_id",
                f"{path}.source_id",
                "badge candidate references an unknown source_id",
            )
        )

    for requirement_id in _sorted_texts(candidate.get("requirement_ids")):
        if requirement_ids and requirement_id not in requirement_ids:
            findings.append(
                SourceEvidenceFreshnessBadgeFinding(
                    "unknown_requirement_id",
                    f"{path}.requirement_ids",
                    "badge candidate references an unknown requirement_id",
                )
            )

    guardrail_values = _sorted_texts(candidate.get("affected_guardrail_bundle_ids"))
    guardrail_bundle_id = _text(candidate.get("guardrail_bundle_id"))
    if guardrail_bundle_id:
        guardrail_values.append(guardrail_bundle_id)
    for guardrail_id in sorted(set(guardrail_values)):
        if guardrail_ids and guardrail_id not in guardrail_ids:
            findings.append(
                SourceEvidenceFreshnessBadgeFinding(
                    "unknown_guardrail_id",
                    f"{path}.guardrail_bundle_id",
                    "badge candidate references an unknown guardrail bundle ID",
                )
            )

    if badge_state == "current" and _candidate_contains_stale_evidence(candidate) and not _has_stale_current_acknowledgement(candidate):
        findings.append(
            SourceEvidenceFreshnessBadgeFinding(
                "stale_source_marked_current_without_acknowledgement",
                path,
                "stale or changed source evidence cannot be marked current without explicit acknowledgement",
            )
        )

    return findings


def _extract_triage_entries(packet: dict[str, Any]) -> list[dict[str, Any]]:
    for key in (
        "source_change_impacts",
        "triage_candidates",
        "changed_sources",
        "source_impacts",
        "items",
        "entries",
    ):
        value = packet.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def _extract_traceability_entries(packet: dict[str, Any]) -> list[dict[str, Any]]:
    for key in (
        "traceability_mappings",
        "source_guardrail_mappings",
        "audit_findings",
        "mappings",
        "items",
        "entries",
    ):
        value = packet.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def _index_by_source_id(entries: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for entry in entries:
        source_id = _text(entry.get("source_id"))
        if source_id:
            indexed[source_id] = entry
    return indexed


def _classify_badge_state(triage_entry: dict[str, Any], trace_entry: dict[str, Any]) -> str:
    values = _flatten_text_values(triage_entry) + _flatten_text_values(trace_entry)
    markers = {value.lower().replace(" ", "_") for value in values}

    if markers & _DEFERRED_MARKERS:
        return "deferred"
    if markers & _NEEDS_REVIEW_MARKERS:
        return "needs-review"
    if markers & _STALE_MARKERS:
        return "stale"
    if markers & _CURRENT_MARKERS:
        return "current"
    return "needs-review"


def _rationale_for_state(
    state: str,
    triage_entry: dict[str, Any],
    trace_entry: dict[str, Any],
) -> str:
    source_id = _text(trace_entry.get("source_id")) or "source"
    if state == "deferred":
        return f"{source_id} has deferred or blocked freshness evidence and should not be treated as current."
    if state == "needs-review":
        return f"{source_id} has traceability gaps, conflicts, or review flags that require human review."
    if state == "stale":
        return f"{source_id} has public source change impact evidence affecting cited guardrails or requirements."
    status = _first_text(triage_entry.get("freshness_status"), trace_entry.get("audit_status")) or "current"
    return f"{source_id} is traceable and the consumed packets classify its public evidence as {status}."


def _build_citations(
    source_id: str,
    triage_entry: dict[str, Any],
    trace_entry: dict[str, Any],
) -> list[dict[str, Any]]:
    citations: list[dict[str, Any]] = []
    for packet_name, entry in (
        ("public_source_change_impact_triage", triage_entry),
        ("public_source_to_guardrail_traceability_audit", trace_entry),
    ):
        if not entry:
            continue
        citations.append(
            {
                "packet": packet_name,
                "source_id": source_id,
                "canonical_url": _first_text(entry.get("canonical_url"), entry.get("url")),
                "evidence_ref": _first_text(
                    entry.get("evidence_ref"),
                    entry.get("citation_ref"),
                    entry.get("source_evidence_id"),
                    entry.get("content_hash"),
                ),
                "observed_at": _first_text(
                    entry.get("observed_at"),
                    entry.get("last_seen_at"),
                    entry.get("verified_at"),
                ),
            }
        )
    return citations


def _packet_refs(
    triage_packet: dict[str, Any],
    traceability_packet: dict[str, Any],
) -> dict[str, Any]:
    return {
        "public_source_change_impact_triage_packet_id": _first_text(
            triage_packet.get("packet_id"),
            triage_packet.get("triage_packet_id"),
        ),
        "public_source_to_guardrail_traceability_audit_packet_id": _first_text(
            traceability_packet.get("packet_id"),
            traceability_packet.get("audit_packet_id"),
        ),
    }


def _flatten_text_values(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, bool):
        return ["true" if value else "false"]
    if isinstance(value, (int, float)):
        return [str(value)]
    if isinstance(value, dict):
        values: list[str] = []
        for key, nested in value.items():
            if isinstance(key, str) and key.endswith(("status", "state", "decision", "reason", "severity")):
                values.extend(_flatten_text_values(nested))
            elif isinstance(nested, (dict, list, tuple)):
                values.extend(_flatten_text_values(nested))
        return values
    if isinstance(value, (list, tuple, set)):
        values = []
        for item in value:
            values.extend(_flatten_text_values(item))
        return values
    return []


def _walk_mapping(value: Any, path: str = "$") -> Iterable[tuple[str, str, Any]]:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            yield child_path, key_text, child
            yield from _walk_mapping(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_mapping(child, f"{path}[{index}]")


def _citations(candidate: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    value = candidate.get("citations") or candidate.get("source_citations") or candidate.get("evidence")
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _candidate_contains_stale_evidence(candidate: Mapping[str, Any]) -> bool:
    values = _flatten_text_values(candidate)
    markers = {_normalize_token(value) for value in values}
    return bool(markers & _STALE_MARKERS)


def _has_stale_current_acknowledgement(candidate: Mapping[str, Any]) -> bool:
    for key in _ACK_KEYS:
        value = candidate.get(key)
        if value is True:
            return True
        if isinstance(value, str) and _text(value):
            return True
        if isinstance(value, Mapping):
            approved = value.get("acknowledged") or value.get("approved") or value.get("human_reviewed")
            if approved is True and _first_text(value.get("reviewer"), value.get("acknowledged_by"), value.get("reason")):
                return True
    return False


def _url_is_private_or_authenticated(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"https", "http"}:
        return True
    if parsed.scheme != "https":
        return True
    hostname = parsed.hostname or ""
    if hostname not in _PUBLIC_HOSTS:
        return True
    path = parsed.path.casefold()
    if hostname == "devhub.portlandoregon.gov" and any(marker in path for marker in _PRIVATE_URL_MARKERS):
        return True
    return False


def _url_is_raw_artifact_ref(url: str) -> bool:
    lowered = url.casefold()
    return any(marker in lowered for marker in _RAW_ARTIFACT_VALUE_MARKERS)


def _looks_like_url_key(normalized_key: str) -> bool:
    return normalized_key in {"url", "canonical_url", "requested_url", "source_url", "evidence_url"} or normalized_key.endswith("_url")


def _truthy_or_present(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return bool(value)
    if isinstance(value, Mapping):
        return bool(value)
    return True


def _dedupe_findings(
    findings: list[SourceEvidenceFreshnessBadgeFinding],
) -> list[SourceEvidenceFreshnessBadgeFinding]:
    deduped: dict[tuple[str, str, str], SourceEvidenceFreshnessBadgeFinding] = {}
    for finding in findings:
        deduped[(finding.code, finding.path, finding.message)] = finding
    return list(deduped.values())


def _normalize_token(value: str) -> str:
    normalized: list[str] = []
    previous_underscore = False
    for char in value.strip().casefold():
        if char.isalnum():
            normalized.append(char)
            previous_underscore = False
        else:
            if not previous_underscore:
                normalized.append("_")
            previous_underscore = True
    return "".join(normalized).strip("_")


def _first_text(*values: Any) -> str | None:
    for value in values:
        text = _text(value)
        if text:
            return text
    return None


def _text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return str(value)


def _sorted_texts(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, dict):
        values = list(value.keys())
    elif isinstance(value, (list, tuple, set)):
        values = list(value)
    else:
        values = [value]
    return sorted(text for item in values if (text := _text(item)))


def _slug(value: str) -> str:
    chars: list[str] = []
    for char in value.lower():
        if char.isalnum():
            chars.append(char)
        elif chars and chars[-1] != "-":
            chars.append("-")
    return "".join(chars).strip("-") or "unknown"
