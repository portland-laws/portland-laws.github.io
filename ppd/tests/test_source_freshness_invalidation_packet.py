from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ppd.source_freshness.invalidation_packet import build_invalidation_packet, load_fixture_packet


FIXTURES = Path(__file__).parent / "fixtures" / "source_freshness"


def _fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_source_freshness_invalidation_packet_lists_affected_public_records() -> None:
    packet = load_fixture_packet(
        FIXTURES / "public_recrawl_batch_plan.json",
        FIXTURES / "changed_public_source_hashes.json",
        generated_at="2026-05-28T00:00:00Z",
    )

    assert packet["fixture_first"] is True
    assert packet["metadata_only"] is True
    assert packet["network_requests_made"] is False
    assert packet["raw_page_bodies_stored"] is False
    assert packet["guardrail_refresh_status"] == "blocked_pending_human_review"
    assert packet["affected_source_record_ids"] == ["source-record-devhub-submit-guide"]
    assert packet["affected_requirement_ids"] == [
        "req-devhub-certification-gate",
        "req-devhub-dynamic-questions",
        "req-devhub-required-uploads",
    ]
    assert packet["affected_process_model_ids"] == [
        "process-devhub-permit-application",
        "process-trade-with-plan-review",
    ]
    assert packet["affected_guardrail_bundle_ids"] == [
        "guardrail-devhub-application-draft",
        "guardrail-official-submission-confirmation",
    ]
    assert packet["affected_agent_readiness_checklist_item_ids"] == [
        "agent-ready-action-gates-current",
        "agent-ready-required-documents-current",
        "agent-ready-source-freshness-current",
    ]


def test_source_freshness_invalidation_packet_contains_only_changed_source() -> None:
    packet = load_fixture_packet(
        FIXTURES / "public_recrawl_batch_plan.json",
        FIXTURES / "changed_public_source_hashes.json",
    )

    assert [source["source_id"] for source in packet["affected_sources"]] == [
        "src-devhub-submit-permit-application-guide"
    ]
    affected = packet["affected_sources"][0]
    assert affected["canonical_url"] == "https://www.portland.gov/ppd/devhub-guide-submit-permit-application"
    assert affected["previous_content_hash"].startswith("sha256:")
    assert affected["new_content_hash"] == "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    assert affected["invalidation_reason"] == "public source content hash changed"
    assert affected["guardrail_refresh_status"] == "blocked_pending_human_review"


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda plan, hashes: hashes.update({"network_requests_made": True}), "live-network evidence"),
        (lambda plan, hashes: hashes.update({"live_network_evidence": {"status": 200}}), "live-network evidence field"),
        (lambda plan, hashes: hashes.update({"raw_html": "raw body"}), "raw HTML/PDF body field"),
        (lambda plan, hashes: hashes.update({"pdf_bytes": "%PDF-1.7"}), "raw HTML/PDF body field"),
        (lambda plan, hashes: hashes.update({"downloaded_document_path": "/home/example/Downloads/guide.pdf"}), "downloaded document path"),
        (lambda plan, hashes: hashes.update({"canonical_url": "https://devhub.portlandoregon.gov/permit/private-case-123"}), "private or authenticated URL"),
        (lambda plan, hashes: hashes.update({"guardrails_remain_current": True}), "guardrails must not be claimed current"),
    ],
)
def test_rejects_unsafe_invalidation_packet_inputs(mutation: object, message: str) -> None:
    plan = _fixture("public_recrawl_batch_plan.json")
    hashes = _fixture("changed_public_source_hashes.json")

    assert callable(mutation)
    mutation(plan, hashes)

    with pytest.raises(ValueError, match=message):
        build_invalidation_packet(plan, hashes)


def test_rejects_raw_body_values_nested_in_metadata() -> None:
    plan = _fixture("public_recrawl_batch_plan.json")
    hashes = _fixture("changed_public_source_hashes.json")
    sources = plan["sources"]
    assert isinstance(sources, list)
    first_source = sources[0]
    assert isinstance(first_source, dict)
    first_source["evidence_excerpt"] = "raw page"

    with pytest.raises(ValueError, match="raw HTML/PDF body content"):
        build_invalidation_packet(plan, hashes)


def test_rejects_unchanged_hash_entries_as_unactionable() -> None:
    plan = _fixture("public_recrawl_batch_plan.json")
    hashes = _fixture("changed_public_source_hashes.json")
    changed_sources = hashes["changed_sources"]
    assert isinstance(changed_sources, list)
    first_change = changed_sources[0]
    assert isinstance(first_change, dict)
    first_change["new_content_hash"] = first_change["previous_content_hash"]

    with pytest.raises(ValueError, match="unactionable because hashes did not change"):
        build_invalidation_packet(plan, hashes)


def test_rejects_unknown_changed_hash_entries_as_unactionable() -> None:
    plan = _fixture("public_recrawl_batch_plan.json")
    hashes = _fixture("changed_public_source_hashes.json")
    changed_sources = hashes["changed_sources"]
    assert isinstance(changed_sources, list)
    first_change = changed_sources[0]
    assert isinstance(first_change, dict)
    first_change["source_id"] = "src-not-in-recrawl-plan"

    with pytest.raises(ValueError, match="unactionable for unknown sources"):
        build_invalidation_packet(plan, hashes)


def test_rejects_changed_source_without_downstream_dependency_links() -> None:
    plan = _fixture("public_recrawl_batch_plan.json")
    hashes = _fixture("changed_public_source_hashes.json")
    sources = plan["sources"]
    assert isinstance(sources, list)
    first_source = sources[0]
    assert isinstance(first_source, dict)
    first_source["affected_guardrail_bundle_ids"] = []

    with pytest.raises(ValueError, match="missing downstream dependency links"):
        build_invalidation_packet(plan, hashes)


def test_rejects_guardrail_current_claim_nested_in_source() -> None:
    plan = _fixture("public_recrawl_batch_plan.json")
    hashes = _fixture("changed_public_source_hashes.json")
    mutated_plan = copy.deepcopy(plan)
    sources = mutated_plan["sources"]
    assert isinstance(sources, list)
    first_source = sources[0]
    assert isinstance(first_source, dict)
    first_source["regenerated_guardrail_status"] = "current"

    with pytest.raises(ValueError, match="guardrails must not be claimed current"):
        build_invalidation_packet(mutated_plan, hashes)
