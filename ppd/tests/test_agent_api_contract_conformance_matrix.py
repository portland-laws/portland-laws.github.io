from pathlib import Path

from ppd.agent_readiness.conformance_matrix import (
    MATRIX_CHECKS,
    load_agent_api_contract_conformance_fixture,
    validate_agent_api_contract_conformance_matrix,
)


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "agent_readiness"
    / "agent_api_contract_conformance_matrix.json"
)


def test_agent_api_contract_conformance_matrix_fixture_passes() -> None:
    matrix = load_agent_api_contract_conformance_fixture(FIXTURE_PATH)

    assert matrix["packet_type"] == "ppd.agent_api_contract_conformance_matrix.v1"
    assert matrix["fixture_first"] is True
    assert matrix["synthetic"] is True
    assert matrix["llm_called"] is False
    assert matrix["devhub_called"] is False
    assert matrix["live_services_called"] is False
    assert matrix["metadata_only"] is True
    assert matrix["matrix_order"] == list(MATRIX_CHECKS)
    assert [row["check_id"] for row in matrix["rows"]] == list(MATRIX_CHECKS)
    assert all(row["conformance_status"] == "pass" for row in matrix["rows"])
    assert matrix["summary"] == {
        "checks_total": 5,
        "checks_passed": 5,
        "checks_failed": 0,
    }
    assert validate_agent_api_contract_conformance_matrix(matrix) == []


def test_agent_api_contract_conformance_matrix_covers_required_guardrail_cases() -> None:
    matrix = load_agent_api_contract_conformance_fixture(FIXTURE_PATH)
    request_types = {row["guardrail_request_type"] for row in matrix["rows"]}

    assert request_types == {
        "missing_facts",
        "stale_evidence",
        "local_preview",
        "consequential_action",
        "manual_handoff",
    }
    for row in matrix["rows"]:
        assert row["source_evidence_ids"]
        assert all(assertion["passed"] is True for assertion in row["assertions"])
