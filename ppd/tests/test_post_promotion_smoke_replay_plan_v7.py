from __future__ import annotations

import json
from pathlib import Path

import pytest

from ppd.post_promotion_smoke_replay_plan_v7 import (
    assert_valid_post_promotion_smoke_replay_plan_v7,
    validate_post_promotion_smoke_replay_plan_v7,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "post_promotion_smoke_replay_plan_v7"


def _load_fixture(name: str) -> dict:
    with (FIXTURE_DIR / name).open(encoding="utf-8") as handle:
        return json.load(handle)


def test_valid_post_promotion_smoke_replay_plan_v7_fixture_passes() -> None:
    plan = _load_fixture("valid_plan.json")

    result = validate_post_promotion_smoke_replay_plan_v7(plan)

    assert result.ok
    assert result.issues == ()
    assert_valid_post_promotion_smoke_replay_plan_v7(plan)


def test_invalid_post_promotion_smoke_replay_plan_v7_fixture_reports_required_failures() -> None:
    plan = _load_fixture("invalid_plan.json")

    result = validate_post_promotion_smoke_replay_plan_v7(plan)
    codes = {issue.code for issue in result.issues}

    assert not result.ok
    assert "missing_promotion_rehearsal_references" in codes
    assert "missing_smoke_scenario_rows" in codes
    assert "missing_information_or_stale_evidence_probe" in codes
    assert "missing_reversible_draft_or_local_pdf_preview_probe" in codes
    assert "missing_exact_confirmation_or_refused_action_probe" in codes
    assert "missing_manual_handoff_probe" in codes
    assert "missing_rollback_trigger_observations" in codes
    assert "missing_monitoring_expectations" in codes
    assert "missing_validation_commands" in codes
    assert "actual_activation_or_promotion_claim" in codes
    assert "live_crawl_execution_claim" in codes
    assert "private_session_or_auth_artifact" in codes
    assert "official_action_completion_claim" in codes
    assert "legal_or_permitting_guarantee" in codes
    assert "active_mutation_flag" in codes


def test_assert_valid_raises_for_invalid_plan() -> None:
    with pytest.raises(ValueError, match="missing_promotion_rehearsal_references"):
        assert_valid_post_promotion_smoke_replay_plan_v7(_load_fixture("invalid_plan.json"))


def test_probe_requirements_accept_either_side_of_or_clauses() -> None:
    plan = _load_fixture("valid_plan.json")
    plan["probes"] = [
        "stale evidence probe rejects obsolete source facts",
        "local PDF preview probe stays local and reversible",
        "refused action probe blocks official execution",
        "manual handoff probe requires the user to take over",
    ]

    assert validate_post_promotion_smoke_replay_plan_v7(plan).ok


def test_private_artifacts_are_rejected_inside_nested_rows() -> None:
    plan = _load_fixture("valid_plan.json")
    plan["smoke_scenario_rows"].append(
        {
            "id": "bad-private-artifact",
            "artifact": "trace.zip captured during authenticated replay"
        }
    )

    result = validate_post_promotion_smoke_replay_plan_v7(plan)

    assert "private_session_or_auth_artifact" in {issue.code for issue in result.issues}


def test_true_mutation_flags_are_rejected_even_without_forbidden_text() -> None:
    plan = _load_fixture("valid_plan.json")
    plan["mutation_controls"]["official_write_enabled"] = True

    result = validate_post_promotion_smoke_replay_plan_v7(plan)

    assert "active_mutation_flag" in {issue.code for issue in result.issues}
