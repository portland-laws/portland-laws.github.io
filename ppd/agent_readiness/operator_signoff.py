"""Operator signoff validation for PP&D implementation-readiness packets.

The validator is deterministic and side-effect free. It is intentionally narrow:
operator signoff packets must be metadata-only, ledger-linked, reviewer-signed,
free of private or raw crawl artifacts, and blocked from production promotion
unless an explicit signed approval is present.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

_READY_STATUSES = {"ready", "implementation_ready", "approved", "promotable"}
_RESOLVED_BLOCKER_STATUSES = {"resolved", "waived", "accepted_risk"}
_CURRENT_PREREQUISITE_STATUSES = {"current", "accepted", "validated", "version_current"}

_PRIVATE_OR_SESSION_KEYS = {
    "access_token",
    "auth_state",
    "browser_context",
    "card_number",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "cvv",
    "email",
    "file_path",
    "har",
    "local_path",
    "password",
    "payment_details",
    "phone",
    "playwright_state",
    "private_value",
    "refresh_token",
    "secret",
    "session_artifact",
    "session_cookie",
    "session_state",
    "screenshot",
    "storage_state",
    "token",
    "trace",
    "user_input",
    "value",
}

_RAW_CRAWL_KEYS = {
    "body",
    "crawl_output_path",
    "downloaded_document",
    "html",
    "raw_body",
    "raw_crawl_output",
    "raw_html",
    "raw_output_ref",
    "raw_text",
    "warc_path",
}

_PRIVATE_STRING_MARKERS = (
    ".har",
    "auth-state",
    "auth_state",
    "cookies.json",
    "playwright/.auth",
    "session-state",
    "session_state",
    "storage-state",
    "storage_state",
    "trace.zip",
)

_RAW_CRAWL_STRING_MARKERS = (
    ".warc",
    "/raw/",
    "raw-crawl",
    "raw_crawl",
    "raw-output",
    "raw_output",
)


class OperatorSignoffReadinessError(ValueError):
    """Raised when an operator signoff packet is not implementation-ready."""

    def __init__(self, problems: Iterable[str]) -> None:
        self.problems = tuple(problems)
        super().__init__("invalid_operator_signoff_readiness_packet: " + "; ".join(self.problems))


@dataclass(frozen=True)
class OperatorSignoffValidationResult:
    """Machine-readable operator signoff validation result."""

    ready: bool
    problems: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {"ready": self.ready, "problems": list(self.problems)}


def validate_operator_signoff_readiness_packet(packet: Mapping[str, Any]) -> OperatorSignoffValidationResult:
    """Validate an operator signoff implementation-readiness packet fail-closed."""

    problems: list[str] = []
    problems.extend(_ledger_link_problems(packet.get("ledger_links")))
    problems.extend(_reviewer_signoff_problems(packet.get("reviewer_signoffs") or packet.get("reviewers")))
    problems.extend(_blocker_readiness_problems(packet))
    problems.extend(_prerequisite_version_problems(packet.get("prerequisite_packets")))
    problems.extend(_artifact_boundary_problems(packet))
    problems.extend(_production_promotion_problems(packet))
    return OperatorSignoffValidationResult(ready=not problems, problems=tuple(problems))


def require_operator_signoff_readiness_packet(packet: Mapping[str, Any]) -> None:
    """Raise when an operator signoff packet is not implementation-ready."""

    result = validate_operator_signoff_readiness_packet(packet)
    if not result.ready:
        raise OperatorSignoffReadinessError(result.problems)


def _ledger_link_problems(value: Any) -> list[str]:
    if not isinstance(value, list) or not value:
        return ["operator signoff packet is missing ledger_links"]

    problems: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            problems.append(f"ledger_links[{index}] must be an object")
            continue
        if not _non_empty_string(item.get("ledger_id")):
            problems.append(f"ledger_links[{index}] is missing ledger_id")
        if not any(_non_empty_string(item.get(key)) for key in ("ledger_ref", "href", "path", "entry_id")):
            problems.append(f"ledger_links[{index}] is missing a ledger reference")
    return problems


def _reviewer_signoff_problems(value: Any) -> list[str]:
    if not isinstance(value, list) or not value:
        return ["operator signoff packet is missing reviewer_signoffs"]

    problems: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            problems.append(f"reviewer_signoffs[{index}] must be an object")
            continue
        if not _non_empty_string(item.get("reviewer_id")):
            problems.append(f"reviewer_signoffs[{index}] is missing reviewer_id")
        if not _non_empty_string(item.get("reviewer_role")):
            problems.append(f"reviewer_signoffs[{index}] is missing reviewer_role")
        if _parse_datetime(item.get("signed_at")) is None:
            problems.append(f"reviewer_signoffs[{index}] is missing a valid signed_at timestamp")
    return problems


def _blocker_readiness_problems(packet: Mapping[str, Any]) -> list[str]:
    readiness = str(packet.get("readiness_status") or packet.get("status") or "").lower()
    blockers = packet.get("blockers")
    if readiness not in _READY_STATUSES or not isinstance(blockers, list):
        return []

    problems: list[str] = []
    for index, blocker in enumerate(blockers):
        if not isinstance(blocker, Mapping):
            problems.append(f"blockers[{index}] must be an object")
            continue
        status = str(blocker.get("status") or blocker.get("resolution_status") or "").lower()
        if status not in _RESOLVED_BLOCKER_STATUSES:
            blocker_id = blocker.get("blocker_id") or f"index-{index}"
            problems.append(f"unresolved blocker is marked ready: {blocker_id}")
    return problems


def _prerequisite_version_problems(value: Any) -> list[str]:
    if not isinstance(value, list) or not value:
        return ["operator signoff packet is missing prerequisite_packets"]

    problems: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            problems.append(f"prerequisite_packets[{index}] must be an object")
            continue
        packet_id = item.get("packet_id") or f"index-{index}"
        version = item.get("version")
        expected = item.get("expected_version") or item.get("minimum_accepted_version")
        status = str(item.get("freshness_status") or item.get("version_status") or "current").lower()
        if not _non_empty_string(packet_id):
            problems.append(f"prerequisite_packets[{index}] is missing packet_id")
        if not _non_empty_string(version):
            problems.append(f"prerequisite packet {packet_id} is missing version")
        if expected is not None and version != expected:
            problems.append(f"prerequisite packet {packet_id} has stale version {version}; expected {expected}")
        if item.get("is_current") is False or status not in _CURRENT_PREREQUISITE_STATUSES:
            problems.append(f"prerequisite packet {packet_id} is not current: {status}")
    return problems


def _artifact_boundary_problems(value: Any, path: str = "$") -> list[str]:
    problems: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized = key_text.lower()
            child_path = f"{path}.{key_text}"
            if normalized in _PRIVATE_OR_SESSION_KEYS and child not in (None, "", [], {}):
                problems.append(f"private or session artifact is not allowed at {child_path}")
            if normalized in _RAW_CRAWL_KEYS and child not in (None, "", [], {}):
                problems.append(f"raw crawl output reference is not allowed at {child_path}")
            problems.extend(_artifact_boundary_problems(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            problems.extend(_artifact_boundary_problems(child, f"{path}[{index}]"))
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in _PRIVATE_STRING_MARKERS):
            problems.append(f"private or session artifact reference is not allowed at {path}")
        if any(marker in lowered for marker in _RAW_CRAWL_STRING_MARKERS):
            problems.append(f"raw crawl output reference is not allowed at {path}")
    return problems


def _production_promotion_problems(packet: Mapping[str, Any]) -> list[str]:
    promotion = packet.get("production_promotion") or packet.get("promotion") or {}
    enabled = _production_enabled(packet) or _production_enabled(promotion)
    if not enabled:
        return []

    approval = None
    if isinstance(promotion, Mapping):
        approval = promotion.get("signed_approval") or promotion.get("approval")
    if approval is None:
        approval = packet.get("signed_production_approval")

    if not isinstance(approval, Mapping):
        return ["production promotion enablement requires explicit signed approval"]

    problems: list[str] = []
    if approval.get("explicit_signed_approval") is not True:
        problems.append("production promotion approval must set explicit_signed_approval true")
    if not _non_empty_string(approval.get("approval_id")):
        problems.append("production promotion approval is missing approval_id")
    if not _non_empty_string(approval.get("reviewer_id")):
        problems.append("production promotion approval is missing reviewer_id")
    if _parse_datetime(approval.get("signed_at")) is None:
        problems.append("production promotion approval is missing a valid signed_at timestamp")
    return problems


def _production_enabled(value: Any) -> bool:
    if not isinstance(value, Mapping):
        return False
    if value.get("production_promotion_enabled") is True:
        return True
    if value.get("enable_production_promotion") is True:
        return True
    if value.get("enabled") is True and str(value.get("target") or value.get("environment") or "").lower() == "production":
        return True
    return str(value.get("promotion_status") or "").lower() in {"production_enabled", "ready_for_production"}


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


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())
