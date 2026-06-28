from __future__ import annotations

import json
from pathlib import Path

from ppd.logic.agent_handoff_expectations import evaluate_matrix

FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "agent_handoff_transcripts"
    / "expectation_matrix.json"
)

REQUIRED_CASE_IDS = {
    "missing-facts-before-application-draft",
    "stale-evidence-refresh-needed",
    "changed-file-preparation-rules",
    "fee-payment-refusal",
    "correction-upload-handoff",
    "devhub-read-only-status-review",
    "reversible-local-preview",
    "manual-handoff-language-for-mfa-captcha-account",
}


def load_matrix() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_fixture_contains_required_synthetic_handoff_cases() -> None:
    matrix = load_matrix()

    assert matrix["matrix_id"]
    assert "No LLM calls" in matrix["non_goals"]
    assert "No DevHub launch" in matrix["non_goals"]
    assert "No private file reads" in matrix["non_goals"]

    case_ids = {case["case_id"] for case in matrix["cases"]}
    assert case_ids == REQUIRED_CASE_IDS


def test_all_fixture_transcripts_satisfy_expectations() -> None:
    matrix = load_matrix()

    issues = evaluate_matrix(matrix)

    assert issues == []


def test_fixture_matrix_is_self_contained_and_synthetic() -> None:
    matrix = load_matrix()
    serialized = json.dumps(matrix, sort_keys=True).casefold()

    forbidden_fragments = (
        "password",
        "cookie",
        "auth state",
        "trace.zip",
        "har file",
        "/users/",
        "c:\\",
        "payment submitted",
        "upload complete",
    )
    for fragment in forbidden_fragments:
        assert fragment not in serialized

    for case in matrix["cases"]:
        assert case["scenario"]
        assert case["transcript"]
        assert case["expected_disposition"] in case["transcript"]
