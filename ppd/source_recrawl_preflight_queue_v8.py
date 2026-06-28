"""Fixture-first PP&D source recrawl preflight queue v8.

This module is intentionally offline-only. It reads committed public fixtures,
normalizes registry URLs, records allowlist/canonicalization decisions, and emits
handoff flags that remain blocked until separate robots and policy decisions are
provided by a later fixture-backed stage.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

DEFAULT_OFFLINE_VALIDATION_COMMANDS: list[list[str]] = [
    ["python3", "-m", "py_compile", "ppd/source_recrawl_preflight_queue_v8.py"],
    ["python3", "-m", "pytest", "ppd/tests/test_source_recrawl_preflight_queue_v8.py"],
]

PUBLIC_PACKET_VERSION = "public-refresh-authorization-packet-v8"
QUEUE_VERSION = "source-recrawl-preflight-queue-v8"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object in {path}")
    return value


def canonicalize_public_url(url: str) -> tuple[str | None, dict[str, Any]]:
    original = url.strip()
    check: dict[str, Any] = {
        "input_url": url,
        "trimmed_url": original,
        "is_valid_public_http_url": False,
        "canonical_url": None,
        "reason": None,
    }
    if not original:
        check["reason"] = "empty_url"
        return None, check

    parts = urlsplit(original)
    scheme = parts.scheme.lower()
    hostname = (parts.hostname or "").lower()
    if scheme not in {"http", "https"} or not hostname:
        check["reason"] = "unsupported_or_missing_public_http_url"
        return None, check

    netloc = hostname
    if parts.port and not ((scheme == "http" and parts.port == 80) or (scheme == "https" and parts.port == 443)):
        netloc = f"{hostname}:{parts.port}"

    path = parts.path or "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")

    canonical = urlunsplit((scheme, netloc, path, parts.query, ""))
    check.update(
        {
            "is_valid_public_http_url": True,
            "canonical_url": canonical,
            "reason": "canonicalized",
        }
    )
    return canonical, check


def host_allowed(canonical_url: str, allowed_hosts: list[str]) -> bool:
    hostname = (urlsplit(canonical_url).hostname or "").lower()
    normalized_hosts = [host.lower().strip() for host in allowed_hosts if host.strip()]
    return any(hostname == host or hostname.endswith(f".{host}") for host in normalized_hosts)


def build_source_recrawl_preflight_queue_v8(
    authorization_packet: dict[str, Any], source_registry: dict[str, Any]
) -> dict[str, Any]:
    if authorization_packet.get("packet_version") != PUBLIC_PACKET_VERSION:
        raise ValueError("authorization packet must be public refresh authorization packet v8")
    if authorization_packet.get("public_fixture_only") is not True:
        raise ValueError("authorization packet must be marked public_fixture_only")

    authorized_ids = list(authorization_packet.get("authorized_source_ids", []))
    ordered_ids = list(authorization_packet.get("source_order", authorized_ids))
    registry_sources = source_registry.get("sources", [])
    if not isinstance(registry_sources, list):
        raise ValueError("source registry fixture must contain a sources list")

    by_id = {source.get("source_id"): source for source in registry_sources if isinstance(source, dict)}
    candidates: list[dict[str, Any]] = []
    skipped_url_reason_rows: list[dict[str, Any]] = []
    seen_canonical_urls: set[str] = set()
    sequence = 0

    for source_id in ordered_ids:
        source = by_id.get(source_id)
        if not source:
            skipped_url_reason_rows.append(
                {
                    "source_id": source_id,
                    "input_url": None,
                    "canonical_url": None,
                    "reason": "authorized_source_missing_from_registry_fixture",
                }
            )
            continue

        urls = source.get("candidate_urls", [])
        allowed_hosts = list(source.get("allowed_hosts", []))
        source_enabled = bool(source.get("enabled", True))
        source_public = bool(source.get("public_source", False))
        source_authorized = source_id in authorized_ids

        for url in urls:
            canonical_url, canonical_check = canonicalize_public_url(str(url))
            if canonical_url is None:
                skipped_url_reason_rows.append(
                    {
                        "source_id": source_id,
                        "input_url": url,
                        "canonical_url": None,
                        "reason": canonical_check["reason"],
                    }
                )
                continue

            allowlisted = host_allowed(canonical_url, allowed_hosts)
            skip_reasons: list[str] = []
            if not source_enabled:
                skip_reasons.append("source_disabled_in_registry_fixture")
            if not source_public:
                skip_reasons.append("source_not_marked_public_in_registry_fixture")
            if not source_authorized:
                skip_reasons.append("source_not_authorized_by_public_packet_v8")
            if not allowlisted:
                skip_reasons.append("canonical_host_not_in_source_allowlist")
            if canonical_url in seen_canonical_urls:
                skip_reasons.append("duplicate_canonical_url")

            if skip_reasons:
                skipped_url_reason_rows.append(
                    {
                        "source_id": source_id,
                        "input_url": url,
                        "canonical_url": canonical_url,
                        "reason": ";".join(skip_reasons),
                    }
                )
                continue

            seen_canonical_urls.add(canonical_url)
            sequence += 1
            candidates.append(
                {
                    "sequence": sequence,
                    "source_id": source_id,
                    "source_name": source.get("source_name", source_id),
                    "input_url": url,
                    "canonical_url": canonical_url,
                    "canonical_url_check": canonical_check,
                    "allowlist_decision": {
                        "allowed": True,
                        "allowed_hosts": allowed_hosts,
                        "reason": "canonical_host_matched_source_allowlist",
                    },
                    "robots_decision_placeholder": {
                        "status": "not_evaluated_offline_preflight_only",
                        "allowed": None,
                    },
                    "policy_decision_placeholder": {
                        "status": "not_evaluated_offline_preflight_only",
                        "allowed": None,
                    },
                    "processor_handoff_eligibility": {
                        "eligible": False,
                        "reason": "blocked_until_fixture_backed_robots_and_policy_decisions_exist",
                    },
                }
            )

    return {
        "queue_version": QUEUE_VERSION,
        "offline_only": True,
        "prohibited_actions": [
            "live_crawl",
            "raw_artifact_download",
            "devhub_open",
            "private_document_read",
            "upload",
            "submit",
            "certify",
            "pay",
            "schedule",
            "legal_or_permitting_guarantee",
        ],
        "authorization_packet_id": authorization_packet.get("packet_id"),
        "source_registry_id": source_registry.get("registry_id"),
        "ordered_public_source_candidates": candidates,
        "skipped_url_reason_rows": skipped_url_reason_rows,
        "offline_validation_commands": authorization_packet.get(
            "offline_validation_commands", DEFAULT_OFFLINE_VALIDATION_COMMANDS
        ),
    }


def build_queue_from_fixture_paths(authorization_packet_path: Path, source_registry_path: Path) -> dict[str, Any]:
    return build_source_recrawl_preflight_queue_v8(
        load_json(authorization_packet_path), load_json(source_registry_path)
    )
