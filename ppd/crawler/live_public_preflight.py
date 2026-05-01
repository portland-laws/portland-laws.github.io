"""Live public crawl readiness preflight without fetching or persistence."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from .crawl_policy import DEFAULT_ALLOWLIST_PATH, CrawlPolicy
from .public_dry_run import DEFAULT_SEED_MANIFEST_PATH, DEFAULT_USER_AGENT, TINY_SEED_FETCH_LIMIT, load_seed_urls
from .robots import RobotsPolicy


MIN_TIMEOUT_SECONDS = 1
MAX_TIMEOUT_SECONDS = 30
DEFAULT_TIMEOUT_SECONDS = 10


@dataclass(frozen=True)
class LivePublicPreflightItem:
    seed_id: str
    url: str
    eligible: bool
    reason_code: str
    host: str
    timeout_seconds: int
    no_persist: bool = True
    details: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "seed_id": self.seed_id,
            "url": self.url,
            "eligible": self.eligible,
            "reason_code": self.reason_code,
            "host": self.host,
            "timeout_seconds": self.timeout_seconds,
            "no_persist": self.no_persist,
            "details": self.details,
        }


@dataclass(frozen=True)
class LivePublicPreflightReport:
    mode: str
    seed_limit: int
    timeout_seconds: int
    no_persist: bool
    items: tuple[LivePublicPreflightItem, ...]

    @property
    def eligible_count(self) -> int:
        return sum(1 for item in self.items if item.eligible)

    @property
    def skipped_count(self) -> int:
        return sum(1 for item in self.items if not item.eligible)

    def to_dict(self) -> dict[str, object]:
        return {
            "mode": self.mode,
            "seed_limit": self.seed_limit,
            "timeout_seconds": self.timeout_seconds,
            "no_persist": self.no_persist,
            "eligible_count": self.eligible_count,
            "skipped_count": self.skipped_count,
            "items": [item.to_dict() for item in self.items],
        }


def bounded_timeout_seconds(value: int) -> int:
    return max(MIN_TIMEOUT_SECONDS, min(int(value), MAX_TIMEOUT_SECONDS))


def build_live_public_preflight_report(
    *,
    seed_manifest_path: Path = DEFAULT_SEED_MANIFEST_PATH,
    allowlist_path: Path = DEFAULT_ALLOWLIST_PATH,
    robots_text_by_host: Optional[dict[str, str]] = None,
    seed_limit: int = TINY_SEED_FETCH_LIMIT,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    no_persist: bool = True,
    user_agent: str = DEFAULT_USER_AGENT,
) -> LivePublicPreflightReport:
    bounded_seed_limit = max(0, min(int(seed_limit), TINY_SEED_FETCH_LIMIT))
    bounded_timeout = bounded_timeout_seconds(timeout_seconds)
    policy = CrawlPolicy.load(allowlist_path)
    seeds = load_seed_urls(seed_manifest_path)[:bounded_seed_limit]
    robots_map = robots_text_by_host or {}
    items: list[LivePublicPreflightItem] = []

    for seed in seeds:
        url = seed["url"]
        host = urlparse(url).netloc.lower()
        robots_text = robots_map.get(host)
        robots_policy = RobotsPolicy.from_text(robots_text) if robots_text is not None else None
        decision = policy.preflight(url, robots_policy=robots_policy, user_agent=user_agent)
        eligible = bool(decision.allowed and no_persist and MIN_TIMEOUT_SECONDS <= bounded_timeout <= MAX_TIMEOUT_SECONDS)
        reason_code = decision.reason_code
        details: dict[str, object] = dict(decision.details)
        if robots_text is None:
            eligible = False
            reason_code = "robots_required"
            details["robots_reason"] = "robots text must be supplied or checked before live fetch eligibility"
        if not no_persist:
            eligible = False
            reason_code = "persist_not_allowed"
            details["persist_reason"] = "live preflight only reports eligibility and must not persist crawl output"
        items.append(
            LivePublicPreflightItem(
                seed_id=seed["id"],
                url=url,
                eligible=eligible,
                reason_code=reason_code,
                host=host,
                timeout_seconds=bounded_timeout,
                no_persist=no_persist,
                details=details,
            )
        )

    return LivePublicPreflightReport(
        mode="live_public_crawl_preflight",
        seed_limit=bounded_seed_limit,
        timeout_seconds=bounded_timeout,
        no_persist=no_persist,
        items=tuple(items),
    )


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Report eligible tiny seed URLs for live PP&D public crawl preflight.")
    parser.add_argument("--seed-manifest", default=str(DEFAULT_SEED_MANIFEST_PATH))
    parser.add_argument("--allowlist", default=str(DEFAULT_ALLOWLIST_PATH))
    parser.add_argument("--robots-json", default="", help="Optional JSON object mapping host to robots.txt text.")
    parser.add_argument("--seed-limit", type=int, default=TINY_SEED_FETCH_LIMIT)
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    args = parser.parse_args(argv)
    robots_text_by_host = json.loads(args.robots_json) if args.robots_json else {}
    report = build_live_public_preflight_report(
        seed_manifest_path=Path(args.seed_manifest),
        allowlist_path=Path(args.allowlist),
        robots_text_by_host=robots_text_by_host,
        seed_limit=args.seed_limit,
        timeout_seconds=args.timeout_seconds,
        no_persist=True,
    )
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
