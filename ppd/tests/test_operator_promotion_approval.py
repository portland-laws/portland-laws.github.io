from pathlib import Path

from ppd.operator_promotion_approval import (
    PROHIBITED_MUTATION_TARGETS,
    REVIEWER_ROLES,
    build_operator_promotion_approval_packet,
    load_fixture_inputs,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "operator_promotion_approval"


def test_builds_fixture_first_operator_promotion_approval_packet() -> None:
    inputs = load_fixture_inputs(FIXTURE_DIR)

    result = build_operator_promotion_approval_packet(inputs)

    assert result.is_valid
    packet = result.packet
    assert packet["packet_type"] == "operator_promotion_approval_packet"
    assert packet["fixture_first"] is True
    assert packet["validation"]["status"] == "valid"
    assert packet["mutation_policy"]["active_registry_mutations"] == []
    assert packet["mutation_policy"]["agent_state_mutations"] == []
    assert set(packet["mutation_policy"]["prohibited_targets"]) == set(PROHIBITED_MUTATION_TARGETS)


def test_approval_packet_contains_required_human_review_surfaces() -> None:
    inputs = load_fixture_inputs(FIXTURE_DIR)

    packet = build_operator_promotion_approval_packet(inputs).packet

    checklist_ids = {item["item_id"] for item in packet["approval_checklist"]}
    assert "approve-offline-release-decision" in checklist_ids
    assert "approve-dry-run-promotion-sequence" in checklist_ids
    assert "approve-release-notes-candidate" in checklist_ids
    assert "approve-post-release-monitoring-plan" in checklist_ids
    assert "attest-no-active-promotion" in checklist_ids
    assert all(item["status"] == "pending_human_review" for item in packet["approval_checklist"])
    assert all(item["citations"] for item in packet["approval_checklist"])


def test_carries_forward_no_go_items_and_rollback_rehearsals() -> None:
    inputs = load_fixture_inputs(FIXTURE_DIR)

    packet = build_operator_promotion_approval_packet(inputs).packet

    no_go_descriptions = "\n".join(
        item["description"] for item in packet["explicit_no_go_carryovers"]
    )
    assert "fixture validation" in no_go_descriptions
    assert "live registry writes" in no_go_descriptions
    assert "reviewer signoff" in no_go_descriptions
    assert "monitoring owners" in no_go_descriptions
    assert packet["rollback_rehearsal_references"]
    assert all(
        reference["must_review_before_promotion"] is True
        for reference in packet["rollback_rehearsal_references"]
    )


def test_signoff_slots_and_no_active_promotion_attestations_are_pending() -> None:
    inputs = load_fixture_inputs(FIXTURE_DIR)

    packet = build_operator_promotion_approval_packet(inputs).packet

    assert [slot["role"] for slot in packet["reviewer_signoff_slots"]] == list(REVIEWER_ROLES)
    assert all(slot["decision"] == "pending" for slot in packet["reviewer_signoff_slots"])
    assert all(slot["reviewer_name"] == "" for slot in packet["reviewer_signoff_slots"])
    attestations = packet["no_active_promotion_attestations"]
    assert len(attestations) == 4
    assert all(item["active_promotion_state"] == "inactive" for item in attestations)
    assert all(item["mutates_active_targets"] == [] for item in attestations)


def test_validation_rejects_active_promotion_inputs() -> None:
    inputs = load_fixture_inputs(FIXTURE_DIR)
    inputs["offline_release_decision_packet"] = {
        **inputs["offline_release_decision_packet"],
        "active_promotion_state": "active",
        "mutates_active_targets": ["active_ppd_registries"],
    }

    result = build_operator_promotion_approval_packet(inputs)

    assert not result.is_valid
    assert result.packet["validation"]["status"] == "invalid"
    assert any("active target mutations" in error for error in result.validation_errors)
    assert any("active_promotion_state" in error for error in result.validation_errors)


def test_validation_rejects_uncited_approval_claims() -> None:
    inputs = load_fixture_inputs(FIXTURE_DIR)
    inputs["release_notes_candidate"] = {
        **inputs["release_notes_candidate"],
        "citations": [],
    }

    result = build_operator_promotion_approval_packet(inputs)

    assert not result.is_valid
    assert any("uncited approval claim" in error or "source_packets" in error for error in result.validation_errors)


def test_validation_rejects_ignored_unresolved_blockers() -> None:
    inputs = load_fixture_inputs(FIXTURE_DIR)
    inputs["offline_release_decision_packet"] = {
        **inputs["offline_release_decision_packet"],
        "unresolved_blockers": [
            {
                "summary": "Open blocker must remain visible.",
                "citations": [],
            }
        ],
    }

    result = build_operator_promotion_approval_packet(inputs)

    assert not result.is_valid
    assert any("explicit_no_go_carryovers" in error and "lacks citations" in error for error in result.validation_errors)


def test_validation_rejects_missing_rollback_rehearsal_references() -> None:
    inputs = load_fixture_inputs(FIXTURE_DIR)
    for packet in inputs.values():
        packet.pop("rollback_refs", None)
        packet.pop("rollback_rehearsal", None)
        packet.pop("rollback_rehearsal_references", None)

    result = build_operator_promotion_approval_packet(inputs)

    assert not result.is_valid
    assert any("rollback_rehearsal_references must be a non-empty list" in error for error in result.validation_errors)


def test_validation_rejects_private_raw_live_and_guarantee_references() -> None:
    unsafe_values = [
        "https://devhub.portlandoregon.gov/login?token=secret",
        "file:///home/user/private-case.pdf",
        "Use the raw body and raw archive output from a downloaded document.",
        "Live promotion complete and release notes published.",
        "This guarantees permit approval and no legal risk.",
    ]
    for unsafe_value in unsafe_values:
        inputs = load_fixture_inputs(FIXTURE_DIR)
        inputs["offline_release_decision_packet"] = {
            **inputs["offline_release_decision_packet"],
            "decision_summary": unsafe_value,
        }

        result = build_operator_promotion_approval_packet(inputs)

        assert not result.is_valid, unsafe_value


def test_validation_rejects_enabled_consequential_controls_and_mutation_flags() -> None:
    inputs = load_fixture_inputs(FIXTURE_DIR)
    inputs["dry_run_promotion_sequence_packet"] = {
        **inputs["dry_run_promotion_sequence_packet"],
        "consequential_controls_enabled": True,
    }

    result = build_operator_promotion_approval_packet(inputs)

    assert not result.is_valid
    assert any("enabled consequential control" in error for error in result.validation_errors)

    inputs = load_fixture_inputs(FIXTURE_DIR)
    inputs["post_release_monitoring_plan"] = {
        **inputs["post_release_monitoring_plan"],
        "active_artifact_mutation_enabled": True,
    }

    result = build_operator_promotion_approval_packet(inputs)

    assert not result.is_valid
    assert any("active artifact mutation flag" in error for error in result.validation_errors)
