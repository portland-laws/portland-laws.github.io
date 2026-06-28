from __future__ import annotations

import copy
import json
from pathlib import Path

from ppd.logic.stale_predicate_remediation_candidate import build_stale_predicate_remediation_candidate
from ppd.validation.stale_predicate_remediation_candidate import (
    finding_codes,
    require_valid_stale_predicate_remediation_candidate,
    validate_stale_predicate_remediation_candidate,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "stale_predicate_remediation_candidate"


def _load_fixture() -> dict:
    with (FIXTURE_DIR / "normalized_citation_evidence_packet.json").open(encoding="utf-8") as handle:
        return json.load(handle)


def test_candidate_is_deterministic_and_preserves_active_bundle_input() -> None:
    fixture = _load_fixture()
    original_active_bundle = copy.deepcopy(fixture["active_guardrail_bundle"])

    first = build_stale_predicate_remediation_candidate(fixture)
    second = build_stale_predicate_remediation_candidate(fixture)

    assert first == second
    assert fixture["active_guardrail_bundle"] == original_active_bundle
    assert first["candidate_status"] == "draft_requires_human_review"
    assert first["candidate_mode"] == "fixture_first_review_only"
    assert first["does_not_replace_active_bundle"] is True
    assert first["active_bundle_mutated"] is False
    assert "active_guardrail_bundle" not in first


def test_maps_normalized_citation_evidence_to_all_stale_guardrail_fix_categories() -> None:
    packet = build_stale_predicate_remediation_candidate(_load_fixture())

    assert [item["target_item_id"] for item in packet["draft_predicate_fixes"]] == ["pred-single-pdf-required"]
    assert [item["target_item_id"] for item in packet["draft_explanation_template_fixes"]] == ["explain-single-pdf-required"]
    assert [item["target_item_id"] for item in packet["draft_refused_action_rule_fixes"]] == ["refuse-submit-application"]
    assert [item["target_item_id"] for item in packet["draft_exact_confirmation_gate_fixes"]] == ["confirm-submit-application"]

    predicate_fix = packet["draft_predicate_fixes"][0]
    assert predicate_fix["draft_fix"]["predicate"] == "requires_drawing_plans_in_one_pdf_and_supporting_documents_as_separate_pdfs"
    assert predicate_fix["normalized_citation_evidence"][0]["citation_span_id"] == "submit-plans-online#single-pdf-process"

    explanation_fix = packet["draft_explanation_template_fixes"][0]
    assert "separate PDFs" in explanation_fix["draft_fix"]["template"]

    refused_fix = packet["draft_refused_action_rule_fixes"][0]
    assert refused_fix["draft_fix"]["action"] == "submit permit application"
    assert "cannot submit" in refused_fix["draft_fix"]["refusal_reason"]

    confirmation_fix = packet["draft_exact_confirmation_gate_fixes"][0]
    assert confirmation_fix["draft_fix"]["required_confirmation_text"] == "I confirm I am ready to submit this PP&D permit application."


def test_preserves_unresolved_human_review_notes() -> None:
    packet = build_stale_predicate_remediation_candidate(_load_fixture())

    assert packet["unresolved_human_review_notes"]
    assert {note["status"] for note in packet["unresolved_human_review_notes"]} == {"unresolved"}
    note_ids = {note["note_id"] for note in packet["unresolved_human_review_notes"]}
    assert "changed-guidance-review-required" in note_ids
    assert "review-evidence-submit-application-confirmation" in note_ids


def test_valid_candidate_passes_validation() -> None:
    packet = build_stale_predicate_remediation_candidate(_load_fixture())

    assert validate_stale_predicate_remediation_candidate(packet) == []
    require_valid_stale_predicate_remediation_candidate(packet)


def test_validation_rejects_active_bundle_replacement_content() -> None:
    packet = build_stale_predicate_remediation_candidate(_load_fixture())
    packet["active_guardrail_bundle"] = {"guardrail_bundle_id": "replacement"}

    codes = finding_codes(validate_stale_predicate_remediation_candidate(packet))

    assert "active_bundle_mutation" in codes


def test_validation_rejects_resolved_human_review_notes() -> None:
    packet = build_stale_predicate_remediation_candidate(_load_fixture())
    packet["unresolved_human_review_notes"][0]["status"] = "resolved"

    codes = finding_codes(validate_stale_predicate_remediation_candidate(packet))

    assert "resolved_human_review_note" in codes


def test_validation_rejects_uncited_draft_fix() -> None:
    packet = build_stale_predicate_remediation_candidate(_load_fixture())
    packet["draft_predicate_fixes"][0]["normalized_citation_evidence"] = []

    codes = finding_codes(validate_stale_predicate_remediation_candidate(packet))

    assert "missing_normalized_citation_evidence" in codes
