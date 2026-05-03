"""Bounded live public scraping for PP&D public sources.

This module is the execution-facing wrapper around the existing public dry-run
crawler. It can perform live HTTP fetches only when explicitly enabled by the
caller, and it records metadata summaries rather than raw response bodies or
downloaded source documents.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from .crawl_policy import DEFAULT_ALLOWLIST_PATH
from .public_dry_run import (
    DEFAULT_SEED_MANIFEST_PATH,
    DEFAULT_USER_AGENT,
    FetchResponse,
    PublicCrawlDryRunReport,
    run_public_crawl_dry_run,
)


LIVE_PUBLIC_SCRAPE_MODE = "bounded_live_public_scrape"


@dataclass(frozen=True)
class LivePublicScrapePolicy:
    allow_live_network: bool = False
    persist_raw_outputs: bool = False
    max_seed_fetches: int = 2
    user_agent: str = DEFAULT_USER_AGENT

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.allow_live_network:
            errors.append("live public scraping requires allow_live_network=True")
        if self.persist_raw_outputs:
            errors.append("live public scraping must not persist raw outputs")
        if self.max_seed_fetches < 1 or self.max_seed_fetches > 2:
            errors.append("live public scraping max_seed_fetches must be between 1 and 2")
        if not self.user_agent.strip():
            errors.append("live public scraping requires a user agent")
        return errors


@dataclass(frozen=True)
class LivePublicScrapeResult:
    mode: str
    allowed: bool
    status: str
    report: Optional[PublicCrawlDryRunReport]
    errors: tuple[str, ...]
    raw_outputs_persisted: bool = False
    downloaded_documents_persisted: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "mode": self.mode,
            "allowed": self.allowed,
            "status": self.status,
            "rawOutputsPersisted": self.raw_outputs_persisted,
            "downloadedDocumentsPersisted": self.downloaded_documents_persisted,
            "errors": list(self.errors),
            "report": None if self.report is None else self.report.to_dict(),
        }


def run_live_public_scrape(
    *,
    seed_manifest_path: Path = DEFAULT_SEED_MANIFEST_PATH,
    allowlist_path: Path = DEFAULT_ALLOWLIST_PATH,
    policy: LivePublicScrapePolicy,
    fetcher: Optional[Callable[[str], FetchResponse]] = None,
    robots_text_by_host: Optional[dict[str, str]] = None,
) -> LivePublicScrapeResult:
    """Run a tiny live public scrape after fail-closed policy validation."""

    policy_errors = policy.validate()
    if policy_errors:
        return LivePublicScrapeResult(
            mode=LIVE_PUBLIC_SCRAPE_MODE,
            allowed=False,
            status="refused_by_policy",
            report=None,
            errors=tuple(policy_errors),
        )

    try:
        report = run_public_crawl_dry_run(
            seed_manifest_path=seed_manifest_path,
            allowlist_path=allowlist_path,
            max_seed_fetches=policy.max_seed_fetches,
            fetcher=fetcher,
            robots_text_by_host=robots_text_by_host,
            user_agent=policy.user_agent,
        )
    except Exception as exc:
        return LivePublicScrapeResult(
            mode=LIVE_PUBLIC_SCRAPE_MODE,
            allowed=True,
            status="failed",
            report=None,
            errors=(str(exc),),
        )

    return LivePublicScrapeResult(
        mode=LIVE_PUBLIC_SCRAPE_MODE,
        allowed=True,
        status="completed",
        report=report,
        errors=(),
        raw_outputs_persisted=False,
        downloaded_documents_persisted=False,
    )


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run a bounded live PP&D public scrape.")
    parser.add_argument("--seed-manifest", default=str(DEFAULT_SEED_MANIFEST_PATH))
    parser.add_argument("--allowlist", default=str(DEFAULT_ALLOWLIST_PATH))
    parser.add_argument("--max-seeds", type=int, default=1)
    parser.add_argument("--live", action="store_true", help="Explicitly permit live public HTTP fetches.")
    args = parser.parse_args(argv)
    result = run_live_public_scrape(
        seed_manifest_path=Path(args.seed_manifest),
        allowlist_path=Path(args.allowlist),
        policy=LivePublicScrapePolicy(
            allow_live_network=bool(args.live),
            persist_raw_outputs=False,
            max_seed_fetches=int(args.max_seeds),
        ),
    )
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0 if result.status == "completed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
