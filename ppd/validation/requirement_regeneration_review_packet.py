"""Validation for requirement regeneration review packets.

The validator is intentionally data-shape tolerant because review packets are assembled
by several PP&D workflows. It rejects unsafe classes of changes without requiring a
shared contract rewrite.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable, Mapping


_CONFIDENCE_ORDER = {
    "unknown": 0,
    "low": 1,
    "medium": 2,
    "moderate": 2,
    "high": 3,
    "verified": 4,
}

_PRIVATE_KEY_RE = re.compile(
    r"(password|passwd|secret|token|api[_-]?key|authorization|cookie|session|ssn|dob|date[_-]?of[_-]?birth|private)",
    re.IGNORECASE,
)
_PRIVATE_VALUE_RE = re.compile(
    r"(Bearer\s+[A-Za-z0-9._~+/=-]{12,}|sk-[A-Za-z0-9]{12,}|\b\d{3}-\d{2}-\d{4}\b|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})"
)
_RAW_ARTIFACT_KEYS = {
    "raw_html",
    "raw_text",
    "raw_response",
    "screenshot",
    "screenshots",
    "trace",
    "traces",
    "har",
    "crawl_log",
    "crawl_logs",
    "downloaded_document",
    "downloaded_documents",
    "raw_crawl_artifact",
    "raw_crawl_artifacts",
}
_PRODUCTION_WORDS = {"production", "prod", "live"}
_REPLACE_WORDS = {"replace", "replacement", "overwrite", "direct_replace"}


@dataclass(frozen=True)
class PacketValidationError:
    code: str
    message: str
    path: str


@dataclass(frozen=True)
class PacketValidationResult:
    ok: bool
    errors: tuple[PacketValidationError, ...]

    def raise_for_errors(self) -> None:
        if self.errors:
            detail = "; ".join(f"{error.code} at {error.path}: {error.message}" for error in self.errors)
            raise ValueError(detail)


def validate_requirement_regeneration_review_packet(packet: Mapping[str, Any]) -> PacketValidationResult:
    """Return validation errors for unsafe requirement regeneration review packets."""

    errors: list[PacketValidationError] = []

    if not _has_human_review_route(packet):
        errors.append(
            PacketValidationError(
                "missing_human_review_routing",
                "packet must route regenerated requirements to a human reviewer",
                "human_review",
            )
        )

    for path, key, value in _walk(packet):
        lowered_key = str(key).lower()
        if lowered_key in _RAW_ARTIFACT_KEYS:
            errors.append(
                PacketValidationError(
                    "raw_crawl_artifact",
                    "review packets must reference sanitized evidence, not embed raw crawl artifacts",
                    path,
                )
            )
        if _PRIVATE_KEY_RE.search(str(key)) or (isinstance(value, str) and _PRIVATE_VALUE_RE.search(value)):
            errors.append(
                PacketValidationError(
                    "private_value",
                    "review packets must not contain private values, credentials, sessions, or direct personal identifiers",
                    path,
                )
            )

    for index, change in enumerate(_iter_requirement_changes(packet)):
        change_path = f"requirement_changes[{index}]"
        if not _has_citation(change):
            errors.append(
                PacketValidationError(
                    "uncited_requirement_change",
                    "each requirement change must include at least one citation or sanitized evidence reference",
                    change_path,
                )
            )
        if _is_confidence_escalation(change) and not _has_confidence_support(change):
            errors.append(
                PacketValidationError(
                    "unsupported_confidence_escalation",
                    "confidence increases require supporting evidence and human-review routing",
                    change_path,
                )
            )
        if _is_direct_production_guardrail_replacement(change):
            errors.append(
                PacketValidationError(
                    "direct_production_guardrail_replacement",
                    "production guardrails may not be directly replaced by regeneration review packets",
                    change_path,
                )
            )

    return PacketValidationResult(ok=not errors, errors=tuple(errors))


def assert_valid_requirement_regeneration_review_packet(packet: Mapping[str, Any]) -> None:
    validate_requirement_regeneration_review_packet(packet).raise_for_errors()


def _iter_requirement_changes(packet: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
    for field in ("requirement_changes", "changes", "requirements"):
        value = packet.get(field)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, Mapping):
                    yield item


def _has_citation(change: Mapping[str, Any]) -> bool:
    for field in ("citations", "citation", "evidence", "evidence_refs", "source_refs", "references"):
        value = change.get(field)
        if isinstance(value, str) and value.strip():
            return True
        if isinstance(value, list) and any(bool(item) for item in value):
            return True
    return False


def _has_confidence_support(change: Mapping[str, Any]) -> bool:
    if not _has_citation(change):
        return False
    for field in ("confidence_support", "confidence_evidence", "review_notes", "rationale"):
        value = change.get(field)
        if isinstance(value, str) and value.strip():
            return True
        if isinstance(value, list) and any(bool(item) for item in value):
            return True
    return False


def _is_confidence_escalation(change: Mapping[str, Any]) -> bool:
    old = _confidence_rank(change.get("old_confidence", change.get("previous_confidence")))
    new = _confidence_rank(change.get("new_confidence", change.get("confidence")))
    return old is not None and new is not None and new > old


def _confidence_rank(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    return _CONFIDENCE_ORDER.get(str(value).strip().lower())


def _has_human_review_route(packet: Mapping[str, Any]) -> bool:
    route = packet.get("human_review") or packet.get("review_route") or packet.get("routing")
    if isinstance(route, Mapping):
        reviewer = route.get("reviewer") or route.get("queue") or route.get("owner")
        required = route.get("required", True)
        return bool(reviewer) and required is not False
    if isinstance(route, str):
        return bool(route.strip())
    return False


def _is_direct_production_guardrail_replacement(change: Mapping[str, Any]) -> bool:
    target = str(change.get("target", change.get("scope", ""))).strip().lower()
    action = str(change.get("action", change.get("operation", ""))).strip().lower()
    kind = str(change.get("kind", change.get("type", ""))).strip().lower()
    guardrail = "guardrail" in target or "guardrail" in kind
    production = any(word in target for word in _PRODUCTION_WORDS) or any(word in kind for word in _PRODUCTION_WORDS)
    replacement = action in _REPLACE_WORDS or any(word in action for word in _REPLACE_WORDS)
    return guardrail and production and replacement


def _walk(value: Any, path: str = "$") -> Iterable[tuple[str, str, Any]]:
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            yield child_path, str(key), child
            yield from _walk(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk(child, f"{path}[{index}]")
