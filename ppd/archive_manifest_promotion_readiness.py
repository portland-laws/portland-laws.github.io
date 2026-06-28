"""Validation for archive manifest promotion readiness packets.

The validator is intentionally small and deterministic. It only inspects the packet
it is given and never performs live processor execution, filesystem reads, or
network access.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import PurePosixPath, PureWindowsPath
from typing import Any


@dataclass(frozen=True)
class PromotionReadinessIssue:
    """A single readiness validation issue."""

    code: str
    message: str


RAW_PATH_TOKENS = (
    "raw_body",
    "raw-body",
    "download_path",
    "download-path",
    "archive_output_path",
    "archive-output-path",
    "raw_output_path",
    "raw-output-path",
)

PRIVATE_PATH_PREFIXES = (
    "/home/",
    "/users/",
    "/var/folders/",
    "/tmp/",
    "/private/",
    "/root/",
)

WINDOWS_PRIVATE_MARKERS = (
    ":\\users\\",
    ":/users/",
    "\\users\\",
)

LIVE_EXECUTION_TOKENS = (
    "live processor execution",
    "live_processor_execution",
    "processor executed",
    "processor_executed",
    "executed live",
    "ran processor",
    "live crawl",
)

ACTIVE_PROMOTION_KEYS = (
    "active_manifest_promotion",
    "manifest_promotion_active",
    "promote_manifest",
    "promotion_enabled",
    "promotion_active",
)


def validate_promotion_readiness_packet(packet: Mapping[str, Any]) -> list[PromotionReadinessIssue]:
    """Return validation issues for an archive manifest promotion readiness packet."""

    issues: list[PromotionReadinessIssue] = []

    evidence = _mapping(packet.get("evidence"))
    attestations = _mapping(packet.get("attestations"))

    if not evidence.get("checksum") and not evidence.get("checksum_evidence"):
        issues.append(PromotionReadinessIssue("missing_checksum_evidence", "Packet is missing checksum evidence."))

    if not evidence.get("freshness") and not evidence.get("freshness_evidence"):
        issues.append(PromotionReadinessIssue("missing_freshness_evidence", "Packet is missing freshness evidence."))

    if attestations.get("no_raw_body") is not True and packet.get("no_raw_body_attestation") is not True:
        issues.append(PromotionReadinessIssue("missing_no_raw_body_attestation", "Packet must attest that no raw body content is included."))

    if _requires_abort_note(packet) and not _non_empty_text(packet.get("abort_note")) and not _non_empty_text(packet.get("abort_notes")):
        issues.append(PromotionReadinessIssue("missing_abort_notes", "Aborted or abort-required packets must include abort notes."))

    known_manifest_ids = set(_string_sequence(packet.get("known_manifest_ids")))
    known_source_ids = set(_string_sequence(packet.get("known_source_ids")))
    manifest_id = _text_or_none(packet.get("manifest_id"))
    source_id = _text_or_none(packet.get("source_id"))

    if manifest_id and known_manifest_ids and manifest_id not in known_manifest_ids:
        issues.append(PromotionReadinessIssue("unknown_manifest_id", f"Unknown manifest id: {manifest_id}"))

    if source_id and known_source_ids and source_id not in known_source_ids:
        issues.append(PromotionReadinessIssue("unknown_source_id", f"Unknown source id: {source_id}"))

    for path_name, path_value in _walk_text(packet):
        normalized = path_value.strip().lower()
        if _looks_like_raw_output_path(path_name, normalized):
            issues.append(PromotionReadinessIssue("raw_output_path_present", f"Raw body/download/archive output path is not allowed at {path_name}."))
        if _looks_like_private_path(normalized):
            issues.append(PromotionReadinessIssue("private_local_path_present", f"Local private path is not allowed at {path_name}."))
        if any(token in normalized for token in LIVE_EXECUTION_TOKENS):
            issues.append(PromotionReadinessIssue("live_processor_execution_claim", f"Live processor execution claims are not allowed at {path_name}."))

    for flag_name in ACTIVE_PROMOTION_KEYS:
        if packet.get(flag_name) is True:
            issues.append(PromotionReadinessIssue("active_manifest_promotion_flag", f"Active manifest promotion flag must be false: {flag_name}."))

    return _dedupe_issues(issues)


def assert_promotion_readiness_packet(packet: Mapping[str, Any]) -> None:
    """Raise ValueError when a readiness packet is not promotion safe."""

    issues = validate_promotion_readiness_packet(packet)
    if issues:
        codes = ", ".join(issue.code for issue in issues)
        raise ValueError(f"Archive manifest promotion readiness packet failed validation: {codes}")


def _requires_abort_note(packet: Mapping[str, Any]) -> bool:
    return bool(packet.get("aborted") or packet.get("abort_required") or packet.get("status") == "aborted")


def _mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    return {}


def _string_sequence(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, Sequence):
        return [item for item in value if isinstance(item, str)]
    return []


def _text_or_none(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _non_empty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _walk_text(value: Any, prefix: str = "$") -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    if isinstance(value, str):
        found.append((prefix, value))
    elif isinstance(value, Mapping):
        for key, child in value.items():
            found.extend(_walk_text(child, f"{prefix}.{key}"))
    elif isinstance(value, Sequence) and not isinstance(value, bytes):
        for index, child in enumerate(value):
            found.extend(_walk_text(child, f"{prefix}[{index}]"))
    return found


def _looks_like_raw_output_path(path_name: str, normalized_value: str) -> bool:
    normalized_name = path_name.lower()
    if any(token in normalized_name for token in RAW_PATH_TOKENS):
        return True
    if any(token in normalized_value for token in RAW_PATH_TOKENS):
        return True
    parts = PurePosixPath(normalized_value).parts
    if any(part in {"raw", "raw_body", "downloads", "download", "archive-output"} for part in parts):
        return True
    return False


def _looks_like_private_path(normalized_value: str) -> bool:
    if normalized_value.startswith(PRIVATE_PATH_PREFIXES):
        return True
    if any(marker in normalized_value for marker in WINDOWS_PRIVATE_MARKERS):
        return True
    windows_parts = PureWindowsPath(normalized_value).parts
    return any(part.lower() == "users" for part in windows_parts)


def _dedupe_issues(issues: list[PromotionReadinessIssue]) -> list[PromotionReadinessIssue]:
    seen: set[tuple[str, str]] = set()
    deduped: list[PromotionReadinessIssue] = []
    for issue in issues:
        key = (issue.code, issue.message)
        if key not in seen:
            seen.add(key)
            deduped.append(issue)
    return deduped
