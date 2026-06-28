from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from ppd.logic.agent_guardrail_api_compat_v6 import (
    INACTIVE_STATUS,
    OFFLINE_VALIDATION_COMMANDS,
    PACKET_VERSION,
    PROHIBITED_EFFECTS,
    SOURCE_FIXTURE_VERSION,
    AgentGuardrailApiCompatV6ValidationError,
    assert_valid_agent_guardrail_api_compatibility_packet_v6,
    build_compatibility_packet_from_fixture,
    dump_packet_json,
    validate_agent_guardrail_api_compatibility_packet_v6,
)

FIXTURE_ROOT = Path(__file__).parent / "fixtures"
MONITORING_FIXTURE = (
    FIXTURE_ROOT
    / "post_activation_monitoring_rehearsal_v5"
    / "monitoring_rehearsal_v5.json"
)
EXPECTED_FIXTURE = (
    FIXTURE_ROOT
    / "agent_guardrail_api_compat_v6"
    / "agent_guardrail_api_compat_v6_expected.json"
)


def _load_expected() -> dict[str, object]:
    with EXPECTED_FIXTURE.open("r", encoding="utf-8") as expected_file:
        loaded = json.load(expected_file)
    assert isinstance(loaded, dict)
    return loaded


def _valid_packet() -> dict[str, object]:
    return build_compatibility_packet_from_fixture(MONITORING_FIXTURE)


def _row(packet: dict[str, object], scenario: str) -> dict[str, object]:
    rows = packet["rows"]
    assert isinstance(rows, list)
    for row in rows:
        assert isinstance(row, dict)
        if row["scenario"] == scenario:
            return row
    raise AssertionError(f"missing row {scenario}")


def _validation_text(packet: dict[str, object]) -> str:
    return " | ".join(validate_agent_guardrail_api_compatibility_packet_v6(packet))


def test_packet_v6_uses_only_v5_monitoring_fixture_and_synthetic_requests() -> None:
    packet = _valid_packet()
    expected = _load_expected()

    assert packet["packet_version"] == PACKET_VERSION == expected["packet_version"]
    assert packet["source_fixture_version"] == SOURCE_FIXTURE_VERSION
    assert packet["status"] == INACTIVE_STATUS
    assert packet["fixture_first"] is True
    assert packet["synthetic_requests_only"] is True
    assert packet["guardrails_activated"] is False
    assert packet["devhub_opened"] is False
    assert packet["live_crawl_performed"] is False
    assert packet["private_documents_read"] is False
    assert packet["official_actions_performed"] == []
    assert packet["legal_or_permitting_guarantees"] == []

    rows = packet["rows"]
    assert isinstance(rows, list)
    scenarios = {row["scenario"] for row in rows}
    assert scenarios == set(expected["required_scenarios"])

    for row in rows:
        assert row["active"] is False
        assert row["guardrails_activated"] is False
        assert row["allowed_effects"] == []
        assert row["prohibited_effects"] == list(PROHIBITED_EFFECTS)
        assert row["monitoring_references"] == [
            "v5-monitor-devhub-faq-freshness",
            "v5-monitor-fee-payment-guide-freshness",
        ]
        assert row["synthetic_agent_request"]
        assert row["synthetic_agent_request"]["scenario"] == row["scenario"]
        assert row["citation_payload"]
        for citation in row["citation_payload"]:
            assert set(citation) == {
                "evidence_id",
                "source_id",
                "title",
                "fixture_anchor",
            }


def test_packet_v6_defines_expected_blocks_and_refusals() -> None:
    packet = _valid_packet()
    rows = {row["scenario"]: row for row in packet["rows"]}

    assert rows["missing_facts"]["expected_block"] == "ask_for_missing_facts"
    assert rows["missing_facts"]["inactive_response"]["missing_fact_prompts"]
    assert rows["stale_source_block"]["inactive_response"]["decision"] == "blocked"
    assert rows["stale_source_block"]["inactive_response"]["stale_source_block"] is True
    assert rows["conflicting_evidence_block"]["expected_block"] == "human_review_required"
    assert rows["conflicting_evidence_block"]["inactive_response"]["conflicting_evidence_block"] is True
    assert rows["reversible_draft_only_action"]["inactive_response"]["next_actions"] == [
        {
            "label": "prepare local draft preview",
            "draft_only": True,
            "reversible": True,
            "official_effect": False,
        }
    ]
    assert rows["reversible_draft_only_action"]["inactive_response"]["limits"] == [
        "local preview only",
        "no upload",
        "no submit",
        "no certification",
    ]
    assert rows["exact_confirmation_checkpoint"]["inactive_response"]["confirmation_match"] == "exact_text_only"
    assert rows["refused_consequential_action"]["inactive_response"]["decision"] == "refused"
    assert rows["refused_consequential_action"]["inactive_response"]["refusal_explanation"]
    assert rows["refused_financial_action"]["inactive_response"]["decision"] == "refused"
    assert rows["refused_financial_action"]["inactive_response"]["refusal_explanation"]
    assert rows["manual_handoff_routing"]["inactive_response"]["handoff_route"] == "attended_devhub_worker"
    assert rows["rollback_notes"]["inactive_response"]["rollback_notes"] == [
        "discard local draft preview",
        "restore fixture request state",
    ]
    assert rows["monitoring_references"]["inactive_response"]["monitoring_reference_required"] is True


def test_packet_v6_exports_exact_offline_validation_commands_only() -> None:
    packet = _valid_packet()
    expected = _load_expected()

    assert packet["offline_validation_commands"] == OFFLINE_VALIDATION_COMMANDS
    assert packet["offline_validation_commands"] == expected["required_offline_validation_commands"]

    validation_row = next(
        row
        for row in packet["rows"]
        if row["scenario"] == "exact_offline_validation_commands"
    )
    assert validation_row["inactive_response"]["validation_commands"] == OFFLINE_VALIDATION_COMMANDS
    flattened = " ".join(" ".join(command) for command in OFFLINE_VALIDATION_COMMANDS)
    prohibited_terms = ["curl", "wget", "playwright", "devhub", "upload", "submit", "pay"]
    for term in prohibited_terms:
        assert term not in flattened.lower()


def test_packet_v6_validator_accepts_generated_packet() -> None:
    packet = _valid_packet()

    assert validate_agent_guardrail_api_compatibility_packet_v6(packet) == []
    assert_valid_agent_guardrail_api_compatibility_packet_v6(packet)


@pytest.mark.parametrize(
    ("scenario", "mutate", "expected_problem"),
    [
        (
            "monitoring_references",
            lambda row: row.__setitem__("monitoring_references", []),
            "monitoring rehearsal references",
        ),
        (
            "missing_facts",
            lambda row: row["inactive_response"].pop("missing_fact_prompts"),
            "missing-fact prompts",
        ),
        (
            "stale_source_block",
            lambda row: row["inactive_response"].pop("stale_source_block"),
            "stale-source block",
        ),
        (
            "conflicting_evidence_block",
            lambda row: row["inactive_response"].pop("conflicting_evidence_block"),
            "conflicting-evidence block",
        ),
        (
            "reversible_draft_only_action",
            lambda row: row["inactive_response"].pop("next_actions"),
            "next-action rows",
        ),
        (
            "exact_confirmation_checkpoint",
            lambda row: row["inactive_response"].pop("exact_confirmation_checkpoint"),
            "exact-confirmation checkpoint",
        ),
        (
            "refused_consequential_action",
            lambda row: row["inactive_response"].pop("refusal_explanation"),
            "refused action explanation",
        ),
        (
            "refused_financial_action",
            lambda row: row["inactive_response"].pop("refusal_explanation"),
            "refused action explanation",
        ),
        (
            "citation_payload",
            lambda row: row.__setitem__("citation_payload", []),
            "citation payloads",
        ),
        (
            "manual_handoff_routing",
            lambda row: row["inactive_response"].pop("handoff_route"),
            "manual handoff routing",
        ),
        (
            "rollback_notes",
            lambda row: row["inactive_response"].pop("rollback_notes"),
            "rollback notes",
        ),
        (
            "exact_offline_validation_commands",
            lambda row: row["inactive_response"].pop("validation_commands"),
            "exact validation commands",
        ),
    ],
)
def test_packet_v6_rejects_missing_required_controls(
    scenario: str,
    mutate: object,
    expected_problem: str,
) -> None:
    packet = deepcopy(_valid_packet())
    row = _row(packet, scenario)
    mutate(row)

    assert expected_problem in _validation_text(packet)


def test_packet_v6_rejects_missing_synthetic_agent_request_rows() -> None:
    packet = deepcopy(_valid_packet())
    _row(packet, "missing_facts").pop("synthetic_agent_request")

    assert "synthetic_agent_request must be present" in _validation_text(packet)


def test_packet_v6_rejects_missing_request_response_schema_fields() -> None:
    packet = deepcopy(_valid_packet())
    row = _row(packet, "missing_facts")
    row.pop("inactive_request")
    row.pop("inactive_response")
    row.pop("requested_action")

    problems = _validation_text(packet)
    assert "inactive_request must be a non-empty object" in problems
    assert "inactive_response must be a non-empty object" in problems
    assert "requested_action is required" in problems


def test_packet_v6_rejects_live_activation_claims_and_active_mutation_flags() -> None:
    packet = deepcopy(_valid_packet())
    packet["guardrails_activated"] = True
    packet["devhub_opened"] = True
    row = _row(packet, "missing_facts")
    row["active"] = True
    row["guardrails_activated"] = True
    row["allowed_effects"] = ["submit"]

    problems = _validation_text(packet)
    assert "guardrails_activated must be False" in problems
    assert "devhub_opened must be False" in problems
    assert "active must be false" in problems
    assert "allowed_effects must be empty" in problems


def test_packet_v6_rejects_private_session_auth_artifacts() -> None:
    packet = deepcopy(_valid_packet())
    _row(packet, "missing_facts")["session_state"] = {"cookie": "set-cookie: secret"}

    assert "private/session/auth artifact material" in _validation_text(packet)


def test_packet_v6_rejects_official_completion_claims_and_guarantees() -> None:
    packet = deepcopy(_valid_packet())
    packet["official_actions_performed"] = ["submitted permit application"]
    packet["legal_or_permitting_guarantees"] = ["permit will be approved"]
    _row(packet, "exact_confirmation_checkpoint")["official_action_completed"] = True

    problems = _validation_text(packet)
    assert "official_actions_performed must be empty" in problems
    assert "legal_or_permitting_guarantees must be empty" in problems
    assert "official-action completion or guarantee claim" in problems


def test_packet_v6_rejects_non_v5_monitoring_fixtures(tmp_path: Path) -> None:
    wrong_fixture = tmp_path / "wrong.json"
    wrong_fixture.write_text(
        json.dumps({"fixture_version": "post-activation-monitoring-rehearsal-v4"}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Expected monitoring fixture version"):
        build_compatibility_packet_from_fixture(wrong_fixture)


def test_packet_v6_assertion_raises_validation_error() -> None:
    packet = deepcopy(_valid_packet())
    packet["offline_validation_commands"] = []

    with pytest.raises(AgentGuardrailApiCompatV6ValidationError, match="offline_validation_commands"):
        assert_valid_agent_guardrail_api_compatibility_packet_v6(packet)


def test_packet_v6_json_dump_is_stable_and_inactive() -> None:
    packet = _valid_packet()
    dumped = dump_packet_json(packet)
    restored = json.loads(dumped)

    assert restored == packet
    assert dumped.endswith("\n")
    assert "inactive_fixture_only" in dumped
    assert "legal_or_permitting_guarantee" in dumped
