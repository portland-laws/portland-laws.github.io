"""Validation for PP&D requirement extraction rerun rehearsal packets.

The validator is intentionally side-effect free. It accepts already-loaded packet
mappings and checks that rehearsal input is limited to cited, registered,
review-owned, public-source deltas with no live extraction or mutation claims.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import urlparse


@dataclass(frozen=True)
class RehearsalValidationIssue:
    """A deterministic validation failure for a rehearsal packet."""

    code: str
    message: str
    path: str


_PRIVATE_URL_MARKERS = (
    "/login",
    "/log-in",
    "/logout",
    "/sign-in",
    "/signin",
    "/register",
    "/account",
    "/accounts/",
    "/my-permits",
    "/mypermits",
    "/dashboard",
    "/profile",
    "/payment",
    "/payments",
    "/checkout",
    "/upload",
    "/submit",
    "/inspection/schedule",
)

_AUTH_SOURCE_TYPES = {
    "devhub_authenticated",
    "authenticated",
    "private",
    "account_scoped",
}

_RAW_REFERENCE_KEYS = {
    "raw_source_text",
    "raw_text",
    "source_text",
    "body_text",
    "html_body",
    "html",
    "pdf_text",
    "downloaded_document",
    "downloaded_documents",
    "downloaded_document_ref",
    "downloaded_document_refs",
    "download_path",
    "download_paths",
    "local_path",
    "local_paths",
    "file_path",
    "file_paths",
    "document_path",
    "document_paths",
    "raw_document_ref",
    "raw_document_refs",
}

_LIVE_CLAIM_KEYS = {
    "live_extraction",
    "live_crawl",
    "live_browser",
    "live_extracted_at",
    "live_crawled_at",
    "browser_session",
    "playwright_session",
    "network_capture",
}

_MUTATION_KEYS = {
    "active_requirement_mutation",
    "active_requirement_mutations",
    "active_mutation",
    "active_mutations",
    "mutates_requirements",
    "mutation_enabled",
    "mutation_flags",
    "write_to_registry",
    "write_registry",
    "commit_requirements",
    "update_requirements",
    "apply_requirement_changes",
}

_REVIEWED_STATUSES = {
    "accepted",
    "approved",
    "human_reviewed",
    "reviewed",
    "needs_revision",
    "rejected",
    "withdrawn",
}

_STALE_STATUSES = {"stale", "superseded", "withdrawn", "obsolete", "retired"}


class RehearsalPacketValidationError(ValueError):
    """Raised when a rehearsal packet fails validation."""

    def __init__(self, issues: Sequence[RehearsalValidationIssue]) -> None:
        self.issues = tuple(issues)
        joined = "; ".join(f"{issue.code} at {issue.path}: {issue.message}" for issue in self.issues)
        super().__init__(joined)


def validate_rehearsal_packet(packet: Mapping[str, Any]) -> list[RehearsalValidationIssue]:
    """Return deterministic validation issues for a rerun rehearsal packet."""

    issues: list[RehearsalValidationIssue] = []
    source_ids = _id_set(packet, "known_source_ids", "source_registry", "sources")
    document_ids = _id_set(packet, "known_document_ids", "document_registry", "documents")
    requirement_ids = _id_set(packet, "known_requirement_ids", "requirement_registry", "requirements")
    evidence_ids = _id_set(packet, "known_evidence_ids", "evidence_registry", "evidence")

    _validate_global_claims(packet, issues)
    _validate_sources(packet, source_ids, issues)
    _validate_deltas(packet, source_ids, document_ids, requirement_ids, evidence_ids, issues)
    _validate_formalized_requirements(packet, issues)
    _validate_stale_candidates(packet, issues)
    _validate_reviewer_owners(packet, issues)
    _scan_for_forbidden_fields(packet, "$", issues)

    return _dedupe_issues(issues)


def assert_valid_rehearsal_packet(packet: Mapping[str, Any]) -> None:
    """Raise if a rerun rehearsal packet is not acceptable."""

    issues = validate_rehearsal_packet(packet)
    if issues:
        raise RehearsalPacketValidationError(issues)


def _validate_global_claims(packet: Mapping[str, Any], issues: list[RehearsalValidationIssue]) -> None:
    mode = _lower_text(packet.get("extraction_mode") or packet.get("mode"))
    if mode in {"live", "crawl", "browser", "devhub", "authenticated"}:
        issues.append(
            RehearsalValidationIssue(
                "live_extraction_claim",
                "rerun rehearsal packets must not claim live extraction or browser collection",
                "$.extraction_mode",
            )
        )


def _validate_sources(
    packet: Mapping[str, Any], source_ids: set[str], issues: list[RehearsalValidationIssue]
) -> None:
    for index, source in enumerate(_records(packet, "source_registry", "sources")):
        path = f"$.sources[{index}]"
        source_id = _record_id(source)
        if source_id and source_id not in source_ids:
            source_ids.add(source_id)
        source_type = _lower_text(source.get("source_type") or source.get("type"))
        if source_type in _AUTH_SOURCE_TYPES:
            issues.append(
                RehearsalValidationIssue(
                    "private_or_authenticated_source",
                    "source registry entries for rehearsal must be public-source metadata only",
                    f"{path}.source_type",
                )
            )
        for key in ("canonical_url", "url", "requested_url"):
            value = source.get(key)
            if isinstance(value, str) and _is_private_or_authenticated_url(value):
                issues.append(
                    RehearsalValidationIssue(
                        "private_or_authenticated_url",
                        "private, account-scoped, payment, upload, submit, or authenticated URLs are not allowed",
                        f"{path}.{key}",
                    )
                )


def _validate_deltas(
    packet: Mapping[str, Any],
    source_ids: set[str],
    document_ids: set[str],
    requirement_ids: set[str],
    evidence_ids: set[str],
    issues: list[RehearsalValidationIssue],
) -> None:
    for index, delta in enumerate(_records(packet, "requirement_deltas", "deltas")):
        path = f"$.requirement_deltas[{index}]"
        requirement_id = _text(delta.get("requirement_id") or delta.get("id"))
        if not requirement_id or requirement_id not in requirement_ids:
            issues.append(
                RehearsalValidationIssue(
                    "unknown_requirement_id",
                    "each requirement delta must reference a known requirement id",
                    f"{path}.requirement_id",
                )
            )

        for field in ("source_id", "source_ids"):
            for value in _as_list(delta.get(field)):
                source_id = _text(value)
                if source_id and source_id not in source_ids:
                    issues.append(
                        RehearsalValidationIssue(
                            "unknown_source_id",
                            "requirement deltas may only cite registered source ids",
                            f"{path}.{field}",
                        )
                    )

        for field in ("document_id", "document_ids"):
            for value in _as_list(delta.get(field)):
                document_id = _text(value)
                if document_id and document_id not in document_ids:
                    issues.append(
                        RehearsalValidationIssue(
                            "unknown_document_id",
                            "requirement deltas may only cite registered document ids",
                            f"{path}.{field}",
                        )
                    )

        citations = _as_list(delta.get("citations")) + _as_list(delta.get("source_evidence_ids")) + _as_list(
            delta.get("evidence_ids")
        )
        if not citations:
            issues.append(
                RehearsalValidationIssue(
                    "uncited_requirement_delta",
                    "each requirement delta must include citations or source evidence ids",
                    path,
                )
            )
        for citation_index, citation in enumerate(citations):
            if isinstance(citation, Mapping):
                evidence_id = _text(citation.get("evidence_id") or citation.get("id"))
                citation_source_id = _text(citation.get("source_id"))
                citation_document_id = _text(citation.get("document_id"))
                if evidence_id and evidence_ids and evidence_id not in evidence_ids:
                    issues.append(
                        RehearsalValidationIssue(
                            "unknown_evidence_id",
                            "citation evidence ids must be known when an evidence registry is supplied",
                            f"{path}.citations[{citation_index}].evidence_id",
                        )
                    )
                if citation_source_id and citation_source_id not in source_ids:
                    issues.append(
                        RehearsalValidationIssue(
                            "unknown_source_id",
                            "citation source ids must be registered",
                            f"{path}.citations[{citation_index}].source_id",
                        )
                    )
                if citation_document_id and citation_document_id not in document_ids:
                    issues.append(
                        RehearsalValidationIssue(
                            "unknown_document_id",
                            "citation document ids must be registered",
                            f"{path}.citations[{citation_index}].document_id",
                        )
                    )
            else:
                evidence_id = _text(citation)
                if evidence_id and evidence_ids and evidence_id not in evidence_ids:
                    issues.append(
                        RehearsalValidationIssue(
                            "unknown_evidence_id",
                            "source evidence ids must be known when an evidence registry is supplied",
                            f"{path}.source_evidence_ids",
                        )
                    )


def _validate_formalized_requirements(
    packet: Mapping[str, Any], issues: list[RehearsalValidationIssue]
) -> None:
    formalized = list(_records(packet, "formalized_requirements"))
    for delta in _records(packet, "requirement_deltas", "deltas"):
        status = _lower_text(delta.get("formalization_status"))
        if status in {"formalized", "compiled", "ready"}:
            formalized.append(delta)
    for index, requirement in enumerate(formalized):
        review_status = _lower_text(requirement.get("human_review_status") or requirement.get("review_status"))
        if review_status not in _REVIEWED_STATUSES:
            issues.append(
                RehearsalValidationIssue(
                    "formalized_requirement_missing_review_status",
                    "formalized requirements must carry a human review status",
                    f"$.formalized_requirements[{index}].human_review_status",
                )
            )


def _validate_stale_candidates(packet: Mapping[str, Any], issues: list[RehearsalValidationIssue]) -> None:
    candidates = _records(packet, "stale_candidates", "candidate_requirements", "requirements")
    for index, candidate in enumerate(candidates):
        status = _lower_text(candidate.get("freshness_status") or candidate.get("status"))
        if status in _STALE_STATUSES:
            note = _text(candidate.get("withdrawal_note") or candidate.get("withdrawal_notes"))
            if not note:
                issues.append(
                    RehearsalValidationIssue(
                        "stale_candidate_missing_withdrawal_note",
                        "stale, obsolete, superseded, retired, or withdrawn candidates require withdrawal notes",
                        f"$.stale_candidates[{index}].withdrawal_note",
                    )
                )


def _validate_reviewer_owners(packet: Mapping[str, Any], issues: list[RehearsalValidationIssue]) -> None:
    owners = _as_list(packet.get("reviewer_owners"))
    owner = _text(packet.get("reviewer_owner"))
    if owner:
        owners.append(owner)
    if not [item for item in owners if _text(item)]:
        issues.append(
            RehearsalValidationIssue(
                "missing_reviewer_owner",
                "rerun rehearsal packets must identify at least one reviewer owner",
                "$.reviewer_owner",
            )
        )

    for index, delta in enumerate(_records(packet, "requirement_deltas", "deltas")):
        delta_owner = _text(delta.get("reviewer_owner") or delta.get("owner"))
        if not delta_owner:
            issues.append(
                RehearsalValidationIssue(
                    "missing_reviewer_owner",
                    "each requirement delta must identify a reviewer owner",
                    f"$.requirement_deltas[{index}].reviewer_owner",
                )
            )


def _scan_for_forbidden_fields(value: Any, path: str, issues: list[RehearsalValidationIssue]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            normalized = key_text.lower()
            if normalized in _RAW_REFERENCE_KEYS and _truthy(child):
                issues.append(
                    RehearsalValidationIssue(
                        "raw_source_text_or_downloaded_document_reference",
                        "rehearsal packets must use citation metadata, not raw source text or downloaded document references",
                        child_path,
                    )
                )
            if normalized in _LIVE_CLAIM_KEYS and _truthy(child):
                issues.append(
                    RehearsalValidationIssue(
                        "live_extraction_claim",
                        "rerun rehearsal packets must not claim live extraction, browser sessions, or network capture",
                        child_path,
                    )
                )
            if normalized in _MUTATION_KEYS and _truthy(child):
                issues.append(
                    RehearsalValidationIssue(
                        "active_requirement_mutation_flag",
                        "rerun rehearsal packets must not enable active requirement mutation flags",
                        child_path,
                    )
                )
            if isinstance(child, str) and normalized.endswith("url") and _is_private_or_authenticated_url(child):
                issues.append(
                    RehearsalValidationIssue(
                        "private_or_authenticated_url",
                        "private, account-scoped, payment, upload, submit, or authenticated URLs are not allowed",
                        child_path,
                    )
                )
            _scan_for_forbidden_fields(child, child_path, issues)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _scan_for_forbidden_fields(child, f"{path}[{index}]", issues)


def _id_set(packet: Mapping[str, Any], *keys: str) -> set[str]:
    ids: set[str] = set()
    for key in keys:
        value = packet.get(key)
        for item in _as_list(value):
            if isinstance(item, Mapping):
                record_id = _record_id(item)
                if record_id:
                    ids.add(record_id)
            else:
                text = _text(item)
                if text:
                    ids.add(text)
    return ids


def _records(packet: Mapping[str, Any], *keys: str) -> Iterable[Mapping[str, Any]]:
    for key in keys:
        for item in _as_list(packet.get(key)):
            if isinstance(item, Mapping):
                yield item


def _record_id(record: Mapping[str, Any]) -> str:
    for key in ("id", "source_id", "document_id", "requirement_id", "evidence_id"):
        value = _text(record.get(key))
        if value:
            return value
    return ""


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return list(value)
    return [value]


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    return ""


def _lower_text(value: Any) -> str:
    return _text(value).lower()


def _truthy(value: Any) -> bool:
    if value is None or value is False:
        return False
    if value == "":
        return False
    if value == [] or value == {}:
        return False
    return True


def _is_private_or_authenticated_url(url: str) -> bool:
    parsed = urlparse(url)
    path = parsed.path.lower()
    host = parsed.netloc.lower()
    query = parsed.query.lower()
    if parsed.username or parsed.password:
        return True
    if host and host not in {
        "www.portland.gov",
        "portland.gov",
        "devhub.portlandoregon.gov",
        "www.portlandoregon.gov",
        "www.portlandmaps.com",
        "portlandmaps.com",
    }:
        return True
    private_text = f"{path}?{query}"
    return any(marker in private_text for marker in _PRIVATE_URL_MARKERS)


def _dedupe_issues(issues: Sequence[RehearsalValidationIssue]) -> list[RehearsalValidationIssue]:
    seen: set[tuple[str, str]] = set()
    deduped: list[RehearsalValidationIssue] = []
    for issue in issues:
        key = (issue.code, issue.path)
        if key not in seen:
            seen.add(key)
            deduped.append(issue)
    return deduped
