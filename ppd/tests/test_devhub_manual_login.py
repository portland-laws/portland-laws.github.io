from __future__ import annotations

import json
from pathlib import Path

from ppd.devhub_manual_login import (
    AccessibleSelectorCapture,
    AuthenticatedStateDetector,
    ManualLoginScaffold,
    RedactionPolicy,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "devhub_manual_login"


def load_snapshot() -> dict[str, object]:
    return json.loads((FIXTURE_DIR / "page_snapshot.json").read_text(encoding="utf-8"))


def test_authenticated_state_detects_attended_login_success() -> None:
    state = AuthenticatedStateDetector().detect_from_text("Dashboard My Permits Sign out")

    assert state.authenticated is True
    assert "sign out" in state.evidence


def test_authenticated_state_rejects_login_prompt() -> None:
    state = AuthenticatedStateDetector().detect_from_text("Welcome to DevHub Sign in Create account")

    assert state.authenticated is False
    assert "sign in" in state.evidence


def test_accessible_selector_capture_prefers_role_and_name() -> None:
    selectors = AccessibleSelectorCapture().capture(
        [
            {"role": "button", "name": "Apply for permit"},
            {"role": "presentation", "name": "Ignored"},
            {"role": "button", "name": "Save \"draft\""},
        ]
    )

    assert [candidate.selector for candidate in selectors] == [
        'get_by_role("button", name="Apply for permit")',
        'get_by_role("button", name="Save \\\"draft\\\"")',
    ]


def test_redaction_policy_removes_credentials_sessions_and_emails() -> None:
    redacted = RedactionPolicy().redact_mapping(
        {
            "password": "secret",
            "authorization": "Bearer abc.def",
            "note": "email planner@example.test",
            "nested": {"csrf_token": "raw-token"},
        }
    )

    assert redacted == {
        "password": "[REDACTED]",
        "authorization": "[REDACTED]",
        "note": "email [REDACTED]",
        "nested": {"csrf_token": "[REDACTED]"},
    }


def test_manual_login_scaffold_uses_mocked_fixture_without_persistence() -> None:
    result = ManualLoginScaffold().analyze_snapshot(load_snapshot())

    assert result.authenticated.authenticated is True
    assert result.persisted_state is False
    assert "session_cookie" in result.redacted_metadata
    assert result.redacted_metadata["session_cookie"] == "[REDACTED]"
    assert result.redacted_metadata["nested"] == {
        "csrf_token": "[REDACTED]",
        "note": "contact [REDACTED]",
    }
    assert [candidate.selector for candidate in result.selectors] == [
        'get_by_role("link", name="My Permits")',
        'get_by_role("button", name="Apply for permit")',
        'get_by_role("textbox", name="Search permits")',
        'get_by_role("button", name="Save \\\"draft\\\"")',
    ]
