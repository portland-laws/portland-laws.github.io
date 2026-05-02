"""Fixture-only Playwright guardrail tests for exact DevHub confirmations."""

from __future__ import annotations

from ppd.devhub.playwright_confirmation_guardrails import (
    CONFIRMATION_PHRASES,
    MANUAL_CONTROL_ACTIONS,
    PlaywrightGuardedAction,
    PlaywrightGuardrailOutcome,
    evaluate_playwright_guarded_action,
)


CONSEQUENTIAL_OR_FINANCIAL_ACTIONS = {
    PlaywrightGuardedAction.OFFICIAL_UPLOAD,
    PlaywrightGuardedAction.SUBMIT_APPLICATION,
    PlaywrightGuardedAction.CERTIFY_STATEMENT,
    PlaywrightGuardedAction.PAY_FEES,
    PlaywrightGuardedAction.CANCEL_REQUEST,
    PlaywrightGuardedAction.SCHEDULE_INSPECTION,
}


NEAR_MISS_CONFIRMATIONS = (
    None,
    "",
    "yes",
    "confirmed",
    "I approve DevHub actions.",
    "I confirm this DevHub action.",
    "I confirm this exact devhub payment action.",
    " I confirm this exact DevHub payment action.",
    "I confirm this exact DevHub payment action. ",
)


def test_guardrail_inventory_covers_all_required_high_risk_actions() -> None:
    expected_actions = {
        PlaywrightGuardedAction.OFFICIAL_UPLOAD,
        PlaywrightGuardedAction.SUBMIT_APPLICATION,
        PlaywrightGuardedAction.CERTIFY_STATEMENT,
        PlaywrightGuardedAction.PAY_FEES,
        PlaywrightGuardedAction.CANCEL_REQUEST,
        PlaywrightGuardedAction.SCHEDULE_INSPECTION,
        PlaywrightGuardedAction.COMPLETE_MFA,
        PlaywrightGuardedAction.COMPLETE_CAPTCHA,
        PlaywrightGuardedAction.CREATE_ACCOUNT,
        PlaywrightGuardedAction.RECOVER_PASSWORD,
    }

    assert set(CONFIRMATION_PHRASES) == expected_actions
    assert all(phrase.startswith("I confirm this exact DevHub ") for phrase in CONFIRMATION_PHRASES.values())


def test_high_risk_playwright_actions_are_refused_without_exact_confirmation() -> None:
    for action in PlaywrightGuardedAction:
        required_phrase = CONFIRMATION_PHRASES[action]
        near_misses = NEAR_MISS_CONFIRMATIONS + (required_phrase.lower(), f"{required_phrase} Please proceed.")

        for confirmation in near_misses:
            decision = evaluate_playwright_guarded_action(action, confirmation)

            assert decision.refused, f"{action.value} accepted non-exact confirmation {confirmation!r}"
            assert decision.outcome == PlaywrightGuardrailOutcome.REFUSE_MISSING_EXACT_CONFIRMATION
            assert decision.exact_confirmation_present is False
            assert decision.may_click_playwright_control is False
            assert decision.required_confirmation == required_phrase


def test_consequential_and_financial_actions_may_proceed_only_with_exact_confirmation() -> None:
    for action in CONSEQUENTIAL_OR_FINANCIAL_ACTIONS:
        decision = evaluate_playwright_guarded_action(action, CONFIRMATION_PHRASES[action])

        assert decision.outcome == PlaywrightGuardrailOutcome.ALLOW_WITH_EXACT_CONFIRMATION
        assert decision.exact_confirmation_present is True
        assert decision.may_click_playwright_control is True
        assert decision.refused is False


def test_mfa_captcha_account_creation_and_password_recovery_still_require_manual_user_control() -> None:
    for action in MANUAL_CONTROL_ACTIONS:
        decision = evaluate_playwright_guarded_action(action, CONFIRMATION_PHRASES[action])

        assert decision.outcome == PlaywrightGuardrailOutcome.REFUSE_MANUAL_CONTROL_REQUIRED
        assert decision.exact_confirmation_present is True
        assert decision.may_click_playwright_control is False
        assert decision.refused is True
