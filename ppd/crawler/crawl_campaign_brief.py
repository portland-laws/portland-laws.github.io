"""Fixture-only PP&D crawl campaign brief loader and validator.

This module validates campaign metadata used to plan bounded public crawl
batches. It performs no network I/O and does not access authenticated surfaces.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

ALLOWED_PUBLIC_HOSTS = frozenset(
    {
        "www.portland.gov",
        "portland.gov",
        "devhub.portlandoregon.gov",
        "www.portlandoregon.gov",
        "www.portlandmaps.com",
    }
)

DISALLOWED_PATH_MARKERS = (
    "/login",
    "/signin",
    "/register",
    "/account",
    "/session",
    "/payment",
    "/checkout",
    "/upload",
    "/submit",
)

REQUIRED_SCOPE_FIELDS = frozenset(
    {
        "agency",
        "jurisdiction",
        "purpose",
        "storage_policy",
        "allowlist_policy",
        "requires_authentication",
    }
)

REQUIRED_BATCH_FIELDS = frozenset(
    {
        "batch_id",
        "permit_family",
        "priority",
        "recrawl_cadence",
        "public_html_seeds",
        "public_pdf_seeds",
        "devhub_public_routes",
        "bounded_follow_patterns",
        "exclude_patterns",
    }
)


def load_campaign_brief(path: str | Path) -> dict[str, Any]:
    """Load a committed campaign brief fixture."""

    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_campaign_brief(brief: dict[str, Any]) -> list[str]:
    """Return validation errors for a fixture-only campaign brief."""

    errors: list[str] = []

    if not isinstance(brief.get("brief_id"), str) or not brief["brief_id"].strip():
        errors.append("brief_id must be a non-empty string")
    if not isinstance(brief.get("task"), str) or not brief["task"].startswith("checkbox-"):
        errors.append("task must be a checkbox-* string")
    if not isinstance(brief.get("last_verified"), str) or not brief["last_verified"].strip():
        errors.append("last_verified must be a non-empty date string")

    scope = brief.get("scope")
    if not isinstance(scope, dict):
        errors.append("scope must be an object")
    else:
        missing_scope = sorted(REQUIRED_SCOPE_FIELDS - set(scope))
        if missing_scope:
            errors.append(f"scope missing fields: {', '.join(missing_scope)}")
        if scope.get("requires_authentication") is not False:
            errors.append("scope.requires_authentication must be false")

    families = brief.get("allowed_public_source_families")
    if not isinstance(families, list) or not families:
        errors.append("allowed_public_source_families must be a non-empty list")
    else:
        for index, family in enumerate(families):
            prefix = f"allowed_public_source_families[{index}]"
            if not isinstance(family, dict):
                errors.append(f"{prefix} must be an object")
                continue
            if not isinstance(family.get("family"), str) or not family["family"].strip():
                errors.append(f"{prefix}.family must be a non-empty string")
            hosts = family.get("host_examples")
            if not isinstance(hosts, list) or not hosts:
                errors.append(f"{prefix}.host_examples must be a non-empty list")
            else:
                for host in hosts:
                    if host not in ALLOWED_PUBLIC_HOSTS:
                        errors.append(f"{prefix}.host_examples contains non-allowlisted host: {host!r}")

    defaults = brief.get("campaign_defaults")
    if not isinstance(defaults, dict):
        errors.append("campaign_defaults must be an object")
    else:
        if defaults.get("body_retention") != "forbidden":
            errors.append("campaign_defaults.body_retention must be 'forbidden'")
        if defaults.get("respect_robots_txt") is not True:
            errors.append("campaign_defaults.respect_robots_txt must be true")
        if not isinstance(defaults.get("max_depth"), int) or defaults["max_depth"] < 0:
            errors.append("campaign_defaults.max_depth must be a non-negative int")

    batches = brief.get("permit_family_batches")
    if not isinstance(batches, list) or not batches:
        errors.append("permit_family_batches must be a non-empty list")
    else:
        seen_ids: set[str] = set()
        for index, batch in enumerate(batches):
            prefix = f"permit_family_batches[{index}]"
            if not isinstance(batch, dict):
                errors.append(f"{prefix} must be an object")
                continue
            missing_batch = sorted(REQUIRED_BATCH_FIELDS - set(batch))
            if missing_batch:
                errors.append(f"{prefix} missing fields: {', '.join(missing_batch)}")
                continue

            batch_id = batch.get("batch_id")
            if not isinstance(batch_id, str) or not batch_id.strip():
                errors.append(f"{prefix}.batch_id must be a non-empty string")
            elif batch_id in seen_ids:
                errors.append(f"{prefix}.batch_id duplicates {batch_id}")
            else:
                seen_ids.add(batch_id)

            priority = batch.get("priority")
            if not isinstance(priority, int) or priority < 1:
                errors.append(f"{prefix}.priority must be an integer >= 1")

            if not isinstance(batch.get("recrawl_cadence"), str) or not batch["recrawl_cadence"].strip():
                errors.append(f"{prefix}.recrawl_cadence must be a non-empty string")

            errors.extend(_validate_url_list(batch.get("public_html_seeds"), f"{prefix}.public_html_seeds"))
            errors.extend(_validate_url_list(batch.get("public_pdf_seeds"), f"{prefix}.public_pdf_seeds"))
            errors.extend(_validate_url_list(batch.get("devhub_public_routes"), f"{prefix}.devhub_public_routes"))

            if not _is_non_empty_string_list(batch.get("bounded_follow_patterns")):
                errors.append(f"{prefix}.bounded_follow_patterns must be a non-empty list of strings")
            if not _is_non_empty_string_list(batch.get("exclude_patterns")):
                errors.append(f"{prefix}.exclude_patterns must be a non-empty list of strings")

    expectations = brief.get("validation_expectations")
    if not _is_non_empty_string_list(expectations):
        errors.append("validation_expectations must be a non-empty list of strings")

    return errors


def campaign_batch_summary(brief: dict[str, Any]) -> dict[str, int]:
    """Return a deterministic aggregate summary of campaign batch seeds."""

    batches = brief.get("permit_family_batches")
    if not isinstance(batches, list):
        return {"batch_count": 0, "public_html_seed_count": 0, "public_pdf_seed_count": 0, "devhub_public_route_count": 0}

    return {
        "batch_count": len(batches),
        "public_html_seed_count": sum(_safe_len(batch.get("public_html_seeds")) for batch in batches if isinstance(batch, dict)),
        "public_pdf_seed_count": sum(_safe_len(batch.get("public_pdf_seeds")) for batch in batches if isinstance(batch, dict)),
        "devhub_public_route_count": sum(_safe_len(batch.get("devhub_public_routes")) for batch in batches if isinstance(batch, dict)),
    }


def _validate_url_list(value: Any, field: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, list):
        return [f"{field} must be a list"]
    for index, url in enumerate(value):
        if not isinstance(url, str) or not url.strip():
            errors.append(f"{field}[{index}] must be a non-empty string")
            continue
        parsed = urlsplit(url.strip())
        if parsed.scheme != "https":
            errors.append(f"{field}[{index}] must use https")
            continue
        if parsed.hostname not in ALLOWED_PUBLIC_HOSTS:
            errors.append(f"{field}[{index}] host must be in allowlist")
            continue
        lowered_path = parsed.path.lower()
        if any(marker in lowered_path for marker in DISALLOWED_PATH_MARKERS):
            errors.append(f"{field}[{index}] includes private or consequential path marker")
    return errors


def _is_non_empty_string_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item.strip() for item in value)


def _safe_len(value: Any) -> int:
    return len(value) if isinstance(value, list) else 0


__all__ = ["ALLOWED_PUBLIC_HOSTS", "campaign_batch_summary", "load_campaign_brief", "validate_campaign_brief"]

