from __future__ import annotations

import json
from pathlib import Path

import pytest

from ppd.logic.guardrail_impact_delta_packet_v1 import (
    EXACT_OFFLINE_VALIDATION_COMMANDS,
    GuardrailImpactDeltaPacketV1Error,
    build_guardrail_impact_delta_packet_v1,
    iter_guardrail_impact_delta_packet_v1_issues,
    validate_guardrail_impact_delta_packet_v1,
)
from ppd.logic.process_dependency_graph_delta_packet_v1 import build_process_dependency_graph_delta_packet_v1


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "guardrail_impact_delta_packet_v1"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _fixture() -> dict:
    return _load_json(FIXTURE_DIR / "source_fixture.json")


def _process_delta_packet() -> dict:
    fixture = _fixture()
    source_path = (FIXTURE_DIR / fixture["source_process_dependency_graph_fixture"]).resolve()
    return build_process_dependency_graph_delta_packet_v1(_load_json(source_path))


def _packet() -> dict:
    return build_guardrail_impact_delta_packet_v1(_process_delta_packet())


def _messages(packet: dict) -> list[str]:
    return [f"{issue.path}: {issue.message}" for issue in iter_guardrail_impact_delta_packet_v1_issues(packet)]


def test_builds_fixture_first_guardrail_impact_delta_packet_v1() -> None:
    packet = _packet()

    assert packet["packet_version"] == "guardrail_impact_delta_packet_v1"
    assert packet["packet_mode"] == "fixture_first_delta_review_only"
    assert packet["mutation_policy"] == "no_compile_no_promotion_no_active_mutation"
    assert packet["promotion_status"] == "not_promoted"
    assert packet["compiler_invocation"] == "not_invoked"
    assert packet["offline_validation_commands"] == [list(command) for command in EXACT_OFFLINE_VALIDATION_COMMANDS]
    validate_guardrail_impact_delta_packet_v1(packet)


def test_maps_every_process_delta_candidate_to_every_required_guardrail_impact_group() -> None:
    packet = _packet()
    fixture = _fixture()
    expected_candidate_ids = set(fixture["expected_candidate_ids"])

    for group_name in fixture["expected_row_groups"]:
        rows = packet[group_name]
        assert {row["candidate_id"] for row in rows} == expected_candidate_ids
        assert all(row["activation_allowed"] is False for row in rows)
        assert all(row["review_status"] == "pending_reviewer_disposition" for row in rows)


def test_packet_contains_deontic_temporal_confirmation_refusal_explanation_stale_and_disposition_data() -> None:
    packet = _packet()

    assert all(row["affected_inputs"] for row in packet["affected_deterministic_predicate_rows"])
    assert all(row["affected_terms"] for row in packet["affected_deontic_rule_rows"])
    assert all(row["temporal_triggers"] for row in packet["affected_temporal_rule_rows"])
    assert all(row["affected_process_stages"] for row in packet["affected_reversible_action_predicate_rows"])
    assert all(row["affected_boundaries"] for row in packet["affected_exact_confirmation_predicate_rows"])
    assert all(row["affected_unsupported_paths"] for row in packet["affected_refused_action_predicate_rows"])
    assert all("{source_evidence_id}" in row["placeholders"] for row in packet["affected_explanation_template_placeholder_rows"])
    assert all(row["reviewer_holds"] for row in packet["stale_source_hold_rows"])
    assert all(row["current_disposition"] == "pending" for row in packet["reviewer_disposition_rows"])
    assert all(row["disposition_required_before_compile"] is True for row in packet["reviewer_disposition_rows"])


@pytest.mark.parametrize(
    "group_name",
    [
        "affected_deterministic_predicate_rows",
        "affected_deontic_rule_rows",
        "affected_temporal_rule_rows",
        "affected_reversible_action_predicate_rows",
        "affected_exact_confirmation_predicate_rows",
        "affected_refused_action_predicate_rows",
        "affected_explanation_template_placeholder_rows",
        "stale_source_hold_rows",
        "reviewer_disposition_rows",
    ],
)
def test_rejects_missing_candidate_from_required_impact_group(group_name: str) -> None:
    packet = _packet()
    packet[group_name] = [row for row in packet[group_name] if row["candidate_id"] != "candidate-trade-license-check"]

    messages = _messages(packet)

    assert any(f"{group_name}: missing row for candidate_id: candidate-trade-license-check" in message for message in messages)


@pytest.mark.parametrize(
    ("group_name", "field_name"),
    [
        ("affected_deterministic_predicate_rows", "affected_inputs"),
        ("affected_deontic_rule_rows", "affected_terms"),
        ("affected_temporal_rule_rows", "temporal_triggers"),
        ("affected_reversible_action_predicate_rows", "affected_process_stages"),
        ("affected_exact_confirmation_predicate_rows", "affected_boundaries"),
        ("affected_refused_action_predicate_rows", "affected_unsupported_paths"),
        ("affected_explanation_template_placeholder_rows", "placeholders"),
        ("stale_source_hold_rows", "reviewer_holds"),
        ("reviewer_disposition_rows", "allowed_dispositions"),
    ],
)
def test_rejects_missing_required_impact_payloads(group_name: str, field_name: str) -> None:
    packet = _packet()
    packet[group_name][0][field_name] = []

    messages = _messages(packet)

    assert any(f"{group_name}[0].{field_name}: required impact payload must be present" in message for message in messages)


def test_rejects_missing_required_explanation_placeholder_and_resolved_disposition() -> None:
    packet = _packet()
    packet["affected_explanation_template_placeholder_rows"][0]["placeholders"] = ["{requirement_id}"]
    packet["reviewer_disposition_rows"][0]["current_disposition"] = "accepted"
    packet["reviewer_disposition_rows"][0]["disposition_required_before_compile"] = False

    messages = _messages(packet)

    assert any("placeholders: missing required explanation placeholders" in message for message in messages)
    assert any("current_disposition: reviewer disposition must remain pending" in message for message in messages)
    assert any("disposition_required_before_compile: reviewer disposition is required before compile" in message for message in messages)


def test_rejects_non_exact_or_live_validation_commands() -> None:
    packet = _packet()
    packet["offline_validation_commands"] = [["python3", "-m", "pytest"], ["curl", "https://devhub.portlandoregon.gov"]]

    messages = _messages(packet)

    assert any("offline_validation_commands: must match exact offline validation commands" in message for message in messages)
    assert any("validation command must remain offline" in message for message in messages)
    with pytest.raises(GuardrailImpactDeltaPacketV1Error):
        validate_guardrail_impact_delta_packet_v1(packet)


@pytest.mark.parametrize(
    ("path", "value", "expected"),
    [
        (("no_active_mutation_attestations", "compiled_guardrails"), True, "active mutation attestation must be false"),
        (("compiler_invocation",), "compiler invoked", "packet must not invoke a guardrail compiler"),
        (("active_guardrail_patch",), {"unsafe": True}, "active mutation output fields are not allowed"),
        (("active_mutation",), True, "active mutation flags must be absent or false"),
        (("notes",), "raw crawl and storage_state were captured", "private, session, browser, raw crawl, or downloaded artifact references are not allowed"),
        (("notes",), "live crawl found authenticated DevHub data", "live crawl or DevHub observation claims are not allowed"),
        (("notes",), "permit guaranteed and will be issued", "legal or permitting guarantee claims are not allowed"),
        (("notes",), "application submitted and fee paid", "official-action completion claims are not allowed"),
    ],
)
def test_rejects_compile_promotion_active_mutation_private_live_guarantee_and_completion_claims(path: tuple[str, ...], value: object, expected: str) -> None:
    packet = _packet()
    target = packet
    for key in path[:-1]:
        target = target.setdefault(key, {})
    target[path[-1]] = value

    messages = _messages(packet)

    assert any(expected in message for message in messages)
