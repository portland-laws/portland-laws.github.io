"""Deterministic fee/payment action gates for DevHub assistance.

This module intentionally does not launch a browser, inspect live DevHub pages,
store payment details, or mark payment workflows complete. It classifies caller-
provided action descriptors so higher-level automation can stop before financial
or completion-sensitive steps.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
from typing import Any, Mapping, Sequence


class PaymentGate(str, Enum):
    """Stable gate names used by DevHub guardrail callers."""

    SAFE_READ_ONLY = "safe_read_only"
    MANUAL_HANDOFF = "manual_handoff"
    REFUSED = "refused"


class PaymentActionCategory(str, Enum):
    """Known fee/payment action categories."""

    FEE_NOTICE_REVIEW = "fee_notice_review"
    OPEN_PAYMENT_SURFACE = "open_payment_surface"
    PAYMENT_DETAIL_ENTRY = "payment_detail_entry"
    SUBMIT_PAYMENT = "submit_payment"
    SAVE_PAYMENT_RECEIPT = "save_payment_receipt"
    COMPLETE_PAYMENT_WORKFLOW = "complete_payment_workflow"
    UNKNOWN_PAYMENT_ACTION = "unknown_payment_action"


@dataclass(frozen=True)
class PaymentActionDecision:
    """Result of classifying a fee/payment action descriptor."""

    action_id: str
    category: PaymentActionCategory
    gate: PaymentGate
    allowed: bool
    reasons: tuple[str, ...]
    required_confirmation: str | None = None
    safe_next_actions: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "category": self.category.value,
            "gate": self.gate.value,
            "allowed": self.allowed,
            "reasons": list(self.reasons),
            "required_confirmation": self.required_confirmation,
            "safe_next_actions": list(self.safe_next_actions),
        }


_PAYMENT_DETAIL_MARKERS = (
    "card",
    "credit card",
    "debit card",
    "cvv",
    "cvc",
    "security code",
    "expiration",
    "expiry",
    "routing",
    "account number",
    "bank account",
    "ach",
    "echeck",
    "payment token",
    "billing address",
)

_SUBMIT_MARKERS = (
    "submit payment",
    "pay now",
    "make payment",
    "complete payment",
    "authorize payment",
    "process payment",
    "purchase permit",
    "confirm payment",
)

_RECEIPT_MARKERS = (
    "save receipt",
    "download receipt",
    "payment receipt",
    "receipt number",
)

_COMPLETE_MARKERS = (
    "mark paid",
    "payment complete",
    "workflow complete",
    "complete workflow",
    "finish payment",
)

_OPEN_PAYMENT_MARKERS = (
    "pay fees",
    "payment portal",
    "payment page",
    "checkout",
)

_REVIEW_MARKERS = (
    "fee notice",
    "fees due",
    "balance due",
    "review fees",
    "view fees",
    "invoice review",
)


def normalize_action_text(action: Mapping[str, Any]) -> str:
    """Return a deterministic lower-case text blob for classification."""

    parts: list[str] = []
    for key in ("action_id", "label", "kind", "url", "text", "aria_label", "role"):
        value = action.get(key)
        if isinstance(value, str):
            parts.append(value)
    fields = action.get("fields")
    if isinstance(fields, Sequence) and not isinstance(fields, (str, bytes)):
        for field in fields:
            if isinstance(field, str):
                parts.append(field)
            elif isinstance(field, Mapping):
                for key in ("name", "label", "placeholder", "autocomplete"):
                    value = field.get(key)
                    if isinstance(value, str):
                        parts.append(value)
    return " ".join(parts).casefold()


def _contains_any(text: str, markers: Sequence[str]) -> bool:
    return any(marker in text for marker in markers)


def classify_payment_action(action: Mapping[str, Any]) -> PaymentActionCategory:
    """Classify a caller-supplied action descriptor without side effects."""

    text = normalize_action_text(action)
    if _contains_any(text, _PAYMENT_DETAIL_MARKERS):
        return PaymentActionCategory.PAYMENT_DETAIL_ENTRY
    if _contains_any(text, _SUBMIT_MARKERS):
        return PaymentActionCategory.SUBMIT_PAYMENT
    if _contains_any(text, _COMPLETE_MARKERS):
        return PaymentActionCategory.COMPLETE_PAYMENT_WORKFLOW
    if _contains_any(text, _RECEIPT_MARKERS):
        return PaymentActionCategory.SAVE_PAYMENT_RECEIPT
    if _contains_any(text, _OPEN_PAYMENT_MARKERS):
        return PaymentActionCategory.OPEN_PAYMENT_SURFACE
    if _contains_any(text, _REVIEW_MARKERS):
        return PaymentActionCategory.FEE_NOTICE_REVIEW
    return PaymentActionCategory.UNKNOWN_PAYMENT_ACTION


def decide_payment_action(action: Mapping[str, Any]) -> PaymentActionDecision:
    """Return the smallest safe gate decision for a fee/payment action."""

    action_id = str(action.get("action_id") or action.get("label") or "payment_action")
    category = classify_payment_action(action)

    if category is PaymentActionCategory.FEE_NOTICE_REVIEW:
        return PaymentActionDecision(
            action_id=action_id,
            category=category,
            gate=PaymentGate.SAFE_READ_ONLY,
            allowed=True,
            reasons=("Fee notice review is read-only and does not enter or submit payment details.",),
            safe_next_actions=("summarize_fee_notice", "ask_user_for_manual_payment_handoff"),
        )

    if category is PaymentActionCategory.OPEN_PAYMENT_SURFACE:
        return PaymentActionDecision(
            action_id=action_id,
            category=category,
            gate=PaymentGate.MANUAL_HANDOFF,
            allowed=False,
            reasons=("Opening or proceeding into a payment surface is a financial workflow boundary.",),
            required_confirmation="User must attend and handle payment workflow manually.",
            safe_next_actions=("review_fee_notice", "manual_payment_handoff"),
        )

    if category is PaymentActionCategory.PAYMENT_DETAIL_ENTRY:
        return PaymentActionDecision(
            action_id=action_id,
            category=category,
            gate=PaymentGate.REFUSED,
            allowed=False,
            reasons=("Payment-detail entry must not be automated or stored.",),
            required_confirmation="User must enter payment details manually outside automation.",
            safe_next_actions=("manual_payment_handoff",),
        )

    if category is PaymentActionCategory.SUBMIT_PAYMENT:
        return PaymentActionDecision(
            action_id=action_id,
            category=category,
            gate=PaymentGate.REFUSED,
            allowed=False,
            reasons=("Final payment execution is consequential and must not be automated.",),
            required_confirmation="User must submit any payment manually and confirm the visible outcome themselves.",
            safe_next_actions=("manual_payment_handoff",),
        )

    if category is PaymentActionCategory.SAVE_PAYMENT_RECEIPT:
        return PaymentActionDecision(
            action_id=action_id,
            category=category,
            gate=PaymentGate.MANUAL_HANDOFF,
            allowed=False,
            reasons=("Receipts can contain private financial or account-scoped details and must not be saved by automation.",),
            required_confirmation="User may save any receipt manually after payment.",
            safe_next_actions=("record_redacted_manual_outcome",),
        )

    if category is PaymentActionCategory.COMPLETE_PAYMENT_WORKFLOW:
        return PaymentActionDecision(
            action_id=action_id,
            category=category,
            gate=PaymentGate.REFUSED,
            allowed=False,
            reasons=("Automation must not mark a payment workflow complete.",),
            required_confirmation="Completion requires user-visible post-action evidence, not an automated claim.",
            safe_next_actions=("record_redacted_manual_outcome",),
        )

    return PaymentActionDecision(
        action_id=action_id,
        category=category,
        gate=PaymentGate.MANUAL_HANDOFF,
        allowed=False,
        reasons=("Unknown fee/payment actions default to manual handoff.",),
        required_confirmation="User attendance is required before continuing.",
        safe_next_actions=("review_fee_notice", "manual_payment_handoff"),
    )


def load_payment_action_fixtures(path: str | Path) -> list[dict[str, Any]]:
    """Load deterministic fixture cases for local validation."""

    fixture_path = Path(path)
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    cases = data.get("cases")
    if not isinstance(cases, list):
        raise ValueError("payment action fixture must contain a cases list")
    return cases


def validate_payment_action_fixtures(path: str | Path) -> list[PaymentActionDecision]:
    """Validate fixture expectations and return computed decisions."""

    decisions: list[PaymentActionDecision] = []
    for case in load_payment_action_fixtures(path):
        if not isinstance(case, Mapping):
            raise ValueError("payment action fixture case must be an object")
        action = case.get("action")
        if not isinstance(action, Mapping):
            raise ValueError("payment action fixture case must contain an action object")
        decision = decide_payment_action(action)
        expected_category = case.get("expected_category")
        expected_gate = case.get("expected_gate")
        expected_allowed = case.get("expected_allowed")
        if expected_category is not None and decision.category.value != expected_category:
            raise AssertionError(f"{decision.action_id}: expected category {expected_category}, got {decision.category.value}")
        if expected_gate is not None and decision.gate.value != expected_gate:
            raise AssertionError(f"{decision.action_id}: expected gate {expected_gate}, got {decision.gate.value}")
        if expected_allowed is not None and decision.allowed is not expected_allowed:
            raise AssertionError(f"{decision.action_id}: expected allowed {expected_allowed}, got {decision.allowed}")
        decisions.append(decision)
    return decisions
