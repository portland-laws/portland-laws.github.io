#!/usr/bin/env python3
"""Bounded public crawl dry-run for PP&D source discovery."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .crawl_policy import DEFAULT_ALLOWLIST_PATH, CrawlPolicy, PreflightDecision
from .robots import RobotsPolicy


DEFAULT_SEED_MANIFEST_PATH = Path(__file__).with_name("seed_manifest.json")
DEFAULT_USER_AGENT = "ppd-public-crawler-dry-run/1.0"
TINY_SEED_FETCH_LIMIT = 2
MAX_BODY_BYTES = 128 * 1024


@dataclass(frozen=True)
class FetchResponse:
    url: str
    status_code: int
    content_type: str
    body: bytes
    headers: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class PublicCrawlDryRunItem:
    seed_id: str
    url: str
    status: str
    reason_code: str
    preflight_reason: str = ""
    robots_reason: str = ""
    content_type: str = ""
    title: Optional[str] = None
    content_hash: Optional[str] = None
    bytes_read: int = 0

    def to_dict(self) -> dict[str, object]:
        return {
            "seed_id": self.seed_id,
            "url": self.url,
            "status": self.status,
            "reason_code": self.reason_code,
            "preflight_reason": self.preflight_reason,
            "robots_reason": self.robots_reason,
            "content_type": self.content_type,
            "title": self.title,
            "content_hash": self.content_hash,
            "bytes_read": self.bytes_read,
        }


@dataclass(frozen=True)
class PublicCrawlDryRunReport:
    items: tuple[PublicCrawlDryRunItem, ...]
    max_seed_fetches: int
    attempted_seed_count: int

    @property
    def fetched_seed_count(self) -> int:
        return sum(1 for item in self.items if item.status == "fetched")

    @property
    def skipped_seed_count(self) -> int:
        return sum(1 for item in self.items if item.status == "skipped")

    def to_dict(self) -> dict[str, object]:
        return {
            "mode": "bounded_public_crawl_dry_run",
            "max_seed_fetches": self.max_seed_fetches,
            "attempted_seed_count": self.attempted_seed_count,
            "fetched_seed_count": self.fetched_seed_count,
            "skipped_seed_count": self.skipped_seed_count,
            "items": [item.to_dict() for item in self.items],
        }


class _TitleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._in_title = False
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        if tag.lower() == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._parts.append(data)

    @property
    def title(self) -> Optional[str]:
        normalized = " ".join("".join(self._parts).split())
        return normalized or None


def extract_html_title(body: bytes, content_type: str) -> Optional[str]:
    if "html" not in content_type.lower():
        return None
    parser = _TitleParser()
    parser.feed(body[:MAX_BODY_BYTES].decode("utf-8", errors="replace"))
    return parser.title


def default_fetcher(
    url: str,
    *,
    user_agent: str = DEFAULT_USER_AGENT,
    max_body_bytes: int = MAX_BODY_BYTES,
) -> FetchResponse:
    request = Request(url, headers={"User-Agent": user_agent})
    with urlopen(request, timeout=20) as response:  # nosec B310 - caller preflights allowlisted public URLs.
        body = response.read(max_body_bytes + 1)[:max_body_bytes]
        headers = {str(key).lower(): str(value) for key, value in response.headers.items()}
        return FetchResponse(
            url=response.geturl(),
            status_code=int(response.status),
            content_type=headers.get("content-type", ""),
            body=body,
            headers=headers,
        )


def load_seed_urls(path: Path = DEFAULT_SEED_MANIFEST_PATH) -> list[dict[str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    seeds = data.get("seeds", [])
    if not isinstance(seeds, list):
        raise ValueError("seed manifest must contain a seeds array")
    normalized: list[dict[str, str]] = []
    for seed in seeds:
        if not isinstance(seed, dict):
            continue
        seed_id = seed.get("id")
        url = seed.get("url")
        if isinstance(seed_id, str) and isinstance(url, str):
            normalized.append({"id": seed_id, "url": url})
    return normalized


def _robots_url_for(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/robots.txt"


def _skip(seed: dict[str, str], decision: PreflightDecision) -> PublicCrawlDryRunItem:
    return PublicCrawlDryRunItem(
        seed_id=seed["id"],
        url=seed["url"],
        status="skipped",
        reason_code=decision.reason_code,
        preflight_reason=decision.reason_code,
        robots_reason=str(decision.details.get("robots_reason", "")),
    )


def run_public_crawl_dry_run(
    *,
    seed_manifest_path: Path = DEFAULT_SEED_MANIFEST_PATH,
    allowlist_path: Path = DEFAULT_ALLOWLIST_PATH,
    max_seed_fetches: int = TINY_SEED_FETCH_LIMIT,
    fetcher: Optional[Callable[[str], FetchResponse]] = None,
    robots_text_by_host: Optional[dict[str, str]] = None,
    user_agent: str = DEFAULT_USER_AGENT,
) -> PublicCrawlDryRunReport:
    bounded_limit = max(0, min(int(max_seed_fetches), TINY_SEED_FETCH_LIMIT))
    seeds = load_seed_urls(seed_manifest_path)[:bounded_limit]
    policy = CrawlPolicy.load(allowlist_path)
    active_fetcher = fetcher or (lambda url: default_fetcher(url, user_agent=user_agent))
    robots_cache = dict(robots_text_by_host or {})
    items: list[PublicCrawlDryRunItem] = []

    for seed in seeds:
        url = seed["url"]
        host = urlparse(url).netloc.lower()
        initial = policy.preflight(url, user_agent=user_agent)
        if not initial.allowed:
            items.append(_skip(seed, initial))
            continue

        if host not in robots_cache:
            try:
                robots_cache[host] = active_fetcher(_robots_url_for(url)).body.decode("utf-8", errors="replace")
            except Exception as exc:  # pragma: no cover - live network failure path.
                items.append(
                    PublicCrawlDryRunItem(
                        seed_id=seed["id"],
                        url=url,
                        status="skipped",
                        reason_code="robots_unavailable",
                        preflight_reason="allowed",
                        robots_reason=str(exc),
                    )
                )
                continue

        robots_policy = RobotsPolicy.from_text(robots_cache[host])
        preflight = policy.preflight(url, robots_policy=robots_policy, user_agent=user_agent)
        if not preflight.allowed:
            items.append(_skip(seed, preflight))
            continue

        response = active_fetcher(url)
        content_preflight = policy.preflight(
            url,
            content_type=response.content_type,
            robots_policy=robots_policy,
            user_agent=user_agent,
        )
        if not content_preflight.allowed:
            items.append(_skip(seed, content_preflight))
            continue

        body = response.body[:MAX_BODY_BYTES]
        items.append(
            PublicCrawlDryRunItem(
                seed_id=seed["id"],
                url=url,
                status="fetched",
                reason_code="fetched",
                preflight_reason=preflight.reason_code,
                robots_reason=str(preflight.details.get("robots_reason", "")),
                content_type=response.content_type.split(";", 1)[0].strip().lower(),
                title=extract_html_title(body, response.content_type),
                content_hash=f"sha256:{hashlib.sha256(body).hexdigest()}",
                bytes_read=len(body),
            )
        )

    return PublicCrawlDryRunReport(
        items=tuple(items),
        max_seed_fetches=bounded_limit,
        attempted_seed_count=len(seeds),
    )


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run a bounded PP&D public crawl dry-run.")
    parser.add_argument("--seed-manifest", default=str(DEFAULT_SEED_MANIFEST_PATH))
    parser.add_argument("--allowlist", default=str(DEFAULT_ALLOWLIST_PATH))
    parser.add_argument("--max-seeds", type=int, default=TINY_SEED_FETCH_LIMIT)
    parser.add_argument("--live", action="store_true", help="Permit live public HTTP fetches after preflight checks.")
    args = parser.parse_args(argv)
    if not args.live:
        print(json.dumps({"ok": False, "error": "pass --live to perform public HTTP fetches"}, indent=2))
        return 2
    report = run_public_crawl_dry_run(
        seed_manifest_path=Path(args.seed_manifest),
        allowlist_path=Path(args.allowlist),
        max_seed_fetches=args.max_seeds,
    )
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
