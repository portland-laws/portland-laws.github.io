from __future__ import annotations

import copy
from pathlib import Path

from ppd.rollback_drill_packet_v6 import (
    load_packet,
    validate_inactive_rollback_drill_packet_v6,
)


FIXTURES = Path(__file__).parent / "fixtures" / "rollback_drill_packet_v6"


def _valid_packet() -> dict:
    return load_packet(FIXTURES / "valid_inactive_packet.json")


def test_valid_inactive_packet_v6_fixture_passes() -> None:
    issues = validate_inactive_rollback_drill_packet_v6(_valid_packet())
    assert issues == []


def test_packet_v6_rejects_each_missing_required_section() -> None:
    required_fields = (
        "smoke_replay_plan_references",
        "rollback_decision_rows",
        "held_source_citation_continuity_checks",
        "affected_agent_capability_notes",
        "safe_downgrade_expectations",
        "manual_reviewer_approval_placeholders",
        "recovery_journal_event_templates",
        "validation_commands",
    )

    for field in required_fields:
        packet = _valid_packet()
        packet.pop(field)
        issues = validate_inactive_rollback_drill_packet_v6(packet)
        assert any(issue.path == field for issue in issues), field


def test_packet_v6_rejects_live_rollback_and_activation_claims() -> None:
    packet = _valid_packet()
    packet["safe_downgrade_expectations"].append("Activation complete after live rollback.")

    messages = [issue.message for issue in validate_inactive_rollback_drill_packet_v6(packet)]

    assert any("live rollback" in message for message in messages)
    assert any("activation" in message for message in messages)


def test_packet_v6_rejects_live_crawl_and_official_completion_claims() -> None:
    packet = _valid_packet()
    packet["smoke_replay_plan_references"].append("Live crawl executed and official action complete.")

    messages = [issue.message for issue in validate_inactive_rollback_drill_packet_v6(packet)]

    assert any("live crawl" in message or "crawl execution" in message for message in messages)
    assert any("official-action" in message for message in messages)


def test_packet_v6_rejects_private_session_auth_artifacts() -> None:
    packet = _valid_packet()
    packet["artifact_manifest"] = {
        "storage_state": "devhub-state.json",
        "note": "session cookie captured",
    }

    messages = [issue.message for issue in validate_inactive_rollback_drill_packet_v6(packet)]

    assert any("private/session/auth artifact keys" in message for message in messages)
    assert any("private session artifacts" in message for message in messages)


def test_packet_v6_rejects_legal_or_permitting_guarantees() -> None:
    packet = _valid_packet()
    packet["manual_reviewer_approval_placeholders"].append("Permit guaranteed after reviewer placeholder signs off.")

    messages = [issue.message for issue in validate_inactive_rollback_drill_packet_v6(packet)]

    assert any("guarantees" in message for message in messages)


def test_packet_v6_rejects_active_mutation_flags() -> None:
    packet = _valid_packet()
    packet["mutation_controls"] = {"active": True, "enabled": True}

    issues = validate_inactive_rollback_drill_packet_v6(packet)

    assert any(issue.path == "$.mutation_controls.active" for issue in issues)
    assert any(issue.path == "$.mutation_controls.enabled" for issue in issues)


def test_packet_v6_rejects_incomplete_decision_rows_and_recovery_templates() -> None:
    packet = _valid_packet()
    packet["rollback_decision_rows"] = [{"condition": "checksum mismatch"}]
    packet["recovery_journal_event_templates"] = [{"event_type": "DevHub attempted action"}]

    issues = validate_inactive_rollback_drill_packet_v6(packet)
    paths = [issue.path for issue in issues]

    assert "rollback_decision_rows[0]" in paths
    assert "recovery_journal_event_templates[0].event_type" in paths
    assert "recovery_journal_event_templates[0].contains_private_artifacts" in paths


def test_validation_commands_must_be_argv_lists() -> None:
    packet = copy.deepcopy(_valid_packet())
    packet["validation_commands"] = ["python3 ppd/daemon/ppd_daemon.py --self-test"]

    issues = validate_inactive_rollback_drill_packet_v6(packet)

    assert any(issue.path == "validation_commands[0]" for issue in issues)
