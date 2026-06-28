from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from ppd.devhub.read_only_pilot_reconciliation import (
    REQUIRED_PACKET_TYPE,
    validate_reconciliation_packet,
)


REQUIRED_RECONCILIATION_ROWS = {
    "observed_surface_deltas": ("delta_id", "surface_id", "decision"),
    "manual_handoff_decisions": ("handoff_id", "surface_id", "reason"),
    "redaction_follow_ups": ("follow_up_id", "owner", "action"),
    "reviewer_owner_fields": ("owner_id", "reviewer_id", "responsibility"),
}

FORBIDDEN_KEY_FRAGMENTS = (
    "auth_state",
    "browser_context",
    "cookie",
    "credential",
    "har_path",
    "har_file",
    "local_private_file_path",
    "password",
    "private_value",
    "raw_authenticated",
    "raw_dom",
    "screenshot",
    "session_state",
    "storage_state",
    "trace_path",
)
MUTATION_FLAG_KEYS = {
    "active_agent_state_mutation",
    "active_surface_registry_mutation",
    "agent_state_mutation",
    "agent_state_mutation_enabled",
    "mutates_active_surface_registry",
    "mutates_agent_state",
    "mutates_surface_registry",
    "surface_registry_mutation_enabled",
    "writes_surface_registry",
}
CONSEQUENTIAL_TERMS = (
    "upload",
    "submit",
    "certify",
    "payment",
    "pay",
    "purchase",
    "schedule",
    "cancel",
    "withdraw",
    "extension",
    "reactivate",
)
ENABLEMENT_KEYS = {"enabled", "allowed", "completed", "performed", "executed", "official_action_completed"}
PRIVATE_VALUE_PATTERNS = (
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    re.compile(r"\b\d{3}[-. ]\d{3}[-. ]\d{4}\b"),
    re.compile(r"/(?:home|Users|tmp|var/tmp)/"),
    re.compile(r"\b(?:auth_state\.json|storage_state\.json|session_state\.json|trace\.zip)\b", re.IGNORECASE),
    re.compile(r"\.(?:har|png|jpg|jpeg|webp)\b", re.IGNORECASE),
)
LIVE_BROWSER_CLAIM_PATTERNS = (
    re.compile(r"\b(?:launched|opened|ran|executed)\s+(?:a\s+)?(?:live\s+)?(?:browser|playwright|devhub)\b", re.IGNORECASE),
    re.compile(r"\b(?:clicked|filled|typed|submitted|uploaded|captured)\s+(?:in|from|with|via)\s+(?:devhub|playwright|browser)\b", re.IGNORECASE),
    re.compile(r"\b(?:captured|stored|saved)\s+(?:screenshot|trace|har|auth\s*state|storage\s*state)\b", re.IGNORECASE),
)
OUTCOME_GUARANTEE_PATTERNS = (
    re.compile(r"\b(?:permit|application|inspection|review|approval|issuance|legal|compliance)\b.{0,80}\b(?:guaranteed|approved|issued|accepted|successful|completed|will\s+pass|will\s+be\s+approved)\b", re.IGNORECASE),
    re.compile(r"\bguarantee[sd]?\b.{0,80}\b(?:permit|approval|issuance|inspection|legal|compliance|outcome)\b", re.IGNORECASE),
)


@dataclass(frozen=True)
class StrictReconciliationValidationResult:
    packet_id: str
    ok: bool
    errors: tuple[str, ...]


def validate_commit_safe_reconciliation_packet(packet: Mapping[str, Any]) -> StrictReconciliationValidationResult:
    errors = list(validate_reconciliation_packet(packet).errors)
    packet_id = _text(packet.get("packet_id")) if isinstance(packet, Mapping) else ""

    if not isinstance(packet, Mapping):
        return StrictReconciliationValidationResult(packet_id=packet_id, ok=False, errors=("packet must be a JSON object",))

    _require(errors, packet.get("packet_type") == REQUIRED_PACKET_TYPE, f"packet_type must be {REQUIRED_PACKET_TYPE}")
    for field_name, required_fields in REQUIRED_RECONCILIATION_ROWS.items():
        _validate_required_rows(errors, packet.get(field_name), field_name, required_fields)

    _scan_packet(errors, packet, "packet")
    return StrictReconciliationValidationResult(packet_id=packet_id, ok=not errors, errors=tuple(_dedupe(errors)))


def assert_commit_safe_reconciliation_packet(packet: Mapping[str, Any]) -> None:
    result = validate_commit_safe_reconciliation_packet(packet)
    if not result.ok:
        raise AssertionError("; ".join(result.errors))


def _validate_required_rows(errors: list[str], value: Any, field_name: str, required_fields: Sequence[str]) -> None:
    rows = _sequence(value)
    if not rows:
        errors.append(f"{field_name} must be non-empty")
        return
    for index, row in enumerate(rows):
        item = _mapping(row)
        path = f"{field_name}[{index}]"
        for field in required_fields:
            _require(errors, bool(_text(item.get(field))), f"{path}.{field} is required")
        _require(errors, bool(_text_list(item.get("citations"))), f"{path}.citations must be non-empty")
        for mutation_field in ("active_registry_mutation", "agent_state_mutation"):
            if mutation_field in item:
                _require(errors, item.get(mutation_field) is False, f"{path}.{mutation_field} must be false")


def _scan_packet(errors: list[str], value: Any, path: str) -> None:
    if isinstance(value, Mapping):
        lowered_values = " ".join(_text(child).casefold() for child in value.values() if isinstance(child, str))
        if any(term in lowered_values for term in CONSEQUENTIAL_TERMS):
            for key, child in value.items():
                if _text(key).casefold() in ENABLEMENT_KEYS and child is True:
                    errors.append(f"{path} must not enable consequential DevHub controls")
        for key, child in value.items():
            key_text = _text(key)
            normalized = key_text.casefold().replace("-", "_")
            child_path = f"{path}.{key_text}"
            if any(fragment in normalized for fragment in FORBIDDEN_KEY_FRAGMENTS):
                errors.append(f"{child_path} contains forbidden private/session artifact field")
            if normalized in MUTATION_FLAG_KEYS and child is True:
                errors.append(f"{child_path} must not enable active surface-registry or agent-state mutation")
            _scan_packet(errors, child, child_path)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _scan_packet(errors, child, f"{path}[{index}]")
        return
    if isinstance(value, str):
        if any(pattern.search(value) for pattern in PRIVATE_VALUE_PATTERNS):
            errors.append(f"{path} contains private value or browser artifact reference")
        if any(pattern.search(value) for pattern in LIVE_BROWSER_CLAIM_PATTERNS):
            errors.append(f"{path} must not claim live browser execution")
        if any(pattern.search(value) for pattern in OUTCOME_GUARANTEE_PATTERNS):
            errors.append(f"{path} must not guarantee legal or permitting outcomes")


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: Any) -> tuple[Any, ...]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(value)
    return ()


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _text_list(value: Any) -> tuple[str, ...]:
    return tuple(item.strip() for item in _sequence(value) if isinstance(item, str) and item.strip())


def _require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def _dedupe(values: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return tuple(result)
