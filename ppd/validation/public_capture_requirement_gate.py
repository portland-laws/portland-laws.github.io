"""Readiness validation for public-capture requirement extraction."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

DEFAULT_MIN_EXTRACTION_CONFIDENCE = 0.75
DEFAULT_MAX_SOURCE_AGE_DAYS = 45


@dataclass(frozen=True)
class RequirementGateIssue:
    """A single reason an assembly is not ready for requirement extraction."""

    code: str
    message: str


class RequirementGateError(ValueError):
    """Raised when requirement extraction is attempted on an unready assembly."""

    def __init__(self, issues: Sequence[RequirementGateIssue]) -> None:
        self.issues = tuple(issues)
        codes = ", ".join(issue.code for issue in self.issues)
        super().__init__(f"public-capture assembly is not ready for requirement extraction: {codes}")


def validate_public_capture_requirement_readiness(
    assembly: Mapping[str, Any],
    *,
    now: datetime | None = None,
    min_confidence: float = DEFAULT_MIN_EXTRACTION_CONFIDENCE,
    max_source_age_days: int = DEFAULT_MAX_SOURCE_AGE_DAYS,
) -> list[RequirementGateIssue]:
    """Return readiness issues that must block requirement extraction."""

    checked_at = _normalize_now(now)
    issues: list[RequirementGateIssue] = []

    if not _non_empty_sequence(_lookup(assembly, "citation_spans", "citations.spans")):
        issues.append(RequirementGateIssue("missing_citation_spans", "citation spans are required"))

    section_order = _lookup(assembly, "section_order", "sections.order")
    if not _valid_section_order(section_order):
        issues.append(RequirementGateIssue("missing_or_invalid_section_order", "section order must be a non-empty ordered list"))

    confidence = _lookup(assembly, "extraction_confidence", "confidence", "requirements.extraction_confidence")
    if confidence is None:
        issues.append(RequirementGateIssue("missing_extraction_confidence", "extraction confidence is required"))
    elif not _meets_confidence(confidence, min_confidence):
        issues.append(RequirementGateIssue("low_extraction_confidence", "extraction confidence is below the required threshold"))

    content_hash = _lookup(assembly, "content_hash", "source.content_hash", "normalized.content_hash")
    if not isinstance(content_hash, str) or not content_hash.strip():
        issues.append(RequirementGateIssue("missing_content_hash", "content hash is required"))

    captured_at = _lookup(assembly, "source_captured_at", "captured_at", "source.captured_at")
    if captured_at is None:
        issues.append(RequirementGateIssue("missing_source_freshness", "source capture timestamp is required"))
    else:
        source_time = _parse_datetime(captured_at)
        if source_time is None:
            issues.append(RequirementGateIssue("invalid_source_freshness", "source capture timestamp must be ISO-8601"))
        elif (checked_at - source_time).days > max_source_age_days:
            issues.append(RequirementGateIssue("stale_source_freshness", "source capture timestamp is stale"))

    owning_surface = _lookup(assembly, "owning_surface", "surface", "metadata.owning_surface")
    if not _valid_owning_surface(owning_surface):
        issues.append(RequirementGateIssue("missing_owning_surface", "owning surface metadata is required"))

    return issues


def require_public_capture_requirement_readiness(
    assembly: Mapping[str, Any],
    *,
    now: datetime | None = None,
    min_confidence: float = DEFAULT_MIN_EXTRACTION_CONFIDENCE,
    max_source_age_days: int = DEFAULT_MAX_SOURCE_AGE_DAYS,
) -> None:
    """Raise when a normalized public-capture assembly must not be extracted."""

    issues = validate_public_capture_requirement_readiness(
        assembly,
        now=now,
        min_confidence=min_confidence,
        max_source_age_days=max_source_age_days,
    )
    if issues:
        raise RequirementGateError(issues)


def _lookup(mapping: Mapping[str, Any], *paths: str) -> Any:
    for path in paths:
        current: Any = mapping
        for part in path.split("."):
            if not isinstance(current, Mapping) or part not in current:
                current = None
                break
            current = current[part]
        if current is not None:
            return current
    return None


def _non_empty_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)) and len(value) > 0


def _valid_section_order(value: Any) -> bool:
    if not _non_empty_sequence(value):
        return False
    return all(isinstance(item, (str, int)) and str(item).strip() for item in value)


def _meets_confidence(value: Any, minimum: float) -> bool:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return False
    return confidence >= minimum


def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str) and value.strip():
        raw = value.strip()
        if raw.endswith("Z"):
            raw = f"{raw[:-1]}+00:00"
        try:
            parsed = datetime.fromisoformat(raw)
        except ValueError:
            return None
    else:
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _normalize_now(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _valid_owning_surface(value: Any) -> bool:
    if not isinstance(value, Mapping):
        return False
    surface_id = value.get("id") or value.get("surface_id") or value.get("name")
    surface_kind = value.get("kind") or value.get("type")
    return isinstance(surface_id, str) and bool(surface_id.strip()) and isinstance(surface_kind, str) and bool(surface_kind.strip())
