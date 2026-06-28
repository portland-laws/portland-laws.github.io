"""Fixture-first public-source delta summary packets for PP&D operators.

This module intentionally consumes committed dry-run metadata only. It does not
crawl, download, authenticate, or write production corpus bundles.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

_ALLOWED_NEXT_STEP_KINDS = {"metadata_review", "fixture_update", "guardrail_review", "operator_note"}
_BLOCKED_GUARDRAIL_STATUSES = {"blocked", "requires_human_review", "unresolved"}
_CHANGED_DELTA_STATUSES = {"added", "changed", "removed"}
_RAW_BODY_KEYS = {"raw_body", "raw_html", "raw_text", "body_excerpt", "raw_body_excerpt", "page_body_excerpt"}
_DOWNLOADED_PATH_KEYS = {
    "downloaded_document_path",
    "downloaded_path",
    "download_path",
    "local_download_path",
    "local_document_path",
    "raw_download_path",
}
_PRODUCTION_READY_VALUES = {"production-ready", "production_ready", "ready_for_production", "prod-ready"}
_PRIVATE_URL_SEGMENTS = {
    "account",
    "accounts",
    "application",
    "applications",
    "auth",
    "dashboard",
    "login",
    "mypermits",
    "my-permits",
    "permitdetails",
    "session",
    "signin",
    "sign-in",
    "storage_state",
}
_PRIVATE_QUERY_NAMES = {"auth", "auth_state", "code", "cookie", "session", "sid", "state", "token"}
_CONSEQUENTIAL_DEVHUB_WORDS = {
    "cancel",
    "certify",
    "pay",
    "payment",
    "purchase",
    "schedule",
    "submit",
    "submission",
    "upload",
    "withdraw",
}


class PublicSourceDeltaSummaryError(ValueError):
    """Raised when a dry-run packet cannot be summarized safely."""


def load_public_data_release_packet(path: str | Path) -> dict[str, Any]:
    """Load a committed public-data dry-run release packet fixture."""

    packet_path = Path(path)
    with packet_path.open("r", encoding="utf-8") as handle:
        packet = json.load(handle)
    if not isinstance(packet, dict):
        raise PublicSourceDeltaSummaryError("release packet must be a JSON object")
    return packet


def build_public_source_delta_summary(packet: dict[str, Any]) -> dict[str, Any]:
    """Build one operator-facing metadata-only summary from a dry-run packet."""

    _validate_metadata_only_packet(packet)
    _validate_packet_body_safety(packet)
    changed_sources = _changed_sources(packet.get("sources", []))
    impacted_requirement_ids = _impacted_requirement_ids(packet.get("requirements", []), changed_sources)
    blocked_guardrails = _blocked_guardrails(packet.get("guardrails", []), impacted_requirement_ids)
    unresolved_review_items = _unresolved_review_items(packet.get("review_items", []))
    allowed_next_steps = _allowed_next_steps(packet.get("next_steps", []))

    return {
        "packet_type": "public_source_delta_summary",
        "summary_id": f"delta-summary::{packet.get('release_id', 'unknown-release')}",
        "source_release_id": packet.get("release_id"),
        "generated_from": "fixture_public_data_dry_run_release_packet",
        "side_effect_policy": {
            "metadata_only": True,
            "crawl_performed": False,
            "download_performed": False,
            "production_bundle_changed": False,
        },
        "changed_sources": changed_sources,
        "impacted_requirement_ids": impacted_requirement_ids,
        "blocked_guardrails": blocked_guardrails,
        "unresolved_review_items": unresolved_review_items,
        "allowed_metadata_only_next_steps": allowed_next_steps,
        "operator_attention_counts": {
            "changed_sources": len(changed_sources),
            "impacted_requirements": len(impacted_requirement_ids),
            "blocked_guardrails": len(blocked_guardrails),
            "unresolved_review_items": len(unresolved_review_items),
            "allowed_next_steps": len(allowed_next_steps),
        },
    }


def build_public_source_delta_summary_from_file(path: str | Path) -> dict[str, Any]:
    """Load and summarize a committed dry-run release packet fixture."""

    return build_public_source_delta_summary(load_public_data_release_packet(path))


def _validate_metadata_only_packet(packet: dict[str, Any]) -> None:
    if packet.get("packet_type") != "public_data_dry_run_release_packet":
        raise PublicSourceDeltaSummaryError("packet_type must be public_data_dry_run_release_packet")
    policy = packet.get("side_effect_policy")
    if not isinstance(policy, dict):
        raise PublicSourceDeltaSummaryError("side_effect_policy is required")
    forbidden_true_flags = ("crawl_performed", "download_performed", "production_bundle_changed")
    for key in forbidden_true_flags:
        if policy.get(key) is True:
            raise PublicSourceDeltaSummaryError(f"dry-run packet is not metadata-only: {key}")
    if policy.get("metadata_only") is not True:
        raise PublicSourceDeltaSummaryError("dry-run packet must declare metadata_only")

    prerequisite_ids = packet.get("prerequisite_packet_ids")
    if not isinstance(prerequisite_ids, list) or not prerequisite_ids:
        raise PublicSourceDeltaSummaryError("prerequisite_packet_ids must list required upstream packet IDs")
    for packet_id in prerequisite_ids:
        if not isinstance(packet_id, str) or not packet_id.strip():
            raise PublicSourceDeltaSummaryError("prerequisite_packet_ids must contain non-empty strings")


def _validate_packet_body_safety(packet: dict[str, Any]) -> None:
    for path, value in _walk_values(packet):
        key = path[-1] if path else ""
        normalized_key = key.lower().replace("-", "_")
        if normalized_key in _RAW_BODY_KEYS and value not in (None, "", [], {}):
            raise PublicSourceDeltaSummaryError(f"raw body excerpt is not allowed: {'.'.join(path)}")
        if normalized_key in _DOWNLOADED_PATH_KEYS and value not in (None, "", [], {}):
            raise PublicSourceDeltaSummaryError(f"downloaded document path is not allowed: {'.'.join(path)}")
        if normalized_key == "production_ready" and value is True:
            raise PublicSourceDeltaSummaryError("production-ready labels are not supported in delta summaries")
        if isinstance(value, str):
            if _is_private_or_authenticated_url(value):
                raise PublicSourceDeltaSummaryError(f"private or authenticated URL is not allowed: {'.'.join(path)}")
            if _is_unsupported_production_ready_label(normalized_key, value):
                raise PublicSourceDeltaSummaryError("production-ready labels are not supported in delta summaries")


def _walk_values(value: Any, path: tuple[str, ...] = ()) -> list[tuple[tuple[str, ...], Any]]:
    values = [(path, value)]
    if isinstance(value, dict):
        for key, child in value.items():
            values.extend(_walk_values(child, path + (str(key),)))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            values.extend(_walk_values(child, path + (str(index),)))
    return values


def _is_private_or_authenticated_url(value: str) -> bool:
    if not value.startswith(("http://", "https://")):
        return False
    parsed = urlparse(value)
    path_segments = {segment.lower() for segment in parsed.path.replace("_", "-").split("/") if segment}
    query_names = {part.split("=", 1)[0].lower() for part in parsed.query.split("&") if part}
    if path_segments.intersection(_PRIVATE_URL_SEGMENTS):
        return True
    if query_names.intersection(_PRIVATE_QUERY_NAMES):
        return True
    if parsed.username or parsed.password:
        return True
    return False


def _is_unsupported_production_ready_label(key: str, value: str) -> bool:
    if key not in {"label", "release_label", "readiness", "readiness_label", "status", "validation_label"}:
        return False
    normalized_value = value.strip().lower().replace(" ", "_")
    return normalized_value in _PRODUCTION_READY_VALUES


def _changed_sources(sources: Any) -> list[dict[str, Any]]:
    if not isinstance(sources, list):
        raise PublicSourceDeltaSummaryError("sources must be a list")
    changed: list[dict[str, Any]] = []
    for source in sources:
        if not isinstance(source, dict):
            raise PublicSourceDeltaSummaryError("each source must be an object")
        delta_status = source.get("delta_status")
        if delta_status in _CHANGED_DELTA_STATUSES:
            changed_fields = source.get("changed_fields")
            if not isinstance(changed_fields, list) or not any(isinstance(field, str) and field for field in changed_fields):
                raise PublicSourceDeltaSummaryError("changed source claims must list changed_fields")
            citations = source.get("citation_refs")
            if not isinstance(citations, list) or not any(isinstance(citation, str) and citation for citation in citations):
                raise PublicSourceDeltaSummaryError("changed source claims must include citation_refs")
            evidence_ref = _required_string(source, "evidence_ref")
            changed.append(
                {
                    "source_id": _required_string(source, "source_id"),
                    "canonical_url": _required_string(source, "canonical_url"),
                    "delta_status": delta_status,
                    "changed_fields": list(changed_fields),
                    "evidence_ref": evidence_ref,
                    "citation_refs": list(citations),
                }
            )
    return changed


def _impacted_requirement_ids(requirements: Any, changed_sources: list[dict[str, Any]]) -> list[str]:
    if not isinstance(requirements, list):
        raise PublicSourceDeltaSummaryError("requirements must be a list")
    changed_source_ids = {source["source_id"] for source in changed_sources}
    impacted: list[str] = []
    for requirement in requirements:
        if not isinstance(requirement, dict):
            raise PublicSourceDeltaSummaryError("each requirement must be an object")
        requirement_sources = set(requirement.get("source_ids", []))
        if changed_source_ids.intersection(requirement_sources):
            impacted.append(_required_string(requirement, "requirement_id"))
    return sorted(set(impacted))


def _blocked_guardrails(guardrails: Any, impacted_requirement_ids: list[str]) -> list[dict[str, Any]]:
    if not isinstance(guardrails, list):
        raise PublicSourceDeltaSummaryError("guardrails must be a list")
    impacted = set(impacted_requirement_ids)
    blocked: list[dict[str, Any]] = []
    for guardrail in guardrails:
        if not isinstance(guardrail, dict):
            raise PublicSourceDeltaSummaryError("each guardrail must be an object")
        requirement_ids = set(guardrail.get("requirement_ids", []))
        if guardrail.get("validation_status") in _BLOCKED_GUARDRAIL_STATUSES or impacted.intersection(requirement_ids):
            blocked.append(
                {
                    "guardrail_id": _required_string(guardrail, "guardrail_id"),
                    "validation_status": guardrail.get("validation_status"),
                    "requirement_ids": sorted(requirement_ids),
                    "block_reason": guardrail.get("block_reason", "impacted public-source requirement"),
                }
            )
    return blocked


def _unresolved_review_items(review_items: Any) -> list[dict[str, Any]]:
    if not isinstance(review_items, list):
        raise PublicSourceDeltaSummaryError("review_items must be a list")
    unresolved: list[dict[str, Any]] = []
    for item in review_items:
        if not isinstance(item, dict):
            raise PublicSourceDeltaSummaryError("each review item must be an object")
        if item.get("status") != "resolved":
            unresolved.append(
                {
                    "review_id": _required_string(item, "review_id"),
                    "status": item.get("status"),
                    "reason": item.get("reason"),
                    "source_ids": list(item.get("source_ids", [])),
                    "requirement_ids": list(item.get("requirement_ids", [])),
                }
            )
    return unresolved


def _allowed_next_steps(next_steps: Any) -> list[dict[str, Any]]:
    if not isinstance(next_steps, list):
        raise PublicSourceDeltaSummaryError("next_steps must be a list")
    allowed: list[dict[str, Any]] = []
    for step in next_steps:
        if not isinstance(step, dict):
            raise PublicSourceDeltaSummaryError("each next step must be an object")
        step_id = _required_string(step, "step_id")
        kind = step.get("kind")
        if kind not in _ALLOWED_NEXT_STEP_KINDS:
            raise PublicSourceDeltaSummaryError(f"unsupported next step kind for delta summary: {step_id}")
        if step.get("metadata_only") is not True:
            raise PublicSourceDeltaSummaryError(f"next step must be metadata-only: {step_id}")
        if _is_live_crawl_or_consequential_devhub_recommendation(step):
            raise PublicSourceDeltaSummaryError(f"unsafe next step recommendation: {step_id}")
        allowed.append(
            {
                "step_id": step_id,
                "kind": kind,
                "description": step.get("description"),
                "metadata_only": True,
            }
        )
    return allowed


def _is_live_crawl_or_consequential_devhub_recommendation(step: dict[str, Any]) -> bool:
    text = " ".join(str(step.get(key, "")) for key in ("step_id", "kind", "description")).lower()
    if "live crawl" in text or "live_crawl" in text or "crawl_performed" in text:
        return True
    if "devhub" not in text and "official" not in text:
        return False
    words = {word.strip(".,:;()[]{}") for word in text.replace("-", " ").split()}
    return bool(words.intersection(_CONSEQUENTIAL_DEVHUB_WORDS))


def _required_string(record: dict[str, Any], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value:
        raise PublicSourceDeltaSummaryError(f"{key} must be a non-empty string")
    return value
