from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from ppd.agent_readiness.contract_examples import (
    EXAMPLE_RESPONSE_TYPES,
    AgentReadinessContractExamplesError,
    build_agent_readiness_contract_examples_packet,
    load_agent_readiness_contract_examples_fixture,
    validate_agent_readiness_contract_examples_packet,
)


_FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "agent_readiness_contract_examples"
    / "synthetic_readiness_contract_examples.json"
)


def _fixture() -> dict:
    return json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))


def _packet() -> dict:
    return load_agent_readiness_contract_examples_fixture(_FIXTURE_PATH)


def test_loads_fixture_first_agent_readiness_contract_examples() -> None:
    packet = _packet()

    assert packet["packet_type"] == "ppd.agent_readiness_contract_examples.v1"
    assert packet["fixture_first"] is True
    assert packet["synthetic"] is True
    assert packet["metadata_only"] is True
    assert packet["llm_called"] is False
    assert packet["devhub_called"] is False
    assert packet["live_services_called"] is False
    assert packet["response_order"] == list(EXAMPLE_RESPONSE_TYPES)
    assert packet["source_registry_promotion_id"] == "source-registry-promotion-agent-examples-v1"
    assert packet["guardrail_promotion_id"] == "guardrail-promotion-agent-examples-v1"
    assert validate_agent_readiness_contract_examples_packet(packet) == []


def test_packet_exposes_the_five_required_synthetic_api_examples() -> None:
    packet = _packet()
    examples = {example["response_type"]: example for example in packet["api_examples"]}

    assert set(examples) == set(EXAMPLE_RESPONSE_TYPES)
    assert examples["missing_fact_prompt"]["prompt_fields"][0]["fact_id"] == "project_scope_summary"
    assert examples["stale_evidence_warning"]["status"] == "blocked_until_refresh"
    assert examples["stale_evidence_warning"]["stale_evidence_ids"] == ["ev-file-standards-stale"]
    assert examples["allowed_local_preview"]["allowed_actions"][0]["devhub_called"] is False
    assert examples["allowed_local_preview"]["allowed_actions"][0]["allowed"] is True
    assert {action["action_id"] for action in examples["refused_consequential_action"]["refused_actions"]} == {
        "pay-review-fees",
        "submit-permit-request",
        "upload-plans-to-official-record",
    }
    assert all(
        action["requires_exact_confirmation"] is True
        for action in examples["refused_consequential_action"]["refused_actions"]
    )
    assert examples["manual_handoff_response"]["manual_handoff_actions"][0]["automation_paused"] is True


def test_each_example_is_cited_from_reviewed_source_registry_metadata() -> None:
    packet = _packet()

    for example in packet["api_examples"]:
        assert example["citations"]
        for citation in example["citations"]:
            assert citation["canonical_url"].startswith("https://www.portland.gov/ppd/")
            assert citation["review_status"] == "reviewed_promotable"
            assert citation["no_raw_body_persisted"] is True


def test_rejects_unreviewed_promotion_inputs() -> None:
    fixture = _fixture()
    fixture["reviewed_guardrail_promotion"]["review_status"] = "draft"

    with pytest.raises(AgentReadinessContractExamplesError) as excinfo:
        build_agent_readiness_contract_examples_packet(fixture)

    assert any("review_status must be reviewed_promotable" in problem for problem in excinfo.value.problems)


def test_rejects_private_or_live_artifact_fields() -> None:
    fixture = _fixture()
    fixture["synthetic_api_examples"][0]["prompt_fields"][0]["value"] = "123 private street"

    with pytest.raises(AgentReadinessContractExamplesError) as excinfo:
        build_agent_readiness_contract_examples_packet(fixture)

    assert any("private or live artifact field" in problem for problem in excinfo.value.problems)


def test_rejects_local_preview_that_calls_devhub() -> None:
    fixture = _fixture()
    fixture["synthetic_api_examples"][2]["allowed_actions"][0]["devhub_called"] = True

    with pytest.raises(AgentReadinessContractExamplesError) as excinfo:
        build_agent_readiness_contract_examples_packet(fixture)

    assert any("must not call DevHub" in problem for problem in excinfo.value.problems)


def test_rejects_consequential_refusal_without_exact_confirmation_gate() -> None:
    fixture = _fixture()
    fixture["synthetic_api_examples"][3]["refused_actions"][0]["requires_exact_confirmation"] = False

    with pytest.raises(AgentReadinessContractExamplesError) as excinfo:
        build_agent_readiness_contract_examples_packet(fixture)

    assert any("must require exact confirmation" in problem for problem in excinfo.value.problems)


def test_rejects_stale_warning_without_stale_source_registry_evidence() -> None:
    fixture = deepcopy(_fixture())
    fixture["reviewed_source_registry_promotion"]["source_evidence"][4]["freshness_status"] = "current"

    with pytest.raises(AgentReadinessContractExamplesError) as excinfo:
        build_agent_readiness_contract_examples_packet(fixture)

    assert any("must have freshness_status=stale" in problem for problem in excinfo.value.problems)
