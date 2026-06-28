"""Validation for PP&D agent readiness release blocker reconciliation packets.

The validator is deterministic and side-effect free. It rejects packet-shaped
metadata that would make release readiness look safer than the cited blocker and
prerequisite evidence supports.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Any, Mapping


@dataclass(frozen=True)
class ReleaseBlockerReconciliationValidationResult:
    """Machine-readable validation result for release blocker reconciliation."""

    ready: bool
    problems: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {"ready": self.ready, "problems": list(self.problems)}


_PRODUCTION_READY_LABELS = {
    "agent_ready",
    "production",
    "production_ready",
    "promotable",
    "ready",
    "ready_for_agent_use",
    "ready_for_production",
    "release_ready",
    "validated_for_release",
}
_UNRESOLVED_STATUSES = {
    "blocked",
    "deferred",
    "failed",
    "missing",
    "open",
    "pending",
    "unresolved",
}
_RESOLVED_STATUSES = {"closed", "complete", "completed", "resolved", "validated"}
_STALE_STATUSES = {"expired", "needs_refresh", "stale", "unknown", "unknown_stale"}
_CURRENT_STATUSES = {"current", "fresh", "verified_current"}
_PRIVATE_KEYS = {
    "access_token",
    "auth_state",
    "browser_state",
    "card_number",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "cvv",
    "devhub_session",
    "email",
    "field_value",
    "har",
    "local_path",
    "password",
    "payment_details",
    "phone",
    "private_artifact",
    "private_value",
    "raw_value",
    "refresh_token",
    "screenshot",
    "secret",
    "session",
    "session_artifact",
    "session_cookie",
    "session_state",
    "ssn",
    "token",
    "trace",
    "user_input",
    "user_supplied_value",
    "value",
}
_LOCAL_PATH_KEYS = {"file_path", "local_file_path", "local_path", "path", "private_file_path"}
_RAW_REFERENCE_KEYS = {
    "archive_artifact_ref",
    "archive_path",
    "crawl_output_path",
    "download_path",
    "download_ref",
    "downloaded_document",
    "raw_archive_ref",
    "raw_body",
    "raw_body_ref",
    "raw_content_ref",
    "raw_crawl_ref",
    "raw_download_ref",
    "raw_html",
    "raw_text",
    "warc_path",
    "warc_ref",
}
_LIVE_EXECUTION_KEYS = {
    "devhub_execution_claim",
    "devhub_execution_enabled",
    "executed_devhub",
    "live_crawl",
    "live_devhub_execution",
    "live_network",
    "live_network_enabled",
    "network_execution_claim",
    "ran_devhub",
    "ran_live_network",
}
_CONSEQUENTIAL_CLASSES = {
    "account_creation",
    "cancellation",
    "certification",
    "consequential",
    "consequential_official",
    "financial",
    "mfa",
    "official",
    "payment",
    "schedule_inspection",
    "submission",
    "upload",
    "upload_to_official_record",
}
_LOCAL_PRIVATE_PATH_RE = re.compile(
    r"(^file://)|(^/home/[^/]+/)|(^/Users/[^/]+/)|(^/private/)|(^~?/\.devhub/)|(^[A-Za-z]:\\Users\\[^\\]+\\)",
    re.IGNORECASE,
)
_RAW_REFERENCE_RE = re.compile(
    r"(\.warc(\.gz)?$|/data/raw/|/raw-crawl/|/downloads?/|archive://|raw_archive|raw_download)",
    re.IGNORECASE,
)
_GUARANTEE_RE = re.compile(
    r"\b(guarantee[sd]?|assure[sd]?|certain(?:ty)?|will be approved|will approve|permit will issue|approval is guaranteed|legally sufficient|code compliant)\b",
    re.IGNORECASE,
)
_LIVE_EXECUTION_RE = re.compile(
    r"\b(live network|live crawl|ran devhub|executed devhub|submitted in devhub|uploaded in devhub|scheduled in devhub|paid in devhub)\b",
    re.IGNORECASE,
)


def validate_agent_readiness_release_blocker_reconciliation_packet(
    packet: Mapping[str, Any],
    *,
    now: datetime | None = None,
    max_evidence_age_days: int = 45,
) -> ReleaseBlockerReconciliationValidationResult:
    """Return fail-closed validation for a release blocker reconciliation packet."""

    check_time = _normalize_now(now)
    evidence_by_id = _evidence_by_id(packet)
    prerequisite_ids = _prerequisite_ids(packet)
    blockers = _blockers(packet)

    problems: list[str] = []
    problems.extend(_blocker_problems(blockers, evidence_by_id, prerequisite_ids))
    problems.extend(_private_artifact_problems(packet))
    problems.extend(_raw_reference_problems(packet))
    problems.extend(_stale_current_claim_problems(packet, evidence_by_id, check_time, max_evidence_age_days))
    problems.extend(_production_ready_with_blockers_problems(packet, blockers))
    problems.extend(_guarantee_text_problems(packet))
    problems.extend(_live_execution_claim_problems(packet))
    problems.extend(_enabled_consequential_control_problems(packet))

    return ReleaseBlockerReconciliationValidationResult(ready=not problems, problems=tuple(problems))


def validate_release_blocker_reconciliation_packet(
    packet: Mapping[str, Any],
    *,
    now: datetime | None = None,
    max_evidence_age_days: int = 45,
) -> ReleaseBlockerReconciliationValidationResult:
    """Short alias for callers that do not need the full agent-readiness name."""

    return validate_agent_readiness_release_blocker_reconciliation_packet(
        packet,
        now=now,
        max_evidence_age_days=max_evidence_age_days,
    )


def require_agent_readiness_release_blocker_reconciliation_packet(
    packet: Mapping[str, Any],
    *,
    now: datetime | None = None,
    max_evidence_age_days: int = 45,
) -> None:
    """Raise ValueError when release blocker reconciliation is unsafe."""

    result = validate_agent_readiness_release_blocker_reconciliation_packet(
        packet,
        now=now,
        max_evidence_age_days=max_evidence_age_days,
    )
    if not result.ready:
        raise ValueError("invalid_release_blocker_reconciliation_packet: " + "; ".join(result.problems))


def _blocker_problems(
    blockers: list[Mapping[str, Any]],
    evidence_by_id: Mapping[str, Mapping[str, Any]],
    prerequisite_ids: set[str],
) -> list[str]:
    problems: list[str] = []
    for index, blocker in enumerate(blockers):
        blocker_id = _object_id(blocker) or f"index-{index}"
        refs = _collect_evidence_refs(blocker)
        if not refs:
            problems.append(f"release blocker lacks source_evidence_ids: {blocker_id}")
        for ref in sorted(refs):
            if ref not in evidence_by_id:
                problems.append(f"release blocker cites unknown source evidence {ref}: {blocker_id}")

        links = blocker.get("prerequisite_links") or blocker.get("prerequisites") or blocker.get("required_prerequisites")
        link_ids = _string_refs(links)
        if not link_ids:
            problems.append(f"release blocker lacks prerequisite_links: {blocker_id}")
        for link_id in sorted(link_ids):
            if prerequisite_ids and link_id not in prerequisite_ids:
                problems.append(f"release blocker references unknown prerequisite {link_id}: {blocker_id}")
    return problems


def _private_artifact_problems(value: Any, path: str = "$", key_name: str = "") -> list[str]:
    problems: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized_key = key_text.lower()
            child_path = f"{path}.{key_text}"
            if normalized_key in _PRIVATE_KEYS and child not in (None, "", [], {}):
                problems.append(f"private or session artifact is not allowed at {child_path}")
            if normalized_key in _LOCAL_PATH_KEYS and _contains_local_private_path(child):
                problems.append(f"local private path is not allowed at {child_path}")
            problems.extend(_private_artifact_problems(child, child_path, normalized_key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            problems.extend(_private_artifact_problems(child, f"{path}[{index}]", key_name))
    elif isinstance(value, str) and key_name in _LOCAL_PATH_KEYS and _LOCAL_PRIVATE_PATH_RE.search(value):
        problems.append(f"local private path is not allowed at {path}")
    return problems


def _raw_reference_problems(value: Any, path: str = "$", key_name: str = "") -> list[str]:
    problems: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized_key = key_text.lower()
            child_path = f"{path}.{key_text}"
            if normalized_key in _RAW_REFERENCE_KEYS and child not in (None, "", [], {}):
                problems.append(f"raw crawl/download/archive reference is not allowed at {child_path}")
            problems.extend(_raw_reference_problems(child, child_path, normalized_key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            problems.extend(_raw_reference_problems(child, f"{path}[{index}]", key_name))
    elif isinstance(value, str) and (key_name in _RAW_REFERENCE_KEYS or _RAW_REFERENCE_RE.search(value)):
        problems.append(f"raw crawl/download/archive reference is not allowed at {path}")
    return problems


def _stale_current_claim_problems(
    packet: Mapping[str, Any],
    evidence_by_id: Mapping[str, Mapping[str, Any]],
    now: datetime,
    max_evidence_age_days: int,
) -> list[str]:
    problems: list[str] = []
    stale_refs = _stale_refs(packet)
    acknowledgement_refs = _acknowledged_stale_refs(packet)
    acknowledged_all = packet.get("stale_current_acknowledged") is True or packet.get("stale_evidence_acknowledged") is True

    for evidence_id, evidence in evidence_by_id.items():
        status = str(evidence.get("freshness_status", "")).lower()
        timestamp = _parse_datetime(
            evidence.get("last_verified_at")
            or evidence.get("captured_at")
            or evidence.get("capture_finished_at")
            or evidence.get("updated_at")
        )
        age_stale = timestamp is not None and (now - timestamp).days > max_evidence_age_days
        claims_current = status in _CURRENT_STATUSES or evidence.get("current") is True
        known_stale = status in _STALE_STATUSES or evidence_id in stale_refs or age_stale
        acknowledged = acknowledged_all or evidence_id in acknowledgement_refs or evidence.get("stale_acknowledged") is True
        if claims_current and known_stale and not acknowledged:
            problems.append(f"stale source evidence is claimed current without acknowledgement: {evidence_id}")

    if stale_refs and not (acknowledged_all or acknowledgement_refs):
        problems.append("packet lists stale evidence without stale-current acknowledgement")
    return problems


def _production_ready_with_blockers_problems(packet: Mapping[str, Any], blockers: list[Mapping[str, Any]]) -> list[str]:
    if not _has_production_ready_label(packet):
        return []
    unresolved = [_object_id(blocker) or "" for blocker in blockers if _is_unresolved_blocker(blocker)]
    if unresolved:
        return ["production-ready release label is not allowed with unresolved blockers: " + ", ".join(sorted(unresolved))]
    if _non_empty(packet.get("unresolved_blockers")) or _non_empty(packet.get("open_blockers")):
        return ["production-ready release label is not allowed with unresolved blocker lists"]
    return []


def _guarantee_text_problems(value: Any, path: str = "$") -> list[str]:
    problems: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            problems.extend(_guarantee_text_problems(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            problems.extend(_guarantee_text_problems(child, f"{path}[{index}]"))
    elif isinstance(value, str) and _GUARANTEE_RE.search(value):
        problems.append(f"legal or permitting outcome guarantee is not allowed at {path}")
    return problems


def _live_execution_claim_problems(value: Any, path: str = "$", key_name: str = "") -> list[str]:
    problems: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized_key = key_text.lower()
            child_path = f"{path}.{key_text}"
            if normalized_key in _LIVE_EXECUTION_KEYS and child not in (False, None, "", [], {}):
                problems.append(f"live network or DevHub execution claim is not allowed at {child_path}")
            if normalized_key in {"execution_mode", "network_mode", "devhub_mode"} and isinstance(child, str):
                if child.lower() not in {"fixture", "metadata_only", "offline", "rehearsal", "manual_handoff"}:
                    problems.append(f"live network or DevHub execution mode is not allowed at {child_path}")
            problems.extend(_live_execution_claim_problems(child, child_path, normalized_key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            problems.extend(_live_execution_claim_problems(child, f"{path}[{index}]", key_name))
    elif isinstance(value, str) and _LIVE_EXECUTION_RE.search(value):
        problems.append(f"live network or DevHub execution claim is not allowed at {path}")
    return problems


def _enabled_consequential_control_problems(value: Any, path: str = "$") -> list[str]:
    problems: list[str] = []
    if isinstance(value, Mapping):
        action_class = _action_class(value)
        enabled = value.get("enabled") is True or value.get("control_enabled") is True or value.get("automation_enabled") is True
        if enabled and action_class in _CONSEQUENTIAL_CLASSES:
            problems.append(f"enabled consequential control is not allowed at {path}: {action_class}")
        for key, child in value.items():
            problems.extend(_enabled_consequential_control_problems(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            problems.extend(_enabled_consequential_control_problems(child, f"{path}[{index}]"))
    return problems


def _evidence_by_id(packet: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    records: dict[str, Mapping[str, Any]] = {}
    for key in ("normalized_source_evidence", "source_evidence", "citations", "sources"):
        raw = packet.get(key)
        if not isinstance(raw, list):
            continue
        for index, item in enumerate(raw):
            if not isinstance(item, Mapping):
                continue
            evidence_id = item.get("evidence_id") or item.get("source_evidence_id") or item.get("source_id")
            if isinstance(evidence_id, str) and evidence_id:
                records[evidence_id] = item
            else:
                records[f"{key}[{index}]"] = item
    return records


def _prerequisite_ids(packet: Mapping[str, Any]) -> set[str]:
    ids: set[str] = set()
    for key in ("prerequisites", "required_prerequisites", "release_prerequisites"):
        raw = packet.get(key)
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, Mapping):
                    item_id = item.get("prerequisite_id") or item.get("id") or item.get("requirement_id")
                    if isinstance(item_id, str) and item_id:
                        ids.add(item_id)
                elif isinstance(item, str) and item:
                    ids.add(item)
    return ids


def _blockers(packet: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    blockers: list[Mapping[str, Any]] = []
    for key in ("release_blockers", "blockers", "unresolved_blockers", "open_blockers"):
        raw = packet.get(key)
        if isinstance(raw, list):
            blockers.extend(item for item in raw if isinstance(item, Mapping))
    return blockers


def _is_unresolved_blocker(blocker: Mapping[str, Any]) -> bool:
    if blocker.get("resolved") is True:
        return False
    if blocker.get("unresolved") is True or blocker.get("blocking") is True:
        return True
    status = str(blocker.get("status") or blocker.get("resolution_status") or "").lower()
    if status in _RESOLVED_STATUSES:
        return False
    if status in _UNRESOLVED_STATUSES:
        return True
    return blocker.get("resolved") is not True


def _has_production_ready_label(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key).lower()
            if key_text in {"label", "release_label", "release_status", "readiness", "readiness_status", "status"}:
                if isinstance(child, str) and child.lower() in _PRODUCTION_READY_LABELS:
                    return True
            if _has_production_ready_label(child):
                return True
    elif isinstance(value, list):
        return any(_has_production_ready_label(item) for item in value)
    return False


def _stale_refs(packet: Mapping[str, Any]) -> set[str]:
    refs: set[str] = set()
    for key in ("stale_evidence", "stale_source_ids", "stale_source_evidence_ids"):
        refs.update(_string_refs(packet.get(key)))
    case_gap = packet.get("case_gap_report")
    if isinstance(case_gap, Mapping):
        refs.update(_string_refs(case_gap.get("stale_evidence")))
        refs.update(_string_refs(case_gap.get("stale_source_ids")))
    return refs


def _acknowledged_stale_refs(packet: Mapping[str, Any]) -> set[str]:
    refs: set[str] = set()
    for key in ("acknowledged_stale_evidence", "stale_acknowledgements", "stale_current_acknowledgements"):
        refs.update(_string_refs(packet.get(key)))
    return refs


def _collect_evidence_refs(value: Any) -> set[str]:
    refs: set[str] = set()
    if isinstance(value, Mapping):
        raw_many = value.get("source_evidence_ids")
        if isinstance(raw_many, list):
            refs.update(item for item in raw_many if isinstance(item, str) and item)
        raw_one = value.get("source_evidence_id")
        if isinstance(raw_one, str) and raw_one:
            refs.add(raw_one)
        for child in value.values():
            refs.update(_collect_evidence_refs(child))
    elif isinstance(value, list):
        for child in value:
            refs.update(_collect_evidence_refs(child))
    return refs


def _string_refs(value: Any) -> set[str]:
    refs: set[str] = set()
    if isinstance(value, str) and value:
        refs.add(value)
    elif isinstance(value, Mapping):
        for key in ("id", "prerequisite_id", "requirement_id", "source_evidence_id", "evidence_id", "source_id"):
            raw = value.get(key)
            if isinstance(raw, str) and raw:
                refs.add(raw)
    elif isinstance(value, list):
        for item in value:
            refs.update(_string_refs(item))
    return refs


def _contains_local_private_path(value: Any) -> bool:
    if isinstance(value, str):
        return bool(_LOCAL_PRIVATE_PATH_RE.search(value))
    if isinstance(value, list):
        return any(_contains_local_private_path(item) for item in value)
    if isinstance(value, Mapping):
        return any(_contains_local_private_path(item) for item in value.values())
    return False


def _action_class(value: Mapping[str, Any]) -> str | None:
    for key in ("action_class", "action_type", "classification", "control_type"):
        raw = value.get(key)
        if isinstance(raw, str) and raw:
            return raw.lower()
    return None


def _object_id(value: Mapping[str, Any]) -> str | None:
    for key in ("blocker_id", "id", "release_blocker_id"):
        raw = value.get(key)
        if isinstance(raw, str) and raw:
            return raw
    return None


def _non_empty(value: Any) -> bool:
    return isinstance(value, list) and len(value) > 0


def _normalize_now(now: datetime | None) -> datetime:
    if now is None:
        return datetime.now(timezone.utc)
    if now.tzinfo is None:
        return now.replace(tzinfo=timezone.utc)
    return now.astimezone(timezone.utc)


def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
