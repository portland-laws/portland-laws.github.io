"""Validation for PP&D public-source-to-guardrail traceability audit packets.

The validator is intentionally dictionary-oriented so deterministic fixtures can be
checked before the PP&D pipeline grows a stable shared packet contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping
from urllib.parse import urlparse


PRIVATE_URL_MARKERS = (
    "/account",
    "/accounts",
    "/dashboard",
    "/identity",
    "/login",
    "/my-permits",
    "/mypermits",
    "/oauth",
    "/permitdetails",
    "/profile",
    "/secure",
    "/signin",
    "/sign-in",
    "/user",
)

SECRET_QUERY_KEYS = {
    "access_token",
    "auth",
    "code",
    "cookie",
    "key",
    "password",
    "session",
    "state",
    "ticket",
    "token",
}

RAW_REFERENCE_KEYS = {
    "archive_artifact_ref",
    "archive_ref",
    "archive_url",
    "body",
    "body_ref",
    "body_url",
    "content",
    "content_ref",
    "download_ref",
    "download_url",
    "har_path",
    "html",
    "raw",
    "raw_body",
    "raw_body_path",
    "raw_body_ref",
    "raw_body_url",
    "raw_download_url",
    "screenshot_path",
    "trace_path",
    "warc_path",
    "warc_ref",
}

SOURCE_ID_KEYS = {
    "citation_source_id",
    "evidence_source_id",
    "source_evidence_id",
    "source_id",
}

SOURCE_ID_LIST_KEYS = {
    "citation_source_ids",
    "evidence_source_ids",
    "source_evidence_ids",
    "source_ids",
}

REQUIREMENT_ID_KEYS = {
    "blocked_by_requirement_id",
    "depends_on_requirement_id",
    "prerequisite_requirement_id",
    "requirement_id",
}

REQUIREMENT_ID_LIST_KEYS = {
    "blocked_by_requirement_ids",
    "depends_on_requirement_ids",
    "prerequisite_requirement_ids",
    "requirement_ids",
}

LIVE_FETCH_KEYS = {
    "fetched_live",
    "live_fetch",
    "live_fetch_claim",
    "live_fetch_performed",
    "used_live_fetch",
}

MUTATION_FLAG_KEYS = {
    "active_bundle_mutation",
    "active_mutation",
    "allow_bundle_mutation",
    "bundle_mutation_active",
    "is_mutable",
    "mutation_enabled",
}


@dataclass(frozen=True)
class TraceabilityAuditFinding:
    """A single validation failure in a traceability audit packet."""

    code: str
    message: str
    path: str


def validate_traceability_audit_packet(
    packet: Mapping[str, Any],
    *,
    known_source_ids: Iterable[str] | None = None,
    known_requirement_ids: Iterable[str] | None = None,
) -> list[TraceabilityAuditFinding]:
    """Return all deterministic traceability audit packet validation failures."""

    source_ids = set(known_source_ids or ()) | _collect_declared_ids(
        packet, "source_id", ("sources", "source_registry", "public_sources")
    )
    requirement_ids = set(known_requirement_ids or ()) | _collect_declared_ids(
        packet, "requirement_id", ("requirements", "requirement_nodes")
    )
    stale_acknowledgements = _collect_acknowledged_stale_source_ids(packet)

    findings: list[TraceabilityAuditFinding] = []
    _walk(packet, "$", findings, source_ids, requirement_ids, stale_acknowledgements)
    _validate_requirements_have_cited_prerequisites(packet, findings, source_ids, requirement_ids)
    return findings


def assert_valid_traceability_audit_packet(
    packet: Mapping[str, Any],
    *,
    known_source_ids: Iterable[str] | None = None,
    known_requirement_ids: Iterable[str] | None = None,
) -> None:
    """Raise ValueError when a traceability audit packet is not acceptable."""

    findings = validate_traceability_audit_packet(
        packet,
        known_source_ids=known_source_ids,
        known_requirement_ids=known_requirement_ids,
    )
    if findings:
        rendered = "; ".join(f"{finding.code} at {finding.path}: {finding.message}" for finding in findings)
        raise ValueError(rendered)


def _walk(
    value: Any,
    path: str,
    findings: list[TraceabilityAuditFinding],
    source_ids: set[str],
    requirement_ids: set[str],
    stale_acknowledgements: set[str],
) -> None:
    if isinstance(value, Mapping):
        _validate_mapping(value, path, findings, source_ids, requirement_ids, stale_acknowledgements)
        for key, nested in value.items():
            _walk(nested, f"{path}.{key}", findings, source_ids, requirement_ids, stale_acknowledgements)
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _walk(nested, f"{path}[{index}]", findings, source_ids, requirement_ids, stale_acknowledgements)
    elif isinstance(value, str):
        _validate_string_reference(value, path, findings)


def _validate_mapping(
    item: Mapping[str, Any],
    path: str,
    findings: list[TraceabilityAuditFinding],
    source_ids: set[str],
    requirement_ids: set[str],
    stale_acknowledgements: set[str],
) -> None:
    for key, nested in item.items():
        key_text = str(key)
        key_lower = key_text.lower()
        nested_path = f"{path}.{key_text}"

        if key_lower in RAW_REFERENCE_KEYS and _is_present(nested):
            findings.append(
                TraceabilityAuditFinding(
                    "raw_reference",
                    "audit packets must not include raw body, download, archive, trace, HAR, or screenshot references",
                    nested_path,
                )
            )

        if key_lower in LIVE_FETCH_KEYS and _truthy(nested):
            findings.append(
                TraceabilityAuditFinding(
                    "live_fetch_claim",
                    "audit packets must not claim live fetches; use deterministic captured source metadata instead",
                    nested_path,
                )
            )

        if key_lower in MUTATION_FLAG_KEYS and _truthy(nested):
            findings.append(
                TraceabilityAuditFinding(
                    "active_bundle_mutation",
                    "guardrail bundle mutation must be inactive while a traceability packet is audited",
                    nested_path,
                )
            )

        if key_lower in SOURCE_ID_KEYS and key_lower != "source_id":
            _validate_known_id(nested, source_ids, "unknown_source_id", nested_path, findings)
        elif key_lower in SOURCE_ID_LIST_KEYS:
            _validate_known_ids(nested, source_ids, "unknown_source_id", nested_path, findings)

        if key_lower in REQUIREMENT_ID_KEYS and key_lower != "requirement_id":
            _validate_known_id(nested, requirement_ids, "unknown_requirement_id", nested_path, findings)
        elif key_lower in REQUIREMENT_ID_LIST_KEYS:
            _validate_known_ids(nested, requirement_ids, "unknown_requirement_id", nested_path, findings)

    _validate_url_mapping(item, path, findings)
    _validate_traceability_gap(item, path, findings)
    _validate_stale_current_source(item, path, findings, stale_acknowledgements)


def _validate_requirements_have_cited_prerequisites(
    packet: Mapping[str, Any],
    findings: list[TraceabilityAuditFinding],
    source_ids: set[str],
    requirement_ids: set[str],
) -> None:
    for collection_key in ("requirements", "requirement_nodes"):
        collection = packet.get(collection_key)
        if not isinstance(collection, list):
            continue
        for index, requirement in enumerate(collection):
            if not isinstance(requirement, Mapping):
                continue
            requirement_path = f"$.{collection_key}[{index}]"
            for prerequisite_key in ("prerequisites", "prerequisite_links", "prerequisite_requirement_ids"):
                if prerequisite_key not in requirement:
                    continue
                prerequisite_value = requirement[prerequisite_key]
                if not _is_present(prerequisite_value):
                    findings.append(
                        TraceabilityAuditFinding(
                            "missing_prerequisite_link",
                            "declared prerequisite collections must name at least one requirement link",
                            f"{requirement_path}.{prerequisite_key}",
                        )
                    )
                    continue
                if prerequisite_key == "prerequisites" and isinstance(prerequisite_value, list):
                    for prereq_index, prereq in enumerate(prerequisite_value):
                        prereq_path = f"{requirement_path}.{prerequisite_key}[{prereq_index}]"
                        if isinstance(prereq, Mapping):
                            linked_requirement = prereq.get("requirement_id") or prereq.get("prerequisite_requirement_id")
                            cited_sources = prereq.get("source_evidence_ids") or prereq.get("citation_source_ids")
                            if not linked_requirement:
                                findings.append(
                                    TraceabilityAuditFinding(
                                        "missing_prerequisite_link",
                                        "prerequisite entries must link to a requirement id",
                                        prereq_path,
                                    )
                                )
                            else:
                                _validate_known_id(linked_requirement, requirement_ids, "unknown_requirement_id", prereq_path, findings)
                            if not cited_sources:
                                findings.append(
                                    TraceabilityAuditFinding(
                                        "uncited_prerequisite_link",
                                        "prerequisite entries must cite source evidence",
                                        prereq_path,
                                    )
                                )
                            else:
                                _validate_known_ids(cited_sources, source_ids, "unknown_source_id", prereq_path, findings)


def _validate_traceability_gap(
    item: Mapping[str, Any], path: str, findings: list[TraceabilityAuditFinding]) -> None:
    if not _looks_like_gap(item):
        return
    citation_values = (
        item.get("citation_ids"),
        item.get("citation_source_ids"),
        item.get("source_evidence_ids"),
        item.get("requirement_ids"),
    )
    if not any(_is_present(value) for value in citation_values):
        findings.append(
            TraceabilityAuditFinding(
                "uncited_traceability_gap",
                "traceability gaps must cite the affected source or requirement evidence",
                path,
            )
        )


def _validate_stale_current_source(
    item: Mapping[str, Any],
    path: str,
    findings: list[TraceabilityAuditFinding],
    stale_acknowledgements: set[str],
) -> None:
    source_id = item.get("source_id")
    if not isinstance(source_id, str):
        return
    freshness = str(item.get("freshness_status", "")).strip().lower()
    marked_current = freshness in {"current", "fresh", "active"} or item.get("marked_current") is True
    stale_indicator = any(
        _truthy(item.get(key))
        for key in ("is_stale", "stale", "staleness_reason", "stale_as_of", "stale_source")
    )
    if marked_current and stale_indicator and source_id not in stale_acknowledgements:
        findings.append(
            TraceabilityAuditFinding(
                "stale_source_marked_current",
                "stale sources may not be marked current without an explicit stale-source acknowledgement",
                path,
            )
        )


def _validate_url_mapping(item: Mapping[str, Any], path: str, findings: list[TraceabilityAuditFinding]) -> None:
    for key in ("canonical_url", "requested_url", "url", "href"):
        value = item.get(key)
        if isinstance(value, str):
            _validate_url(value, f"{path}.{key}", findings)

    source_type = str(item.get("source_type", "")).lower()
    privacy = str(item.get("privacy_classification", "")).lower()
    auth_scope = str(item.get("auth_scope", "")).lower()
    if source_type == "devhub_authenticated" or privacy in {"private", "authenticated", "account_scoped"} or auth_scope == "authenticated":
        findings.append(
            TraceabilityAuditFinding(
                "private_or_authenticated_source",
                "public traceability audit packets must not include private or authenticated source records",
                path,
            )
        )


def _validate_url(url: str, path: str, findings: list[TraceabilityAuditFinding]) -> None:
    parsed = urlparse(url)
    if parsed.username or parsed.password:
        findings.append(
            TraceabilityAuditFinding(
                "private_or_authenticated_url",
                "URLs with embedded credentials are not permitted in public traceability packets",
                path,
            )
        )
    lowered_path = parsed.path.lower()
    if any(marker in lowered_path for marker in PRIVATE_URL_MARKERS):
        findings.append(
            TraceabilityAuditFinding(
                "private_or_authenticated_url",
                "URLs that point at private, account, sign-in, or authenticated surfaces are not permitted",
                path,
            )
        )
    query_keys = {part.split("=", 1)[0].lower() for part in parsed.query.split("&") if part}
    if query_keys & SECRET_QUERY_KEYS:
        findings.append(
            TraceabilityAuditFinding(
                "private_or_authenticated_url",
                "URLs with token, session, auth, or credential query parameters are not permitted",
                path,
            )
        )
    if "/download" in lowered_path or lowered_path.endswith((".warc", ".har")):
        findings.append(
            TraceabilityAuditFinding(
                "raw_reference",
                "download, WARC, and HAR references are not permitted in traceability audit packets",
                path,
            )
        )


def _validate_string_reference(value: str, path: str, findings: list[TraceabilityAuditFinding]) -> None:
    lowered = value.lower()
    if lowered.startswith(("http://", "https://")):
        _validate_url(value, path, findings)
    if "live fetch" in lowered or "fetched live" in lowered:
        findings.append(
            TraceabilityAuditFinding(
                "live_fetch_claim",
                "audit packet text must not claim live fetches",
                path,
            )
        )


def _validate_known_id(
    value: Any,
    known_ids: set[str],
    code: str,
    path: str,
    findings: list[TraceabilityAuditFinding],
) -> None:
    if not isinstance(value, str) or not value:
        return
    if known_ids and value not in known_ids:
        findings.append(TraceabilityAuditFinding(code, f"unknown id {value!r}", path))


def _validate_known_ids(
    value: Any,
    known_ids: set[str],
    code: str,
    path: str,
    findings: list[TraceabilityAuditFinding],
) -> None:
    if isinstance(value, str):
        _validate_known_id(value, known_ids, code, path, findings)
        return
    if not isinstance(value, list):
        return
    for index, item in enumerate(value):
        _validate_known_id(item, known_ids, code, f"{path}[{index}]", findings)


def _collect_declared_ids(packet: Mapping[str, Any], id_key: str, collection_keys: tuple[str, ...]) -> set[str]:
    declared: set[str] = set()
    for collection_key in collection_keys:
        collection = packet.get(collection_key)
        if not isinstance(collection, list):
            continue
        for item in collection:
            if isinstance(item, Mapping) and isinstance(item.get(id_key), str):
                declared.add(item[id_key])
    return declared


def _collect_acknowledged_stale_source_ids(packet: Mapping[str, Any]) -> set[str]:
    acknowledged: set[str] = set()
    for key in ("acknowledged_stale_source_ids", "stale_source_acknowledgements"):
        value = packet.get(key)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    acknowledged.add(item)
                elif isinstance(item, Mapping) and isinstance(item.get("source_id"), str):
                    acknowledged.add(item["source_id"])
    return acknowledged


def _looks_like_gap(item: Mapping[str, Any]) -> bool:
    if "gap_id" in item:
        return True
    kind = str(item.get("type", item.get("gap_type", ""))).lower()
    status = str(item.get("traceability_status", "")).lower()
    return "gap" in kind or status == "gap"


def _is_present(value: Any) -> bool:
    if value is None:
        return False
    if value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _truthy(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "active", "enabled", "mutable"}
    return bool(value)
