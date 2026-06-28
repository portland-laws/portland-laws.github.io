"""Fail-closed validation for agent-facing PP&D readiness contract packets.

This module validates packet-shaped dictionaries before they are exposed to an
agent. It is deterministic, fixture-friendly, and intentionally avoids live LLM,
DevHub, browser, or filesystem side effects.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Any, Mapping


@dataclass(frozen=True)
class ReadinessContractPacketValidationResult:
    """Machine-readable validation result for an agent-facing packet."""

    ready: bool
    problems: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {"ready": self.ready, "problems": list(self.problems)}


_RESPONSE_EXAMPLE_KEYS = {
    "agent_response_example",
    "example_response",
    "example_responses",
    "response_example",
    "response_examples",
    "sample_response",
    "sample_responses",
}
_STALE_STATUSES = {"expired", "needs_refresh", "stale", "unknown", "unknown_stale"}
_CURRENT_STATUSES = {"current", "fresh", "verified_current"}
_PRIVATE_VALUE_KEYS = {
    "access_token",
    "auth_state",
    "bank_account",
    "card_number",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "cvv",
    "email",
    "entered_value",
    "field_value",
    "local_path",
    "password",
    "payment_details",
    "phone",
    "private_value",
    "raw_value",
    "refresh_token",
    "secret",
    "session_cookie",
    "session_state",
    "ssn",
    "token",
    "user_input",
    "user_supplied_value",
    "value",
}
_LOCAL_PATH_KEYS = {"file_path", "local_file_path", "local_path", "path", "private_file_path"}
_LIVE_LLM_FLAG_KEYS = {
    "allow_live_llm_execution",
    "autonomous_llm_execution",
    "execute_llm",
    "live_llm",
    "live_llm_execution",
    "llm_execution_enabled",
    "run_live_llm",
    "use_live_llm",
}
_BLOCKED_ACTION_CLASSES = {
    "cancellation",
    "certification",
    "payment",
    "schedule_inspection",
    "submission",
    "upload_to_official_record",
}
_CONSEQUENTIAL_CLASSES = _BLOCKED_ACTION_CLASSES | {
    "consequential",
    "consequential_official",
    "financial",
    "official",
    "upload",
}
_BLOCKED_DECISIONS = {"blocked", "manual_handoff_required", "refused"}
_DOWNGRADED_DECISIONS = {"allowed", "draft", "ready", "reversible", "safe", "safe_action"}
_DEVHUB_AUTOMATION_KEYS = {
    "automated_devhub",
    "devhub_automation",
    "devhub_automation_claim",
    "devhub_automation_claims",
    "devhub_automation_enabled",
}
_AUTOMATION_VERBS = {
    "account creation",
    "captcha",
    "cancel",
    "certify",
    "mfa",
    "payment",
    "schedule inspection",
    "submit",
    "upload",
}
_LOCAL_PRIVATE_PATH_RE = re.compile(
    r"(^file://)|(^/home/[^/]+/)|(^/Users/[^/]+/)|(^/private/)|(^~?/\.devhub/)|(^[A-Za-z]:\\Users\\[^\\]+\\)",
    re.IGNORECASE,
)


def validate_agent_facing_readiness_contract_packet(
    packet: Mapping[str, Any],
    *,
    now: datetime | None = None,
    max_evidence_age_days: int = 45,
) -> ReadinessContractPacketValidationResult:
    """Return fail-closed validation for an agent-facing readiness packet."""

    check_time = _normalize_now(now)
    evidence_by_id = _evidence_by_id(packet)
    stale_source_ids = _stale_source_ids(packet)
    blocked_action_ids = _blocked_action_ids(packet)

    problems: list[str] = []
    problems.extend(_response_example_citation_problems(packet, evidence_by_id))
    problems.extend(_stale_source_id_problems(evidence_by_id, stale_source_ids, check_time, max_evidence_age_days))
    problems.extend(_private_value_and_path_problems(packet))
    problems.extend(_blocked_action_downgrade_problems(packet, blocked_action_ids))
    problems.extend(_manual_handoff_response_problems(packet, blocked_action_ids))
    problems.extend(_live_llm_flag_problems(packet))
    problems.extend(_devhub_automation_claim_problems(packet))

    return ReadinessContractPacketValidationResult(ready=not problems, problems=tuple(problems))


def require_agent_facing_readiness_contract_packet(
    packet: Mapping[str, Any],
    *,
    now: datetime | None = None,
    max_evidence_age_days: int = 45,
) -> None:
    """Raise ValueError when an agent-facing packet violates the contract."""

    result = validate_agent_facing_readiness_contract_packet(
        packet,
        now=now,
        max_evidence_age_days=max_evidence_age_days,
    )
    if not result.ready:
        raise ValueError("invalid_agent_facing_readiness_contract_packet: " + "; ".join(result.problems))


def _response_example_citation_problems(value: Any, evidence_by_id: Mapping[str, Mapping[str, Any]], path: str = "$", inherited_refs: frozenset[str] = frozenset()) -> list[str]:
    problems: list[str] = []
    if isinstance(value, Mapping):
        local_refs = inherited_refs | frozenset(_collect_direct_evidence_refs(value))
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if str(key).lower() in _RESPONSE_EXAMPLE_KEYS and child not in (None, "", [], {}):
                refs = local_refs | frozenset(_collect_evidence_refs(child))
                if not refs:
                    problems.append(f"response example lacks source_evidence_ids at {child_path}")
                for ref in sorted(refs):
                    if ref not in evidence_by_id:
                        problems.append(f"response example cites unknown source evidence {ref} at {child_path}")
            problems.extend(_response_example_citation_problems(child, evidence_by_id, child_path, local_refs))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            problems.extend(_response_example_citation_problems(child, evidence_by_id, f"{path}[{index}]", inherited_refs))
    return problems


def _stale_source_id_problems(
    evidence_by_id: Mapping[str, Mapping[str, Any]],
    stale_source_ids: set[str],
    now: datetime,
    max_evidence_age_days: int,
) -> list[str]:
    problems: list[str] = []
    for evidence_id, evidence in evidence_by_id.items():
        status = str(evidence.get("freshness_status", "")).lower()
        timestamp = _parse_datetime(
            evidence.get("last_verified_at")
            or evidence.get("captured_at")
            or evidence.get("capture_finished_at")
            or evidence.get("updated_at")
        )
        is_age_stale = timestamp is not None and (now - timestamp).days > max_evidence_age_days
        if status in _CURRENT_STATUSES and (evidence_id in stale_source_ids or is_age_stale):
            problems.append(f"stale source evidence is marked current: {evidence_id}")
        if status in _STALE_STATUSES and evidence.get("current") is True:
            problems.append(f"stale source evidence carries current=true: {evidence_id}")
    return problems


def _private_value_and_path_problems(value: Any, path: str = "$", key_name: str = "") -> list[str]:
    problems: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized_key = key_text.lower()
            child_path = f"{path}.{key_text}"
            if normalized_key in _PRIVATE_VALUE_KEYS and child not in (None, "", [], {}):
                problems.append(f"private value field is not allowed at {child_path}")
            if normalized_key in _LOCAL_PATH_KEYS and _contains_local_private_path(child):
                problems.append(f"local private path is not allowed at {child_path}")
            problems.extend(_private_value_and_path_problems(child, child_path, normalized_key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            problems.extend(_private_value_and_path_problems(child, f"{path}[{index}]", key_name))
    elif isinstance(value, str) and key_name in _LOCAL_PATH_KEYS and _LOCAL_PRIVATE_PATH_RE.search(value):
        problems.append(f"local private path is not allowed at {path}")
    return problems


def _blocked_action_downgrade_problems(value: Any, blocked_action_ids: set[str], path: str = "$") -> list[str]:
    problems: list[str] = []
    if isinstance(value, Mapping):
        action_id = _action_id(value)
        decision = _decision(value)
        action_class = _action_classification(value)
        if action_id in blocked_action_ids and decision in _DOWNGRADED_DECISIONS:
            problems.append(f"blocked action is downgraded to {decision} at {path}: {action_id}")
        if action_id in blocked_action_ids and value.get("blocked") is False:
            problems.append(f"blocked action is marked blocked=false at {path}: {action_id}")
        if action_class in _BLOCKED_ACTION_CLASSES and decision in _DOWNGRADED_DECISIONS:
            problems.append(f"blocked action class is downgraded to {decision} at {path}: {action_class}")
        for key, child in value.items():
            problems.extend(_blocked_action_downgrade_problems(child, blocked_action_ids, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            problems.extend(_blocked_action_downgrade_problems(child, blocked_action_ids, f"{path}[{index}]"))
    return problems


def _manual_handoff_response_problems(packet: Mapping[str, Any], blocked_action_ids: set[str]) -> list[str]:
    needs_handoff = bool(blocked_action_ids) or _contains_consequential_action(packet)
    if not needs_handoff:
        return []

    response = packet.get("manual_handoff_response") or packet.get("manual_handoff")
    if not isinstance(response, Mapping):
        return ["manual_handoff_response is required for blocked or consequential actions"]

    problems: list[str] = []
    if not response.get("response_template") and not response.get("message"):
        problems.append("manual_handoff_response must include a response_template or message")
    if not _collect_evidence_refs(response):
        problems.append("manual_handoff_response must cite source_evidence_ids")
    if response.get("requires_user_attendance") is not True and response.get("requires_manual_handoff") is not True:
        problems.append("manual_handoff_response must require user attendance or manual handoff")
    if response.get("automated") is True or response.get("automation_allowed") is True:
        problems.append("manual_handoff_response must not claim automation is allowed")
    return problems


def _live_llm_flag_problems(value: Any, path: str = "$") -> list[str]:
    problems: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized_key = key_text.lower()
            child_path = f"{path}.{key_text}"
            if normalized_key in _LIVE_LLM_FLAG_KEYS and child not in (False, None, "", [], {}):
                problems.append(f"live LLM execution flag is not allowed at {child_path}")
            if normalized_key in {"execution_mode", "llm_mode", "mode"} and isinstance(child, str) and child.lower() in {"live", "live_llm", "autonomous"}:
                problems.append(f"live LLM execution mode is not allowed at {child_path}")
            problems.extend(_live_llm_flag_problems(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            problems.extend(_live_llm_flag_problems(child, f"{path}[{index}]"))
    return problems


def _devhub_automation_claim_problems(value: Any, path: str = "$") -> list[str]:
    problems: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized_key = key_text.lower()
            child_path = f"{path}.{key_text}"
            if normalized_key in _DEVHUB_AUTOMATION_KEYS and child not in (False, None, "", [], {}):
                problems.append(f"DevHub automation claim is not allowed at {child_path}")
            if normalized_key in {"automation_mode", "devhub_mode"} and isinstance(child, str) and child.lower() not in {"attended", "manual", "manual_handoff", "metadata_only"}:
                problems.append(f"DevHub automation mode must remain attended/manual at {child_path}")
            if normalized_key in {"claim", "claims", "summary"} and _contains_blocked_automation_text(child):
                problems.append(f"DevHub blocked-action automation claim is not allowed at {child_path}")
            problems.extend(_devhub_automation_claim_problems(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            problems.extend(_devhub_automation_claim_problems(child, f"{path}[{index}]"))
    return problems


def _evidence_by_id(packet: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    evidence_by_id: dict[str, Mapping[str, Any]] = {}
    for key in ("normalized_source_evidence", "citations", "sources", "source_registry"):
        raw = packet.get(key)
        if not isinstance(raw, list):
            continue
        for index, item in enumerate(raw):
            if not isinstance(item, Mapping):
                continue
            evidence_id = item.get("evidence_id") or item.get("source_evidence_id") or item.get("source_id")
            if isinstance(evidence_id, str) and evidence_id:
                evidence_by_id[evidence_id] = item
            else:
                evidence_by_id[f"{key}[{index}]"] = item
    return evidence_by_id


def _stale_source_ids(packet: Mapping[str, Any]) -> set[str]:
    refs: set[str] = set()
    for container_key in ("stale_source_ids", "stale_evidence"):
        refs.update(_string_refs(packet.get(container_key)))
    case_gap = packet.get("case_gap_report")
    if isinstance(case_gap, Mapping):
        refs.update(_string_refs(case_gap.get("stale_evidence")))
        refs.update(_string_refs(case_gap.get("stale_source_ids")))
    return refs


def _blocked_action_ids(packet: Mapping[str, Any]) -> set[str]:
    refs: set[str] = set()
    refs.update(_string_refs(packet.get("blocked_actions")))
    case_gap = packet.get("case_gap_report")
    if isinstance(case_gap, Mapping):
        refs.update(_string_refs(case_gap.get("blocked_actions")))
    action_decision = packet.get("action_decision_output")
    if isinstance(action_decision, Mapping):
        refs.update(_string_refs(action_decision.get("blocked_actions")))
    return refs


def _string_refs(value: Any) -> set[str]:
    refs: set[str] = set()
    if isinstance(value, str) and value:
        refs.add(value)
    elif isinstance(value, Mapping):
        for key in ("action_id", "id", "source_evidence_id", "evidence_id", "source_id"):
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


def _contains_blocked_automation_text(value: Any) -> bool:
    if isinstance(value, str):
        normalized = value.lower()
        return "devhub" in normalized and "automat" in normalized and any(verb in normalized for verb in _AUTOMATION_VERBS)
    if isinstance(value, list):
        return any(_contains_blocked_automation_text(item) for item in value)
    return False


def _contains_consequential_action(value: Any) -> bool:
    if isinstance(value, Mapping):
        action_class = _action_classification(value)
        if action_class in _CONSEQUENTIAL_CLASSES:
            return True
        return any(_contains_consequential_action(child) for child in value.values())
    if isinstance(value, list):
        return any(_contains_consequential_action(child) for child in value)
    return False


def _action_id(value: Mapping[str, Any]) -> str | None:
    for key in ("action_id", "requested_action_id", "id"):
        raw = value.get(key)
        if isinstance(raw, str) and raw:
            return raw
    return None


def _decision(value: Mapping[str, Any]) -> str | None:
    for key in ("decision", "status", "readiness", "classification"):
        raw = value.get(key)
        if isinstance(raw, str) and raw:
            return raw.lower()
    if value.get("allowed") is True:
        return "allowed"
    return None


def _action_classification(value: Mapping[str, Any]) -> str | None:
    for key in ("action_class", "action_type", "classification"):
        raw = value.get(key)
        if isinstance(raw, str) and raw:
            return raw.lower()
    return None


def _collect_evidence_refs(value: Any) -> set[str]:
    refs: set[str] = set()
    if isinstance(value, Mapping):
        refs.update(_collect_direct_evidence_refs(value))
        for child in value.values():
            refs.update(_collect_evidence_refs(child))
    elif isinstance(value, list):
        for child in value:
            refs.update(_collect_evidence_refs(child))
    return refs


def _collect_direct_evidence_refs(value: Mapping[str, Any]) -> set[str]:
    refs: set[str] = set()
    raw_many = value.get("source_evidence_ids")
    if isinstance(raw_many, list):
        refs.update(item for item in raw_many if isinstance(item, str) and item)
    raw_one = value.get("source_evidence_id")
    if isinstance(raw_one, str) and raw_one:
        refs.add(raw_one)
    return refs


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
