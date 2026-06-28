"""Validation for PP&D public recrawl batch plans.

The validator is intentionally side-effect free. It accepts plain dictionaries so
fixtures, daemon payloads, and future typed contracts can all be checked before
any network client or processor suite is invoked.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable
from urllib.parse import urlparse, parse_qs


DEFAULT_ALLOWED_HOSTS = frozenset(
    {
        "www.portland.gov",
        "devhub.portlandoregon.gov",
        "www.portlandoregon.gov",
        "www.portlandmaps.com",
    }
)

_PRIVATE_PATH_MARKERS = (
    "/admin",
    "/account",
    "/accounts",
    "/auth",
    "/dashboard",
    "/login",
    "/logout",
    "/my/",
    "/my-",
    "/oauth",
    "/password",
    "/profile",
    "/register",
    "/session",
    "/signin",
    "/sign-in",
    "/user",
)

_PRIVATE_QUERY_KEYS = frozenset(
    {
        "access_token",
        "apikey",
        "api_key",
        "auth",
        "code",
        "key",
        "password",
        "private_token",
        "refresh_token",
        "session",
        "signature",
        "sig",
        "token",
    }
)

_DOCUMENT_PATH_KEYS = (
    "downloaded_document_path",
    "downloaded_document_paths",
    "download_path",
    "download_paths",
    "document_path",
    "document_paths",
    "raw_document_path",
    "raw_document_paths",
)

_RAW_BODY_KEYS = (
    "persist_raw_body",
    "raw_body_persistence",
    "store_raw_body",
    "save_raw_body",
)

_LIVE_NETWORK_KEYS = (
    "allow_live_network",
    "enable_live_network",
    "live_network",
    "network_enabled",
    "use_live_network",
)

_DRY_RUN_KEYS = (
    "dry_run_only",
    "dry_run",
)


@dataclass(frozen=True)
class ValidationIssue:
    """A deterministic validation failure for a recrawl batch plan."""

    code: str
    message: str
    path: str = "$"


def validate_public_recrawl_batch_plan(
    plan: dict[str, Any],
    *,
    allowed_hosts: Iterable[str] = DEFAULT_ALLOWED_HOSTS,
) -> list[ValidationIssue]:
    """Return all validation issues for a public recrawl batch plan."""

    allowed = frozenset(host.lower() for host in allowed_hosts)
    issues: list[ValidationIssue] = []

    if not isinstance(plan, dict):
        return [ValidationIssue("invalid_plan", "plan must be a dictionary")]

    if _has_truthy(plan, _LIVE_NETWORK_KEYS):
        issues.append(
            ValidationIssue(
                "live_network_flag",
                "public recrawl batch plans must not enable live-network execution",
            )
        )

    if not _is_dry_run_only(plan):
        issues.append(
            ValidationIssue(
                "missing_dry_run_only",
                "public recrawl batch plans must declare dry-run-only status",
            )
        )

    rate_limit = _first_present(plan, ("rate_limit", "rate_limits", "throttle"))
    if not _has_bounded_rate_limit(rate_limit):
        issues.append(
            ValidationIssue(
                "unbounded_rate_limit",
                "public recrawl batch plans must include a bounded positive rate limit",
                "$.rate_limit",
            )
        )

    if _allows_raw_body_persistence(plan):
        issues.append(
            ValidationIssue(
                "raw_body_persistence",
                "public recrawl batch plans must not persist raw response bodies",
            )
        )

    document_path = _first_present(plan, _DOCUMENT_PATH_KEYS)
    if _has_non_empty_value(document_path):
        issues.append(
            ValidationIssue(
                "downloaded_document_path",
                "public recrawl batch plans must not contain downloaded document paths",
            )
        )

    targets = _targets(plan)
    if not targets:
        issues.append(
            ValidationIssue(
                "missing_targets",
                "public recrawl batch plans must include at least one target URL",
                "$.targets",
            )
        )

    for index, target in enumerate(targets):
        target_path = f"$.targets[{index}]"
        url = _target_url(target)
        parsed = urlparse(url) if url else None

        if not url:
            issues.append(
                ValidationIssue(
                    "missing_url",
                    "recrawl target must include a URL",
                    target_path,
                )
            )
            continue

        if parsed is None or parsed.scheme not in {"https", "http"} or not parsed.hostname:
            issues.append(
                ValidationIssue(
                    "unsupported_url",
                    "recrawl target URL must be an absolute HTTP(S) URL",
                    f"{target_path}.url",
                )
            )
            continue

        host = parsed.hostname.lower()
        if host not in allowed:
            issues.append(
                ValidationIssue(
                    "outside_allowlist_host",
                    "recrawl target host is outside the PP&D public allowlist",
                    f"{target_path}.url",
                )
            )

        if _is_private_or_authenticated_url(url):
            issues.append(
                ValidationIssue(
                    "private_or_authenticated_url",
                    "recrawl target appears private, authenticated, or tokenized",
                    f"{target_path}.url",
                )
            )

        if isinstance(target, dict):
            if not _has_evidence(target, "robots"):
                issues.append(
                    ValidationIssue(
                        "missing_robots_evidence",
                        "recrawl target must include robots evidence",
                        target_path,
                    )
                )
            if not _has_evidence(target, "policy"):
                issues.append(
                    ValidationIssue(
                        "missing_policy_evidence",
                        "recrawl target must include crawl policy evidence",
                        target_path,
                    )
                )
            if _allows_raw_body_persistence(target):
                issues.append(
                    ValidationIssue(
                        "raw_body_persistence",
                        "recrawl target must not persist raw response bodies",
                        target_path,
                    )
                )
            target_document_path = _first_present(target, _DOCUMENT_PATH_KEYS)
            if _has_non_empty_value(target_document_path):
                issues.append(
                    ValidationIssue(
                        "downloaded_document_path",
                        "recrawl target must not contain downloaded document paths",
                        target_path,
                    )
                )
        else:
            issues.append(
                ValidationIssue(
                    "missing_robots_evidence",
                    "string recrawl targets cannot carry robots evidence",
                    target_path,
                )
            )
            issues.append(
                ValidationIssue(
                    "missing_policy_evidence",
                    "string recrawl targets cannot carry crawl policy evidence",
                    target_path,
                )
            )

    return issues


def assert_public_recrawl_batch_plan_is_safe(
    plan: dict[str, Any],
    *,
    allowed_hosts: Iterable[str] = DEFAULT_ALLOWED_HOSTS,
) -> None:
    """Raise ValueError when the plan fails public recrawl validation."""

    issues = validate_public_recrawl_batch_plan(plan, allowed_hosts=allowed_hosts)
    if issues:
        details = "; ".join(f"{issue.code} at {issue.path}: {issue.message}" for issue in issues)
        raise ValueError(details)


def _targets(plan: dict[str, Any]) -> list[Any]:
    value = _first_present(plan, ("targets", "urls", "seeds"))
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if value is None:
        return []
    return [value]


def _target_url(target: Any) -> str | None:
    if isinstance(target, str):
        return target
    if isinstance(target, dict):
        value = _first_present(target, ("url", "canonical_url", "requested_url"))
        return value if isinstance(value, str) else None
    return None


def _first_present(mapping: dict[str, Any], keys: Iterable[str]) -> Any:
    for key in keys:
        if key in mapping:
            return mapping[key]
    return None


def _has_truthy(mapping: dict[str, Any], keys: Iterable[str]) -> bool:
    return any(bool(mapping.get(key)) for key in keys)


def _is_dry_run_only(plan: dict[str, Any]) -> bool:
    if bool(plan.get("dry_run_only")):
        return True
    return bool(plan.get("dry_run")) and not bool(plan.get("execute"))


def _has_bounded_rate_limit(value: Any) -> bool:
    if isinstance(value, dict):
        delay = value.get("min_delay_seconds") or value.get("delay_seconds")
        per_host = value.get("max_requests_per_host") or value.get("max_requests")
        return _positive_number(delay) and _positive_int(per_host)
    return False


def _positive_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0


def _positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _allows_raw_body_persistence(mapping: dict[str, Any]) -> bool:
    for key in _RAW_BODY_KEYS:
        value = mapping.get(key)
        if value is True:
            return True
        if isinstance(value, str) and value.lower() not in {"", "false", "none", "no", "disabled"}:
            return True
    return False


def _has_non_empty_value(value: Any) -> bool:
    if value is None:
        return False
    if value == "":
        return False
    if isinstance(value, (list, tuple, set, dict)) and not value:
        return False
    return True


def _has_evidence(target: dict[str, Any], evidence_type: str) -> bool:
    direct_keys = (
        f"{evidence_type}_evidence",
        f"{evidence_type}_policy_evidence",
        f"{evidence_type}_checked_at",
    )
    if any(_has_non_empty_value(target.get(key)) for key in direct_keys):
        return True

    evidence = target.get("evidence")
    if isinstance(evidence, dict):
        nested = evidence.get(evidence_type)
        return _has_non_empty_value(nested)
    return False


def _is_private_or_authenticated_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.username or parsed.password:
        return True

    path = parsed.path.lower()
    if any(marker in path for marker in _PRIVATE_PATH_MARKERS):
        return True

    query = parse_qs(parsed.query, keep_blank_values=True)
    if any(key.lower() in _PRIVATE_QUERY_KEYS for key in query):
        return True

    host = (parsed.hostname or "").lower()
    if host == "devhub.portlandoregon.gov" and path not in {"", "/"}:
        public_markers = ("/public", "/permit", "/search")
        if not any(path.startswith(marker) for marker in public_markers):
            return True

    return False
