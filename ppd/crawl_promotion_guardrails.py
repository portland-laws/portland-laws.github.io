"""Guardrails for deciding whether a crawl result may be promoted.

The checks here are intentionally deterministic and side-effect free.  They do
not crawl, authenticate, download, or write any output.  Callers pass the crawl
preflight summary and planned output paths, and the validator returns a promotion
verdict plus machine-readable blocking reasons.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePath
from typing import Any, Mapping, Sequence

_SAFE_PRELIGHT_STATES = {"allow", "allowed", "pass", "passed", "known_allowed", "ok"}
_RAW_PATH_MARKERS = (
    "raw",
    "raw_bodies",
    "body_cache",
    "download",
    "downloads",
    "documents",
    "doc_cache",
    "html",
    "pdf",
)
_RAW_FILE_SUFFIXES = {".html", ".htm", ".pdf", ".doc", ".docx", ".zip"}


@dataclass(frozen=True)
class CrawlPromotionVerdict:
    """Result of crawl promotion guardrail validation."""

    allowed: bool
    reasons: tuple[str, ...]


def validate_crawl_promotion_guardrails(summary: Mapping[str, Any]) -> CrawlPromotionVerdict:
    """Return whether a crawl summary is safe to promote.

    Expected keys are deliberately plain dictionaries so this module can be used
    from daemon code, tests, and fixtures without coupling to crawler internals:

    - robots_preflight: explicit allow/pass state required
    - policy_preflight: explicit allow/pass state required
    - rate_limit_policy: mapping with enabled truthy and requests_per_minute > 0
    - freshness_policy: mapping with is_stale false and stale false
    - host_expansion: mapping with over_broad false and unexpected_hosts empty
    - output_paths: sequence of paths that would be persisted
    """

    reasons: list[str] = []

    if not _is_safe_preflight(summary.get("robots_preflight")):
        reasons.append("robots_preflight_unknown")

    if not _is_safe_preflight(summary.get("policy_preflight")):
        reasons.append("policy_preflight_unknown")

    if not _has_rate_limit_policy(summary.get("rate_limit_policy")):
        reasons.append("rate_limit_policy_missing")

    if _freshness_policy_is_stale(summary.get("freshness_policy")):
        reasons.append("freshness_policy_stale")

    if _host_expansion_is_over_broad(summary.get("host_expansion")):
        reasons.append("host_expansion_over_broad")

    raw_paths = tuple(path for path in _output_paths(summary.get("output_paths")) if _looks_like_raw_output_path(path))
    if raw_paths:
        reasons.append("raw_output_path_persistence")

    return CrawlPromotionVerdict(allowed=not reasons, reasons=tuple(reasons))


def _is_safe_preflight(value: Any) -> bool:
    if isinstance(value, Mapping):
        state = value.get("state", value.get("status"))
        if value.get("unknown") is True:
            return False
        if value.get("allowed") is True or value.get("passed") is True:
            return True
        return _is_safe_preflight(state)
    if value is None:
        return False
    return str(value).strip().lower() in _SAFE_PRELIGHT_STATES


def _has_rate_limit_policy(value: Any) -> bool:
    if not isinstance(value, Mapping):
        return False
    if value.get("missing") is True:
        return False
    if value.get("enabled") is False:
        return False
    rate = value.get("requests_per_minute", value.get("rpm", value.get("max_requests_per_minute")))
    try:
        return float(rate) > 0
    except (TypeError, ValueError):
        return False


def _freshness_policy_is_stale(value: Any) -> bool:
    if not isinstance(value, Mapping):
        return True
    return bool(value.get("is_stale") or value.get("stale") or value.get("expired"))


def _host_expansion_is_over_broad(value: Any) -> bool:
    if not isinstance(value, Mapping):
        return True
    if value.get("over_broad") or value.get("wildcard") or value.get("allows_all_hosts"):
        return True
    unexpected = value.get("unexpected_hosts", ())
    if unexpected:
        return True
    allowed_hosts = value.get("allowed_hosts", ())
    expanded_hosts = value.get("expanded_hosts", ())
    if allowed_hosts and expanded_hosts:
        return not set(map(str.lower, expanded_hosts)).issubset(set(map(str.lower, allowed_hosts)))
    return False


def _output_paths(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, PurePath)):
        return (str(value),)
    if isinstance(value, Sequence):
        return tuple(str(item) for item in value)
    return ()


def _looks_like_raw_output_path(path: str) -> bool:
    lowered = path.replace("\\", "/").lower()
    pure = PurePath(lowered)
    if pure.suffix in _RAW_FILE_SUFFIXES:
        return True
    parts = set(pure.parts)
    return any(marker in parts for marker in _RAW_PATH_MARKERS)
