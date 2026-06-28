"""Validation for PP&D processor handoff manifest rehearsal packets."""

from __future__ import annotations

from pathlib import PurePosixPath, PureWindowsPath
from typing import Any, Mapping, Sequence

DEFAULT_ALLOWLISTED_SOURCE_IDS = frozenset(
    {
        "portland_devhub_permits",
        "portland_maps_public",
        "portland_ppd_public_plan",
        "ppd_rehearsal_fixture",
    }
)

_RAW_OUTPUT_TOKENS = ("raw_body", "raw-body", "rawbody", "download", "downloads", "archive", "archives")
_PRIVATE_PATH_PREFIXES = (
    "/home/",
    "/users/",
    "/var/folders/",
    "/tmp/",
    "/private/",
    "~/",
    "file://",
)
_PRIVATE_WINDOWS_MARKERS = ("\\users\\", "\\appdata\\", "\\temp\\")
_LIVE_EXECUTION_KEYS = (
    "live_processor_execution",
    "processor_executed",
    "processor_execution_claimed",
    "executed_live",
    "ran_processor",
)
_MUTATION_KEYS = (
    "active_artifact_mutation",
    "artifact_mutation_active",
    "mutate_artifacts",
    "mutates_artifacts",
    "modifies_artifacts",
    "writes_artifacts",
)


def validate_processor_handoff_manifest(
    manifest: Mapping[str, Any],
    *,
    allowlisted_source_ids: Sequence[str] | None = None,
) -> list[str]:
    """Return validation errors for a PP&D processor handoff rehearsal manifest."""

    errors: list[str] = []
    allowlist = set(allowlisted_source_ids or DEFAULT_ALLOWLISTED_SOURCE_IDS)

    if not _non_empty_text(manifest.get("processor_policy")):
        errors.append("missing processor_policy")
    if not _non_empty_text(manifest.get("version_notes")):
        errors.append("missing version_notes")

    source_ids = _source_ids(manifest)
    if not source_ids:
        errors.append("missing source_ids")
    for source_id in source_ids:
        if source_id not in allowlist:
            errors.append(f"non-allowlisted source_id: {source_id}")

    for path in _paths_from_manifest(manifest):
        normalized = path.replace("\\", "/").lower()
        if any(token in normalized for token in _RAW_OUTPUT_TOKENS):
            errors.append(f"raw/download/archive output path is not allowed: {path}")
        if _is_private_local_path(path):
            errors.append(f"private local path is not allowed: {path}")

    for key in _LIVE_EXECUTION_KEYS:
        if manifest.get(key) is True:
            errors.append(f"live processor execution claim is not allowed: {key}")

    attestations = manifest.get("attestations")
    no_raw_body = manifest.get("no_raw_body_attestation") is True
    if isinstance(attestations, Mapping):
        no_raw_body = no_raw_body or attestations.get("no_raw_body") is True
    if not no_raw_body:
        errors.append("missing no-raw-body attestation")

    abort_conditions = manifest.get("abort_conditions")
    if not isinstance(abort_conditions, Sequence) or isinstance(abort_conditions, (str, bytes)) or not abort_conditions:
        errors.append("missing abort_conditions")

    for key in _MUTATION_KEYS:
        if manifest.get(key) is True:
            errors.append(f"active artifact mutation flag is not allowed: {key}")

    artifact_policy = manifest.get("artifact_policy")
    if isinstance(artifact_policy, Mapping):
        for key in _MUTATION_KEYS:
            if artifact_policy.get(key) is True:
                errors.append(f"active artifact mutation flag is not allowed: artifact_policy.{key}")

    return errors


def assert_valid_processor_handoff_manifest(
    manifest: Mapping[str, Any],
    *,
    allowlisted_source_ids: Sequence[str] | None = None,
) -> None:
    errors = validate_processor_handoff_manifest(manifest, allowlisted_source_ids=allowlisted_source_ids)
    if errors:
        raise ValueError("invalid processor handoff manifest: " + "; ".join(errors))


def _non_empty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _source_ids(manifest: Mapping[str, Any]) -> list[str]:
    values: list[str] = []
    raw_sources = manifest.get("source_ids", manifest.get("sources", []))
    if isinstance(raw_sources, str):
        raw_sources = [raw_sources]
    if not isinstance(raw_sources, Sequence):
        return values
    for item in raw_sources:
        if isinstance(item, str):
            values.append(item)
        elif isinstance(item, Mapping):
            source_id = item.get("source_id", item.get("id"))
            if isinstance(source_id, str):
                values.append(source_id)
    return values


def _paths_from_manifest(manifest: Mapping[str, Any]) -> list[str]:
    paths: list[str] = []
    for key in ("output_paths", "artifact_paths", "paths"):
        value = manifest.get(key, [])
        if isinstance(value, str):
            paths.append(value)
        elif isinstance(value, Sequence) and not isinstance(value, (bytes, str)):
            paths.extend(item for item in value if isinstance(item, str))
    artifacts = manifest.get("artifacts", [])
    if isinstance(artifacts, Sequence) and not isinstance(artifacts, (bytes, str)):
        for artifact in artifacts:
            if isinstance(artifact, Mapping):
                for key in ("path", "output_path", "href"):
                    value = artifact.get(key)
                    if isinstance(value, str):
                        paths.append(value)
    return paths


def _is_private_local_path(path: str) -> bool:
    lower = path.lower()
    posix = PurePosixPath(path)
    windows = PureWindowsPath(path)
    if lower.startswith(_PRIVATE_PATH_PREFIXES):
        return True
    if any(marker in lower for marker in _PRIVATE_WINDOWS_MARKERS):
        return True
    if posix.is_absolute() and not lower.startswith("/ppd/"):
        return True
    if windows.is_absolute():
        return True
    return False
