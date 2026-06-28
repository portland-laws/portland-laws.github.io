from __future__ import annotations

import json
from pathlib import Path

from ppd.logic.stale_citation_remediation_queue_v6 import (
    assert_valid_queue_v6,
    validate_queue_v6,
)


FIXTURES = Path(__file__).parent / "fixtures" / "stale_citation_queue_v6"


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _codes(queue: dict) -> set[str]:
    return {violation.code for violation in validate_queue_v6(queue)}


def test_accepts_minimal_valid_queue_v6_fixture() -> None:
    queue = _load_fixture("valid_queue.json")

    assert validate_queue_v6(queue) == []
    assert_valid_queue_v6(queue)


def test_rejects_missing_required_evidence_and_review_tables() -> None:
    queue = _load_fixture("valid_queue.json")
    for key in (
        "result_intake_refs",
        "cited_requirement_evidence_rows",
        "unaffected_citation_rows",
        "changed_source_hash_placeholders",
        "human_review_hold_rows",
        "downstream_guardrail_bundle_impact_placeholders",
        "validation_commands",
    ):
        queue.pop(key)

    codes = _codes(queue)

    assert "missing_result_intake_refs" in codes
    assert "missing_cited_requirement_evidence_rows" in codes
    assert "missing_unaffected_citation_rows" in codes
    assert "missing_changed_source_hash_placeholders" in codes
    assert "missing_human_review_hold_rows" in codes
    assert "missing_downstream_guardrail_bundle_impact_placeholders" in codes
    assert "missing_validation_commands" in codes


def test_rejects_live_crawl_raw_private_official_guarantee_and_mutation_claims() -> None:
    queue = _load_fixture("invalid_forbidden_claims.json")

    codes = _codes(queue)

    assert "live_crawl_execution_claim" in codes
    assert "downloaded_or_raw_crawl_artifact" in codes
    assert "private_or_session_artifact" in codes
    assert "official_action_completion_claim" in codes
    assert "legal_or_permitting_guarantee" in codes
    assert "forbidden_true_flag" in codes
    assert "forbidden_artifact_path" in codes


def test_requires_changed_hashes_and_guardrail_impacts_to_remain_placeholders() -> None:
    queue = _load_fixture("valid_queue.json")
    queue["changed_source_hash_placeholders"][0]["changed_source_hash_placeholder"] = "sha256:actual-new-hash"
    queue["downstream_guardrail_bundle_impact_placeholders"][0]["status"] = "complete"
    queue["human_review_hold_rows"][0]["status"] = "released"

    codes = _codes(queue)

    assert "invalid_changed_source_hash_placeholder" in codes
    assert "invalid_guardrail_impact_status" in codes
    assert "invalid_human_review_hold_status" in codes
