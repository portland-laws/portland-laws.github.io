"""Fixture-first end-to-end readiness digest for synthetic PP&D cases.

The digest links committed metadata packets for public sources, extraction,
process modeling, guardrails, user gaps, local preview, DevHub preflight,
action journal expectations, and post-action review. It is intentionally
fixture-only and must never claim official permit readiness.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable, Mapping


_REQUIRED_PACKET_KEYS = (
    "public_source_packet",
    "extraction_packet",
    "process_model_packet",
    "guardrail_packet",
    "user_gap_packet",
    "local_preview_packet",
    "devhub_preflight_packet",
    "journal_packet",
    "post_action_packet",
)

_BLOCKING_PACKET_KEYS = {
    "user_gap_packet",
    "devhub_preflight_packet",
    "journal_packet",
    "post_action_packet",
}

_OFFICIAL_READY_VALUES = {
    "official_ready",
    "ready_for_submission",
    "ready_for_payment",
    "ready_for_upload",
    "ready_to_submit",
    "ready-to-submit",
    "submit_ready",
    "submission_ready",
}
_UNSUPPORTED_READY_FRAGMENTS = {
    "official_ready",
    "ready_for_submission",
    "ready_for_payment",
    "ready_for_upload",
    "ready_to_submit",
    "ready-to-submit",
    "submit_ready",
    "submission_ready",
    "ready for submission",
    "ready to submit",
}
_STALE_COMPONENT_STATUSES = {"expired", "needs_refresh", "stale", "unknown_stale"}
_UNREVIEWED_COMPONENT_STATUSES = {"not_reviewed", "pending_review", "unreviewed"}
_STATUS_KEYS = {
    "component_status",
    "freshness_status",
    "human_review_status",
    "readiness_status",
    "review_status",
    "status",
    "synthetic_case_status",
    "validation_status",
}
_PRIVATE_KEY_FRAGMENTS = {
    "access_token",
    "api_key",
    "auth_state",
    "client_secret",
    "credential",
    "cookie",
    "local_storage",
    "password",
    "payment_detail",
    "private_value",
    "refresh_token",
    "secret",
    "session_storage",
}
_RAW_OR_AUTH_ARTIFACT_FRAGMENTS = {
    "authenticated_artifact",
    "browser_trace",
    "crawl_body",
    "har_path",
    "raw_body",
    "raw_crawl",
    "raw_html",
    "raw_response",
    "screenshot_path",
    "trace_path",
}
_DOWNLOADED_PATH_KEYS = {
    "download_path",
    "downloaded_document_path",
    "downloaded_document_paths",
    "local_document_path",
    "local_document_paths",
}
_CONSEQUENTIAL_ACTION_VALUES = {
    "cancel",
    "cancellation",
    "certification",
    "certify",
    "consequential",
    "consequential_official",
    "financial",
    "official",
    "payment",
    "purchase",
    "schedule_inspection",
    "submission",
    "submit",
    "upload_to_official_record",
}
_BLOCKED_OR_HANDOFF_STATUSES = {
    "blocked",
    "blocked_pending_user_confirmation",
    "blocked_pending_user_or_manual_review",
    "blocked_until_manual_handoff",
    "blocked_until_user_attended",
    "manual_handoff_required",
    "refused",
    "requires_manual_handoff",
}


class E2EReadinessDigestError(ValueError):
    """Raised when a synthetic end-to-end readiness digest is unsafe."""

    def __init__(self, problems: Iterable[str]) -> None:
        self.problems = tuple(problems)
        super().__init__("invalid PP&D end-to-end readiness digest: " + "; ".join(self.problems))


def load_e2e_readiness_digest_fixture(path: str | Path) -> dict[str, Any]:
    """Load and build a digest from a committed JSON fixture."""

    fixture_path = Path(path)
    raw = json.loads(fixture_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise E2EReadinessDigestError(["fixture root must be an object"])
    return build_e2e_readiness_digest(raw)


def build_e2e_readiness_digest(fixture: Mapping[str, Any]) -> dict[str, Any]:
    """Build one synthetic case status from fixture packet summaries."""

    source = deepcopy(dict(fixture))
    problems = _fixture_problems(source)
    if problems:
        raise E2EReadinessDigestError(problems)

    packets = {key: source[key] for key in _REQUIRED_PACKET_KEYS}
    source_evidence_ids = sorted(_collect_source_evidence_ids(packets))
    blocking_reasons = _blocking_reasons(packets)
    synthetic_case_status = (
        "synthetic_blocked_pending_user_or_manual_review"
        if blocking_reasons
        else "synthetic_ready_for_reversible_draft_only"
    )

    digest = {
        "digest_type": "ppd.e2e_readiness_digest.v1",
        "fixture_first": True,
        "live_services_called": False,
        "official_readiness": False,
        "synthetic_only": True,
        "case_id": str(source["case_id"]),
        "process_id": str(source["process_id"]),
        "synthetic_case_status": synthetic_case_status,
        "source_evidence_ids": source_evidence_ids,
        "packet_links": [_packet_link(key, packets[key]) for key in _REQUIRED_PACKET_KEYS],
        "blocking_reasons": blocking_reasons,
        "next_safe_actions": _next_safe_actions(packets, blocking_reasons),
    }

    digest_problems = validate_e2e_readiness_digest(digest)
    if digest_problems:
        raise E2EReadinessDigestError(digest_problems)
    return digest


def validate_e2e_readiness_digest(digest: Mapping[str, Any]) -> list[str]:
    """Validate a built digest without touching live services."""

    problems: list[str] = []
    if digest.get("digest_type") != "ppd.e2e_readiness_digest.v1":
        problems.append("digest_type must be ppd.e2e_readiness_digest.v1")
    if digest.get("fixture_first") is not True:
        problems.append("digest must be fixture_first")
    if digest.get("live_services_called") is not False:
        problems.append("digest must confirm live_services_called is false")
    if digest.get("official_readiness") is not False:
        problems.append("digest must not mark official_readiness")
    if digest.get("synthetic_only") is not True:
        problems.append("digest must be synthetic_only")
    if not _non_empty_text(digest.get("case_id")):
        problems.append("digest is missing case_id")
    if not _non_empty_text(digest.get("process_id")):
        problems.append("digest is missing process_id")

    status = str(digest.get("synthetic_case_status") or "")
    status_lower = status.lower()
    if not status:
        problems.append("digest is missing synthetic_case_status")
    if status_lower in _OFFICIAL_READY_VALUES or not status.startswith("synthetic_"):
        problems.append("synthetic_case_status must not claim official readiness")
    if _has_unsupported_ready_status(status_lower):
        problems.append("synthetic_case_status contains unsupported ready-to-submit status")

    evidence_ids = digest.get("source_evidence_ids")
    if not isinstance(evidence_ids, list) or not evidence_ids or not all(isinstance(item, str) and item for item in evidence_ids):
        problems.append("digest must include source_evidence_ids")

    packet_links = digest.get("packet_links")
    if not isinstance(packet_links, list):
        problems.append("digest must link every required packet")
    else:
        linked_keys = {link.get("packet_key") for link in packet_links if isinstance(link, Mapping)}
        for key in _REQUIRED_PACKET_KEYS:
            if key not in linked_keys:
                problems.append(f"digest is missing packet link: {key}")
        if len(packet_links) != len(_REQUIRED_PACKET_KEYS):
            problems.append("digest must link every required packet exactly once")
        for index, link in enumerate(packet_links):
            if not isinstance(link, Mapping):
                problems.append(f"packet_links[{index}] must be an object")
                continue
            if link.get("packet_key") not in _REQUIRED_PACKET_KEYS:
                problems.append(f"packet_links[{index}] has unsupported packet_key")
            if not _non_empty_text(link.get("packet_id")):
                problems.append(f"packet_links[{index}] is missing packet_id")
            refs = link.get("source_evidence_ids")
            if not isinstance(refs, list) or not refs:
                problems.append(f"packet_links[{index}] must cite source_evidence_ids")
            elif not all(isinstance(ref, str) and ref for ref in refs):
                problems.append(f"packet_links[{index}] has invalid source_evidence_ids")

    problems.extend(_safety_problems(digest, "digest"))
    return problems


def _fixture_problems(fixture: Mapping[str, Any]) -> list[str]:
    problems: list[str] = []
    for key in ("case_id", "process_id"):
        if not _non_empty_text(fixture.get(key)):
            problems.append(f"fixture is missing {key}")
    for key in _REQUIRED_PACKET_KEYS:
        packet = fixture.get(key)
        if not isinstance(packet, Mapping):
            problems.append(f"fixture is missing {key}")
            continue
        if packet.get("fixture_first") is not True:
            problems.append(f"{key} must be fixture_first")
        if packet.get("live_services_called") is not False:
            problems.append(f"{key} must confirm live_services_called is false")
        if packet.get("official_readiness") is not False:
            problems.append(f"{key} must not claim official_readiness")
        if not _non_empty_text(packet.get("packet_id")):
            problems.append(f"{key} is missing packet_id")
        if not _collect_source_evidence_ids(packet):
            problems.append(f"{key} must cite source_evidence_ids")
    problems.extend(_safety_problems(fixture, "fixture"))
    return problems


def _packet_link(packet_key: str, packet: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "packet_key": packet_key,
        "packet_id": str(packet["packet_id"]),
        "status": str(packet.get("status") or "fixture_validated"),
        "source_evidence_ids": sorted(_collect_source_evidence_ids(packet)),
    }


def _blocking_reasons(packets: Mapping[str, Mapping[str, Any]]) -> list[dict[str, str]]:
    reasons: list[dict[str, str]] = []
    for key in sorted(_BLOCKING_PACKET_KEYS):
        packet = packets[key]
        for reason in packet.get("blocking_reasons", []):
            if isinstance(reason, str) and reason:
                reasons.append({"packet_key": key, "reason": reason})
        if packet.get("requires_manual_handoff") is True:
            reasons.append({"packet_key": key, "reason": "manual_handoff_required"})
        if packet.get("requires_exact_confirmation") is True:
            reasons.append({"packet_key": key, "reason": "exact_confirmation_required"})
    return reasons


def _next_safe_actions(packets: Mapping[str, Mapping[str, Any]], blocking_reasons: list[Mapping[str, str]]) -> list[str]:
    actions: list[str] = ["review_digest_with_user", "keep_live_services_disabled"]
    if blocking_reasons:
        actions.append("resolve_missing_or_gated_items_before_official_action")
    preview_packet = packets.get("local_preview_packet", {})
    if preview_packet.get("status") in {"metadata_only_preview_ready", "fixture_validated"}:
        actions.append("inspect_local_preview_metadata")
    return actions


def _safety_problems(value: Any, path: str) -> list[str]:
    problems: list[str] = []
    if isinstance(value, Mapping):
        problems.extend(_mapping_safety_problems(value, path))
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            problems.extend(_safety_problems(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            problems.extend(_safety_problems(child, f"{path}[{index}]"))
    elif isinstance(value, str):
        problems.extend(_string_safety_problems(value, path))
    return problems


def _mapping_safety_problems(mapping: Mapping[str, Any], path: str) -> list[str]:
    problems: list[str] = []
    for key, raw_value in mapping.items():
        key_text = str(key)
        key_lower = key_text.lower()
        if any(fragment in key_lower for fragment in _PRIVATE_KEY_FRAGMENTS):
            problems.append(f"{path}.{key_text} must not contain private values")
        if any(fragment in key_lower for fragment in _RAW_OR_AUTH_ARTIFACT_FRAGMENTS):
            problems.append(f"{path}.{key_text} must not reference raw crawl or authenticated artifacts")
        if key_lower in _DOWNLOADED_PATH_KEYS or ("download" in key_lower and "path" in key_lower):
            problems.append(f"{path}.{key_text} must not reference downloaded document paths")
        if key_lower in _STATUS_KEYS and isinstance(raw_value, str):
            status = raw_value.strip().lower()
            if status in _STALE_COMPONENT_STATUSES:
                problems.append(f"{path}.{key_text} is stale: {status}")
            if status in _UNREVIEWED_COMPONENT_STATUSES:
                problems.append(f"{path}.{key_text} is unreviewed: {status}")
            if _has_unsupported_ready_status(status):
                problems.append(f"{path}.{key_text} contains unsupported ready-to-submit status")
    if _is_consequential_action(mapping) and not _is_blocked_or_manual_handoff(mapping):
        problems.append(f"{path} has consequential action without blocked or manual-handoff status")
    return problems


def _string_safety_problems(value: str, path: str) -> list[str]:
    problems: list[str] = []
    text = value.strip()
    lower = text.lower()
    if _looks_like_local_downloaded_document_path(text):
        problems.append(f"{path} must not contain downloaded document paths")
    if _has_unsupported_ready_status(lower) and "synthetic_ready_for_reversible_draft_only" not in lower:
        problems.append(f"{path} contains unsupported ready-to-submit status")
    return problems


def _has_unsupported_ready_status(status: str) -> bool:
    return any(fragment in status for fragment in _UNSUPPORTED_READY_FRAGMENTS)


def _looks_like_local_downloaded_document_path(text: str) -> bool:
    lower = text.lower()
    if not lower.endswith((".pdf", ".doc", ".docx", ".xls", ".xlsx")):
        return False
    return lower.startswith(("/home/", "/users/", "c:\\", "c:/")) or "/downloads/" in lower or "\\downloads\\" in lower


def _is_consequential_action(mapping: Mapping[str, Any]) -> bool:
    for key in ("action_class", "action_type", "action_category", "gate_type"):
        raw = mapping.get(key)
        if isinstance(raw, str):
            normalized = raw.strip().lower()
            if normalized in _CONSEQUENTIAL_ACTION_VALUES:
                return True
            if any(fragment in normalized for fragment in ("submit", "certif", "payment", "purchase", "schedule", "cancel")):
                return True
    return mapping.get("consequential_action") is True or mapping.get("official_action") is True


def _is_blocked_or_manual_handoff(mapping: Mapping[str, Any]) -> bool:
    if mapping.get("blocked") is True or mapping.get("requires_manual_handoff") is True:
        return True
    status = mapping.get("status") or mapping.get("readiness_status") or mapping.get("gate_status")
    if isinstance(status, str):
        normalized = status.strip().lower()
        return normalized in _BLOCKED_OR_HANDOFF_STATUSES or normalized.startswith("blocked_")
    return False


def _collect_source_evidence_ids(value: Any) -> set[str]:
    refs: set[str] = set()
    if isinstance(value, Mapping):
        raw_many = value.get("source_evidence_ids")
        if isinstance(raw_many, list):
            refs.update(item for item in raw_many if isinstance(item, str) and item)
        raw_one = value.get("source_evidence_id")
        if isinstance(raw_one, str) and raw_one:
            refs.add(raw_one)
        for child in value.values():
            refs.update(_collect_source_evidence_ids(child))
    elif isinstance(value, list):
        for child in value:
            refs.update(_collect_source_evidence_ids(child))
    return refs


def _non_empty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())
