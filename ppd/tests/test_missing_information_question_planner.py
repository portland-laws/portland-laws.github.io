from __future__ import annotations

import json
from pathlib import Path

from ppd.logic.missing_information_question_planner import plan_missing_information_questions


def _load_fixture(name: str) -> dict:
    fixture_path = Path(__file__).parent / "fixtures" / "missing_information_question_planner" / name
    return json.loads(fixture_path.read_text(encoding="utf-8"))


def test_planner_builds_minimal_ordered_questions_from_fixture() -> None:
    fixture = _load_fixture("basic_gap.json")

    plan = plan_missing_information_questions(
        fixture["process_model"],
        fixture["user_gap_analysis"],
    ).to_dict()

    assert plan["case_id"] == "case-001"
    assert plan["process_id"] == "residential-building-permit-demo"
    assert [question["category"] for question in plan["questions"]] == [
        "missing_fact",
        "missing_fact",
        "missing_document",
        "stale_evidence",
        "conflicting_evidence",
    ]
    assert plan["questions"][0]["prompt"] == "What is the project address for the permit?"
    assert plan["questions"][0]["answer_type"] == "postal_address"
    assert plan["questions"][0]["source_requirement_ids"] == ["req-address"]
    assert plan["next_safe_actions"] == [
        "ask_planned_missing_information_questions",
        "update_local_gap_analysis_from_user_answers",
    ]


def test_planner_refuses_forbidden_capabilities_without_creating_action_steps() -> None:
    fixture = _load_fixture("basic_gap.json")

    plan = plan_missing_information_questions(
        fixture["process_model"],
        fixture["user_gap_analysis"],
    ).to_dict()

    refused = set(plan["refused_capabilities"])
    assert "devhub" in refused
    assert "submit" in refused
    assert "certify" in refused
    assert "upload" in refused
    assert "schedule" in refused
    assert "cancel" in refused
    assert "payment" in refused or "pay fee" in refused

    rendered_plan = json.dumps(plan).lower()
    assert "ask_planned_missing_information_questions" in rendered_plan
    assert "open_devhub" not in rendered_plan
    assert "live_crawl" not in rendered_plan
    assert "submit_application" not in rendered_plan
    assert "enter_payment" not in rendered_plan


def test_planner_returns_reversible_draft_action_when_no_questions_are_needed() -> None:
    plan = plan_missing_information_questions(
        {"process_id": "demo-process", "required_user_facts": []},
        {"case_id": "case-ready", "process_id": "demo-process", "missing_facts": []},
    ).to_dict()

    assert plan["questions"] == []
    assert plan["next_safe_actions"] == ["prepare_reversible_local_draft_plan"]
