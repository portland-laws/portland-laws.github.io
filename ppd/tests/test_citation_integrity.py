from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ppd.citation_integrity import assert_citation_integrity, validate_citation_integrity


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "citation_integrity" / "synthetic_ppd_citations.json"


def load_fixture() -> dict:
    with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def issue_messages(document: dict) -> list[str]:
    return [f"{issue.path}: {issue.message}" for issue in validate_citation_integrity(document)]


def test_committed_synthetic_fixture_passes_citation_integrity() -> None:
    document = load_fixture()

    assert validate_citation_integrity(document) == []
    assert_citation_integrity(document)


def test_every_checked_section_requires_citations() -> None:
    document = load_fixture()
    document["requirements"][0]["citations"] = []

    messages = issue_messages(document)

    assert "requirements[0].citations: at least one citation is required" in messages


def test_unknown_evidence_id_is_rejected() -> None:
    document = load_fixture()
    document["guardrail_predicates"][0]["citations"][0]["evidence_id"] = "synthetic-evidence:missing"

    messages = issue_messages(document)

    assert "guardrail_predicates[0].citations[0].evidence_id: unknown evidence_id" in messages


def test_unknown_span_id_is_rejected_for_known_evidence() -> None:
    document = load_fixture()
    document["next_safe_action_explanations"][0]["citations"][0]["span_id"] = "span:missing"

    messages = issue_messages(document)

    assert "next_safe_action_explanations[0].citations[0].span_id: unknown span_id for evidence_id" in messages


def test_evidence_must_be_committed_and_synthetic() -> None:
    document = load_fixture()
    broken_document = copy.deepcopy(document)
    broken_document["evidence"][0]["committed"] = False
    broken_document["evidence"][1]["synthetic"] = False

    messages = issue_messages(broken_document)

    assert "evidence[0].committed: evidence must be marked committed" in messages
    assert "evidence[1].synthetic: evidence must be marked synthetic" in messages


def test_assertion_error_contains_stable_issue_text() -> None:
    document = load_fixture()
    document["process_model_rules"][0].pop("citations")

    with pytest.raises(AssertionError) as exc_info:
        assert_citation_integrity(document)

    assert "process_model_rules[0].citations: at least one citation is required" in str(exc_info.value)
