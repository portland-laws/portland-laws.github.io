from __future__ import annotations

import copy
import json
from pathlib import Path

from ppd.logic.requirement_reextraction_batch_plan_v6 import (
    assert_valid_batch_plan_v6,
    validate_batch_plan_v6,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "requirement_reextraction_batch_plan_v6.json"


REQUIRED_INACTIVE_GUARDRAILS = {
    "live_site_access",
    "authenticated_devhub_access",
    "private_document_access",
    "raw_body_storage",
    "transactional_actions",
    "legal_or_permitting_guarantees",
}


def load_plan() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def codes(plan: dict) -> set[str]:
    return {violation.code for violation in validate_batch_plan_v6(plan)}


def test_accepts_valid_fixture_first_batch_plan_v6() -> None:
    plan = load_plan()

    assert validate_batch_plan_v6(plan) == []
    assert_valid_batch_plan_v6(plan)


def test_plan_consumes_only_stale_citation_queue_v6_fixtures() -> None:
    plan = load_plan()

    assert plan["mode"] == "fixture_first_offline_only"
    assert plan["stale_citation_remediation_refs"] == [
        {
            "queue_id": "stale-citation-remediation-queue-v6",
            "fixture_path": "ppd/tests/fixtures/stale_citation_queue_v6/valid_queue.json",
        }
    ]


def test_batches_group_changed_documents_and_refresh_fixtures_by_permit_process() -> None:
    plan = load_plan()
    batches = plan["permit_process_batches"]

    assert batches
    for batch in batches:
        assert batch["permit_process"]
        assert batch["changed_public_documents"]
        assert batch["cite_extraction_fixtures_to_refresh"]
        for document in batch["changed_public_documents"]:
            assert document["stale_citation_queue_fixture_id"].startswith("queue-v6-")
            assert document["change_reason"] == "fixture_stale_citation_remediation"
        for fixture in batch["cite_extraction_fixtures_to_refresh"]:
            assert fixture.startswith("ppd/tests/fixtures/cite_extraction/")
            assert fixture.endswith(".json")


def test_human_review_holds_are_carried_forward() -> None:
    plan = load_plan()

    for batch in plan["permit_process_batches"]:
        assert batch["human_review_holds"]
        for hold in batch["human_review_holds"]:
            assert hold["carried_forward"] is True
            assert hold["status"] in {"hold", "pending_human_review", "requires_human_review"}
            assert hold["reason"]


def test_guardrails_remain_inactive() -> None:
    plan = load_plan()
    guardrails = plan["guardrails"]

    assert set(guardrails) == REQUIRED_INACTIVE_GUARDRAILS
    assert all(status == "inactive" for status in guardrails.values())


def test_offline_validation_commands_only() -> None:
    plan = load_plan()
    commands = plan["offline_validation_commands"]

    assert commands == [
        ["python3", "-m", "py_compile", "ppd/logic/requirement_reextraction_batch_plan_v6.py"],
        ["python3", "-m", "pytest", "ppd/tests/test_requirement_reextraction_batch_plan_v6.py"],
    ]


def test_rejects_missing_required_plan_sections() -> None:
    plan = load_plan()
    for key in (
        "stale_citation_remediation_refs",
        "permit_process_batches",
        "reviewer_acceptance_criteria",
        "guardrails",
        "offline_validation_commands",
    ):
        plan.pop(key)

    found = codes(plan)

    assert "missing_stale_citation_remediation_refs" in found
    assert "missing_permit_process_grouping" in found
    assert "missing_reviewer_acceptance_criteria" in found
    assert "missing_inactive_guardrail_preservation" in found
    assert "missing_validation_commands" in found


def test_rejects_missing_batch_level_requirements() -> None:
    plan = load_plan()
    batch = plan["permit_process_batches"][0]
    batch.pop("changed_public_documents")
    batch.pop("cite_extraction_fixtures_to_refresh")
    batch.pop("human_review_holds")

    found = codes(plan)

    assert "missing_changed_public_documents" in found
    assert "missing_extraction_fixture_references" in found
    assert "missing_propagated_human_review_holds" in found


def test_rejects_unpropagated_holds_and_active_guardrails() -> None:
    plan = load_plan()
    plan["permit_process_batches"][0]["human_review_holds"][0]["carried_forward"] = False
    plan["permit_process_batches"][0]["human_review_holds"][0]["status"] = "released"
    plan["guardrails"]["live_site_access"] = "active"

    found = codes(plan)

    assert "human_review_hold_not_carried_forward" in found
    assert "invalid_human_review_hold_status" in found
    assert "guardrail_not_inactive" in found


def test_rejects_live_crawl_raw_private_official_guarantee_and_mutation_claims() -> None:
    plan = copy.deepcopy(load_plan())
    plan["notes"] = [
        "live crawl executed for this plan",
        "permit submitted and payment submitted",
        "guaranteed approval for the permit",
        "/tmp/downloads/source.pdf",
    ]
    plan["raw_body"] = "raw"
    plan["auth_state_path"] = "/tmp/.auth/storage_state.json"
    plan["active_mutation"] = True

    found = codes(plan)

    assert "live_crawl_execution_claim" in found
    assert "downloaded_or_raw_crawl_artifact" in found
    assert "private_or_session_artifact" in found
    assert "official_action_completion_claim" in found
    assert "legal_or_permitting_guarantee" in found
    assert "active_mutation_or_forbidden_true_flag" in found
    assert "forbidden_artifact_path" in found


def test_rejects_unsupported_validation_commands() -> None:
    plan = load_plan()
    plan["offline_validation_commands"] = [["curl", "https://www.portland.gov/ppd"]]

    assert "unsupported_validation_command" in codes(plan)
