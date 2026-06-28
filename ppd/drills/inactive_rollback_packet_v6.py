"""Inactive rollback drill packet v6.

This module is fixture-first by design. It reads an inactive guardrail smoke
replay plan fixture and assembles an offline rollback drill packet. It does not
activate, roll back, crawl, upload, submit, schedule, pay, certify, or open any
external PP&D system.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PACKET_VERSION = "inactive-rollback-drill-packet-v6"
SOURCE_FIXTURE_KIND = "inactive-guardrail-smoke-replay-plan-v6"


def load_replay_plan(path: Path) -> dict[str, Any]:
    """Load and validate an inactive replay plan fixture."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("fixture_kind") != SOURCE_FIXTURE_KIND:
        raise ValueError("expected inactive guardrail smoke replay plan v6 fixture")
    if data.get("mode") != "inactive_fixture_replay_only":
        raise ValueError("fixture must be inactive replay only")
    if data.get("live_actions_allowed") is not False:
        raise ValueError("fixture must explicitly disallow live actions")
    return data


def build_packet(plan: dict[str, Any]) -> dict[str, Any]:
    """Build a deterministic inactive rollback drill packet from fixtures only."""
    replay_rows = plan.get("replay_rows", [])
    held_sources = plan.get("held_sources", [])
    affected_agents = plan.get("affected_agents", [])
    downgrade_expectations = plan.get("safe_downgrade_expectations", [])

    decision_rows = []
    for index, row in enumerate(replay_rows, start=1):
        decision_rows.append(
            {
                "row_id": f"rollback-decision-v6-{index:02d}",
                "source_replay_id": row["replay_id"],
                "guardrail": row["guardrail"],
                "observed_fixture_result": row["observed_result"],
                "rollback_decision": "hold_inactive_no_live_rollback",
                "reason": row["rollback_reason"],
                "required_manual_reviewer": "manual_reviewer_placeholder",
                "approval_status": "not_requested_fixture_only",
            }
        )

    citation_checks = []
    for source in held_sources:
        citation_checks.append(
            {
                "source_id": source["source_id"],
                "title": source["title"],
                "held_citation": source["citation"],
                "continuity_check": "citation_retained_from_fixture",
                "private_document_accessed": False,
            }
        )

    capability_notes = []
    for agent in affected_agents:
        capability_notes.append(
            {
                "agent_id": agent["agent_id"],
                "capability": agent["capability"],
                "inactive_effect": agent["inactive_effect"],
                "live_guardrail_changed": False,
            }
        )

    journal_templates = []
    for event_name in plan.get("recovery_journal_event_names", []):
        journal_templates.append(
            {
                "event_name": event_name,
                "timestamp_utc": "",
                "operator": "",
                "notes": "",
                "evidence_fixture_ids": [row["replay_id"] for row in replay_rows],
            }
        )

    return {
        "packet_version": PACKET_VERSION,
        "source_fixture_kind": plan["fixture_kind"],
        "mode": "inactive_fixture_packet_only",
        "prohibited_actions": plan["prohibited_actions"],
        "rollback_decision_rows": decision_rows,
        "held_source_citation_continuity_checks": citation_checks,
        "affected_agent_capability_notes": capability_notes,
        "safe_downgrade_expectations": downgrade_expectations,
        "manual_reviewer_approval_placeholders": [
            {
                "approval_id": "manual-reviewer-approval-v6-01",
                "reviewer_name": "",
                "reviewed_at_utc": "",
                "decision": "",
                "comments": "",
            }
        ],
        "recovery_journal_event_templates": journal_templates,
        "offline_validation_commands": plan["offline_validation_commands"],
        "live_guardrails_activated": False,
        "live_guardrails_rolled_back": False,
        "devhub_opened": False,
        "live_sites_crawled": False,
        "private_documents_read": False,
    }


def build_packet_from_fixture(path: Path) -> dict[str, Any]:
    return build_packet(load_replay_plan(path))
