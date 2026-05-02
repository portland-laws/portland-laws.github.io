"""Tests for fixture-only PP&D missing-information response planning."""

from __future__ import annotations

import json
from pathlib import Path

from ppd.logic.missing_information_response_plan import (
    FORBIDDEN_QUESTION_TERMS,
    build_missing_information_questions,
    validate_missing_information_response_plan,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "agent_missing_information_response_plan.json"


def load_fixture() -> dict:
    with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def test_agent_missing_information_response_plan_fixture_is_valid() -> None:
    fixture = load_fixture()

    assert validate_missing_information_response_plan(fixture) == []


def test_agent_missing_information_response_plan_derives_all_question_types() -> None:
    fixture = load_fixture()
    questions = build_missing_information_questions(fixture)

    assert {question.question_type for question in questions} == {
        "unresolved_fact",
        "required_document_placeholder",
        "stale_evidence",
        "default_stop_gate",
    }
    assert len(questions) == 6
    assert all(question.prompt.endswith("?") for question in questions)
    assert all(question.evidence_ids for question in questions)


def test_agent_missing_information_questions_do_not_suggest_prohibited_actions() -> None:
    fixture = load_fixture()
    questions = build_missing_information_questions(fixture)

    for question in questions:
        lowered_prompt = question.prompt.lower()
        for forbidden_term in FORBIDDEN_QUESTION_TERMS:
            assert forbidden_term not in lowered_prompt


def test_agent_missing_information_response_plan_rejects_unknown_evidence() -> None:
    fixture = load_fixture()
    fixture["unresolvedFacts"][0] = dict(fixture["unresolvedFacts"][0])
    fixture["unresolvedFacts"][0]["evidenceIds"] = ["missing_public_evidence"]

    errors = validate_missing_information_response_plan(fixture)

    assert any("unknown evidence id missing_public_evidence" in error for error in errors)
