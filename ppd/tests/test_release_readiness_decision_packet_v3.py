from __future__ import annotations

import copy
import json
from pathlib import Path

from ppd.release_readiness_decision_packet_v3 import (
    build_all_release_readiness_decision_packets_v3,
    build_release_readiness_decision_packet_v3,
    validate_release_readiness_decision_packet_v3,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "release_readiness_decision_packet_v3" / "scenarios.json"


def load_fixture() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _issue_codes(packet: dict[str, object]) -> set[str]:
    return {issue.code for issue in validate_release_readiness_decision_packet_v3(packet)}


def test_release_readiness_decision_packet_v3_has_only_synthetic_scenarios() -> None:
    fixture = load_fixture()
    packets = build_all_release_readiness_decision_packets_v3()

    assert set(packets) == set(fixture["scenarios"])
    assert set(packets) == {"release-ready", "release-held", "release-rejected"}


def test_release_readiness_decision_packet_v3_sections_and_effects() -> None:
    fixture = load_fixture()
    required_sections = fixture["required_sections"]
    forbidden_effects = fixture["forbidden_effects"]

    for scenario in fixture["scenarios"]:
        packet = build_release_readiness_decision_packet_v3(str(scenario))
        assert packet["packet_version"] == "release-readiness-decision-packet-v3"
        assert packet["scenario"] == scenario

        for section in required_sections:
            assert section in packet
            assert packet[section]

        for key, expected in forbidden_effects.items():
            assert packet[key] is expected

        assert validate_release_readiness_decision_packet_v3(packet) == []


def test_release_readiness_decision_packet_v3_decisions_are_distinct() -> None:
    ready = build_release_readiness_decision_packet_v3("release-ready")
    held = build_release_readiness_decision_packet_v3("release-held")
    rejected = build_release_readiness_decision_packet_v3("release-rejected")

    assert ready["decision"] == {
        "status": "ready",
        "release_allowed": True,
        "hold_required": False,
        "rejection_required": False,
        "basis": "synthetic offline fixture decision packet v3",
    }
    assert held["decision"]["status"] == "held"
    assert held["decision"]["release_allowed"] is False
    assert held["decision"]["hold_required"] is True
    assert held["decision"]["rejection_required"] is False
    assert rejected["decision"]["status"] == "rejected"
    assert rejected["decision"]["release_allowed"] is False
    assert rejected["decision"]["hold_required"] is False
    assert rejected["decision"]["rejection_required"] is True


def test_release_readiness_decision_packet_v3_validation_commands_are_exact_offline_commands() -> None:
    packet = build_release_readiness_decision_packet_v3("release-ready")

    assert packet["offline_validation_commands"] == [
        ["python3", "-m", "py_compile", "ppd/release_readiness_decision_packet_v3.py"],
        ["python3", "-m", "pytest", "ppd/tests/test_release_readiness_decision_packet_v3.py"],
        ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
    ]
    assert packet["validation_commands"] == packet["offline_validation_commands"]


def test_release_readiness_decision_packet_v3_rejects_unknown_scenario() -> None:
    try:
        build_release_readiness_decision_packet_v3("live-release")
    except ValueError as exc:
        assert "unsupported synthetic scenario" in str(exc)
    else:
        raise AssertionError("unknown scenarios must be rejected")


def test_validation_rejects_missing_required_decision_sections() -> None:
    fixture = load_fixture()
    required_sections = list(fixture["required_sections"])
    packet = build_release_readiness_decision_packet_v3("release-ready")

    for section in required_sections:
        broken = copy.deepcopy(packet)
        broken[section] = []
        assert section in _issue_codes(broken)


def test_validation_rejects_private_session_auth_and_browser_artifacts() -> None:
    packet = build_release_readiness_decision_packet_v3("release-ready")

    for field in ("auth_state", "session_state", "private_artifacts", "screenshots", "trace_path", "har_path"):
        broken = copy.deepcopy(packet)
        broken[field] = "ppd/tests/fixtures/private-devhub-session/artifact.json"
        assert "private_or_session_artifact" in _issue_codes(broken)


def test_validation_rejects_prohibited_claim_fields() -> None:
    packet = build_release_readiness_decision_packet_v3("release-ready")

    for field in (
        "live_devhub_interaction_claims",
        "active_surface_map_mutation_claims",
        "form_fill_claims",
        "upload_claims",
        "official_action_completion_claims",
        "legal_guarantees",
        "permitting_guarantees",
    ):
        broken = copy.deepcopy(packet)
        broken[field] = ["claim is not allowed"]
        assert "prohibited_claim" in _issue_codes(broken)


def test_validation_rejects_active_mutation_flags_and_forbidden_effects() -> None:
    packet = build_release_readiness_decision_packet_v3("release-ready")

    for field in ("active_mutation_flags", "mutates_remote_state", "uploads_documents", "submits_forms", "active_surface_map_mutation"):
        broken = copy.deepcopy(packet)
        broken[field] = True
        assert "active_mutation_flag" in _issue_codes(broken)

    broken = copy.deepcopy(packet)
    broken["devhub_access_allowed"] = True
    broken["artifact_promotion_allowed"] = True
    codes = _issue_codes(broken)
    assert "forbidden_effect" in codes


def test_validation_rejects_prohibited_unnegated_claim_text() -> None:
    packet = build_release_readiness_decision_packet_v3("release-ready")
    broken = copy.deepcopy(packet)
    broken["reviewer_dispositions"][0]["notes"] = "Reviewer completed the official action after a live DevHub interaction."

    codes = _issue_codes(broken)

    assert "prohibited_claim_text" in codes


def test_validation_allows_negated_safety_attestations() -> None:
    packet = build_release_readiness_decision_packet_v3("release-ready")
    packet["rollback_notes"].append("No screenshots, traces, HAR, private values, uploads, or live DevHub interaction were created.")

    assert validate_release_readiness_decision_packet_v3(packet) == []
