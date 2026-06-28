"""Validation for PP&D post-release audit findings packets.

The checks here are intentionally deterministic and side-effect free. They are
meant for release/audit packets assembled from fixtures or normalized metadata,
not for live DevHub, crawler, or network execution.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping


@dataclass(frozen=True)
class PostReleaseAuditValidationResult:
    """Machine-readable validation result for post-release audit packets."""

    ready: bool
    problems: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {"ready": self.ready, "problems": list(self.problems)}


_FINDING_KEYS = {"finding", "findings", "audit_finding", "audit_findings"}
_CITATION_KEYS = {"source_evidence_id", "source_evidence_ids", "citation_id", "citation_ids", "citations"}
_PRIVATE_KEYS = {
    "access_token",
    "auth_state",
    "browser_context",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "devhub_session",
    "email",
    "har",
    "local_path",
    "password",
    "payment_details",
    "phone",
    "private_artifact",
    "private_file_path",
    "raw_value",
    "refresh_token",
    "secret",
    "session",
    "session_cookie",
    "session_file",
    "session_state",
    "storage_state",
    "token",
    "trace",
    "user_input",
    "value",
}
_LOCAL_PATH_KEYS = {"file_path", "local_file_path", "local_path", "path", "private_file_path", "session_file"}
_RAW_REFERENCE_KEYS = {
    "archive_artifact_ref",
    "archive_path",
    "crawl_output",
    "download_artifact_ref",
    "download_path",
    "downloaded_document",
    "raw_archive_ref",
    "raw_body",
    "raw_crawl_ref",
    "raw_download_ref",
    "raw_html",
    "raw_text",
    "warc_path",
}
_PRODUCTION_READY_VALUES = {"production", "production_ready", "ready_for_production", "release_ready"}
_BLOCKER_KEYS = {"blocker", "blockers", "open_blockers", "unresolved_blockers", "known_blockers"}
_LIVE_EXECUTION_KEYS = {
    "devhub_execution_claim",
    "devhub_execution_enabled",
    "execute_devhub",
    "execute_live_network",
    "live_devhub",
    "live_devhub_execution",
    "live_network",
    "live_network_execution",
    "network_execution_enabled",
    "ran_devhub",
    "ran_live_crawl",
}
_ENABLED_CAPABILITY_KEYS = {
    "cancellation_enabled",
    "certification_enabled",
    "payment_enabled",
    "scheduling_enabled",
    "submission_enabled",
    "upload_enabled",
}
_BLOCKED_CAPABILITY_TYPES = {
    "cancel",
    "cancellation",
    "certification",
    "certify",
    "payment",
    "schedule",
    "schedule_inspection",
    "scheduling",
    "submission",
    "submit",
    "upload",
    "upload_to_official_record",
}
_ALLOWED_CAPABILITY_STATES = {"blocked", "disabled", "manual_handoff_required", "refused"}
_LOCAL_PRIVATE_PATH_RE = re.compile(
    r"(^file://)|(^/home/[^/]+/)|(^/Users/[^/]+/)|(^/private/)|(^~?/\.devhub/)|(^[A-Za-z]:\\Users\\[^\\]+\\)",
    re.IGNORECASE,
)
_RAW_REFERENCE_RE = re.compile(
    r"(\.har$|\.trace$|trace\.zip$|\.warc(\.gz)?$|raw-crawl|raw_download|/downloads?/|/archives?/|archive_artifact|download_artifact)",
    re.IGNORECASE,
)
_GUARANTEE_RE = re.compile(
    r"\b(guarantee[sd]?|ensures?|will)\b.{0,80}\b(approval|approved|permit issuance|legal compliance|code compliant|permitting outcome)\b|\b(approved|legal|code compliant)\b.{0,40}\bguarantee[sd]?\b",
    re.IGNORECASE,
)
_LIVE_EXECUTION_RE = re.compile(
    r"\b(live network|live devhub|executed in devhub|ran against devhub|performed live crawl|submitted through devhub)\b",
    re.IGNORECASE,
)


def validate_post_release_audit_findings_packet(packet: Mapping[str, Any]) -> PostReleaseAuditValidationResult:
    """Return fail-closed validation for a PP&D post-release audit findings packet."""

    problems: list[str] = []
    evidence_ids = _evidence_ids(packet)
    problems.extend(_finding_citation_problems(packet, evidence_ids))
    problems.extend(_private_artifact_problems(packet))
    problems.extend(_raw_reference_problems(packet))
    problems.extend(_guarantee_claim_problems(packet))
    problems.extend(_production_ready_blocker_problems(packet))
    problems.extend(_live_execution_claim_problems(packet))
    problems.extend(_enabled_capability_problems(packet))
    return PostReleaseAuditValidationResult(ready=not problems, problems=tuple(problems))


def require_post_release_audit_findings_packet(packet: Mapping[str, Any]) -> None:
    """Raise ValueError when a post-release audit findings packet is unsafe."""

    result = validate_post_release_audit_findings_packet(packet)
    if not result.ready:
        raise ValueError("invalid_post_release_audit_findings_packet: " + "; ".join(result.problems))


def _finding_citation_problems(value: Any, evidence_ids: set[str], path: str = "$") -> list[str]:
    problems: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if str(key).lower() in _FINDING_KEYS:
                findings = child if isinstance(child, list) else [child]
                for index, finding in enumerate(findings):
                    finding_path = f"{child_path}[{index}]"
                    refs = _collect_evidence_refs(finding)
                    if not refs:
                        problems.append(f"audit finding lacks citation at {finding_path}")
                    for ref in sorted(refs):
                        if ref not in evidence_ids:
                            problems.append(f"audit finding cites unknown source evidence {ref} at {finding_path}")
            problems.extend(_finding_citation_problems(child, evidence_ids, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            problems.extend(_finding_citation_problems(child, evidence_ids, f"{path}[{index}]"))
    return problems


def _private_artifact_problems(value: Any, path: str = "$") -> list[str]:
    problems: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized_key = key_text.lower()
            child_path = f"{path}.{key_text}"
            if normalized_key in _PRIVATE_KEYS and child not in (None, False, "", [], {}):
                problems.append(f"private or session artifact is not allowed at {child_path}")
            if normalized_key in _LOCAL_PATH_KEYS and _contains_local_private_path(child):
                problems.append(f"local private path is not allowed at {child_path}")
            problems.extend(_private_artifact_problems(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            problems.extend(_private_artifact_problems(child, f"{path}[{index}]"))
    return problems


def _raw_reference_problems(value: Any, path: str = "$") -> list[str]:
    problems: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text.lower() in _RAW_REFERENCE_KEYS and child not in (None, False, "", [], {}):
                problems.append(f"raw crawl/download/archive reference is not allowed at {child_path}")
            if _contains_raw_reference(child):
                problems.append(f"raw crawl/download/archive reference is not allowed at {child_path}")
            problems.extend(_raw_reference_problems(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            problems.extend(_raw_reference_problems(child, f"{path}[{index}]"))
    return problems


def _guarantee_claim_problems(value: Any, path: str = "$") -> list[str]:
    problems: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text.lower() in {"guarantee", "guarantees", "outcome_guarantee", "legal_guarantee"} and child not in (None, False, "", [], {}):
                problems.append(f"legal or permitting outcome guarantee is not allowed at {child_path}")
            problems.extend(_guarantee_claim_problems(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            problems.extend(_guarantee_claim_problems(child, f"{path}[{index}]"))
    elif isinstance(value, str) and _GUARANTEE_RE.search(value):
        problems.append(f"legal or permitting outcome guarantee is not allowed at {path}")
    return problems


def _production_ready_blocker_problems(packet: Mapping[str, Any]) -> list[str]:
    has_production_ready_label = _contains_production_ready_label(packet)
    if not has_production_ready_label:
        return []
    blockers = _collect_blockers(packet)
    if blockers:
        return ["production-ready label is not allowed while unresolved blockers remain"]
    return []


def _live_execution_claim_problems(value: Any, path: str = "$") -> list[str]:
    problems: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text.lower() in _LIVE_EXECUTION_KEYS and child not in (None, False, "", [], {}):
                problems.append(f"live network or DevHub execution claim is not allowed at {child_path}")
            problems.extend(_live_execution_claim_problems(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            problems.extend(_live_execution_claim_problems(child, f"{path}[{index}]"))
    elif isinstance(value, str) and _LIVE_EXECUTION_RE.search(value):
        problems.append(f"live network or DevHub execution claim is not allowed at {path}")
    return problems


def _enabled_capability_problems(value: Any, path: str = "$") -> list[str]:
    problems: list[str] = []
    if isinstance(value, Mapping):
        capability_type = _capability_type(value)
        state = str(value.get("state") or value.get("status") or value.get("decision") or "").lower()
        enabled = value.get("enabled") is True or value.get("allowed") is True or state in {"enabled", "allowed", "ready"}
        if capability_type in _BLOCKED_CAPABILITY_TYPES and enabled and state not in _ALLOWED_CAPABILITY_STATES:
            problems.append(f"blocked consequential capability is enabled at {path}: {capability_type}")
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text.lower() in _ENABLED_CAPABILITY_KEYS and child is True:
                problems.append(f"blocked consequential capability flag is enabled at {child_path}")
            problems.extend(_enabled_capability_problems(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            problems.extend(_enabled_capability_problems(child, f"{path}[{index}]"))
    return problems


def _evidence_ids(packet: Mapping[str, Any]) -> set[str]:
    ids: set[str] = set()
    for key in ("normalized_source_evidence", "citations", "sources", "source_registry"):
        raw = packet.get(key)
        if not isinstance(raw, list):
            continue
        for item in raw:
            if not isinstance(item, Mapping):
                continue
            for id_key in ("evidence_id", "source_evidence_id", "citation_id", "source_id"):
                value = item.get(id_key)
                if isinstance(value, str) and value:
                    ids.add(value)
    return ids


def _collect_evidence_refs(value: Any) -> set[str]:
    refs: set[str] = set()
    if isinstance(value, Mapping):
        for key in _CITATION_KEYS:
            raw = value.get(key)
            if isinstance(raw, str) and raw:
                refs.add(raw)
            elif isinstance(raw, list):
                for item in raw:
                    if isinstance(item, str) and item:
                        refs.add(item)
                    elif isinstance(item, Mapping):
                        refs.update(_collect_evidence_refs(item))
        for child in value.values():
            refs.update(_collect_evidence_refs(child))
    elif isinstance(value, list):
        for child in value:
            refs.update(_collect_evidence_refs(child))
    return refs


def _contains_local_private_path(value: Any) -> bool:
    if isinstance(value, str):
        return bool(_LOCAL_PRIVATE_PATH_RE.search(value))
    if isinstance(value, list):
        return any(_contains_local_private_path(item) for item in value)
    if isinstance(value, Mapping):
        return any(_contains_local_private_path(item) for item in value.values())
    return False


def _contains_raw_reference(value: Any) -> bool:
    if isinstance(value, str):
        return bool(_RAW_REFERENCE_RE.search(value))
    if isinstance(value, list):
        return any(_contains_raw_reference(item) for item in value)
    return False


def _contains_production_ready_label(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key).lower() in {"production_ready", "ready_for_production"} and child is True:
                return True
            if _contains_production_ready_label(child):
                return True
    elif isinstance(value, list):
        return any(_contains_production_ready_label(item) for item in value)
    elif isinstance(value, str):
        return value.strip().lower() in _PRODUCTION_READY_VALUES
    return False


def _collect_blockers(value: Any) -> list[Any]:
    blockers: list[Any] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key).lower() in _BLOCKER_KEYS and child not in (None, False, "", [], {}):
                blockers.append(child)
            blockers.extend(_collect_blockers(child))
    elif isinstance(value, list):
        for child in value:
            blockers.extend(_collect_blockers(child))
    return blockers


def _capability_type(value: Mapping[str, Any]) -> str | None:
    for key in ("capability", "capability_type", "action", "action_class", "action_type", "name"):
        raw = value.get(key)
        if isinstance(raw, str) and raw:
            normalized = raw.strip().lower()
            if normalized in _BLOCKED_CAPABILITY_TYPES:
                return normalized
    return None
