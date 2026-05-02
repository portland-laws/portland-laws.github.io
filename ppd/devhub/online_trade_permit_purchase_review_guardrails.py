"""Guardrails for DevHub online trade permit purchase review actions.

This module is fixture-only policy logic. It does not open DevHub, authenticate,
submit, certify, pay, cancel, schedule inspections, or persist browser/session
artifacts.
"""

from __future__ import annotations

from typing import Any, Mapping

PREVIEW_ACTION = "preview_online_trade_permit_purchase_review"
GUARDED_ACTIONS = {
    "official_online_trade_permit_purchase": "consequential",
    "certify_online_trade_permit_purchase": "consequential",
    "pay_online_trade_permit_fees": "financial",
    "cancel_online_trade_permit_purchase": "consequential",
    "schedule_online_trade_permit_inspection": "consequential",
}
REFUSED_STATUS = "refused_missing_exact_session_confirmation"
PREVIEW_STATUS = "preview_ready"
CONFIRMED_STATUS = "exact_session_confirmation_present"


def build_purchase_review_preview(workflow: Mapping[str, Any]) -> dict[str, Any]:
    """Return a redacted, non-official preview for a mocked purchase review."""

    permit = _string(workflow.get("permitType"))
    session_id = _string(workflow.get("sessionId"))
    review_steps = workflow.get("reviewSteps", [])
    if not isinstance(review_steps, list):
        review_steps = []

    return {
        "status": PREVIEW_STATUS,
        "actionId": PREVIEW_ACTION,
        "sessionId": session_id,
        "permitType": permit,
        "officialActionPerformed": False,
        "paymentAttempted": False,
        "certificationAttempted": False,
        "cancellationAttempted": False,
        "inspectionSchedulingAttempted": False,
        "reviewSteps": [_redacted_step(step) for step in review_steps if isinstance(step, Mapping)],
    }


def evaluate_purchase_review_action(
    workflow: Mapping[str, Any],
    action_id: str,
    confirmation: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Classify whether a requested purchase-review action may proceed.

    Preview is read-only and always returns a non-official preview. Official
    purchase, certification, payment, cancellation, and inspection scheduling are
    refused unless the confirmation matches the current fixture session, the
    exact action id, and the exact session-specific confirmation phrase.
    """

    if action_id == PREVIEW_ACTION:
        return build_purchase_review_preview(workflow)

    if action_id not in GUARDED_ACTIONS:
        return {
            "status": "refused_unknown_action",
            "actionId": action_id,
            "allowed": False,
            "officialActionPerformed": False,
            "reason": "action is not part of the online trade permit purchase review fixture",
        }

    confirmation = confirmation or {}
    expected_session_id = _string(workflow.get("sessionId"))
    expected_phrase = _string(workflow.get("requiredConfirmationPhrase"))
    confirmation_session_id = _string(confirmation.get("sessionId"))
    confirmation_action_id = _string(confirmation.get("actionId"))
    confirmation_phrase = _string(confirmation.get("phrase"))

    classification = GUARDED_ACTIONS[action_id]
    matches = (
        confirmation_session_id == expected_session_id
        and confirmation_action_id == action_id
        and confirmation_phrase == expected_phrase
        and expected_session_id != ""
        and expected_phrase != ""
    )

    if not matches:
        return {
            "status": REFUSED_STATUS,
            "actionId": action_id,
            "classification": classification,
            "allowed": False,
            "officialActionPerformed": False,
            "paymentAttempted": False,
            "requiredSessionId": expected_session_id,
            "requiredConfirmationPhrase": expected_phrase,
            "receivedSessionId": confirmation_session_id,
            "receivedActionId": confirmation_action_id,
            "receivedPhrase": confirmation_phrase,
            "reason": "exact current-session confirmation for this specific action is required",
        }

    return {
        "status": CONFIRMED_STATUS,
        "actionId": action_id,
        "classification": classification,
        "allowed": True,
        "officialActionPerformed": False,
        "paymentAttempted": False,
        "sessionId": expected_session_id,
        "confirmationRecorded": True,
        "nextStep": "hand off to guarded executor checkpoint; this fixture performs no live DevHub action",
    }


def validate_purchase_review_fixture(data: Mapping[str, Any]) -> list[str]:
    """Validate the deterministic fixture used by guardrail tests."""

    errors: list[str] = []
    workflow = data.get("workflow")
    attempts = data.get("attempts")
    if not isinstance(workflow, Mapping):
        return ["fixture workflow must be an object"]
    if not isinstance(attempts, list) or not attempts:
        errors.append("fixture attempts must be a non-empty list")
        attempts = []

    if _string(workflow.get("sessionId")) == "":
        errors.append("workflow sessionId is required")
    if _string(workflow.get("requiredConfirmationPhrase")) == "":
        errors.append("workflow requiredConfirmationPhrase is required")
    if _string(workflow.get("permitType")) != "online_trade_permit":
        errors.append("workflow permitType must be online_trade_permit")

    private_markers = ("password", "token", "secret", "cookie", "trace", "screenshot", "authState")
    serialized = repr(data).lower()
    for marker in private_markers:
        if marker.lower() in serialized:
            errors.append(f"fixture must not contain private DevHub artifact marker: {marker}")

    for index, attempt in enumerate(attempts):
        if not isinstance(attempt, Mapping):
            errors.append(f"attempt {index} must be an object")
            continue
        action_id = _string(attempt.get("actionId"))
        expected_status = _string(attempt.get("expectedStatus"))
        decision = evaluate_purchase_review_action(
            workflow,
            action_id,
            attempt.get("confirmation") if isinstance(attempt.get("confirmation"), Mapping) else None,
        )
        if decision.get("status") != expected_status:
            errors.append(
                f"attempt {index} expected {expected_status or ''} "
                f"but evaluated {decision.get('status')}"
            )
    return errors


def _redacted_step(step: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "id": _string(step.get("id")),
        "label": _string(step.get("label")),
        "sourceRequirement": _string(step.get("sourceRequirement")),
        "redactedValue": _string(step.get("redactedValue", "[REDACTED]")),
    }


def _string(value: Any) -> str:
    if value is None:
        return ""
    return str(value)
