from __future__ import annotations

import pytest

from ppd.logic.guardrail_explanation_packet import (
    MissingCitationError,
    render_guardrail_explanation_packet,
    render_or_block_guardrail_explanation_packet,
)


def test_renderer_is_deterministic_and_cited() -> None:
    guardrail = {
        "guardrail_bundle_id": "bundle-demo",
        "process_id": "demo-process",
        "summary": "Demo guardrail summary.",
        "blocked_actions": [
            {
                "id": "submit",
                "label": "Do not submit",
                "reason": "Submission requires user attendance.",
                "citation_ids": ["ev-submit"],
            }
        ],
    }
    next_safe_action = {
        "actions": [
            {
                "id": "ask-address",
                "label": "Ask for the project address",
                "explanation": "The address is needed before draft work.",
                "citation_ids": ["ev-address"],
            }
        ]
    }
    question_plan = {
        "questions": [
            {
                "id": "q-address",
                "question": "What is the project address?",
                "citation_ids": ["ev-address"],
            }
        ]
    }
    evidence_pack = {
        "evidence": [
            {
                "evidence_id": "ev-address",
                "source_id": "source-devhub-guide",
                "title": "DevHub guide",
                "url": "https://www.portland.gov/ppd/devhub-guide-submit-permit-application",
                "quote": "Applications require project information.",
            },
            {
                "evidence_id": "ev-submit",
                "source_id": "source-devhub-guide",
                "title": "DevHub guide",
                "url": "https://www.portland.gov/ppd/devhub-guide-submit-permit-application",
                "quote": "Submission is an official workflow step.",
            },
        ]
    }

    first = render_guardrail_explanation_packet(
        guardrail=guardrail,
        next_safe_action=next_safe_action,
        evidence_pack=evidence_pack,
        question_plan=question_plan,
    )
    second = render_guardrail_explanation_packet(
        guardrail=guardrail,
        next_safe_action=next_safe_action,
        evidence_pack=evidence_pack,
        question_plan=question_plan,
    )

    assert first == second
    assert first["status"] == "ready"
    assert [citation["evidence_id"] for citation in first["citations"]] == ["ev-address", "ev-submit"]
    assert first["blocked_actions"][0]["citations"][0]["evidence_id"] == "ev-submit"


def test_renderer_fails_closed_on_missing_citation() -> None:
    guardrail = {
        "guardrail_bundle_id": "bundle-demo",
        "process_id": "demo-process",
        "blocked_actions": [{"id": "submit", "citation_ids": ["missing-evidence"]}],
    }

    with pytest.raises(MissingCitationError):
        render_guardrail_explanation_packet(
            guardrail=guardrail,
            next_safe_action={"actions": []},
            evidence_pack={"evidence": []},
            question_plan={"questions": []},
        )

    blocked = render_or_block_guardrail_explanation_packet(
        guardrail=guardrail,
        next_safe_action={"actions": []},
        evidence_pack={"evidence": []},
        question_plan={"questions": []},
    )

    assert blocked["status"] == "blocked_missing_citations"
    assert blocked["citations"] == []
