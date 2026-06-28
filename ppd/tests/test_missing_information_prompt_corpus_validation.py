from __future__ import annotations

from pathlib import Path

import pytest

from ppd.logic.missing_information_prompt_corpus_validation import (
    assert_valid_prompt_corpus,
    validate_prompt_corpus,
    validate_prompt_corpus_file,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "missing_information_prompt_corpora"


def issue_codes(corpus: dict) -> set[str]:
    return {issue.code for issue in validate_prompt_corpus(corpus)}


def cited_case(prompt: str, **overrides: object) -> dict:
    case = {
        "id": "case",
        "prompt": prompt,
        "citations": ["ppd-source"],
        "expected_refusal": True,
    }
    case.update(overrides)
    return {"cases": [case]}


def test_valid_fixture_has_no_validation_issues() -> None:
    assert validate_prompt_corpus_file(FIXTURE_DIR / "valid_corpus.json") == []


def test_rejects_uncited_prompt_case() -> None:
    corpus = {"cases": [{"id": "uncited", "prompt": "Ask for missing permit facts."}]}

    assert "missing_citation" in issue_codes(corpus)


def test_rejects_private_case_facts() -> None:
    corpus = cited_case("Ask about permit number 24-123456-000-00-CO at 1234 SE Main St.")

    assert "private_case_fact" in issue_codes(corpus)


def test_rejects_local_private_paths() -> None:
    corpus = cited_case("Use the applicant PDF at /Users/alex/Downloads/private-plan.pdf.")

    assert "local_private_path" in issue_codes(corpus)


def test_rejects_legal_or_permitting_outcome_guarantees() -> None:
    corpus = cited_case("Tell the user this permit will be approved after upload.")

    assert "outcome_guarantee" in issue_codes(corpus)


def test_rejects_raw_crawl_download_or_archive_references() -> None:
    corpus = cited_case("Base the prompt on the raw crawl archive_artifact_ref and downloaded HTML.")

    assert "raw_artifact_reference" in issue_codes(corpus)


def test_rejects_live_llm_or_devhub_execution_claims() -> None:
    corpus = cited_case("Say I logged in and clicked submit in DevHub during a live browser session.")

    assert "live_execution_claim" in issue_codes(corpus)


def test_rejects_unsafe_case_without_refusal_expectation() -> None:
    corpus = {
        "cases": [
            {
                "id": "no-refusal",
                "prompt": "Guarantee the application will be issued. Cite [ppd-source].",
                "citations": ["ppd-source"],
            }
        ]
    }

    assert "missing_refusal_expectation" in issue_codes(corpus)


@pytest.mark.parametrize(
    "kind",
    [
        "payment",
        "upload",
        "submission",
        "scheduling",
        "cancellation",
        "certification",
    ],
)
def test_rejects_enabled_consequential_controls(kind: str) -> None:
    corpus = cited_case(
        "Ask only for missing facts before any official action.",
        controls=[{"kind": kind, "label": kind.title(), "enabled": True}],
    )

    assert "enabled_consequential_control" in issue_codes(corpus)


def test_disabled_consequential_controls_are_allowed_when_case_is_otherwise_safe() -> None:
    corpus = {
        "cases": [
            {
                "id": "disabled-controls",
                "prompt": "Ask for the missing permit type and cite [ppd-source].",
                "citations": ["ppd-source"],
                "controls": [{"kind": "payment", "enabled": False}],
            }
        ]
    }

    assert validate_prompt_corpus(corpus) == []


def test_assert_valid_prompt_corpus_raises_with_issue_codes() -> None:
    corpus = {"cases": [{"id": "bad", "prompt": "Ask for missing permit facts."}]}

    with pytest.raises(ValueError, match="bad:missing_citation"):
        assert_valid_prompt_corpus(corpus)
