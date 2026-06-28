from __future__ import annotations

import copy
from pathlib import Path

from ppd.logic.guardrail_recompile_staging_packet_v6 import (
    OFFLINE_VALIDATION_COMMANDS,
    PACKET_VERSION,
    build_guardrail_recompile_staging_packet_v6,
    validate_guardrail_recompile_staging_packet_v6,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "process_model_refresh_impact_queue_v6" / "sample_queue.json"


def test_builds_inactive_packet_from_process_model_refresh_impact_queue_fixture() -> None:
    packet = build_guardrail_recompile_staging_packet_v6(FIXTURE_PATH)

    assert packet["packet_version"] == PACKET_VERSION
    assert packet["source_queue_version"] == "process_model_refresh_impact_queue_v6"
    assert packet["activation_status"] == "inactive"
    assert packet["side_effect_policy"] == "offline_fixture_only"
    assert len(packet["process_impact_references"]) == 2
    assert len(packet["inactive_guardrail_bundle_candidates"]) == 2
    assert all(candidate["activation_status"] == "inactive" for candidate in packet["inactive_guardrail_bundle_candidates"])
    result = validate_guardrail_recompile_staging_packet_v6(packet)
    assert result.valid, result.problems


def test_preserves_exact_confirmations_and_refused_actions_as_placeholders() -> None:
    packet = build_guardrail_recompile_staging_packet_v6(FIXTURE_PATH)
    checks = packet["exact_confirmation_and_refused_action_preservation_checks"]

    exact_checks = [check for check in checks if check["check_type"] == "exact_confirmation_preservation"]
    refused_checks = [check for check in checks if check["check_type"] == "refused_action_preservation"]

    assert exact_checks
    assert refused_checks
    assert any("action-submit-permit-request" in check["preserved_action_ids"] for check in exact_checks)
    assert any("action-final-submit-payment" in check["preserved_action_ids"] for check in refused_checks)
    assert all(check["status"] == "placeholder_pending_review" for check in checks)


def test_stale_evidence_creates_stop_gate_and_blocks_candidate_activation() -> None:
    packet = build_guardrail_recompile_staging_packet_v6(FIXTURE_PATH)

    stop_gates = packet["stale_evidence_stop_gates"]
    assert stop_gates == [
        {
            "refresh_impact_id": "impact-trade-payment-002",
            "process_id": "standard-trade-permit",
            "gate": "stop_on_stale_evidence",
            "stale_evidence_ids": ["evidence-fee-payment-guide"],
            "blocks_activation": True,
            "resolution_placeholder": "reviewer_must_refresh_or_retire_evidence_before_activation",
        }
    ]

    blocked = [
        candidate
        for candidate in packet["inactive_guardrail_bundle_candidates"]
        if candidate["refresh_impact_id"] == "impact-trade-payment-002"
    ][0]
    assert blocked["candidate_status"] == "blocked_stale_evidence"


def test_includes_rollback_reviewers_and_exact_offline_validation_commands() -> None:
    packet = build_guardrail_recompile_staging_packet_v6(FIXTURE_PATH)

    assert packet["rollback_comparison_rows"] == [
        {
            "refresh_impact_id": "impact-building-intake-001",
            "process_id": "building-permit-intake",
            "baseline_guardrail_bundle_id": "guardrail-building-intake-current-v5",
            "candidate_guardrail_bundle_id": "guardrail-building-intake-candidate-v6",
            "comparison_status": "placeholder_pending_offline_diff",
            "rollback_available": True,
        },
        {
            "refresh_impact_id": "impact-trade-payment-002",
            "process_id": "standard-trade-permit",
            "baseline_guardrail_bundle_id": "guardrail-trade-current-v5",
            "candidate_guardrail_bundle_id": "guardrail-trade-candidate-v6",
            "comparison_status": "placeholder_pending_offline_diff",
            "rollback_available": True,
        },
    ]
    assert any(
        placeholder["reviewer_role"] == "fee_workflow_reviewer" and placeholder["signoff_status"] == "not_signed"
        for placeholder in packet["reviewer_signoff_placeholders"]
    )
    assert packet["offline_validation_commands"] == [list(command) for command in OFFLINE_VALIDATION_COMMANDS]


def test_validator_rejects_missing_required_staging_sections() -> None:
    packet = build_guardrail_recompile_staging_packet_v6(FIXTURE_PATH)
    required_sections = (
        "process_impact_references",
        "inactive_guardrail_bundle_candidates",
        "source_evidence_carry_forward_rows",
        "deterministic_predicate_refresh_placeholders",
        "exact_confirmation_and_refused_action_preservation_checks",
        "rollback_comparison_rows",
        "reviewer_signoff_placeholders",
    )

    for section in required_sections:
        broken = copy.deepcopy(packet)
        broken[section] = []
        result = validate_guardrail_recompile_staging_packet_v6(broken)
        assert not result.valid, section


def test_validator_rejects_missing_per_candidate_references_and_placeholders() -> None:
    packet = build_guardrail_recompile_staging_packet_v6(FIXTURE_PATH)
    cases = (
        ("process_impact_references", "impact-building-intake-001"),
        ("source_evidence_carry_forward_rows", "impact-building-intake-001"),
        ("deterministic_predicate_refresh_placeholders", "impact-building-intake-001"),
        ("rollback_comparison_rows", "impact-building-intake-001"),
        ("reviewer_signoff_placeholders", "impact-building-intake-001"),
    )

    for section, impact_id in cases:
        broken = copy.deepcopy(packet)
        broken[section] = [row for row in broken[section] if row.get("refresh_impact_id") != impact_id]
        result = validate_guardrail_recompile_staging_packet_v6(broken)
        assert not result.valid, section


def test_validator_rejects_missing_exact_confirmation_or_refused_action_preservation_checks() -> None:
    packet = build_guardrail_recompile_staging_packet_v6(FIXTURE_PATH)
    for check_type in ("exact_confirmation_preservation", "refused_action_preservation"):
        broken = copy.deepcopy(packet)
        broken["exact_confirmation_and_refused_action_preservation_checks"] = [
            row
            for row in broken["exact_confirmation_and_refused_action_preservation_checks"]
            if not (row["refresh_impact_id"] == "impact-building-intake-001" and row["check_type"] == check_type)
        ]
        result = validate_guardrail_recompile_staging_packet_v6(broken)
        assert not result.valid, check_type


def test_validator_rejects_missing_stale_evidence_stop_gate() -> None:
    packet = build_guardrail_recompile_staging_packet_v6(FIXTURE_PATH)
    broken = copy.deepcopy(packet)
    broken["stale_evidence_stop_gates"] = []

    result = validate_guardrail_recompile_staging_packet_v6(broken)

    assert not result.valid
    assert any("stale_evidence_stop_gates must include impact-trade-payment-002" in problem for problem in result.problems)


def test_validator_rejects_active_live_private_completion_guarantee_and_mutation_claims() -> None:
    packet = build_guardrail_recompile_staging_packet_v6(FIXTURE_PATH)
    cases = (
        ("activation_status", "active"),
        ("active_activation_claim", True),
        ("active_guardrail_mutation", True),
        ("live_crawl_note", "live crawl executed"),
        ("session_state_path", "private/session.json"),
        ("auth_state", "auth.json"),
        ("official_action_note", "official action completed"),
        ("guarantee_note", "permit will be approved"),
        ("mutation_note", "active guardrail mutation applied"),
    )

    for key, value in cases:
        broken = copy.deepcopy(packet)
        broken[key] = value
        result = validate_guardrail_recompile_staging_packet_v6(broken)
        assert not result.valid, key


def test_fixture_path_is_local_to_ppd_tests() -> None:
    assert FIXTURE_PATH == Path(__file__).parent / "fixtures" / "process_model_refresh_impact_queue_v6" / "sample_queue.json"
