from __future__ import annotations

from pathlib import Path

from ppd.drills.inactive_rollback_packet_v6 import build_packet_from_fixture


def test_inactive_rollback_packet_v6_uses_only_fixture_inputs() -> None:
    fixture = Path(__file__).parent / "fixtures" / "inactive_guardrail_smoke_replay_plan_v6.json"

    packet = build_packet_from_fixture(fixture)

    assert packet["packet_version"] == "inactive-rollback-drill-packet-v6"
    assert packet["mode"] == "inactive_fixture_packet_only"
    assert packet["live_guardrails_activated"] is False
    assert packet["live_guardrails_rolled_back"] is False
    assert packet["devhub_opened"] is False
    assert packet["live_sites_crawled"] is False
    assert packet["private_documents_read"] is False
    assert packet["rollback_decision_rows"] == [
        {
            "row_id": "rollback-decision-v6-01",
            "source_replay_id": "inactive-smoke-replay-v6-001",
            "guardrail": "held_source_citation_required",
            "observed_fixture_result": "fixture_blocked_uncited_downgrade",
            "rollback_decision": "hold_inactive_no_live_rollback",
            "reason": "rollback remains inactive because citation continuity held in fixture replay",
            "required_manual_reviewer": "manual_reviewer_placeholder",
            "approval_status": "not_requested_fixture_only",
        },
        {
            "row_id": "rollback-decision-v6-02",
            "source_replay_id": "inactive-smoke-replay-v6-002",
            "guardrail": "manual_reviewer_required_before_recovery",
            "observed_fixture_result": "fixture_requires_manual_placeholder",
            "rollback_decision": "hold_inactive_no_live_rollback",
            "reason": "rollback remains inactive pending manual reviewer placeholder completion",
            "required_manual_reviewer": "manual_reviewer_placeholder",
            "approval_status": "not_requested_fixture_only",
        },
    ]


def test_inactive_rollback_packet_v6_contains_required_drill_sections() -> None:
    fixture = Path(__file__).parent / "fixtures" / "inactive_guardrail_smoke_replay_plan_v6.json"

    packet = build_packet_from_fixture(fixture)

    assert packet["held_source_citation_continuity_checks"][0]["continuity_check"] == "citation_retained_from_fixture"
    assert packet["held_source_citation_continuity_checks"][0]["private_document_accessed"] is False
    assert packet["affected_agent_capability_notes"][0]["live_guardrail_changed"] is False
    assert packet["safe_downgrade_expectations"][0]["expected_result"] == "no live capability activation and no live rollback"
    assert packet["manual_reviewer_approval_placeholders"][0]["decision"] == ""
    assert [event["event_name"] for event in packet["recovery_journal_event_templates"]] == [
        "rollback_drill_packet_opened",
        "manual_review_placeholder_recorded",
        "inactive_recovery_drill_closed",
    ]
    assert packet["offline_validation_commands"] == [
        ["python3", "-m", "py_compile", "ppd/drills/inactive_rollback_packet_v6.py"],
        ["python3", "-m", "pytest", "ppd/tests/test_inactive_rollback_packet_v6.py"],
    ]
