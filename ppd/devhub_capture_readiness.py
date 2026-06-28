"""Validate attended DevHub capture readiness manifests.

This module is intentionally offline-only. It validates a small JSON-compatible
manifest before any authenticated or attended DevHub capture is attempted.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


EXACT_BOUNDARY_NOTICES = (
    "Manual login handoff only: a human operator must authenticate in the browser and remain present for the entire capture.",
    "Capture scope is accessible structure only: collect semantic headings, labels, links, form field names, and status text; do not capture screenshots, traces, HAR data, cookies, credentials, or session state.",
    "No transactional actions: do not upload files, submit forms, schedule inspections or appointments, make payments, certify statements, create accounts, cancel records, or change permit/project state.",
)

_FORBIDDEN_ARTIFACT_KEYS = (
    "session_state",
    "storage_state",
    "cookies",
    "credentials",
    "passwords",
    "screenshots",
    "screenshot",
    "traces",
    "trace",
    "har",
    "har_data",
    "downloads",
    "downloaded_documents",
    "raw_crawl_output",
)

_FORBIDDEN_ACTIONS = (
    "upload",
    "uploads",
    "submit",
    "submission",
    "submissions",
    "schedule",
    "scheduling",
    "payment",
    "payments",
    "pay",
    "certify",
    "certification",
    "cancel",
    "cancellation",
    "create_account",
    "account_creation",
)

_REQUIRED_REDACTION_CATEGORIES = (
    "credentials",
    "cookies",
    "session_state",
    "personal_identifiers",
    "payment_information",
)


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: tuple[str, ...]

    def require_ok(self) -> None:
        if not self.ok:
            raise ValueError("DevHub capture readiness manifest rejected: " + "; ".join(self.errors))


def load_manifest(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("manifest root must be a JSON object")
    return data


def validate_manifest(manifest: Mapping[str, Any]) -> ValidationResult:
    errors: list[str] = []

    _require_true(manifest, "manual_login_handoff", errors)
    _require_true(manifest, "human_operator_attendance", errors)
    _require_equal(manifest, "capture_scope", "accessible_structure_only", errors)
    _validate_redaction_policy(manifest.get("redaction_policy"), errors)
    _validate_boundary_notices(manifest.get("boundary_notices"), errors)
    _reject_forbidden_artifacts(manifest, errors)
    _reject_forbidden_actions(manifest, errors)

    return ValidationResult(ok=not errors, errors=tuple(errors))


def assert_manifest_ready(manifest: Mapping[str, Any]) -> None:
    validate_manifest(manifest).require_ok()


def _require_true(manifest: Mapping[str, Any], key: str, errors: list[str]) -> None:
    if manifest.get(key) is not True:
        errors.append(f"{key} must be true")


def _require_equal(manifest: Mapping[str, Any], key: str, expected: str, errors: list[str]) -> None:
    if manifest.get(key) != expected:
        errors.append(f"{key} must be {expected!r}")


def _validate_redaction_policy(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("redaction_policy must be an object")
        return
    if value.get("enabled") is not True:
        errors.append("redaction_policy.enabled must be true")
    categories = value.get("categories")
    if not _is_string_sequence(categories):
        errors.append("redaction_policy.categories must be a list of strings")
        return
    missing = sorted(set(_REQUIRED_REDACTION_CATEGORIES).difference(categories))
    if missing:
        errors.append("redaction_policy.categories missing: " + ", ".join(missing))


def _validate_boundary_notices(value: Any, errors: list[str]) -> None:
    if not _is_string_sequence(value):
        errors.append("boundary_notices must be a list of exact strings")
        return
    if tuple(value) != EXACT_BOUNDARY_NOTICES:
        errors.append("boundary_notices must exactly match the required attended-capture boundary notices")


def _reject_forbidden_artifacts(manifest: Mapping[str, Any], errors: list[str]) -> None:
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, Mapping):
        errors.append("artifacts must be an object")
        return
    for key in _FORBIDDEN_ARTIFACT_KEYS:
        if artifacts.get(key) not in (None, False, [], {}, ""):
            errors.append(f"artifacts.{key} is forbidden")


def _reject_forbidden_actions(manifest: Mapping[str, Any], errors: list[str]) -> None:
    actions = manifest.get("allowed_actions")
    if not _is_string_sequence(actions):
        errors.append("allowed_actions must be a list of strings")
        return
    normalized = {action.strip().lower().replace("-", "_") for action in actions}
    forbidden = sorted(normalized.intersection(_FORBIDDEN_ACTIONS))
    if forbidden:
        errors.append("allowed_actions includes forbidden actions: " + ", ".join(forbidden))


def _is_string_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)) and all(isinstance(item, str) for item in value)
