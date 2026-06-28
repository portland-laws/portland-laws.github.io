from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ppd.devhub.attended_worker_journal import (
    JournalValidationError,
    validate_attended_worker_journal_sequence,
)


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "devhub_attended_worker_journal_sequence.json"
)


def _load_fixture_events() -> list[dict[str, object]]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))["events"]


def test_fixture_requires_full_attended_completion_sequence() -> None:
    events = _load_fixture_events()

    validate_attended_worker_journal_sequence(events)

    completed = [event for event in events if event["event_type"] == "devhub_action_mark_complete"]
    assert completed == [
        {
            "event_id": "evt-006",
            "event_type": "devhub_action_mark_complete",
            "action_id": "read-fee-notice",
            "occurred_at": "2026-05-15T00:05:00Z",
            "actor": "attended_worker",
            "completion_evidence": "user_visible_post_action_review",
        }
    ]


def test_completion_fails_without_exact_confirmation_checkpoint() -> None:
    events = [
        event
        for event in _load_fixture_events()
        if not (
            event.get("action_id") == "read-fee-notice"
            and event.get("event_type") == "exact_confirmation_checkpoint"
        )
    ]

    with pytest.raises(JournalValidationError, match="exact-confirmation|exact_confirmation"):
        validate_attended_worker_journal_sequence(events)


def test_final_official_action_cannot_be_marked_complete() -> None:
    events = copy.deepcopy(_load_fixture_events())
    events.extend(
        [
            {
                "event_id": "evt-010",
                "event_type": "devhub_action_preview",
                "action_id": "submit-permit-request",
                "occurred_at": "2026-05-15T00:09:00Z",
                "actor": "attended_worker",
                "preview": {
                    "user_visible_summary": "Submission remains a manual handoff.",
                    "will_click_final_official_control": False,
                },
            },
            {
                "event_id": "evt-011",
                "event_type": "exact_confirmation_checkpoint",
                "action_id": "submit-permit-request",
                "occurred_at": "2026-05-15T00:10:00Z",
                "actor": "user",
                "confirmation": {
                    "required_phrase": "Manual handoff only; do not submit.",
                    "received_phrase": "Manual handoff only; do not submit.",
                    "matched_exactly": True,
                },
            },
            {
                "event_id": "evt-012",
                "event_type": "post_action_review_evidence",
                "action_id": "submit-permit-request",
                "occurred_at": "2026-05-15T00:11:00Z",
                "actor": "attended_worker",
                "evidence": {
                    "review_result": "manual_handoff_only",
                    "user_visible_outcome": "No final submission made.",
                },
            },
            {
                "event_id": "evt-013",
                "event_type": "devhub_action_mark_complete",
                "action_id": "submit-permit-request",
                "occurred_at": "2026-05-15T00:12:00Z",
                "actor": "attended_worker",
                "completion_evidence": "user_visible_post_action_review",
            },
        ]
    )

    with pytest.raises(JournalValidationError, match="manual handoff"):
        validate_attended_worker_journal_sequence(events)


def test_fixture_does_not_commit_private_devhub_artifacts() -> None:
    fixture_text = FIXTURE_PATH.read_text(encoding="utf-8")

    forbidden_terms = [
        "auth_state",
        "cookie",
        "credentials",
        "har_path",
        "mfa_code",
        "password",
        "payment_details",
        "screenshot_path",
        "session_file",
        "trace_path",
    ]
    for term in forbidden_terms:
        assert term not in fixture_text
