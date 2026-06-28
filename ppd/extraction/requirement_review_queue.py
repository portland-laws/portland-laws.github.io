"""Validation for requirement extraction human-review queue packets.

The review queue is the boundary between source extraction and formal PP&D
requirements. Packets crossing this boundary must be citation-only, deterministic,
and explicitly owned by a reviewer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import parse_qsl, urlparse


_REVIEW_STATUSES = {
    "needs_review",
    "in_review",
    "approved",
    "rejected",
    "changes_requested",
}

_FORMALIZED_STATUSES = {"formalized", "compiled", "published", "active"}

_PRIVATE_URL_MARKERS = (
    "account",
    "admin",
    "auth",
    "callback",
    "case",
    "dashboard",
    "login",
    "logout",
    "my-permits",
    "mypermits",
    "oauth",
    "password",
    "payment",
    "permitdetails",
    "profile",
    "session",
    "signin",
    "sign-in",
    "upload",
)

_PRIVATE_QUERY_KEYS = {
    "access_token",
    "apikey",
    "api_key",
    "auth",
    "code",
    "id_token",
    "jwt",
    "key",
    "password",
    "refresh_token",
    "session",
    "sessionid",
    "sid",
    "signature",
    "token",
}

_RAW_TEXT_KEYS = {
    "body_text",
    "downloaded_text",
    "extracted_source_text",
    "full_text",
    "html",
    "markdown",
    "normalized_text",
    "ocr_text",
    "page_text",
    "raw_body",
    "raw_html",
    "raw_source_text",
    "source_raw_text",
    "source_text",
}

_DOWNLOADED_DOCUMENT_KEYS = {
    "archive_artifact_ref",
    "download_path",
    "downloaded_document",
    "downloaded_document_ref",
    "local_document_path",
    "raw_document_ref",
    "source_file_path",
    "warc_path",
}

_LIVE_EXTRACTION_KEYS = {
    "browser_session_id",
    "crawl_run_id",
    "extracted_at_live",
    "live_claim",
    "live_extraction",
    "live_extraction_claim",
    "playwright_trace",
    "session_state_ref",
}

_MUTATION_KEYS = {
    "active_requirement_mutation",
    "active_requirement_mutation_flag",
    "active_requirement_mutation_flags",
    "mutate_active_requirement",
    "mutation_flags",
    "patch_target_requirement_id",
    "target_active_requirement_id",
    "updates_active_requirement",
}


@dataclass(frozen=True)
class ReviewQueueValidationError:
    """A single deterministic validation finding."""

    code: str
    message: str
    path: str


def validate_review_queue_packet(
    packet: Mapping[str, Any], known_source_ids: Iterable[str] | None = None
) -> list[ReviewQueueValidationError]:
    """Return validation errors for a requirement human-review queue packet."""

    errors: list[ReviewQueueValidationError] = []
    known_sources = set(known_source_ids or ()) | _source_ids_from_packet(packet)

    if _truthy(packet.get("live_extraction")) or _truthy(packet.get("live_extraction_claim")):
        errors.append(
            ReviewQueueValidationError(
                "live_extraction_claim",
                "review queue packets must be deterministic fixtures, not live extraction claims",
                "packet",
            )
        )

    _reject_disallowed_payload_keys(packet, "packet", errors)

    candidates = packet.get("requirement_candidates", packet.get("candidates"))
    if not isinstance(candidates, Sequence) or isinstance(candidates, (str, bytes)):
        errors.append(
            ReviewQueueValidationError(
                "missing_requirement_candidates",
                "packet must include a list of requirement candidates",
                "packet.requirement_candidates",
            )
        )
        return errors

    for index, candidate in enumerate(candidates):
        path = f"packet.requirement_candidates[{index}]"
        if not isinstance(candidate, Mapping):
            errors.append(
                ReviewQueueValidationError(
                    "invalid_requirement_candidate",
                    "requirement candidate must be an object",
                    path,
                )
            )
            continue
        _validate_candidate(candidate, path, known_sources, errors)

    return errors


def assert_valid_review_queue_packet(
    packet: Mapping[str, Any], known_source_ids: Iterable[str] | None = None
) -> None:
    """Raise ValueError when a review queue packet is not acceptable."""

    errors = validate_review_queue_packet(packet, known_source_ids)
    if errors:
        detail = "; ".join(f"{error.code} at {error.path}" for error in errors)
        raise ValueError(f"invalid requirement review queue packet: {detail}")


def _validate_candidate(
    candidate: Mapping[str, Any],
    path: str,
    known_sources: set[str],
    errors: list[ReviewQueueValidationError],
) -> None:
    _reject_disallowed_payload_keys(candidate, path, errors)

    citations = candidate.get("citations", candidate.get("source_evidence_ids"))
    if not _has_citation(citations):
        errors.append(
            ReviewQueueValidationError(
                "uncited_requirement_candidate",
                "requirement candidates must include at least one source citation",
                f"{path}.citations",
            )
        )
    else:
        _validate_citations(citations, f"{path}.citations", known_sources, errors)

    review_status = candidate.get("human_review_status")
    formalization_status = str(candidate.get("formalization_status", "")).strip().lower()
    if formalization_status in _FORMALIZED_STATUSES and review_status not in _REVIEW_STATUSES:
        errors.append(
            ReviewQueueValidationError(
                "formalized_without_review_status",
                "formalized requirements must carry an explicit human review status",
                f"{path}.human_review_status",
            )
        )

    reviewer_owner = candidate.get("reviewer_owner", candidate.get("review_owner"))
    if not isinstance(reviewer_owner, str) or not reviewer_owner.strip():
        errors.append(
            ReviewQueueValidationError(
                "missing_reviewer_owner",
                "requirement candidates must name the reviewer owner responsible for disposition",
                f"{path}.reviewer_owner",
            )
        )

    for key in _MUTATION_KEYS:
        if key in candidate and _active_mutation_value(candidate[key]):
            errors.append(
                ReviewQueueValidationError(
                    "active_requirement_mutation_flag",
                    "review queue candidates must not mutate active requirements",
                    f"{path}.{key}",
                )
            )


def _validate_citations(
    citations: Any,
    path: str,
    known_sources: set[str],
    errors: list[ReviewQueueValidationError],
) -> None:
    citation_items: Sequence[Any]
    if isinstance(citations, Sequence) and not isinstance(citations, (str, bytes)):
        citation_items = citations
    else:
        citation_items = [citations]

    for index, citation in enumerate(citation_items):
        citation_path = f"{path}[{index}]"
        if isinstance(citation, str):
            source_id = citation
            url = None
        elif isinstance(citation, Mapping):
            source_id = citation.get("source_id") or citation.get("source")
            url = citation.get("canonical_url") or citation.get("url")
            _reject_disallowed_payload_keys(citation, citation_path, errors)
        else:
            errors.append(
                ReviewQueueValidationError(
                    "invalid_citation",
                    "citation must be a source ID string or citation object",
                    citation_path,
                )
            )
            continue

        if not isinstance(source_id, str) or not source_id.strip():
            errors.append(
                ReviewQueueValidationError(
                    "missing_source_id",
                    "citation must include a source_id",
                    f"{citation_path}.source_id",
                )
            )
        elif source_id not in known_sources:
            errors.append(
                ReviewQueueValidationError(
                    "unknown_source_id",
                    "citation source_id is not present in the packet source registry",
                    f"{citation_path}.source_id",
                )
            )

        if isinstance(url, str) and _private_or_authenticated_url(url):
            errors.append(
                ReviewQueueValidationError(
                    "private_or_authenticated_url",
                    "citations must not point at private, authenticated, tokenized, or local URLs",
                    f"{citation_path}.url",
                )
            )


def _source_ids_from_packet(packet: Mapping[str, Any]) -> set[str]:
    source_ids: set[str] = set()
    registry = packet.get("source_registry", packet.get("sources", []))

    if isinstance(registry, Mapping):
        for key, value in registry.items():
            if isinstance(key, str):
                source_ids.add(key)
            if isinstance(value, Mapping) and isinstance(value.get("source_id"), str):
                source_ids.add(value["source_id"])
    elif isinstance(registry, Sequence) and not isinstance(registry, (str, bytes)):
        for item in registry:
            if isinstance(item, str):
                source_ids.add(item)
            elif isinstance(item, Mapping) and isinstance(item.get("source_id"), str):
                source_ids.add(item["source_id"])

    return source_ids


def _reject_disallowed_payload_keys(
    value: Any,
    path: str,
    errors: list[ReviewQueueValidationError],
) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = str(key)
            normalized = key_text.strip().lower()
            nested_path = f"{path}.{key_text}"
            if normalized in _RAW_TEXT_KEYS and _truthy(nested):
                errors.append(
                    ReviewQueueValidationError(
                        "raw_source_text_present",
                        "review queue packets must cite source spans instead of carrying raw source text",
                        nested_path,
                    )
                )
            if normalized in _DOWNLOADED_DOCUMENT_KEYS and _truthy(nested):
                errors.append(
                    ReviewQueueValidationError(
                        "downloaded_document_reference",
                        "review queue packets must not reference raw downloaded documents or local archive files",
                        nested_path,
                    )
                )
            if normalized in _LIVE_EXTRACTION_KEYS and _truthy(nested):
                errors.append(
                    ReviewQueueValidationError(
                        "live_extraction_claim",
                        "review queue packets must not carry live extraction session claims",
                        nested_path,
                    )
                )
            if isinstance(nested, str) and _private_or_authenticated_url(nested):
                errors.append(
                    ReviewQueueValidationError(
                        "private_or_authenticated_url",
                        "review queue packets must not include private, authenticated, tokenized, or local URLs",
                        nested_path,
                    )
                )
            _reject_disallowed_payload_keys(nested, nested_path, errors)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, item in enumerate(value):
            _reject_disallowed_payload_keys(item, f"{path}[{index}]", errors)


def _has_citation(citations: Any) -> bool:
    if citations is None:
        return False
    if isinstance(citations, str):
        return bool(citations.strip())
    if isinstance(citations, Sequence) and not isinstance(citations, (str, bytes)):
        return any(_has_citation(item) for item in citations)
    if isinstance(citations, Mapping):
        return bool(citations.get("source_id") or citations.get("source"))
    return False


def _private_or_authenticated_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme and parsed.scheme not in {"http", "https"}:
        return True
    hostname = (parsed.hostname or "").lower()
    if hostname in {"localhost", "127.0.0.1", "0.0.0.0"} or hostname.endswith(".local"):
        return True
    if parsed.username or parsed.password:
        return True

    path_parts = [part.lower() for part in parsed.path.split("/") if part]
    if any(part in _PRIVATE_URL_MARKERS for part in path_parts):
        return True

    query_keys = {key.lower() for key, _value in parse_qsl(parsed.query, keep_blank_values=True)}
    if query_keys & _PRIVATE_QUERY_KEYS:
        return True

    return False


def _active_mutation_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() not in {"", "false", "none", "no", "inactive"}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return any(_active_mutation_value(item) for item in value)
    if isinstance(value, Mapping):
        return any(_active_mutation_value(item) for item in value.values())
    return value is not None


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return bool(value)
    if isinstance(value, Mapping):
        return bool(value)
    return value is not None
