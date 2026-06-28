from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from ppd.logic.process_model_impact_rehearsal import (
    RehearsalInputError,
    build_process_model_impact_rehearsal_packet,
    load_json_fixture,
)


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "process_model_impact_rehearsal"
    / "synthetic_packet.json"
)


def test_builds_cited_process_model_impact_rehearsal_without_mutating_inputs() -> None:
    source_packet = load_json_fixture(FIXTURE_PATH)
    original_packet = deepcopy(source_packet)

    rehearsal = build_process_model_impact_rehearsal_packet(source_packet)

    assert source_packet == original_packet
    assert rehearsal["packet_type"] == "fixture_first_process_model_impact_rehearsal"
    assert rehearsal["process_mutation_policy"] == {
        "fixture_only": True,
        "blocked_operations": [
            "compile_guardrails",
            "promote_guardrail_bundle",
            "change_active_process_model",
            "write_process_model_fixture",
        ],
        "compiled": False,
        "promoted": False,
        "active_process_models_changed": False,
    }
    assert rehearsal["no_process_mutation_attestation"]["input_unchanged"] is True

    process_ids = {process["process_id"] for process in rehearsal["affected_processes"]}
    assert process_ids == {
        "single_pdf_process.synthetic",
        "trade_permit_with_plan_review.synthetic",
    }


def test_rehearsal_summarizes_required_fact_document_unsupported_and_owner_impacts() -> None:
    rehearsal = build_process_model_impact_rehearsal_packet(load_json_fixture(FIXTURE_PATH))
    by_process = {process["process_id"]: process for process in rehearsal["affected_processes"]}

    single_pdf = by_process["single_pdf_process.synthetic"]
    assert single_pdf["cited_affected_stages"] == [
        {
            "stage": "document preparation",
            "requirement_ids": ["REQ-SYN-PLAN-PDF-SEPARATION"],
            "citations": ["ppd-submit-plans-online#single-pdf-process"],
        }
    ]
    assert single_pdf["required_fact_changes"]["add"] == [
        "drawing_pages_combined_into_single_pdf",
        "project_has_plan_review",
    ]
    assert single_pdf["required_fact_changes"]["review"] == [
        "supporting_documents_uploaded_as_separate_pdfs"
    ]
    assert single_pdf["reviewer_owners"] == ["ppd-document-rules-reviewer"]
    assert single_pdf["no_process_mutation_attestation"]["compiled"] is False
    assert single_pdf["no_process_mutation_attestation"]["promoted"] is False

    trade = by_process["trade_permit_with_plan_review.synthetic"]
    assert trade["reviewer_owners"] == [
        "ppd-application-data-reviewer",
        "ppd-process-path-reviewer",
    ]
    assert trade["required_fact_changes"]["add"] == [
        "devhub_dynamic_questions_reviewed",
        "permit_path_confirmed_devhub_supported",
    ]
    assert trade["unsupported_path_notes"] == [
        {
            "requirement_id": "REQ-SYN-NON-DEVHUB-PATH",
            "note": "Do not assume DevHub supports this request type until the fixture path is confirmed by cited public guidance.",
            "citations": ["ppd-devhub-faq#not-all-permits"],
        },
        {
            "requirement_id": "REQ-SYN-NON-DEVHUB-PATH",
            "note": "Some permit types may require email or another official path instead of DevHub; rehearsal must flag this before draft planning.",
            "citations": ["ppd-devhub-faq#not-all-permits"],
        },
    ]
    assert {
        (impact["document"], impact["impact_type"])
        for impact in trade["document_rule_impacts"]
    } == {("application_form_pdf", "change")}


def test_rehearsal_reports_reviewed_out_candidates_as_unsupported() -> None:
    rehearsal = build_process_model_impact_rehearsal_packet(load_json_fixture(FIXTURE_PATH))

    assert rehearsal["unsupported_requirement_candidates"] == [
        {
            "process_id": "single_pdf_process.synthetic",
            "requirement_id": "REQ-SYN-UNREVIEWED-FEE-TEXT",
            "review_status": "rejected_needs_source",
            "reason": "candidate was not approved for impact rehearsal",
        }
    ]


def test_rehearsal_rejects_compile_or_promotion_inputs() -> None:
    packet = load_json_fixture(FIXTURE_PATH)
    packet["guardrail_recompilation_rehearsal_packet"]["compiled"] = True

    _assert_rejected(packet, "compiled=false")


def test_rehearsal_rejects_uncited_stage_impacts() -> None:
    packet = load_json_fixture(FIXTURE_PATH)
    packet["reviewed_synthetic_requirement_candidates"][0]["source_evidence_ids"] = []

    _assert_rejected(packet, "requires source_evidence_ids")


def test_rehearsal_rejects_uncited_document_rule_impacts() -> None:
    packet = load_json_fixture(FIXTURE_PATH)
    packet["guardrail_recompilation_rehearsal_packet"]["predicate_impacts"][0]["citation_ids"] = []

    _assert_rejected(packet, "requires citation_ids")


def test_rehearsal_rejects_unknown_process_or_requirement_ids() -> None:
    packet = load_json_fixture(FIXTURE_PATH)
    packet["reviewed_synthetic_requirement_candidates"][0]["process_id"] = "unknown.process"

    _assert_rejected(packet, "unknown process_id")

    packet = load_json_fixture(FIXTURE_PATH)
    packet["guardrail_recompilation_rehearsal_packet"]["predicate_impacts"][0]["requirement_id"] = "REQ-UNKNOWN"

    _assert_rejected(packet, "unknown requirement_id")


def test_rehearsal_rejects_stale_current_evidence_without_acknowledgement() -> None:
    packet = load_json_fixture(FIXTURE_PATH)
    packet["current_source_evidence"] = [
        {
            "source_evidence_id": "ppd-submit-plans-online#single-pdf-process",
            "freshness_status": "stale",
        }
    ]

    _assert_rejected(packet, "stale-current evidence requires explicit acknowledgement")

    packet["stale_current_evidence_acknowledgement"] = {
        "acknowledged": True,
        "reviewer_owner": "ppd-source-freshness-reviewer",
    }
    build_process_model_impact_rehearsal_packet(packet)


def test_rehearsal_rejects_private_case_facts_live_execution_and_outcome_guarantees() -> None:
    packet = load_json_fixture(FIXTURE_PATH)
    packet["private_case_facts"] = {"property_address": "123 Private St"}
    _assert_rejected(packet, "private case facts")

    packet = load_json_fixture(FIXTURE_PATH)
    packet["live_crawler_execution"] = True
    _assert_rejected(packet, "live compiler or crawler execution")

    packet = load_json_fixture(FIXTURE_PATH)
    packet["review_note"] = "This permit will be approved after the rehearsal."
    _assert_rejected(packet, "outcome guarantees")


def test_rehearsal_rejects_missing_reviewer_owner_and_active_mutation_flags() -> None:
    packet = load_json_fixture(FIXTURE_PATH)
    packet["reviewed_synthetic_requirement_candidates"][0]["reviewer_owner"] = ""
    _assert_rejected(packet, "missing reviewer_owner")

    packet = load_json_fixture(FIXTURE_PATH)
    packet["active_process_model_mutated"] = True
    _assert_rejected(packet, "active process-model mutation")


def _assert_rejected(packet: dict, expected: str) -> None:
    try:
        build_process_model_impact_rehearsal_packet(packet)
    except RehearsalInputError as exc:
        assert expected in str(exc)
    else:
        raise AssertionError(f"expected RehearsalInputError containing {expected!r}")
