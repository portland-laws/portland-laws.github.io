from __future__ import annotations

import json
from pathlib import Path

from ppd.release_blockers import reconcile_agent_readiness_release_blockers


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "release_blockers" / "agent_readiness_inputs.json"


def _load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_reconciliation_packet_is_fixture_first_and_live_actions_disabled() -> None:
    fixture = _load_fixture()

    packet = reconcile_agent_readiness_release_blockers(
        fixture["guardrail_consumer_contract_audit"],
        fixture["post_release_audit_findings"],
        fixture["safe_next_action_user_handoff_checklist"],
    )

    assert packet["fixture_first"] is True
    assert packet["live_actions_disabled"] is True
    assert packet["consumers_invoked"] is False
    assert packet["devhub_launched"] is False
    assert packet["urls_fetched"] is False
    assert packet["guardrail_bundles_changed"] is False
    assert packet["disabled_live_action_attestations"]
    prohibited_actions = packet["disabled_live_action_attestations"][0]["prohibited_actions"]
    assert "submit_permit_request" in prohibited_actions
    assert "execute_payment" in prohibited_actions


def test_reconciliation_packet_preserves_cited_blockers_and_reviewer_owners() -> None:
    fixture = _load_fixture()

    packet = reconcile_agent_readiness_release_blockers(
        fixture["guardrail_consumer_contract_audit"],
        fixture["post_release_audit_findings"],
        fixture["safe_next_action_user_handoff_checklist"],
    )

    blockers = packet["remaining_blockers"]
    blocker_ids = {blocker["blocker_id"] for blocker in blockers}
    assert "guardrail-consumer-contract-missing-action-gate" in blocker_ids
    assert "post-release-audit-no-owner-routing" in blocker_ids
    assert "handoff-exact-confirmation-copy-missing" in blocker_ids
    assert all(blocker["citations"] for blocker in blockers)

    owner_names = {owner["owner"] for owner in packet["reviewer_owners"]}
    assert "guardrail-contract-reviewer" in owner_names
    assert "post-release-audit-reviewer" in owner_names
    assert "user-handoff-reviewer" in owner_names


def test_reconciliation_packet_acknowledges_stale_evidence_and_recommends_offline_work() -> None:
    fixture = _load_fixture()

    packet = reconcile_agent_readiness_release_blockers(
        fixture["guardrail_consumer_contract_audit"],
        fixture["post_release_audit_findings"],
        fixture["safe_next_action_user_handoff_checklist"],
    )

    stale_ids = {item["evidence_id"] for item in packet["stale_evidence_acknowledgements"]}
    assert "guardrail-consumer-contract-source-freshness-20260508" in stale_ids
    assert "post-release-audit-open-findings-snapshot" in stale_ids

    recommendations = packet["next_offline_daemon_recommendations"]
    assert recommendations
    assert all(recommendation["mode"] == "offline_only" for recommendation in recommendations)
    assert {recommendation["recommendation_id"] for recommendation in recommendations} >= {
        "offline-review-open-blockers",
        "offline-validate-fixtures",
        "offline-keep-live-actions-disabled",
    }
