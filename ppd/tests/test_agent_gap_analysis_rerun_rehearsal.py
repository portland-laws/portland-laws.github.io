from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ppd.agent_gap_analysis_rerun_rehearsal import (
    GapAnalysisRerunRehearsalError,
    build_gap_analysis_rerun_rehearsal_packet,
    validate_gap_analysis_rerun_rehearsal_packet,
)

FIXTURES = Path(__file__).parent / "fixtures"
PROCESS_IMPACT_PACKET = FIXTURES / "process_model_impact_rehearsal" / "synthetic_packet.json"
PROMPT_CORPUS = FIXTURES / "agent_missing_information_prompt_corpus" / "corpus.json"
EXPECTED_PACKET = FIXTURES / "gap_analysis_rerun_rehearsal" / "expected_packet.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_builds_fixture_first_gap_analysis_rerun_rehearsal_packet() -> None:
    packet = build_gap_analysis_rerun_rehearsal_packet(_load(PROCESS_IMPACT_PACKET), _load(PROMPT_CORPUS))

    assert packet == _load(EXPECTED_PACKET)
    assert validate_gap_analysis_rerun_rehearsal_packet(packet) == []
    assert packet["execution_boundaries"] == {
        "calls_llm": False,
        "launches_devhub": False,
        "uses_authenticated_session": False,
        "reads_private_files": False,
        "runs_agent_consumers": False,
        "writes_private_artifacts": False,
    }


def test_rehearsal_packet_contains_cited_deltas_prompts_notes_blocks_and_safe_actions() -> None:
    packet = build_gap_analysis_rerun_rehearsal_packet(_load(PROCESS_IMPACT_PACKET), _load(PROMPT_CORPUS))

    assert len(packet["synthetic_case_deltas"]) == 3
    assert len(packet["missing_fact_prompts"]) == 3
    assert {note["kind"] for note in packet["stale_conflicting_evidence_notes"]} == {"stale_evidence"}
    assert {action["action_id"] for action in packet["blocked_action_expectations"]} == {
        "certify_acknowledgement",
        "purchase_trade_permit",
        "submit_payment",
        "submit_permit_application",
        "upload_to_official_record",
    }
    assert all(row["source_evidence_ids"] for group in (
        "synthetic_case_deltas",
        "missing_fact_prompts",
        "stale_conflicting_evidence_notes",
        "blocked_action_expectations",
        "next_safe_action_candidates",
    ) for row in packet[group])
    assert all(action["requires_devhub"] is False for action in packet["next_safe_action_candidates"])
    assert all(action["reads_private_files"] is False for action in packet["next_safe_action_candidates"])
    assert all(action["runs_agent_consumer"] is False for action in packet["next_safe_action_candidates"])


def test_rehearsal_rejects_private_inputs_and_live_execution_flags() -> None:
    process_packet = _load(PROCESS_IMPACT_PACKET)
    prompt_corpus = _load(PROMPT_CORPUS)
    prompt_corpus["synthetic_user_cases"][0]["private_path"] = "/home/example/private-case.pdf"
    prompt_corpus["synthetic_user_cases"][0]["calls_llm"] = True

    with pytest.raises(GapAnalysisRerunRehearsalError) as excinfo:
        build_gap_analysis_rerun_rehearsal_packet(process_packet, prompt_corpus)

    assert "private_input_present" in str(excinfo.value)
    assert "live_execution_requested" in str(excinfo.value)


def test_validation_rejects_downgraded_blocked_actions_and_unsafe_next_actions() -> None:
    packet = build_gap_analysis_rerun_rehearsal_packet(_load(PROCESS_IMPACT_PACKET), _load(PROMPT_CORPUS))
    unsafe = copy.deepcopy(packet)
    unsafe["blocked_action_expectations"][0]["blocked"] = False
    unsafe["next_safe_action_candidates"][0]["requires_devhub"] = True

    codes = {issue.code for issue in validate_gap_analysis_rerun_rehearsal_packet(unsafe)}

    assert "blocked_action_not_blocked" in codes
    assert "unsafe_next_action" in codes
