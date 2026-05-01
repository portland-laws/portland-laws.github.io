#!/usr/bin/env python3
"""Deterministic robots.txt helpers for PP&D public source discovery.

This module intentionally performs no network access. Callers provide robots.txt
text captured by an approved fetch step, then use the parser to decide whether a
candidate public URL may be fetched.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Optional
from urllib.parse import quote, urlparse


@dataclass(frozen=True)
class RobotsRule:
    directive: str
    path: str
    line_number: int

    @property
    def is_allow(self) -> bool:
        return self.directive == "allow"

    @property
    def is_disallow(self) -> bool:
        return self.directive == "disallow"


@dataclass(frozen=True)
class RobotsGroup:
    user_agents: tuple[str, ...] = field(default_factory=tuple)
    rules: tuple[RobotsRule, ...] = field(default_factory=tuple)
    crawl_delay: Optional[float] = None

    def matches(self, user_agent: str) -> bool:
        normalized = user_agent.lower()
        for candidate in self.user_agents:
            agent = candidate.lower()
            if agent == "*" or agent in normalized:
                return True
        return False

    @property
    def specificity(self) -> int:
        if not self.user_agents:
            return 0
        if "*" in self.user_agents:
            return 1
        return max(len(agent) for agent in self.user_agents)


@dataclass(frozen=True)
class RobotsDecision:
    allowed: bool
    reason: str
    matched_rule: Optional[RobotsRule] = None
    crawl_delay: Optional[float] = None


@dataclass(frozen=True)
class RobotsPolicy:
    groups: tuple[RobotsGroup, ...] = field(default_factory=tuple)
    sitemaps: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_text(cls, text: str) -> "RobotsPolicy":
        groups: list[RobotsGroup] = []
        sitemaps: list[str] = []
        current_agents: list[str] = []
        current_rules: list[RobotsRule] = []
        current_delay: Optional[float] = None
        saw_rule = False

        def flush_group() -> None:
            nonlocal current_agents, current_rules, current_delay, saw_rule
            if current_agents:
                groups.append(
                    RobotsGroup(
                        user_agents=tuple(current_agents),
                        rules=tuple(current_rules),
                        crawl_delay=current_delay,
                    )
                )
            current_agents = []
            current_rules = []
            current_delay = None
            saw_rule = False

        for line_number, raw_line in enumerate(text.splitlines(), start=1):
            line = raw_line.split("#", 1)[0].strip()
            if not line or ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.strip().lower()
            value = value.strip()

            if key == "sitemap" and value:
                sitemaps.append(value)
                continue

            if key == "user-agent":
                if saw_rule:
                    flush_group()
                if value:
                    current_agents.append(value.lower())
                continue

            if key in {"allow", "disallow"}:
                saw_rule = True
                current_rules.append(RobotsRule(directive=key, path=value, line_number=line_number))
                continue

            if key == "crawl-delay" and value:
                saw_rule = True
                try:
                    current_delay = float(value)
                except ValueError:
                    current_delay = None

        flush_group()
        return cls(groups=tuple(groups), sitemaps=tuple(sitemaps))

    def group_for(self, user_agent: str) -> Optional[RobotsGroup]:
        matches = [group for group in self.groups if group.matches(user_agent)]
        if not matches:
            return None
        return max(matches, key=lambda group: group.specificity)

    def can_fetch(self, url: str, user_agent: str = "ppd-public-crawler") -> RobotsDecision:
        group = self.group_for(user_agent) or self.group_for("*")
        if group is None:
            return RobotsDecision(allowed=True, reason="robots_no_matching_group")

        parsed = urlparse(url)
        candidate_path = parsed.path or "/"
        if parsed.query:
            candidate_path = f"{candidate_path}?{parsed.query}"
        encoded_path = quote(candidate_path, safe="/%?=&;:+,$-_.!~*'()")

        matching_rules = [
            rule
            for rule in group.rules
            if rule.path and (candidate_path.startswith(rule.path) or encoded_path.startswith(rule.path))
        ]
        if not matching_rules:
            return RobotsDecision(
                allowed=True,
                reason="robots_no_matching_rule",
                crawl_delay=group.crawl_delay,
            )

        matched = max(matching_rules, key=lambda rule: (len(rule.path), 1 if rule.is_allow else 0))
        if matched.is_disallow:
            return RobotsDecision(
                allowed=False,
                reason="robots_disallowed",
                matched_rule=matched,
                crawl_delay=group.crawl_delay,
            )
        return RobotsDecision(
            allowed=True,
            reason="robots_allowed",
            matched_rule=matched,
            crawl_delay=group.crawl_delay,
        )


def policy_from_lines(lines: Iterable[str]) -> RobotsPolicy:
    return RobotsPolicy.from_text("\n".join(lines))
