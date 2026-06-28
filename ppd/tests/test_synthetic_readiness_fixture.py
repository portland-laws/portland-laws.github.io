from __future__ import annotations

import json
from pathlib import Path
from typing import Any


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "synthetic_readiness"
    / "narrow_single_pdf_upload_staging.json"
)


FORBIDDEN_KEYS = {
    "auth_state",
    "cookies",
    "credential",
    "credentials",
    "har",
    "password",
    "payment_details",
    "private_uploads",
    "raw_crawl_output",
    "screenshot",
    "screenshots",
    "session",
    "trace",
    "traces",
}


CONSEQUENTIAL_CLASSIFICATIONS = {"consequential_official", "financial"}
SAFE_NEXT_ACTION_CLASSIFICATIONS = {"safe_read_only", "reversible_draft"}


def _load_fixture() -> dict[str, Any]:
    with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
        data = json.load(fixture_file)
    assert isinstance(data, dict)
    return data


def _walk_values(value: Any) -> list[Any]:
    values = [value]
    if isinstance(value, dict):
        for nested in value.values():
            values.extend(_walk_values(nested))
    elif isinstance(value, list):
        for nested in value:
            values.extend(_walk_values(nested))
    return values


def test_synthetic_readiness_fixture_links_the_full_offline_chain() -> None:
    fixture = _load_fixture()

    assert fixture["synthetic"] is True
    assert fixture["fixture_id"] == "synthetic-readiness-single-pdf-upload-staging-v1"

    sources = {source["source_id"]: source for source in fixture["source_registry"]}
    manifests = {manifest["manifest_id"]: manifest for manifest in fixture["archive_manifest"]}
    documents = {document["document_id"]: document for document in fixture["document_records"]}
    requirements = {
        requirement["requirement_id"]: requirement
        for requirement in fixture["extracted_requirements"]
    }

    assert sources
    assert manifests
    assert documents
    assert requirements

    for source in sources.values():
        assert source["privacy_classification"] == "public"
        assert source["canonical_url"].startswith(("https://www.portland.gov/", "https://devhub.portlandoregon.gov"))

    for manifest in manifests.values():
        assert manifest["source_id"] in sources
        assert manifest["normalized_document_id"] in documents
        assert manifest["no_raw_body_persisted"] is True
        assert manifest["archive_artifact_ref"].startswith("metadata-only:")

    citation_ids: set[str] = set()
    for document in documents.values():
        assert document["source_id"] in sources
        for citation_span in document["citation_spans"]:
            citation_ids.add(citation_span["citation_span_id"])
            assert citation_span["source_id"] == document["source_id"]
            assert citation_span["manifest_id"] in manifests

    for requirement in requirements.values():
        assert requirement["formalization_status"] == "formalized"
        assert set(requirement["source_evidence_ids"]).issubset(citation_ids)

    process_model = fixture["process_model"]
    assert process_model["guardrail_bundle_id"] == fixture["guardrail_bundle"]["guardrail_bundle_id"]

    process_requirement_ids: set[str] = set()
    for collection_name in ("eligibility_rules", "required_user_facts", "required_documents", "file_rules"):
        for item in process_model[collection_name]:
            process_requirement_ids.update(item.get("source_requirement_ids", []))
    assert process_requirement_ids
    assert process_requirement_ids.issubset(requirements)

    guardrail_bundle = fixture["guardrail_bundle"]
    assert guardrail_bundle["process_id"] == process_model["process_id"]
    assert set(guardrail_bundle["source_evidence_ids"]).issubset(citation_ids)
    assert guardrail_bundle["deterministic_predicates"]
    assert guardrail_bundle["exact_confirmation_predicates"]
    assert guardrail_bundle["refused_action_predicates"]

    gap_analysis = fixture["user_gap_analysis"]
    assert gap_analysis["process_id"] == process_model["process_id"]
    assert gap_analysis["guardrail_bundle_id"] == guardrail_bundle["guardrail_bundle_id"]
    assert gap_analysis["missing_facts"]
    assert gap_analysis["missing_documents"]
    assert gap_analysis["blocked_actions"]
    assert gap_analysis["next_safe_actions"]

    next_safe_action = gap_analysis["next_safe_actions"][0]
    assert next_safe_action["classification"] in SAFE_NEXT_ACTION_CLASSIFICATIONS
    assert set(next_safe_action["depends_on_missing_facts"]).issubset(set(gap_analysis["missing_facts"]))

    next_safe_output = fixture["next_safe_action_output"]
    assert next_safe_output["case_id"] == gap_analysis["case_id"]
    assert next_safe_output["selected_next_safe_action_id"] == next_safe_action["next_safe_action_id"]
    assert next_safe_output["classification"] in SAFE_NEXT_ACTION_CLASSIFICATIONS
    assert set(next_safe_output["source_evidence_ids"]).issubset(citation_ids)


def test_synthetic_readiness_fixture_blocks_consequential_devhub_actions() -> None:
    fixture = _load_fixture()

    surface_actions = {
        action["action_id"]: action
        for surface in fixture["devhub_surface_map"]
        for action in surface["actions"]
    }
    blocked_action_ids = {
        blocked_action["action_id"]
        for blocked_action in fixture["user_gap_analysis"]["blocked_actions"]
    }
    next_safe_blocked_action_ids = set(
        fixture["next_safe_action_output"]["blocked_action_ids"]
    )

    consequential_action_ids = {
        action_id
        for action_id, action in surface_actions.items()
        if action["classification"] in CONSEQUENTIAL_CLASSIFICATIONS
    }

    assert consequential_action_ids
    assert consequential_action_ids.issubset(blocked_action_ids)
    assert consequential_action_ids.issubset(next_safe_blocked_action_ids)

    refused_descriptions = " ".join(
        predicate["description"].lower()
        for predicate in fixture["guardrail_bundle"]["refused_action_predicates"]
    )
    for prohibited_word in ("captcha", "mfa", "payment", "upload", "certification", "submission"):
        assert prohibited_word in refused_descriptions


def test_synthetic_readiness_fixture_contains_no_live_or_private_artifacts() -> None:
    fixture = _load_fixture()

    assert "downloaded_documents" in fixture["prohibited_artifacts"]
    assert "raw_crawl_output" in fixture["prohibited_artifacts"]

    for value in _walk_values(fixture):
        if isinstance(value, dict):
            lowered_keys = {str(key).lower() for key in value}
            assert not lowered_keys.intersection(FORBIDDEN_KEYS - {"raw_crawl_output", "downloaded_documents"})
        elif isinstance(value, str):
            lowered_value = value.lower()
            assert "/home/" not in lowered_value
            assert "file://" not in lowered_value
            assert "playwright/.auth" not in lowered_value
            assert "storage_state" not in lowered_value
            assert "set-cookie" not in lowered_value
