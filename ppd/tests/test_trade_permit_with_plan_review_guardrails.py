from __future__ import annotations

import json
from pathlib import Path
from typing import Any


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "guardrails"
    / "trade_permit_with_plan_review_guardrails.json"
)


EXACT_CONFIRMATIONS = {
    "submit_request": "I confirm submitting this trade permit with plan review request.",
    "pay_intake_fees": "I confirm paying intake fees for this trade permit with plan review request.",
    "upload_corrections": "I confirm uploading these corrections for the trade permit with plan review request.",
}


def load_fixture() -> dict[str, Any]:
    with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def evaluate_case(fixture: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    compiled = fixture["compiled_guardrails"]
    requested_action = case["requested_action"]
    known_facts = case.get("known_facts", {})
    documents = case.get("documents", {})
    confirmation = case.get("user_confirmation")

    missing_facts = [
        fact["id"]
        for fact in compiled["required_facts"]
        if requested_action in fact["blocks_actions"] and not known_facts.get(fact["id"])
    ]
    missing_documents = [
        document["id"]
        for document in compiled["required_documents"]
        if requested_action in document["blocks_actions"] and not documents.get(document["id"])
    ]

    stop_points: list[str] = []
    if not missing_facts and not missing_documents:
        for gate in compiled["action_gates"]:
            if gate["action"] != requested_action:
                continue
            if gate.get("requires_exact_confirmation") and confirmation != EXACT_CONFIRMATIONS[requested_action]:
                stop_points.append(gate["id"])

    return {
        "allowed": not missing_facts and not missing_documents and not stop_points,
        "missing_facts": missing_facts,
        "missing_documents": missing_documents,
        "stop_points": stop_points,
    }


def test_trade_plan_review_guardrail_fixture_shape() -> None:
    fixture = load_fixture()

    assert fixture["process_id"] == "trade_permit_with_plan_review"
    assert fixture["compiled_guardrails"]["required_facts"]
    assert fixture["compiled_guardrails"]["required_documents"]
    assert fixture["compiled_guardrails"]["action_gates"]
    assert fixture["cases"]

    source_ids = {source["source_id"] for source in fixture["source_basis"]}
    assert "devhub_application_guidance_trade_plan_review" in source_ids
    assert "devhub_faq_trade_plan_review_payments_corrections" in source_ids


def test_trade_plan_review_missing_fact_guardrails_are_user_questions() -> None:
    fixture = load_fixture()
    facts = fixture["compiled_guardrails"]["required_facts"]

    fact_ids = {fact["id"] for fact in facts}
    assert {
        "project_address",
        "trade_scope",
        "project_description",
        "contractor_license_status",
    }.issubset(fact_ids)
    assert all(fact["missing_behavior"] == "ask_user" for fact in facts)

    case = next(item for item in fixture["cases"] if item["id"] == "missing_trade_plan_review_facts")
    assert evaluate_case(fixture, case) == case["expected"]


def test_trade_plan_review_required_document_guardrails_block_submission() -> None:
    fixture = load_fixture()
    documents = fixture["compiled_guardrails"]["required_documents"]

    document_ids = {document["id"] for document in documents}
    assert {"application_pdf", "drawing_plan_pdf", "supporting_documents_pdf"}.issubset(document_ids)
    assert all(document["file_rule"] == "document_is_pdf(file)" for document in documents)
    assert all("submit_request" in document["blocks_actions"] for document in documents)

    case = next(item for item in fixture["cases"] if item["id"] == "missing_required_plan_review_documents")
    assert evaluate_case(fixture, case) == case["expected"]


def test_trade_plan_review_payment_has_financial_stop_point() -> None:
    fixture = load_fixture()
    payment_gate = next(
        gate for gate in fixture["compiled_guardrails"]["action_gates"] if gate["id"] == "intake_fee_payment_stop"
    )

    assert payment_gate["action"] == "pay_intake_fees"
    assert payment_gate["classification"] == "financial"
    assert payment_gate["requires_exact_confirmation"] is True
    assert payment_gate["requires_payment_preview"] is True

    case = next(item for item in fixture["cases"] if item["id"] == "payment_requires_financial_confirmation")
    assert evaluate_case(fixture, case) == case["expected"]


def test_trade_plan_review_correction_upload_requires_confirmation_gate() -> None:
    fixture = load_fixture()
    correction_gate = next(
        gate
        for gate in fixture["compiled_guardrails"]["action_gates"]
        if gate["id"] == "correction_upload_confirmation"
    )

    assert correction_gate["action"] == "upload_corrections"
    assert correction_gate["classification"] == "potentially_consequential"
    assert correction_gate["requires_exact_confirmation"] is True
    assert correction_gate["requires_document_inventory"] is True

    case = next(item for item in fixture["cases"] if item["id"] == "correction_upload_requires_exact_confirmation")
    assert evaluate_case(fixture, case) == case["expected"]
