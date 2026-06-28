"""Build fixture-first post-recrawl metadata review packets.

The packet intentionally keeps only crawl metadata. It does not store page bodies,
PDF bytes, or raw downloaded documents.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any

_METADATA_FIELDS = (
    "status_code",
    "content_hash",
    "normalized_document_ref",
    "skipped_reason",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _stable_id(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()[:16]


def normalize_document_ref(value: Any) -> str | None:
    """Normalize document references for deterministic metadata comparison."""
    if value is None:
        return None
    text = str(value).strip().lower()
    if not text:
        return None
    return " ".join(text.replace("_", "-").split())


def _by_url(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        url = str(row.get("url", "")).strip()
        if not url:
            raise ValueError("manifest rows must include a non-empty url")
        indexed[url] = row
    return indexed


def _metadata(row: dict[str, Any] | None) -> dict[str, Any]:
    if row is None:
        return {field: None for field in _METADATA_FIELDS}
    return {
        "status_code": row.get("status_code"),
        "content_hash": row.get("content_hash"),
        "normalized_document_ref": normalize_document_ref(row.get("document_ref")),
        "skipped_reason": row.get("skipped_reason"),
    }


def _changed_fields(expected: dict[str, Any], observed: dict[str, Any]) -> list[str]:
    return [field for field in _METADATA_FIELDS if expected.get(field) != observed.get(field)]


def build_post_recrawl_metadata_review_packet(delta: dict[str, Any]) -> dict[str, Any]:
    """Compare synthetic archive manifest deltas and return a review packet."""
    expected_rows = deepcopy(delta.get("expected", []))
    observed_rows = deepcopy(delta.get("observed", []))
    previous_sources = deepcopy(delta.get("previous_sources", {}))
    current_sources = deepcopy(delta.get("current_sources", {}))

    if not isinstance(expected_rows, list) or not isinstance(observed_rows, list):
        raise TypeError("expected and observed manifest entries must be lists")
    if not isinstance(previous_sources, dict) or not isinstance(current_sources, dict):
        raise TypeError("source freshness maps must be objects")

    expected_by_url = _by_url(expected_rows)
    observed_by_url = _by_url(observed_rows)
    all_urls = sorted(set(expected_by_url) | set(observed_by_url))

    comparisons: list[dict[str, Any]] = []
    invalidation_candidates: list[dict[str, Any]] = []

    for url in all_urls:
        expected = _metadata(expected_by_url.get(url))
        observed = _metadata(observed_by_url.get(url))
        expected_present = url in expected_by_url
        observed_present = url in observed_by_url
        changed = _changed_fields(expected, observed)

        if not expected_present:
            outcome = "unexpected_observed"
        elif not observed_present:
            outcome = "missing_observed"
        elif changed:
            outcome = "metadata_changed"
        else:
            outcome = "matched"

        comparison = {
            "url": url,
            "expected_present": expected_present,
            "observed_present": observed_present,
            "outcome": outcome,
            "changed_fields": changed,
            "expected": expected,
            "observed": observed,
        }
        comparisons.append(comparison)

        invalidating_fields = [
            field for field in changed if field in {"status_code", "content_hash", "normalized_document_ref"}
        ]
        if invalidating_fields or outcome in {"unexpected_observed", "missing_observed"}:
            invalidation_candidates.append(
                {
                    "candidate_id": _stable_id(url),
                    "url": url,
                    "reason": outcome,
                    "fields": invalidating_fields or changed,
                }
            )

    freshness_updates: list[dict[str, Any]] = []
    for source_id in sorted(set(previous_sources) | set(current_sources)):
        previous = previous_sources.get(source_id)
        current = current_sources.get(source_id)
        if previous != current:
            freshness_updates.append(
                {
                    "source_id": source_id,
                    "previous_fetched_at": previous,
                    "current_fetched_at": current,
                    "changed": True,
                }
            )

    summary = {
        "expected_count": len(expected_rows),
        "observed_count": len(observed_rows),
        "matched_count": sum(1 for row in comparisons if row["outcome"] == "matched"),
        "metadata_changed_count": sum(1 for row in comparisons if row["outcome"] == "metadata_changed"),
        "missing_observed_count": sum(1 for row in comparisons if row["outcome"] == "missing_observed"),
        "unexpected_observed_count": sum(1 for row in comparisons if row["outcome"] == "unexpected_observed"),
        "source_freshness_update_count": len(freshness_updates),
        "downstream_invalidation_candidate_count": len(invalidation_candidates),
    }

    return {
        "packet_version": 1,
        "generated_at": str(delta.get("generated_at") or _utc_now()),
        "fixture_id": delta.get("fixture_id"),
        "privacy": {
            "stores_page_bodies": False,
            "stores_pdfs": False,
            "stores_downloaded_documents": False,
            "metadata_only": True,
        },
        "summary": summary,
        "comparisons": comparisons,
        "source_freshness_updates": freshness_updates,
        "downstream_invalidation_candidates": invalidation_candidates,
    }
