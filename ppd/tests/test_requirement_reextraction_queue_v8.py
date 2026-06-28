from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from ppd.requirement_reextraction_queue_v8 import (
    assert_valid_reextraction_queue,
    build_reextraction_queue,
    validate_reextraction_queue,
)

FIXTURES = Path(__file__).parent / "fixtures" / "requirement_reextraction_queue_v8"


def _queue() -> dict[str, object]:
    return build_reextraction_queue(
        FIXTURES / "source_freshness_diff_intake_v8.json",
        FIXTURES / "requirement_inventory_v8.json",
    )


def test_builds_ordered_fixture_only_reextraction_queue_v8() -> None:
    result = _queue()

    assert result["queue_version"] == "v8"
    assert result["fixture_only"] is True
    assert result["source_freshness_diff_ref"].endswith("source_freshness_diff_intake_v8.json")
    assert result["requirement_inventory_ref"].endswith("requirement_inventory_v8.json")
    assert result["live_actions_performed"] == []
    assert [row["requirement_id"] for row in result["reextraction_candidates"]] == [
        "REQ-BLDG-INTAKE-001",
        "REQ-BLDG-PLAN-002",
        "REQ-ZONING-REVIEW-001",
    ]
    assert result["permit_type_process_stage_grouping_rows"] == [
        {
            "permit_type": "building",
            "process_stage": "intake",
            "requirement_id": "REQ-BLDG-INTAKE-001",
            "source_id": "devhub-building-submittal-checklist",
        },
        {
            "permit_type": "building",
            "process_stage": "plan_review",
            "requirement_id": "REQ-BLDG-PLAN-002",
            "source_id": "devhub-building-submittal-checklist",
        },
        {
            "permit_type": "zoning",
            "process_stage": "review",
            "requirement_id": "REQ-ZONING-REVIEW-001",
            "source_id": "devhub-zoning-standards-summary",
        },
    ]
    assert [row["requirement_id"] for row in result["unchanged_requirement_carry_forward_rows"]] == [
        "REQ-SITE-INTAKE-001",
    ]
    assert result["reviewer_hold_reasons"] == [
        {
            "source_id": "devhub-fee-schedule-summary",
            "hold_reason": "conflicting freshness signals in source diff fixture",
            "evidence_ref": "fixture://source-freshness-diff-v8/devhub-fee-schedule-summary",
        }
    ]
    assert result["offline_validation_commands"] == [
        ["python3", "-m", "py_compile", "ppd/requirement_reextraction_queue_v8.py"],
        ["python3", "-m", "pytest", "ppd/tests/test_requirement_reextraction_queue_v8.py"],
    ]
    assert validate_reextraction_queue(result) == []
    assert_valid_reextraction_queue(result)


def test_evidence_references_are_preserved_for_each_diff_row() -> None:
    result = _queue()

    assert result["affected_source_evidence_refs"] == [
        {
            "source_id": "devhub-building-submittal-checklist",
            "evidence_ref": "fixture://source-freshness-diff-v8/devhub-building-submittal-checklist",
            "freshness_status": "changed",
        },
        {
            "source_id": "devhub-zoning-standards-summary",
            "evidence_ref": "fixture://source-freshness-diff-v8/devhub-zoning-standards-summary",
            "freshness_status": "new",
        },
        {
            "source_id": "devhub-fee-schedule-summary",
            "evidence_ref": "fixture://source-freshness-diff-v8/devhub-fee-schedule-summary",
            "freshness_status": "conflict",
        },
        {
            "source_id": "devhub-site-development-intake",
            "evidence_ref": "fixture://source-freshness-diff-v8/devhub-site-development-intake",
            "freshness_status": "unchanged",
        },
    ]


def test_rejects_missing_required_v8_queue_references_and_sections() -> None:
    queue = deepcopy(_queue())
    for field in (
        "source_freshness_diff_ref",
        "requirement_inventory_ref",
        "reextraction_candidates",
        "affected_source_evidence_refs",
        "permit_type_process_stage_grouping_rows",
        "unchanged_requirement_carry_forward_rows",
        "reviewer_hold_reasons",
        "offline_validation_commands",
    ):
        queue[field] = [] if field.endswith(("candidates", "refs", "rows", "reasons", "commands")) else ""

    errors = validate_reextraction_queue(queue)
    paths = {error.path for error in errors}

    assert "source_freshness_diff_ref" in paths
    assert "requirement_inventory_ref" in paths
    assert "reextraction_candidates" in paths
    assert "affected_source_evidence_refs" in paths
    assert "permit_type_process_stage_grouping_rows" in paths
    assert "unchanged_requirement_carry_forward_rows" in paths
    assert "reviewer_hold_reasons" in paths
    assert "offline_validation_commands" in paths


def test_rejects_unordered_reextraction_candidates() -> None:
    queue = deepcopy(_queue())
    queue["reextraction_candidates"] = list(reversed(queue["reextraction_candidates"]))

    errors = validate_reextraction_queue(queue)

    assert any(error.path == "reextraction_candidates" for error in errors)


def test_rejects_missing_candidate_evidence_and_grouping_coverage() -> None:
    queue = deepcopy(_queue())
    queue["affected_source_evidence_refs"] = queue["affected_source_evidence_refs"][:1]
    queue["permit_type_process_stage_grouping_rows"] = queue["permit_type_process_stage_grouping_rows"][:1]

    errors = validate_reextraction_queue(queue)
    paths = {error.path for error in errors}

    assert "affected_source_evidence_refs" in paths
    assert "permit_type_process_stage_grouping_rows" in paths


def test_rejects_live_crawl_artifacts_claims_guarantees_and_mutation_flags() -> None:
    queue = deepcopy(_queue())
    queue.update(
        {
            "live_crawl_executed": True,
            "live_crawl_execution_claims": ["live crawl executed"],
            "downloaded_artifacts": ["/tmp/downloaded.pdf"],
            "raw_crawl_artifacts": ["/tmp/raw.html"],
            "auth_state_path": "/tmp/storage-state.json",
            "devhub_session_path": "/tmp/session.json",
            "official_action_completed": True,
            "legal_guarantee": "legal guarantee",
            "permitting_guarantee": "permitting guarantee",
            "active_mutation_flags": ["submit_enabled"],
        }
    )

    errors = validate_reextraction_queue(queue)
    paths = {error.path for error in errors}

    assert "queue.live_crawl_executed" in paths
    assert "queue.live_crawl_execution_claims" in paths
    assert "queue.downloaded_artifacts" in paths
    assert "queue.raw_crawl_artifacts" in paths
    assert "queue.auth_state_path" in paths
    assert "queue.devhub_session_path" in paths
    assert "queue.official_action_completed" in paths
    assert "queue.legal_guarantee" in paths
    assert "queue.permitting_guarantee" in paths
    assert "queue.active_mutation_flags" in paths


def test_rejects_invalid_validation_command_shape() -> None:
    queue = deepcopy(_queue())
    queue["offline_validation_commands"] = ["python3 ppd/daemon/ppd_daemon.py --self-test"]

    errors = validate_reextraction_queue(queue)

    assert any(error.path == "offline_validation_commands" for error in errors)
