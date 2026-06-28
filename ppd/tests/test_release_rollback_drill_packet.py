from __future__ import annotations

import copy
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from ppd.agent_readiness.release_rollback_drill_packet import (
    build_release_rollback_drill_packet,
    validate_release_rollback_drill_packet,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "release_rollback_drill"


def _load_inputs() -> dict[str, Any]:
    return json.loads((FIXTURE_DIR / "input_packets.json").read_text(encoding="utf-8"))


def _valid_packet() -> dict[str, Any]:
    inputs = _load_inputs()
    return build_release_rollback_drill_packet(
        inputs["promotion_audit_log_candidate"],
        inputs["operator_promotion_approval_packet"],
        inputs["post_release_monitoring_plan"],
    )


def test_builds_fixture_first_release_rollback_drill_packet() -> None:
    inputs = _load_inputs()

    packet = build_release_rollback_drill_packet(
        inputs["promotion_audit_log_candidate"],
        inputs["operator_promotion_approval_packet"],
        inputs["post_release_monitoring_plan"],
    )
    result = validate_release_rollback_drill_packet(packet)

    assert result.valid, result.problems
    assert packet["drill_status"] == "rollback_rehearsal_packet_only"
    assert packet["rollback_boundary"]["active_rollback"] is False
    assert packet["rollback_boundary"]["mutates_registries"] is False
    assert packet["rollback_boundary"]["mutates_manifests"] is False
    assert packet["rollback_boundary"]["mutates_requirements"] is False
    assert packet["rollback_boundary"]["mutates_process_models"] is False
    assert packet["rollback_boundary"]["mutates_guardrails"] is False
    assert packet["rollback_boundary"]["mutates_release_notes"] is False
    assert packet["rollback_boundary"]["mutates_schedules"] is False
    assert packet["rollback_boundary"]["mutates_agent_state"] is False
    assert packet["rollback_decision_points"]
    assert packet["affected_artifact_references"]
    assert packet["reviewer_owner_fields"]
    assert packet["smoke_test_rerun_checklist"]
    assert packet["no_active_rollback_attestations"]
    assert all(item["source_evidence_ids"] for item in packet["rollback_decision_points"])
    assert all(item["active_artifact_mutation"] is False for item in packet["affected_artifact_references"])
    assert all(item["schedule_enabled"] is False for item in packet["smoke_test_rerun_checklist"])
    assert all(item["writes_active_state"] is False for item in packet["smoke_test_rerun_checklist"])


@pytest.mark.parametrize(
    ("mutate", "expected_problem"),
    [
        (
            lambda packet: packet["rollback_boundary"].update({"active_rollback": True}),
            "active_rollback",
        ),
        (
            lambda packet: packet.update({"rollback_decision_points": []}),
            "rollback_decision_points must be a non-empty list",
        ),
        (
            lambda packet: packet["rollback_decision_points"][0].update({"source_evidence_ids": []}),
            "lacks source_evidence_ids",
        ),
        (
            lambda packet: packet["affected_artifact_references"][0].update({"active_artifact_mutation": True}),
            "must not mutate active artifacts",
        ),
        (
            lambda packet: packet["reviewer_owner_fields"][0].update({"reviewer_owner_id": ""}),
            "lacks reviewer_owner_id",
        ),
        (
            lambda packet: packet["smoke_test_rerun_checklist"][0].update({"schedule_enabled": True}),
            "must keep schedules disabled",
        ),
        (
            lambda packet: packet["no_active_rollback_attestations"][0].update({"attested": False}),
            "must be attested",
        ),
        (
            lambda packet: packet["rollback_decision_points"][0].update({"private_ref": "/home/alex/devhub-session.json"}),
            "private, runtime, raw, or downloaded artifact reference",
        ),
        (
            lambda packet: packet["rollback_decision_points"][0].update({"rollback_condition": "Rollback executed against active manifests."}),
            "active rollback, live operation, or mutation claim",
        ),
    ],
)
def test_rejects_unsafe_or_incomplete_release_rollback_drill_packet(
    mutate: Callable[[dict[str, Any]], None], expected_problem: str
) -> None:
    packet = copy.deepcopy(_valid_packet())

    mutate(packet)

    result = validate_release_rollback_drill_packet(packet)
    assert not result.valid
    assert any(expected_problem in problem for problem in result.problems)


def test_rejects_invalid_source_monitoring_plan() -> None:
    inputs = _load_inputs()
    inputs["post_release_monitoring_plan"]["monitoring_checks"][0]["source_evidence_ids"] = []

    with pytest.raises(ValueError, match="invalid_source_post_release_monitoring_plan"):
        build_release_rollback_drill_packet(
            inputs["promotion_audit_log_candidate"],
            inputs["operator_promotion_approval_packet"],
            inputs["post_release_monitoring_plan"],
        )
