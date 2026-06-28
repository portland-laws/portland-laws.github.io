"""Validate post-recrawl invalidation decision queues.

The queue consumed after a recrawl is allowed to describe review decisions only.
It must not contain private evidence, raw crawl content, downloaded local files,
or any instruction that directly promotes data to production.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import PurePath
from typing import Any

_PRIVATE_URL_MARKERS = (
    "localhost",
    "127.0.0.1",
    "devhub.portlandoregon.gov",
    "session",
    "token=",
    "auth=",
)

_AUTHENTICATED_MARKERS = {
    "private",
    "authenticated",
    "auth_required",
    "requires_auth",
    "devhub_authenticated",
}

_RAW_BODY_FIELDS = {
    "raw_body",
    "raw_html",
    "raw_text",
    "body_excerpt",
    "raw_body_excerpt",
    "document_body_excerpt",
    "page_body_excerpt",
}

_DOWNLOADED_PATH_FIELDS = {
    "downloaded_path",
    "download_path",
    "local_path",
    "file_path",
    "filesystem_path",
    "document_path",
    "downloaded_document_path",
}

_PRODUCTION_FIELDS = {
    "promote_to_production",
    "production_promotion",
    "direct_production_promotion",
}

_POLICY_PREFIXES = ("PPD-", "POLICY-", "RECrawl-", "RECRAWL-")


@dataclass(frozen=True)
class QueueValidationError:
    """Single validation failure for a queue item."""

    path: str
    message: str


def validate_decision_queue(queue: Any) -> list[QueueValidationError]:
    """Return validation errors for a post-recrawl invalidation queue."""

    errors: list[QueueValidationError] = []
    decisions = _decisions_from_queue(queue)
    if decisions is None:
        return [QueueValidationError("$", "queue must be a list or an object with a decisions list")]

    for index, decision in enumerate(decisions):
        path = f"$.decisions[{index}]"
        if not isinstance(decision, Mapping):
            errors.append(QueueValidationError(path, "decision must be an object"))
            continue
        _validate_decision(decision, path, errors)

    return errors


def assert_valid_decision_queue(queue: Any) -> None:
    """Raise ValueError when the queue contains rejected decision content."""

    errors = validate_decision_queue(queue)
    if errors:
        detail = "; ".join(f"{error.path}: {error.message}" for error in errors)
        raise ValueError(f"invalid post-recrawl invalidation decision queue: {detail}")


def _decisions_from_queue(queue: Any) -> Sequence[Any] | None:
    if isinstance(queue, list):
        return queue
    if isinstance(queue, Mapping) and isinstance(queue.get("decisions"), list):
        return queue["decisions"]
    return None


def _validate_decision(decision: Mapping[str, Any], path: str, errors: list[QueueValidationError]) -> None:
    review_link = _first_present(decision, ("metadata_review_link", "metadataReviewLink", "review_link"))
    if not _is_non_empty_string(review_link):
        errors.append(QueueValidationError(path, "missing metadata-review link"))

    if _has_risk_decision(decision) and not _has_citation(decision):
        errors.append(QueueValidationError(path, "risk decision must include at least one citation"))

    if _is_skipped(decision) and not _has_policy_code(decision):
        errors.append(QueueValidationError(path, "skipped decisions must include a policy code"))

    if _directly_promotes_to_production(decision):
        errors.append(QueueValidationError(path, "direct production promotion is not allowed"))

    _scan_for_forbidden_content(decision, path, errors)


def _scan_for_forbidden_content(value: Any, path: str, errors: list[QueueValidationError]) -> None:
    if isinstance(value, Mapping):
        if _evidence_is_private_or_authenticated(value):
            errors.append(QueueValidationError(path, "private or authenticated evidence is not allowed"))

        for key, child in value.items():
            child_path = f"{path}.{key}"
            normalized = str(key).lower()
            if normalized in _RAW_BODY_FIELDS and _is_non_empty_string(child):
                errors.append(QueueValidationError(child_path, "raw body excerpts are not allowed"))
            if normalized in _DOWNLOADED_PATH_FIELDS and _looks_like_downloaded_path(child):
                errors.append(QueueValidationError(child_path, "downloaded document paths are not allowed"))
            _scan_for_forbidden_content(child, child_path, errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _scan_for_forbidden_content(child, f"{path}[{index}]", errors)


def _first_present(item: Mapping[str, Any], keys: Sequence[str]) -> Any:
    for key in keys:
        if key in item:
            return item[key]
    return None


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _has_risk_decision(decision: Mapping[str, Any]) -> bool:
    for key in ("risk_decision", "riskDecision", "risk", "risk_level"):
        value = decision.get(key)
        if _is_non_empty_string(value) or isinstance(value, Mapping):
            return True
    return False


def _has_citation(decision: Mapping[str, Any]) -> bool:
    for key in ("citations", "citation_links", "source_citations", "cited_evidence"):
        value = decision.get(key)
        if isinstance(value, list) and any(_is_non_empty_string(item) or isinstance(item, Mapping) for item in value):
            return True
        if _is_non_empty_string(value):
            return True
    evidence = decision.get("evidence")
    if isinstance(evidence, list):
        return any(isinstance(item, Mapping) and _is_non_empty_string(item.get("citation")) for item in evidence)
    return False


def _is_skipped(decision: Mapping[str, Any]) -> bool:
    status = str(decision.get("status", "")).lower()
    action = str(decision.get("action", "")).lower()
    return "skip" in status or "skip" in action or _is_non_empty_string(decision.get("skipped_reason"))


def _has_policy_code(decision: Mapping[str, Any]) -> bool:
    values = []
    for key in ("policy_code", "policy_codes", "policyCode", "skip_policy_code"):
        value = decision.get(key)
        if isinstance(value, list):
            values.extend(str(item) for item in value)
        elif value is not None:
            values.append(str(value))
    return any(item.startswith(_POLICY_PREFIXES) for item in values)


def _directly_promotes_to_production(decision: Mapping[str, Any]) -> bool:
    for key in _PRODUCTION_FIELDS:
        if decision.get(key) is True:
            return True
    target = str(decision.get("promotion_target", decision.get("target", ""))).lower()
    action = str(decision.get("action", "")).lower()
    return target == "production" or action in {"promote_to_production", "production_promote"}


def _evidence_is_private_or_authenticated(item: Mapping[str, Any]) -> bool:
    source_type = str(item.get("source_type", item.get("access", ""))).lower()
    if source_type in _AUTHENTICATED_MARKERS:
        return True
    if item.get("private") is True or item.get("authenticated") is True or item.get("auth_required") is True:
        return True
    url = str(item.get("url", item.get("href", ""))).lower()
    return bool(url) and any(marker in url for marker in _PRIVATE_URL_MARKERS)


def _looks_like_downloaded_path(value: Any) -> bool:
    if not _is_non_empty_string(value):
        return False
    text = value.strip()
    if text.startswith(("http://", "https://")):
        return False
    path = PurePath(text)
    return path.is_absolute() or len(path.parts) > 1 or text.startswith(("./", "../"))
