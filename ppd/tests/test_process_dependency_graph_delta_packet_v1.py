from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ppd.logic.process_dependency_graph_delta_packet_v1 import (
    EXACT_OFFLINE_VALIDATION_COMMANDS,
    ProcessDependencyGraphDeltaPacketV1Error,
    build_process_dependency_graph_delta_packet_v1,
    iter_process_dependency_graph_delta_packet_v1_issues,
    validate_process_dependency_graph_delta_packet_v1,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "process_dependency_graph_delta_packet_v1" / "source_fixture.json"


def _source_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _valid_packet() -> dict:
    return build_process_dependency_graph_delta_packet_v1(_source_fixture())


def _messages(packet: dict) -> list[str]:
    return [f"{issue.path}: {issue.message}" for issue in iter_process_dependency_graph_delta_packet_v1_issues(packet)]


def test_builds_valid_inactive_packet_from_fixture() -> None:
    packet = _valid_packet()

    assert packet["packet_version"] == "process_dependency_graph_delta_packet_v1"
    assert packet["mutation_policy"] == "inactive_fixture_review_only"
    assert packet["promotion_status"] == "not_promoted"
    assert packet["validation_commands"] == [list(command) for command in EXACT_OFFLINE_VALIDATION_COMMANDS]
    assert packet["offline_validation_commands"] == [list(command) for command in EXACT_OFFLINE_VALIDATION_COMMANDS]
    validate_process_dependency_graph_delta_packet_v1(packet)


@pytest.mark.parametrize(
    ("field", "expected"),
    [
        ("affected_permit_family_rows", "affected_permit_family_rows"),
        ("process_stage_rows", "process_stage_rows"),
        ("required_user_fact_rows", "required_user_fact_rows"),
        ("required_document_rows", "required_document_rows"),
        ("fee_deadline_trigger_rows", "fee_deadline_trigger_rows"),
        ("unsupported_path_rows", "unsupported_path_rows"),
        ("devhub_boundary_reference_rows", "devhub_boundary_reference_rows"),
        ("reviewer_hold_rows", "reviewer_hold_rows"),
    ],
)
def test_rejects_missing_required_impact_row_group(field: str, expected: str) -> None:
    packet = _valid_packet()
    packet[field] = []

    messages = _messages(packet)

    assert any(expected in message and "must contain at least one row" in message for message in messages)
    with pytest.raises(ProcessDependencyGraphDeltaPacketV1Error):
        validate_process_dependency_graph_delta_packet_v1(packet)


@pytest.mark.parametrize(
    "field",
    [
        "affected_permit_family_rows",
        "process_stage_rows",
        "required_user_fact_rows",
        "required_document_rows",
        "fee_deadline_trigger_rows",
        "unsupported_path_rows",
        "devhub_boundary_reference_rows",
        "reviewer_hold_rows",
    ],
)
def test_rejects_candidate_missing_from_required_impact_group(field: str) -> None:
    packet = _valid_packet()
    packet[field] = [row for row in packet[field] if row["candidate_id"] != "candidate-trade-license-check"]

    messages = _messages(packet)

    assert any(f"{field}: missing row for candidate_id: candidate-trade-license-check" in message for message in messages)


@pytest.mark.parametrize("field", ["validation_commands", "offline_validation_commands"])
def test_rejects_missing_validation_commands(field: str) -> None:
    packet = _valid_packet()
    del packet[field]

    messages = _messages(packet)

    assert any(f"{field}: missing required field" in message for message in messages)
    assert any(f"{field}: must match exact offline validation commands" in message for message in messages)


@pytest.mark.parametrize(
    ("path", "value", "expected"),
    [
        (("notes",), "raw crawl output saved under /private/session/file.html", "private/session/browser/raw/downloaded artifact references are not allowed"),
        (("notes",), "observed in DevHub during a real browser session", "live crawl or DevHub claims are not allowed"),
        (("notes",), "permit will be approved after this packet", "legal or permitting guarantees are not allowed"),
        (("notes",), "payment submitted and uploaded to DevHub", "official-action completion claims are not allowed"),
        (("active_mutation",), True, "active mutation flags are not allowed"),
        (("evidence", "session_file"), "redacted", "private/session/browser/raw/downloaded artifact fields are not allowed"),
    ],
)
def test_rejects_unsafe_private_live_guarantee_completion_and_mutation_claims(path: tuple[str, ...], value: object, expected: str) -> None:
    packet = _valid_packet()
    target = packet
    for key in path[:-1]:
        target = target.setdefault(key, {})
    target[path[-1]] = value

    messages = _messages(packet)

    assert any(expected in message for message in messages)


def test_builder_rejects_candidate_missing_required_impacts() -> None:
    fixture = copy.deepcopy(_source_fixture())
    fixture["requirement_delta_candidates"][0]["required_documents"] = []

    with pytest.raises(ProcessDependencyGraphDeltaPacketV1Error, match="required_documents must be a non-empty string list"):
        build_process_dependency_graph_delta_packet_v1(fixture)
