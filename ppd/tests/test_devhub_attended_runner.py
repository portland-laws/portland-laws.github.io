from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from ppd.devhub.attended_runner import (
    AttendedDevHubRunner,
    DevHubSafetyError,
    JournalEvent,
    dump_jsonl_journal,
    load_jsonl_journal,
)


def test_manual_login_handoff_must_be_confirmed() -> None:
    runner = AttendedDevHubRunner()

    with pytest.raises(DevHubSafetyError):
        runner.require_manual_login_handoff(confirmed=False)

    event = runner.require_manual_login_handoff(confirmed=True)
    assert event.action == "manual_login_handoff"


def test_guarded_transition_requires_pause_token() -> None:
    runner = AttendedDevHubRunner()

    with pytest.raises(DevHubSafetyError):
        runner.require_pause("submit", pause_token=None)

    event = runner.require_pause("submit", pause_token="attended-review-1")
    assert event.transition == "submit"
    assert event.pause_token == "attended-review-1"


def test_redacted_facts_produce_reversible_draft_events() -> None:
    runner = AttendedDevHubRunner()
    fills = runner.plan_draft_fills(
        {"project_name": "REDACTED_PROJECT", "site_address": "REDACTED_ADDRESS"},
        {"site_address": "#address", "project_name": "#project"},
    )

    events = runner.reversible_events_for_fills(fills)

    assert [event.selector for event in events] == ["#project", "#address", "#address", "#project"]
    assert [event.value for event in events] == ["REDACTED_PROJECT", "REDACTED_ADDRESS", "", ""]
    assert events[0].note == "redacted_fact:project_name"
    assert events[-1].note == "undo_redacted_fact:project_name"


def test_jsonl_journal_round_trip_uses_local_fixture_style(tmp_path: Path) -> None:
    fixture_dir = Path(__file__).parent / "fixtures" / "devhub"
    assert fixture_dir.parts[-2:] == ("fixtures", "devhub")

    path = tmp_path / "journal.jsonl"
    source = [JournalEvent(action="fill", selector="#x", value="REDACTED")]

    dump_jsonl_journal(source, path)
    loaded = load_jsonl_journal(path)

    assert loaded == source


def test_replay_blocks_guarded_action_without_pause_token() -> None:
    runner = AttendedDevHubRunner(dry_run=True)

    with pytest.raises(DevHubSafetyError):
        asyncio.run(runner.replay([{"action": "payment"}]))


def test_replay_allows_guarded_action_with_pause_token_in_dry_run() -> None:
    runner = AttendedDevHubRunner(dry_run=True)

    applied = asyncio.run(runner.replay([{"action": "upload", "pause_token": "human-ok"}]))

    assert applied == [JournalEvent(action="upload", pause_token="human-ok")]
    assert runner.events[0].action == "pause"
    assert runner.events[0].transition == "upload"
