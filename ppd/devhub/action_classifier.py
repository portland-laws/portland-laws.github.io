"""Guarded action classification for DevHub workflow models."""

from __future__ import annotations

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


def classify_workflow_action(action: DevHubWorkflowAction) -> ActionGateClassification:
    if action.kind in FINANCIAL_ACTIONS:
        return ActionGateClassification.FINANCIAL
    if action.kind in CONSEQUENTIAL_ACTIONS:
        return ActionGateClassification.POTENTIALLY_CONSEQUENTIAL
    if action.kind in DRAFT_EDIT_ACTIONS:
        return ActionGateClassification.REVERSIBLE_DRAFT_EDIT
    return ActionGateClassification.SAFE_READ_ONLY
