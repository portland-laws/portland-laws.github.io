from __future__ import annotations

import copy
from pathlib import Path

from ppd.agent_readiness.post_promotion_smoke_replay_v6 import (
    build_post_promotion_smoke_replay_v6_from_fixture,
    validate_post_promotion_smoke_replay_v6,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "post_promotion_smoke_replay_v6"
SOURCE_FIXTURE = FIXTURE_DIR / "source_fixture.json"


def _valid_packet():
    return build_post_promotion_smoke_replay_v6_from_fixture(SOURCE_FIXTURE)


def _problems(packet):
    return "\n".join(validate_post_promotion_smoke_replay_v6(packet).problems)


def _packet_without_source_role(role):
    packet = _valid_packet()
    packet["source_fixture_refs"] = [
        row for row in packet["source_fixture_refs"] if row.get("fixture_role") != role
    ]
    return packet


def test_post_promotion_smoke_replay_v6_rejects_missing_fixture_references():
    promotion_missing = _packet_without_source_role("inactive_guardrail_promotion_rehearsal_v6")
    assert (
        "source_fixture_refs must include an inactive_guardrail_promotion_rehearsal_v6 fixture"
        in _problems(promotion_missing)
    )

    placeholder_missing = _packet_without_source_role("inactive_guardrail_placeholder_fixture")
    assert (
        "source_fixture_refs must include an inactive_guardrail_placeholder_fixture"
        in _problems(placeholder_missing)
    )

    missing_path = _valid_packet()
    missing_path["source_fixture_refs"][0]["path"] = ""
    assert "source_fixture_refs[0].path is required" in _problems(missing_path)


def test_post_promotion_smoke_replay_v6_rejects_missing_required_validation_surfaces():
    required_fields = {
        "inactive_guardrail_placeholder_checks": "inactive_guardrail_placeholder_checks must be a non-empty list",
        "lookup_health_checks": "lookup_health_checks must be a non-empty list",
        "unresolved_hold_display_checks": "unresolved_hold_display_checks must be a non-empty list",
        "stale_source_stop_gates": "stale_source_stop_gates must be a non-empty list",
        "exact_confirmation_checkpoint_checks": "exact_confirmation_checkpoint_checks must be a non-empty list",
        "refused_action_checks": "refused_action_checks must be a non-empty list",
        "reversible_draft_only_routing_checks": "reversible_draft_only_routing_checks must be a non-empty list",
        "local_pdf_preview_routing_checks": "local_pdf_preview_routing_checks must be a non-empty list",
        "rollback_trigger_visibility_checks": "rollback_trigger_visibility_checks must be a non-empty list",
        "manual_handoff_reminders": "manual_handoff_reminders must be a non-empty list",
        "exact_offline_validation_commands": "exact_offline_validation_commands must be a non-empty list",
        "validation_commands": "validation_commands must be a non-empty list",
    }

    for field, expected_problem in required_fields.items():
        packet = _valid_packet()
        packet[field] = []
        assert expected_problem in _problems(packet)


def test_post_promotion_smoke_replay_v6_rejects_missing_expected_smoke_categories():
    packet = _valid_packet()
    packet["smoke_expectations"] = [
        row
        for row in packet["smoke_expectations"]
        if row.get("expectation_id")
        not in {
            "lookup-health-check",
            "unresolved-hold-display-check",
            "stale-source-stop-gate-check",
            "exact-confirmation-checkpoint-check",
            "refused-consequential-action-check",
            "refused-financial-action-check",
            "reversible-draft-only-routing-check",
            "local-pdf-preview-routing-check",
            "rollback-trigger-visibility-check",
            "manual-handoff-reminder-check",
            "exact-offline-validation-command-check",
        }
    ]

    problems = _problems(packet)

    assert "smoke_expectations must be a non-empty list" in problems
    assert "smoke_expectations missing required expectation ids" in problems
    assert "lookup-health-check" in problems
    assert "manual-handoff-reminder-check" in problems


def test_post_promotion_smoke_replay_v6_rejects_unsafe_row_mutations():
    packet = _valid_packet()
    packet["inactive_guardrail_placeholder_checks"][0]["activation_allowed"] = True
    packet["lookup_health_checks"][0]["lookup_status"] = "live_lookup"
    packet["unresolved_hold_display_checks"][0]["blocks_agent_ready"] = False
    packet["stale_source_stop_gates"][0]["source_may_be_used_for_final_answer"] = True
    packet["exact_confirmation_checkpoint_checks"][0]["exact_confirmation_required"] = False
    packet["refused_action_checks"] = [
        row for row in packet["refused_action_checks"] if row.get("action_category") != "financial"
    ]
    packet["refused_action_checks"][0]["official_action_completed"] = True
    packet["reversible_draft_only_routing_checks"][0]["route"] = "official_action"
    packet["local_pdf_preview_routing_checks"][0]["route"] = "official_upload"
    packet["rollback_trigger_visibility_checks"][0]["rollback_trigger_visible"] = False
    packet["manual_handoff_reminders"][0]["handoff_status"] = "dismissed"

    problems = _problems(packet)

    assert "inactive_guardrail_placeholder_checks[0].activation_allowed must be false" in problems
    assert "lookup_health_checks[0].lookup_status must be healthy_fixture_lookup" in problems
    assert "unresolved_hold_display_checks[0].blocks_agent_ready must be true" in problems
    assert "stale_source_stop_gates[0].source_may_be_used_for_final_answer must be false" in problems
    assert "exact_confirmation_checkpoint_checks[0].exact_confirmation_required must be true" in problems
    assert "refused_action_checks must include a financial action refusal" in problems
    assert "refused_action_checks[0].official_action_completed must be false" in problems
    assert "reversible_draft_only_routing_checks[0].route must be reversible_draft_only" in problems
    assert "local_pdf_preview_routing_checks[0].route must be local_pdf_preview_only" in problems
    assert "rollback_trigger_visibility_checks[0].rollback_trigger_visible must be true" in problems
    assert "manual_handoff_reminders[0].handoff_status must be pending_manual_handoff" in problems


def test_post_promotion_smoke_replay_v6_rejects_unsafe_claims_and_artifacts():
    unsafe_cases = [
        ({"active_activation_claimed": True}, "packet.unsafe_probe.active_activation_claimed must not be true"),
        ({"active_mutation": True}, "packet.unsafe_probe.active_mutation must not be true"),
        ({"private_document_value": "owner upload"}, "must not contain private"),
        ({"devhub_session_id": "session-123"}, "must not contain private"),
        ({"auth_state": "stored"}, "must not contain private"),
        ({"trace_file": "trace.zip"}, "must not contain private"),
        ({"operator_note": "guardrails activated for release"}, "prohibited activation"),
        ({"operator_note": "opened DevHub and submitted permit"}, "prohibited activation"),
        ({"operator_note": "official action completed"}, "prohibited activation"),
        ({"operator_note": "permit guaranteed"}, "prohibited activation"),
        ({"operator_note": "legal advice provided"}, "prohibited activation"),
    ]

    for injected, expected_problem in unsafe_cases:
        packet = _valid_packet()
        packet["unsafe_probe"] = copy.deepcopy(injected)
        assert expected_problem in _problems(packet)


def test_post_promotion_smoke_replay_v6_rejects_non_exact_validation_commands():
    packet = _valid_packet()
    packet["exact_offline_validation_commands"] = [["python3", "-m", "pytest"]]
    packet["validation_commands"] = [["python3", "-m", "pytest"]]

    problems = _problems(packet)

    assert "exact_offline_validation_commands must exactly match post-promotion smoke replay v6 commands" in problems
    assert "validation_commands must contain only the PP&D daemon self-test command" in problems
