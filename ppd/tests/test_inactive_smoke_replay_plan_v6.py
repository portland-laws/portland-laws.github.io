from __future__ import annotations

import copy
import json
from pathlib import Path

from ppd.guardrails.inactive_smoke_replay_plan_v6 import (
    assert_inactive_smoke_replay_plan_v6,
    validate_inactive_smoke_replay_plan_v6,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "inactive_smoke_replay_plan_v6"


def load_valid_plan() -> dict[str, object]:
    return json.loads((FIXTURE_DIR / "valid_plan.json").read_text(encoding="utf-8"))


def finding_codes(plan: dict[str, object]) -> set[str]:
    return {finding.code for finding in validate_inactive_smoke_replay_plan_v6(plan).findings}


def test_valid_inactive_smoke_replay_plan_v6_passes() -> None:
    plan = load_valid_plan()

    result = validate_inactive_smoke_replay_plan_v6(plan)

    assert result.ok
    assert result.findings == ()
    assert_inactive_smoke_replay_plan_v6(plan)


def test_rejects_each_missing_required_rehearsal_section() -> None:
    required_keys = {
        "activation_rehearsal_references",
        "post_activation_smoke_scenarios",
        "source_freshness_precheck_rows",
        "agent_facing_response_probes",
        "rollback_trigger_observations",
        "monitoring_signal_expectations",
        "reviewer_attendance_checkpoints",
        "validation_commands",
    }

    for key in required_keys:
        plan = load_valid_plan()
        plan[key] = []

        assert f"missing_{key}" in finding_codes(plan)


def test_rejects_actual_activation_and_live_crawl_claims() -> None:
    plan = load_valid_plan()
    plan["notes"] = [
        "Activation completed after review.",
        "Live crawl executed against the public site.",
    ]

    codes = finding_codes(plan)

    assert "actual_activation_claims" in codes
    assert "live_crawl_execution_claims" in codes


def test_rejects_private_session_auth_and_official_completion_claims() -> None:
    plan = load_valid_plan()
    plan["artifacts"] = {
        "session": "Stored session state and cookies were attached.",
        "official": "Submitted the permit request and payment completed.",
    }

    codes = finding_codes(plan)

    assert "private_session_auth_artifacts" in codes
    assert "official_action_completion_claims" in codes


def test_rejects_legal_or_permitting_guarantees() -> None:
    plan = load_valid_plan()
    plan["review_summary"] = "Permit guaranteed and approval assured after this replay."

    assert "legal_or_permitting_guarantees" in finding_codes(plan)


def test_rejects_active_mutation_flags() -> None:
    plan = load_valid_plan()
    plan["execution"] = {
        "allow_mutations": True,
        "execute_live_crawl": True,
    }

    assert "active_mutation_flag" in finding_codes(plan)


def test_rejects_disabled_inactive_safeguards() -> None:
    plan = load_valid_plan()
    plan["dry_run"] = False
    plan["read_only"] = False
    plan["requires_reviewer_attendance"] = False

    assert "inactive_guardrail_disabled" in finding_codes(plan)


def test_assertion_raises_readable_error_for_invalid_plan() -> None:
    plan = copy.deepcopy(load_valid_plan())
    plan["status"] = "active"
    plan["mutation_enabled"] = True

    try:
        assert_inactive_smoke_replay_plan_v6(plan)
    except ValueError as exc:
        message = str(exc)
    else:
        raise AssertionError("invalid inactive smoke replay plan should raise ValueError")

    assert "inactive" in message
    assert "active mutation flags" in message
