from __future__ import annotations

import json
from pathlib import Path

from ppd.logic.inactive_public_refresh_delta_plan_v1 import (
    OFFLINE_VALIDATION_COMMANDS,
    PLAN_VERSION,
    QUEUE_VERSION,
    build_inactive_public_refresh_delta_plan,
)

FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "public_refresh_reextraction_queue_v2"
    / "inactive_delta_rows.json"
)


def _fixture_rows() -> list[dict[str, object]]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_builds_inactive_delta_plan_from_synthetic_queue_rows_only() -> None:
    plan = build_inactive_public_refresh_delta_plan(_fixture_rows())

    assert plan["plan_version"] == PLAN_VERSION
    assert plan["queue_version"] == QUEUE_VERSION
    assert plan["status"] == "inactive_placeholder"
    assert plan["source_policy"] == {
        "input_source": "synthetic_fixture_rows_only",
        "live_extraction": False,
        "live_crawling": False,
        "document_downloads": False,
        "devhub_access": False,
        "active_process_model_mutation": False,
        "active_guardrail_mutation": False,
        "official_actions": False,
    }
    assert len(plan["process_model_delta_placeholders"]) == 4
    assert all(
        placeholder["status"] == "inactive_placeholder"
        for placeholder in plan["process_model_delta_placeholders"]
    )
    assert all(
        placeholder["activation_gate"] == "human_review_and_separate_guardrail_compile_required"
        for placeholder in plan["process_model_delta_placeholders"]
    )


def test_separates_stage_document_unsupported_and_evidence_hold_sections() -> None:
    plan = build_inactive_public_refresh_delta_plan(_fixture_rows())

    assert [item["row_id"] for item in plan["stage_level_eligibility_changes"]] == ["sprrqv2-001"]
    assert [item["row_id"] for item in plan["document_requirement_changes"]] == ["sprrqv2-002"]
    assert [item["row_id"] for item in plan["unsupported_path_notes"]] == ["sprrqv2-003"]
    assert [item["row_id"] for item in plan["evidence_holds"]["stale"]] == ["sprrqv2-002"]
    assert [item["row_id"] for item in plan["evidence_holds"]["conflicting"]] == ["sprrqv2-003"]


def test_includes_affected_guardrails_reviewer_routing_rollback_and_validation_commands() -> None:
    plan = build_inactive_public_refresh_delta_plan(_fixture_rows())

    guardrail_ids = {item["guardrail_bundle_id"] for item in plan["affected_guardrail_bundle_refs"]}
    assert guardrail_ids == {
        "guardrail-bundle-building-plan-review",
        "guardrail-bundle-standard-trade",
        "guardrail-bundle-devhub-official-actions",
    }
    assert all(item["action"] == "review_only_no_mutation" for item in plan["affected_guardrail_bundle_refs"])
    assert len(plan["reviewer_routing"]) == 4
    assert all(item["requires_human_review"] is True for item in plan["reviewer_routing"])
    assert len(plan["rollback_notes"]) == 4
    assert all(item["rollback_scope"] == "discard_inactive_placeholder_only" for item in plan["rollback_notes"])
    assert plan["validation_commands"] == OFFLINE_VALIDATION_COMMANDS


def test_rejects_non_synthetic_or_malformed_rows_without_raising() -> None:
    rows = _fixture_rows()
    rows.append(
        {
            "queue_version": "live-public-refresh-requirement-reextraction-queue",
            "row_id": "bad-live-row",
            "process_id": "building-permit-plan-review",
            "permit_type": "building permit with plan review",
            "process_stage": "document preparation",
            "change_type": "document_requirement",
            "requirement_id": "bad-live-req",
            "requirement_type": "document_requirement",
            "proposed_text": "This row must be rejected because it is not synthetic queue v2 input.",
            "source_evidence_ids": ["live-evidence"],
            "evidence_status": "current",
            "guardrail_bundle_refs": ["guardrail-bundle-building-plan-review"],
            "reviewer_groups": ["ppd-process-model-reviewers"],
            "rollback_note": "No-op.",
        }
    )
    rows.append({"queue_version": QUEUE_VERSION, "row_id": "missing-required-fields"})

    plan = build_inactive_public_refresh_delta_plan(rows)

    assert len(plan["process_model_delta_placeholders"]) == 4
    assert plan["rejected_rows"] == [
        {"row_id": "bad-live-row", "reason": "unsupported queue_version"},
        {
            "row_id": "missing-required-fields",
            "reason": "missing fields: change_type, evidence_status, guardrail_bundle_refs, permit_type, process_id, process_stage, proposed_text, requirement_id, requirement_type, reviewer_groups, rollback_note, source_evidence_ids",
        },
    ]
