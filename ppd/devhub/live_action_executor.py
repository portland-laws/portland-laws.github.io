"""Guarded live DevHub action execution boundary.

The executor in this module is intentionally small and explicit. It supports
draft field fills and exact-confirmed official-action checkpoints against an
injected Playwright-like page object, while refusing MFA, CAPTCHA, account
creation, password recovery, and payment-detail entry. It never stores browser
state or credentials.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Protocol


class LiveDevHubActionKind(str, Enum):
    USER_LOGIN_HANDOFF = "user_login_handoff"
    READ_FORM_STATE = "read_form_state"
    FILL_FIELD = "fill_field"
    SAVE_DRAFT = "save_draft"
    OFFICIAL_UPLOAD = "official_upload"
    SUBMIT_APPLICATION = "submit_application"
    CERTIFY_STATEMENT = "certify_statement"
    CANCEL_REQUEST = "cancel_request"
    SCHEDULE_INSPECTION = "schedule_inspection"
    OPEN_PAYMENT_REVIEW = "open_payment_review"
    PAY_FEE = "pay_fee"
    ENTER_PAYMENT_DETAILS = "enter_payment_details"
    MFA = "mfa"
    CAPTCHA = "captcha"
    ACCOUNT_CREATION = "account_creation"
    PASSWORD_RECOVERY = "password_recovery"


READ_OR_DRAFT_ACTIONS = frozenset(
    {
        LiveDevHubActionKind.USER_LOGIN_HANDOFF,
        LiveDevHubActionKind.READ_FORM_STATE,
        LiveDevHubActionKind.FILL_FIELD,
        LiveDevHubActionKind.SAVE_DRAFT,
    }
)

OFFICIAL_ACTIONS = frozenset(
    {
        LiveDevHubActionKind.OFFICIAL_UPLOAD,
        LiveDevHubActionKind.SUBMIT_APPLICATION,
        LiveDevHubActionKind.CERTIFY_STATEMENT,
        LiveDevHubActionKind.CANCEL_REQUEST,
        LiveDevHubActionKind.SCHEDULE_INSPECTION,
        LiveDevHubActionKind.OPEN_PAYMENT_REVIEW,
    }
)

ALWAYS_REFUSED_ACTIONS = frozenset(
    {
        LiveDevHubActionKind.PAY_FEE,
        LiveDevHubActionKind.ENTER_PAYMENT_DETAILS,
        LiveDevHubActionKind.MFA,
        LiveDevHubActionKind.CAPTCHA,
        LiveDevHubActionKind.ACCOUNT_CREATION,
        LiveDevHubActionKind.PASSWORD_RECOVERY,
    }
)


class PlaywrightLikePage(Protocol):
    def fill(self, selector: str, value: str) -> Any:
        ...

    def click(self, selector: str) -> Any:
        ...

    def set_input_files(self, selector: str, files: str | list[str]) -> Any:
        ...


@dataclass(frozen=True)
class LiveDevHubActionRequest:
    action_kind: LiveDevHubActionKind
    target_description: str
    selector: str = ""
    redacted_value: str = ""
    local_file_path: str = ""
    allow_live_execution: bool = False
    allow_official_execution: bool = False
    user_authorized_browser: bool = False
    expected_confirmation_phrase: str = ""
    provided_confirmation_phrase: str = ""


@dataclass(frozen=True)
class LiveDevHubActionResult:
    action_kind: LiveDevHubActionKind
    status: str
    allowed: bool
    executed: bool
    reason: str
    requires_exact_confirmation: bool
    required_confirmation_phrase: str = ""
    requires_manual_handoff: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "actionKind": self.action_kind.value,
            "status": self.status,
            "allowed": self.allowed,
            "executed": self.executed,
            "reason": self.reason,
            "requiresExactConfirmation": self.requires_exact_confirmation,
            "requiredConfirmationPhrase": self.required_confirmation_phrase,
            "requiresManualHandoff": self.requires_manual_handoff,
        }


def build_required_confirmation_phrase(request: LiveDevHubActionRequest) -> str:
    if request.expected_confirmation_phrase.strip():
        return request.expected_confirmation_phrase.strip()
    target = " ".join(request.target_description.split())
    return f"I authorize DevHub action {request.action_kind.value} for {target}."


def evaluate_live_devhub_action(request: LiveDevHubActionRequest) -> LiveDevHubActionResult:
    """Return the fail-closed decision for a proposed live DevHub action."""

    if request.action_kind in ALWAYS_REFUSED_ACTIONS:
        return LiveDevHubActionResult(
            action_kind=request.action_kind,
            status="refused",
            allowed=False,
            executed=False,
            reason=_always_refused_reason(request.action_kind),
            requires_exact_confirmation=request.action_kind not in {LiveDevHubActionKind.MFA, LiveDevHubActionKind.CAPTCHA},
            required_confirmation_phrase=build_required_confirmation_phrase(request),
            requires_manual_handoff=True,
        )

    if not request.user_authorized_browser:
        return LiveDevHubActionResult(
            action_kind=request.action_kind,
            status="refused",
            allowed=False,
            executed=False,
            reason="a user-authorized live browser handoff is required",
            requires_exact_confirmation=request.action_kind in OFFICIAL_ACTIONS,
            required_confirmation_phrase=build_required_confirmation_phrase(request) if request.action_kind in OFFICIAL_ACTIONS else "",
            requires_manual_handoff=True,
        )

    if not request.allow_live_execution:
        return LiveDevHubActionResult(
            action_kind=request.action_kind,
            status="ready_but_not_executed",
            allowed=True,
            executed=False,
            reason="live execution flag is disabled",
            requires_exact_confirmation=request.action_kind in OFFICIAL_ACTIONS,
            required_confirmation_phrase=build_required_confirmation_phrase(request) if request.action_kind in OFFICIAL_ACTIONS else "",
            requires_manual_handoff=False,
        )

    if request.action_kind in READ_OR_DRAFT_ACTIONS:
        if request.action_kind == LiveDevHubActionKind.FILL_FIELD and (not request.selector or request.redacted_value == ""):
            return LiveDevHubActionResult(
                action_kind=request.action_kind,
                status="refused",
                allowed=False,
                executed=False,
                reason="draft field fill requires selector and value",
                requires_exact_confirmation=False,
            )
        return LiveDevHubActionResult(
            action_kind=request.action_kind,
            status="allowed",
            allowed=True,
            executed=False,
            reason="reversible draft or read-only action is allowed in the user-authorized browser",
            requires_exact_confirmation=False,
        )

    if request.action_kind in OFFICIAL_ACTIONS:
        required_phrase = build_required_confirmation_phrase(request)
        exact = request.provided_confirmation_phrase.strip() == required_phrase
        if not request.allow_official_execution or not exact:
            return LiveDevHubActionResult(
                action_kind=request.action_kind,
                status="refused",
                allowed=False,
                executed=False,
                reason="official DevHub actions require allow_official_execution and exact action confirmation",
                requires_exact_confirmation=True,
                required_confirmation_phrase=required_phrase,
                requires_manual_handoff=True,
            )
        if request.action_kind == LiveDevHubActionKind.OFFICIAL_UPLOAD and not _is_existing_local_file(request.local_file_path):
            return LiveDevHubActionResult(
                action_kind=request.action_kind,
                status="refused",
                allowed=False,
                executed=False,
                reason="official upload requires an existing local file selected by the user",
                requires_exact_confirmation=True,
                required_confirmation_phrase=required_phrase,
                requires_manual_handoff=True,
            )
        if not request.selector:
            return LiveDevHubActionResult(
                action_kind=request.action_kind,
                status="refused",
                allowed=False,
                executed=False,
                reason="official action requires an explicit selector",
                requires_exact_confirmation=True,
                required_confirmation_phrase=required_phrase,
                requires_manual_handoff=True,
            )
        return LiveDevHubActionResult(
            action_kind=request.action_kind,
            status="allowed",
            allowed=True,
            executed=False,
            reason="exact confirmation satisfied for the specific official action",
            requires_exact_confirmation=True,
            required_confirmation_phrase=required_phrase,
        )

    return LiveDevHubActionResult(
        action_kind=request.action_kind,
        status="refused",
        allowed=False,
        executed=False,
        reason="unknown live DevHub action",
        requires_exact_confirmation=True,
        required_confirmation_phrase=build_required_confirmation_phrase(request),
    )


def execute_live_devhub_action(
    request: LiveDevHubActionRequest,
    *,
    page: Optional[PlaywrightLikePage] = None,
) -> LiveDevHubActionResult:
    """Execute a gated action against an injected Playwright-like page object."""

    decision = evaluate_live_devhub_action(request)
    if not decision.allowed or decision.status != "allowed":
        return decision
    if page is None:
        return LiveDevHubActionResult(
            action_kind=request.action_kind,
            status="ready_for_execution",
            allowed=True,
            executed=False,
            reason="no page object was supplied",
            requires_exact_confirmation=decision.requires_exact_confirmation,
            required_confirmation_phrase=decision.required_confirmation_phrase,
        )

    if request.action_kind == LiveDevHubActionKind.FILL_FIELD:
        page.fill(request.selector, request.redacted_value)
    elif request.action_kind == LiveDevHubActionKind.OFFICIAL_UPLOAD:
        page.set_input_files(request.selector, request.local_file_path)
    elif request.action_kind in {
        LiveDevHubActionKind.SAVE_DRAFT,
        LiveDevHubActionKind.SUBMIT_APPLICATION,
        LiveDevHubActionKind.CERTIFY_STATEMENT,
        LiveDevHubActionKind.CANCEL_REQUEST,
        LiveDevHubActionKind.SCHEDULE_INSPECTION,
        LiveDevHubActionKind.OPEN_PAYMENT_REVIEW,
    }:
        page.click(request.selector)
    else:
        return LiveDevHubActionResult(
            action_kind=request.action_kind,
            status="refused",
            allowed=False,
            executed=False,
            reason="action has no executor mapping",
            requires_exact_confirmation=decision.requires_exact_confirmation,
            required_confirmation_phrase=decision.required_confirmation_phrase,
        )

    return LiveDevHubActionResult(
        action_kind=request.action_kind,
        status="executed",
        allowed=True,
        executed=True,
        reason=decision.reason,
        requires_exact_confirmation=decision.requires_exact_confirmation,
        required_confirmation_phrase=decision.required_confirmation_phrase,
    )


def _is_existing_local_file(value: str) -> bool:
    try:
        path = Path(value)
    except TypeError:
        return False
    return path.is_file()


def _always_refused_reason(action_kind: LiveDevHubActionKind) -> str:
    if action_kind == LiveDevHubActionKind.PAY_FEE:
        return "final payment execution remains a manual payment-processor handoff"
    if action_kind == LiveDevHubActionKind.ENTER_PAYMENT_DETAILS:
        return "payment-detail entry must remain manual and must not be stored by the agent"
    if action_kind in {LiveDevHubActionKind.MFA, LiveDevHubActionKind.CAPTCHA}:
        return "security challenges must not be automated"
    return "account setup or recovery must remain a user-controlled handoff"
