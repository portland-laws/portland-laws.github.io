"""Deterministic readiness reports for PP&D synthetic fixtures.

The helper intentionally works from committed fixture JSON only. It does not crawl,
fetch, authenticate, or inspect private DevHub state.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

REPORT_VERSION = "ppd-readiness-report-v1"
REQUIRED_COLLECTIONS = (
    "sources",
    "archive_manifests",
    "documents",
    "requirements",
    "process_models",
    "guardrail_bundles",
)


def load_fixture(path: str | Path) -> dict[str, Any]:
    """Load a committed synthetic readiness fixture."""

    fixture_path = Path(path)
    with fixture_path.open("r", encoding="utf-8") as fixture_file:
        data = json.load(fixture_file)
    if not isinstance(data, dict):
        raise ValueError("readiness fixture must contain a JSON object")
    return data


def build_readiness_report(fixture: Mapping[str, Any]) -> dict[str, Any]:
    """Build a stable readiness report from a PP&D synthetic fixture."""

    collections = _normalized_collections(fixture)
    checks = _build_checks(collections)
    missing = [check["check_id"] for check in checks if check["status"] != "pass"]

    return {
        "report_version": REPORT_VERSION,
        "fixture_id": str(fixture.get("fixture_id", "unknown-fixture")),
        "ready": not missing,
        "counts": {
            name: len(collections[name])
            for name in REQUIRED_COLLECTIONS
        },
        "checks": checks,
        "blocking_check_ids": missing,
    }


def report_as_json(report: Mapping[str, Any]) -> str:
    """Serialize a readiness report in deterministic JSON form."""

    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def _normalized_collections(fixture: Mapping[str, Any]) -> dict[str, list[Mapping[str, Any]]]:
    collections: dict[str, list[Mapping[str, Any]]] = {}
    for name in REQUIRED_COLLECTIONS:
        value = fixture.get(name, [])
        if not isinstance(value, list):
            raise ValueError(f"{name} must be a list")
        normalized_items: list[Mapping[str, Any]] = []
        for index, item in enumerate(value):
            if not isinstance(item, Mapping):
                raise ValueError(f"{name}[{index}] must be an object")
            normalized_items.append(item)
        collections[name] = sorted(normalized_items, key=_stable_item_key)
    return collections


def _build_checks(collections: Mapping[str, Sequence[Mapping[str, Any]]]) -> list[dict[str, Any]]:
    source_ids = _ids(collections["sources"], "source_id")
    document_ids = _ids(collections["documents"], "document_id")
    requirement_ids = _ids(collections["requirements"], "requirement_id")
    process_ids = _ids(collections["process_models"], "process_id")
    guardrail_process_ids = _ids(collections["guardrail_bundles"], "process_id")

    checks = [
        _check(
            "required_collections_present",
            all(collections[name] for name in REQUIRED_COLLECTIONS),
            "synthetic fixture includes every readiness collection",
        ),
        _check(
            "sources_are_public_and_allowlisted",
            all(_source_is_public_and_allowlisted(source) for source in collections["sources"]),
            "sources are public, allowlisted PP&D anchors or public references",
        ),
        _check(
            "archives_do_not_persist_raw_bodies",
            all(manifest.get("no_raw_body_persisted") is True for manifest in collections["archive_manifests"]),
            "archive manifests state that raw bodies are not persisted",
        ),
        _check(
            "archives_reference_known_sources",
            all(str(manifest.get("source_id")) in source_ids for manifest in collections["archive_manifests"]),
            "archive manifests reference known synthetic sources",
        ),
        _check(
            "documents_reference_known_sources",
            all(str(document.get("source_id")) in source_ids for document in collections["documents"]),
            "documents reference known synthetic sources",
        ),
        _check(
            "requirements_have_document_evidence",
            all(_requirement_has_document_evidence(requirement, document_ids) for requirement in collections["requirements"]),
            "requirements include committed synthetic document evidence",
        ),
        _check(
            "requirements_are_reviewed_for_formalization",
            all(_requirement_is_reviewed(requirement) for requirement in collections["requirements"]),
            "requirements are human-review ready and formalized in the fixture",
        ),
        _check(
            "process_models_reference_requirements",
            all(_process_references_known_requirements(process, requirement_ids) for process in collections["process_models"]),
            "process models reference known synthetic requirements",
        ),
        _check(
            "guardrails_cover_process_models",
            process_ids == guardrail_process_ids and bool(process_ids),
            "each process model has a matching guardrail bundle",
        ),
        _check(
            "guardrails_are_validated",
            all(bundle.get("validation_status") == "validated" for bundle in collections["guardrail_bundles"]),
            "guardrail bundles are marked validated in the committed fixture",
        ),
    ]
    return sorted(checks, key=lambda check: check["check_id"])


def _check(check_id: str, passed: bool, description: str) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "description": description,
        "status": "pass" if passed else "fail",
    }


def _ids(items: Iterable[Mapping[str, Any]], key: str) -> set[str]:
    return {str(item.get(key)) for item in items if item.get(key) is not None}


def _stable_item_key(item: Mapping[str, Any]) -> str:
    for key in (
        "source_id",
        "manifest_id",
        "document_id",
        "requirement_id",
        "process_id",
        "guardrail_bundle_id",
    ):
        value = item.get(key)
        if value is not None:
            return str(value)
    return json.dumps(item, sort_keys=True)


def _source_is_public_and_allowlisted(source: Mapping[str, Any]) -> bool:
    source_type = str(source.get("source_type", ""))
    allowlist_policy = str(source.get("allowlist_policy", ""))
    privacy = str(source.get("privacy_classification", ""))
    return source_type.startswith("public") and allowlist_policy == "allowlisted" and privacy == "public"


def _requirement_has_document_evidence(requirement: Mapping[str, Any], document_ids: set[str]) -> bool:
    evidence_ids = requirement.get("source_evidence_ids", [])
    if not isinstance(evidence_ids, list) or not evidence_ids:
        return False
    return all(str(evidence_id) in document_ids for evidence_id in evidence_ids)


def _requirement_is_reviewed(requirement: Mapping[str, Any]) -> bool:
    return (
        requirement.get("human_review_status") in {"synthetic_reviewed", "reviewed"}
        and requirement.get("formalization_status") in {"synthetic_formalized", "formalized"}
    )


def _process_references_known_requirements(process: Mapping[str, Any], requirement_ids: set[str]) -> bool:
    referenced = process.get("requirement_ids", [])
    if not isinstance(referenced, list) or not referenced:
        return False
    return all(str(requirement_id) in requirement_ids for requirement_id in referenced)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a deterministic PP&D readiness report from a synthetic fixture.")
    parser.add_argument("fixture", type=Path, help="Path to a committed synthetic readiness fixture JSON file.")
    args = parser.parse_args(argv)

    report = build_readiness_report(load_fixture(args.fixture))
    print(report_as_json(report), end="")
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
