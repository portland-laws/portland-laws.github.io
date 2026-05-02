"""Exact-confirmation guardrails for mocked Playwright DevHub actions.

This module is intentionally fixture-only and browser-free. It models the
preflight decision a Playwright executor must make before touching consequential,
financial, verification, or account-recovery controls in DevHub.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PlaywrightGuardedAction(str, Enum):
    OFFICIAL_UPLOAD = "official_upload"
    SUBMIT_APPLICATION = "submit_application"
    CERTIFY_STATEMENT = "certify_statement"
    PAY_FEES = "pay_fees"
    CANCEL_REQUEST = "cancel_request"
    SCHEDULE_INSPECTION = "schedule_inspection"
    COMPLETE_MFA = "complete_mfa"
    COMPLETE_CAPTCHA = "complete_captcha"
    CREATE_ACCOUNT = "create_account"
    RECOVER_PASSWORD = "recover_password"


class PlaywrightGuardrailOutcome(str, Enum):
    ALLOW_WITH_EXACT_CONFIRMATION = "allow_with_exact_confirmation"
    REFUSE_MISSING_EXACT_CONFIRMATION = "refuse_missing_exact_confirmation"
    REFUSE_MANUAL_CONTROL_REQUIRED = "refuse_manual_control_required"


CONFIRMATION_PHRASES: dict[PlaywrightGuardedAction, str] = {
    PlaywrightGuardedAction.OFFICIAL_UPLOAD: "I confirm this exact DevHub official upload action.",
    PlaywrightGuardedAction.SUBMIT_APPLICATION: "I confirm this exact DevHub submit application action.",
    PlaywrightGuardedAction.CERTIFY_STATEMENT: "I confirm this exact DevHub certification action.",
    PlaywrightGuardedAction.PAY_FEES: "I confirm this exact DevHub payment action.",
    PlaywrightGuardedAction.CANCEL_REQUEST: "I confirm this exact DevHub cancellation action.",
    PlaywrightGuardedAction.SCHEDULE_INSPECTION: "I confirm this exact DevHub inspection scheduling action.",
    PlaywrightGuardedAction.COMPLETE_MFA: "I confirm this exact DevHub MFA action.",
    PlaywrightGuardedAction.COMPLETE_CAPTCHA: "I confirm this exact DevHub CAPTCHA action.",
    PlaywrightGuardedAction.CREATE_ACCOUNT: "I confirm this exact DevHub account creation action.",
    PlaywrightGuardedAction.RECOVER_PASSWORD: "I confirm this exact DevHub password recovery action.",
}

MANUAL_CONTROL_ACTIONS = frozenset(
    {
        PlaywrightGuardedAction.COMPLETE_MFA,
        PlaywrightGuardedAction.COMPLETE_CAPTCHA,
        PlaywrightGuardedAction.CREATE_ACCOUNT,
        PlaywrightGuardedAction.RECOVER_PASSWORD,
    }
)


@dataclass(frozen=True)
class PlaywrightGuardrailDecision:
    action: PlaywrightGuardedAction
    outcome: PlaywrightGuardrailOutcome
    exact_confirmation_present: bool
    required_confirmation: str
    may_click_playwright_control: bool
    reason: str

    @property
    def refused(self) -> bool:
        return self.outcome != PlaywrightGuardrailOutcome.ALLOW_WITH_EXACT_CONFIRMATION


def evaluate_playwright_guarded_action(
    action: PlaywrightGuardedAction | str,
    user_confirmation: str | None,
) -> PlaywrightGuardrailDecision:
    """Evaluate whether a mocked Playwright action may proceed.

    Confirmation is exact string equality. Case changes, added whitespace,
    paraphrases, and generic approvals are treated as missing confirmation.
    MFA, CAPTCHA, account creation, and password recovery remain manual-control
    flows even when the user supplies the exact phrase.
    """

    guarded_action = action if isinstance(action, PlaywrightGuardedAction) else PlaywrightGuardedAction(action)
    required_confirmation = CONFIRMATION_PHRASES[guarded_action]
    exact_confirmation_present = user_confirmation == required_confirmation

    if not exact_confirmation_present:
        return PlaywrightGuardrailDecision(
            action=guarded_action,
            outcome=PlaywrightGuardrailOutcome.REFUSE_MISSING_EXACT_CONFIRMATION,
            exact_confirmation_present=False,
            required_confirmation=required_confirmation,
            may_click_playwright_control=False,
            reason="Exact user confirmation is required before this DevHub action can be considered.",
        )

    if guarded_action in MANUAL_CONTROL_ACTIONS:
        return PlaywrightGuardrailDecision(
            action=guarded_action,
            outcome=PlaywrightGuardrailOutcome.REFUSE_MANUAL_CONTROL_REQUIRED,
            exact_confirmation_present=True,
            required_confirmation=required_confirmation,
            may_click_playwright_control=False,
            reason="This DevHub verification or account-control flow must be completed manually by the user.",
        )

    return PlaywrightGuardrailDecision(
        action=guarded_action,
        outcome=PlaywrightGuardrailOutcome.ALLOW_WITH_EXACT_CONFIRMATION,
        exact_confirmation_present=True,
        required_confirmation=required_confirmation,
        may_click_playwright_control=True,
        reason="Exact user confirmation is present for the named DevHub action.",
    )
