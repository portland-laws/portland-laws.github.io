"""Validation for guardrail regeneration readiness packets.

The readiness packet is intentionally accepted as a plain mapping so callers can
validate JSON records before converting them into richer internal contracts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import urlparse


RAW_BODY_FIELD_NAMES = frozenset(
    {
        "raw_body",
        "response_body",
        "body_bytes",
        "raw_html",
        "raw_text",
        "page_source",
        "html_source",
        "body_html",
        "dom_snapshot",
    }
)

DOWNLOADED_DOCUMENT_PATH_FIELD_NAMES = frozenset(
    {
        "downloaded_document_path",
        "downloaded_document_paths",
        "download_path",
        "download_paths",
        "local_document_path",
        "local_document_paths",
        "local_download_path",
        "filesystem_path",
        "file_system_path",
        "absolute_path",
    }
)

STALE_FRESHNESS_STATUSES = frozenset(
    {
        "stale",
        "expired",
        "outdated",
        "superseded",
        "needs_refresh",
        "missing",
        "unknown",
    }
)

CURRENT_CACHE_STATUSES = frozenset(
    {
        "current",
        "fresh",
        "valid",
        "hit",
        "cache_hit",
        "up_to_date",
        "unchanged",
    }
)

REVIEWED_STATUSES = frozenset({"reviewed", "approved", "accepted", "human_reviewed"})
PUBLIC_HOSTS = frozenset(
    {
        "www.portland.gov",
        "portland.gov",
        "devhub.portlandoregon.gov",
        "www.portlandoregon.gov",
        "www.portlandmaps.com",
        "portlandmaps.com",
    }
)
PRIVATE_PATH_MARKERS = (
    "/login",
    "/signin",
    "/sign-in",
    "/register",
    "/account",
    "/accounts",
    "/dashboard",
    "/my-permits",
    "/mypermits",
    "/cart",
    "/checkout",
    "/payment",
    "/payments",
    "/upload",
    "/uploads",
    "/submit",
)
PRIVATE_QUERY_MARKERS = (
    "token",
    "session",
    "auth",
    "code",
    "state",
    "password",
    "receipt",
    "payment",
)


@dataclass(frozen=True)
class ReadinessIssue:
    """A single validation problem found in a readiness packet."""

    code: str
    message: str
    location: str


@dataclass(frozen=True)
class ReadinessValidationResult:
    """Validation result for a guardrail regeneration readiness packet."""

    ready: bool
    issues: tuple[ReadinessIssue, ...]

    def messages(self) -> tuple[str, ...]:
        return tuple(issue.message for issue in self.issues)


class GuardrailRegenerationReadinessError(ValueError):
    """Raised when a guardrail regeneration packet is not ready."""

    def __init__(self, issues: Sequence[ReadinessIssue]) -> None:
        self.issues = tuple(issues)
        detail = "; ".join(issue.message for issue in self.issues)
        super().__init__(detail)


def validate_guardrail_regeneration_readiness(packet: Mapping[str, Any]) -> ReadinessValidationResult:
    """Validate a guardrail regeneration readiness packet.

    The validator rejects packets that would let refreshed predicates advance
    without current public citations, human review, and explicit affected IDs.
    It also blocks fields that must not be committed, such as raw response bodies
    and downloaded document paths.
    """

    issues: list[ReadinessIssue] = []

    affected_requirement_ids = _string_set(packet.get("affected_requirement_ids"))
    affected_predicate_ids = _string_set(packet.get("affected_predicate_ids"))
    if not affected_requirement_ids:
        issues.append(
            ReadinessIssue(
                code="missing_affected_requirement_ids",
                message="readiness packet must name at least one affected requirement ID",
                location="affected_requirement_ids",
            )
        )
    if not affected_predicate_ids:
        issues.append(
            ReadinessIssue(
                code="missing_affected_predicate_ids",
                message="readiness packet must name at least one affected predicate ID",
                location="affected_predicate_ids",
            )
        )

    source_evidence = _list_of_mappings(packet.get("source_evidence"))
    cited_evidence_ids: set[str] = set()
    for index, evidence in enumerate(source_evidence):
        location = f"source_evidence[{index}]"
        evidence_id = _clean_string(evidence.get("source_evidence_id") or evidence.get("evidence_id"))
        if evidence_id:
            cited_evidence_ids.add(evidence_id)
        freshness_status = _clean_string(evidence.get("freshness_status")).lower()
        if freshness_status in STALE_FRESHNESS_STATUSES:
            issues.append(
                ReadinessIssue(
                    code="stale_source_evidence",
                    message=f"source evidence {evidence_id or index} has stale freshness status {freshness_status!r}",
                    location=f"{location}.freshness_status",
                )
            )
        if _truthy(evidence.get("stale")) or _truthy(evidence.get("requires_refresh")):
            issues.append(
                ReadinessIssue(
                    code="stale_source_evidence",
                    message=f"source evidence {evidence_id or index} is marked stale or requiring refresh",
                    location=location,
                )
            )
        _validate_url_fields(evidence, location, issues)

    refreshed_predicates = _list_of_mappings(packet.get("refreshed_predicates"))
    for index, predicate in enumerate(refreshed_predicates):
        location = f"refreshed_predicates[{index}]"
        predicate_id = _clean_string(predicate.get("predicate_id")) or str(index)
        predicate_evidence_ids = _string_set(
            predicate.get("source_evidence_ids")
            or predicate.get("citation_evidence_ids")
            or predicate.get("citations")
        )
        if not predicate_evidence_ids:
            issues.append(
                ReadinessIssue(
                    code="uncited_refreshed_predicate",
                    message=f"refreshed predicate {predicate_id} must cite refreshed public source evidence",
                    location=f"{location}.source_evidence_ids",
                )
            )
        elif cited_evidence_ids and not predicate_evidence_ids.issubset(cited_evidence_ids):
            missing = sorted(predicate_evidence_ids - cited_evidence_ids)
            issues.append(
                ReadinessIssue(
                    code="uncited_refreshed_predicate",
                    message=f"refreshed predicate {predicate_id} cites evidence not present in the readiness packet: {', '.join(missing)}",
                    location=f"{location}.source_evidence_ids",
                )
            )
        if predicate_id and affected_predicate_ids and predicate_id not in affected_predicate_ids:
            issues.append(
                ReadinessIssue(
                    code="missing_affected_predicate_id",
                    message=f"refreshed predicate {predicate_id} is not listed in affected_predicate_ids",
                    location=f"{location}.predicate_id",
                )
            )

    _validate_recursive_fields(packet, "$", issues)
    _validate_url_fields(packet, "$", issues)
    _validate_cache_statuses(packet, "$", _human_reviewed(packet), issues)
    _validate_automatic_promotion(packet, issues)

    return ReadinessValidationResult(ready=not issues, issues=tuple(issues))


def assert_guardrail_regeneration_readiness(packet: Mapping[str, Any]) -> None:
    """Raise if a readiness packet is not acceptable for regeneration."""

    result = validate_guardrail_regeneration_readiness(packet)
    if not result.ready:
        raise GuardrailRegenerationReadinessError(result.issues)


def _validate_recursive_fields(value: Any, location: str, issues: list[ReadinessIssue]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_location = f"{location}.{key_text}" if location != "$" else key_text
            normalized_key = key_text.lower()
            if normalized_key in RAW_BODY_FIELD_NAMES:
                issues.append(
                    ReadinessIssue(
                        code="raw_body_field",
                        message=f"readiness packets must not include raw body field {key_text!r}",
                        location=child_location,
                    )
                )
            if normalized_key in DOWNLOADED_DOCUMENT_PATH_FIELD_NAMES:
                issues.append(
                    ReadinessIssue(
                        code="downloaded_document_path",
                        message=f"readiness packets must not include downloaded document path field {key_text!r}",
                        location=child_location,
                    )
                )
            if _looks_like_local_document_path(normalized_key, child):
                issues.append(
                    ReadinessIssue(
                        code="downloaded_document_path",
                        message=f"readiness packet field {key_text!r} appears to contain a local downloaded document path",
                        location=child_location,
                    )
                )
            _validate_url_fields({key_text: child}, child_location, issues)
            _validate_recursive_fields(child, child_location, issues)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _validate_recursive_fields(child, f"{location}[{index}]", issues)


def _validate_url_fields(value: Mapping[str, Any], location: str, issues: list[ReadinessIssue]) -> None:
    for key, child in value.items():
        key_text = str(key).lower()
        if "url" not in key_text and key_text not in {"href", "link"}:
            continue
        for url in _string_values(child):
            if _is_private_or_authenticated_url(url):
                issues.append(
                    ReadinessIssue(
                        code="private_or_authenticated_url",
                        message=f"readiness packets must cite only public unauthenticated URLs: {url}",
                        location=location,
                    )
                )


def _validate_cache_statuses(
    value: Any,
    location: str,
    human_reviewed: bool,
    issues: list[ReadinessIssue],
) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_location = f"{location}.{key_text}" if location != "$" else key_text
            normalized_key = key_text.lower()
            if normalized_key in {"cache_status", "current_cache_status", "source_cache_status"}:
                status = _clean_string(child).lower()
                if status in CURRENT_CACHE_STATUSES and not human_reviewed:
                    issues.append(
                        ReadinessIssue(
                            code="current_cache_status_before_review",
                            message=f"cache status {status!r} cannot be treated as current before human review",
                            location=child_location,
                        )
                    )
            _validate_cache_statuses(child, child_location, human_reviewed, issues)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _validate_cache_statuses(child, f"{location}[{index}]", human_reviewed, issues)


def _validate_automatic_promotion(packet: Mapping[str, Any], issues: list[ReadinessIssue]) -> None:
    promotion_fields = (
        "automatic_guardrail_promotion",
        "auto_promote_guardrails",
        "promote_guardrails",
        "promote_to_active",
        "promotion_mode",
        "target_validation_status",
    )
    for field in promotion_fields:
        if field not in packet:
            continue
        value = packet[field]
        if _truthy(value) or _clean_string(value).lower() in {"automatic", "auto", "active", "promoted", "approved"}:
            issues.append(
                ReadinessIssue(
                    code="automatic_guardrail_promotion",
                    message="readiness packets must not request automatic guardrail promotion",
                    location=field,
                )
            )


def _human_reviewed(packet: Mapping[str, Any]) -> bool:
    status = _clean_string(packet.get("human_review_status") or packet.get("review_status")).lower()
    if status in REVIEWED_STATUSES:
        return True
    review = packet.get("review")
    if isinstance(review, Mapping):
        review_status = _clean_string(review.get("status") or review.get("human_review_status")).lower()
        return review_status in REVIEWED_STATUSES
    return False


def _is_private_or_authenticated_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return True
    host = (parsed.hostname or "").lower()
    if host not in PUBLIC_HOSTS:
        return True
    path = parsed.path.lower()
    if host == "devhub.portlandoregon.gov" and path not in {"", "/"}:
        return True
    if any(marker in path for marker in PRIVATE_PATH_MARKERS):
        return True
    query = parsed.query.lower()
    return any(marker in query for marker in PRIVATE_QUERY_MARKERS)


def _looks_like_local_document_path(key: str, value: Any) -> bool:
    if not isinstance(value, str):
        return False
    text = value.strip().lower()
    if not text:
        return False
    if key.endswith("path") and (text.startswith("/") or text.startswith("~/") or ":\\" in text):
        return True
    return text.endswith((".pdf", ".doc", ".docx", ".xls", ".xlsx")) and (
        text.startswith("/") or "/downloads/" in text or "\\downloads\\" in text
    )


def _list_of_mappings(value: Any) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def _string_set(value: Any) -> set[str]:
    return {item for item in _string_values(value) if item}


def _string_values(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value.strip()
    elif isinstance(value, Mapping):
        evidence_id = value.get("source_evidence_id") or value.get("evidence_id") or value.get("id")
        if isinstance(evidence_id, str):
            yield evidence_id.strip()
    elif isinstance(value, list) or isinstance(value, tuple) or isinstance(value, set):
        for item in value:
            yield from _string_values(item)


def _clean_string(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on", "auto", "automatic"}
    return bool(value)
