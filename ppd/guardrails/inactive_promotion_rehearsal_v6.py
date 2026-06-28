"""Validation for inactive guardrail promotion rehearsal v6 artifacts.

The validator is intentionally text-oriented because the rehearsal handoff may be
kept as Markdown, JSON, or another commit-safe manifest. It checks for required
review rows and rejects language that would make an inactive rehearsal look like
an active promotion or official PP&D action.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, Sequence


@dataclass(frozen=True)
class RehearsalRule:
    """A named regular-expression rule used by the v6 rehearsal validator."""

    rule_id: str
    description: str
    patterns: tuple[str, ...]

    def matches(self, text: str) -> bool:
        return all(re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE) for pattern in self.patterns)


@dataclass(frozen=True)
class RehearsalValidationResult:
    """Structured result for inactive promotion rehearsal validation."""

    is_valid: bool
    missing_required: tuple[str, ...]
    forbidden_claims: tuple[str, ...]

    def raise_for_invalid(self) -> None:
        if self.is_valid:
            return
        parts: list[str] = []
        if self.missing_required:
            parts.append("missing required rehearsal evidence: " + ", ".join(self.missing_required))
        if self.forbidden_claims:
            parts.append("forbidden inactive rehearsal content: " + ", ".join(self.forbidden_claims))
        raise ValueError("; ".join(parts))


REQUIRED_RULES: tuple[RehearsalRule, ...] = (
    RehearsalRule(
        "release_readiness_references",
        "release readiness references are cited",
        (r"release\s+readiness", r"reference|citation|source|evidence"),
    ),
    RehearsalRule(
        "inactive_promotion_candidate_rows",
        "inactive promotion candidate rows are present",
        (r"inactive\s+promotion\s+candidate", r"\|[^\n]*(candidate|bundle|guardrail)[^\n]*\|"),
    ),
    RehearsalRule(
        "reviewer_controlled_signoff_placeholders",
        "reviewer-controlled signoff placeholders are present",
        (r"reviewer[-\s]+controlled", r"sign[-\s]*off", r"placeholder|pending|tbd"),
    ),
    RehearsalRule(
        "source_freshness_clearance_prerequisites",
        "source freshness clearance prerequisites are present",
        (r"source\s+freshness", r"clearance", r"prerequisite|precondition|required"),
    ),
    RehearsalRule(
        "unresolved_hold_propagation",
        "unresolved hold propagation is present",
        (r"unresolved\s+hold", r"propagat"),
    ),
    RehearsalRule(
        "rollback_checkpoint_rows",
        "rollback checkpoint rows are present",
        (r"rollback\s+checkpoint", r"\|[^\n]*(checkpoint|rollback)[^\n]*\|"),
    ),
    RehearsalRule(
        "post_promotion_smoke_replay_expectations",
        "post-promotion smoke replay expectations are present",
        (r"post[-\s]+promotion", r"smoke\s+replay", r"expectation|expected|must"),
    ),
    RehearsalRule(
        "agent_api_compatibility_reminders",
        "agent API compatibility reminders are present",
        (r"agent\s+api", r"compatibility", r"reminder|verify|check"),
    ),
    RehearsalRule(
        "monitoring_handoff_rows",
        "monitoring handoff rows are present",
        (r"monitoring\s+handoff", r"\|[^\n]*(owner|handoff|monitoring)[^\n]*\|"),
    ),
    RehearsalRule(
        "validation_commands",
        "validation commands are present",
        (r"validation\s+commands?", r"python3\s+ppd/daemon/ppd_daemon\.py\s+--self-test"),
    ),
)

FORBIDDEN_RULES: tuple[RehearsalRule, ...] = (
    RehearsalRule(
        "active_activation_claims",
        "inactive rehearsals must not claim active activation",
        (
            r"\b(active\s+activation\s+complete|activated\s+in\s+production|promoted\s+to\s+active|active\s+promotion\s+complete|go[-\s]*live\s+complete)\b",
        ),
    ),
    RehearsalRule(
        "private_session_or_auth_artifacts",
        "inactive rehearsals must not include private/session/auth artifacts",
        (
            r"\b(cookie|session\s*token|auth\s*state|storageState|trace\.zip|\.har\b|playwright\s+trace|private\s+upload|password|mfa\s+secret)\b",
        ),
    ),
    RehearsalRule(
        "official_action_completion_claims",
        "inactive rehearsals must not claim official PP&D action completion",
        (
            r"\b(official\s+action\s+complete|submitted\s+to\s+pp&d|submitted\s+to\s+devhub|payment\s+completed|inspection\s+scheduled|certification\s+completed|uploaded\s+to\s+official\s+record)\b",
        ),
    ),
    RehearsalRule(
        "legal_or_permitting_guarantees",
        "inactive rehearsals must not provide legal or permitting guarantees",
        (
            r"\b(legal\s+advice|guaranteed\s+approval|permit\s+will\s+be\s+approved|approval\s+is\s+guaranteed|legally\s+binding\s+determination)\b",
        ),
    ),
    RehearsalRule(
        "active_mutation_flags",
        "inactive rehearsals must not enable active mutation flags",
        (
            r"\b(active|activate|mutation|mutate|writes_enabled|live_mutation|production_write)\b\s*[:=]\s*(true|1|yes|on)",
        ),
    ),
)


def validate_inactive_promotion_rehearsal_v6(text: str) -> RehearsalValidationResult:
    """Validate an inactive guardrail promotion rehearsal v6 handoff."""

    missing_required = tuple(rule.rule_id for rule in REQUIRED_RULES if not rule.matches(text))
    forbidden_claims = tuple(rule.rule_id for rule in FORBIDDEN_RULES if rule.matches(text))
    return RehearsalValidationResult(
        is_valid=not missing_required and not forbidden_claims,
        missing_required=missing_required,
        forbidden_claims=forbidden_claims,
    )


def assert_inactive_promotion_rehearsal_v6(text: str) -> None:
    """Raise ValueError when a rehearsal handoff is not valid."""

    validate_inactive_promotion_rehearsal_v6(text).raise_for_invalid()


def validate_many_inactive_promotion_rehearsals_v6(texts: Iterable[str]) -> tuple[RehearsalValidationResult, ...]:
    """Validate multiple rehearsal artifacts without side effects."""

    return tuple(validate_inactive_promotion_rehearsal_v6(text) for text in texts)


def required_rule_ids() -> Sequence[str]:
    """Return stable required rule identifiers for tests and daemon reports."""

    return tuple(rule.rule_id for rule in REQUIRED_RULES)


def forbidden_rule_ids() -> Sequence[str]:
    """Return stable forbidden rule identifiers for tests and daemon reports."""

    return tuple(rule.rule_id for rule in FORBIDDEN_RULES)
