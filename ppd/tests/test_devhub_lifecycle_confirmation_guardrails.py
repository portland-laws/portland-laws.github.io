"""Fixture-only DevHub lifecycle confirmation guardrail tests.

These tests use synthetic action records only. They do not open DevHub, log in,
submit, upload, pay, certify, cancel, schedule inspections, or persist private
session artifacts.
"""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub" / "lifecycle_action_guardrail_cases.json"

OFFICIAL_ACTION_IDS = {
    "official_extension",
    "official_reactivation",
    "official_cancellation",
    "official_refund",
    "official_payment",
    "official_certification",
    "official_upload",
    "official_inspection_scheduling",
}

PREVIEW_MODES_ALLOWED_WITHOUT_CONFIRMATION = {"read_only_preview", "draft_preview"}

PRIVATE_ARTIFACT_MARKERS = (
    "password",
    "token",
    "cookie",
    "storage_state",
    "auth_state",
    "captcha",
    "mfa",
    "trace.zip",
    "/traces/",
    "\\traces\\",
    "/screenshots/",
    "\\screenshots\\",
    "/downloads/",
    "\\downloads\\",
    "ppd/data/private",
    "ppd\\data\\private",
    "payment_card",
    "card_number",
    "routing_number",
    "account_number",
)


class DevHubLifecycleConfirmationGuardrailTests(unittest.TestCase):
    def setUp(self) -> None:
        with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
            self.fixture = json.load(fixture_file)

    def test_mocked_read_only_and_draft_previews_do_not_need_confirmation(self) -> None:
        preview_cases = self.fixture["previewCases"]
        self.assertGreaterEqual(len(preview_cases), 1)

        for case in preview_cases:
            with self.subTest(case=case["caseId"]):
                self.assertFalse(case["officialAction"])
                self.assertIn(case["previewMode"], PREVIEW_MODES_ALLOWED_WITHOUT_CONFIRMATION)
                self.assertNotIn("confirmation", case)
                self.assertEqual(_mock_guarded_decision(case, self.fixture["sessionId"]), "allow_preview")

    def test_all_lifecycle_official_actions_are_denied_without_confirmation(self) -> None:
        denied_cases = self.fixture["noConfirmationDeniedCases"]
        denied_action_ids = {case["actionId"] for case in denied_cases}
        self.assertEqual(denied_action_ids, OFFICIAL_ACTION_IDS)

        for case in denied_cases:
            with self.subTest(case=case["caseId"]):
                self.assertTrue(case["officialAction"])
                self.assertNotIn("confirmation", case)
                self.assertEqual(
                    _mock_guarded_decision(case, self.fixture["sessionId"]),
                    "deny_missing_exact_confirmation",
                )

    def test_official_actions_require_exact_session_specific_confirmation(self) -> None:
        confirmed_cases = self.fixture["confirmedCases"]
        confirmed_action_ids = {case["actionId"] for case in confirmed_cases}
        self.assertEqual(confirmed_action_ids, OFFICIAL_ACTION_IDS)

        for case in confirmed_cases:
            with self.subTest(case=case["caseId"]):
                self.assertEqual(
                    _mock_guarded_decision(case, self.fixture["sessionId"]),
                    "allow_official_mock_action",
                )

                wrong_session = copy.deepcopy(case)
                wrong_session["confirmation"]["sessionId"] = "different-session"
                self.assertEqual(
                    _mock_guarded_decision(wrong_session, self.fixture["sessionId"]),
                    "deny_missing_exact_confirmation",
                )

                wrong_action = copy.deepcopy(case)
                wrong_action["confirmation"]["actionId"] = "official_upload"
                if case["actionId"] == "official_upload":
                    wrong_action["confirmation"]["actionId"] = "official_payment"
                self.assertEqual(
                    _mock_guarded_decision(wrong_action, self.fixture["sessionId"]),
                    "deny_missing_exact_confirmation",
                )

                wrong_phrase = copy.deepcopy(case)
                wrong_phrase["confirmation"]["phrase"] = "CONFIRM"
                self.assertEqual(
                    _mock_guarded_decision(wrong_phrase, self.fixture["sessionId"]),
                    "deny_missing_exact_confirmation",
                )

    def test_fixture_does_not_contain_private_devhub_artifacts(self) -> None:
        for path, value in _walk_strings(self.fixture):
            normalized = value.lower()
            for marker in PRIVATE_ARTIFACT_MARKERS:
                with self.subTest(path=path, marker=marker):
                    self.assertNotIn(marker.lower(), normalized)

    def test_fixture_schema_is_narrow_and_deterministic(self) -> None:
        self.assertEqual(self.fixture["schemaVersion"], 1)
        self.assertEqual(
            set(self.fixture),
            {"schemaVersion", "fixtureId", "sessionId", "notes", "previewCases", "noConfirmationDeniedCases", "confirmedCases"},
        )
        all_case_ids: set[str] = set()
        for group_name in ("previewCases", "noConfirmationDeniedCases", "confirmedCases"):
            for case in self.fixture[group_name]:
                case_id = case["caseId"]
                self.assertNotIn(case_id, all_case_ids)
                all_case_ids.add(case_id)
                self.assertEqual(set(case) - _allowed_case_keys(), set())


def _mock_guarded_decision(case: dict[str, Any], session_id: str) -> str:
    if not case["officialAction"]:
        if case["previewMode"] in PREVIEW_MODES_ALLOWED_WITHOUT_CONFIRMATION:
            return "allow_preview"
        return "deny_unsupported_preview"

    if case["actionId"] not in OFFICIAL_ACTION_IDS:
        return "deny_unknown_official_action"

    if _has_exact_session_confirmation(case, session_id):
        return "allow_official_mock_action"

    return "deny_missing_exact_confirmation"


def _has_exact_session_confirmation(case: dict[str, Any], session_id: str) -> bool:
    confirmation = case.get("confirmation")
    if not isinstance(confirmation, dict):
        return False

    action_id = case["actionId"]
    expected_phrase = f"CONFIRM {session_id} {action_id}"
    return (
        confirmation.get("sessionId") == session_id
        and confirmation.get("actionId") == action_id
        and confirmation.get("phrase") == expected_phrase
    )


def _allowed_case_keys() -> set[str]:
    return {
        "caseId",
        "actionId",
        "lifecycleAction",
        "classification",
        "previewMode",
        "officialAction",
        "confirmation",
        "expectedDecision",
    }


def _walk_strings(value: Any, path: str = "$") -> list[tuple[str, str]]:
    if isinstance(value, str):
        return [(path, value)]
    if isinstance(value, list):
        strings: list[tuple[str, str]] = []
        for index, item in enumerate(value):
            strings.extend(_walk_strings(item, f"{path}[{index}]"))
        return strings
    if isinstance(value, dict):
        strings = []
        for key, item in value.items():
            strings.extend(_walk_strings(item, f"{path}.{key}"))
        return strings
    return []


if __name__ == "__main__":
    unittest.main()
