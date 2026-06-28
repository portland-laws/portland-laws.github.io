"""Validation for requirement rerun review disposition packets.

The validator is intentionally schema-light: rerun packets are produced by several
small tools, so this module rejects dangerous fields and checks the minimum audit
contract without requiring one exact envelope shape.
"""

from __future__ import annotations

from dataclasses import dataclass
from ipaddress import ip_address
from typing import Any, Iterable, Mapping
from urllib.parse import parse_qs, urlparse


PRIVATE_HOST_SUFFIXES = (".local", ".internal", ".lan")
AUTH_QUERY_KEYS = {
    "access_token",
    "api_key",
    "apikey",
    "auth",
    "authorization",
    "client_secret",
    "key",
    "password",
    "private_token",
    "secret",
    "signature",
    "token",
    "x-amz-credential",
    "x-amz-signature",
}
RAW_OR_DOWNLOADED_KEYS = {
    "downloaded_document",
    "downloaded_document_path",
    "downloaded_documents",
    "extracted_text",
    "full_text",
    "html",
    "local_document_path",
    "raw_html",
    "raw_markdown",
    "raw_source_text",
    "source_text",
    "text_content",
}
LIVE_EXTRACTION_KEYS = {
    "extracted_live",
    "live_crawl",
    "live_extraction",
    "live_fetch",
    "ran_browser_extraction",
}
MUTATION_KEYS = {
    "active_requirement_mutation",
    "mutate_requirements",
    "requirement_mutation_enabled",
    "update_requirements",
    "write_requirements",
}
HUMAN_REVIEW_STATUSES = {"human_reviewed", "reviewed", "approved_by_human"}
WITHDRAWN_STALE_DISPOSITIONS = {"stale_withdrawn", "withdraw_stale", "withdrawn_stale"}


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    path: str
    message: str


def validate_requirement_rerun_review_packet(
    packet: Mapping[str, Any],
    *,
    known_source_ids: Iterable[str] = (),
    known_document_ids: Iterable[str] = (),
    known_requirement_ids: Iterable[str] = (),
) -> list[ValidationIssue]:
    """Return validation issues for a rerun review disposition packet."""

    issues: list[ValidationIssue] = []
    known_sources = set(known_source_ids)
    known_documents = set(known_document_ids)
    known_requirements = set(known_requirement_ids)

    _walk(packet, "$", issues)
    _validate_references(packet, known_sources, known_documents, known_requirements, issues)
    _validate_dispositions(packet, issues)
    return issues


def assert_valid_requirement_rerun_review_packet(
    packet: Mapping[str, Any],
    *,
    known_source_ids: Iterable[str] = (),
    known_document_ids: Iterable[str] = (),
    known_requirement_ids: Iterable[str] = (),
) -> None:
    issues = validate_requirement_rerun_review_packet(
        packet,
        known_source_ids=known_source_ids,
        known_document_ids=known_document_ids,
        known_requirement_ids=known_requirement_ids,
    )
    if issues:
        detail = "; ".join(f"{issue.code} at {issue.path}: {issue.message}" for issue in issues)
        raise ValueError(detail)


def _walk(value: Any, path: str, issues: list[ValidationIssue]) -> None:
    if isinstance(value, Mapping):
        for raw_key, child in value.items():
            key = str(raw_key)
            child_path = f"{path}.{key}"
            normalized = key.lower().replace("-", "_")
            if normalized in RAW_OR_DOWNLOADED_KEYS:
                issues.append(ValidationIssue("raw_or_downloaded_reference", child_path, "raw source text or downloaded-document references are not allowed"))
            if normalized in LIVE_EXTRACTION_KEYS and bool(child):
                issues.append(ValidationIssue("live_extraction_claim", child_path, "rerun review packets must not claim live extraction"))
            if normalized in MUTATION_KEYS and bool(child):
                issues.append(ValidationIssue("active_requirement_mutation", child_path, "requirement mutation flags must be inactive"))
            if normalized == "extraction_mode" and str(child).lower() == "live":
                issues.append(ValidationIssue("live_extraction_claim", child_path, "extraction_mode must not be live"))
            _walk(child, child_path, issues)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk(child, f"{path}[{index}]", issues)
    elif isinstance(value, str):
        if _looks_like_private_or_authenticated_url(value):
            issues.append(ValidationIssue("private_or_authenticated_url", path, "private or authenticated URLs are not allowed"))


def _validate_references(
    packet: Mapping[str, Any],
    known_sources: set[str],
    known_documents: set[str],
    known_requirements: set[str],
    issues: list[ValidationIssue],
) -> None:
    for path, key, value in _iter_scalar_fields(packet):
        normalized = key.lower().replace("-", "_")
        if normalized == "source_id" and known_sources and str(value) not in known_sources:
            issues.append(ValidationIssue("unknown_source_id", path, f"unknown source_id {value!r}"))
        elif normalized == "document_id" and known_documents and str(value) not in known_documents:
            issues.append(ValidationIssue("unknown_document_id", path, f"unknown document_id {value!r}"))
        elif normalized == "requirement_id" and known_requirements and str(value) not in known_requirements:
            issues.append(ValidationIssue("unknown_requirement_id", path, f"unknown requirement_id {value!r}"))


def _validate_dispositions(packet: Mapping[str, Any], issues: list[ValidationIssue]) -> None:
    dispositions = packet.get("dispositions")
    if not isinstance(dispositions, list):
        issues.append(ValidationIssue("missing_dispositions", "$.dispositions", "packet must include a dispositions list"))
        return

    for index, item in enumerate(dispositions):
        path = f"$.dispositions[{index}]"
        if not isinstance(item, Mapping):
            issues.append(ValidationIssue("invalid_disposition", path, "disposition entries must be objects"))
            continue

        decision = str(item.get("decision", item.get("disposition", ""))).strip().lower()
        citations = item.get("citations", item.get("citation_ids"))
        if not _has_citation(citations):
            issues.append(ValidationIssue("uncited_disposition_decision", path, "each disposition decision must include at least one citation"))

        owner = item.get("reviewer_owner", item.get("reviewer", item.get("owner")))
        if not str(owner or "").strip():
            issues.append(ValidationIssue("missing_reviewer_owner", path, "each disposition must name a reviewer owner"))

        if decision in WITHDRAWN_STALE_DISPOSITIONS and not str(item.get("stale_withdrawal_rationale", "")).strip():
            issues.append(ValidationIssue("missing_stale_withdrawal_rationale", path, "stale withdrawal decisions require a rationale"))

        if bool(item.get("formalized_requirement", item.get("formalized", False))):
            status = str(item.get("human_review_status", item.get("review_status", ""))).strip().lower()
            if status not in HUMAN_REVIEW_STATUSES:
                issues.append(ValidationIssue("formalized_without_human_review", path, "formalized requirements require human-review status"))


def _has_citation(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return any(_has_citation(item) for item in value)
    if isinstance(value, Mapping):
        return any(str(value.get(key, "")).strip() for key in ("citation_id", "source_id", "document_id", "requirement_id", "url"))
    return False


def _iter_scalar_fields(value: Any, path: str = "$"):
    if isinstance(value, Mapping):
        for raw_key, child in value.items():
            key = str(raw_key)
            child_path = f"{path}.{key}"
            if isinstance(child, (Mapping, list)):
                yield from _iter_scalar_fields(child, child_path)
            else:
                yield child_path, key, child
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _iter_scalar_fields(child, f"{path}[{index}]")


def _looks_like_private_or_authenticated_url(value: str) -> bool:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False
    if parsed.username or parsed.password:
        return True
    host = (parsed.hostname or "").lower().strip("[]")
    if host in {"localhost", "0.0.0.0"} or host.endswith(PRIVATE_HOST_SUFFIXES):
        return True
    try:
        address = ip_address(host)
    except ValueError:
        address = None
    if address is not None and (address.is_private or address.is_loopback or address.is_link_local):
        return True
    query_keys = {key.lower() for key in parse_qs(parsed.query)}
    return bool(query_keys & AUTH_QUERY_KEYS)
