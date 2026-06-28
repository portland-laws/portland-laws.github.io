"""Fixture-first public crawl dry-run promotion manifest validation.

This module is intentionally offline-only. It validates a committed promotion
manifest that references existing planning artifacts and release candidate
fixtures, but it never fetches URLs or persists raw response bodies.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REQUIRED_TOP_LEVEL_KEYS = {
    "manifest_id",
    "mode",
    "source_plan",
    "offline_release_candidate_bundle",
    "allowlisted_public_metadata_targets",
    "robots_policy_prerequisites",
    "processor_handoffs",
    "rate_limit_notes",
    "expected_archive_manifest_ids",
    "operator_abort_conditions",
    "raw_body_persistence",
}

REQUIRED_TARGET_KEYS = {
    "target_id",
    "label",
    "public_metadata_url",
    "metadata_only",
    "allowlist_basis",
    "expected_processor_handoff_id",
}

REQUIRED_POLICY_KEYS = {
    "evidence_id",
    "target_id",
    "robots_txt_reviewed",
    "policy_reviewed",
    "evidence_reference",
    "approved_for_dry_run",
}

REQUIRED_HANDOFF_KEYS = {
    "handoff_id",
    "processor",
    "input_descriptor",
    "output_descriptor",
    "raw_body_allowed",
}

REQUIRED_ABORT_KEYS = {
    "condition_id",
    "description",
    "operator_action",
}


class PromotionManifestError(ValueError):
    """Raised when the dry-run promotion manifest is invalid."""


def load_manifest(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise PromotionManifestError("manifest must be a JSON object")
    return data


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    missing = sorted(REQUIRED_TOP_LEVEL_KEYS - set(manifest))
    if missing:
        errors.append("missing top-level keys: " + ", ".join(missing))

    if manifest.get("mode") != "fixture_first_public_crawl_dry_run_promotion":
        errors.append("mode must be fixture_first_public_crawl_dry_run_promotion")

    raw_body = manifest.get("raw_body_persistence")
    if raw_body != {"allowed": False, "reason": "metadata-only dry run; raw response bodies are not fetched or persisted"}:
        errors.append("raw_body_persistence must explicitly forbid raw body storage")

    source_plan = manifest.get("source_plan")
    if not isinstance(source_plan, dict) or not source_plan.get("artifact_id") or not source_plan.get("fixture_reference"):
        errors.append("source_plan must reference the public recrawl execution rehearsal plan")

    bundle = manifest.get("offline_release_candidate_bundle")
    if not isinstance(bundle, dict) or not bundle.get("bundle_id") or not bundle.get("fixture_reference"):
        errors.append("offline_release_candidate_bundle must reference the offline release candidate bundle")

    targets = manifest.get("allowlisted_public_metadata_targets")
    if not isinstance(targets, list) or not targets:
        errors.append("allowlisted_public_metadata_targets must be a non-empty list")
        targets = []

    handoffs = manifest.get("processor_handoffs")
    if not isinstance(handoffs, list) or not handoffs:
        errors.append("processor_handoffs must be a non-empty list")
        handoffs = []

    policies = manifest.get("robots_policy_prerequisites")
    if not isinstance(policies, list) or not policies:
        errors.append("robots_policy_prerequisites must be a non-empty list")
        policies = []

    aborts = manifest.get("operator_abort_conditions")
    if not isinstance(aborts, list) or not aborts:
        errors.append("operator_abort_conditions must be a non-empty list")
        aborts = []

    handoff_ids = set()
    for index, handoff in enumerate(handoffs):
        if not isinstance(handoff, dict):
            errors.append(f"processor_handoffs[{index}] must be an object")
            continue
        missing_handoff = sorted(REQUIRED_HANDOFF_KEYS - set(handoff))
        if missing_handoff:
            errors.append(f"processor_handoffs[{index}] missing keys: " + ", ".join(missing_handoff))
        handoff_id = handoff.get("handoff_id")
        if isinstance(handoff_id, str):
            handoff_ids.add(handoff_id)
        if handoff.get("raw_body_allowed") is not False:
            errors.append(f"processor_handoffs[{index}] must forbid raw body input")

    target_ids = set()
    for index, target in enumerate(targets):
        if not isinstance(target, dict):
            errors.append(f"allowlisted_public_metadata_targets[{index}] must be an object")
            continue
        missing_target = sorted(REQUIRED_TARGET_KEYS - set(target))
        if missing_target:
            errors.append(f"allowlisted_public_metadata_targets[{index}] missing keys: " + ", ".join(missing_target))
        target_id = target.get("target_id")
        if isinstance(target_id, str):
            target_ids.add(target_id)
        if target.get("metadata_only") is not True:
            errors.append(f"allowlisted_public_metadata_targets[{index}] must be metadata_only")
        url = target.get("public_metadata_url")
        if not isinstance(url, str) or not url.startswith("https://www.portland.gov/"):
            errors.append(f"allowlisted_public_metadata_targets[{index}] must use an allowlisted public Portland metadata URL")
        expected_handoff = target.get("expected_processor_handoff_id")
        if expected_handoff not in handoff_ids:
            errors.append(f"allowlisted_public_metadata_targets[{index}] references an unknown processor handoff")

    policy_target_ids = set()
    for index, policy in enumerate(policies):
        if not isinstance(policy, dict):
            errors.append(f"robots_policy_prerequisites[{index}] must be an object")
            continue
        missing_policy = sorted(REQUIRED_POLICY_KEYS - set(policy))
        if missing_policy:
            errors.append(f"robots_policy_prerequisites[{index}] missing keys: " + ", ".join(missing_policy))
        if isinstance(policy.get("target_id"), str):
            policy_target_ids.add(policy["target_id"])
        if policy.get("robots_txt_reviewed") is not True:
            errors.append(f"robots_policy_prerequisites[{index}] must record robots_txt_reviewed=true")
        if policy.get("policy_reviewed") is not True:
            errors.append(f"robots_policy_prerequisites[{index}] must record policy_reviewed=true")
        if policy.get("approved_for_dry_run") is not True:
            errors.append(f"robots_policy_prerequisites[{index}] must approve dry-run promotion")

    for target_id in sorted(target_ids - policy_target_ids):
        errors.append(f"target {target_id} has no robots/policy prerequisite evidence")

    rate_limit_notes = manifest.get("rate_limit_notes")
    if not isinstance(rate_limit_notes, dict):
        errors.append("rate_limit_notes must be an object")
    else:
        if rate_limit_notes.get("live_fetches_performed") != 0:
            errors.append("rate_limit_notes.live_fetches_performed must be 0")
        if not rate_limit_notes.get("operator_note"):
            errors.append("rate_limit_notes.operator_note is required")

    archive_ids = manifest.get("expected_archive_manifest_ids")
    if not isinstance(archive_ids, list) or not archive_ids or not all(isinstance(item, str) and item for item in archive_ids):
        errors.append("expected_archive_manifest_ids must be a non-empty list of strings")

    for index, abort in enumerate(aborts):
        if not isinstance(abort, dict):
            errors.append(f"operator_abort_conditions[{index}] must be an object")
            continue
        missing_abort = sorted(REQUIRED_ABORT_KEYS - set(abort))
        if missing_abort:
            errors.append(f"operator_abort_conditions[{index}] missing keys: " + ", ".join(missing_abort))

    return errors


def assert_valid_manifest(path: Path) -> dict[str, Any]:
    manifest = load_manifest(path)
    errors = validate_manifest(manifest)
    if errors:
        raise PromotionManifestError("; ".join(errors))
    return manifest
