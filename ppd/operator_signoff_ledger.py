"""Validation helpers for PP&D operator signoff ledger packets."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any


FORBIDDEN_ACTION_TERMS = (
    "payment",
    "pay_fee",
    "fee_payment",
    "upload",
    "submission",
    "submit",
    "schedule",
    "scheduling",
    "cancel",
    "cancellation",
    "certify",
    "certification",
)

UNSAFE_ARTIFACT_TERMS = (
    "auth_state",
    "browser_state",
    "cookie",
    "credential",
    "har",
    "local_private_path",
    "password",
    "payment_detail",
    "private_artifact",
    "private_devhub",
    "raw_authenticated",
    "raw_body",
    "raw_crawl",
    "screen_capture",
    "secret",
    "storage_state",
    "trace",
    "token",
)

_APPROVED_VALUES = {"approved", "approve", "accepted", "production_approved"}
_RESOLVED_VALUES = {"resolved", "closed", "cleared", "mitigated"}


@dataclass(frozen=True)
class SignoffLedgerValidationResult:
    """Result returned by the operator signoff ledger packet validator."""

    ok: bool
    errors: tuple[str, ...]


def validate_operator_signoff_ledger_packet(packet: Mapping[str, Any]) -> SignoffLedgerValidationResult:
    """Validate a committed operator signoff ledger packet.

    The validator is intentionally shape-tolerant because daemon-generated packets
    may be plain JSON fixtures while future ledgers may use richer typed records.
    It enforces only the high-risk signoff invariants needed before approval.
    """

    errors: list[str] = []

    if not _non_empty_sequence(packet.get("reviewer_prompts")):
        errors.append("missing reviewer prompts")

    if not _non_empty_sequence(packet.get("prerequisite_packet_links")):
        errors.append("missing prerequisite packet links")

    unsafe_paths = sorted(_unsafe_artifact_paths(packet))
    if unsafe_paths:
        errors.append("unsafe artifact references: " + ", ".join(unsafe_paths))

    if _has_unresolved_approved_blocker(packet):
        errors.append("unresolved blocker marked approved")

    if _requests_production_promotion(packet) and not _has_required_production_signatures(packet):
        errors.append("unsigned production promotion")

    forbidden_actions = sorted(_forbidden_enabled_actions(packet))
    if forbidden_actions:
        errors.append("forbidden official-action enablement: " + ", ".join(forbidden_actions))

    return SignoffLedgerValidationResult(ok=not errors, errors=tuple(errors))


def require_valid_operator_signoff_ledger_packet(packet: Mapping[str, Any]) -> None:
    """Raise ValueError when an operator signoff ledger packet is not acceptable."""

    result = validate_operator_signoff_ledger_packet(packet)
    if not result.ok:
        raise ValueError("; ".join(result.errors))


def _non_empty_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes)) and len(value) > 0


def _normal_text(value: Any) -> str:
    return str(value).strip().lower().replace("-", "_").replace(" ", "_")


def _walk_json(value: Any, path: str = "$") -> list[tuple[str, Any]]:
    items = [(path, value)]
    if isinstance(value, Mapping):
        for key, child in value.items():
            items.extend(_walk_json(child, f"{path}.{key}"))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, child in enumerate(value):
            items.extend(_walk_json(child, f"{path}[{index}]"))
    return items


def _unsafe_artifact_paths(packet: Mapping[str, Any]) -> set[str]:
    unsafe: set[str] = set()
    for path, value in _walk_json(packet):
        path_text = _normal_text(path)
        value_text = _normal_text(value) if isinstance(value, (str, int, float, bool)) else ""
        combined = f"{path_text} {value_text}"
        if any(term in combined for term in UNSAFE_ARTIFACT_TERMS):
            unsafe.add(path)
    return unsafe


def _is_approved(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _normal_text(value) in _APPROVED_VALUES


def _is_resolved(value: Any) -> bool:
    return _normal_text(value) in _RESOLVED_VALUES


def _has_unresolved_approved_blocker(packet: Mapping[str, Any]) -> bool:
    blockers = packet.get("blockers", ())
    if not _non_empty_sequence(blockers):
        return False

    for blocker in blockers:
        if not isinstance(blocker, Mapping):
            continue
        status = blocker.get("status", "")
        approved = blocker.get("approved", blocker.get("approval_status", False))
        if _is_approved(approved) and not _is_resolved(status):
            return True
    return False


def _requests_production_promotion(packet: Mapping[str, Any]) -> bool:
    promotion = packet.get("production_promotion")
    if isinstance(promotion, Mapping):
        requested = promotion.get("requested", promotion.get("approved", promotion.get("enabled", False)))
        return _is_approved(requested)
    return _is_approved(packet.get("promotion_status")) or packet.get("promote_to_production") is True


def _has_required_production_signatures(packet: Mapping[str, Any]) -> bool:
    promotion = packet.get("production_promotion")
    if isinstance(promotion, Mapping):
        signatures = promotion.get("signatures", {})
    else:
        signatures = packet.get("signatures", {})

    if not isinstance(signatures, Mapping):
        return False

    operator = signatures.get("operator") or signatures.get("operator_signature")
    reviewer = signatures.get("reviewer") or signatures.get("reviewer_signature")
    return bool(operator) and bool(reviewer)


def _is_enabled_action_record(record: Mapping[str, Any]) -> bool:
    if record.get("enabled") is True or record.get("allowed") is True:
        return True
    state = _normal_text(record.get("state", record.get("status", "")))
    return state in {"enabled", "allowed", "approved"}


def _forbidden_enabled_actions(packet: Mapping[str, Any]) -> set[str]:
    forbidden: set[str] = set()
    for path, value in _walk_json(packet):
        if isinstance(value, Mapping) and not _is_enabled_action_record(value):
            continue
        if isinstance(value, Mapping):
            action_text = _normal_text(value.get("action", value.get("name", value.get("type", path))))
        elif isinstance(value, str):
            action_text = _normal_text(value)
        else:
            continue
        for term in FORBIDDEN_ACTION_TERMS:
            if term in action_text:
                forbidden.add(action_text)
    return forbidden
