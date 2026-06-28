from __future__ import annotations

import json
from pathlib import Path
from typing import Any


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "daemon"
    / "blocked_task_prompt_budget_repeated_llm_router_exit.json"
)


def _load_fixture() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_repeated_llm_router_exits_are_summarized_for_daemon_repair() -> None:
    fixture = _load_fixture()

    assert fixture["scenario"] == "blocked_task_prompt_budget_after_repeated_llm_router_exit"
    assert fixture["blocked_task"]["checkbox_id"] == "checkbox-63"

    exits = fixture["llm_router_exits"]
    assert len(exits) == 2
    assert {exit_record["exit_kind"] for exit_record in exits} == {
        "prompt_budget_exceeded"
    }
    assert all(exit_record["should_retry_domain_work"] is False for exit_record in exits)

    daemon_prompt = fixture["daemon_prompt"]
    assert "checkbox-63" in daemon_prompt["target_summary"]
    assert "blocked-task prompt-budget" in daemon_prompt["target_summary"]

    compact_errors = daemon_prompt["compact_errors"]
    assert len(compact_errors) == 2
    prompt_budget_error = compact_errors[0]
    assert prompt_budget_error["exit_kind"] == "prompt_budget_exceeded"
    assert prompt_budget_error["count"] == 2
    assert "fixture and test repair" in prompt_budget_error["summary"]

    repair_hint = daemon_prompt["next_daemon_repair_hint"]
    assert "syntax-valid" in repair_hint
    assert "fixture/test replacement" in repair_hint
    assert "retry_blocked_domain_work is false" in repair_hint


def test_blocked_domain_work_is_not_retried_after_prompt_budget_exits() -> None:
    fixture = _load_fixture()

    daemon_prompt = fixture["daemon_prompt"]
    domain_work_retry = fixture["domain_work_retry"]

    assert daemon_prompt["retry_blocked_domain_work"] is False
    assert domain_work_retry["attempted"] is False
    assert domain_work_retry["blocked_reason"] == "prompt_budget_exceeded"
    assert domain_work_retry["attempts_after_block"] == []


def test_prompt_budget_fixture_is_compact_and_redacted() -> None:
    raw_fixture = FIXTURE_PATH.read_text(encoding="utf-8")
    fixture = _load_fixture()

    assert len(raw_fixture) < 5000
    assert len(fixture["daemon_prompt"]["compact_errors"]) <= 3

    lowered = raw_fixture.lower()
    forbidden_fragments = (
        "authorization:",
        "cookie:",
        "password",
        "auth_state",
        "trace.zip",
        ".har",
        "screenshot",
    )
    for fragment in forbidden_fragments:
        assert fragment not in lowered
