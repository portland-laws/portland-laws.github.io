from __future__ import annotations

import json
from pathlib import Path

import pytest

from ppd.logic.agent_gap_analysis_rerun_packet import compile_agent_gap_analysis_rerun_packet

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "agent_gap_analysis_rerun_packet"


def _load_fixture(name: str) -> dict:
    with (FIXTURE_DIR / name).open(encoding="utf-8") as handle:
        return json.load(handle)


def test_rerun_packet_uses_draft_candidate_and_reports_changed_gaps() -> None:
    packet = compile_agent_gap_analysis_rerun_packet(_load_fixture("synthetic_case_packet.json"))

    assert packet["packet_status"] == "fixture_only_no_private_file_reads_no_devhub_launch"
    assert packet["guardrail_candidate"]["candidate_status"] == "draft_review_required"
    assert packet["guardrail_candidate"]["does_not_replace_active_bundle"] is True
    assert "supporting_documents_are_separate_pdfs" not in packet["baseline_missing_facts"]
    assert "supporting_documents_are_separate_pdfs" in packet["rerun_missing_facts"]
    assert packet["changed_missing_facts"]["added"] == ["supporting_documents_are_separate_pdfs"]


def test_rerun_packet_surfaces_stale_evidence_blocked_actions_and_handoffs() -> None:
    packet = compile_agent_gap_analysis_rerun_packet(_load_fixture("synthetic_case_packet.json"))

    assert packet["stale_evidence"] == ["property_owner_authorization", "site_plan_doc"]
    blocked_ids = {action["action_id"] for action in packet["blocked_actions"]}
    assert {"submit permit application", "upload supporting documents"}.issubset(blocked_ids)
    assert all(action["requires_exact_confirmation"] for action in packet["blocked_actions"])
    handoff_ids = {handoff["handoff_id"] for handoff in packet["manual_handoffs"]}
    assert {"submit permit application", "upload supporting documents"}.issubset(handoff_ids)


def test_rerun_packet_allows_only_local_previews_and_user_questions() -> None:
    packet = compile_agent_gap_analysis_rerun_packet(_load_fixture("synthetic_case_packet.json"))

    assert packet["allowed_local_previews"]
    assert all(preview["allowed"] is True for preview in packet["allowed_local_previews"])
    assert all(preview["requires_devhub"] is False for preview in packet["allowed_local_previews"])
    assert all(preview["requires_private_file_read"] is False for preview in packet["allowed_local_previews"])
    question_ids = {question["question_id"] for question in packet["user_facing_questions"]}
    assert "missing_fact.supporting_documents_are_separate_pdfs" in question_ids
    assert "stale_evidence.site_plan_doc" in question_ids


def test_rerun_packet_rejects_private_paths_and_live_devhub_launch() -> None:
    fixture = _load_fixture("synthetic_case_packet.json")
    fixture["synthetic_case"]["private_path"] = "/home/alex/private/devhub/session.json"
    with pytest.raises(ValueError):
        compile_agent_gap_analysis_rerun_packet(fixture)

    fixture = _load_fixture("synthetic_case_packet.json")
    fixture["synthetic_case"]["launch_devhub"] = True
    with pytest.raises(ValueError):
        compile_agent_gap_analysis_rerun_packet(fixture)
