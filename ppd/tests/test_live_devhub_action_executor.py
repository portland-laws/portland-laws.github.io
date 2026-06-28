from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ppd.devhub.live_action_executor import (
    LiveDevHubActionKind,
    LiveDevHubActionRequest,
    build_required_confirmation_phrase,
    evaluate_live_devhub_action,
    execute_live_devhub_action,
)


class FakePage:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, object]] = []

    def fill(self, selector: str, value: str) -> None:
        self.calls.append(("fill", selector, value))

    def click(self, selector: str) -> None:
        self.calls.append(("click", selector, None))

    def set_input_files(self, selector: str, files: str | list[str]) -> None:
        self.calls.append(("set_input_files", selector, files))


class LiveDevHubActionExecutorTest(unittest.TestCase):
    def test_draft_fill_executes_only_in_user_authorized_live_context(self) -> None:
        page = FakePage()
        request = LiveDevHubActionRequest(
            action_kind=LiveDevHubActionKind.FILL_FIELD,
            target_description="building permit draft",
            selector='input[name="projectAddress"]',
            redacted_value="[REDACTED ADDRESS]",
            user_authorized_browser=True,
            allow_live_execution=True,
        )

        result = execute_live_devhub_action(request, page=page)

        self.assertTrue(result.allowed)
        self.assertTrue(result.executed)
        self.assertEqual([("fill", 'input[name="projectAddress"]', "[REDACTED ADDRESS]")], page.calls)

    def test_official_submit_requires_exact_action_confirmation(self) -> None:
        request = LiveDevHubActionRequest(
            action_kind=LiveDevHubActionKind.SUBMIT_APPLICATION,
            target_description="building permit draft 123",
            selector='button:has-text("Submit")',
            user_authorized_browser=True,
            allow_live_execution=True,
            allow_official_execution=True,
        )
        phrase = build_required_confirmation_phrase(request)

        refused = evaluate_live_devhub_action(request)
        confirmed = evaluate_live_devhub_action(
            LiveDevHubActionRequest(
                action_kind=request.action_kind,
                target_description=request.target_description,
                selector=request.selector,
                user_authorized_browser=True,
                allow_live_execution=True,
                allow_official_execution=True,
                provided_confirmation_phrase=phrase,
            )
        )

        self.assertFalse(refused.allowed)
        self.assertTrue(refused.requires_exact_confirmation)
        self.assertEqual(phrase, refused.required_confirmation_phrase)
        self.assertTrue(confirmed.allowed)
        self.assertEqual("allowed", confirmed.status)

    def test_exact_confirmed_upload_sets_user_selected_file(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".pdf") as handle:
            upload_request = LiveDevHubActionRequest(
                action_kind=LiveDevHubActionKind.OFFICIAL_UPLOAD,
                target_description="correction document upload",
                selector='input[type="file"]',
                local_file_path=handle.name,
                user_authorized_browser=True,
                allow_live_execution=True,
                allow_official_execution=True,
            )
            phrase = build_required_confirmation_phrase(upload_request)
            page = FakePage()
            result = execute_live_devhub_action(
                LiveDevHubActionRequest(
                    action_kind=upload_request.action_kind,
                    target_description=upload_request.target_description,
                    selector=upload_request.selector,
                    local_file_path=upload_request.local_file_path,
                    user_authorized_browser=True,
                    allow_live_execution=True,
                    allow_official_execution=True,
                    provided_confirmation_phrase=phrase,
                ),
                page=page,
            )

        self.assertTrue(result.executed)
        self.assertEqual("set_input_files", page.calls[0][0])

    def test_payment_and_security_sensitive_actions_are_not_automated(self) -> None:
        for action in (
            LiveDevHubActionKind.PAY_FEE,
            LiveDevHubActionKind.ENTER_PAYMENT_DETAILS,
            LiveDevHubActionKind.MFA,
            LiveDevHubActionKind.CAPTCHA,
            LiveDevHubActionKind.ACCOUNT_CREATION,
        ):
            with self.subTest(action=action.value):
                request = LiveDevHubActionRequest(
                    action_kind=action,
                    target_description="DevHub checkpoint",
                    user_authorized_browser=True,
                    allow_live_execution=True,
                    allow_official_execution=True,
                    provided_confirmation_phrase="anything",
                )
                result = execute_live_devhub_action(request, page=FakePage())
                self.assertFalse(result.allowed)
                self.assertFalse(result.executed)
                self.assertTrue(result.requires_manual_handoff)


if __name__ == "__main__":
    unittest.main()
