"""Validation for post-gap agent readiness replay v6.

This module is intentionally narrow and deterministic. It validates a text
payload that represents an agent readiness replay report before any live PP&D
automation path can be activated.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str


_REQUIRED_REFERENCES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("missing_user_gap_analysis", ("user gap analysis", "gap analysis")),
    ("missing_journal_dry_run_reference", ("journal dry-run", "journal dry run")),
    ("missing_synthetic_agent_requests", ("synthetic agent request", "synthetic agent requests")),
    ("missing_question_ordering_checks", ("question-ordering check", "question ordering check")),
    ("missing_stale_conflicting_evidence_explanations", ("stale evidence", "conflicting evidence")),
    ("missing_reversible_draft_routing_check", ("reversible draft",)),
    ("missing_local_pdf_preview_routing_check", ("local pdf preview", "local PDF preview")),
    ("missing_refused_consequential_action_check", ("refused consequential action",)),
    ("missing_refused_financial_action_check", ("refused financial action",)),
    ("missing_manual_handoff_reminder", ("manual handoff",)),
    ("missing_journal_event_expectations", ("journal event expectation", "journal event expectations")),
    ("missing_citation_payloads", ("citation payload", "citation payloads")),
    ("missing_validation_commands", ("validation command", "validation commands")),
)

_FORBIDDEN_MARKERS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("live_activation_claim", ("live activation enabled", "activated live automation", "live crawl enabled")),
    ("private_session_artifact", ("devhub session", "session cookie", "auth state", "private token", "bearer token")),
    ("official_action_completion_claim", ("submitted permit", "completed official action", "official action completed")),
    ("legal_or_permitting_guarantee", ("legal guarantee", "permit guaranteed", "approval guaranteed")),
    ("active_mutation_flag", ("active mutation", "mutation enabled", "write mode enabled", "live mutation")),
)


def _normalise_text(payload: str | Mapping[str, object]) -> str:
    if isinstance(payload, str):
        return payload.lower()
    parts: list[str] = []
    for key, value in payload.items():
        parts.append(str(key))
        parts.append(str(value))
    return "\n".join(parts).lower()


def _contains_any(text: str, needles: Iterable[str]) -> bool:
    return any(needle.lower() in text for needle in needles)


def validate_post_gap_agent_readiness_replay_v6(payload: str | Mapping[str, object]) -> list[ValidationIssue]:
    """Return validation issues for an agent readiness replay v6 payload."""
    text = _normalise_text(payload)
    issues: list[ValidationIssue] = []

    for code, required_markers in _REQUIRED_REFERENCES:
        if not _contains_any(text, required_markers):
            issues.append(ValidationIssue(code=code, message=f"Required replay evidence is missing: {code}"))

    for code, forbidden_markers in _FORBIDDEN_MARKERS:
        if _contains_any(text, forbidden_markers):
            issues.append(ValidationIssue(code=code, message=f"Forbidden readiness claim or artifact detected: {code}"))

    return issues


def assert_post_gap_agent_readiness_replay_v6(payload: str | Mapping[str, object]) -> None:
    issues = validate_post_gap_agent_readiness_replay_v6(payload)
    if issues:
        details = ", ".join(issue.code for issue in issues)
        raise ValueError(f"post-gap agent readiness replay v6 validation failed: {details}")
