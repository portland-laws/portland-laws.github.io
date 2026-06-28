"""Deterministic public crawl batch-plan normalization for PP&D.

This module intentionally performs no network I/O. It accepts committed seed
fixtures or in-memory seed dictionaries and returns a normalized batch plan that
can be validated before any crawler or processor is allowed to run.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import ParseResult, parse_qsl, urlencode, urlparse, urlunparse


ALLOWED_PUBLIC_HOSTS: frozenset[str] = frozenset(
    {
        "www.portland.gov",
        "devhub.portlandoregon.gov",
        "www.portlandoregon.gov",
        "www.portlandmaps.com",
    }
)

PRIVATE_PATH_MARKERS: tuple[str, ...] = (
    "/login",
    "/signin",
    "/sign-in",
    "/register",
    "/account",
    "/accounts",
    "/dashboard",
    "/my-permits",
    "/mypermits",
    "/payments",
    "/checkout",
    "/upload",
    "/submit",
)

PDF_EXTENSIONS: tuple[str, ...] = (".pdf",)
SUPPORTED_SCHEMES: frozenset[str] = frozenset({"http", "https"})


@dataclass(frozen=True)
class PublicCrawlSeed:
    """A public crawl seed from a committed fixture or a caller."""

    url: str
    label: str = ""
    source_page: str = ""
    source_kind: str = "seed"


def load_seed_fixture(path: str | Path) -> list[dict[str, Any]]:
    """Load crawl seeds from a committed JSON fixture without fetching URLs."""

    fixture_path = Path(path)
    with fixture_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, dict):
        seeds = payload.get("seeds", [])
    else:
        seeds = payload
    if not isinstance(seeds, list):
        raise ValueError("public crawl seed fixture must contain a list of seeds")
    return seeds


def normalize_public_crawl_batch_plan(seeds: Iterable[dict[str, Any] | PublicCrawlSeed]) -> dict[str, Any]:
    """Return a deterministic PP&D public crawl batch plan.

    The result is metadata only. It never contains raw bodies, downloaded PDF
    content, credentials, browser state, or authenticated page data.
    """

    records_by_url: dict[str, dict[str, Any]] = {}
    skipped_duplicates: list[dict[str, str]] = []

    for index, raw_seed in enumerate(seeds):
        seed = _coerce_seed(raw_seed)
        canonical_url = canonicalize_public_url(seed.url)
        if canonical_url in records_by_url:
            skipped_duplicates.append(
                {
                    "canonical_url": canonical_url,
                    "skipped_reason": "duplicate_canonical_url",
                }
            )
            continue
        records_by_url[canonical_url] = _normalize_seed(index=index, seed=seed, canonical_url=canonical_url)

    records = sorted(records_by_url.values(), key=lambda record: record["canonical_url"])
    return {
        "plan_version": "ppd-public-crawl-batch-plan-v1",
        "network_io_permitted": False,
        "raw_body_persistence_permitted": False,
        "allowed_hosts": sorted(ALLOWED_PUBLIC_HOSTS),
        "records": records,
        "skipped_duplicates": skipped_duplicates,
        "summary": _summarize(records, skipped_duplicates),
    }


def canonicalize_public_url(url: str) -> str:
    """Canonicalize enough for deterministic fixture validation."""

    parsed = urlparse(url.strip())
    scheme = parsed.scheme.lower() or "https"
    host = (parsed.hostname or "").lower()
    netloc = host
    if parsed.port is not None:
        netloc = f"{host}:{parsed.port}"
    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/")
    query_pairs = sorted(parse_qsl(parsed.query, keep_blank_values=True))
    query = urlencode(query_pairs, doseq=True)
    canonical = ParseResult(
        scheme=scheme,
        netloc=netloc,
        path=path,
        params="",
        query=query,
        fragment="",
    )
    return urlunparse(canonical)


def _coerce_seed(raw_seed: dict[str, Any] | PublicCrawlSeed) -> PublicCrawlSeed:
    if isinstance(raw_seed, PublicCrawlSeed):
        return raw_seed
    if not isinstance(raw_seed, dict):
        raise TypeError("public crawl seed must be a dict or PublicCrawlSeed")
    url = str(raw_seed.get("url", "")).strip()
    if not url:
        raise ValueError("public crawl seed is missing url")
    return PublicCrawlSeed(
        url=url,
        label=str(raw_seed.get("label", "")),
        source_page=str(raw_seed.get("source_page", "")),
        source_kind=str(raw_seed.get("source_kind", "seed")),
    )


def _normalize_seed(index: int, seed: PublicCrawlSeed, canonical_url: str) -> dict[str, Any]:
    parsed = urlparse(canonical_url)
    skip_reason = _skip_reason(parsed)
    decision = "skip" if skip_reason else "include"
    source_type = _source_type(parsed)
    return {
        "batch_item_id": f"public-seed-{index:04d}",
        "canonical_url": canonical_url,
        "requested_url": seed.url,
        "label": seed.label,
        "source_page": seed.source_page,
        "source_kind": seed.source_kind,
        "host": parsed.hostname or "",
        "source_type": source_type,
        "decision": decision,
        "skipped_reason": skip_reason,
        "crawl_frequency": _crawl_frequency(canonical_url, source_type),
        "processor_policy": "metadata_and_normalized_text_only",
        "privacy_classification": "public",
        "requires_authentication": bool(skip_reason == "private_or_authenticated"),
        "fetch_mode": "not_fetched_fixture_plan_only",
        "no_raw_body_persisted": True,
        "raw_body_ref": None,
    }


def _skip_reason(parsed: ParseResult) -> str | None:
    host = parsed.hostname or ""
    path = parsed.path.lower()
    if parsed.scheme not in SUPPORTED_SCHEMES:
        return "unsupported_scheme"
    if host not in ALLOWED_PUBLIC_HOSTS:
        return "outside_allowlist"
    if host == "www.portlandmaps.com" and "/advanced/" in path:
        return "private_or_authenticated"
    if any(marker in path for marker in PRIVATE_PATH_MARKERS):
        return "private_or_authenticated"
    return None


def _source_type(parsed: ParseResult) -> str:
    host = parsed.hostname or ""
    path = parsed.path.lower()
    if path.endswith(PDF_EXTENSIONS) or path.endswith("/download"):
        return "public_pdf"
    if host == "devhub.portlandoregon.gov":
        return "devhub_public"
    if host == "www.portlandmaps.com":
        return "external_reference"
    return "public_html"


def _crawl_frequency(canonical_url: str, source_type: str) -> str:
    if source_type == "devhub_public":
        return "daily_or_every_few_days"
    if "devhub" in canonical_url or "submit-permit" in canonical_url or "how-pay-fees" in canonical_url:
        return "daily_or_every_few_days"
    if source_type == "public_pdf":
        return "monthly_unless_linked_page_changed"
    return "weekly"


def _summarize(records: list[dict[str, Any]], skipped_duplicates: list[dict[str, str]]) -> dict[str, int]:
    included = sum(1 for record in records if record["decision"] == "include")
    skipped = len(records) - included
    return {
        "total_unique_records": len(records),
        "included_records": included,
        "skipped_records": skipped,
        "duplicate_records": len(skipped_duplicates),
    }


__all__ = [
    "ALLOWED_PUBLIC_HOSTS",
    "PublicCrawlSeed",
    "canonicalize_public_url",
    "load_seed_fixture",
    "normalize_public_crawl_batch_plan",
]
