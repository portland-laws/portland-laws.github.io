"""Validation for public-source recrawl dry-run command plans.

The validator is intentionally conservative: a dry-run recrawl plan is only
acceptable when every target is public, allowlisted, supported by robots and
policy evidence, and represented as planning-only work with explicit throttling
and abort conditions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence
from urllib.parse import urlparse


ALLOWLISTED_HOSTS = frozenset(
    {
        "portland.gov",
        "www.portland.gov",
        "efiles.portlandoregon.gov",
        "www.portlandmaps.com",
    }
)

_AUTH_KEYS = frozenset(
    {
        "auth",
        "authenticated",
        "authentication",
        "authorization",
        "bearer_token",
        "cookie",
        "cookies",
        "credentials",
        "login",
        "password",
        "private",
        "session",
        "token",
    }
)

_RAW_OUTPUT_KEYS = frozenset(
    {
        "archive_output_path",
        "archive_path",
        "body_path",
        "download_path",
        "download_output_path",
        "raw_body_path",
        "raw_download_path",
        "raw_output_path",
    }
)

_LIVE_OR_EXECUTION_KEYS = frozenset(
    {
        "execute_processor",
        "execute_processors",
        "live_fetch",
        "perform_fetch",
        "processor_execution",
        "run_processor",
        "run_processors",
    }
)

_SCHEDULE_MUTATION_KEYS = frozenset(
    {
        "activate_schedule",
        "disable_schedule",
        "enable_schedule",
        "mutate_schedule",
        "schedule_mutation",
        "update_schedule",
        "write_schedule",
    }
)


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str


class PublicSourceRecrawlDryRunPlanError(ValueError):
    """Raised when a dry-run command plan is not safe to accept."""

    def __init__(self, issues: Sequence[ValidationIssue]) -> None:
        self.issues = tuple(issues)
        detail = "; ".join(f"{issue.code}: {issue.message}" for issue in self.issues)
        super().__init__(detail)


def validate_public_source_recrawl_dry_run_command_plan(plan: Mapping[str, Any]) -> list[ValidationIssue]:
    """Return validation issues for a public-source recrawl dry-run plan."""

    issues: list[ValidationIssue] = []
    targets = _targets(plan)

    if not targets:
        issues.append(ValidationIssue("missing_targets", "at least one public source target is required"))

    for index, target in enumerate(targets):
        prefix = f"targets[{index}]"
        target_url = _string_value(target, "url") or _string_value(target, "target")
        if not target_url:
            issues.append(ValidationIssue("missing_target_url", f"{prefix} must include a url"))
            continue

        parsed = urlparse(target_url)
        host = parsed.hostname or ""
        if parsed.scheme != "https":
            issues.append(ValidationIssue("non_https_target", f"{prefix} must use https: {target_url}"))
        if host not in ALLOWLISTED_HOSTS:
            issues.append(ValidationIssue("non_allowlisted_target", f"{prefix} host is not allowlisted: {host or target_url}"))

        if _has_truthy_key(target, _AUTH_KEYS):
            issues.append(ValidationIssue("private_or_authenticated_target", f"{prefix} includes private or authentication fields"))

    if _has_truthy_key(plan, _AUTH_KEYS):
        issues.append(ValidationIssue("private_or_authenticated_plan", "plan includes private or authentication fields"))

    if not _has_evidence(plan, "robots"):
        issues.append(ValidationIssue("missing_robots_evidence", "plan must cite robots.txt evidence"))
    if not _has_evidence(plan, "policy"):
        issues.append(ValidationIssue("missing_policy_evidence", "plan must cite public-source policy evidence"))

    if _has_present_key(plan, _RAW_OUTPUT_KEYS):
        issues.append(ValidationIssue("raw_output_path", "dry-run plans must not include raw body, download, or archive output paths"))

    if _has_truthy_key(plan, _LIVE_OR_EXECUTION_KEYS):
        issues.append(ValidationIssue("live_fetch_or_processor_execution", "dry-run plans must not claim live fetches or processor execution"))

    if not _has_note(plan, ("rate_limit", "rate_limits", "rate_limit_notes", "throttle", "throttling")):
        issues.append(ValidationIssue("missing_rate_limit_notes", "plan must document rate-limit or throttling behavior"))

    abort_conditions = plan.get("abort_conditions") or plan.get("abort_if") or plan.get("abort_notes")
    if not _has_text_or_items(abort_conditions):
        issues.append(ValidationIssue("missing_abort_conditions", "plan must document abort conditions"))

    if _has_truthy_key(plan, _SCHEDULE_MUTATION_KEYS):
        issues.append(ValidationIssue("schedule_mutation", "dry-run plans must not mutate active schedules"))

    return issues


def assert_valid_public_source_recrawl_dry_run_command_plan(plan: Mapping[str, Any]) -> None:
    """Raise when a public-source recrawl dry-run plan is unsafe or incomplete."""

    issues = validate_public_source_recrawl_dry_run_command_plan(plan)
    if issues:
        raise PublicSourceRecrawlDryRunPlanError(issues)


def _targets(plan: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    raw_targets = plan.get("targets") or plan.get("sources") or []
    if isinstance(raw_targets, Mapping):
        raw_targets = [raw_targets]
    if not isinstance(raw_targets, Sequence) or isinstance(raw_targets, (str, bytes)):
        return []

    targets: list[Mapping[str, Any]] = []
    for item in raw_targets:
        if isinstance(item, Mapping):
            targets.append(item)
        elif isinstance(item, str):
            targets.append({"url": item})
    return targets


def _string_value(mapping: Mapping[str, Any], key: str) -> str:
    value = mapping.get(key)
    return value.strip() if isinstance(value, str) else ""


def _has_truthy_key(mapping: Mapping[str, Any], keys: frozenset[str]) -> bool:
    for key, value in mapping.items():
        lowered = str(key).lower()
        if lowered in keys and bool(value):
            return True
    return False


def _has_present_key(mapping: Mapping[str, Any], keys: frozenset[str]) -> bool:
    for key, value in mapping.items():
        lowered = str(key).lower()
        if lowered in keys and value not in (None, "", [], {}):
            return True
    return False


def _has_evidence(plan: Mapping[str, Any], kind: str) -> bool:
    direct_keys = (
        f"{kind}_evidence",
        f"{kind}_txt_evidence",
        f"{kind}_notes",
        f"{kind}_url",
    )
    if _has_note(plan, direct_keys):
        return True

    evidence = plan.get("evidence")
    if isinstance(evidence, Mapping):
        return _has_note(evidence, direct_keys + (kind,))
    if isinstance(evidence, Sequence) and not isinstance(evidence, (str, bytes)):
        needle = kind.lower()
        return any(needle in str(item).lower() for item in evidence)
    return False


def _has_note(mapping: Mapping[str, Any], keys: Sequence[str]) -> bool:
    for key in keys:
        if _has_text_or_items(mapping.get(key)):
            return True
    return False


def _has_text_or_items(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return bool(value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return bool(value)
    return False


__all__ = [
    "ALLOWLISTED_HOSTS",
    "PublicSourceRecrawlDryRunPlanError",
    "ValidationIssue",
    "assert_valid_public_source_recrawl_dry_run_command_plan",
    "validate_public_source_recrawl_dry_run_command_plan",
]
