"""Validation for PP&D release-blocker burn-down queues.

The validator is intentionally side-effect free. It accepts plain dictionaries so
it can be used by daemon task-board checks, fixtures, or future JSON manifests
without coupling the queue format to a shared contract prematurely.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence


OPEN_STATUSES = frozenset(
    {
        "blocked",
        "in_progress",
        "needs_reconciliation",
        "open",
        "pending",
        "todo",
        "unresolved",
    }
)

CLOSED_STATUSES = frozenset({"closed", "done", "reconciled", "resolved"})

PRODUCTION_READY_LABELS = frozenset(
    {
        "production-ready",
        "production_ready",
        "release-ready",
        "release_ready",
        "ready-for-production",
        "ready_for_production",
    }
)

PRIORITY_VALUES_REQUIRING_CITATION = frozenset(
    {
        "blocker",
        "critical",
        "high",
        "p0",
        "p1",
        "release-blocker",
        "release_blocker",
    }
)

PRIVATE_ARTIFACT_MARKERS = (
    ".auth/",
    ".devhub/",
    ".session",
    ".storage_state",
    "auth-state",
    "browser-state",
    "cookie",
    "cookies",
    "credential",
    "devhub-session",
    "har",
    "localstorage",
    "mfa",
    "password",
    "playwright-report",
    "private-upload",
    "screenshot",
    "session-state",
    "storage-state",
    "trace.zip",
    "traces/",
)

RAW_CRAWL_MARKERS = (
    "raw-crawl",
    "raw_crawl",
    "crawl/raw",
    "crawler/raw",
    "raw-response",
    "raw_response",
    "warc/",
    ".warc",
    "response-body",
    "html-dump",
    "downloaded-documents/",
    "downloads/raw",
)

ENABLEMENT_TERMS = (
    "enable payment",
    "enable payments",
    "enter payment",
    "make payment",
    "pay fee",
    "payment execution",
    "submit payment",
    "enable upload",
    "upload correction",
    "upload document",
    "upload file",
    "official upload",
    "enable submission",
    "final submission",
    "submit application",
    "submit permit",
    "submit request",
    "enable scheduling",
    "schedule inspection",
    "inspection scheduling",
    "enable cancellation",
    "cancel inspection",
    "cancel permit",
    "withdraw permit",
    "enable certification",
    "certify acknowledgement",
    "certify application",
    "certification enablement",
)


@dataclass(frozen=True)
class QueueViolation:
    """A deterministic validation failure for a burn-down queue item."""

    code: str
    item_id: str
    message: str


@dataclass(frozen=True)
class QueueValidationReport:
    """Validation result returned by release-blocker burn-down checks."""

    ok: bool
    violations: tuple[QueueViolation, ...]

    def require_ok(self) -> None:
        if self.ok:
            return
        rendered = "; ".join(
            f"{violation.item_id}:{violation.code}" for violation in self.violations
        )
        raise ValueError(f"release-blocker burn-down queue rejected: {rendered}")


def validate_release_blocker_burndown_queue(
    queue: Mapping[str, Any] | Sequence[Mapping[str, Any]],
) -> QueueValidationReport:
    """Validate a PP&D release-blocker burn-down queue.

    The accepted input is either a queue mapping with an ``items`` list or a bare
    sequence of item mappings. The function never reads files, follows links, or
    performs network work.
    """

    violations: list[QueueViolation] = []
    for index, item in enumerate(_iter_items(queue)):
        item_id = str(item.get("id") or item.get("task_id") or f"item-{index + 1}")
        labels = _normalized_values(item.get("labels"), item.get("tags"))
        status = _normalized_status(item)
        text_values = tuple(_flatten_text(item))

        if _is_release_blocker(item, labels) and not _has_reconciliation_link(item):
            violations.append(
                QueueViolation(
                    code="missing_reconciliation_link",
                    item_id=item_id,
                    message="Release-blocker queue items must cite a reconciliation link.",
                )
            )

        if _priority_requires_citation(item) and not _has_priority_citation(item):
            violations.append(
                QueueViolation(
                    code="uncited_blocker_priority",
                    item_id=item_id,
                    message="Blocker priority must be backed by a citation or source evidence id.",
                )
            )

        private_reference = _first_marker_match(text_values, PRIVATE_ARTIFACT_MARKERS)
        if private_reference is not None:
            violations.append(
                QueueViolation(
                    code="private_or_session_artifact_reference",
                    item_id=item_id,
                    message=f"Queue item references private/session artifact marker: {private_reference}.",
                )
            )

        raw_reference = _first_marker_match(text_values, RAW_CRAWL_MARKERS)
        if raw_reference is not None:
            violations.append(
                QueueViolation(
                    code="raw_crawl_output_reference",
                    item_id=item_id,
                    message=f"Queue item references raw crawl output marker: {raw_reference}.",
                )
            )

        if labels.intersection(PRODUCTION_READY_LABELS) and status in OPEN_STATUSES:
            violations.append(
                QueueViolation(
                    code="production_ready_with_open_blockers",
                    item_id=item_id,
                    message="Production-ready labels are not allowed while blockers remain open.",
                )
            )

        enablement = _first_marker_match(text_values, ENABLEMENT_TERMS)
        if enablement is not None:
            violations.append(
                QueueViolation(
                    code="consequential_action_enablement",
                    item_id=item_id,
                    message=f"Queue item enables a prohibited PP&D action: {enablement}.",
                )
            )

    return QueueValidationReport(ok=not violations, violations=tuple(violations))


def assert_release_blocker_burndown_queue_safe(
    queue: Mapping[str, Any] | Sequence[Mapping[str, Any]],
) -> None:
    """Raise ``ValueError`` when a release-blocker burn-down queue is unsafe."""

    validate_release_blocker_burndown_queue(queue).require_ok()


def _iter_items(
    queue: Mapping[str, Any] | Sequence[Mapping[str, Any]],
) -> Iterable[Mapping[str, Any]]:
    if isinstance(queue, Mapping):
        items = queue.get("items", ())
    else:
        items = queue
    if not isinstance(items, Sequence) or isinstance(items, (str, bytes)):
        return ()
    return (item for item in items if isinstance(item, Mapping))


def _normalized_status(item: Mapping[str, Any]) -> str:
    raw_status = (
        item.get("status")
        or item.get("blocker_status")
        or item.get("resolution_status")
        or "open"
    )
    status = _normalize_token(raw_status)
    if status in CLOSED_STATUSES:
        return status
    return status or "open"


def _is_release_blocker(item: Mapping[str, Any], labels: set[str]) -> bool:
    values = _normalized_values(
        item.get("type"),
        item.get("kind"),
        item.get("category"),
        item.get("priority"),
        item.get("severity"),
    )
    return bool(
        {"release-blocker", "release_blocker", "blocker"}.intersection(labels | values)
    )


def _priority_requires_citation(item: Mapping[str, Any]) -> bool:
    priority_values = _normalized_values(item.get("priority"), item.get("severity"))
    labels = _normalized_values(item.get("labels"), item.get("tags"))
    return bool(
        priority_values.intersection(PRIORITY_VALUES_REQUIRING_CITATION)
        or labels.intersection({"priority:blocker", "priority:critical", "priority:high"})
    )


def _has_reconciliation_link(item: Mapping[str, Any]) -> bool:
    return _has_any_non_empty(
        item,
        (
            "reconciliation_link",
            "reconciliation_links",
            "reconciled_by",
            "reconciliation_evidence",
        ),
    )


def _has_priority_citation(item: Mapping[str, Any]) -> bool:
    return _has_any_non_empty(
        item,
        (
            "priority_citation",
            "priority_citations",
            "priority_source_evidence_ids",
            "source_evidence_ids",
            "citations",
            "evidence_ids",
        ),
    )


def _has_any_non_empty(item: Mapping[str, Any], keys: Iterable[str]) -> bool:
    for key in keys:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return True
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            if any(str(entry).strip() for entry in value):
                return True
    return False


def _normalized_values(*values: Any) -> set[str]:
    normalized: set[str] = set()
    for value in values:
        if value is None:
            continue
        if isinstance(value, str):
            token = _normalize_token(value)
            if token:
                normalized.add(token)
            continue
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            for entry in value:
                token = _normalize_token(entry)
                if token:
                    normalized.add(token)
    return normalized


def _normalize_token(value: Any) -> str:
    return str(value).strip().lower().replace(" ", "_")


def _flatten_text(value: Any) -> Iterable[str]:
    if value is None:
        return
    if isinstance(value, str):
        yield value.lower()
        return
    if isinstance(value, Mapping):
        for nested_value in value.values():
            yield from _flatten_text(nested_value)
        return
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        for nested_value in value:
            yield from _flatten_text(nested_value)
        return
    yield str(value).lower()


def _first_marker_match(values: Iterable[str], markers: Sequence[str]) -> str | None:
    for value in values:
        normalized_value = value.replace("_", "-")
        for marker in markers:
            normalized_marker = marker.lower().replace("_", "-")
            if normalized_marker in normalized_value:
                return marker
    return None
