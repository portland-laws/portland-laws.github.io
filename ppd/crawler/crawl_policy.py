#!/usr/bin/env python3
"""Fail-closed crawl-policy preflight helpers for PP&D public discovery.

The helpers in this module are deterministic and side-effect free. They do not
fetch URLs, read cookies, open browser sessions, or inspect authenticated state.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

try:
    from .robots import RobotsPolicy
except ImportError:  # pragma: no cover - supports direct script-style imports.
    from robots import RobotsPolicy  # type: ignore


DEFAULT_ALLOWLIST_PATH = Path(__file__).with_name("allowlist.json")
PRIVATE_OR_CONSEQUENTIAL_TERMS = (
    "account",
    "cart",
    "checkout",
    "dashboard",
    "draft",
    "inspection",
    "login",
    "logout",
    "my-permits",
    "mypermits",
    "password",
    "payment",
    "profile",
    "register",
    "schedule",
    "sign-in",
    "signin",
    "submit",
    "upload",
)


@dataclass(frozen=True)
class PreflightDecision:
    allowed: bool
    reason_code: str
    url: str
    host: str = ""
    normalized_path: str = ""
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CrawlPolicy:
    allowlist: dict[str, Any]

    @classmethod
    def load(cls, path: Path = DEFAULT_ALLOWLIST_PATH) -> "CrawlPolicy":
        return cls(json.loads(path.read_text(encoding="utf-8")))

    @property
    def allowed_hosts(self) -> list[dict[str, Any]]:
        return list(self.allowlist.get("allowed_hosts", []))

    def host_policy(self, host: str) -> Optional[dict[str, Any]]:
        normalized = host.lower()
        for item in self.allowed_hosts:
            if str(item.get("host", "")).lower() == normalized:
                return item
        return None

    def preflight(
        self,
        url: str,
        *,
        content_type: Optional[str] = None,
        robots_policy: Optional[RobotsPolicy] = None,
        user_agent: str = "ppd-public-crawler",
    ) -> PreflightDecision:
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        path = parsed.path or "/"
        path_for_checks = path.lower()
        if parsed.query:
            path_for_checks = f"{path_for_checks}?{parsed.query.lower()}"

        if parsed.scheme != "https":
            return PreflightDecision(False, "scheme_not_https", url, host, path)

        policy = self.host_policy(host)
        if policy is None:
            return PreflightDecision(False, "host_not_allowlisted", url, host, path)

        if any(term in path_for_checks for term in PRIVATE_OR_CONSEQUENTIAL_TERMS):
            return PreflightDecision(False, "private_or_authenticated", url, host, path)

        for fragment in policy.get("disallowed_path_fragments", []):
            if str(fragment).lower() in path_for_checks:
                return PreflightDecision(False, "private_or_authenticated", url, host, path, {"fragment": fragment})

        prefixes = policy.get("allowed_path_prefixes", [])
        if prefixes and not any(path.startswith(str(prefix)) for prefix in prefixes):
            return PreflightDecision(False, "path_not_in_scope", url, host, path, {"allowed_path_prefixes": prefixes})

        if content_type:
            normalized_content_type = content_type.split(";", 1)[0].strip().lower()
            allowed_types = [str(item).lower() for item in policy.get("allowed_content_types", [])]
            if allowed_types and normalized_content_type not in allowed_types:
                return PreflightDecision(
                    False,
                    "content_type_not_allowed",
                    url,
                    host,
                    path,
                    {"content_type": normalized_content_type, "allowed_content_types": allowed_types},
                )

        if robots_policy is not None:
            robots_decision = robots_policy.can_fetch(url, user_agent=user_agent)
            if not robots_decision.allowed:
                details: dict[str, Any] = {"robots_reason": robots_decision.reason}
                if robots_decision.matched_rule is not None:
                    details["robots_rule"] = {
                        "directive": robots_decision.matched_rule.directive,
                        "path": robots_decision.matched_rule.path,
                        "line_number": robots_decision.matched_rule.line_number,
                    }
                return PreflightDecision(False, "robots_disallowed", url, host, path, details)

            details = {"robots_reason": robots_decision.reason}
            if robots_decision.crawl_delay is not None:
                details["crawl_delay_seconds"] = robots_decision.crawl_delay
            return PreflightDecision(True, "allowed", url, host, path, details)

        return PreflightDecision(True, "allowed", url, host, path)


def preflight_url(
    url: str,
    *,
    allowlist_path: Path = DEFAULT_ALLOWLIST_PATH,
    content_type: Optional[str] = None,
    robots_text: Optional[str] = None,
    user_agent: str = "ppd-public-crawler",
) -> PreflightDecision:
    robots_policy = RobotsPolicy.from_text(robots_text) if robots_text is not None else None
    return CrawlPolicy.load(allowlist_path).preflight(
        url,
        content_type=content_type,
        robots_policy=robots_policy,
        user_agent=user_agent,
    )
