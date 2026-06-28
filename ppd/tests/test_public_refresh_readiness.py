from __future__ import annotations

import json
from pathlib import Path

import pytest

from ppd.extraction.public_refresh_readiness import ReadinessInputError, build_readiness_packet


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "public_refresh_readiness_v1" / "synthetic_rows.json"


def _load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_builds_fixture_first_readiness_packet_without_live_permissions() -> None:
    fixture = _load_fixture()

    packet = build_readiness_packet(
        fixture["archive_patch_preview_rows"],
        fixture["citation_impact_queue_rows"],
    )

    assert packet["schema_version"] == "public-refresh-normalized-document-extraction-readiness-v1"
    assert packet["input_policy"] == {
        "accepted_archive_rows": "synthetic inactive archive patch preview rows only",
        "accepted_citation_rows": "synthetic inactive citation impact queue rows only",
        "live_extraction": False,
        "live_crawling": False,
        "document_downloads": False,
        "raw_output_storage": False,
        "devhub_opened": False,
        "active_document_record_mutation": False,
        "official_actions": False,
    }
    assert [item[0] for item in packet["offline_validation_commands"]] == ["python3", "python3", "python3"]
    assert len(packet["planned_documents"]) == 3


def test_plans_routes_placeholders_and_review_holds() -> None:
    fixture = _load_fixture()

    packet = build_readiness_packet(
        fixture["archive_patch_preview_rows"],
        fixture["citation_impact_queue_rows"],
    )

    by_source = {item["source_id"]: item for item in packet["planned_documents"]}
    html_plan = by_source["src-ppd-html-apply-permits-preview"]
    pdf_plan = by_source["src-ppd-pdf-file-standards-preview"]
    form_plan = by_source["src-ppd-form-permit-application-preview"]

    assert html_plan["normalized_document_placeholder_id"].startswith("normdoc-placeholder-v1-")
    assert html_plan["extraction_route"]["route_name"] == "html_structure_and_links"
    assert pdf_plan["extraction_route"]["route_name"] == "pdf_text_tables_and_fields"
    assert form_plan["extraction_route"]["route_name"] == "pdf_text_tables_and_fields"
    assert pdf_plan["stale_source_hold"] is True
    assert pdf_plan["human_review_status"] == "hold_for_stale_source"
    assert packet["stale_source_holds"] == [
        {
            "source_id": "src-ppd-pdf-file-standards-preview",
            "canonical_url": "https://www.portland.gov/ppd/spp-file-naming-standards-preparing-pdfs",
            "hold_reason": "synthetic fixture marks source freshness unverified",
            "release_condition": "fresh synthetic inactive preview row with reviewed source freshness metadata",
        }
    ]


def test_citation_span_acceptance_and_unmatched_queue_routing() -> None:
    fixture = _load_fixture()

    packet = build_readiness_packet(
        fixture["archive_patch_preview_rows"],
        fixture["citation_impact_queue_rows"],
    )

    by_source = {item["source_id"]: item for item in packet["planned_documents"]}
    html_checks = by_source["src-ppd-html-apply-permits-preview"]["citation_span_acceptance_checks"]
    pdf_checks = by_source["src-ppd-pdf-file-standards-preview"]["citation_span_acceptance_checks"]

    assert html_checks[0]["accepted_for_planning"] is True
    assert pdf_checks[0]["accepted_for_planning"] is True
    assert packet["unmatched_citation_queue_rows"] == [
        {
            "source_id": "src-ppd-missing-preview",
            "impacted_requirement_id": "req-unmatched-citation-001",
            "accepted_for_planning": False,
            "reason": "source_not_in_inactive_archive_preview",
            "routing": "human_review_required",
        }
    ]
    assert packet["human_review_routing"]["citation_queue_triage"] == ["req-unmatched-citation-001"]


def test_rejects_non_synthetic_or_live_like_rows() -> None:
    fixture = _load_fixture()
    bad_archive_rows = list(fixture["archive_patch_preview_rows"])
    bad_archive_rows[0] = dict(bad_archive_rows[0], synthetic=False)

    with pytest.raises(ReadinessInputError, match="not marked synthetic"):
        build_readiness_packet(bad_archive_rows, fixture["citation_impact_queue_rows"])

    bad_citation_rows = list(fixture["citation_impact_queue_rows"])
    bad_citation_rows[0] = dict(bad_citation_rows[0], raw_output_ref="raw/live/output.html")

    with pytest.raises(ReadinessInputError, match="raw_output_ref"):
        build_readiness_packet(fixture["archive_patch_preview_rows"], bad_citation_rows)
