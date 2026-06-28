import json
from pathlib import Path


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "process_dependency_graph"
    / "synthetic_residential_fixture_replacement.json"
)


REQUIRED_KINDS = {
    "required_fact",
    "required_document",
    "deadline",
    "fee_trigger",
    "exception",
    "unsupported_path",
    "devhub_action_gate",
}


def load_fixture():
    with FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def test_fixture_declares_all_dependency_node_kinds():
    fixture = load_fixture()
    observed_kinds = {node["kind"] for node in fixture["nodes"]}

    assert REQUIRED_KINDS <= observed_kinds
    assert fixture["is_synthetic"] is True
    assert fixture["source_policy"] == {
        "live_crawl_required": False,
        "authenticated_devhub_required": False,
        "contains_private_values": False,
        "contains_raw_downloads": False,
    }


def test_dependency_edges_reference_known_nodes():
    fixture = load_fixture()
    node_ids = {node["id"] for node in fixture["nodes"]}

    assert fixture["edges"], "fixture should include graph edges"
    for edge in fixture["edges"]:
        assert edge["from"] in node_ids
        assert edge["to"] in node_ids
        assert edge["relationship"]


def test_devhub_action_gates_capture_attendance_and_confirmation_policy():
    fixture = load_fixture()
    gates = {
        node["id"]: node
        for node in fixture["nodes"]
        if node["kind"] == "devhub_action_gate"
    }

    assert gates["gate_attended_login"]["requires_attendance"] is True
    assert gates["gate_draft_fill"]["action_class"] == "reversible_draft"
    assert gates["gate_draft_fill"]["requires_exact_confirmation"] is False

    for gate_id in (
        "gate_submit_application",
        "gate_submit_payment",
        "gate_schedule_inspection",
    ):
        assert gates[gate_id]["requires_attendance"] is True
        assert gates[gate_id]["requires_exact_confirmation"] is True


def test_expected_guardrail_outcomes_cover_blocked_and_reversible_paths():
    fixture = load_fixture()
    outcomes = {outcome["case"]: outcome for outcome in fixture["expected_guardrail_outcomes"]}

    assert "missing_required_fact" in outcomes
    assert "owner_applicant_ready_for_draft" in outcomes
    assert "unsupported_scope" in outcomes
    assert "gate_draft_fill" in outcomes["owner_applicant_ready_for_draft"]["allowed_gate_ids"]
    assert "gate_submit_payment" in outcomes["owner_applicant_ready_for_draft"]["blocked_gate_ids"]
    assert "gate_submit_application" in outcomes["unsupported_scope"]["blocked_gate_ids"]
