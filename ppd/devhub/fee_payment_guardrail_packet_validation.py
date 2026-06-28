"""Validation for commit-safe DevHub fee/payment guardrail packets.

The validator is intentionally fixture-first and side-effect free. It accepts
redacted guardrail metadata for fee notice review, but rejects packet content
that would cross into payment details, receipt capture, payment completion, raw
authenticated page text, browser artifacts, private values, or unsafe next-step
recommendations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from ppd.devhub.payment_action_gate import PaymentGate, decide_payment_action


class FeePaymentGuardrailPacketError(ValueError):
    """Raised when a fee/payment guardrail packet is not commit-safe."""


@dataclass(frozen=True)
class FeePaymentGuardrailPacketValidation:
    """Structured validation result for safe guardrail packets."""

    packet_id: str
    fee_trigger_count: int
    safe_action_count: int
    source_evidence_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "packet_id": self.packet_id,
            "fee_trigger_count": self.fee_trigger_count,
            "safe_action_count": self.safe_action_count,
            "source_evidence_count": self.source_evidence_count,
            "validation_status": "accepted_commit_safe_fee_payment_guardrail_packet",
        }


_PAYMENT_FIELD_KEYS = {
    "account_number",
    "ach_account_number",
    "ach_routing_number",
    "bank_account",
    "bank_account_number",
    "card_cvv",
    "card_expiration",
    "card_number",
    "cardholder_name",
    "checking_account",
    "credit_card",
    "cvc",
    "cvv",
    "debit_card",
    "expiration_date",
    "expiry_date",
    "payment_account",
    "payment_instrument",
    "payment_token",
    "routing_number",
    "security_code",
}

_PRIVATE_KEYS = {
    "auth_state",
    "authorization",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "mfa_code",
    "password",
    "private_value",
    "secret",
    "session_state",
    "token",
}

_BROWSER_ARTIFACT_KEYS = {
    "browser_context",
    "browser_state",
    "download_path",
    "har",
    "har_path",
    "playwright_trace",
    "recording",
    "screenshot",
    "screenshot_path",
    "storage_state",
    "trace",
    "trace_path",
    "video_path",
}

_AUTHENTICATED_RAW_TEXT_KEYS = {
    "authenticated_raw_text",
    "auth_raw_text",
    "inner_text",
    "page_text",
    "raw_accessible_tree",
    "raw_authenticated_text",
    "raw_html",
    "raw_text",
    "text_content",
}

_RECEIPT_KEYS = {
    "payment_receipt",
    "receipt",
    "receipt_claim",
    "receipt_downloaded",
    "receipt_number",
    "receipt_saved",
}

_COMPLETION_KEYS = {
    "final_payment_complete",
    "final_payment_completed",
    "payment_complete",
    "payment_completed",
    "payment_status",
    "workflow_complete",
    "workflow_completed",
}

_PAYMENT_FIELD_TEXT_MARKERS = (
    "card number",
    "credit card",
    "debit card",
    "cvv",
    "cvc",
    "security code",
    "expiration date",
    "expiry date",
    "routing number",
    "bank account",
    "ach account",
    "payment token",
)

_PRIVATE_VALUE_MARKERS = (
    "4111111111111111",
    "4242424242424242",
    "5555555555554444",
    "password=",
    "bearer ",
    "sessionid=",
    "storage_state",
    "trace.zip",
    "har.zip",
)

_RECEIPT_CLAIM_MARKERS = (
    "receipt downloaded",
    "receipt saved",
    "saved receipt",
    "downloaded receipt",
    "receipt number",
)

_PAYMENT_COMPLETION_MARKERS = (
    "final payment complete",
    "payment completed",
    "payment complete",
    "marked paid",
    "workflow complete",
)

_SAFE_ACTION_FIELDS = ("next_safe_actions", "safe_next_actions", "recommended_safe_actions")
_FEE_TRIGGER_FIELDS = ("fee_triggers", "feeTriggers")
_SOURCE_EVIDENCE_FIELDS = ("source_evidence_ids", "sourceEvidenceIds", "source_evidence")


def validate_fee_payment_guardrail_packet(packet: Mapping[str, Any]) -> FeePaymentGuardrailPacketValidation:
    """Validate that a fee/payment guardrail packet is safe to commit.

    Accepted packets may describe cited fee triggers and read-only review actions.
    They must not include payment card or bank fields, private values,
    authenticated raw text, browser artifacts, receipt claims, payment completion
    claims, or safe-action recommendations that enter or submit payment details.
    """

    if not isinstance(packet, Mapping):
        raise FeePaymentGuardrailPacketError("fee/payment guardrail packet must be an object")

    errors = list(_walk_rejections(packet, "$"))
    errors.extend(_validate_fee_triggers(packet))
    errors.extend(_validate_safe_actions(packet))

    if errors:
        raise FeePaymentGuardrailPacketError("; ".join(errors))

    source_evidence_ids = _packet_source_evidence_ids(packet)
    packet_id = _text(packet.get("packet_id") or packet.get("guardrail_packet_id") or "fee_payment_guardrail_packet")
    return FeePaymentGuardrailPacketValidation(
        packet_id=packet_id,
        fee_trigger_count=len(_fee_triggers(packet)),
        safe_action_count=len(_safe_actions(packet)),
        source_evidence_count=len(source_evidence_ids),
    )


def _walk_rejections(value: Any, path: str) -> Iterable[str]:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized_key = _normalize_token(key_text)
            child_path = f"{path}.{key_text}"

            if normalized_key in _PAYMENT_FIELD_KEYS:
                yield f"{child_path} contains prohibited payment card or bank field"
            if normalized_key in _PRIVATE_KEYS:
                yield f"{child_path} contains prohibited private value field"
            if normalized_key in _BROWSER_ARTIFACT_KEYS:
                yield f"{child_path} contains prohibited browser artifact field"
            if normalized_key in _AUTHENTICATED_RAW_TEXT_KEYS:
                yield f"{child_path} contains prohibited authenticated raw text field"
            if normalized_key in _RECEIPT_KEYS:
                yield f"{child_path} contains prohibited receipt claim field"
            if normalized_key in _COMPLETION_KEYS and _looks_like_completion_claim(child):
                yield f"{child_path} claims final payment completion"

            yield from _walk_rejections(child, child_path)
        return

    if isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_rejections(child, f"{path}[{index}]")
        return

    if isinstance(value, str):
        lowered = value.casefold()
        if any(marker in lowered for marker in _PAYMENT_FIELD_TEXT_MARKERS):
            yield f"{path} contains prohibited payment card or bank text"
        if any(marker in lowered for marker in _PRIVATE_VALUE_MARKERS):
            yield f"{path} contains prohibited private or browser artifact value"
        if _path_allows_claim_text(path) and any(marker in lowered for marker in _RECEIPT_CLAIM_MARKERS):
            yield f"{path} claims payment receipt handling"
        if _path_allows_claim_text(path) and any(marker in lowered for marker in _PAYMENT_COMPLETION_MARKERS):
            yield f"{path} claims final payment completion"


def _validate_fee_triggers(packet: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    packet_evidence = _packet_source_evidence_ids(packet)
    for index, trigger in enumerate(_fee_triggers(packet)):
        path = f"$.fee_triggers[{index}]"
        if not isinstance(trigger, Mapping):
            errors.append(f"{path} must be an object")
            continue
        trigger_text = _text(trigger.get("trigger") or trigger.get("label") or trigger.get("description"))
        trigger_evidence = _evidence_ids(trigger)
        if not trigger_text:
            errors.append(f"{path} must describe the fee trigger")
        if not trigger_evidence:
            errors.append(f"{path} must cite source evidence")
        elif packet_evidence and not set(trigger_evidence).issubset(set(packet_evidence)):
            errors.append(f"{path} cites evidence not declared by the packet")
    return errors


def _validate_safe_actions(packet: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for index, action in enumerate(_safe_actions(packet)):
        path = f"$.next_safe_actions[{index}]"
        descriptor = _action_descriptor(action)
        decision = decide_payment_action(descriptor)
        if decision.gate is PaymentGate.REFUSED:
            errors.append(f"{path} recommends refused payment action {decision.category.value}")
        elif decision.allowed is False and decision.gate is not PaymentGate.SAFE_READ_ONLY:
            errors.append(f"{path} recommends payment handoff action as safe automation")
    return errors


def _fee_triggers(packet: Mapping[str, Any]) -> list[Any]:
    for field in _FEE_TRIGGER_FIELDS:
        value = packet.get(field)
        if isinstance(value, list):
            return value
    return []


def _safe_actions(packet: Mapping[str, Any]) -> list[Any]:
    for field in _SAFE_ACTION_FIELDS:
        value = packet.get(field)
        if isinstance(value, list):
            return value
    return []


def _packet_source_evidence_ids(packet: Mapping[str, Any]) -> tuple[str, ...]:
    evidence_ids: list[str] = []
    for field in _SOURCE_EVIDENCE_FIELDS:
        value = packet.get(field)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    evidence_ids.append(item)
                elif isinstance(item, Mapping):
                    item_id = _text(item.get("id") or item.get("evidence_id"))
                    if item_id:
                        evidence_ids.append(item_id)
    return tuple(dict.fromkeys(evidence_ids))


def _evidence_ids(value: Mapping[str, Any]) -> tuple[str, ...]:
    ids: list[str] = []
    for field in ("source_evidence_ids", "sourceEvidenceIds", "evidence_ids", "evidenceId", "evidence_id"):
        item = value.get(field)
        if isinstance(item, str) and item.strip():
            ids.append(item.strip())
        elif isinstance(item, list):
            ids.extend(_text(child) for child in item if _text(child))
    return tuple(dict.fromkeys(ids))


def _action_descriptor(action: Any) -> dict[str, Any]:
    if isinstance(action, Mapping):
        return dict(action)
    return {"action_id": _text(action) or "next_safe_action", "label": _text(action), "kind": "recommendation"}


def _looks_like_completion_claim(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, str):
        lowered = value.casefold().strip()
        return lowered in {"complete", "completed", "paid", "true", "yes"} or any(
            marker in lowered for marker in _PAYMENT_COMPLETION_MARKERS
        )
    return False


def _path_allows_claim_text(path: str) -> bool:
    lowered = path.casefold()
    return any(marker in lowered for marker in ("claim", "outcome", "receipt", "completion", "status", "evidence"))


def _normalize_token(value: str) -> str:
    normalized = []
    for character in value.strip():
        if character.isalnum():
            normalized.append(character.lower())
        else:
            normalized.append("_")
    return "_".join(part for part in "".join(normalized).split("_") if part)


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""
