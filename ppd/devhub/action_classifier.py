"""Guarded action classification for DevHub workflow models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ppd.contracts.processes import ActionGateClassification

from .workflow import DevHubActionKind, DevHubWorkflowAction


FINANCIAL_ACTIONS = {
    DevHubActionKind.PAY_FEE,
    DevHubActionKind.ENTER_PAYMENT_DETAILS,
}

CONSEQUENTIAL_ACTIONS = {
    DevHubActionKind.SUBMIT_APPLICATION,
    DevHubActionKind.OFFICIAL_UPLOAD,
    DevHubActionKind.SCHEDULE_INSPECTION,
    DevHubActionKind.CANCEL_REQUEST,
    DevHubActionKind.CERTIFY_ACKNOWLEDGMENT,
}

DRAFT_EDIT_ACTIONS = {
    DevHubActionKind.SAVE_DRAFT,
    DevHubActionKind.FILL_FIELD,
    DevHubActionKind.ATTACH_DRAFT_FILE,
}

CONFIRMATION_REQUIRED_CLASSIFICATIONS = {
    ActionGateClassification.POTENTIALLY_CONSEQUENTIAL,
    ActionGateClassification.FINANCIAL,
}


@dataclass(frozen=True)
class ActionConfirmationDecision:
    """Result of checking whether a proposed DevHub action may proceed."""

    allowed: bool
    classification: ActionGateClassification
    requires_exact_confirmation: bool
    expected_confirmation: Optional[str] = None
    reason: str = ""


def classify_workflow_action(action: DevHubWorkflowAction) -> ActionGateClassification:
    if action.kind in FINANCIAL_ACTIONS:
        return ActionGateClassification.FINANCIAL
    if action.kind in CONSEQUENTIAL_ACTIONS:
        return ActionGateClassification.POTENTIALLY_CONSEQUENTIAL
    if action.kind in DRAFT_EDIT_ACTIONS:
        return ActionGateClassification.REVERSIBLE_DRAFT_EDIT
    return ActionGateClassification.SAFE_READ_ONLY


def action_requires_exact_confirmation(action: DevHubWorkflowAction) -> bool:
    """Return True when an action is consequential or financial."""

    return classify_workflow_action(action) in CONFIRMATION_REQUIRED_CLASSIFICATIONS


def is_exactly_confirmed(action: DevHubWorkflowAction, user_confirmation: Optional[str]) -> bool:
    """Check the high-friction confirmation gate for consequential actions.

    Confirmation is intentionally exact and case-sensitive. Surrounding
    whitespace is ignored so copy/paste from a prompt does not fail because of a
    stray newline, but paraphrases, partial text, punctuation changes, and case
    changes do not authorize the action.
    """

    if not action_requires_exact_confirmation(action):
        return True
    expected = (action.confirmation_text or "").strip()
    provided = (user_confirmation or "").strip()
    return bool(expected) and provided == expected


def decide_action_confirmation(
    action: DevHubWorkflowAction,
    user_confirmation: Optional[str],
) -> ActionConfirmationDecision:
    """Return an auditable allow/deny decision for a DevHub action."""

    classification = classify_workflow_action(action)
    requires_confirmation = classification in CONFIRMATION_REQUIRED_CLASSIFICATIONS
    expected = (action.confirmation_text or "").strip() or None

    if not requires_confirmation:
        return ActionConfirmationDecision(
            allowed=True,
            classification=classification,
            requires_exact_confirmation=False,
            expected_confirmation=None,
            reason="action does not require explicit confirmation",
        )

    if not expected:
        return ActionConfirmationDecision(
            allowed=False,
            classification=classification,
            requires_exact_confirmation=True,
            expected_confirmation=None,
            reason="consequential or financial action has no configured confirmation text",
        )

    if is_exactly_confirmed(action, user_confirmation):
        return ActionConfirmationDecision(
            allowed=True,
            classification=classification,
            requires_exact_confirmation=True,
            expected_confirmation=expected,
            reason="user supplied the exact explicit confirmation text",
        )

    return ActionConfirmationDecision(
        allowed=False,
        classification=classification,
        requires_exact_confirmation=True,
        expected_confirmation=expected,
        reason="user confirmation did not exactly match the required text",
    )
