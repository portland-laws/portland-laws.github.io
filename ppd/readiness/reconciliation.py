"""Validate PP&D fixture-first implementation readiness packets."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

REQUIRED_DISABLED_CAPABILITIES = {
    "live_crawl",
    "devhub_authenticated_automation",
    "payment",
    "upload",
    "submission",
    "scheduling",
    "cancellation",
    "certification",
}

REQUIRED_LINKS = {
    "source_registry_update_candidate",
    "stale_guardrail_audit",
    "agent_response_regression_matrix",
    "attended_pilot_evidence_template",
}

_REQUIRED_LINK_FIELDS = ("fixture", "packet_id", "packet_version")
_REQUIRED_BLOCKER_FIELDS = ("id", "status", "summary", "source_evidence_ids")
_READY_FOR_PRODUCTION_LABELS = {
    "production_ready",
    "ready_for_production",
    "ready_for_release",
    "release_ready",
    "production",
    "ready",
}
_PRIVATE_OR_SESSION_KEY_MARKERS = (
    "auth_state",
    "browser_state",
    "cookie",
    "credential",
    "devhub_session",
    "har_path",
    "local_private_path",
    "password",
    "private_artifact",
    "private_value",
    "session_artifact",
    "session_storage",
    "screenshot",
    "storage_state",
    "trace_path",
)
_RAW_CRAWL_KEY_MARKERS = (
    "crawl_output",
    "downloaded_document_path",
    "raw_archive",
    "raw_body",
    "raw_crawl",
    "raw_html",
    "raw_response",
    "raw_text",
    "warc_path",
)
_PRIVATE_OR_SESSION_VALUE_MARKERS = (
    ".har",
    ".trace",
    "/.auth/",
    "/auth-state",
    "/browser-state",
    "/cookies",
    "/session",
    "/storage-state",
    "/trace",
    "/traces",
    "auth_state.json",
    "storage_state.json",
)
_RAW_CRAWL_VALUE_MARKERS = (
    ".warc",
    "/crawl-output/",
    "/downloaded-documents/",
    "/raw-crawl/",
    "/raw/",
    "raw_body",
    "raw_crawl_output",
)
_LOCAL_PRIVATE_PREFIXES = ("/home/", "/private/", "/tmp/", "/var/tmp/", "~/", "../", "./")
_ENABLEMENT_KEY_MARKERS = (
    "certification",
    "consequential",
    "devhub_authenticated_automation",
    "live_crawl",
    "official_action",
    "payment",
    "scheduling",
    "submission",
    "upload",
    "cancellation",
)
_ENABLEMENT_VALUE_MARKERS = {
    "allowed",
    "enabled",
    "execute",
    "permitted",
    "ready",
    "ready_for_action",
    "true",
    "yes",
}


def load_packet(path: Path) -> dict[str, Any]:
    """Load a readiness reconciliation packet from a committed fixture."""
    with path.open("r", encoding="utf-8") as handle:
        packet = json.load(handle)
    if not isinstance(packet, dict):
        raise ValueError("readiness packet must be a JSON object")
    return packet


def validate_packet(packet: Mapping[str, Any]) -> list[str]:
    """Return validation errors for a readiness reconciliation packet."""
    errors: list[str] = []

    if packet.get("mode") != "fixture_first":
        errors.append("mode must be fixture_first")

    evidence_ids = _validate_evidence_catalog(packet, errors)
    _validate_prerequisite_links(packet, errors)
    _validate_release_blockers(packet, evidence_ids, errors)
    _validate_disabled_capabilities(packet, errors)
    _validate_production_labels(packet, errors)
    _scan_for_private_or_raw_artifacts(packet, "packet", errors)
    _scan_for_consequential_enablement(packet, "packet", errors)

    forbidden_evidence = packet.get("forbidden_live_evidence_present")
    if forbidden_evidence is not False:
        errors.append("forbidden_live_evidence_present must be false")

    return errors


def _validate_evidence_catalog(packet: Mapping[str, Any], errors: list[str]) -> set[str]:
    catalog = packet.get("evidence_catalog")
    if not isinstance(catalog, list) or not catalog:
        errors.append("evidence_catalog must be a non-empty list")
        return set()

    evidence_ids: set[str] = set()
    for index, item in enumerate(catalog):
        if not isinstance(item, Mapping):
            errors.append(f"evidence_catalog[{index}] must be an object")
            continue
        evidence_id = item.get("evidence_id")
        if not _nonempty_text(evidence_id):
            errors.append(f"evidence_catalog[{index}].evidence_id is required")
            continue
        evidence_ids.add(str(evidence_id))
        if not _nonempty_text(item.get("citation")):
            errors.append(f"evidence_catalog[{index}].citation is required")
    return evidence_ids


def _validate_prerequisite_links(packet: Mapping[str, Any], errors: list[str]) -> None:
    links = packet.get("linked_artifacts")
    if not isinstance(links, Mapping):
        errors.append("linked_artifacts must be an object")
        links = {}

    missing_links = sorted(REQUIRED_LINKS.difference(str(key) for key in links.keys()))
    if missing_links:
        errors.append("missing linked artifacts: " + ", ".join(missing_links))

    for link_name in sorted(REQUIRED_LINKS):
        artifact = links.get(link_name)
        if not isinstance(artifact, Mapping):
            if link_name in links:
                errors.append(f"linked_artifacts.{link_name} must be an object")
            continue
        for field in _REQUIRED_LINK_FIELDS:
            if not _nonempty_text(artifact.get(field)):
                errors.append(f"linked_artifacts.{link_name}.{field} is required")


def _validate_release_blockers(packet: Mapping[str, Any], evidence_ids: set[str], errors: list[str]) -> None:
    blockers = packet.get("release_blockers")
    if not isinstance(blockers, list) or not blockers:
        errors.append("release_blockers must be a non-empty list")
        return

    for index, blocker in enumerate(blockers):
        if not isinstance(blocker, Mapping):
            errors.append(f"release_blockers[{index}] must be an object")
            continue
        for field in _REQUIRED_BLOCKER_FIELDS:
            if field == "source_evidence_ids":
                continue
            if not _nonempty_text(blocker.get(field)):
                errors.append(f"release_blockers[{index}].{field} is required")
        if blocker.get("status") != "blocking":
            errors.append(f"release_blockers[{index}].status must be blocking")

        cited_ids = blocker.get("source_evidence_ids")
        if not _text_list(cited_ids):
            errors.append(f"release_blockers[{index}].source_evidence_ids must be a non-empty list")
            continue
        unknown = sorted(set(str(item) for item in cited_ids).difference(evidence_ids))
        if unknown:
            errors.append(f"release_blockers[{index}] cites unknown evidence ids: " + ", ".join(unknown))


def _validate_disabled_capabilities(packet: Mapping[str, Any], errors: list[str]) -> None:
    disabled = packet.get("disabled_capabilities")
    if not isinstance(disabled, list):
        errors.append("disabled_capabilities must be a list")
        disabled_set: set[str] = set()
    else:
        disabled_set = {item for item in disabled if isinstance(item, str)}

    missing_disabled = sorted(REQUIRED_DISABLED_CAPABILITIES.difference(disabled_set))
    if missing_disabled:
        errors.append("missing disabled capabilities: " + ", ".join(missing_disabled))


def _validate_production_labels(packet: Mapping[str, Any], errors: list[str]) -> None:
    blockers = packet.get("release_blockers")
    unresolved = packet.get("unresolved_blockers")
    blockers_present = bool(blockers) or bool(unresolved)
    if not blockers_present:
        return

    if packet.get("production_ready") is True:
        errors.append("production_ready cannot be true while release blockers remain")

    for key in ("production_status", "release_status", "readiness_status", "readiness_label"):
        value = packet.get(key)
        if isinstance(value, str) and _normalized(value) in _READY_FOR_PRODUCTION_LABELS:
            errors.append(f"{key} cannot be {value!r} while release blockers remain")


def _scan_for_private_or_raw_artifacts(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            key_normalized = _normalized(key_text)
            child_path = f"{path}.{key_text}"
            if _contains_marker(key_normalized, _PRIVATE_OR_SESSION_KEY_MARKERS):
                errors.append(f"{child_path} private/session artifact field is not allowed")
            if _contains_marker(key_normalized, _RAW_CRAWL_KEY_MARKERS):
                errors.append(f"{child_path} raw crawl output reference is not allowed")
            _scan_for_private_or_raw_artifacts(child, child_path, errors)
        return

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _scan_for_private_or_raw_artifacts(child, f"{path}[{index}]", errors)
        return

    if isinstance(value, str):
        normalized = _normalized_path(value)
        if normalized.startswith(_LOCAL_PRIVATE_PREFIXES) or _contains_marker(normalized, _PRIVATE_OR_SESSION_VALUE_MARKERS):
            errors.append(f"{path} private/session artifact reference is not allowed")
        if _contains_marker(normalized, _RAW_CRAWL_VALUE_MARKERS):
            errors.append(f"{path} raw crawl output reference is not allowed")


def _scan_for_consequential_enablement(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            key_normalized = _normalized(key_text)
            child_path = f"{path}.{key_text}"
            if _contains_marker(key_normalized, _ENABLEMENT_KEY_MARKERS) and _is_enabled_value(child):
                errors.append(f"{child_path} consequential action enablement is not allowed")
            _scan_for_consequential_enablement(child, child_path, errors)
        return

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _scan_for_consequential_enablement(child, f"{path}[{index}]", errors)


def _is_enabled_value(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, str):
        return _normalized(value) in _ENABLEMENT_VALUE_MARKERS
    if isinstance(value, Mapping):
        for key in ("enabled", "allowed", "ready", "can_execute", "automation_allowed"):
            if _is_enabled_value(value.get(key)):
                return True
    return False


def _text_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(_nonempty_text(item) for item in value)


def _nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _contains_marker(value: str, markers: tuple[str, ...]) -> bool:
    return any(marker in value for marker in markers)


def _normalized(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def _normalized_path(value: str) -> str:
    return value.strip().replace("\\", "/").lower()
