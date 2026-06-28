"""Validation for inactive PP&D guardrail smoke replay plan v6.

The validator is intentionally fixture-friendly and side-effect free. It checks that an
inactive replay plan includes the rehearsal evidence needed by reviewers while
rejecting language or flags that imply activation, live crawling, private session
artifacts, official completion, legal guarantees, or mutation capability.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Iterable, Mapping


REQUIRED_SECTIONS: Mapping[str, str] = {
    "activation_rehearsal_references": "missing activation rehearsal references",
    "post_activation_smoke_scenarios": "missing post-activation smoke scenarios",
    "source_freshness_precheck_rows": "missing source-freshness precheck rows",
    "agent_facing_response_probes": "missing agent-facing response probes",
    "rollback_trigger_observations": "missing rollback trigger observations",
    "monitoring_signal_expectations": "missing monitoring signal expectations",
    "reviewer_attendance_checkpoints": "missing reviewer attendance checkpoints",
    "validation_commands": "missing validation commands",
}

INACTIVE_STATUSES = {"inactive", "rehearsal", "planned", "dry_run", "draft"}

FORBIDDEN_TEXT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "actual activation claims",
        re.compile(r"\b(activated|activation completed|activated in production|production activation|went live|live activation)\b", re.IGNORECASE),
    ),
    (
        "live crawl execution claims",
        re.compile(r"\b(live crawl executed|executed live crawl|live crawl completed|crawled live|ran live crawl|production crawl)\b", re.IGNORECASE),
    ),
    (
        "private/session/auth artifacts",
        re.compile(
            r"\b(cookie|cookies|session state|auth state|storage state|credential|credentials|password|bearer token|access token|refresh token|mfa|captcha|har file|trace zip|screenshot|private upload|private document|local private path)\b|\.(har|trace\.zip)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "official-action completion claims",
        re.compile(r"\b(submitted|submission completed|paid fees|payment completed|scheduled inspection|uploaded correction|certified acknowledgement|cancelled permit|withdrew application|official action completed)\b", re.IGNORECASE),
    ),
    (
        "legal or permitting guarantees",
        re.compile(r"\b(guaranteed approval|permit guaranteed|legally sufficient|legal advice|compliance guaranteed|approval assured|will be approved|permit will issue)\b", re.IGNORECASE),
    ),
)

FORBIDDEN_TRUE_FLAGS = {
    "active",
    "activated",
    "allow_mutations",
    "mutations_enabled",
    "mutation_enabled",
    "execute_live_crawl",
    "live_crawl",
    "crawl_executed",
    "official_action_completed",
    "submitted",
    "paid",
    "certified",
    "uploaded_to_official_record",
    "schedule_inspection",
    "scheduled_inspection",
}

FORBIDDEN_FALSE_FLAGS = {
    "inactive",
    "dry_run",
    "read_only",
    "requires_reviewer_attendance",
}


@dataclass(frozen=True)
class ValidationFinding:
    """A single deterministic validation finding."""

    code: str
    message: str
    path: str


@dataclass(frozen=True)
class ValidationResult:
    """Validation result for an inactive smoke replay plan."""

    ok: bool
    findings: tuple[ValidationFinding, ...]


def validate_inactive_smoke_replay_plan_v6(plan: Mapping[str, Any]) -> ValidationResult:
    """Validate an inactive guardrail smoke replay plan v6 mapping."""

    findings: list[ValidationFinding] = []

    version = str(plan.get("version", "")).strip().lower()
    if version not in {"v6", "6"}:
        findings.append(
            ValidationFinding(
                code="wrong_version",
                message="inactive guardrail smoke replay plan must declare version v6",
                path="$.version",
            )
        )

    status = str(plan.get("status", "")).strip().lower()
    if status not in INACTIVE_STATUSES:
        findings.append(
            ValidationFinding(
                code="not_inactive",
                message="inactive guardrail smoke replay plan must remain inactive/dry-run only",
                path="$.status",
            )
        )

    for key, message in REQUIRED_SECTIONS.items():
        if _is_missing_section(plan.get(key)):
            findings.append(
                ValidationFinding(
                    code=f"missing_{key}",
                    message=message,
                    path=f"$.{key}",
                )
            )

    for path, value in _walk(plan):
        key = path.rsplit(".", 1)[-1].strip("[]").lower()
        normalized_key = key.replace("-", "_")
        if normalized_key in FORBIDDEN_TRUE_FLAGS and value is True:
            findings.append(
                ValidationFinding(
                    code="active_mutation_flag",
                    message="active mutation flags are not allowed in inactive smoke replay plan v6",
                    path=path,
                )
            )
        if normalized_key in FORBIDDEN_FALSE_FLAGS and value is False:
            findings.append(
                ValidationFinding(
                    code="inactive_guardrail_disabled",
                    message="inactive/read-only/reviewer-attendance safeguards must not be disabled",
                    path=path,
                )
            )
        if isinstance(value, str):
            for label, pattern in FORBIDDEN_TEXT_PATTERNS:
                if pattern.search(value):
                    findings.append(
                        ValidationFinding(
                            code=_code_from_label(label),
                            message=f"{label} are not allowed in inactive smoke replay plan v6",
                            path=path,
                        )
                    )

    return ValidationResult(ok=not findings, findings=tuple(findings))


def assert_inactive_smoke_replay_plan_v6(plan: Mapping[str, Any]) -> None:
    """Raise ValueError when the inactive v6 smoke replay plan is invalid."""

    result = validate_inactive_smoke_replay_plan_v6(plan)
    if result.ok:
        return
    rendered = "; ".join(f"{finding.path}: {finding.message}" for finding in result.findings)
    raise ValueError(rendered)


def _is_missing_section(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, Mapping):
        return not value
    if isinstance(value, Iterable) and not isinstance(value, (bytes, bytearray)):
        return not list(value)
    return False


def _walk(value: Any, path: str = "$") -> Iterable[tuple[str, Any]]:
    yield path, value
    if isinstance(value, Mapping):
        for key, child in value.items():
            yield from _walk(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk(child, f"{path}[{index}]")
    elif isinstance(value, tuple):
        for index, child in enumerate(value):
            yield from _walk(child, f"{path}[{index}]")


def _code_from_label(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
