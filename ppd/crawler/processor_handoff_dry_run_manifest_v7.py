"""Validation for PP&D processor handoff dry-run manifest v7.

This validator is intentionally fixture-first and side-effect free. It checks that
handoff manifests include the dry-run evidence rows needed before processor work
can be planned, while rejecting live execution claims, raw artifacts, private
session material, official-action claims, legal guarantees, and active mutation
flags.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any, Iterable, Mapping, Sequence


REQUIRED_SECTIONS: tuple[tuple[str, str], ...] = (
    ("recrawl_preflight_refs", "missing recrawl preflight references"),
    ("processor_invocation_plans", "missing processor invocation plans"),
    ("archive_manifest_placeholders", "missing archive manifest placeholders"),
    ("normalized_document_reference_placeholders", "missing normalized document reference placeholders"),
    ("no_raw_body_persistence_assertions", "missing no-raw-body persistence assertions"),
    ("skipped_source_evidence_rows", "missing skipped-source evidence rows"),
    ("validation_handoff_rows", "missing validation handoff rows"),
    ("validation_commands", "missing validation commands"),
)

FORBIDDEN_KEY_FRAGMENTS: tuple[tuple[str, str], ...] = (
    ("live_processor_execution", "rejects live processor or crawl execution claims"),
    ("processor_executed", "rejects live processor or crawl execution claims"),
    ("processor_invoked", "rejects live processor or crawl execution claims"),
    ("live_crawl_execution", "rejects live processor or crawl execution claims"),
    ("crawl_executed", "rejects live processor or crawl execution claims"),
    ("network_invoked", "rejects live processor or crawl execution claims"),
    ("downloaded_artifact", "rejects downloaded or raw crawl artifacts"),
    ("downloaded_document", "rejects downloaded or raw crawl artifacts"),
    ("raw_crawl_artifact", "rejects downloaded or raw crawl artifacts"),
    ("raw_crawl_output", "rejects downloaded or raw crawl artifacts"),
    ("raw_body", "rejects downloaded or raw crawl artifacts"),
    ("warc", "rejects downloaded or raw crawl artifacts"),
    ("session_artifact", "rejects private/session/auth artifacts"),
    ("session_state", "rejects private/session/auth artifacts"),
    ("auth_artifact", "rejects private/session/auth artifacts"),
    ("auth_state", "rejects private/session/auth artifacts"),
    ("cookie", "rejects private/session/auth artifacts"),
    ("credential", "rejects private/session/auth artifacts"),
    ("trace", "rejects private/session/auth artifacts"),
    ("har", "rejects private/session/auth artifacts"),
    ("screenshot", "rejects private/session/auth artifacts"),
    ("official_action_completion", "rejects official-action completion claims"),
    ("official_action_completed", "rejects official-action completion claims"),
    ("permit_guarantee", "rejects legal or permitting guarantees"),
    ("permitting_guarantee", "rejects legal or permitting guarantees"),
    ("legal_guarantee", "rejects legal or permitting guarantees"),
    ("active_mutation", "rejects active mutation flags"),
    ("mutation_enabled", "rejects active mutation flags"),
)

FORBIDDEN_TEXT_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\blive\s+(?:processor|crawl)\s+(?:was\s+)?(?:executed|run|completed|invoked)\b", re.I), "rejects live processor or crawl execution claims"),
    (re.compile(r"\b(?:processor|crawl)\s+(?:was\s+)?(?:executed|run|completed|invoked)\b", re.I), "rejects live processor or crawl execution claims"),
    (re.compile(r"\bdownloaded\s+(?:crawl\s+)?(?:artifact|document)s?\b", re.I), "rejects downloaded or raw crawl artifacts"),
    (re.compile(r"\braw\s+(?:body|crawl\s+(?:artifact|output))\b", re.I), "rejects downloaded or raw crawl artifacts"),
    (re.compile(r"\b(?:private|session|auth)\s+artifact\b", re.I), "rejects private/session/auth artifacts"),
    (re.compile(r"\bofficial\s+action\s+(?:was\s+)?completed\b", re.I), "rejects official-action completion claims"),
    (re.compile(r"\b(?:legal|permit|permitting)\s+guarantee\b", re.I), "rejects legal or permitting guarantees"),
    (re.compile(r"\bmutation\s+(?:is\s+)?(?:active|enabled)\b", re.I), "rejects active mutation flags"),
)

SAFE_TEXT_PATH_FRAGMENTS = (
    "assertion",
    "dry_run",
    "guardrail",
    "handoff",
    "placeholder",
    "preflight",
    "prohibition",
    "validation",
)


@dataclass(frozen=True)
class ValidationResult:
    """Result from processor handoff dry-run manifest v7 validation."""

    valid: bool
    errors: tuple[str, ...]


class ProcessorHandoffDryRunManifestV7Error(ValueError):
    """Raised when a dry-run manifest v7 is not valid."""


def validate_processor_handoff_dry_run_manifest_v7(manifest: Mapping[str, Any] | str | bytes) -> ValidationResult:
    """Validate a PP&D processor handoff dry-run manifest v7."""

    parsed = _parse_manifest(manifest)
    errors: list[str] = []

    version = parsed.get("manifest_version", parsed.get("schema_version", parsed.get("version")))
    if version not in {7, "7", "v7"}:
        errors.append("manifest version must be v7")

    if parsed.get("manifest_type") not in {None, "ppd_processor_handoff_dry_run_manifest"}:
        errors.append("manifest_type must be ppd_processor_handoff_dry_run_manifest")

    for key, message in REQUIRED_SECTIONS:
        if not _is_present(parsed.get(key)):
            errors.append(message)

    errors.extend(_processor_plan_errors(parsed.get("processor_invocation_plans")))
    errors.extend(_archive_placeholder_errors(parsed.get("archive_manifest_placeholders")))
    errors.extend(_normalized_placeholder_errors(parsed.get("normalized_document_reference_placeholders")))
    errors.extend(_no_raw_body_assertion_errors(parsed.get("no_raw_body_persistence_assertions")))
    errors.extend(_validation_command_errors(parsed.get("validation_commands")))
    errors.extend(_forbidden_key_errors(parsed))
    errors.extend(_forbidden_text_errors(parsed))

    return ValidationResult(valid=not errors, errors=tuple(dict.fromkeys(errors)))


def require_processor_handoff_dry_run_manifest_v7(manifest: Mapping[str, Any] | str | bytes) -> Mapping[str, Any]:
    """Return the parsed manifest or raise with actionable validation errors."""

    parsed = _parse_manifest(manifest)
    result = validate_processor_handoff_dry_run_manifest_v7(parsed)
    if not result.valid:
        raise ProcessorHandoffDryRunManifestV7Error("; ".join(result.errors))
    return parsed


def _processor_plan_errors(value: Any) -> list[str]:
    errors: list[str] = []
    for index, row in enumerate(_rows(value)):
        if row.get("dry_run") is not True:
            errors.append(f"processor_invocation_plans[{index}].dry_run must be true")
        if row.get("processor_invocation_allowed") is not False:
            errors.append(f"processor_invocation_plans[{index}].processor_invocation_allowed must be false")
        if row.get("network_allowed") is not False:
            errors.append(f"processor_invocation_plans[{index}].network_allowed must be false")
        if row.get("metadata_only") is not True:
            errors.append(f"processor_invocation_plans[{index}].metadata_only must be true")
    return errors


def _archive_placeholder_errors(value: Any) -> list[str]:
    errors: list[str] = []
    for index, row in enumerate(_rows(value)):
        if not _present_text(row.get("archive_manifest_id")):
            errors.append(f"archive_manifest_placeholders[{index}].archive_manifest_id is required")
        if row.get("placeholder_only") is not True:
            errors.append(f"archive_manifest_placeholders[{index}].placeholder_only must be true")
        if row.get("artifact_persisted") is not False:
            errors.append(f"archive_manifest_placeholders[{index}].artifact_persisted must be false")
    return errors


def _normalized_placeholder_errors(value: Any) -> list[str]:
    errors: list[str] = []
    for index, row in enumerate(_rows(value)):
        if not _present_text(row.get("normalized_document_id")):
            errors.append(f"normalized_document_reference_placeholders[{index}].normalized_document_id is required")
        if row.get("placeholder_only") is not True:
            errors.append(f"normalized_document_reference_placeholders[{index}].placeholder_only must be true")
        if row.get("document_content_persisted") is not False:
            errors.append(f"normalized_document_reference_placeholders[{index}].document_content_persisted must be false")
    return errors


def _no_raw_body_assertion_errors(value: Any) -> list[str]:
    errors: list[str] = []
    for index, row in enumerate(_rows(value)):
        if row.get("no_raw_body_persisted") is not True:
            errors.append(f"no_raw_body_persistence_assertions[{index}].no_raw_body_persisted must be true")
        if row.get("persist_raw_body") is not False:
            errors.append(f"no_raw_body_persistence_assertions[{index}].persist_raw_body must be false")
        if row.get("download_documents") is not False:
            errors.append(f"no_raw_body_persistence_assertions[{index}].download_documents must be false")
    return errors


def _validation_command_errors(value: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, Sequence) or isinstance(value, (bytes, bytearray, str)):
        return errors
    for index, command in enumerate(value):
        if not isinstance(command, Sequence) or isinstance(command, (bytes, bytearray, str)):
            errors.append(f"validation_commands[{index}] must be an argv list")
            continue
        if not command or not all(isinstance(part, str) and part.strip() for part in command):
            errors.append(f"validation_commands[{index}] must contain non-empty strings")
    return errors


def _parse_manifest(manifest: Mapping[str, Any] | str | bytes) -> Mapping[str, Any]:
    if isinstance(manifest, Mapping):
        return manifest
    if isinstance(manifest, bytes):
        manifest = manifest.decode("utf-8")
    if isinstance(manifest, str):
        decoded = json.loads(manifest)
        if not isinstance(decoded, Mapping):
            raise ProcessorHandoffDryRunManifestV7Error("manifest JSON must decode to an object")
        return decoded
    raise ProcessorHandoffDryRunManifestV7Error("manifest must be a mapping, JSON string, or JSON bytes")


def _is_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return bool(value) and all(_is_present(item) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        return bool(value) and all(_is_present(item) for item in value)
    return True


def _present_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _rows(value: Any) -> Iterable[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (bytes, bytearray, str)):
        return ()
    rows: list[Mapping[str, Any]] = []
    for item in value:
        if isinstance(item, Mapping):
            rows.append(item)
    return tuple(rows)


def _walk(value: Any, path: tuple[str, ...] = ()) -> Iterable[tuple[tuple[str, ...], Any]]:
    yield path, value
    if isinstance(value, Mapping):
        for key, child in value.items():
            yield from _walk(child, (*path, str(key)))
    elif isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        for index, child in enumerate(value):
            yield from _walk(child, (*path, str(index)))


def _normalized_path(path: tuple[str, ...]) -> str:
    return ".".join(part.strip().lower().replace("-", "_").replace(" ", "_") for part in path)


def _truthy_for_rejection(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip()) and value.strip().lower() not in {"false", "no", "none", "null", "0"}
    return bool(value)


def _forbidden_key_errors(manifest: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for path, value in _walk(manifest):
        normalized = _normalized_path(path)
        if not path or not _truthy_for_rejection(value):
            continue
        for fragment, message in FORBIDDEN_KEY_FRAGMENTS:
            if fragment in normalized:
                errors.append(message)
        if "mutation" in normalized and _truthy_for_rejection(value):
            errors.append("rejects active mutation flags")
    return errors


def _forbidden_text_errors(manifest: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for path, value in _walk(manifest):
        if not isinstance(value, str) or not value.strip():
            continue
        normalized = _normalized_path(path)
        if any(fragment in normalized for fragment in SAFE_TEXT_PATH_FRAGMENTS):
            continue
        for pattern, message in FORBIDDEN_TEXT_PATTERNS:
            if pattern.search(value):
                errors.append(message)
    return errors
