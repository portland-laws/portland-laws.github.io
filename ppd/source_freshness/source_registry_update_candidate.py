"""Build fixture-first SourceRegistry update candidate packets.

This module converts already-reviewed metadata-only recrawl outcomes into
proposed SourceRegistry field updates. It never crawls, fetches, or edits the
live registry; callers receive a candidate packet for separate review.
"""

from __future__ import annotations

import json
import re
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

from ppd.source_freshness.invalidation_packet import (
    PUBLIC_SOURCE_HOSTS,
    _assert_metadata_only,
    _looks_private_or_authenticated_url,
)

REVIEWED_STATUSES = frozenset({"reviewed", "approved", "accepted", "human_reviewed"})
PROPOSED_FIELD_NAMES = (
    "last_seen_at",
    "freshness_status",
    "content_hash",
    "skipped_reason",
)
PRIOR_REGISTRY_ID_KEYS = (
    "prior_registry_id",
    "prior_source_id",
    "prior_source_registry_id",
    "registry_source_id",
)
LIVE_EDIT_KEYS = frozenset(
    {
        "apply_to_live_registry",
        "applied_to_live_registry",
        "edit_live_registry",
        "live_registry_edit",
        "live_registry_updated",
        "registry_mutated",
        "write_to_registry",
    }
)
PRODUCTION_REPLACEMENT_KEYS = frozenset(
    {
        "production_registry",
        "production_registry_replacement",
        "production_source_registry",
        "replace_live_registry",
        "replace_production_registry",
        "replace_source_registry",
        "replacement_registry",
        "replacement_source_registry",
        "source_registry_replacement",
    }
)
RAW_ARCHIVE_PATH_KEYS = frozenset(
    {
        "archive_path",
        "archive_tar_path",
        "archive_zip_path",
        "raw_archive",
        "raw_archive_path",
        "raw_warc_path",
        "warc",
        "warc_path",
        "wget_archive_path",
    }
)
RAW_ARCHIVE_PATH_PATTERN = re.compile(
    r"(^|/)(raw[-_ ]?archives?|archive[-_ ]?raw|warc|wget[-_ ]?archive)(/|$)|\\.warc(\\.gz)?$|\\.zip$|\\.tar(\\.gz)?$",
    re.IGNORECASE,
)
LOWER_LIVE_EDIT_KEYS = frozenset(item.lower() for item in LIVE_EDIT_KEYS)
LOWER_PRODUCTION_REPLACEMENT_KEYS = frozenset(item.lower() for item in PRODUCTION_REPLACEMENT_KEYS)
LOWER_RAW_ARCHIVE_PATH_KEYS = frozenset(item.lower() for item in RAW_ARCHIVE_PATH_KEYS)


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object fixture at {path}")
    return data


def _stable_id(*parts: str) -> str:
    joined = "|".join(parts)
    return sha256(joined.encode("utf-8")).hexdigest()[:16]


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _optional_text(value: Any) -> str | None:
    text = _text(value)
    return text or None


def _required_text(row: Mapping[str, Any], field: str) -> str:
    value = _optional_text(row.get(field))
    if value is None:
        raise ValueError(f"{field} is required")
    return value


def _review_status(row: Mapping[str, Any]) -> str:
    return _text(row.get("human_review_status") or row.get("review_status") or row.get("status")).lower()


def _assert_reviewed(row: Mapping[str, Any], label: str) -> None:
    status = _review_status(row)
    if status not in REVIEWED_STATUSES:
        raise ValueError(f"{label} must be reviewed before registry update candidates are built")


def _is_falsey_claim(value: Any) -> bool:
    return value is False or value is None or value in {"false", "not_applied", "proposed_only"}


def _assert_no_live_edit_claims(value: Any, path: str = "packet") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            key_lower = key_text.lower()
            if key_text in LIVE_EDIT_KEYS or key_lower in LOWER_LIVE_EDIT_KEYS:
                if not _is_falsey_claim(child):
                    raise ValueError(f"live registry edits are not allowed in candidate fixtures: {path}.{key_text}")
            _assert_no_live_edit_claims(child, f"{path}.{key_text}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_no_live_edit_claims(child, f"{path}[{index}]")


def _assert_no_production_registry_replacement(value: Any, path: str = "packet") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            key_lower = key_text.lower()
            if key_lower in LOWER_PRODUCTION_REPLACEMENT_KEYS and not _is_falsey_claim(child):
                raise ValueError(f"production registry replacement is not allowed in candidate fixtures: {path}.{key_text}")
            if key_lower in {"registry_target", "target_registry"} and isinstance(child, str):
                if child.lower() in {"live", "production", "prod"}:
                    raise ValueError(f"production registry replacement is not allowed in candidate fixtures: {path}.{key_text}")
            _assert_no_production_registry_replacement(child, f"{path}.{key_text}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_no_production_registry_replacement(child, f"{path}[{index}]")


def _assert_no_raw_archive_paths(value: Any, path: str = "packet") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if key_text.lower() in LOWER_RAW_ARCHIVE_PATH_KEYS:
                raise ValueError(f"raw archive path field is not allowed in registry update candidate fixtures: {path}.{key_text}")
            _assert_no_raw_archive_paths(child, f"{path}.{key_text}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_no_raw_archive_paths(child, f"{path}[{index}]")
    elif isinstance(value, str) and RAW_ARCHIVE_PATH_PATTERN.search(value):
        raise ValueError(f"raw archive path is not allowed in registry update candidate fixtures: {path}")


def _assert_allowlisted_public_url(url: str, label: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{label} must be an http(s) URL")
    if parsed.netloc not in PUBLIC_SOURCE_HOSTS:
        raise ValueError(f"{label} is outside the PP&D public allowlist")
    if _looks_private_or_authenticated_url(url):
        raise ValueError(f"{label} is a private or authenticated URL")


def _registry_index(rows: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(rows, list):
        raise ValueError("current_source_registry must be a list")
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("source registry entries must be objects")
        source_id = _required_text(row, "source_id")
        if source_id in indexed:
            raise ValueError(f"duplicate source registry entry: {source_id}")
        _assert_allowlisted_public_url(_required_text(row, "canonical_url"), f"source registry {source_id} canonical_url")
        indexed[source_id] = row
    return indexed


def _outcome_rows(packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = packet.get("reviewed_recrawl_outcomes") or packet.get("recrawl_outcomes") or packet.get("source_outcomes")
    if not isinstance(rows, list) or not rows:
        raise ValueError("reviewed recrawl outcomes must be a non-empty list")
    normalized: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("reviewed recrawl outcomes must be objects")
        normalized.append(row)
    return normalized


def _link_list(row: Mapping[str, Any], key: str) -> list[str]:
    value = row.get(key, [])
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        source_id = row.get("source_id", "")
        raise ValueError(f"source {source_id} requires {key} to be a list of non-empty strings")
    return sorted(set(value))


def _downstream_links(outcome: Mapping[str, Any]) -> dict[str, list[str]]:
    explicit = outcome.get("downstream_invalidation_links")
    if isinstance(explicit, Mapping):
        return {
            "requirement_ids": _link_list(explicit, "requirement_ids"),
            "process_model_ids": _link_list(explicit, "process_model_ids"),
            "guardrail_bundle_ids": _link_list(explicit, "guardrail_bundle_ids"),
            "agent_readiness_checklist_item_ids": _link_list(explicit, "agent_readiness_checklist_item_ids"),
        }
    return {
        "requirement_ids": _link_list(outcome, "affected_requirement_ids"),
        "process_model_ids": _link_list(outcome, "affected_process_model_ids"),
        "guardrail_bundle_ids": _link_list(outcome, "affected_guardrail_bundle_ids"),
        "agent_readiness_checklist_item_ids": _link_list(outcome, "affected_agent_readiness_checklist_item_ids"),
    }


def _proposed_fields(outcome: Mapping[str, Any]) -> dict[str, Any]:
    proposed = {
        "last_seen_at": _required_text(outcome, "last_seen_at"),
        "freshness_status": _required_text(outcome, "freshness_status"),
        "content_hash": _optional_text(outcome.get("content_hash")),
        "skipped_reason": _optional_text(outcome.get("skipped_reason")),
    }
    content_hash = proposed["content_hash"]
    if content_hash is not None and not str(content_hash).startswith("sha256:"):
        raise ValueError("content_hash must use sha256: format when present")
    return proposed


def _prior_fields(registry_entry: Mapping[str, Any]) -> dict[str, Any]:
    return {field: registry_entry.get(field) for field in PROPOSED_FIELD_NAMES}


def _changed_fields(prior: Mapping[str, Any], proposed: Mapping[str, Any]) -> list[str]:
    return [field for field in PROPOSED_FIELD_NAMES if prior.get(field) != proposed.get(field)]


def _assert_prior_registry_id(outcome: Mapping[str, Any], source_id: str) -> None:
    for key in PRIOR_REGISTRY_ID_KEYS:
        prior_id = _optional_text(outcome.get(key))
        if prior_id is not None:
            if prior_id != source_id:
                raise ValueError(f"prior registry id for {source_id} does not match source_id")
            return
    raise ValueError(f"missing prior registry id for {source_id}")


def build_source_registry_update_candidate_packet(
    packet: Mapping[str, Any],
    *,
    generated_at: str = "2026-05-28T00:00:00Z",
) -> dict[str, Any]:
    """Build proposed SourceRegistry updates from reviewed metadata fixtures."""
    working = deepcopy(dict(packet))
    _assert_metadata_only(working)
    _assert_no_raw_archive_paths(working)
    _assert_no_live_edit_claims(working)
    _assert_no_production_registry_replacement(working)
    _assert_reviewed(working, "recrawl packet")

    registry = _registry_index(working.get("current_source_registry"))
    candidates: list[dict[str, Any]] = []

    for outcome in sorted(_outcome_rows(working), key=lambda row: _required_text(row, "source_id")):
        _assert_reviewed(outcome, f"recrawl outcome {outcome.get('source_id', '')}")
        source_id = _required_text(outcome, "source_id")
        _assert_prior_registry_id(outcome, source_id)
        if source_id not in registry:
            raise ValueError(f"recrawl outcome references unknown source_id: {source_id}")
        canonical_url = _required_text(outcome, "canonical_url")
        _assert_allowlisted_public_url(canonical_url, f"recrawl outcome {source_id} canonical_url")
        registry_entry = registry[source_id]
        registry_url = _required_text(registry_entry, "canonical_url")
        if canonical_url != registry_url:
            raise ValueError(f"recrawl outcome canonical_url does not match registry for {source_id}")

        prior = _prior_fields(registry_entry)
        proposed = _proposed_fields(outcome)
        changed = _changed_fields(prior, proposed)
        links = _downstream_links(outcome)
        review_evidence_id = _optional_text(outcome.get("review_evidence_id"))
        if "content_hash" in changed:
            if not review_evidence_id:
                raise ValueError(f"changed content_hash for {source_id} requires review_evidence_id")
            if not any(links.values()):
                raise ValueError(f"changed content_hash for {source_id} requires downstream invalidation links")

        candidates.append(
            {
                "candidate_id": "source-registry-update-" + _stable_id(source_id, canonical_url, proposed["last_seen_at"]),
                "source_id": source_id,
                "prior_registry_id": source_id,
                "canonical_url": canonical_url,
                "candidate_status": "proposed_only",
                "registry_edit_status": "not_applied",
                "prior_fields": prior,
                "proposed_fields": proposed,
                "changed_fields": changed,
                "downstream_invalidation_links": links,
                "review_evidence_id": review_evidence_id,
            }
        )

    packet_out = {
        "packet_id": "source-registry-update-candidates-" + _stable_id(_text(working.get("fixture_id")), generated_at),
        "packet_version": 1,
        "generated_at": generated_at,
        "fixture_id": working.get("fixture_id"),
        "fixture_first": True,
        "metadata_only": True,
        "network_requests_made": False,
        "raw_page_bodies_stored": False,
        "live_registry_edited": False,
        "candidate_count": len(candidates),
        "changed_candidate_count": sum(1 for candidate in candidates if candidate["changed_fields"]),
        "source_registry_update_candidates": candidates,
        "validation_notes": [
            "input recrawl outcomes are reviewed metadata fixtures",
            "packet proposes SourceRegistry field updates only",
            "no live crawl or authenticated automation is represented",
            "live SourceRegistry mutation remains blocked pending separate review",
        ],
    }
    _assert_metadata_only(packet_out)
    _assert_no_raw_archive_paths(packet_out)
    _assert_no_live_edit_claims(packet_out)
    _assert_no_production_registry_replacement(packet_out)
    return packet_out


def load_source_registry_update_candidate_packet(
    fixture_path: Path,
    *,
    generated_at: str = "2026-05-28T00:00:00Z",
) -> dict[str, Any]:
    return build_source_registry_update_candidate_packet(_read_json(fixture_path), generated_at=generated_at)
