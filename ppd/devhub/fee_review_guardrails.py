"""Fixture-backed DevHub fee review guardrails.

This module models read-only fee/payment readiness review from redacted DevHub
fixtures. It deliberately does not automate payment-detail entry or payment
execution. Exact session-specific confirmation can satisfy a checkpoint, but the
financial action remains a manual handoff rather than a browser action.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Mapping


READ_ONLY_SUMMARY_ACTION = "summarize_payment_readiness"
ENTER_PAYMENT_DETAILS_ACTION = "enter_payment_details"
EXECUTE_PAYMENT_ACTION = "execute_payment"

FINANCIAL_ACTIONS = {ENTER_PAYMENT_DETAILS_ACTION, EXECUTE_PAYMENT_ACTION}

_PAYMENT_DETAIL_KEYS = {
    "account_number",
    "bank_account",
    "card_cvv",
    "card_expiration",
    "card_number",
    "credit_card",
    "cvv",
    "expiration_date",
    "payment_account",
    "routing_number",
    "security_code",
}

_PRIVATE_VALUE_MARKERS = (
    "4111",
    "4242",
    "5555",
    "amex",
    "mastercard",
    "visa",
    "cvv",
    "routing",
    "password",
    "token",
)


def summarize_payment_readiness(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """Return a read-only summary of mocked DevHub fee payment readiness."""

    _assert_commit_safe_fixture(snapshot)
    fees = list(snapshot.get("feeLineItems", snapshot.get("fee_line_items", ())))
    payable_items = [_summarize_fee_item(item) for item in fees if _is_payable_now(item)]
    deferred_items = [_summarize_fee_item(item) for item in fees if not _is_payable_now(item)]
    total_due = sum((Decimal(str(item["amount"])) for item in payable_items), Decimal("0.00"))

    pay_button_visible = bool(snapshot.get("payButtonVisible", snapshot.get("pay_button_visible", False)))
    signed_in = bool(snapshot.get("accountSignedIn", snapshot.get("account_signed_in", False)))
    has_payable_items = bool(payable_items)
    ready_for_user_review = signed_in and pay_button_visible and has_payable_items

    return {
        "action": READ_ONLY_SUMMARY_ACTION,
        "action_classification": "safe_read_only",
        "ready_for_user_payment_review": ready_for_user_review,
        "payable_item_count": len(payable_items),
        "total_due": _format_money(total_due),
        "currency": str(snapshot.get("currency", "USD")),
        "payable_items": payable_items,
        "deferred_or_blocked_items": deferred_items,
        "blocked_agent_actions": sorted(FINANCIAL_ACTIONS),
        "source_evidence": list(snapshot.get("sourceEvidence", snapshot.get("source_evidence", ()))),
    }


def evaluate_fee_review_action(
    snapshot: Mapping[str, Any],
    action: str,
    confirmation_text: str = "",
    session_id: str = "",
) -> dict[str, Any]:
    """Evaluate whether a DevHub fee-review action is allowed for automation."""

    _assert_commit_safe_fixture(snapshot)
    normalized_action = action.strip().lower()

    if normalized_action == READ_ONLY_SUMMARY_ACTION:
        return {
            "action": normalized_action,
            "action_classification": "safe_read_only",
            "permitted": True,
            "confirmation_satisfied": True,
            "summary": summarize_payment_readiness(snapshot),
            "refusal_reasons": [],
        }

    if normalized_action not in FINANCIAL_ACTIONS:
        return {
            "action": normalized_action,
            "action_classification": "unknown",
            "permitted": False,
            "confirmation_satisfied": False,
            "refusal_reasons": ["unknown_fee_review_action"],
        }

    confirmation_satisfied = _has_exact_session_confirmation(snapshot, confirmation_text, session_id)
    refusal_reasons = []
    if not confirmation_satisfied:
        refusal_reasons.append("exact_session_specific_user_confirmation_required")

    if normalized_action == ENTER_PAYMENT_DETAILS_ACTION:
        refusal_reasons.append("payment_detail_entry_must_remain_manual")
    else:
        refusal_reasons.append("payment_execution_must_remain_manual")

    return {
        "action": normalized_action,
        "action_classification": "financial",
        "permitted": False,
        "confirmation_satisfied": confirmation_satisfied,
        "expected_session_id": str(snapshot.get("sessionId", snapshot.get("session_id", ""))),
        "refusal_reasons": refusal_reasons,
    }


def _summarize_fee_item(item: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "id": str(item.get("id", "")),
        "label": str(item.get("label", "")),
        "amount": _format_money(Decimal(str(item.get("amount", "0.00")))),
        "status": str(item.get("status", "")),
        "can_pay_now": bool(item.get("canPayNow", item.get("can_pay_now", False))),
        "evidence_id": str(item.get("evidenceId", item.get("evidence_id", ""))),
    }


def _is_payable_now(item: Mapping[str, Any]) -> bool:
    status = str(item.get("status", "")).lower()
    return bool(item.get("canPayNow", item.get("can_pay_now", False))) and status in {"due", "payable", "ready"}


def _has_exact_session_confirmation(snapshot: Mapping[str, Any], confirmation_text: str, session_id: str) -> bool:
    expected_session_id = str(snapshot.get("sessionId", snapshot.get("session_id", "")))
    confirmation = snapshot.get("confirmation", {})
    if not isinstance(confirmation, Mapping):
        return False
    expected_text = str(confirmation.get("exactText", confirmation.get("exact_text", "")))
    return bool(expected_session_id and expected_text) and session_id == expected_session_id and confirmation_text == expected_text


def _format_money(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.01'))}"


def _assert_commit_safe_fixture(value: Any) -> None:
    findings = list(_walk_unsafe_values(value, "$"))
    if findings:
        raise ValueError("DevHub fee review fixture contains unsafe payment/private data: " + "; ".join(findings))


def _walk_unsafe_values(value: Any, path: str) -> list[str]:
    findings: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized_key = key_text.strip().lower()
            child_path = f"{path}.{key_text}"
            if normalized_key in _PAYMENT_DETAIL_KEYS:
                findings.append(f"{child_path} uses prohibited payment detail key")
            findings.extend(_walk_unsafe_values(child, child_path))
        return findings

    if isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(_walk_unsafe_values(child, f"{path}[{index}]"))
        return findings

    if isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in _PRIVATE_VALUE_MARKERS):
            findings.append(f"{path} contains prohibited private/payment marker")
    return findings
