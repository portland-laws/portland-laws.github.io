"""Validation-only source coverage gap report for PP&D permit families.

The report compares public source inventory categories with committed
permit-process fixture metadata. It is intentionally fixture-only: no live crawl,
no DevHub session access, and no raw document persistence.
"""

from __future__ import annotations

from typing import Any, Mapping
from urllib.parse import urlparse


MODULE_PURPOSE = "validation_only_source_coverage_gap_report"
SCHEMA_VERSION = 1

_ALLOWED_HOSTS = {
    "www.portland.gov",
    "devhub.portlandoregon.gov",
    "www.portlandoregon.gov",
    "www.portlandmaps.com",
}

_PRIVATE_PATH_MARKERS = (
    "/mypermits",
    "/my-permits",
    "/account",
    "/login",
    "/signin",
    "/sign-in",
    "/dashboard",
    "/cart",
    "/checkout",
    "/payment",
    "/payments",
    "/upload",
    "/uploads",
    "/submit",
)

_UNSAFE_KEYS = {
    "authorization",
    "auth",
    "body",
    "content",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "download_path",
    "downloaded_document",
    "html",
    "password",
    "raw_body",
    "raw_content",
    "raw_html",
    "raw_response",
    "response_body",
    "screenshot",
    "screenshot_path",
    "secret",
    "session",
    "storage_state",
    "text",
    "token",
    "trace",
    "trace_path",
    "username",
}

_REQUIRED_CATEGORY_FIELDS = (
    "category_id",
    "permit_family",
    "canonical_url",
    "authority_label",
    "recrawl_cadence",
)


def build_source_coverage_gap_report(
    public_source_inventory: Mapping[str, Any],
    permit_process_fixture_index: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a deterministic coverage report from fixture dictionaries."""

    categories = _read_records(public_source_inventory, ("categories", "records", "inventory"))
    process_fixtures = _read_records(permit_process_fixture_index, ("process_fixtures", "permit_processes", "processes", "fixtures"))

    validation_errors: list[str] = []
    category_rows: list[dict[str, Any]] = []
    fixture_rows: list[dict[str, Any]] = []

    for position, category in enumerate(categories):
        row, errors = _normalize_category(category, position)
        category_rows.append(row)
        validation_errors.extend(errors)

    for position, fixture in enumerate(process_fixtures):
        row, errors = _normalize_fixture(fixture, position)
        fixture_rows.append(row)
        validation_errors.extend(errors)

    fixture_families = {row["permit_family"] for row in fixture_rows if row["permit_family"]}
    category_families = {row["permit_family"] for row in category_rows if row["permit_family"]}

    covered_families = sorted(category_families.intersection(fixture_families))
    missing_families = sorted(category_families.difference(fixture_families))
    orphan_fixture_families = sorted(fixture_families.difference(category_families))

    missing_categories = [
        {
            "category_id": row["category_id"],
            "permit_family": row["permit_family"],
            "canonical_url": row["canonical_url"],
            "authority_label": row["authority_label"],
            "recrawl_cadence": row["recrawl_cadence"],
        }
        for row in category_rows
        if row["permit_family"] in missing_families
    ]

    return {
        "schemaVersion": SCHEMA_VERSION,
        "reportType": "ppd_public_source_fixture_coverage_gap",
        "validationOnly": True,
        "coverageStatus": "invalid" if validation_errors else "gaps_found" if missing_families else "complete",
        "summary": {
            "inventoryCategoryCount": len(category_rows),
            "permitProcessFixtureCount": len(fixture_rows),
            "coveredPermitFamilyCount": len(covered_families),
            "missingPermitFamilyCount": len(missing_families),
            "orphanFixtureFamilyCount": len(orphan_fixture_families),
        },
        "coveredPermitFamilies": covered_families,
        "missingPermitFamilies": missing_families,
        "missingCategories": missing_categories,
        "orphanFixtureFamilies": orphan_fixture_families,
        "validationErrors": sorted(validation_errors),
    }


def assert_source_coverage_gap_report(report: Mapping[str, Any]) -> None:
    """Raise AssertionError when a generated report is malformed."""

    errors = validate_source_coverage_gap_report(report)
    if errors:
        raise AssertionError("; ".join(errors))


def validate_source_coverage_gap_report(report: Mapping[str, Any]) -> list[str]:
    """Validate the shape and safety posture of a generated report."""

    errors: list[str] = []
    if report.get("schemaVersion") != SCHEMA_VERSION:
        errors.append("coverage report schemaVersion must be 1")
    if report.get("reportType") != "ppd_public_source_fixture_coverage_gap":
        errors.append("coverage report reportType is not recognized")
    if report.get("validationOnly") is not True:
        errors.append("coverage report must be validationOnly")
    if report.get("coverageStatus") not in {"complete", "gaps_found", "invalid"}:
        errors.append("coverage report coverageStatus is not recognized")
    if not isinstance(report.get("summary"), Mapping):
        errors.append("coverage report summary is required")
    for key in ("coveredPermitFamilies", "missingPermitFamilies", "missingCategories", "orphanFixtureFamilies", "validationErrors"):
        if not isinstance(report.get(key), list):
            errors.append(f"coverage report {key} must be a list")
    return errors


def _read_records(data: Mapping[str, Any], keys: tuple[str, ...]) -> list[Mapping[str, Any]]:
    for key in keys:
        value = data.get(key)
        if isinstance(value, list):
            return [item if isinstance(item, Mapping) else {} for item in value]
    if isinstance(data, list):
        return [item if isinstance(item, Mapping) else {} for item in data]
    return []


def _normalize_category(category: Mapping[str, Any], position: int) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    row = {
        "category_id": _text(category, "category_id", "categoryId", "id"),
        "permit_family": _normalize_family(_text(category, "permit_family", "permitFamily", "family")),
        "canonical_url": _text(category, "canonical_url", "canonicalUrl", "url"),
        "authority_label": _text(category, "authority_label", "authorityLabel", "authority"),
        "recrawl_cadence": _text(category, "recrawl_cadence", "recrawlCadence", "cadence"),
    }

    for field in _REQUIRED_CATEGORY_FIELDS:
        if not row[field]:
            errors.append(f"category[{position}] missing {field}")

    errors.extend(_validate_public_url(row["canonical_url"], f"category[{position}].canonical_url"))
    errors.extend(_validate_no_unsafe_content(category, f"category[{position}]"))
    return row, errors


def _normalize_fixture(fixture: Mapping[str, Any], position: int) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    family = _normalize_family(_text(fixture, "permit_family", "permitFamily", "family", "permit_type", "permitType"))
    row = {
        "fixture_id": _text(fixture, "fixture_id", "fixtureId", "id"),
        "permit_family": family,
        "fixture_path": _text(fixture, "fixture_path", "fixturePath", "path"),
    }
    if not family:
        errors.append(f"process_fixture[{position}] missing permit_family")
    if not row["fixture_id"]:
        errors.append(f"process_fixture[{position}] missing fixture_id")
    if row["fixture_path"] and not row["fixture_path"].startswith("ppd/tests/fixtures/"):
        errors.append(f"process_fixture[{position}] fixture_path must stay under ppd/tests/fixtures")
    errors.extend(_validate_no_unsafe_content(fixture, f"process_fixture[{position}]"))
    return row, errors


def _validate_public_url(url: str, path: str) -> list[str]:
    errors: list[str] = []
    parsed = urlparse(url)
    if parsed.scheme != "https":
        errors.append(f"{path} must be an https URL")
    if parsed.netloc not in _ALLOWED_HOSTS:
        errors.append(f"{path} host is not PP&D allowlisted")
    lowered_path = parsed.path.lower()
    for marker in _PRIVATE_PATH_MARKERS:
        if marker in lowered_path:
            errors.append(f"{path} points at a private or action-oriented DevHub path")
            break
    return errors


def _validate_no_unsafe_content(value: Any, path: str) -> list[str]:
    errors: list[str] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized_key = str(key).strip().lower().replace("-", "_")
            nested_path = f"{path}.{key}"
            if normalized_key in _UNSAFE_KEYS:
                errors.append(f"{nested_path} is not allowed in validation-only coverage fixtures")
            errors.extend(_validate_no_unsafe_content(nested, nested_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            errors.extend(_validate_no_unsafe_content(nested, f"{path}[{index}]"))
    return errors


def _text(data: Mapping[str, Any], *keys: str) -> str:
    for key in keys:
        value = data.get(key)
        if isinstance(value, str):
            return value.strip()
    return ""


def _normalize_family(value: str) -> str:
    return " ".join(value.strip().lower().replace("_", "-").split())
