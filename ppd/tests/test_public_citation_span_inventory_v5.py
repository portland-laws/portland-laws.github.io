from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from ppd.agent_readiness.public_citation_span_inventory_v5 import (
    EXPECTED_VALIDATION_COMMANDS,
    build_public_citation_span_inventory_v5,
    build_public_citation_span_inventory_v5_from_normalized_fixture,
    validate_public_citation_span_inventory_v5,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "public_metadata_manifest_dry_run_v5" / "manifest.json"


def test_builds_fixture_first_public_citation_span_inventory_v5() -> None:
    inventory = build_public_citation_span_inventory_v5_from_normalized_fixture(FIXTURE_PATH)

    assert inventory["inventory_version"] == "public-citation-span-inventory-v5"
    assert inventory["mode"] == "fixture_first_normalized_public_document_records_only"
    assert inventory["source_ids"] == [
        "ppd-fee-payment-guide-pdf",
        "ppd-online-tools-overview",
        "ppd-permit-application-form",
    ]
    assert inventory["document_ids"] == [
        "docrec-v5-ppd-fee-payment-guide-pdf",
        "docrec-v5-ppd-online-tools-overview",
        "docrec-v5-ppd-permit-application-form",
    ]
    assert inventory["document_record_refs"] == [
        "document-record://public-dry-run-v5/docrec-v5-ppd-fee-payment-guide-pdf",
        "document-record://public-dry-run-v5/docrec-v5-ppd-online-tools-overview",
        "document-record://public-dry-run-v5/docrec-v5-ppd-permit-application-form",
    ]
    assert inventory["row_count"] == 3
    assert inventory["validation_commands"] == [list(command) for command in EXPECTED_VALIDATION_COMMANDS]
    assert inventory["attestations"] == {
        "live_crawl_performed": False,
        "document_downloaded": False,
        "raw_body_persisted": False,
        "devhub_opened": False,
        "legal_or_permitting_guarantee": False,
        "active_mutation_enabled": False,
    }


def test_maps_requirement_ready_span_fields_by_source_and_document() -> None:
    inventory = build_public_citation_span_inventory_v5_from_normalized_fixture(FIXTURE_PATH)
    row = inventory["spans_by_source_id"]["ppd-online-tools-overview"]["docrec-v5-ppd-online-tools-overview"][0]

    assert row["source_id"] == "ppd-online-tools-overview"
    assert row["document_id"] == "docrec-v5-ppd-online-tools-overview"
    assert row["document_record_ref"] == "document-record://public-dry-run-v5/docrec-v5-ppd-online-tools-overview"
    assert row["page_or_section_anchor"] == "section:ppd-online-tools-overview-section-1"
    assert row["quoted_text_placeholder"] == "placeholder:quoted-text-not-stored-fixture-only"
    assert row["normalized_text_placeholder"] == "placeholder:normalized-text-pending-requirement-extraction"
    assert row["extraction_confidence"] == "synthetic-metadata-high"
    assert row["stale_source_hold"] == "hold_until_public_source_freshness_reviewed"
    assert row["reviewer_routing"] == ["public_citation_span_reviewer", "requirement_extraction_reviewer"]
    assert row["rollback_notes"]
    assert row["live_crawl_performed"] is False
    assert row["document_downloaded"] is False
    assert row["raw_body_persisted"] is False
    assert row["devhub_opened"] is False
    assert row["legal_or_permitting_guarantee"] is False
    assert row["active_mutation_enabled"] is False


def test_pdf_rows_use_page_anchor_and_route_to_extraction_reviewer() -> None:
    inventory = build_public_citation_span_inventory_v5_from_normalized_fixture(FIXTURE_PATH)
    row = inventory["spans_by_source_id"]["ppd-fee-payment-guide-pdf"]["docrec-v5-ppd-fee-payment-guide-pdf"][0]

    assert row["page_or_section_anchor"] == "page:1"
    assert "pdf_or_form_extraction_reviewer" in row["reviewer_routing"]
    assert row["extraction_confidence"] == "synthetic-metadata-medium"


@pytest.mark.parametrize("key", ["source_ids", "document_ids", "document_record_refs"])
def test_inventory_validator_rejects_missing_top_level_lists(key: str) -> None:
    inventory = build_public_citation_span_inventory_v5_from_normalized_fixture(FIXTURE_PATH)
    inventory[key] = []

    with pytest.raises(ValueError, match=key):
        validate_public_citation_span_inventory_v5(inventory)


def test_inventory_validator_rejects_missing_document_record_references() -> None:
    inventory = build_public_citation_span_inventory_v5_from_normalized_fixture(FIXTURE_PATH)
    row = inventory["spans_by_source_id"]["ppd-online-tools-overview"]["docrec-v5-ppd-online-tools-overview"][0]
    row.pop("document_record_ref")

    with pytest.raises(ValueError, match="document_record_ref"):
        validate_public_citation_span_inventory_v5(inventory)


def test_inventory_validator_rejects_missing_citation_span_rows() -> None:
    inventory = build_public_citation_span_inventory_v5_from_normalized_fixture(FIXTURE_PATH)
    inventory["spans_by_source_id"]["ppd-online-tools-overview"]["docrec-v5-ppd-online-tools-overview"] = []

    with pytest.raises(ValueError, match="citation span rows"):
        validate_public_citation_span_inventory_v5(inventory)


@pytest.mark.parametrize("field", ["source_id", "document_id"])
def test_inventory_validator_rejects_missing_row_source_or_document_ids(field: str) -> None:
    inventory = build_public_citation_span_inventory_v5_from_normalized_fixture(FIXTURE_PATH)
    row = inventory["spans_by_source_id"]["ppd-online-tools-overview"]["docrec-v5-ppd-online-tools-overview"][0]
    row[field] = ""

    with pytest.raises(ValueError, match=field):
        validate_public_citation_span_inventory_v5(inventory)


@pytest.mark.parametrize(
    "field, value, match",
    [
        ("page_or_section_anchor", "", "page_or_section_anchor"),
        ("page_or_section_anchor", "paragraph:1", "page_or_section_anchor"),
        ("quoted_text_placeholder", "", "quoted_text_placeholder"),
        ("quoted_text_placeholder", "actual quoted source text", "quoted_text_placeholder"),
        ("normalized_text_placeholder", "", "normalized_text_placeholder"),
        ("normalized_text_placeholder", "actual normalized source text", "normalized_text_placeholder"),
        ("extraction_confidence", "", "extraction_confidence"),
        ("extraction_confidence", "unapproved", "extraction_confidence"),
        ("stale_source_hold", "", "stale_source_hold"),
        ("stale_source_hold", "not held", "stale_source_hold"),
        ("reviewer_routing", [], "reviewer_routing"),
        ("rollback_notes", [], "rollback_notes"),
    ],
)
def test_inventory_validator_rejects_missing_required_row_fields(field: str, value: object, match: str) -> None:
    inventory = build_public_citation_span_inventory_v5_from_normalized_fixture(FIXTURE_PATH)
    row = inventory["spans_by_source_id"]["ppd-online-tools-overview"]["docrec-v5-ppd-online-tools-overview"][0]
    row[field] = value

    with pytest.raises(ValueError, match=match):
        validate_public_citation_span_inventory_v5(inventory)


def test_inventory_validator_rejects_missing_validation_commands() -> None:
    inventory = build_public_citation_span_inventory_v5_from_normalized_fixture(FIXTURE_PATH)
    inventory["validation_commands"] = []

    with pytest.raises(ValueError, match="validation_commands"):
        validate_public_citation_span_inventory_v5(inventory)


@pytest.mark.parametrize(
    "flag",
    [
        "live_crawl_performed",
        "document_downloaded",
        "raw_body_persisted",
        "devhub_opened",
        "legal_or_permitting_guarantee",
        "active_mutation_enabled",
    ],
)
def test_inventory_validator_rejects_true_runtime_or_mutation_flags(flag: str) -> None:
    inventory = build_public_citation_span_inventory_v5_from_normalized_fixture(FIXTURE_PATH)
    row = inventory["spans_by_source_id"]["ppd-online-tools-overview"]["docrec-v5-ppd-online-tools-overview"][0]
    row[flag] = True

    with pytest.raises(ValueError, match=flag):
        validate_public_citation_span_inventory_v5(inventory)


@pytest.mark.parametrize(
    "key",
    [
        "raw_body",
        "raw_html",
        "raw_pdf",
        "body_text",
        "session_state",
        "auth_state",
        "devhub_session",
        "cookie",
        "access_token",
        "screenshot",
        "trace",
        "downloaded_document_claim",
        "legal_guarantee",
    ],
)
def test_rejects_raw_private_session_or_auth_artifact_keys(key: str) -> None:
    inventory = build_public_citation_span_inventory_v5_from_normalized_fixture(FIXTURE_PATH)
    row = inventory["spans_by_source_id"]["ppd-online-tools-overview"]["docrec-v5-ppd-online-tools-overview"][0]
    row[key] = "not allowed"

    with pytest.raises(ValueError, match="prohibited artifact key"):
        validate_public_citation_span_inventory_v5(inventory)


@pytest.mark.parametrize(
    "claim",
    [
        "live crawl performed",
        "document downloaded",
        "downloaded document claim",
        "raw body artifact",
        "devhub opened",
        "legal advice",
        "permit guaranteed",
        "auth token",
    ],
)
def test_rejects_prohibited_claim_text(claim: str) -> None:
    inventory = build_public_citation_span_inventory_v5_from_normalized_fixture(FIXTURE_PATH)
    row = inventory["spans_by_source_id"]["ppd-online-tools-overview"]["docrec-v5-ppd-online-tools-overview"][0]
    row["operator_note"] = claim

    with pytest.raises(ValueError, match="prohibited claim phrase"):
        validate_public_citation_span_inventory_v5(inventory)


def test_rejects_missing_record_citation_spans_before_inventory_build() -> None:
    inventory = build_public_citation_span_inventory_v5_from_normalized_fixture(FIXTURE_PATH)
    row = inventory["spans_by_source_id"]["ppd-online-tools-overview"]["docrec-v5-ppd-online-tools-overview"][0]
    minimal_record = {
        "source_id": row["source_id"],
        "document_id": row["document_id"],
        "extraction_confidence": row["extraction_confidence"],
        "sections": [{"section_id": "fixture-section"}],
        "citation_spans": [],
        "rollback_notes": ["fixture rollback"],
    }

    with pytest.raises(ValueError, match="citation_spans"):
        build_public_citation_span_inventory_v5([minimal_record])


def test_rejects_record_without_page_or_section_anchors_before_inventory_build() -> None:
    minimal_record = {
        "source_id": "fixture-source",
        "document_id": "fixture-document",
        "extraction_confidence": "synthetic-metadata-high",
        "sections": [],
        "pdf_pages": [],
        "citation_spans": [{"span_id": "span-1"}],
        "rollback_notes": ["fixture rollback"],
    }

    with pytest.raises(ValueError, match="section or page anchors"):
        build_public_citation_span_inventory_v5([minimal_record])


def test_validator_rejects_row_count_mismatch() -> None:
    inventory = build_public_citation_span_inventory_v5_from_normalized_fixture(FIXTURE_PATH)
    mutated = deepcopy(inventory)
    mutated["row_count"] = 999

    with pytest.raises(ValueError, match="row_count"):
        validate_public_citation_span_inventory_v5(mutated)
