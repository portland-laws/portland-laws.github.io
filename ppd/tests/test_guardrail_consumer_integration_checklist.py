from __future__ import annotations

from pathlib import Path

import pytest

from ppd.guardrail_consumer_integration_checklist import (
    REQUIRED_EXPECTATION_IDS,
    GuardrailConsumerIntegrationChecklistError,
    assert_valid_guardrail_consumer_integration_checklist,
    build_guardrail_consumer_integration_checklist,
    load_fixture,
    validate_guardrail_consumer_integration_checklist,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "guardrail_consumer_integration_checklist"


def test_build_checklist_exposes_required_cited_consumer_expectations() -> None:
    packet = build_guardrail_consumer_integration_checklist(load_fixture(FIXTURE_DIR / "input.json"))

    assert packet["packet_type"] == "ppd.guardrail_consumer_integration_checklist.v1"
    assert packet["fixture_first"] is True
    assert packet["metadata_only"] is True
    assert packet["live_services_called"] is False
    assert packet["live_enforcement_enabled"] is False
    assert packet["active_guardrail_bundles_changed"] is False
    assert [item["expectation_id"] for item in packet["api_contract_expectations"]] == list(REQUIRED_EXPECTATION_IDS)

    for expectation in packet["api_contract_expectations"]:
        assert expectation["citations"]
        assert expectation["source_packet_ids"]
        assert expectation["consumer_must"]
        assert expectation["consumer_must_not"]
        assert expectation["live_enforcement_enabled"] is False
        assert expectation["guardrail_bundle_mutation_allowed"] is False

    refused = next(
        item for item in packet["api_contract_expectations"] if item["expectation_id"] == "refused_consequential_actions"
    )
    assert set(refused["refused_actions"]) == {
        "payment",
        "upload",
        "submission",
        "scheduling",
        "cancellation",
        "certification",
    }
    assert validate_guardrail_consumer_integration_checklist(packet) == []
    assert_valid_guardrail_consumer_integration_checklist(packet)


def test_checklist_rejects_live_guardrail_enforcement_input() -> None:
    fixture = load_fixture(FIXTURE_DIR / "input.json")
    fixture["inputs"]["guardrail_activation_decision"]["live_enforcement_enabled"] = True

    with pytest.raises(GuardrailConsumerIntegrationChecklistError, match="live_enforcement_enabled false"):
        build_guardrail_consumer_integration_checklist(fixture)


def test_checklist_validation_rejects_uncited_expectation() -> None:
    packet = build_guardrail_consumer_integration_checklist(load_fixture(FIXTURE_DIR / "input.json"))
    packet["api_contract_expectations"][0]["citations"] = []

    errors = validate_guardrail_consumer_integration_checklist(packet)

    assert any("citations must be non-empty" in error for error in errors)


def test_checklist_validation_rejects_active_bundle_mutation_claim() -> None:
    packet = build_guardrail_consumer_integration_checklist(load_fixture(FIXTURE_DIR / "input.json"))
    packet["active_guardrail_bundles_changed"] = True

    errors = validate_guardrail_consumer_integration_checklist(packet)

    assert "active_guardrail_bundles_changed must be false" in errors


def test_checklist_rejects_private_case_facts_and_local_paths() -> None:
    packet = build_guardrail_consumer_integration_checklist(load_fixture(FIXTURE_DIR / "input.json"))
    packet["api_contract_expectations"][0]["private_case_fact"] = "permit address"
    packet["api_contract_expectations"][1]["notes"] = "read /home/example/private.pdf"

    errors = validate_guardrail_consumer_integration_checklist(packet)

    assert any("unsafe private or raw field" in error for error in errors)
    assert any("unsafe private or raw reference" in error for error in errors)


def test_checklist_rejects_stale_source_marked_current_without_acknowledgement() -> None:
    packet = build_guardrail_consumer_integration_checklist(load_fixture(FIXTURE_DIR / "input.json"))
    packet["source_status_probe"] = {
        "source_id": "fixture:stale-current",
        "freshness_status": "current",
        "stale_evidence": ["fixture:old-guidance"],
    }

    errors = validate_guardrail_consumer_integration_checklist(packet)

    assert any("stale source is marked current without acknowledgement" in error for error in errors)


def test_checklist_rejects_blocked_action_downgrade() -> None:
    packet = build_guardrail_consumer_integration_checklist(load_fixture(FIXTURE_DIR / "input.json"))
    packet["user_gap_analysis"] = {
        "blocked_actions": [
            {
                "action_id": "submit-permit",
                "classification": "submission",
                "status": "next_safe_action",
            }
        ]
    }

    errors = validate_guardrail_consumer_integration_checklist(packet)

    assert any("blocked consequential action is downgraded" in error for error in errors)


def test_checklist_rejects_missing_manual_handoff_expectations() -> None:
    packet = build_guardrail_consumer_integration_checklist(load_fixture(FIXTURE_DIR / "input.json"))
    manual = next(item for item in packet["api_contract_expectations"] if item["expectation_id"] == "manual_handoffs")
    manual["consumer_must"] = ["Return a generic escalation status."]
    manual["consumer_must_not"] = ["Do not store private data."]

    errors = validate_guardrail_consumer_integration_checklist(packet)

    assert any("manual_handoffs expectation must require manual handoff" in error for error in errors)


def test_checklist_rejects_live_llm_or_devhub_execution_claims() -> None:
    packet = build_guardrail_consumer_integration_checklist(load_fixture(FIXTURE_DIR / "input.json"))
    packet["api_contract_expectations"][0]["llm_execution_completed"] = True
    packet["api_contract_expectations"][1]["notes"] = "Live DevHub execution completed."

    errors = validate_guardrail_consumer_integration_checklist(packet)

    assert any("live LLM or DevHub execution claim" in error for error in errors)


def test_checklist_rejects_enabled_consequential_controls() -> None:
    packet = build_guardrail_consumer_integration_checklist(load_fixture(FIXTURE_DIR / "input.json"))
    packet["payment_enabled"] = True

    errors = validate_guardrail_consumer_integration_checklist(packet)

    assert any("enabled consequential control" in error for error in errors)
