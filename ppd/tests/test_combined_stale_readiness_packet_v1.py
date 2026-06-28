from __future__ import annotations

from copy import deepcopy

from ppd.validation.combined_stale_readiness_packet_v1 import validate_packet


def _valid_packet() -> dict:
    return {
        "schema_version": "combined-public-devhub-stale-readiness-packet-v1",
        "public_monitoring_references": ["public monitor fixture ref"],
        "stale_source_hold_references": ["stale source hold fixture ref"],
        "devhub_surface_delta_references": ["DevHub surface delta fixture ref"],
        "devhub_agent_impact_references": ["DevHub agent impact fixture ref"],
        "recommendations": {
            "proceed": "Proceed only after fixture validation remains clean.",
            "hold": "Hold when a required reference is stale or absent.",
            "reject": "Reject when prohibited artifacts or claims appear.",
        },
        "dependency_ordering": ["public references", "DevHub deltas", "review"],
        "reviewer_routing": ["PP&D automation reviewer"],
        "rollback_notes": ["Remove packet from promotion queue and keep fixture-only evidence."],
        "validation_commands": [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]],
        "mutation_flags": {"active_mutation": False},
    }


def _codes(packet: dict) -> set[str]:
    return {issue.code for issue in validate_packet(packet)}


def test_valid_packet_has_no_issues() -> None:
    assert validate_packet(_valid_packet()) == []


def test_rejects_missing_required_references_and_controls() -> None:
    required_fields = {
        "public_monitoring_references": "missing_public_monitoring_references",
        "stale_source_hold_references": "missing_stale_source_hold_references",
        "devhub_surface_delta_references": "missing_devhub_surface_delta_references",
        "devhub_agent_impact_references": "missing_devhub_agent_impact_references",
        "dependency_ordering": "missing_dependency_ordering",
        "reviewer_routing": "missing_reviewer_routing",
        "rollback_notes": "missing_rollback_notes",
        "validation_commands": "missing_validation_commands",
    }
    for field, expected_code in required_fields.items():
        packet = _valid_packet()
        packet[field] = []
        assert expected_code in _codes(packet)


def test_rejects_missing_proceed_hold_reject_recommendations() -> None:
    for recommendation in ("proceed", "hold", "reject"):
        packet = _valid_packet()
        packet["recommendations"] = deepcopy(packet["recommendations"])
        packet["recommendations"][recommendation] = ""
        assert f"missing_{recommendation}_recommendation" in _codes(packet)


def test_rejects_forbidden_artifacts_claims_and_mutation_flags() -> None:
    forbidden_packets = [
        {"evidence": {"credentials": "fixture must not include credentials"}},
        {"evidence": "session cookie captured in browser state"},
        {"evidence": "screenshot and trace are attached"},
        {"evidence": "HAR file and downloaded document are present"},
        {"claim": "live DevHub crawl completed"},
        {"claim": "official action completed for this permit"},
        {"claim": "release promoted to production"},
        {"claim": "permitting guarantee: will be approved"},
        {"mutation_flags": {"active_mutation": True}},
    ]

    for fragment in forbidden_packets:
        packet = _valid_packet()
        packet.update(fragment)
        assert validate_packet(packet), fragment
