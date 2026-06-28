from __future__ import annotations

from ppd.validation.requirement_reextraction_queue_v7 import (
    assert_valid_requirement_reextraction_queue_v7,
    validate_requirement_reextraction_queue_v7,
)


def _valid_entry() -> dict[str, object]:
    return {
        "source_freshness_diff_ref": "freshness-diff:example:2026-06-02",
        "source_to_extraction_work_rows": [{"source_id": "src-1", "work_id": "work-1"}],
        "changed_section_placeholders": [{"section_ref": "33.110", "status": "placeholder"}],
        "citation_span_refresh_expectations": [{"citation": "33.110.220", "expectation": "refresh span before reviewer decision"}],
        "requirement_family_hints": ["zoning-use-review"],
        "stale_evidence_hold_carry_forward_rows": [{"evidence_id": "ev-1", "hold_reason": "stale until recrawled"}],
        "reviewer_assignment_placeholders": [{"queue_role": "ppd-reviewer", "assignee": None}],
        "validation_commands": [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]],
    }


def test_accepts_complete_deterministic_queue_entry() -> None:
    payload = {"version": 7, "entries": [_valid_entry()]}

    assert validate_requirement_reextraction_queue_v7(payload) == []
    assert_valid_requirement_reextraction_queue_v7(payload)


def test_rejects_missing_required_downstream_references() -> None:
    entry = _valid_entry()
    entry.pop("source_freshness_diff_ref")
    entry["changed_section_placeholders"] = []
    entry["citation_span_refresh_expectations"] = ""

    errors = validate_requirement_reextraction_queue_v7({"entries": [entry]})
    paths = {error.path for error in errors}

    assert "entries[0].source_freshness_diff_ref" in paths
    assert "entries[0].changed_section_placeholders" in paths
    assert "entries[0].citation_span_refresh_expectations" in paths


def test_rejects_live_crawl_artifacts_claims_and_mutation_flags() -> None:
    entry = _valid_entry()
    entry.update(
        {
            "live_crawl_executed": True,
            "raw_crawl_artifacts": ["/tmp/raw.html"],
            "auth_state_path": "/tmp/storage-state.json",
            "official_action_completed": True,
            "legal_guarantee": "guaranteed approval",
            "active_mutation_flags": ["submit_enabled"],
        }
    )

    errors = validate_requirement_reextraction_queue_v7({"entries": [entry]})
    paths = {error.path for error in errors}

    assert "entries[0].live_crawl_executed" in paths
    assert "entries[0].raw_crawl_artifacts" in paths
    assert "entries[0].auth_state_path" in paths
    assert "entries[0].official_action_completed" in paths
    assert "entries[0].legal_guarantee" in paths
    assert "entries[0].active_mutation_flags" in paths


def test_rejects_invalid_validation_command_shape() -> None:
    entry = _valid_entry()
    entry["validation_commands"] = ["python3 ppd/daemon/ppd_daemon.py --self-test"]

    errors = validate_requirement_reextraction_queue_v7({"entries": [entry]})

    assert any(error.path == "entries[0].validation_commands" for error in errors)
