"""Fixture-only PP&D public source inventory coverage helpers.

This module validates curated source inventory coverage reports. It is limited to
public fixture metadata and must not crawl, authenticate, download documents, or
persist raw response bodies.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse


REQUIRED_GUIDANCE_CATEGORIES = (
    "permit_extension",
    "permit_reactivation",
    "permit_cancellation",
    "permit_refund",
    "inspection_results",
)

FORBIDDEN_TEXT_MARKERS = (
    "ppd/data/private",
    "devhub/session",
    "devhub/sessions",
    "storage_state",
    "auth_state",
    "cookies.json",
    "localstorage.json",
    "trace.zip",
    "playwright-report",
    "/screenshots/",
    "screenshot.png",
    "screenshot.jpg",
    "screenshot.jpeg",
    "screenshot.webp",
    "/downloads/",
    "downloaded_documents",
    "raw_body",
    "rawbody",
    "response_body",
    "responsebody",
    "raw_html",
    "rawhtml",
    "credential",
    "credentials",
    "password",
    "bearer",
    "authorization",
    "session_cookie",
)

ALLOWED_PUBLIC_HOSTS = {
    "www.portland.gov",
    "devhub.portlandoregon.gov",
    "www.portlandoregon.gov",
    "www.portlandmaps.com",
}

PRIVATE_DEVHUB_PATH_PARTS = (
    "/dashboard",
    "/my-permits",
    "/mypermits",
    "/account",
    "/login",
    "/signin",
    "/sign-in",
    "/checkout",
    "/payment",
    "/cart",
)


class CoverageReportError(ValueError):
    """Raised when a fixture-only coverage report violates PP&D constraints."""


def load_coverage_report(path: str | Path) -> dict[str, Any]:
    """Load and validate a fixture-only source inventory coverage report."""

    report_path = Path(path)
    with report_path.open("r", encoding="utf-8") as handle:
        report = json.load(handle)
    validate_coverage_report(report)
    return report


def validate_coverage_report(report: Mapping[str, Any]) -> None:
    """Fail closed if the coverage report is incomplete or unsafe."""

    errors: list[str] = []
    if report.get("schemaVersion") != 1:
        errors.append("schemaVersion must be 1")
    if report.get("sourceMode") != "fixture_only_public_source_inventory":
        errors.append("sourceMode must be fixture_only_public_source_inventory")
    if report.get("liveCrawlingUsed") is not False:
        errors.append("liveCrawlingUsed must be false")
    if report.get("authenticatedAutomationUsed") is not False:
        errors.append("authenticatedAutomationUsed must be false")
    if not str(report.get("generatedAt", "")).endswith("Z"):
        errors.append("generatedAt must be an ISO UTC timestamp ending in Z")

    _collect_forbidden_text(report, "$", errors)

    categories = report.get("categories")
    if not isinstance(categories, list):
        errors.append("categories must be a list")
        categories = []

    seen_categories: set[str] = set()
    for index, category in enumerate(categories):
        if not isinstance(category, Mapping):
            errors.append(f"categories[{index}] must be an object")
            continue
        _validate_category(category, index, seen_categories, errors)

    missing = sorted(set(REQUIRED_GUIDANCE_CATEGORIES) - seen_categories)
    if missing:
        errors.append("missing required guidance categories: " + ", ".join(missing))

    if errors:
        raise CoverageReportError("; ".join(errors))


def category_claims(report: Mapping[str, Any]) -> dict[str, list[str]]:
    """Return category IDs mapped to their public coverage claims."""

    validate_coverage_report(report)
    claims: dict[str, list[str]] = {}
    for category in report.get("categories", []):
        category_id = str(category.get("categoryId", ""))
        claims[category_id] = [str(claim) for claim in category.get("coverageClaims", [])]
    return claims


def _validate_category(
    category: Mapping[str, Any],
    index: int,
    seen_categories: set[str],
    errors: list[str],
) -> None:
    category_id = str(category.get("categoryId", ""))
    prefix = f"categories[{index}]"
    if category_id not in REQUIRED_GUIDANCE_CATEGORIES:
        errors.append(f"{prefix}.categoryId is not a required guidance category")
    if category_id in seen_categories:
        errors.append(f"duplicate categoryId {category_id}")
    seen_categories.add(category_id)

    authority_label = str(category.get("authorityLabel", "")).strip()
    if not authority_label:
        errors.append(f"{prefix}.authorityLabel is required")

    recrawl_cadence = str(category.get("recommendedRecrawlCadence", "")).strip()
    if recrawl_cadence not in {"weekly", "monthly", "quarterly"}:
        errors.append(f"{prefix}.recommendedRecrawlCadence must be weekly, monthly, or quarterly")

    claims = category.get("coverageClaims")
    if not isinstance(claims, list) or not claims or not all(str(claim).strip() for claim in claims):
        errors.append(f"{prefix}.coverageClaims must be a non-empty list of strings")

    evidence = category.get("publicSourceEvidence")
    if not isinstance(evidence, list) or not evidence:
        errors.append(f"{prefix}.publicSourceEvidence must be a non-empty list")
        return

    for evidence_index, item in enumerate(evidence):
        if not isinstance(item, Mapping):
            errors.append(f"{prefix}.publicSourceEvidence[{evidence_index}] must be an object")
            continue
        _validate_evidence(item, f"{prefix}.publicSourceEvidence[{evidence_index}]", errors)


def _validate_evidence(item: Mapping[str, Any], prefix: str, errors: list[str]) -> None:
    evidence_id = str(item.get("evidenceId", "")).strip()
    if not evidence_id:
        errors.append(f"{prefix}.evidenceId is required")
    fixture_ref = str(item.get("fixtureRef", "")).strip()
    if not fixture_ref.startswith("ppd/tests/fixtures/"):
        errors.append(f"{prefix}.fixtureRef must point under ppd/tests/fixtures")

    source_url = str(item.get("sourceUrl", "")).strip()
    parsed = urlparse(source_url)
    if parsed.scheme != "https" or parsed.netloc not in ALLOWED_PUBLIC_HOSTS:
        errors.append(f"{prefix}.sourceUrl must be an allowed public HTTPS PP&D source")
    if parsed.netloc == "devhub.portlandoregon.gov" and any(part in parsed.path.lower() for part in PRIVATE_DEVHUB_PATH_PARTS):
        errors.append(f"{prefix}.sourceUrl must not be a private DevHub workflow path")

    citation = str(item.get("citation", "")).strip()
    if not citation:
        errors.append(f"{prefix}.citation is required")

    captured_at = str(item.get("fixtureCapturedAt", "")).strip()
    if not captured_at.endswith("Z"):
        errors.append(f"{prefix}.fixtureCapturedAt must end in Z")

    evidence_type = str(item.get("evidenceType", "")).strip()
    if evidence_type not in {"source_inventory_record", "normalized_public_guidance_fixture"}:
        errors.append(f"{prefix}.evidenceType is not supported")


def _collect_forbidden_text(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            lower_key = key_text.lower()
            if lower_key in {"body", "html", "text", "content", "rawbody", "raw_body", "responsebody", "response_body"}:
                if child not in (None, "", [], {}):
                    errors.append(f"{path}.{key_text} must not contain raw response body content")
            _collect_forbidden_text(child, f"{path}.{key_text}", errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _collect_forbidden_text(child, f"{path}[{index}]", errors)
    elif isinstance(value, str):
        lower_value = value.lower()
        for marker in FORBIDDEN_TEXT_MARKERS:
            if marker in lower_value:
                errors.append(f"{path} contains forbidden private/raw artifact marker {marker}")
