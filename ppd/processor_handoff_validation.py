"""Validation for PP&D processor handoff dry-run packets.

The processor handoff boundary must stay metadata-only, policy-preflighted,
and replayable. This module intentionally accepts plain dictionaries so callers
can validate decoded JSON before constructing richer contracts.
"""

from __future__ import annotations

from ipaddress import ip_address
from typing import Any
from urllib.parse import parse_qsl, urlparse


_POLICY_EVIDENCE_KEYS = (
    "policy_preflight_evidence",
    "policyPreflightEvidence",
    "preflight_evidence",
)

_CONTRACT_ID_KEYS = (
    "processor_contract_id",
    "processorContractId",
    "processor_contract_identifier",
    "processorContractIdentifier",
    "contract_id",
)

_CONTRACT_VERSION_KEYS = (
    "processor_contract_version",
    "processorContractVersion",
    "contract_version",
    "contractVersion",
    "processor_version",
    "processorVersion",
)

_LIVE_EXECUTION_KEYS = {
    "allow_live_execution",
    "allow_live_network",
    "allow_network",
    "execute_live",
    "execution_enabled",
    "live_execution",
    "live_network",
    "network_enabled",
    "perform_execution",
    "run_live",
    "use_live_network",
    "allowLiveExecution",
    "allowLiveNetwork",
    "allowNetwork",
    "executeLive",
    "executionEnabled",
    "liveExecution",
    "liveNetwork",
    "networkEnabled",
    "performExecution",
    "runLive",
    "useLiveNetwork",
}

_DRY_RUN_KEYS = {
    "dry_run",
    "dryRun",
    "metadata_only_dry_run",
    "metadataOnlyDryRun",
}

_RAW_BODY_KEYS = {
    "archive_body",
    "body",
    "content",
    "html",
    "raw_archive",
    "raw_body",
    "raw_content",
    "raw_html",
    "response_body",
    "text",
}

_RAW_PERSISTENCE_KEYS = {
    "archive_raw_body",
    "commit_raw_archive",
    "persist_archive",
    "persist_raw_archive",
    "persist_raw_body",
    "persistRawArchive",
    "persistRawBody",
    "raw_archive_persistence",
    "rawArchivePersistence",
    "save_raw_archive",
    "saveRawArchive",
    "store_raw_body",
    "storeRawBody",
}

_LOCAL_PATH_KEYS = {
    "download_path",
    "downloadPath",
    "downloaded_document_path",
    "downloadedDocumentPath",
    "downloaded_path",
    "downloadedPath",
    "file_path",
    "filePath",
    "filesystem_path",
    "filesystemPath",
    "local_path",
    "localPath",
    "path",
}

_NORMALIZED_DOCUMENT_KEYS = {
    "normalized_document_id",
    "normalizedDocumentId",
    "normalized_document_ref",
    "normalizedDocumentRef",
    "normalized_document_reference",
    "normalizedDocumentReference",
}

_SOURCE_REGISTRY_KEYS = {
    "source_registry_id",
    "sourceRegistryId",
    "source_id",
    "sourceId",
}

_SKIP_FLAG_KEYS = {"skipped", "skip", "is_skipped", "isSkipped"}
_SKIP_REASON_KEYS = {"skip_reason", "skipReason", "skipped_reason", "skippedReason", "reason"}
_UNACTIONABLE_SKIP_REASONS = {
    "",
    "n/a",
    "na",
    "none",
    "null",
    "other",
    "skip",
    "skipped",
    "todo",
    "tbd",
    "unknown",
    "unspecified",
}
_ACTIONABLE_SKIP_REASONS = {
    "outside_allowlist",
    "unsupported_scheme",
    "private_authenticated",
    "disallowed_by_robots",
    "disallowed_by_policy",
    "raw_download_not_permitted",
    "too_large",
    "unsupported_content_type",
    "policy_preflight_failed",
    "missing_source_registry_id",
}

_ARTIFACT_KEYS = ("artifacts", "artifact_references", "artifactReferences")
_RATE_LIMIT_KEYS = ("rate_limit", "rateLimit", "rate_limits", "rateLimits")
_UNBOUNDED_VALUES = {"", "none", "null", "unbounded", "unlimited", "infinite", "inf", "no_limit"}
_AUTH_QUERY_KEYS = {
    "access_token",
    "api_key",
    "apikey",
    "auth",
    "authorization",
    "key",
    "password",
    "signature",
    "sig",
    "token",
}


def validate_processor_handoff_packet(packet: dict[str, Any]) -> list[str]:
    """Return validation errors for an unsafe processor handoff dry-run packet."""

    errors: list[str] = []
    if not isinstance(packet, dict):
        return ["handoff packet must be an object"]

    if not _has_policy_preflight_evidence(packet):
        errors.append("missing policy preflight evidence")

    contract_id = _first_present(packet, _CONTRACT_ID_KEYS)
    if not isinstance(contract_id, str) or not contract_id.strip():
        errors.append("missing processor contract identifier")

    contract_version = _first_present(packet, _CONTRACT_VERSION_KEYS)
    if not isinstance(contract_version, str) or not contract_version.strip():
        errors.append("missing processor contract version")

    rate_limit = _first_present(packet, _RATE_LIMIT_KEYS)
    if not _has_bounded_rate_limit(rate_limit):
        errors.append("missing bounded rate limit")

    _scan_value(packet, "$", errors)
    _validate_artifacts(packet, errors)
    return errors


def assert_valid_processor_handoff_packet(packet: dict[str, Any]) -> None:
    """Raise ValueError when a handoff packet fails validation."""

    errors = validate_processor_handoff_packet(packet)
    if errors:
        raise ValueError("invalid processor handoff packet: " + "; ".join(errors))


def _first_present(packet: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in packet:
            return packet[key]
    return None


def _has_policy_preflight_evidence(packet: dict[str, Any]) -> bool:
    evidence = _first_present(packet, _POLICY_EVIDENCE_KEYS)
    if not isinstance(evidence, dict) or not evidence:
        return False
    return any(isinstance(value, str) and value.strip() for value in evidence.values())


def _has_bounded_rate_limit(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() not in _UNBOUNDED_VALUES
    if not isinstance(value, dict):
        return False

    if str(value.get("mode", "")).strip().lower() in _UNBOUNDED_VALUES:
        return False

    request_limit = _positive_number(value.get("max_requests", value.get("requests", value.get("limit"))))
    window = _positive_number(value.get("per_seconds", value.get("window_seconds", value.get("seconds"))))
    return request_limit and window


def _positive_number(value: Any) -> bool:
    if isinstance(value, bool) or value is None:
        return False
    try:
        return float(value) > 0
    except (TypeError, ValueError):
        return False


def _scan_value(value: Any, location: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        _validate_skipped_object(value, location, errors)
        _validate_normalized_document_reference(value, location, errors)
        for key, item in value.items():
            key_text = str(key)
            item_location = f"{location}.{key_text}"
            if key_text in _LIVE_EXECUTION_KEYS and bool(item):
                errors.append(f"live execution flag is not allowed at {item_location}")
            if key_text in _DRY_RUN_KEYS and item is not True:
                errors.append(f"dry-run packet cannot disable dry-run mode at {item_location}")
            if key_text in _RAW_BODY_KEYS and _has_payload(item):
                errors.append(f"raw archive/body field is not allowed at {item_location}")
            if key_text in _RAW_PERSISTENCE_KEYS and bool(item):
                errors.append(f"raw archive persistence is not allowed at {item_location}")
            if key_text in _LOCAL_PATH_KEYS and _looks_like_local_path(item):
                errors.append(f"local downloaded document path is not allowed at {item_location}")
            if isinstance(item, str) and _is_private_or_authenticated_url(item):
                errors.append(f"private or authenticated URL is not allowed at {item_location}")
            _scan_value(item, item_location, errors)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _scan_value(item, f"{location}[{index}]", errors)
    elif isinstance(value, str) and _is_private_or_authenticated_url(value):
        errors.append(f"private or authenticated URL is not allowed at {location}")


def _validate_skipped_object(value: dict[str, Any], location: str, errors: list[str]) -> None:
    status = str(value.get("status", "")).strip().lower()
    skipped = status == "skipped" or any(value.get(key) is True for key in _SKIP_FLAG_KEYS)
    if not skipped:
        return
    reason = _first_text(value, _SKIP_REASON_KEYS)
    normalized = reason.strip().lower().replace("-", "_").replace(" ", "_")
    if normalized in _UNACTIONABLE_SKIP_REASONS or normalized not in _ACTIONABLE_SKIP_REASONS:
        errors.append(f"unactionable skip reason is not allowed at {location}")


def _validate_normalized_document_reference(value: dict[str, Any], location: str, errors: list[str]) -> None:
    has_normalized_reference = any(_has_payload(value.get(key)) for key in _NORMALIZED_DOCUMENT_KEYS)
    if not has_normalized_reference:
        return
    has_source_registry_id = any(isinstance(value.get(key), str) and value.get(key, "").strip() for key in _SOURCE_REGISTRY_KEYS)
    if not has_source_registry_id:
        errors.append(f"normalized document reference requires source registry id at {location}")


def _first_text(value: dict[str, Any], keys: set[str]) -> str:
    for key in keys:
        item = value.get(key)
        if isinstance(item, str):
            return item
    return ""


def _has_payload(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (bytes, bytearray)):
        return len(value) > 0
    if isinstance(value, (list, dict, tuple, set)):
        return len(value) > 0
    return True


def _looks_like_local_path(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    text = value.strip()
    if not text:
        return False
    return (
        text.startswith("/")
        or text.startswith("./")
        or text.startswith("../")
        or text.startswith("~/")
        or text.startswith("file://")
        or "\\" in text
    )


def _is_private_or_authenticated_url(value: str) -> bool:
    parsed = urlparse(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False
    if parsed.username or parsed.password:
        return True

    query_keys = {key.lower() for key, _ in parse_qsl(parsed.query, keep_blank_values=True)}
    if query_keys & _AUTH_QUERY_KEYS:
        return True

    host = parsed.hostname or ""
    if host in {"localhost", "127.0.0.1", "0.0.0.0"}:
        return True
    try:
        address = ip_address(host)
    except ValueError:
        return False
    return address.is_private or address.is_loopback or address.is_link_local


def _validate_artifacts(packet: dict[str, Any], errors: list[str]) -> None:
    artifacts = None
    for key in _ARTIFACT_KEYS:
        if key in packet:
            artifacts = packet[key]
            break
    if artifacts is None:
        return
    if not isinstance(artifacts, list):
        errors.append("artifact references must be a list")
        return
    for index, artifact in enumerate(artifacts):
        location = f"$.artifacts[{index}]"
        if not isinstance(artifact, dict):
            errors.append(f"artifact reference must be an object at {location}")
            continue
        if artifact.get("metadata_only") is not True and artifact.get("metadataOnly") is not True:
            errors.append(f"artifact reference must be metadata-only at {location}")
        for key in _RAW_BODY_KEYS | _LOCAL_PATH_KEYS:
            if key in artifact and _has_payload(artifact[key]):
                errors.append(f"artifact reference contains non-metadata field at {location}.{key}")
