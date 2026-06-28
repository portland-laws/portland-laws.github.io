"""Validation for PP&D processor handoff dry-run manifest v8.

The v8 dry-run manifest is a fixture-first contract. It must describe only the
metadata and placeholders needed to plan processor handoff validation. It must
not claim live processor/crawl execution, persist raw crawl outputs, include
private/session/auth artifacts, complete official actions, make legal or
permitting guarantees, or enable mutation.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from pathlib import PurePosixPath, PureWindowsPath
from typing import Any, Iterable, Mapping, Sequence

MANIFEST_VERSION_VALUES = {8, "8", "v8", "processor_handoff_dry_run_manifest_v8"}
MANIFEST_TYPE = "ppd_processor_handoff_dry_run_manifest"

REQUIRED_SECTIONS: tuple[tuple[str, str], ...] = (
    ("preflight_queue_references", "missing preflight queue references"),
    ("planned_processor_invocation_rows", "missing planned processor invocation rows"),
    ("response_metadata_placeholders", "missing response metadata placeholders"),
    ("content_hash_placeholders", "missing content hash placeholders"),
    ("normalized_document_reference_placeholders", "missing normalized document reference placeholders"),
    ("no_raw_body_persistence_assertions", "missing no-raw-body persistence assertions"),
    ("skipped_source_rows", "missing skipped source rows"),
    ("validation_commands", "missing validation commands"),
)

LIVE_PROCESSOR_KEYS = {
    "live_processor_execution",
    "live_processor_execution_claim",
    "processor_executed",
    "processor_execution_claimed",
    "processor_invoked",
    "processor_invocation_claimed",
    "ran_processor",
}
LIVE_CRAWL_KEYS = {
    "live_crawl_execution",
    "live_crawl_execution_claim",
    "crawl_executed",
    "crawl_execution_claimed",
    "crawl_invoked",
    "network_invoked",
    "network_fetch_completed",
}
RAW_ARTIFACT_KEYS = {
    "downloaded_artifact",
    "downloaded_artifacts",
    "downloaded_document",
    "downloaded_documents",
    "raw_crawl_artifact",
    "raw_crawl_artifacts",
    "raw_crawl_output",
    "raw_body",
    "raw_html",
    "raw_text",
    "body",
    "html",
    "pdf_bytes",
    "document_bytes",
    "warc_path",
    "archive_artifact_path",
}
PRIVATE_ARTIFACT_KEYS = {
    "session_artifact",
    "session_artifacts",
    "session_state",
    "auth_artifact",
    "auth_artifacts",
    "auth_state",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "password",
    "token",
    "trace",
    "traces",
    "har",
    "screenshot",
    "screenshots",
}
OFFICIAL_ACTION_KEYS = {
    "official_action_completion",
    "official_action_completed",
    "submitted",
    "certified",
    "uploaded_to_official_record",
    "payment_completed",
    "inspection_scheduled",
}
GUARANTEE_KEYS = {
    "legal_guarantee",
    "legal_guarantees",
    "permit_guarantee",
    "permit_guarantees",
    "permitting_guarantee",
    "permitting_guarantees",
    "approval_guarantee",
}
MUTATION_KEYS = {
    "active_mutation",
    "mutation_active",
    "mutation_enabled",
    "mutate_artifacts",
    "writes_artifacts",
    "persist_outputs",
}

SAFE_FALSE_KEYS = {
    "live_processor_execution_allowed",
    "live_crawl_execution_allowed",
    "network_allowed",
    "processor_invocation_allowed",
    "raw_artifact_download_allowed",
    "download_documents",
    "document_content_persisted",
    "artifact_persisted",
    "persist_raw_body",
    "raw_body_persisted",
    "official_action_allowed",
    "official_action_completed",
    "legal_or_permitting_guarantees_made",
    "mutation_enabled",
}

PRIVATE_PATH_PREFIXES = (
    "/home/",
    "/users/",
    "/var/folders/",
    "/tmp/",
    "/private/",
    "~/",
    "file://",
)
PRIVATE_WINDOWS_MARKERS = ("\\users\\", "\\appdata\\", "\\temp\\")
RAW_PATH_TOKENS = ("raw_body", "raw-body", "raw_crawl", "downloaded", "downloads", "warc", "har")

FORBIDDEN_TEXT_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\blive\s+processor\s+(?:was\s+)?(?:executed|run|completed|invoked)\b", re.I), "rejects live processor execution claims"),
    (re.compile(r"\bprocessor\s+(?:was\s+)?(?:executed|run|completed|invoked)\b", re.I), "rejects live processor execution claims"),
    (re.compile(r"\blive\s+crawl\s+(?:was\s+)?(?:executed|run|completed|invoked)\b", re.I), "rejects live crawl execution claims"),
    (re.compile(r"\bcrawl\s+(?:was\s+)?(?:executed|run|completed|invoked)\b", re.I), "rejects live crawl execution claims"),
    (re.compile(r"\bdownloaded\s+(?:crawl\s+)?(?:artifact|document)s?\b", re.I), "rejects downloaded or raw crawl artifacts"),
    (re.compile(r"\braw\s+(?:body|crawl\s+(?:artifact|output))\b", re.I), "rejects downloaded or raw crawl artifacts"),
    (re.compile(r"\b(?:private|session|auth)\s+artifact\b", re.I), "rejects private/session/auth artifacts"),
    (re.compile(r"\bofficial\s+action\s+(?:was\s+)?completed\b", re.I), "rejects official-action completion claims"),
    (re.compile(r"\b(?:legal|permit|permitting|approval)\s+guarantee\b", re.I), "rejects legal or permitting guarantees"),
    (re.compile(r"\bmutation\s+(?:is\s+)?(?:active|enabled)\b", re.I), "rejects active mutation flags"),
)

SAFE_TEXT_PATH_FRAGMENTS = (
    "assertion",
    "dry_run",
    "forbidden",
    "guardrail",
    "handoff",
    "placeholder",
    "preflight",
    "prohibition",
    "validation",
)


@dataclass(frozen=True)
class ValidationResult:
    """Result from processor handoff dry-run manifest v8 validation."""

    valid: bool
    errors: tuple[str, ...]


class ProcessorHandoffDryRunManifestV8Error(ValueError):
    """Raised when a dry-run manifest v8 is not valid."""


def validate_processor_handoff_dry_run_manifest_v8(manifest: Mapping[str, Any] | str | bytes) -> ValidationResult:
    """Validate a PP&D processor handoff dry-run manifest v8."""

    parsed = _parse_manifest(manifest)
    errors: list[str] = []

    version = parsed.get("manifest_version", parsed.get("schema_version", parsed.get("version")))
    if version not in MANIFEST_VERSION_VALUES:
        errors.append("manifest version must be v8")

    if parsed.get("manifest_type") not in {None, MANIFEST_TYPE}:
        errors.append(f"manifest_type must be {MANIFEST_TYPE}")

    for key, message in REQUIRED_SECTIONS:
        if not _is_present(parsed.get(key)):
            errors.append(message)

    errors.extend(_preflight_queue_reference_errors(parsed.get("preflight_queue_references")))
    errors.extend(_planned_processor_invocation_errors(parsed.get("planned_processor_invocation_rows")))
    errors.extend(_response_metadata_placeholder_errors(parsed.get("response_metadata_placeholders")))
    errors.extend(_content_hash_placeholder_errors(parsed.get("content_hash_placeholders")))
    errors.extend(_normalized_document_placeholder_errors(parsed.get("normalized_document_reference_placeholders")))
    errors.extend(_no_raw_body_assertion_errors(parsed.get("no_raw_body_persistence_assertions")))
    errors.extend(_skipped_source_row_errors(parsed.get("skipped_source_rows")))
    errors.extend(_validation_command_errors(parsed.get("validation_commands")))
    errors.extend(_forbidden_key_errors(parsed))
    errors.extend(_forbidden_path_errors(parsed))
    errors.extend(_forbidden_text_errors(parsed))

    return ValidationResult(valid=not errors, errors=tuple(dict.fromkeys(errors)))


def require_processor_handoff_dry_run_manifest_v8(manifest: Mapping[str, Any] | str | bytes) -> Mapping[str, Any]:
    """Return the parsed manifest or raise with actionable validation errors."""

    parsed = _parse_manifest(manifest)
    result = validate_processor_handoff_dry_run_manifest_v8(parsed)
    if not result.valid:
        raise ProcessorHandoffDryRunManifestV8Error("; ".join(result.errors))
    return parsed


def _preflight_queue_reference_errors(value: Any) -> list[str]:
    errors: list[str] = []
    for index, row in enumerate(_rows(value)):
        if not _present_text(row.get("queue_ref")):
            errors.append(f"preflight_queue_references[{index}].queue_ref is required")
        if not _present_text(row.get("queue_schema_version")):
            errors.append(f"preflight_queue_references[{index}].queue_schema_version is required")
        if row.get("fixture_only") is not True:
            errors.append(f"preflight_queue_references[{index}].fixture_only must be true")
    return errors


def _planned_processor_invocation_errors(value: Any) -> list[str]:
    errors: list[str] = []
    for index, row in enumerate(_rows(value)):
        if not _present_text(row.get("source_id")):
            errors.append(f"planned_processor_invocation_rows[{index}].source_id is required")
        if not _present_text(row.get("processor_name")):
            errors.append(f"planned_processor_invocation_rows[{index}].processor_name is required")
        if row.get("dry_run") is not True:
            errors.append(f"planned_processor_invocation_rows[{index}].dry_run must be true")
        if row.get("processor_invocation_allowed") is not False:
            errors.append(f"planned_processor_invocation_rows[{index}].processor_invocation_allowed must be false")
        if row.get("network_allowed") is not False:
            errors.append(f"planned_processor_invocation_rows[{index}].network_allowed must be false")
        if row.get("metadata_only") is not True:
            errors.append(f"planned_processor_invocation_rows[{index}].metadata_only must be true")
    return errors


def _response_metadata_placeholder_errors(value: Any) -> list[str]:
    errors: list[str] = []
    for index, row in enumerate(_rows(value)):
        if not _present_text(row.get("source_id")):
            errors.append(f"response_metadata_placeholders[{index}].source_id is required")
        if row.get("placeholder_only") is not True:
            errors.append(f"response_metadata_placeholders[{index}].placeholder_only must be true")
        if "http_status" not in row:
            errors.append(f"response_metadata_placeholders[{index}].http_status placeholder is required")
        if "content_type" not in row:
            errors.append(f"response_metadata_placeholders[{index}].content_type placeholder is required")
        if "redirect_chain" not in row:
            errors.append(f"response_metadata_placeholders[{index}].redirect_chain placeholder is required")
    return errors


def _content_hash_placeholder_errors(value: Any) -> list[str]:
    errors: list[str] = []
    for index, row in enumerate(_rows(value)):
        if not _present_text(row.get("source_id")):
            errors.append(f"content_hash_placeholders[{index}].source_id is required")
        content_hash = row.get("content_hash")
        if not _present_text(content_hash):
            errors.append(f"content_hash_placeholders[{index}].content_hash is required")
        elif not content_hash.startswith("placeholder:"):
            errors.append(f"content_hash_placeholders[{index}].content_hash must be a placeholder")
        if row.get("placeholder_only") is not True:
            errors.append(f"content_hash_placeholders[{index}].placeholder_only must be true")
    return errors


def _normalized_document_placeholder_errors(value: Any) -> list[str]:
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


def _skipped_source_row_errors(value: Any) -> list[str]:
    errors: list[str] = []
    for index, row in enumerate(_rows(value)):
        if not _present_text(row.get("source_id")):
            errors.append(f"skipped_source_rows[{index}].source_id is required")
        if not _present_text(row.get("skipped_reason")):
            errors.append(f"skipped_source_rows[{index}].skipped_reason is required")
        if row.get("processor_invocation_allowed") is not False:
            errors.append(f"skipped_source_rows[{index}].processor_invocation_allowed must be false")
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
            raise ProcessorHandoffDryRunManifestV8Error("manifest JSON must decode to an object")
        return decoded
    raise ProcessorHandoffDryRunManifestV8Error("manifest must be a mapping, JSON string, or JSON bytes")


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
    return ".".join(_normalize_key(part) for part in path)


def _normalize_key(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def _truthy_for_rejection(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip()) and value.strip().lower() not in {"false", "no", "none", "null", "0"}
    return bool(value)


def _forbidden_key_errors(manifest: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for path, value in _walk(manifest):
        if not path:
            continue
        key = _normalize_key(path[-1])
        normalized_path = _normalized_path(path)
        if key in SAFE_FALSE_KEYS and value is False:
            continue
        if key in LIVE_PROCESSOR_KEYS and _truthy_for_rejection(value):
            errors.append("rejects live processor execution claims")
        if key in LIVE_CRAWL_KEYS and _truthy_for_rejection(value):
            errors.append("rejects live crawl execution claims")
        if key in RAW_ARTIFACT_KEYS and _truthy_for_rejection(value):
            errors.append("rejects downloaded or raw crawl artifacts")
        if key in PRIVATE_ARTIFACT_KEYS and _truthy_for_rejection(value):
            errors.append("rejects private/session/auth artifacts")
        if key in OFFICIAL_ACTION_KEYS and _truthy_for_rejection(value):
            errors.append("rejects official-action completion claims")
        if key in GUARANTEE_KEYS and _truthy_for_rejection(value):
            errors.append("rejects legal or permitting guarantees")
        if key in MUTATION_KEYS and _truthy_for_rejection(value):
            errors.append("rejects active mutation flags")
        if "mutation" in normalized_path and _truthy_for_rejection(value) and key not in SAFE_FALSE_KEYS:
            errors.append("rejects active mutation flags")
    return errors


def _forbidden_path_errors(manifest: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for path, value in _walk(manifest):
        if not isinstance(value, str) or not value.strip():
            continue
        key = _normalize_key(path[-1]) if path else ""
        if key not in {"path", "output_path", "artifact_path", "artifact_ref", "href", "url", "file"}:
            continue
        lower = value.lower().replace("\\", "/")
        if any(token in lower for token in RAW_PATH_TOKENS):
            errors.append("rejects downloaded or raw crawl artifacts")
        if _is_private_local_path(value):
            errors.append("rejects private/session/auth artifacts")
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


def _is_private_local_path(path: str) -> bool:
    lower = path.lower()
    posix = PurePosixPath(path)
    windows = PureWindowsPath(path)
    if lower.startswith(PRIVATE_PATH_PREFIXES):
        return True
    if any(marker in lower for marker in PRIVATE_WINDOWS_MARKERS):
        return True
    if posix.is_absolute() and not lower.startswith("/ppd/"):
        return True
    if windows.is_absolute():
        return True
    return False
