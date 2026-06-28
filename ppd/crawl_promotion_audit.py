"""Fixture-first crawl promotion audit for PP&D source candidates.

This module is intentionally small and dependency-free. It validates synthetic
fixtures before any public fetch can be considered eligible.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


REQUIRED_COLLECTIONS = (
    "source_registry",
    "discovery_decisions",
    "dry_run_crawl_plans",
    "robots_preflight",
    "processor_choices",
    "rate_limit_buckets",
    "output_policies",
)


@dataclass(frozen=True)
class CrawlPromotionAuditRow:
    source_id: str
    eligible: bool
    reasons: tuple[str, ...]
    rate_limit_bucket: str | None
    processor: str | None
    metadata_only: bool


def _index_by_source_id(records: list[Mapping[str, Any]], collection: str) -> dict[str, Mapping[str, Any]]:
    indexed: dict[str, Mapping[str, Any]] = {}
    for record in records:
        source_id = record.get("source_id")
        if not isinstance(source_id, str) or not source_id:
            raise ValueError(f"{collection} contains a record without a non-empty source_id")
        if source_id in indexed:
            raise ValueError(f"{collection} contains duplicate source_id {source_id!r}")
        indexed[source_id] = record
    return indexed


def audit_fixture_records(fixture: Mapping[str, Any]) -> list[CrawlPromotionAuditRow]:
    """Join fixture records and decide public-fetch eligibility.

    The input must contain only synthetic records. A source is eligible only when
    every joined gate explicitly allows a metadata-only dry-run promotion.
    """

    if fixture.get("fixture_kind") != "synthetic_crawl_promotion_audit":
        raise ValueError("fixture_kind must be synthetic_crawl_promotion_audit")

    indexed: dict[str, dict[str, Mapping[str, Any]]] = {}
    for collection in REQUIRED_COLLECTIONS:
        records = fixture.get(collection)
        if not isinstance(records, list):
            raise ValueError(f"{collection} must be a list")
        indexed[collection] = _index_by_source_id(records, collection)

    source_ids = sorted(indexed["source_registry"])
    rows: list[CrawlPromotionAuditRow] = []

    for source_id in source_ids:
        reasons: list[str] = []
        joined: dict[str, Mapping[str, Any] | None] = {
            collection: indexed[collection].get(source_id) for collection in REQUIRED_COLLECTIONS
        }

        missing = [name for name, record in joined.items() if record is None]
        if missing:
            reasons.append("missing joined records: " + ", ".join(missing))

        registry = joined["source_registry"] or {}
        discovery = joined["discovery_decisions"] or {}
        plan = joined["dry_run_crawl_plans"] or {}
        preflight = joined["robots_preflight"] or {}
        processor = joined["processor_choices"] or {}
        bucket = joined["rate_limit_buckets"] or {}
        policy = joined["output_policies"] or {}

        if registry.get("synthetic") is not True:
            reasons.append("source registry record is not marked synthetic")
        if registry.get("status") != "active":
            reasons.append("source registry status is not active")
        if registry.get("public_source") is not True:
            reasons.append("source is not marked public_source")

        if discovery.get("decision") != "promote":
            reasons.append("discovery decision is not promote")
        if discovery.get("fixture_only") is not True:
            reasons.append("discovery decision is not fixture-only")

        if plan.get("mode") != "dry_run":
            reasons.append("crawl plan is not dry_run")
        if plan.get("would_fetch_public_url") is not True:
            reasons.append("crawl plan does not identify a public URL candidate")
        if plan.get("live_fetch_performed") is not False:
            reasons.append("crawl plan must prove no live fetch was performed")

        if preflight.get("robots_allowed") is not True:
            reasons.append("robots preflight does not allow fetch")
        if preflight.get("preflight_status") != "passed":
            reasons.append("preflight status is not passed")

        if processor.get("capability") not in {"html_metadata", "pdf_metadata", "api_metadata"}:
            reasons.append("processor capability is not metadata-capable")
        if processor.get("selected") is not True:
            reasons.append("processor choice is not selected")

        if not isinstance(bucket.get("bucket_id"), str) or not bucket.get("bucket_id"):
            reasons.append("rate-limit bucket_id is missing")
        if bucket.get("eligible_for_public_fetch") is not True:
            reasons.append("rate-limit bucket is not eligible for public fetch")

        metadata_only = policy.get("metadata_only") is True
        if not metadata_only:
            reasons.append("output policy is not metadata-only")
        if policy.get("store_raw_document") is not False:
            reasons.append("output policy must reject raw document storage")
        if policy.get("emit_public_fetch") is not True:
            reasons.append("output policy does not permit public fetch emission")

        rows.append(
            CrawlPromotionAuditRow(
                source_id=source_id,
                eligible=not reasons,
                reasons=tuple(reasons),
                rate_limit_bucket=bucket.get("bucket_id") if isinstance(bucket.get("bucket_id"), str) else None,
                processor=processor.get("capability") if isinstance(processor.get("capability"), str) else None,
                metadata_only=metadata_only,
            )
        )

    return rows


def eligible_source_ids(fixture: Mapping[str, Any]) -> list[str]:
    """Return source ids that pass every crawl promotion gate."""

    return [row.source_id for row in audit_fixture_records(fixture) if row.eligible]
