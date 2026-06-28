"""Validation for post-promotion smoke replay plan v7.

The validator is intentionally data-shape tolerant so replay plans can be kept as
JSON/YAML-like dictionaries while still enforcing the mandatory rehearsal and
safety probes required by the PP&D promotion process.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class ValidationIssue:
    """A deterministic validation failure for a replay plan."""

    code: str
    message: str


@dataclass(frozen=True)
class SmokeReplayPlanValidation:
    """Validation result for a post-promotion smoke replay plan."""

    issues: tuple[ValidationIssue, ...]

    @property
    def ok(self) -> bool:
        return not self.issues

    def require_ok(self) -> None:
        if self.issues:
            detail = "; ".join(f"{issue.code}: {issue.message}" for issue in self.issues)
            raise ValueError(detail)


_FIELD_REQUIREMENTS: tuple[tuple[str, tuple[str, ...], str], ...] = (
    (
        "missing_promotion_rehearsal_references",
        ("promotion_rehearsal_references", "promotion_rehearsals", "rehearsal_references"),
        "plan must cite at least one prior promotion rehearsal reference",
    ),
    (
        "missing_smoke_scenario_rows",
        ("smoke_scenario_rows", "scenario_rows", "smoke_scenarios"),
        "plan must include at least one smoke scenario row",
    ),
    (
        "missing_rollback_trigger_observations",
        ("rollback_trigger_observations", "rollback_observations", "rollback_triggers"),
        "plan must include rollback trigger observations",
    ),
    (
        "missing_monitoring_expectations",
        ("monitoring_expectations", "monitoring", "post_promotion_monitoring"),
        "plan must include monitoring expectations",
    ),
    (
        "missing_validation_commands",
        ("validation_commands", "validation", "commands"),
        "plan must include deterministic validation commands",
    ),
)

_PROBE_REQUIREMENTS: tuple[tuple[str, tuple[tuple[str, ...], ...], str], ...] = (
    (
        "missing_information_or_stale_evidence_probe",
        (("missing", "information"), ("stale", "evidence")),
        "plan must probe missing information or stale evidence handling",
    ),
    (
        "missing_reversible_draft_or_local_pdf_preview_probe",
        (("reversible", "draft"), ("local", "pdf", "preview")),
        "plan must probe reversible draft or local PDF preview behavior",
    ),
    (
        "missing_exact_confirmation_or_refused_action_probe",
        (("exact", "confirmation"), ("refused", "action")),
        "plan must probe exact-confirmation or refused-action behavior",
    ),
    (
        "missing_manual_handoff_probe",
        (("manual", "handoff"),),
        "plan must probe manual handoff behavior",
    ),
)

_FORBIDDEN_TEXT_PATTERNS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "actual_activation_or_promotion_claim",
        re.compile(r"\b(activated|activation|promoted|promotion)\b.{0,48}\b(production|prod|live|complete|completed|done|successful|succeeded)\b|\b(production|prod|live)\b.{0,48}\b(activated|promoted)\b", re.IGNORECASE),
        "plan must not claim actual activation or promotion completion",
    ),
    (
        "live_crawl_execution_claim",
        re.compile(r"\b(live\s+crawl\s+(executed|ran|completed|started)|ran\s+(a\s+)?live\s+crawl|crawled\s+.*\blive\b|executed\s+.*\blive\s+crawl)\b", re.IGNORECASE),
        "plan must not claim live crawl execution",
    ),
    (
        "private_session_or_auth_artifact",
        re.compile(r"\b(cookie|cookies|session\s*(token|state|file|storage)|auth\s*(state|token|file)|storage_state|trace\.zip|\.har\b|password|credential|secret|mfa\s*code|captcha\s*token)\b", re.IGNORECASE),
        "plan must not include private session, authentication, trace, HAR, credential, MFA, or CAPTCHA artifacts",
    ),
    (
        "official_action_completion_claim",
        re.compile(r"\b(submitted\s+(the\s+)?(permit|application|request)|paid\s+(the\s+)?fee|scheduled\s+(the\s+)?inspection|uploaded\s+(the\s+)?correction|certified\s+(the\s+)?acknowledg|cancelled\s+(the\s+)?inspection|canceled\s+(the\s+)?inspection)\b", re.IGNORECASE),
        "plan must not claim official-action completion",
    ),
    (
        "legal_or_permitting_guarantee",
        re.compile(r"\b(legal\s+advice|guarantee[sd]?\s+(permit|approval|issuance|compliance)|permit\s+will\s+be\s+approved|approval\s+is\s+guaranteed|legally\s+guaranteed)\b", re.IGNORECASE),
        "plan must not make legal or permitting guarantees",
    ),
)

_MUTATION_KEY_RE = re.compile(r"(active_)?mutation|mutating|write_enabled|allow_live|execute_live|official_write", re.IGNORECASE)
_MUTATION_TEXT_RE = re.compile(r"\b(active[_ -]?mutation|mutation[_ -]?enabled|write[_ -]?enabled|allow[_ -]?live[_ -]?mutation|execute[_ -]?live)\s*[:=]\s*(true|yes|on|1)\b", re.IGNORECASE)
_DRY_RUN_FALSE_RE = re.compile(r"\bdry[_ -]?run\s*[:=]\s*(false|no|off|0)\b", re.IGNORECASE)


def validate_post_promotion_smoke_replay_plan_v7(plan: Mapping[str, Any]) -> SmokeReplayPlanValidation:
    """Validate the mandatory v7 smoke replay plan safety envelope."""

    issues: list[ValidationIssue] = []
    text_values = tuple(_iter_text(plan))
    all_text = "\n".join(text_values)

    for code, aliases, message in _FIELD_REQUIREMENTS:
        if not any(_has_non_empty_value(plan, alias) for alias in aliases):
            issues.append(ValidationIssue(code, message))

    for code, alternatives, message in _PROBE_REQUIREMENTS:
        if not _has_probe(alternatives, text_values):
            issues.append(ValidationIssue(code, message))

    for code, pattern, message in _FORBIDDEN_TEXT_PATTERNS:
        if pattern.search(all_text):
            issues.append(ValidationIssue(code, message))

    if _has_active_mutation_flag(plan) or _MUTATION_TEXT_RE.search(all_text) or _DRY_RUN_FALSE_RE.search(all_text):
        issues.append(
            ValidationIssue(
                "active_mutation_flag",
                "plan must keep active mutation, live execution, and official write flags disabled",
            )
        )

    return SmokeReplayPlanValidation(tuple(_dedupe_issues(issues)))


def assert_valid_post_promotion_smoke_replay_plan_v7(plan: Mapping[str, Any]) -> None:
    """Raise ValueError when a v7 smoke replay plan is invalid."""

    validate_post_promotion_smoke_replay_plan_v7(plan).require_ok()


def _has_non_empty_value(plan: Mapping[str, Any], key: str) -> bool:
    if key not in plan:
        return False
    value = plan[key]
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return any(_has_content(item) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_has_content(item) for item in value)
    return True


def _has_content(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return any(_has_content(item) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_has_content(item) for item in value)
    return True


def _has_probe(alternatives: tuple[tuple[str, ...], ...], text_values: Sequence[str]) -> bool:
    normalized_values = tuple(_normalize(value) for value in text_values)
    return any(
        any(all(term in value for term in alternative) for value in normalized_values)
        for alternative in alternatives
    )


def _iter_text(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        stripped = value.strip()
        if stripped:
            yield stripped
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            yield str(key)
            yield from _iter_text(item)
        return
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        for item in value:
            yield from _iter_text(item)
        return
    if value is not None:
        yield str(value)


def _has_active_mutation_flag(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if _MUTATION_KEY_RE.search(str(key)) and item is True:
                return True
            if str(key).lower().replace("-", "_") == "dry_run" and item is False:
                return True
            if _has_active_mutation_flag(item):
                return True
        return False
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_has_active_mutation_flag(item) for item in value)
    return False


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _dedupe_issues(issues: Sequence[ValidationIssue]) -> Iterable[ValidationIssue]:
    seen: set[str] = set()
    for issue in issues:
        if issue.code in seen:
            continue
        seen.add(issue.code)
        yield issue
