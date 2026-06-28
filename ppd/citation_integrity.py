"""Fixture-first citation integrity validation for PP&D artifacts.

This module intentionally validates local JSON-like fixtures only. It does not fetch,
crawl, or infer evidence from live sources.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

CHECKED_SECTIONS = (
    "requirements",
    "process_model_rules",
    "guardrail_predicates",
    "next_safe_action_explanations",
)


@dataclass(frozen=True)
class CitationIssue:
    """A deterministic validation issue for a cited PP&D artifact."""

    path: str
    message: str


def validate_citation_integrity(document: Mapping[str, Any]) -> list[CitationIssue]:
    """Validate that every checked artifact cites committed synthetic evidence.

    Expected input is a local fixture-shaped mapping with an ``evidence`` list and
    the four checked artifact lists named in ``CHECKED_SECTIONS``. Each artifact
    must contain at least one citation with an ``evidence_id`` and ``span_id``.
    Evidence records must be marked ``synthetic`` and ``committed`` and expose
    matching span IDs.
    """

    issues: list[CitationIssue] = []
    evidence_index = _index_evidence(document.get("evidence"), issues)

    for section in CHECKED_SECTIONS:
        entries = document.get(section)
        if not isinstance(entries, list):
            issues.append(CitationIssue(section, "section must be a list"))
            continue

        for entry_index, entry in enumerate(entries):
            entry_path = f"{section}[{entry_index}]"
            if not isinstance(entry, Mapping):
                issues.append(CitationIssue(entry_path, "entry must be an object"))
                continue

            entry_id = entry.get("id")
            if not isinstance(entry_id, str) or not entry_id.strip():
                issues.append(CitationIssue(f"{entry_path}.id", "id must be a non-empty string"))

            citations = entry.get("citations")
            if not isinstance(citations, list) or not citations:
                issues.append(CitationIssue(f"{entry_path}.citations", "at least one citation is required"))
                continue

            for citation_index, citation in enumerate(citations):
                citation_path = f"{entry_path}.citations[{citation_index}]"
                _validate_citation(citation, citation_path, evidence_index, issues)

    return issues


def assert_citation_integrity(document: Mapping[str, Any]) -> None:
    """Raise ``AssertionError`` with stable text when citation validation fails."""

    issues = validate_citation_integrity(document)
    if issues:
        formatted = "; ".join(f"{issue.path}: {issue.message}" for issue in issues)
        raise AssertionError(f"citation integrity validation failed: {formatted}")


def _index_evidence(raw_evidence: Any, issues: list[CitationIssue]) -> dict[str, set[str]]:
    if not isinstance(raw_evidence, list):
        issues.append(CitationIssue("evidence", "evidence must be a list"))
        return {}

    evidence_index: dict[str, set[str]] = {}
    for evidence_position, evidence in enumerate(raw_evidence):
        evidence_path = f"evidence[{evidence_position}]"
        if not isinstance(evidence, Mapping):
            issues.append(CitationIssue(evidence_path, "evidence entry must be an object"))
            continue

        evidence_id = evidence.get("evidence_id")
        if not isinstance(evidence_id, str) or not evidence_id.strip():
            issues.append(CitationIssue(f"{evidence_path}.evidence_id", "evidence_id must be a non-empty string"))
            continue

        if evidence_id in evidence_index:
            issues.append(CitationIssue(f"{evidence_path}.evidence_id", "duplicate evidence_id"))
            continue

        if evidence.get("synthetic") is not True:
            issues.append(CitationIssue(f"{evidence_path}.synthetic", "evidence must be marked synthetic"))

        if evidence.get("committed") is not True:
            issues.append(CitationIssue(f"{evidence_path}.committed", "evidence must be marked committed"))

        spans = evidence.get("spans")
        if not isinstance(spans, list) or not spans:
            issues.append(CitationIssue(f"{evidence_path}.spans", "at least one span is required"))
            evidence_index[evidence_id] = set()
            continue

        span_ids: set[str] = set()
        for span_position, span in enumerate(spans):
            span_path = f"{evidence_path}.spans[{span_position}]"
            if not isinstance(span, Mapping):
                issues.append(CitationIssue(span_path, "span must be an object"))
                continue
            span_id = span.get("span_id")
            if not isinstance(span_id, str) or not span_id.strip():
                issues.append(CitationIssue(f"{span_path}.span_id", "span_id must be a non-empty string"))
                continue
            if span_id in span_ids:
                issues.append(CitationIssue(f"{span_path}.span_id", "duplicate span_id for evidence"))
            span_ids.add(span_id)

        evidence_index[evidence_id] = span_ids

    return evidence_index


def _validate_citation(
    citation: Any,
    citation_path: str,
    evidence_index: Mapping[str, set[str]],
    issues: list[CitationIssue],
) -> None:
    if not isinstance(citation, Mapping):
        issues.append(CitationIssue(citation_path, "citation must be an object"))
        return

    evidence_id = citation.get("evidence_id")
    span_id = citation.get("span_id")

    if not isinstance(evidence_id, str) or not evidence_id.strip():
        issues.append(CitationIssue(f"{citation_path}.evidence_id", "evidence_id must be a non-empty string"))
        return

    if not isinstance(span_id, str) or not span_id.strip():
        issues.append(CitationIssue(f"{citation_path}.span_id", "span_id must be a non-empty string"))
        return

    span_ids = evidence_index.get(evidence_id)
    if span_ids is None:
        issues.append(CitationIssue(f"{citation_path}.evidence_id", "unknown evidence_id"))
        return

    if span_id not in span_ids:
        issues.append(CitationIssue(f"{citation_path}.span_id", "unknown span_id for evidence_id"))


__all__ = [
    "CHECKED_SECTIONS",
    "CitationIssue",
    "assert_citation_integrity",
    "validate_citation_integrity",
]
