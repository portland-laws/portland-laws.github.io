"""Validation for public source monitoring schedule candidates.

This module is intentionally small and deterministic. It validates candidate
metadata before any live crawl, authenticated automation, or schedule mutation
can occur.
"""

from __future__ import annotations

from dataclasses import dataclass
from ipaddress import ip_address
from typing import Any, Iterable, Mapping
from urllib.parse import parse_qs, urlparse


DEFAULT_ALLOWLISTED_HOSTS = frozenset(
    {
        "portland.gov",
        "www.portland.gov",
        "efiles.portlandoregon.gov",
        "publicnotices.portland.gov",
        "www.portlandmaps.com",
    }
)

SECRET_QUERY_KEYS = frozenset(
    {
        "access_token",
        "api_key",
        "apikey",
        "auth",
        "code",
        "key",
        "password",
        "private_key",
        "session",
        "signature",
        "signed",
        "token",
    }
)

RAW_OR_DOWNLOAD_PATH_PARTS = (
    "/raw/",
    "/raw-body/",
    "/body/raw",
    "/download/",
    "/downloads/",
    "/archive/",
    "/archives/",
    "/export/",
    "/exports/",
)

RAW_OR_DOWNLOAD_SUFFIXES = (
    ".7z",
    ".bz2",
    ".doc",
    ".docx",
    ".gz",
    ".pdf",
    ".rar",
    ".tar",
    ".tgz",
    ".xls",
    ".xlsx",
    ".zip",
)

LIVE_NETWORK_KEYS = frozenset(
    {
        "executed_live_network",
        "live_network_execution",
        "network_executed",
        "ran_live",
        "real_browser_run",
    }
)

SCHEDULE_MUTATION_KEYS = frozenset(
    {
        "active",
        "auto_start",
        "cron_enabled",
        "enabled",
        "mutate_schedule",
        "schedule_mutation",
        "schedule_mutation_enabled",
        "start_immediately",
    }
)


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str


def validate_schedule_candidate(
    candidate: Mapping[str, Any],
    allowlisted_hosts: Iterable[str] = DEFAULT_ALLOWLISTED_HOSTS,
) -> list[ValidationIssue]:
    """Return validation issues for a public source monitoring candidate."""

    issues: list[ValidationIssue] = []
    allowlist = {host.lower() for host in allowlisted_hosts}
    urls = _candidate_urls(candidate)

    if not urls:
        issues.append(ValidationIssue("missing_source_url", "Candidate must declare at least one public source URL."))

    for url in urls:
        issues.extend(_validate_url(url, allowlist))

    if not _truthy(candidate.get("robots_txt_checked")):
        issues.append(ValidationIssue("missing_robots_prerequisite", "robots_txt_checked must be true before scheduling."))

    if not _truthy(candidate.get("source_policy_reviewed")) and not _truthy(candidate.get("policy_reviewed")):
        issues.append(ValidationIssue("missing_policy_prerequisite", "source_policy_reviewed or policy_reviewed must be true before scheduling."))

    for key in sorted(LIVE_NETWORK_KEYS):
        if _truthy(candidate.get(key)):
            issues.append(ValidationIssue("live_network_execution_claim", f"{key} must not be true in a schedule candidate."))

    reviewer_owners = candidate.get("reviewer_owners") or candidate.get("reviewers") or candidate.get("owners")
    if not _non_empty_string_list(reviewer_owners):
        issues.append(ValidationIssue("missing_reviewer_owners", "At least one reviewer owner is required."))

    abort_conditions = candidate.get("abort_conditions")
    if not _non_empty_string_list(abort_conditions):
        issues.append(ValidationIssue("missing_abort_conditions", "At least one abort condition is required."))

    for key in sorted(SCHEDULE_MUTATION_KEYS):
        if _truthy(candidate.get(key)):
            issues.append(ValidationIssue("active_schedule_mutation", f"{key} must not be true during candidate validation."))

    return issues


def assert_valid_schedule_candidate(candidate: Mapping[str, Any]) -> None:
    issues = validate_schedule_candidate(candidate)
    if issues:
        details = "; ".join(f"{issue.code}: {issue.message}" for issue in issues)
        raise ValueError(details)


def _candidate_urls(candidate: Mapping[str, Any]) -> list[str]:
    values: list[str] = []
    for key in ("source_url", "url"):
        value = candidate.get(key)
        if isinstance(value, str) and value.strip():
            values.append(value.strip())
    for key in ("source_urls", "urls"):
        value = candidate.get(key)
        if isinstance(value, str) and value.strip():
            values.append(value.strip())
        elif isinstance(value, list):
            values.extend(item.strip() for item in value if isinstance(item, str) and item.strip())
    return values


def _validate_url(url: str, allowlisted_hosts: set[str]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower().rstrip(".")

    if parsed.scheme not in {"http", "https"}:
        issues.append(ValidationIssue("private_or_authenticated_url", "Only http and https public URLs are allowed."))

    if parsed.username or parsed.password:
        issues.append(ValidationIssue("private_or_authenticated_url", "URLs must not embed authentication credentials."))

    if not hostname:
        issues.append(ValidationIssue("non_allowlisted_host", "URL must include a host."))
    elif _is_private_host(hostname):
        issues.append(ValidationIssue("private_or_authenticated_url", "Private, loopback, or local hosts are not allowed."))
    elif hostname not in allowlisted_hosts:
        issues.append(ValidationIssue("non_allowlisted_host", f"Host is not allowlisted: {hostname}"))

    query_keys = {key.lower() for key in parse_qs(parsed.query, keep_blank_values=True)}
    if query_keys & SECRET_QUERY_KEYS:
        issues.append(ValidationIssue("private_or_authenticated_url", "URL query string appears to contain authentication material."))

    path = parsed.path.lower()
    padded_path = f"/{path.strip('/')}/" if path else "/"
    if any(part in padded_path for part in RAW_OR_DOWNLOAD_PATH_PARTS) or path.endswith(RAW_OR_DOWNLOAD_SUFFIXES):
        issues.append(ValidationIssue("raw_body_download_or_archive_path", "Raw body, download, archive, export, and document artifact paths are not schedule sources."))

    return issues


def _is_private_host(hostname: str) -> bool:
    if hostname in {"localhost", "localhost.localdomain"} or hostname.endswith(".local"):
        return True
    try:
        address = ip_address(hostname)
    except ValueError:
        return False
    return address.is_private or address.is_loopback or address.is_link_local or address.is_reserved or address.is_multicast


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on", "enabled", "active"}
    if isinstance(value, int):
        return value != 0
    return bool(value)


def _non_empty_string_list(value: Any) -> bool:
    if not isinstance(value, list):
        return False
    return any(isinstance(item, str) and item.strip() for item in value)
