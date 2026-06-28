from pathlib import Path

import pytest

from ppd.logic.agent_readiness_replay_v7 import (
    ReplayFixtureError,
    load_replay_fixtures,
    replay_agent_readiness_v7,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "agent_readiness_replay_v7"
FIXTURE_PATHS = [
    FIXTURE_DIR / "guardrail_recompile_reviewer_packet_v7.json",
    FIXTURE_DIR / "inactive_guardrail_staging_v7.json",
]

REQUIRED_SCENARIOS = {
    "missing_information",
    "stale_evidence_stop",
    "reversible_draft",
    "local_pdf_preview",
    "exact_confirmation_checkpoint",
    "refused_consequential_action",
    "refused_financial_action",
    "rollback_visibility",
    "source_citation_explanation",
    "manual_handoff",
}

PROHIBITED_COMMAND_TOKENS = {
    "curl",
    "wget",
    "playwright",
    "npm",
    "pnpm",
    "devhub",
    "upload",
    "submit",
    "pay",
    "schedule",
}


def test_agent_readiness_replay_v7_covers_required_agent_responses_offline_only():
    fixtures = load_replay_fixtures(FIXTURE_PATHS)

    report = replay_agent_readiness_v7(fixtures)

    assert report.replay_id == "post-recompile-agent-readiness-replay-v7"
    assert report.offline_only is True
    assert report.guardrails_activated is False
    assert {case.scenario for case in report.cases} == REQUIRED_SCENARIOS
    assert len(report.cases) == len(REQUIRED_SCENARIOS)


def test_agent_readiness_replay_v7_uses_only_exact_offline_validation_commands():
    fixtures = load_replay_fixtures(FIXTURE_PATHS)

    report = replay_agent_readiness_v7(fixtures)

    for case in report.cases:
        assert case.validation_command
        assert all(isinstance(part, str) and part for part in case.validation_command)
        lowered = {part.lower() for part in case.validation_command}
        assert lowered.isdisjoint(PROHIBITED_COMMAND_TOKENS)
        assert case.validation_command[0] == "python3"


def test_agent_readiness_replay_v7_keeps_citations_and_refusals_visible():
    fixtures = load_replay_fixtures(FIXTURE_PATHS)

    report = replay_agent_readiness_v7(fixtures)
    cases = {case.scenario: case for case in report.cases}

    assert cases["refused_consequential_action"].status == "refused"
    assert cases["refused_financial_action"].status == "refused"
    assert cases["manual_handoff"].status == "handoff_required"
    assert cases["rollback_visibility"].status == "rollback_visible"
    assert cases["source_citation_explanation"].citations
    assert all(case.citations for case in report.cases)


def test_agent_readiness_replay_v7_rejects_live_or_active_fixture_kinds():
    fixtures = load_replay_fixtures(FIXTURE_PATHS)
    mutated = dict(fixtures[0])
    mutated["fixture_kind"] = "live_devhub_capture"

    with pytest.raises(ReplayFixtureError):
        replay_agent_readiness_v7([mutated, fixtures[1]])


def test_agent_readiness_replay_v7_rejects_active_guardrails():
    fixtures = load_replay_fixtures(FIXTURE_PATHS)
    mutated = dict(fixtures[1])
    mutated["guardrails_active"] = True

    with pytest.raises(ReplayFixtureError):
        replay_agent_readiness_v7([fixtures[0], mutated])
