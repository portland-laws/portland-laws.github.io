from __future__ import annotations

import pytest

from ppd.validation.inactive_guardrail_recompile_staging_packet_v7 import reject_packet, validate_packet


def valid_packet() -> dict[str, object]:
    return {
        "packet_version": 7,
        "guardrail_mode": "inactive",
        "process_model_impact_queue_refs": ["pmq-fixture-001"],
        "affected_guardrail_bundle_rows": ["GuardrailBundle:fixture-row-001"],
        "deterministic_predicate_change_placeholders": ["predicate-change-placeholder"],
        "deontic_rule_review_placeholders": ["deontic-review-placeholder"],
        "temporal_rule_review_placeholders": ["temporal-review-placeholder"],
        "reversible_action_predicate_preservation_notes": ["preserve reversible-action predicates"],
        "exact_confirmation_gate_preservation_notes": ["preserve exact-confirmation gates"],
        "refused_action_gate_preservation_notes": ["preserve refused-action gates"],
        "stale_evidence_hold_propagation_rows": ["stale-evidence-row-placeholder"],
        "rollback_checkpoint_placeholders": ["rollback-checkpoint-placeholder"],
        "reviewer_signoff_placeholders": ["reviewer-signoff-placeholder"],
        "validation_commands": [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]],
        "notes": "Inactive deterministic fixture only.",
    }


@pytest.mark.parametrize(
    ("field", "code"),
    [
        ("process_model_impact_queue_refs", "missing_process_model_impact_queue_refs"),
        ("affected_guardrail_bundle_rows", "missing_affected_guardrail_bundle_rows"),
        ("deterministic_predicate_change_placeholders", "missing_deterministic_predicate_change_placeholders"),
        ("deontic_rule_review_placeholders", "missing_deontic_rule_review_placeholders"),
        ("temporal_rule_review_placeholders", "missing_temporal_rule_review_placeholders"),
        ("reversible_action_predicate_preservation_notes", "missing_reversible_action_predicate_preservation_notes"),
        ("exact_confirmation_gate_preservation_notes", "missing_exact_confirmation_gate_preservation_notes"),
        ("refused_action_gate_preservation_notes", "missing_refused_action_gate_preservation_notes"),
        ("stale_evidence_hold_propagation_rows", "missing_stale_evidence_hold_propagation_rows"),
        ("rollback_checkpoint_placeholders", "missing_rollback_checkpoint_placeholders"),
        ("reviewer_signoff_placeholders", "missing_reviewer_signoff_placeholders"),
        ("validation_commands", "missing_validation_commands"),
    ],
)
def test_packet_v7_rejects_missing_required_rows_and_placeholders(field: str, code: str) -> None:
    packet = valid_packet()
    packet[field] = []

    issues = validate_packet(packet)

    assert code in {issue.code for issue in issues}


@pytest.mark.parametrize(
    ("notes", "code"),
    [
        ("Updated active guardrail bundle row.", "active_guardrail_mutation_claim"),
        ("Activated guardrail after review.", "guardrail_activation_claim"),
        ("Executed a crawl against the live DevHub site.", "live_crawl_execution_claim"),
        ("Stored raw crawl artifact and captured html.", "downloaded_or_raw_crawl_artifact"),
        ("Attached DevHub session cookie and auth token.", "private_session_auth_artifact"),
        ("Officially completed permit submission.", "official_action_completion_claim"),
        ("This guarantees permit approval.", "legal_or_permitting_guarantee"),
        ("active_mutation: true", "active_mutation_flag"),
    ],
)
def test_packet_v7_rejects_prohibited_claims_and_flags(notes: str, code: str) -> None:
    packet = valid_packet()
    packet["notes"] = notes

    issues = validate_packet(packet)

    assert code in {issue.code for issue in issues}


def test_packet_v7_rejects_nested_active_mutation_flags() -> None:
    packet = valid_packet()
    packet["staging_flags"] = {"write_active": True}

    issues = validate_packet(packet)

    assert "active_mutation_flag" in {issue.code for issue in issues}


def test_packet_v7_accepts_inactive_deterministic_fixture() -> None:
    reject_packet(valid_packet())
