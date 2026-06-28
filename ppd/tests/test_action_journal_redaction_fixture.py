from __future__ import annotations

import json
from pathlib import Path

from ppd.devhub.action_journal_redaction import (
    ALLOWED_EVENT_TYPES,
    validate_action_journal_event,
    validate_redaction_fixture,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "action_journal" / "redaction_fixture.json"


def _load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_action_journal_redaction_fixture_contract() -> None:
    fixture = _load_fixture()

    validate_redaction_fixture(fixture)


def test_commit_safe_fixture_covers_required_event_types() -> None:
    fixture = _load_fixture()
    event_types = {event["event_type"] for event in fixture["commit_safe_events"]}

    assert event_types == ALLOWED_EVENT_TYPES


def test_rejected_fixture_events_are_not_commit_safe() -> None:
    fixture = _load_fixture()

    for rejected in fixture["rejected_events"]:
        issues = validate_action_journal_event(rejected["event"])
        assert issues, rejected["expected_rejection"]
