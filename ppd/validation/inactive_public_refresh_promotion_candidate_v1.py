"""Validation for inactive public refresh promotion candidates.

The validator is intentionally schema-tolerant: PP&D promotion fixtures may use
slightly different field names while the safety requirements remain fixed.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REQUIRED_REFERENCE_TYPES = (
    "SourceRegistry",
    "ArchiveManifest",
    "DocumentRecord",
    "RequirementNode",
    "ProcessModel",
    "GuardrailBundle",
    "agent-readiness",
)

_REQUIRED_LIST_FIELDS = {
    "reviewer_bundle_references": ("reviewer_bundle_references", "reviewer_bundle_refs", "reviewer_bundles"),
    "inactive_promotion_manifests": ("inactive_promotion_manifests", "inactive_promotion_manifest_refs", "inactive_manifests"),
    "promotion_preconditions": ("promotion_preconditions", "preconditions"),
    "reviewer_approvals": ("reviewer_approvals", "approvals"),
    "rollback_checkpoints": ("rollback_checkpoints", "rollback_points"),
    "validation_commands": ("validation_commands", "validation"),
}

_MUTATION_FLAGS = (
    "active_mutation",
    "active_mutation_enabled",
    "mutation_enabled",
    "mutates_live",
    "writes_enabled",
    "write_enabled",
    "crawl_enabled",
    "live_crawl_enabled",
    "extraction_enabled",
    "live_extraction_enabled",
    "activate_release",
    "activate_promotion",
    "release_activation",
    "promotion_activation",
)

_FORBIDDEN_CLAIM_NEEDLES = (
    "live crawl",
    "live-crawl",
    "live extraction",
    "live-extraction",
    "crawled live",
    "extracted live",
    "devhub",
    "active promotion",
    "promotion activated",
    "activate promotion",
    "release activation",
    "release activated",
    "activate release",
    "official action complete",
    "official-action complete",
    "official action completed",
    "official-action completed",
    "legally guaranteed",
    "legal guarantee",
    "permitting guaranteed",
    "permitting guarantee",
    "permit guaranteed",
    "guaranteed approval",
)

_ARTIFACT_FORBIDDEN_VALUES = {"private", "raw", "downloaded"}


def validate_candidate(candidate: dict[str, Any]) -> list[str]:
    """Return validation error strings for an inactive public refresh candidate."""

    errors: list[str] = []

    version = _first_value(candidate, ("candidate_version", "version", "schema_version"))
    if version not in {"v1", "inactive-public-refresh-promotion-candidate-v1"}:
        errors.append("candidate version must be v1")

    state = _first_value(candidate, ("promotion_state", "state", "status"))
    if state != "inactive":
        errors.append("promotion state must be inactive")

    active = _first_value(candidate, ("active", "is_active"), default=False)
    if active is True:
        errors.append("candidate must not be active")

    for label, aliases in _REQUIRED_LIST_FIELDS.items():
        values = _first_present(candidate, aliases)
        if not _non_empty(values):
            errors.append(f"missing {label}")

    coverage = _first_present(
        candidate,
        ("reference_coverage", "references", "coverage", "required_reference_coverage"),
    )
    missing_reference_types = _missing_reference_coverage(coverage)
    for reference_type in missing_reference_types:
        errors.append(f"missing reference coverage for {reference_type}")

    for path, value in _walk(candidate):
        key = path[-1] if path else ""
        if key in _MUTATION_FLAGS and value is True:
            errors.append(f"active mutation flag set: {'.'.join(path)}")
        if key in _MUTATION_FLAGS and isinstance(value, str) and value.lower() in {"true", "yes", "enabled", "active"}:
            errors.append(f"active mutation flag set: {'.'.join(path)}")

    for artifact in candidate.get("artifacts", ()) or ():
        if isinstance(artifact, dict):
            artifact_values = {str(value).lower() for value in artifact.values() if isinstance(value, str)}
            if artifact_values & _ARTIFACT_FORBIDDEN_VALUES:
                errors.append("artifact must not be private, raw, or downloaded")

    claim_text = "\n".join(_claim_strings(candidate)).lower()
    for needle in _FORBIDDEN_CLAIM_NEEDLES:
        if needle in claim_text:
            errors.append(f"forbidden claim: {needle}")

    return _dedupe(errors)


def validate_candidate_file(path: str | Path) -> list[str]:
    """Load and validate a JSON candidate file."""

    with Path(path).open("r", encoding="utf-8") as handle:
        candidate = json.load(handle)
    if not isinstance(candidate, dict):
        return ["candidate must be a JSON object"]
    return validate_candidate(candidate)


def _first_value(candidate: dict[str, Any], aliases: tuple[str, ...], default: Any = None) -> Any:
    value = _first_present(candidate, aliases)
    return default if value is None else value


def _first_present(candidate: dict[str, Any], aliases: tuple[str, ...]) -> Any:
    for alias in aliases:
        if alias in candidate:
            return candidate[alias]
    return None


def _non_empty(value: Any) -> bool:
    if isinstance(value, (list, tuple, set)):
        return bool(value)
    if isinstance(value, dict):
        return bool(value)
    if isinstance(value, str):
        return bool(value.strip())
    return value is not None


def _missing_reference_coverage(coverage: Any) -> list[str]:
    if not isinstance(coverage, dict):
        return list(REQUIRED_REFERENCE_TYPES)

    missing: list[str] = []
    normalized = {str(key).lower(): value for key, value in coverage.items()}
    for reference_type in REQUIRED_REFERENCE_TYPES:
        value = normalized.get(reference_type.lower())
        if not _non_empty(value):
            missing.append(reference_type)
    return missing


def _claim_strings(value: Any) -> list[str]:
    strings: list[str] = []
    for path, item in _walk(value):
        if isinstance(item, str) and any(part in {"claim", "claims", "summary", "description", "notes"} for part in path):
            strings.append(item)
    return strings


def _walk(value: Any, path: tuple[str, ...] = ()) -> list[tuple[tuple[str, ...], Any]]:
    found = [(path, value)]
    if isinstance(value, dict):
        for key, item in value.items():
            found.extend(_walk(item, path + (str(key),)))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(_walk(item, path + (str(index),)))
    return found


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
