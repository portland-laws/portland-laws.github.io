"""Validation for redacted DevHub recorder manifests.

This module intentionally validates already-produced metadata manifests only. It does
not import or launch Playwright, read browser state, or inspect private page data.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


FORBIDDEN_KEY_PARTS = (
    "auth_state",
    "storage_state",
    "cookie",
    "local_storage",
    "session_storage",
    "screenshot",
    "trace",
    "har",
    "password",
    "credential",
    "secret",
    "token",
    "payment",
    "card_number",
    "cvv",
    "ssn",
    "private_value",
    "raw_value",
    "raw_page_value",
    "page_value",
)

FORBIDDEN_ARTIFACT_SUFFIXES = (
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".zip",
    ".trace",
    ".har",
    ".webm",
)

REDACTED_VALUES = {"", "[REDACTED]", "", "REDACTED", None}
PRIVATE_VALUE_KEYS = {"value", "default_value", "current_value", "input_value", "text_content"}
SAFE_RECORDER_MODES = {"manifest_only", "redacted_manifest"}
SAFE_PRIVACY_CLASSES = {"public", "redacted", "metadata_only"}


@dataclass(frozen=True)
class RecorderManifestError:
    """A single manifest validation error."""

    path: str
    code: str
    message: str


@dataclass(frozen=True)
class RecorderManifestValidation:
    """Result returned by :func:`validate_recorder_manifest`."""

    ok: bool
    errors: tuple[RecorderManifestError, ...]

    def raise_for_errors(self) -> None:
        if not self.ok:
            details = "; ".join(f"{error.path}: {error.message}" for error in self.errors)
            raise ValueError(details)


def validate_recorder_manifest(manifest: Mapping[str, Any]) -> RecorderManifestValidation:
    """Validate a redacted DevHub recorder manifest.

    The validator is intentionally small and conservative. It accepts metadata-only
    manifests and rejects fields that imply browser launch, persisted browser state,
    binary capture artifacts, or private page values.
    """

    errors: list[RecorderManifestError] = []

    if not isinstance(manifest, Mapping):
        return RecorderManifestValidation(
            ok=False,
            errors=(
                RecorderManifestError("$", "manifest_not_object", "manifest must be a JSON object"),
            ),
        )

    _require_string(manifest, "manifest_version", errors)
    _require_string(manifest, "recorded_at", errors)
    _require_mapping(manifest, "surface", errors)
    _require_mapping(manifest, "recorder", errors)
    _require_mapping(manifest, "privacy", errors)

    recorder = manifest.get("recorder")
    if isinstance(recorder, Mapping):
        mode = recorder.get("mode")
        if mode not in SAFE_RECORDER_MODES:
            errors.append(
                RecorderManifestError(
                    "$.recorder.mode",
                    "unsafe_recorder_mode",
                    "recorder mode must be metadata-only",
                )
            )
        if recorder.get("playwright_launched") is not False:
            errors.append(
                RecorderManifestError(
                    "$.recorder.playwright_launched",
                    "playwright_launch_not_allowed",
                    "manifest validation must not represent a Playwright launch",
                )
            )
        if recorder.get("auth_state_saved") is not False:
            errors.append(
                RecorderManifestError(
                    "$.recorder.auth_state_saved",
                    "auth_state_not_allowed",
                    "auth state must not be saved",
                )
            )
        if recorder.get("artifacts_saved") not in (False, [], (), None):
            errors.append(
                RecorderManifestError(
                    "$.recorder.artifacts_saved",
                    "artifacts_not_allowed",
                    "screenshots, traces, HAR files, and similar artifacts must not be saved",
                )
            )

    privacy = manifest.get("privacy")
    if isinstance(privacy, Mapping):
        privacy_class = privacy.get("classification")
        if privacy_class not in SAFE_PRIVACY_CLASSES:
            errors.append(
                RecorderManifestError(
                    "$.privacy.classification",
                    "unsafe_privacy_classification",
                    "privacy classification must be public, redacted, or metadata_only",
                )
            )
        if privacy.get("private_values_persisted") is not False:
            errors.append(
                RecorderManifestError(
                    "$.privacy.private_values_persisted",
                    "private_values_not_allowed",
                    "private page values must not be persisted",
                )
            )

    surface = manifest.get("surface")
    if isinstance(surface, Mapping):
        _require_string(surface, "surface_id", errors, "$.surface")
        _require_string(surface, "url_pattern", errors, "$.surface")
        if surface.get("auth_scope") not in {"public", "authenticated_attended", "unknown"}:
            errors.append(
                RecorderManifestError(
                    "$.surface.auth_scope",
                    "invalid_auth_scope",
                    "auth_scope must be public, authenticated_attended, or unknown",
                )
            )

    _walk_forbidden_content(manifest, "$", errors)
    return RecorderManifestValidation(ok=not errors, errors=tuple(errors))


def validate_recorder_manifest_file(path: str | Path) -> RecorderManifestValidation:
    """Load and validate a recorder manifest JSON file."""

    manifest_path = Path(path)
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(data, Mapping):
        return RecorderManifestValidation(
            ok=False,
            errors=(
                RecorderManifestError("$", "manifest_not_object", "manifest must be a JSON object"),
            ),
        )
    return validate_recorder_manifest(data)


def _require_string(
    mapping: Mapping[str, Any],
    key: str,
    errors: list[RecorderManifestError],
    base_path: str = "$",
) -> None:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        errors.append(
            RecorderManifestError(
                f"{base_path}.{key}",
                "missing_required_string",
                f"{key} must be a non-empty string",
            )
        )


def _require_mapping(
    mapping: Mapping[str, Any],
    key: str,
    errors: list[RecorderManifestError],
) -> None:
    if not isinstance(mapping.get(key), Mapping):
        errors.append(
            RecorderManifestError(
                f"$.{key}",
                "missing_required_object",
                f"{key} must be an object",
            )
        )


def _walk_forbidden_content(value: Any, path: str, errors: list[RecorderManifestError]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            normalized_key = key_text.lower().replace("-", "_")
            if any(part in normalized_key for part in FORBIDDEN_KEY_PARTS):
                errors.append(
                    RecorderManifestError(
                        child_path,
                        "forbidden_key",
                        f"{key_text} is not allowed in a commit-safe DevHub recorder manifest",
                    )
                )
            if normalized_key in PRIVATE_VALUE_KEYS and child not in REDACTED_VALUES:
                errors.append(
                    RecorderManifestError(
                        child_path,
                        "unredacted_private_value",
                        f"{key_text} must be omitted or redacted",
                    )
                )
            _walk_forbidden_content(child, child_path, errors)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _walk_forbidden_content(child, f"{path}[{index}]", errors)
    elif isinstance(value, str):
        lowered = value.lower()
        if _looks_like_forbidden_artifact(lowered):
            errors.append(
                RecorderManifestError(
                    path,
                    "forbidden_artifact_reference",
                    "manifest must not reference screenshots, traces, HAR files, or other browser artifacts",
                )
            )


def _looks_like_forbidden_artifact(value: str) -> bool:
    return any(value.endswith(suffix) for suffix in FORBIDDEN_ARTIFACT_SUFFIXES)


__all__ = [
    "RecorderManifestError",
    "RecorderManifestValidation",
    "validate_recorder_manifest",
    "validate_recorder_manifest_file",
]
