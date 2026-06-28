from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from ppd.process_model_impact_packet import (
    FORBIDDEN_OFFICIAL_ACTIONS,
    ProcessModelImpactPacketError,
    build_process_model_impact_packet,
    build_process_model_impact_packet_from_fixture,
    load_process_model_impact_fixture,
    validate_process_model_impact_packet,
)


FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "process_model_impact"
    / "synthetic_reviewed_requirement_changes.json"
)


def test_fixture_first_impact_packet_maps_reviewed_changes_into_one_process_model() -> None:
    packet = build_process_model_impact_packet_from_fixture(FIXTURE)

    model = packet["process_model"]
    linkage = packet["guardrail_bundle_linkage"]

    assert packet["packet_type"] == "fixture_first_process_model_impact_packet"
    assert packet["fixture_first"] is True
    assert packet["metadata_only"] is True
    assert packet["live_services_called"] is False
    assert packet["official_actions_enabled"] is False
    assert packet["enabled_official_actions"] == []
    assert set(packet["disabled_official_actions"]) == FORBIDDEN_OFFICIAL_ACTIONS
    assert packet["production_status"] == "not_ready_for_production"
    assert set(packet["unresolved_blockers"]) == FORBIDDEN_OFFICIAL_ACTIONS

    assert model["process_id"] == "synthetic-residential-alteration-impact-model"
    assert model["guardrail_bundle_id"] == "guardrail-bundle-synthetic-residential-alteration-impact-v1"
    assert linkage["guardrail_bundle_id"] == model["guardrail_bundle_id"]
    assert linkage["process_id"] == model["process_id"]

    assert "chg-unreviewed-note-ignored" not in model["requirement_change_ids"]
    assert model["affected_stages"] == [
        "property lookup",
        "eligibility screening",
        "document preparation",
        "acknowledgement/certification review",
    ]
    assert {fact["fact_key"] for fact in model["required_user_facts"]} == {
        "property_address_or_public_property_reference",
        "residential_alteration_scope",
    }
    assert {document["document_key"] for document in model["required_documents"]} == {
        "combined_drawing_plan_pdf",
        "separate_supporting_document_pdfs",
    }
    assert {blocker["blocked_action"] for blocker in model["guardrail_bundle_blockers"]} == FORBIDDEN_OFFICIAL_ACTIONS
    assert set(linkage["blocked_actions"]) == FORBIDDEN_OFFICIAL_ACTIONS


def test_impact_packet_records_unsupported_paths_and_devhub_surface_references() -> None:
    packet = build_process_model_impact_packet_from_fixture(FIXTURE)
    model = packet["process_model"]

    unsupported_paths = {item["path"] for item in model["unsupported_paths"]}
    assert "Do not split drawing sheets into multiple plan PDFs for this synthetic process model." in unsupported_paths
    assert (
        "Consequential DevHub workflows require attended handoff and exact confirmation outside this fixture-first packet."
        in unsupported_paths
    )

    assert model["devhub_surface_refs"] == [
        "devhub-application-questionnaire",
        "devhub-application-start",
        "devhub-attachment-list",
        "devhub-cancellation-or-withdrawal",
        "devhub-fee-payment",
        "devhub-inspection-scheduling",
        "devhub-property-search",
        "devhub-submit-application",
        "devhub-upload-staging",
    ]


def test_impact_packet_records_cited_stage_mappings_for_every_reviewed_change() -> None:
    packet = build_process_model_impact_packet_from_fixture(FIXTURE)
    model = packet["process_model"]

    mapped_change_ids = {mapping["requirement_change_id"] for mapping in model["stage_mappings"]}

    assert mapped_change_ids == set(model["requirement_change_ids"])
    assert all(mapping["source_evidence_ids"] for mapping in model["stage_mappings"])


def test_impact_packet_rejects_uncommitted_evidence_ids() -> None:
    fixture = load_process_model_impact_fixture(FIXTURE)
    fixture["reviewed_requirement_changes"][0]["source_evidence_ids"] = ["src-not-committed"]

    with pytest.raises(ProcessModelImpactPacketError, match="uncommitted evidence ids"):
        build_process_model_impact_packet(fixture)


def test_impact_packet_rejects_enabled_official_actions() -> None:
    fixture = load_process_model_impact_fixture(FIXTURE)
    fixture["reviewed_requirement_changes"][0]["conditions"]["enabled_official_actions"] = ["submission"]

    with pytest.raises(ProcessModelImpactPacketError, match="attempts to enable official actions"):
        build_process_model_impact_packet(fixture)


def test_impact_packet_rejects_private_or_raw_runtime_fields() -> None:
    fixture = load_process_model_impact_fixture(FIXTURE)
    fixture["raw_html"] = "not committed"

    with pytest.raises(ProcessModelImpactPacketError, match="private or raw field"):
        build_process_model_impact_packet(fixture)


def test_impact_packet_rejects_missing_stage_mappings() -> None:
    packet = build_process_model_impact_packet_from_fixture(FIXTURE)
    unsafe = deepcopy(packet)
    unsafe["process_model"]["stage_mappings"] = unsafe["process_model"]["stage_mappings"][:-1]

    with pytest.raises(ProcessModelImpactPacketError, match="missing stage mapping"):
        validate_process_model_impact_packet(unsafe)


def test_impact_packet_rejects_uncited_requirement_links() -> None:
    packet = build_process_model_impact_packet_from_fixture(FIXTURE)
    unsafe = deepcopy(packet)
    del unsafe["process_model"]["required_documents"][0]["source_evidence_ids"]

    with pytest.raises(ProcessModelImpactPacketError, match="requirement link lacks source_evidence_ids"):
        validate_process_model_impact_packet(unsafe)


def test_impact_packet_rejects_stale_source_references() -> None:
    fixture = load_process_model_impact_fixture(FIXTURE)
    fixture["source_evidence"][0]["freshness_status"] = "stale"

    with pytest.raises(ProcessModelImpactPacketError, match="stale source evidence"):
        build_process_model_impact_packet(fixture)


def test_impact_packet_rejects_private_case_facts() -> None:
    fixture = load_process_model_impact_fixture(FIXTURE)
    fixture["reviewed_requirement_changes"][0]["conditions"]["case_fact_value"] = "123 Private Street"

    with pytest.raises(ProcessModelImpactPacketError, match="private or raw field"):
        build_process_model_impact_packet(fixture)


def test_impact_packet_rejects_consequential_action_enablement() -> None:
    packet = build_process_model_impact_packet_from_fixture(FIXTURE)
    unsafe = deepcopy(packet)
    unsafe["process_model"]["submission_enabled"] = True

    with pytest.raises(ProcessModelImpactPacketError, match="consequential action enablement"):
        validate_process_model_impact_packet(unsafe)


def test_impact_packet_rejects_production_ready_status_with_unresolved_blockers() -> None:
    packet = build_process_model_impact_packet_from_fixture(FIXTURE)
    unsafe = deepcopy(packet)
    unsafe["production_status"] = "ready_for_production"

    with pytest.raises(ProcessModelImpactPacketError, match="ready-for-production status"):
        validate_process_model_impact_packet(unsafe)
