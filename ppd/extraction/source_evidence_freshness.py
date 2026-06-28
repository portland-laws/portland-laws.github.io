"""Source-evidence freshness checks for PP&D document-preparation guidance.

The checks in this module are intentionally deterministic. They do not crawl or
fetch sources; callers provide captured source evidence and a fixed as-of date.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, Iterable, Mapping, Sequence

REQUIRED_DOCUMENT_PREPARATION_RULES = ("file_naming", "single_pdf")
DEFAULT_MAX_EVIDENCE_AGE_DAYS = 45


@dataclass(frozen=True)
class SourceEvidence:
    """Captured public-source evidence for one or more PP&D rules."""

    evidence_id: str
    source_name: str
    canonical_url: str
    captured_at: date | None
    supports_rules: tuple[str, ...]

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "SourceEvidence":
        captured_at = _parse_date(value.get("captured_at"))
        supports_rules = tuple(str(rule) for rule in value.get("supports_rules", ()))
        return cls(
            evidence_id=str(value.get("evidence_id", "")),
            source_name=str(value.get("source_name", "")),
            canonical_url=str(value.get("canonical_url", "")),
            captured_at=captured_at,
            supports_rules=supports_rules,
        )


@dataclass(frozen=True)
class RuleFreshnessFinding:
    """Freshness status for a required document-preparation rule."""

    rule: str
    status: str
    evidence_ids: tuple[str, ...]
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule": self.rule,
            "status": self.status,
            "evidence_ids": list(self.evidence_ids),
            "reason": self.reason,
        }


@dataclass(frozen=True)
class DocumentPreparationReadiness:
    """Readiness decision for a document-preparation recommendation."""

    ready: bool
    status: str
    findings: tuple[RuleFreshnessFinding, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ready": self.ready,
            "status": self.status,
            "findings": [finding.to_dict() for finding in self.findings],
        }


def evaluate_document_preparation_source_evidence(
    evidence: Iterable[SourceEvidence | Mapping[str, Any]],
    *,
    as_of: date | str,
    required_rules: Sequence[str] = REQUIRED_DOCUMENT_PREPARATION_RULES,
    max_age_days: int = DEFAULT_MAX_EVIDENCE_AGE_DAYS,
) -> DocumentPreparationReadiness:
    """Evaluate whether required document-preparation rules have fresh evidence.

    A recommendation is ready only when every required rule has at least one
    captured source-evidence item and every evidence item supporting that rule is
    within the configured age window.
    """

    as_of_date = _parse_required_date(as_of, "as_of")
    evidence_items = tuple(_coerce_evidence(item) for item in evidence)
    findings: list[RuleFreshnessFinding] = []

    for rule in required_rules:
        supporting = tuple(item for item in evidence_items if rule in item.supports_rules)
        if not supporting:
            findings.append(
                RuleFreshnessFinding(
                    rule=rule,
                    status="missing",
                    evidence_ids=(),
                    reason="No source evidence supports this required document-preparation rule.",
                )
            )
            continue

        missing_capture_dates = tuple(item for item in supporting if item.captured_at is None)
        if missing_capture_dates:
            findings.append(
                RuleFreshnessFinding(
                    rule=rule,
                    status="stale",
                    evidence_ids=tuple(item.evidence_id for item in missing_capture_dates),
                    reason="Source evidence is missing a capture date and cannot prove freshness.",
                )
            )
            continue

        stale = tuple(
            item
            for item in supporting
            if item.captured_at is not None
            and _age_days(item.captured_at, as_of_date) > max_age_days
        )
        if stale:
            findings.append(
                RuleFreshnessFinding(
                    rule=rule,
                    status="stale",
                    evidence_ids=tuple(item.evidence_id for item in stale),
                    reason="Source evidence is older than the allowed freshness window.",
                )
            )
            continue

        findings.append(
            RuleFreshnessFinding(
                rule=rule,
                status="fresh",
                evidence_ids=tuple(item.evidence_id for item in supporting),
                reason="Required rule is supported by fresh source evidence.",
            )
        )

    ready = all(finding.status == "fresh" for finding in findings)
    return DocumentPreparationReadiness(
        ready=ready,
        status="ready" if ready else "blocked_by_source_evidence",
        findings=tuple(findings),
    )


def evaluate_fixture_case(case: Mapping[str, Any]) -> dict[str, Any]:
    """Evaluate one JSON fixture case and return a serializable decision."""

    result = evaluate_document_preparation_source_evidence(
        case.get("source_evidence", ()),
        as_of=case["as_of"],
        required_rules=tuple(case.get("required_rules", REQUIRED_DOCUMENT_PREPARATION_RULES)),
        max_age_days=int(case.get("max_age_days", DEFAULT_MAX_EVIDENCE_AGE_DAYS)),
    )
    return result.to_dict()


def _coerce_evidence(value: SourceEvidence | Mapping[str, Any]) -> SourceEvidence:
    if isinstance(value, SourceEvidence):
        return value
    return SourceEvidence.from_mapping(value)


def _age_days(captured_at: date, as_of: date) -> int:
    return (as_of - captured_at).days


def _parse_required_date(value: date | str, field_name: str) -> date:
    parsed = _parse_date(value)
    if parsed is None:
        raise ValueError(f"{field_name} must be an ISO-8601 date")
    return parsed


def _parse_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).date() if value.tzinfo else value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        normalized = value.strip()
        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"
        try:
            return datetime.fromisoformat(normalized).date()
        except ValueError:
            return date.fromisoformat(normalized[:10])
    raise TypeError(f"Unsupported date value: {value!r}")
