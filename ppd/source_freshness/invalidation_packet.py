"""Fixture-first source freshness invalidation packet builder.

The builder operates only on already-materialized metadata fixtures. It does not
fetch pages, store page bodies, accept downloaded documents, or mark downstream
guardrails current without review.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

PUBLIC_SOURCE_HOSTS = frozenset(
    {
        "www.portland.gov",
        "www.portlandoregon.gov",
        "www.portlandmaps.com",
        "devhub.portlandoregon.gov",
    }
)

RAW_BODY_KEYS = frozenset(
    {
        "body",
        "body_text",
        "content_body",
        "document_bytes",
        "document_text",
        "html",
        "page_body",
        "pdf_body",
        "pdf_bytes",
        "rawBody",
        "raw_body",
        "raw_crawl_output",
        "raw_html",
        "raw_page_body",
        "response_body",
        "text_content",
    }
)

PRIVATE_OR_ARTIFACT_KEYS = frozenset(
    {
        "auth_state",
        "cookie",
        "cookies",
        "credential",
        "credentials",
        "download_path",
        "downloadedDocumentPath",
        "downloaded_document",
        "downloaded_document_path",
        "downloaded_path",
        "har",
        "local_path",
        "password",
        "payment_details",
        "screenshot",
        "session_state",
        "storage_state",
        "trace",
    }
)

GUARDRAIL_CURRENT_CLAIM_KEYS = frozenset(
    {
        "guardrail_current",
        "guardrail_status",
        "guardrails_current",
        "guardrails_remain_current",
        "regenerated_guardrail_status",
        "regenerated_guardrails_marked_current",
    }
)

NETWORK_EVIDENCE_KEYS = frozenset(
    {
        "browser_evidence",
        "crawl_evidence",
        "fetch_result",
        "fetched_at",
        "live_evidence",
        "live_network_evidence",
        "network_evidence",
        "playwright_trace",
        "response_snapshot",
    }
)

FORBIDDEN_CURRENT_VALUES = frozenset(
    {
        "current",
        "guardrails_current",
        "review_not_required",
        "still_current",
        "validated_current",
    }
)

PRIVATE_URL_PATH_PARTS = (
    "/login",
    "/signin",
    "/sign-in",
    "/account",
    "/accounts",
    "/auth",
    "/dashboard",
    "/my-permits",
    "/permit/",
    "/permits/",
    "/private",
    "/secure",
)
LOCAL_PATH_PATTERN = re.compile(
    r"(^|\s)(file://|/home/|/users/|/tmp/|/var/folders/|[a-z]:\\\\users\\\\|[a-z]:\\\\temp\\\\)",
    re.IGNORECASE,
)
DOWNLOADED_DOCUMENT_PATTERN = re.compile(
    r"(downloads?/|downloaded[^\s]*\.(pdf|html?)|\.(pdf|html?)\s*$)",
    re.IGNORECASE,
)
RAW_BODY_VALUE_PATTERNS = (
    "",
    "%pdf-",
)


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object fixture at {path}")
    return data


def _assert_metadata_only(value: Any, path: str = "packet") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            key_lower = key_text.lower()
            if key_text in RAW_BODY_KEYS or key_lower in {item.lower() for item in RAW_BODY_KEYS}:
                raise ValueError(f"raw HTML/PDF body field is not allowed in freshness fixtures: {path}.{key_text}")
            if key_text in PRIVATE_OR_ARTIFACT_KEYS or key_lower in {item.lower() for item in PRIVATE_OR_ARTIFACT_KEYS}:
                raise ValueError(f"downloaded document path or private artifact field is not allowed: {path}.{key_text}")
            if key_text in NETWORK_EVIDENCE_KEYS or key_lower in {item.lower() for item in NETWORK_EVIDENCE_KEYS}:
                raise ValueError(f"live-network evidence field is not allowed in freshness fixtures: {path}.{key_text}")
            if key_lower == "network_requests_made" and child is not False:
                raise ValueError("freshness invalidation packets must not include live-network evidence")
            if key_lower in {"fixture_first", "metadata_only"} and child is False:
                raise ValueError("freshness invalidation packets must be metadata-only fixtures")
            if _claims_guardrails_current(key_text, child):
                raise ValueError("guardrails must not be claimed current without human review")
            _assert_metadata_only(child, f"{path}.{key_text}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_metadata_only(child, f"{path}[{index}]")
    elif isinstance(value, str):
        lowered = value.lower()
        if any(pattern in lowered for pattern in RAW_BODY_VALUE_PATTERNS):
            raise ValueError(f"raw HTML/PDF body content is not allowed in freshness fixtures: {path}")
        if LOCAL_PATH_PATTERN.search(value) or DOWNLOADED_DOCUMENT_PATTERN.search(value):
            raise ValueError(f"downloaded document path is not allowed in freshness fixtures: {path}")
        if _looks_private_or_authenticated_url(value):
            raise ValueError(f"private or authenticated URL is not allowed in freshness fixtures: {path}")
        if lowered in {"live_network", "live_browser", "live_crawl", "fetched_live"}:
            raise ValueError(f"live-network evidence marker is not allowed in freshness fixtures: {path}")


def _claims_guardrails_current(key: str, value: Any) -> bool:
    key_lower = key.lower()
    if key in GUARDRAIL_CURRENT_CLAIM_KEYS or key_lower in {item.lower() for item in GUARDRAIL_CURRENT_CLAIM_KEYS}:
        return value is True or (isinstance(value, str) and value.lower() in FORBIDDEN_CURRENT_VALUES)
    if key_lower in {"status", "validation_status"} and isinstance(value, str):
        return value.lower() in {"guardrails_current", "validated_current_without_review"}
    return False


def _looks_private_or_authenticated_url(value: str) -> bool:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False
    lowered_path = parsed.path.lower()
    lowered_query = parsed.query.lower()
    if parsed.netloc not in PUBLIC_SOURCE_HOSTS:
        return True
    if parsed.netloc == "devhub.portlandoregon.gov" and lowered_path not in {"", "/"}:
        return True
    if any(part in lowered_path for part in PRIVATE_URL_PATH_PARTS):
        return True
    return any(secret in lowered_query for secret in ("token=", "auth=", "session=", "password=", "code="))


def _as_sorted_unique(values: list[str]) -> list[str]:
    return sorted(set(values))


def _as_string_list(source: dict[str, Any], key: str) -> list[str]:
    value = source.get(key, [])
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        source_id = source.get("source_id", "")
        raise ValueError(f"source {source_id} requires {key} to be a list of non-empty strings")
    return value


def _changed_source_index(changed_hashes: dict[str, Any]) -> dict[str, dict[str, str]]:
    changed_sources = changed_hashes.get("changed_sources", [])
    if not isinstance(changed_sources, list):
        raise ValueError("changed_sources must be a list")

    indexed: dict[str, dict[str, str]] = {}
    for entry in changed_sources:
        if not isinstance(entry, dict):
            raise ValueError("changed source entries must be objects")
        source_id = entry.get("source_id")
        if not isinstance(source_id, str) or not source_id:
            raise ValueError("changed source entries require a source_id")
        if source_id in indexed:
            raise ValueError(f"changed source {source_id} appears more than once")
        new_hash = entry.get("new_content_hash")
        previous_hash = entry.get("previous_content_hash")
        if not isinstance(new_hash, str) or not isinstance(previous_hash, str):
            raise ValueError(f"changed source {source_id} requires previous and new content hashes")
        if not new_hash.startswith("sha256:") or not previous_hash.startswith("sha256:"):
            raise ValueError(f"changed source {source_id} requires sha256 content hashes")
        if new_hash == previous_hash:
            raise ValueError(f"changed source {source_id} is unactionable because hashes did not change")
        indexed[source_id] = {
            "previous_content_hash": previous_hash,
            "new_content_hash": new_hash,
            "detected_at": str(entry.get("detected_at", changed_hashes.get("detected_at", "fixture"))),
        }
    return indexed


def _validate_changed_source_is_actionable(source: dict[str, Any], change: dict[str, str]) -> None:
    source_id = source.get("source_id")
    current_hash = source.get("current_content_hash")
    if not isinstance(current_hash, str) or not current_hash.startswith("sha256:"):
        raise ValueError(f"changed source {source_id} requires a planned current_content_hash")
    if current_hash != change["previous_content_hash"]:
        raise ValueError(f"changed source {source_id} previous hash does not match recrawl plan current hash")

    dependency_keys = (
        "source_record_ids",
        "affected_requirement_ids",
        "affected_process_model_ids",
        "affected_guardrail_bundle_ids",
        "affected_agent_readiness_checklist_item_ids",
    )
    missing = [key for key in dependency_keys if not _as_string_list(source, key)]
    if missing:
        raise ValueError(f"changed source {source_id} is missing downstream dependency links: {', '.join(missing)}")


def _source_index(sources: list[Any]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for source in sources:
        if not isinstance(source, dict):
            raise ValueError("recrawl source entries must be objects")
        source_id = source.get("source_id")
        if not isinstance(source_id, str) or not source_id:
            raise ValueError("recrawl source entries require source_id")
        canonical_url = source.get("canonical_url")
        if not isinstance(canonical_url, str) or not canonical_url:
            raise ValueError(f"source {source_id} requires canonical_url")
        if _looks_private_or_authenticated_url(canonical_url):
            raise ValueError(f"source {source_id} uses a private or authenticated URL")
        indexed[source_id] = source
    return indexed


def build_invalidation_packet(
    recrawl_batch_plan: dict[str, Any],
    changed_hashes: dict[str, Any],
    *,
    generated_at: str = "2026-05-28T00:00:00Z",
) -> dict[str, Any]:
    """Build a deterministic invalidation packet from metadata-only fixtures."""

    _assert_metadata_only(recrawl_batch_plan)
    _assert_metadata_only(changed_hashes)

    sources = recrawl_batch_plan.get("sources", [])
    if not isinstance(sources, list):
        raise ValueError("recrawl batch plan sources must be a list")

    changed_by_source = _changed_source_index(changed_hashes)
    indexed_sources = _source_index(sources)
    unknown_changed_sources = sorted(set(changed_by_source) - set(indexed_sources))
    if unknown_changed_sources:
        raise ValueError(f"changed hash entries are unactionable for unknown sources: {', '.join(unknown_changed_sources)}")

    affected_sources: list[dict[str, Any]] = []
    affected_source_record_ids: list[str] = []
    affected_requirement_ids: list[str] = []
    affected_process_model_ids: list[str] = []
    affected_guardrail_bundle_ids: list[str] = []
    affected_checklist_item_ids: list[str] = []

    for source_id in sorted(changed_by_source):
        source = indexed_sources[source_id]
        change = changed_by_source[source_id]
        _validate_changed_source_is_actionable(source, change)

        source_record_ids = _as_string_list(source, "source_record_ids")
        requirement_ids = _as_string_list(source, "affected_requirement_ids")
        process_model_ids = _as_string_list(source, "affected_process_model_ids")
        guardrail_bundle_ids = _as_string_list(source, "affected_guardrail_bundle_ids")
        checklist_item_ids = _as_string_list(source, "affected_agent_readiness_checklist_item_ids")

        affected_sources.append(
            {
                "source_id": source_id,
                "canonical_url": source.get("canonical_url"),
                "source_type": source.get("source_type"),
                "owning_surface": source.get("owning_surface"),
                "crawl_frequency": source.get("crawl_frequency"),
                "freshness_watch_reason": source.get("freshness_watch_reason"),
                "previous_content_hash": change["previous_content_hash"],
                "planned_content_hash": source.get("current_content_hash"),
                "new_content_hash": change["new_content_hash"],
                "detected_at": change["detected_at"],
                "affected_source_record_ids": _as_sorted_unique(source_record_ids),
                "affected_requirement_ids": _as_sorted_unique(requirement_ids),
                "affected_process_model_ids": _as_sorted_unique(process_model_ids),
                "affected_guardrail_bundle_ids": _as_sorted_unique(guardrail_bundle_ids),
                "affected_agent_readiness_checklist_item_ids": _as_sorted_unique(checklist_item_ids),
                "invalidation_reason": "public source content hash changed",
                "guardrail_refresh_status": "blocked_pending_human_review",
            }
        )
        affected_source_record_ids.extend(source_record_ids)
        affected_requirement_ids.extend(requirement_ids)
        affected_process_model_ids.extend(process_model_ids)
        affected_guardrail_bundle_ids.extend(guardrail_bundle_ids)
        affected_checklist_item_ids.extend(checklist_item_ids)

    packet = {
        "packet_id": f"freshness-invalidation-{recrawl_batch_plan.get('batch_id', 'fixture')}",
        "generated_at": generated_at,
        "recrawl_batch_plan_id": recrawl_batch_plan.get("batch_id"),
        "source_hash_batch_id": changed_hashes.get("batch_id"),
        "fixture_first": True,
        "metadata_only": True,
        "network_requests_made": False,
        "raw_page_bodies_stored": False,
        "affected_sources": affected_sources,
        "affected_source_record_ids": _as_sorted_unique(affected_source_record_ids),
        "affected_requirement_ids": _as_sorted_unique(affected_requirement_ids),
        "affected_process_model_ids": _as_sorted_unique(affected_process_model_ids),
        "affected_guardrail_bundle_ids": _as_sorted_unique(affected_guardrail_bundle_ids),
        "affected_agent_readiness_checklist_item_ids": _as_sorted_unique(affected_checklist_item_ids),
        "agent_readiness_checklist_catalog": recrawl_batch_plan.get("agent_readiness_checklist_catalog", {}),
        "guardrail_refresh_status": "blocked_pending_human_review",
        "validation_notes": [
            "input fixtures contain metadata and hashes only",
            "no public or authenticated page body is persisted",
            "no live crawl, browser automation, login, upload, submission, scheduling, or payment action is represented",
            "changed source hashes invalidate downstream guardrails until human review resolves the change",
        ],
    }
    _assert_metadata_only(packet)
    return packet


def load_fixture_packet(
    recrawl_batch_plan_path: Path,
    changed_hashes_path: Path,
    *,
    generated_at: str = "2026-05-28T00:00:00Z",
) -> dict[str, Any]:
    return build_invalidation_packet(
        _read_json(recrawl_batch_plan_path),
        _read_json(changed_hashes_path),
        generated_at=generated_at,
    )
