from __future__ import annotations

import json
from pathlib import Path

from ppd.guardrails.inactive_public_refresh_recompile_plan import (
    assemble_inactive_public_refresh_recompile_plan,
)


def _fixture_rows() -> dict[str, object]:
    fixture_path = Path(__file__).parent / "fixtures" / "inactive_public_refresh_recompile_plan" / "synthetic_rows.json"
    return json.loads(fixture_path.read_text(encoding="utf-8"))


def test_assemble_inactive_public_refresh_recompile_plan_from_fixture_rows() -> None:
    rows = _fixture_rows()

    plan = assemble_inactive_public_refresh_recompile_plan(
        rows["process_model_delta_plan_rows"],
        rows["requirement_reextraction_queue_rows"],
    )

    assert plan["plan_id"] == "inactive-public-refresh-guardrail-recompile-plan-v1"
    assert plan["execution_mode"] == "offline_fixture_only"
    assert plan["performs_live_extraction"] is False
    assert plan["performs_live_crawling"] is False
    assert plan["downloads_documents"] is False
    assert plan["opens_devhub"] is False
    assert plan["performs_official_actions"] is False
    assert plan["mutates_active_guardrails"] is False
    assert plan["input_counts"]["paired_candidate_rows"] == 2

    candidates = plan["inactive_guardrail_bundle_recompile_candidates"]
    assert len(candidates) == 2
    assert candidates[0]["bundle_state"] == "inactive"
    assert candidates[0]["source_mode"] == "fixture_only"
    assert candidates[0]["guardrail_bundle"]["activation_status"] == "inactive_hold"
    assert candidates[0]["deterministic_predicate_placeholder_changes"]
    assert candidates[0]["reversible_action_predicate_impacts"]
    assert candidates[0]["exact_confirmation_predicate_impacts"]
    assert candidates[0]["refused_action_predicate_impacts"]
    assert candidates[0]["explanation_template_refresh_notes"]
    assert candidates[0]["validation_status_holds"]
    assert candidates[0]["rollback_notes"]
    assert plan["exact_offline_validation_commands"]


def test_blocked_live_terms_are_reported_but_not_executed() -> None:
    plan = assemble_inactive_public_refresh_recompile_plan(
        [
            {
                "row_id": "delta-live-term",
                "process_model_id": "public-refresh-intake",
                "delta_kind": "fixture_mentions_do_not_crawl",
            }
        ],
        [
            {
                "row_id": "queue-live-term",
                "requirement_id": "req-live-term",
                "queue_reason": "synthetic row says do not open DevHub or download documents",
            }
        ],
    )

    assert "crawl" in plan["blocked_live_action_terms_observed_in_fixtures"]
    assert "devhub" in plan["blocked_live_action_terms_observed_in_fixtures"]
    assert "download" in plan["blocked_live_action_terms_observed_in_fixtures"]
    assert plan["performs_live_crawling"] is False
    assert plan["downloads_documents"] is False
    assert plan["opens_devhub"] is False
