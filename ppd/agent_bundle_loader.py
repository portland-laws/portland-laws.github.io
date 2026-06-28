"""Fixture-first PP&D agent bundle loader.

The loader is intentionally small and deterministic: it accepts a JSON fixture for one
synthetic permit process and validates the citation-bearing references needed by an
agent before returning the loadable bundle.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REQUIRED_TOP_LEVEL_KEYS = (
    "bundle_id",
    "permit_process_id",
    "source_index_references",
    "requirement_nodes",
    "process_model_stages",
    "guardrail_bundle_ids",
    "unsupported_path_taxonomy",
    "next_safe_action_ids",
)

REQUIRED_CITED_KEYS = ("source_index_ref", "citation")


class AgentBundleFixtureError(ValueError):
    """Raised when a PP&D agent bundle fixture is incomplete or malformed."""


def load_agent_bundle_fixture(path: str | Path) -> dict[str, Any]:
    """Load and validate a cited PP&D agent bundle fixture."""

    fixture_path = Path(path)
    try:
        raw_bundle = json.loads(fixture_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AgentBundleFixtureError(f"Invalid JSON fixture: {fixture_path}") from exc

    if not isinstance(raw_bundle, dict):
        raise AgentBundleFixtureError("Agent bundle fixture must be a JSON object")

    _require_keys(raw_bundle, REQUIRED_TOP_LEVEL_KEYS, "bundle")
    _validate_non_empty_strings(raw_bundle, ("bundle_id", "permit_process_id"), "bundle")
    _validate_source_index_references(raw_bundle["source_index_references"])
    _validate_cited_collection(raw_bundle["requirement_nodes"], "requirement_nodes")
    _validate_cited_collection(raw_bundle["process_model_stages"], "process_model_stages")
    _validate_non_empty_string_list(raw_bundle["guardrail_bundle_ids"], "guardrail_bundle_ids")
    _validate_non_empty_string_list(raw_bundle["next_safe_action_ids"], "next_safe_action_ids")
    _validate_unsupported_path_taxonomy(raw_bundle["unsupported_path_taxonomy"])

    return raw_bundle


def _require_keys(value: dict[str, Any], required_keys: tuple[str, ...], label: str) -> None:
    missing = [key for key in required_keys if key not in value]
    if missing:
        joined = ", ".join(missing)
        raise AgentBundleFixtureError(f"Missing required {label} key(s): {joined}")


def _validate_non_empty_strings(value: dict[str, Any], keys: tuple[str, ...], label: str) -> None:
    for key in keys:
        if not isinstance(value.get(key), str) or not value[key].strip():
            raise AgentBundleFixtureError(f"{label}.{key} must be a non-empty string")


def _validate_non_empty_string_list(value: Any, label: str) -> None:
    if not isinstance(value, list) or not value:
        raise AgentBundleFixtureError(f"{label} must be a non-empty list")
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise AgentBundleFixtureError(f"{label}[{index}] must be a non-empty string")


def _validate_source_index_references(value: Any) -> None:
    if not isinstance(value, list) or not value:
        raise AgentBundleFixtureError("source_index_references must be a non-empty list")

    seen_ids: set[str] = set()
    for index, reference in enumerate(value):
        if not isinstance(reference, dict):
            raise AgentBundleFixtureError(f"source_index_references[{index}] must be an object")
        _require_keys(reference, ("id", "title", "url", "retrieved_date"), f"source_index_references[{index}]")
        _validate_non_empty_strings(reference, ("id", "title", "url", "retrieved_date"), f"source_index_references[{index}]")
        reference_id = reference["id"]
        if reference_id in seen_ids:
            raise AgentBundleFixtureError(f"Duplicate source index reference id: {reference_id}")
        seen_ids.add(reference_id)


def _validate_cited_collection(value: Any, label: str) -> None:
    if not isinstance(value, list) or not value:
        raise AgentBundleFixtureError(f"{label} must be a non-empty list")

    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise AgentBundleFixtureError(f"{label}[{index}] must be an object")
        _require_keys(item, REQUIRED_CITED_KEYS, f"{label}[{index}]")
        _validate_non_empty_strings(item, REQUIRED_CITED_KEYS, f"{label}[{index}]")


def _validate_unsupported_path_taxonomy(value: Any) -> None:
    if not isinstance(value, list) or not value:
        raise AgentBundleFixtureError("unsupported_path_taxonomy must be a non-empty list")

    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise AgentBundleFixtureError(f"unsupported_path_taxonomy[{index}] must be an object")
        _require_keys(item, ("id", "label", "source_index_ref", "citation"), f"unsupported_path_taxonomy[{index}]")
        _validate_non_empty_strings(
            item,
            ("id", "label", "source_index_ref", "citation"),
            f"unsupported_path_taxonomy[{index}]",
        )
