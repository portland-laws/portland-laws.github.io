from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from ppd.agent_readiness_replay_v5 import replay_agent_readiness_v5


FIXTURES = Path(__file__).parent / "fixtures" / "agent_readiness_replay_v5"


def test_agent_readiness_replay_v5_uses_only_committed_fixtures() -> None:
    replay = replay_agent_readiness_v5(
        FIXTURES / "guardrail_recompile_reviewer_packet_v5.json",
        FIXTURES / "synthetic_agent_requests_v5.json",
    )

    assert replay["version"] == "agent_readiness_replay_v5"
    assert replay["source_versions"] == [
        "guardrail_recompile_reviewer_packet_v5",
        "synthetic_agent_requests_v5",
    ]
    assert replay["reviewer_packet_references"]
    assert replay["synthetic_agent_request_references"]
    assert len(replay["responses"]) == 3

    for response in replay["responses"]:
        assert response["activated_guardrails"] is False
        assert response["opened_devhub"] is False
        assert response["read_private_documents"] is False
        assert response["performed_prohibited_action"] is False
        assert response["offline_validation_commands"] == [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]]


def test_agent_readiness_replay_v5_blocks_and_refuses_expected_cases() -> None:
    replay = replay_agent_readiness_v5(
        FIXTURES / "guardrail_recompile_reviewer_packet_v5.json",
        FIXTURES / "synthetic_agent_requests_v5.json",
    )
    responses = {item["id"]: item for item in replay["responses"]}

    missing = responses["missing-info-draft-only"]
    assert missing["missing_information_prompts"] == [
        "Which permit number or IVR number should be reviewed?",
        "Which property address should be used for the draft-only readiness check?",
    ]
    assert [action["label"] for action in missing["next_actions"]] == ["prepare draft question list"]
    assert missing["citation_payloads"][0]["source"] == "fixture"

    stale = responses["stale-and-conflicting-evidence"]
    assert stale["stale_evidence_block"] is True
    assert stale["conflicting_evidence_block"] is True
    assert stale["manual_handoff_reminders"]
    assert stale["rollback_notes"]

    refused = responses["confirmation-and-refusals"]
    assert refused["exact_confirmation_checkpoint"] == "Type EXACTLY: I confirm this is a draft-only readiness review."
    assert {item["category"] for item in refused["refused_actions"]} == {"consequential", "financial"}
    assert all("must stay manual" in item["explanation"] for item in refused["refused_actions"])


def test_agent_readiness_replay_v5_rejects_missing_required_packet_and_request_fields(tmp_path: Path) -> None:
    packet, requests = _valid_inputs()

    invalid_cases: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
    invalid_cases.append(("missing reviewer packet references", _without(packet, "reviewer_packet_references"), requests))
    invalid_cases.append(("missing synthetic agent request references", packet, _without(requests, "synthetic_agent_request_references")))
    invalid_cases.append(("missing synthetic agent requests", packet, _without(requests, "scenarios")))
    invalid_cases.append(("missing citation payloads", _without(packet, "citation_payloads"), requests))
    invalid_cases.append(("missing manual handoff reminders", _without(packet, "manual_handoff_reminders"), requests))
    invalid_cases.append(("missing rollback notes", _without(packet, "rollback_notes"), requests))
    invalid_cases.append(("missing validation commands", _without(packet, "offline_validation_commands"), requests))

    for label, invalid_packet, invalid_requests in invalid_cases:
        packet_path, requests_path = _write_inputs(tmp_path, label, invalid_packet, invalid_requests)
        with pytest.raises(ValueError):
            replay_agent_readiness_v5(packet_path, requests_path)


def test_agent_readiness_replay_v5_rejects_missing_scenario_checks(tmp_path: Path) -> None:
    expected_check_keys = [
        "missing_information_prompts",
        "stale_evidence_block",
        "conflicting_evidence_block",
        "reversible_draft_only_next_actions",
        "exact_confirmation_checkpoint",
        "refused_consequential_or_financial_actions",
        "citation_payloads",
        "manual_handoff_reminders",
        "rollback_notes",
        "offline_validation_commands",
    ]

    for key in expected_check_keys:
        packet, requests = _valid_inputs()
        del requests["scenarios"][0]["expected"][key]
        packet_path, requests_path = _write_inputs(tmp_path, f"missing-{key}", packet, requests)
        with pytest.raises(ValueError, match="missing expected checks"):
            replay_agent_readiness_v5(packet_path, requests_path)

    packet, requests = _valid_inputs()
    del requests["scenarios"][0]["evidence_state"]["stale"]
    packet_path, requests_path = _write_inputs(tmp_path, "missing-stale", packet, requests)
    with pytest.raises(ValueError, match="stale and conflicting evidence"):
        replay_agent_readiness_v5(packet_path, requests_path)

    packet, requests = _valid_inputs()
    requests["scenarios"][0]["requested_actions"] = []
    packet_path, requests_path = _write_inputs(tmp_path, "missing-draft-action", packet, requests)
    with pytest.raises(ValueError, match="reversible draft-only action"):
        replay_agent_readiness_v5(packet_path, requests_path)

    packet, requests = _valid_inputs()
    del requests["scenarios"][2]["exact_confirmation"]
    packet_path, requests_path = _write_inputs(tmp_path, "missing-confirmation", packet, requests)
    with pytest.raises(ValueError, match="exact confirmation"):
        replay_agent_readiness_v5(packet_path, requests_path)


def test_agent_readiness_replay_v5_rejects_unsafe_claims_and_artifacts(tmp_path: Path) -> None:
    unsafe_mutations = [
        ("active_guardrail_mutation", True),
        ("session_token", "private-token"),
        ("autonomous_official_action", True),
        ("operator_note", "The application submitted the application autonomously."),
        ("legal_note", "This is legal advice and guarantee permit approval."),
        ("active_mutation", True),
    ]

    for key, value in unsafe_mutations:
        packet, requests = _valid_inputs()
        packet[key] = value
        packet_path, requests_path = _write_inputs(tmp_path, f"unsafe-{key}", packet, requests)
        with pytest.raises(ValueError):
            replay_agent_readiness_v5(packet_path, requests_path)


def _valid_inputs() -> tuple[dict[str, Any], dict[str, Any]]:
    packet_path = FIXTURES / "guardrail_recompile_reviewer_packet_v5.json"
    requests_path = FIXTURES / "synthetic_agent_requests_v5.json"
    import json

    return json.loads(packet_path.read_text(encoding="utf-8")), json.loads(requests_path.read_text(encoding="utf-8"))


def _without(value: dict[str, Any], key: str) -> dict[str, Any]:
    copy = deepcopy(value)
    copy.pop(key, None)
    return copy


def _write_inputs(tmp_path: Path, label: str, packet: dict[str, Any], requests: dict[str, Any]) -> tuple[Path, Path]:
    import json

    safe_label = label.replace(" ", "-").replace("_", "-")
    packet_path = tmp_path / f"{safe_label}-packet.json"
    requests_path = tmp_path / f"{safe_label}-requests.json"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    requests_path.write_text(json.dumps(requests), encoding="utf-8")
    return packet_path, requests_path
