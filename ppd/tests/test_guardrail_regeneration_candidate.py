from __future__ import annotations

import json
from pathlib import Path

from ppd.logic.guardrail_regeneration_candidate import compile_guardrail_regeneration_candidate


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "guardrail_regeneration_candidate"


def _load_fixture(name: str) -> dict:
    with (FIXTURE_DIR / name).open(encoding="utf-8") as handle:
        return json.load(handle)


def test_candidate_packet_is_deterministic_and_does_not_replace_active_bundle() -> None:
    process_model_change = _load_fixture("process_model_change.json")

    first = compile_guardrail_regeneration_candidate(process_model_change)
    second = compile_guardrail_regeneration_candidate(process_model_change)

    assert first == second
    assert first["candidate_status"] == "draft_review_required"
    assert first["does_not_replace_active_bundle"] is True
    assert first["active_guardrail_bundle_id"] == process_model_change["active_guardrail_bundle_id"]
    assert first["candidate_id"].startswith("guardrail-candidate-")


def test_candidate_packet_compiles_impacted_change_categories() -> None:
    packet = compile_guardrail_regeneration_candidate(_load_fixture("process_model_change.json"))

    predicate_kinds = {predicate["kind"] for predicate in packet["draft_predicates"]}
    assert "requires_user_fact" in predicate_kinds
    assert "requires_document" in predicate_kinds
    assert "requires_file_rule" in predicate_kinds
    assert "action_gate" in predicate_kinds

    required_values = {predicate.get("value") for predicate in packet["draft_predicates"]}
    assert "supporting_documents_are_separate_pdfs" in required_values
    assert "application_forms_pdf" in required_values
    assert "applications_calculations_and_supporting_documents_uploaded_as_separate_pdfs" in required_values


def test_candidate_packet_adds_refusal_and_exact_confirmation_gates() -> None:
    packet = compile_guardrail_regeneration_candidate(_load_fixture("process_model_change.json"))

    refused_actions = {predicate["action"] for predicate in packet["refused_action_predicates"]}
    exact_actions = {predicate["action"] for predicate in packet["exact_confirmation_predicates"]}

    assert refused_actions == {"upload supporting documents", "submit permit application"}
    assert exact_actions == {"upload supporting documents", "submit permit application"}
    assert all(
        predicate["review_status"] == "draft_requires_human_review"
        for predicate in packet["refused_action_predicates"]
    )
    assert any(
        predicate["required_confirmation_text"] == "I confirm I am ready to submit this PP&D permit application."
        for predicate in packet["exact_confirmation_predicates"]
    )


def test_candidate_packet_tracks_unresolved_review_notes() -> None:
    packet = compile_guardrail_regeneration_candidate(_load_fixture("process_model_change.json"))

    note_ids = {note["note_id"] for note in packet["unresolved_review_notes"]}
    assert "human-review-required" in note_ids
    assert packet["source_evidence_ids"] == [
        "ppd-source-submit-plans-online#single-pdf-guidance",
        "ppd-source-devhub-guide-submit-permit-application#upload-step",
    ]
    assert packet["explanation_templates"]
