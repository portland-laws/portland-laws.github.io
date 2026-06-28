"""Validation guardrails for PP&D dry-run crawl plans.

The validator intentionally accepts plain dictionaries so it can be used before
any crawler-specific plan object is constructed. It is conservative: when a
field looks like a URL, host allowlist, rate policy, freshness policy, or output
path, it is checked regardless of where it appears in the plan.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import urlparse

_ALLOWED_SCHEMES = {"http", "https"}
_ALLOWED_PUBLIC_HOSTS = {
    "www.portland.gov",
    "portland.gov",
    "devhub.portlandoregon.gov",
}
_DEVHUB_HOSTS = {"devhub.portlandoregon.gov"}
_PRIVATE_DEVHUB_TOKENS = {
    "account",
    "admin",
    "auth",
    "authorize",
    "cart",
    "checkout",
    "dashboard",
    "login",
    "logout",
    "my-permits",
    "my_permits",
    "oauth",
    "password",
    "payment",
    "profile",
    "secure",
    "session",
    "signin",
    "sign-in",
    "signup",
    "sign-up",
    "submit",
    "token",
    "user",
}
_RAW_OUTPUT_TOKENS = {
    "body",
    "bodies",
    "document",
    "documents",
    "download",
    "downloads",
    "html",
    "pdf",
    "raw",
    "response",
    "responses",
    "snapshot",
    "snapshots",
}
_DOCUMENT_EXTENSIONS = {
    ".doc",
    ".docx",
    ".htm",
    ".html",
    ".pdf",
    ".rtf",
    ".xls",
    ".xlsx",
    ".zip",
}
_RATE_POLICY_KEYS = {
    "rate_limit",
    "rate_limit_policy",
    "rate_policy",
    "crawl_rate_limit",
    "throttle",
    "throttle_policy",
}
_FRESHNESS_POLICY_KEYS = {
    "freshness",
    "freshness_policy",
    "max_age",
    "max_age_days",
    "recrawl_after",
    "recrawl_after_days",
    "staleness_policy",
}
_OUTPUT_PATH_KEYS = {
    "output",
    "output_dir",
    "output_path",
    "path",
    "persist_path",
    "storage_path",
    "target_path",
    "write_path",
}
_HOST_SCOPE_KEYS = {
    "allowed_hosts",
    "allow_hosts",
    "allowlist_hosts",
    "domains",
    "host_allowlist",
    "hosts",
    "scope_hosts",
}
_URL_KEYS = {"url", "urls", "seed", "seeds", "start_url", "start_urls"}


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    location: str


class CrawlPlanValidationError(ValueError):
    """Raised when a dry-run crawl plan violates PP&D guardrails."""

    def __init__(self, issues: Sequence[ValidationIssue]) -> None:
        self.issues = tuple(issues)
        message = "; ".join(
            f"{issue.location}: {issue.code}: {issue.message}" for issue in self.issues
        )
        super().__init__(message)


def validate_dry_run_crawl_plan(plan: Mapping[str, Any]) -> None:
    """Validate a dry-run crawl plan, raising on any guardrail violation."""

    issues = list(iter_dry_run_crawl_plan_issues(plan))
    if issues:
        raise CrawlPlanValidationError(issues)


def iter_dry_run_crawl_plan_issues(plan: Mapping[str, Any]) -> Iterable[ValidationIssue]:
    """Yield all validation issues found in a dry-run crawl plan."""

    if not isinstance(plan, Mapping):
        yield ValidationIssue("invalid-plan", "plan must be a mapping", "$")
        return

    dry_run = plan.get("dry_run", plan.get("dryRun", True))
    if dry_run is not True:
        yield ValidationIssue(
            "not-dry-run",
            "crawl plan validation only permits explicit dry_run=true plans",
            "$.dry_run",
        )

    if not _has_policy(plan, _RATE_POLICY_KEYS):
        yield ValidationIssue(
            "missing-rate-limit-policy",
            "dry-run crawl plans must include a rate-limit or throttle policy",
            "$",
        )

    if not _has_policy(plan, _FRESHNESS_POLICY_KEYS):
        yield ValidationIssue(
            "missing-freshness-policy",
            "dry-run crawl plans must include a freshness or recrawl policy",
            "$",
        )

    yield from _walk(plan, "$", parent_key="")


def _walk(value: Any, location: str, parent_key: str) -> Iterable[ValidationIssue]:
    key = _normalize_key(parent_key)

    if isinstance(value, Mapping):
        for child_key, child_value in value.items():
            child_location = f"{location}.{child_key}"
            yield from _walk(child_value, child_location, str(child_key))
        return

    if isinstance(value, (list, tuple, set)):
        for index, child_value in enumerate(value):
            yield from _walk(child_value, f"{location}[{index}]", parent_key)
        return

    if isinstance(value, str):
        if key in _URL_KEYS or _looks_like_url(value):
            yield from _validate_url(value, location)
        if key in _HOST_SCOPE_KEYS:
            yield from _validate_host_scope([value], location)
        if key in _OUTPUT_PATH_KEYS or _looks_like_output_path(value):
            yield from _validate_output_path(value, location)
        return

    if isinstance(value, Sequence) and key in _HOST_SCOPE_KEYS:
        hosts = [item for item in value if isinstance(item, str)]
        yield from _validate_host_scope(hosts, location)


def _validate_url(url: str, location: str) -> Iterable[ValidationIssue]:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return

    scheme = parsed.scheme.lower()
    host = (parsed.hostname or "").lower()

    if scheme not in _ALLOWED_SCHEMES:
        yield ValidationIssue(
            "unsupported-url-scheme",
            f"unsupported URL scheme {scheme!r}; only http and https are allowed",
            location,
        )

    if parsed.username or parsed.password:
        yield ValidationIssue(
            "authenticated-url",
            "URLs must not include embedded credentials",
            location,
        )

    if host in _DEVHUB_HOSTS and _contains_private_devhub_token(parsed.path, parsed.query):
        yield ValidationIssue(
            "private-devhub-url",
            "DevHub URL appears to target an authenticated or private workflow",
            location,
        )

    if host and not _is_allowed_host(host):
        yield ValidationIssue(
            "host-out-of-scope",
            f"host {host!r} is outside the PP&D public crawl allowlist",
            location,
        )


def _validate_host_scope(hosts: Sequence[str], location: str) -> Iterable[ValidationIssue]:
    for host_value in hosts:
        host = _host_from_scope_value(host_value)
        if not host:
            continue
        if "*" in host or host.startswith("."):
            yield ValidationIssue(
                "over-broad-host-expansion",
                f"host scope {host_value!r} is too broad",
                location,
            )
        elif not _is_allowed_host(host):
            yield ValidationIssue(
                "host-out-of-scope",
                f"host {host!r} is outside the PP&D public crawl allowlist",
                location,
            )


def _validate_output_path(path_value: str, location: str) -> Iterable[ValidationIssue]:
    lowered = path_value.lower()
    path = PurePosixPath(lowered.replace("\\", "/"))
    parts = {part for part in path.parts if part not in {"/", ".", ".."}}

    if path.suffix in _DOCUMENT_EXTENSIONS or parts.intersection(_RAW_OUTPUT_TOKENS):
        yield ValidationIssue(
            "raw-output-path",
            "output path would persist raw bodies or downloaded documents",
            location,
        )


def _has_policy(plan: Mapping[str, Any], keys: set[str]) -> bool:
    for key, value in _iter_mapping_items(plan):
        if _normalize_key(key) in keys and value not in (None, "", [], {}):
            return True
    return False


def _iter_mapping_items(value: Any) -> Iterable[tuple[str, Any]]:
    if isinstance(value, Mapping):
        for key, child in value.items():
            yield str(key), child
            yield from _iter_mapping_items(child)
    elif isinstance(value, (list, tuple, set)):
        for child in value:
            yield from _iter_mapping_items(child)


def _normalize_key(key: str) -> str:
    return key.replace("-", "_").strip().lower()


def _looks_like_url(value: str) -> bool:
    parsed = urlparse(value)
    return bool(parsed.scheme and parsed.netloc)


def _looks_like_output_path(value: str) -> bool:
    lowered = value.lower()
    return lowered.startswith(("ppd/", "./ppd/", "/")) or any(
        token in lowered for token in ("output", "artifact", "crawl")
    )


def _host_from_scope_value(value: str) -> str:
    parsed = urlparse(value if "://" in value else f"https://{value}")
    return (parsed.hostname or "").lower()


def _is_allowed_host(host: str) -> bool:
    return host in _ALLOWED_PUBLIC_HOSTS


def _contains_private_devhub_token(path: str, query: str) -> bool:
    text = f"{path}?{query}".lower()
    normalized = text.replace("_", "-")
    tokens = {part for part in normalized.replace("?", "/").replace("&", "/").replace("=", "/").split("/") if part}
    return bool(tokens.intersection(_PRIVATE_DEVHUB_TOKENS))
