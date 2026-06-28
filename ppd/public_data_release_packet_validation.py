"""Validation for PP&D public-data dry-run release packets.

The validator is intentionally schema-light: release packet producers may add fields,
but these guardrails must remain present before a packet can be promoted.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional


PRIVATE_OR_SESSION_PATTERNS = (
    re.compile(r"(^|/)(\.daemon|devhub|session|sessions|auth|auth_state|storage_state|trace|traces)(/|$)", re.IGNORECASE),
    re.compile(r"(^|/)(cookies?|tokens?|secrets?)(\.|/|$)", re.IGNORECASE),
)

RAW_CRAWL_PATTERNS = (
    re.compile(r"(^|/)(raw[-_ ]?crawl|crawl[-_ ]?raw|downloaded[-_ ]?documents?|raw[-_ ]?downloads?)(/|$)", re.IGNORECASE),
    re.compile(r"\.(har|warc|pcap)$", re.IGNORECASE),
)


@dataclass(frozen=True)
class ReleasePacketValidationError:
    code: str
    message: str


def load_release_packet(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("release packet must be a JSON object")
    return data


def validate_release_packet(packet: Mapping[str, Any]) -> List[ReleasePacketValidationError]:
    """Return all blocking validation errors for a dry-run release packet."""
    errors: List[ReleasePacketValidationError] = []

    _validate_prerequisite_links(packet, errors)
    _validate_versions(packet, errors)
    _validate_operator_checklist(packet, errors)
    _validate_artifacts(packet, errors)
    _validate_consequential_action_readiness(packet, errors)
    _validate_production_signoff(packet, errors)

    return errors


def assert_valid_release_packet(packet: Mapping[str, Any]) -> None:
    errors = validate_release_packet(packet)
    if errors:
        details = "; ".join(error.code + ": " + error.message for error in errors)
        raise ValueError(details)


def _validate_prerequisite_links(packet: Mapping[str, Any], errors: List[ReleasePacketValidationError]) -> None:
    links = packet.get("prerequisite_packet_links")
    if not isinstance(links, list) or not links:
        errors.append(ReleasePacketValidationError("missing_prerequisite_packet_links", "release packet must link prerequisite packets"))
        return

    for index, link in enumerate(links):
        if isinstance(link, str):
            target = link.strip()
        elif isinstance(link, Mapping):
            target = str(link.get("url") or link.get("path") or link.get("packet") or "").strip()
        else:
            target = ""
        if not target:
            errors.append(ReleasePacketValidationError("missing_prerequisite_packet_link", "prerequisite link at index " + str(index) + " has no target"))


def _validate_versions(packet: Mapping[str, Any], errors: List[ReleasePacketValidationError]) -> None:
    expected = packet.get("expected_versions")
    if not isinstance(expected, Mapping):
        expected = {}

    for field_name in ("source_version", "guardrail_version"):
        actual_value = _string_value(packet.get(field_name))
        expected_value = _string_value(expected.get(field_name))
        if not actual_value:
            errors.append(ReleasePacketValidationError("missing_" + field_name, field_name + " is required"))
        elif expected_value and actual_value != expected_value:
            errors.append(ReleasePacketValidationError("stale_" + field_name, field_name + " " + actual_value + " does not match expected " + expected_value))


def _validate_operator_checklist(packet: Mapping[str, Any], errors: List[ReleasePacketValidationError]) -> None:
    checklist = packet.get("operator_checklist")
    if not isinstance(checklist, list) or not checklist:
        errors.append(ReleasePacketValidationError("missing_operator_checklist", "operator checklist is required"))
        return

    for index, item in enumerate(checklist):
        if not isinstance(item, Mapping):
            errors.append(ReleasePacketValidationError("invalid_operator_checklist_item", "checklist item " + str(index) + " must be an object"))
            continue
        citations = item.get("citations")
        citation = item.get("citation")
        has_citation_list = isinstance(citations, list) and any(str(value).strip() for value in citations)
        has_single_citation = isinstance(citation, str) and bool(citation.strip())
        if not has_citation_list and not has_single_citation:
            label = _string_value(item.get("label") or item.get("text") or item.get("id") or str(index))
            errors.append(ReleasePacketValidationError("uncited_operator_checklist_item", "operator checklist item " + label + " lacks citations"))


def _validate_artifacts(packet: Mapping[str, Any], errors: List[ReleasePacketValidationError]) -> None:
    for path in _artifact_paths(packet):
        normalized = path.replace("\\", "/")
        for pattern in PRIVATE_OR_SESSION_PATTERNS:
            if pattern.search(normalized):
                errors.append(ReleasePacketValidationError("private_or_session_artifact", "artifact is not releasable: " + path))
                break
        for pattern in RAW_CRAWL_PATTERNS:
            if pattern.search(normalized):
                errors.append(ReleasePacketValidationError("raw_crawl_output", "raw crawl output is not releasable: " + path))
                break


def _validate_consequential_action_readiness(packet: Mapping[str, Any], errors: List[ReleasePacketValidationError]) -> None:
    readiness = packet.get("consequential_action_readiness")
    if readiness is True:
        errors.append(ReleasePacketValidationError("consequential_action_readiness", "dry-run packet must not be ready for consequential action"))
    if isinstance(readiness, Mapping) and readiness.get("ready") is True:
        errors.append(ReleasePacketValidationError("consequential_action_readiness", "dry-run packet must not be ready for consequential action"))

    release_mode = _string_value(packet.get("release_mode") or packet.get("mode")).lower()
    if release_mode and release_mode != "dry-run":
        errors.append(ReleasePacketValidationError("non_dry_run_release_mode", "public-data release packet validation only permits dry-run mode"))


def _validate_production_signoff(packet: Mapping[str, Any], errors: List[ReleasePacketValidationError]) -> None:
    target = _string_value(packet.get("promotion_target") or packet.get("target_environment") or packet.get("environment")).lower()
    if target not in ("production", "prod"):
        return

    signoff = packet.get("human_signoff")
    if not isinstance(signoff, Mapping) or signoff.get("approved") is not True or not _string_value(signoff.get("by")):
        errors.append(ReleasePacketValidationError("missing_human_signoff", "production promotion requires explicit human signoff"))


def _artifact_paths(packet: Mapping[str, Any]) -> Iterable[str]:
    artifacts = packet.get("artifacts")
    if isinstance(artifacts, list):
        for artifact in artifacts:
            if isinstance(artifact, str):
                yield artifact
            elif isinstance(artifact, Mapping):
                value = artifact.get("path") or artifact.get("uri") or artifact.get("href")
                if value is not None:
                    yield str(value)

    manifest = packet.get("manifest")
    if isinstance(manifest, Mapping):
        for value in manifest.values():
            if isinstance(value, str):
                yield value
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        yield item
                    elif isinstance(item, Mapping):
                        nested_value = item.get("path") or item.get("uri") or item.get("href")
                        if nested_value is not None:
                            yield str(nested_value)


def _string_value(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


__all__ = [
    "ReleasePacketValidationError",
    "assert_valid_release_packet",
    "load_release_packet",
    "validate_release_packet",
]
