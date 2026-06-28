"""Validation for PP&D public-recrawl operator checklist packets.

The validator is deterministic and side-effect free. It accepts plain packet
mappings so daemon proposals, fixtures, and future operator UI exports can be
checked before any live network client, browser session, processor invocation,
or production promotion is considered.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping
from urllib.parse import parse_qsl, urlparse


DEFAULT_ALLOWED_HOSTS = frozenset(
    {
        "www.portland.gov",
        "devhub.portlandoregon.gov",
        "www.portlandoregon.gov",
        "www.portlandmaps.com",
    }
)

_LIVE_NETWORK_KEYS = frozenset(
    {
        "allow_live_network",
        "allow_network",
        "execute_live",
        "executed_live_network",
        "live_crawl",
        "live_execution",
        "live_network",
        "network_enabled",
        "network_invoked",
        "run_live",
        "use_live_network",
    }
)

_RAW_BODY_KEYS = frozenset(
    {
        "body",
        "content",
        "html",
        "persist_raw_body",
        "raw_body",
        "raw_body_persistence",
        "raw_content",
        "raw_html",
        "response_body",
        "save_raw_body",
        "store_raw_body",
        "text",
    }
)

_DOWNLOADED_DOCUMENT_PATH_KEYS = frozenset(
    {
        "archive_path",
        "document_path",
        "document_paths",
        "download_path",
        "download_paths",
        "downloaded_document_path",
        "downloaded_document_paths",
        "local_document_path",
        "local_path",
        "pdf_path",
        "raw_document_path",
        "saved_path",
        "warc_path",
    }
)

_URL_FIELD_KEYS = frozenset(
    {
        "canonical_url",
        "href",
        "requested_url",
        "source_url",
        "start_url",
        "target_url",
        "url",
    }
)

_AUTH_QUERY_KEYS = frozenset(
    {
        "access_token",
        "api_key",
        "auth",
        "auth_token",
        "bearer",
        "client_secret",
        "code",
        "credential",
        "jwt",
        "key",
        "oauth",
        "password",
        "private_key",
        "secret",
        "session",
        "session_id",
        "sid",
        "signature",
        "signed",
        "state",
        "token",
    }
)

_PRIVATE_PATH_MARKERS = (
    "/account",
    "/accounts",
    "/admin",
    "/application",
    "/applications",
    "/auth",
    "/cart",
    "/dashboard",
    "/document",
    "/documents",
    "/inspection",
    "/inspections",
    "/login",
    "/logout",
    "/my",
    "/oauth",
    "/password",
    "/payment",
    "/payments",
    "/permit/",
    "/permits/",
    "/private",
    "/profile",
    "/register",
    "/secure",
    "/session",
    "/signin",
    "/sign-in",
    "/sso",
    "/upload",
    "/uploads",
    "/user",
)

_PRODUCTION_PROMOTION_KEYS = frozenset(
    {
        "auto_promote_to_production",
        "direct_production_promotion",
        "promote_directly",
        "promote_to_prod",
        "promote_to_production",
        "production_promotion",
        "skip_staging_review",
    }
)

_ABORT_KEYS = ("abort_conditions", "abortConditions", "stop_conditions", "stopConditions")
_REVIEW_KEYS = ("post_run_review_prompts", "postRunReviewPrompts", "review_prompts", "reviewPrompts")


@dataclass(frozen=True)
class ChecklistValidationIssue:
    """A deterministic validation issue for an operator checklist packet."""

    code: str
    message: str
    path: str = "$"


def validate_public_recrawl_operator_checklist_packet(
    packet: Mapping[str, Any],
    *,
    allowed_hosts: Iterable[str] = DEFAULT_ALLOWED_HOSTS,
) -> list[ChecklistValidationIssue]:
    """Return validation issues for a public-recrawl operator checklist packet."""

    if not isinstance(packet, Mapping):
        return [ChecklistValidationIssue("invalid_packet", "packet must be a mapping")]

    allowed = frozenset(host.lower() for host in allowed_hosts)
    issues: list[ChecklistValidationIssue] = []

    _collect_live_network_claims(packet, issues, "$", strict_text=True)
    _collect_raw_body_persistence(packet, issues, "$")
    _collect_downloaded_document_paths(packet, issues, "$")
    _collect_production_promotion(packet, issues, "$")
    _collect_url_issues(packet, issues, "$", allowed)

    if not _has_required_list(packet, _ABORT_KEYS):
        issues.append(
            ChecklistValidationIssue(
                "missing_abort_conditions",
                "public-recrawl operator checklist packets must include explicit abort conditions",
                "$.abort_conditions",
            )
        )

    if not _has_required_list(packet, _REVIEW_KEYS):
        issues.append(
            ChecklistValidationIssue(
                "missing_post_run_review_prompts",
                "public-recrawl operator checklist packets must include post-run review prompts",
                "$.post_run_review_prompts",
            )
        )

    return _dedupe_issues(issues)


def assert_public_recrawl_operator_checklist_packet_is_safe(packet: Mapping[str, Any], **kwargs: Any) -> None:
    """Raise ValueError when the operator checklist packet is unsafe."""

    issues = validate_public_recrawl_operator_checklist_packet(packet, **kwargs)
    if issues:
        details = "; ".join(f"{issue.code} at {issue.path}: {issue.message}" for issue in issues)
        raise ValueError(details)


def issue_codes(issues: Iterable[ChecklistValidationIssue]) -> set[str]:
    """Return issue codes from validation results for tests and daemon diagnostics."""

    return {issue.code for issue in issues}


def _collect_live_network_claims(value: Any, issues: list[ChecklistValidationIssue], path: str, *, strict_text: bool) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized = _normalize_key(key_text)
            child_path = f"{path}.{key_text}"
            if normalized in _LIVE_NETWORK_KEYS and _truthy_or_enabled_text(child):
                issues.append(
                    ChecklistValidationIssue(
                        "live_network_execution_claim",
                        "operator checklist packets must not claim live-network execution is enabled or already performed",
                        child_path,
                    )
                )
            _collect_live_network_claims(child, issues, child_path, strict_text=False)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _collect_live_network_claims(child, issues, f"{path}[{index}]", strict_text=False)
    elif strict_text and isinstance(value, str) and _mentions_live_network_execution(value):
        issues.append(
            ChecklistValidationIssue(
                "live_network_execution_claim",
                "operator checklist packets must not claim live-network execution is enabled or already performed",
                path,
            )
        )


def _collect_raw_body_persistence(value: Any, issues: list[ChecklistValidationIssue], path: str) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized = _normalize_key(key_text)
            child_path = f"{path}.{key_text}"
            if normalized in _RAW_BODY_KEYS and _non_empty_or_enabled(child):
                issues.append(
                    ChecklistValidationIssue(
                        "raw_body_persistence",
                        "operator checklist packets must not persist raw response bodies or raw page content",
                        child_path,
                    )
                )
            _collect_raw_body_persistence(child, issues, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _collect_raw_body_persistence(child, issues, f"{path}[{index}]")


def _collect_downloaded_document_paths(value: Any, issues: list[ChecklistValidationIssue], path: str) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized = _normalize_key(key_text)
            child_path = f"{path}.{key_text}"
            if normalized in _DOWNLOADED_DOCUMENT_PATH_KEYS and _has_value(child):
                issues.append(
                    ChecklistValidationIssue(
                        "downloaded_document_path",
                        "operator checklist packets must not include downloaded document, archive, or local artifact paths",
                        child_path,
                    )
                )
            _collect_downloaded_document_paths(child, issues, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _collect_downloaded_document_paths(child, issues, f"{path}[{index}]")


def _collect_production_promotion(value: Any, issues: list[ChecklistValidationIssue], path: str) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized = _normalize_key(key_text)
            child_path = f"{path}.{key_text}"
            if normalized in _PRODUCTION_PROMOTION_KEYS and _promotion_is_direct(child):
                issues.append(
                    ChecklistValidationIssue(
                        "direct_production_promotion",
                        "operator checklist packets must not permit direct production promotion",
                        child_path,
                    )
                )
            _collect_production_promotion(child, issues, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _collect_production_promotion(child, issues, f"{path}[{index}]")


def _collect_url_issues(value: Any, issues: list[ChecklistValidationIssue], path: str, allowed_hosts: frozenset[str]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized = _normalize_key(key_text)
            child_path = f"{path}.{key_text}"
            if normalized in _URL_FIELD_KEYS and isinstance(child, str):
                _append_url_issues(child, issues, child_path, allowed_hosts)
            else:
                _collect_url_issues(child, issues, child_path, allowed_hosts)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _collect_url_issues(child, issues, f"{path}[{index}]", allowed_hosts)
    elif isinstance(value, str) and _looks_like_url(value):
        _append_url_issues(value, issues, path, allowed_hosts)


def _append_url_issues(url: str, issues: list[ChecklistValidationIssue], path: str, allowed_hosts: frozenset[str]) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        issues.append(
            ChecklistValidationIssue(
                "unsupported_url",
                "public-recrawl URLs must be absolute HTTP(S) URLs",
                path,
            )
        )
        return

    host = parsed.hostname.lower()
    if host not in allowed_hosts:
        issues.append(
            ChecklistValidationIssue(
                "outside_allowlist_host",
                "public-recrawl URLs must stay inside the PP&D public host allowlist",
                path,
            )
        )

    if _is_private_or_authenticated_url(parsed):
        issues.append(
            ChecklistValidationIssue(
                "private_or_authenticated_url",
                "public-recrawl URLs must not be authenticated, tokenized, or private account URLs",
                path,
            )
        )


def _is_private_or_authenticated_url(parsed: Any) -> bool:
    if parsed.username or parsed.password:
        return True
    path = (parsed.path or "").lower()
    if any(path == marker or path.startswith(marker + "/") for marker in _PRIVATE_PATH_MARKERS):
        return True
    query_keys = {_normalize_key(key) for key, _value in parse_qsl(parsed.query, keep_blank_values=True)}
    if query_keys.intersection(_AUTH_QUERY_KEYS):
        return True
    return False


def _has_required_list(packet: Mapping[str, Any], keys: tuple[str, ...]) -> bool:
    for key in keys:
        value = packet.get(key)
        if isinstance(value, list) and any(_valid_required_list_item(item) for item in value):
            return True
    return False


def _valid_required_list_item(item: Any) -> bool:
    if isinstance(item, str):
        return bool(item.strip())
    if isinstance(item, Mapping):
        return any(isinstance(value, str) and value.strip() for value in item.values())
    return False


def _truthy_or_enabled_text(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, str):
        normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
        return normalized in {"true", "yes", "enabled", "allowed", "live", "executed", "performed"}
    return False


def _non_empty_or_enabled(value: Any) -> bool:
    if value is False or value is None:
        return False
    if isinstance(value, str):
        normalized = value.strip().lower()
        return normalized not in {"", "false", "no", "none", "disabled", "metadata_only"}
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return bool(value)


def _has_value(value: Any) -> bool:
    if value in (None, "", [], {}, ()):
        return False
    return True


def _promotion_is_direct(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, str):
        normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
        return normalized in {"true", "yes", "direct", "automatic", "auto", "prod", "production", "promote"}
    if isinstance(value, Mapping):
        return bool(value.get("direct") or value.get("automatic") or value.get("skip_review"))
    return False


def _mentions_live_network_execution(value: str) -> bool:
    text = value.strip().lower()
    return "live network" in text and any(marker in text for marker in ("executed", "performed", "enabled", "allowed"))


def _looks_like_url(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")


def _normalize_key(value: str) -> str:
    return value.strip().replace("-", "_").lower()


def _dedupe_issues(issues: list[ChecklistValidationIssue]) -> list[ChecklistValidationIssue]:
    seen: set[tuple[str, str]] = set()
    unique: list[ChecklistValidationIssue] = []
    for issue in issues:
        key = (issue.code, issue.path)
        if key in seen:
            continue
        seen.add(key)
        unique.append(issue)
    return unique
