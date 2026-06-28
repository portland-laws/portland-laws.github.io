from __future__ import annotations

import json
from pathlib import Path

from ppd.agent_readiness.post_recompile_agent_readiness_replay_packet_v1 import (
    EXACT_OFFLINE_VALIDATION_COMMANDS,
    build_replay_packet,
    build_replay_packet_from_fixture,
)
from ppd.validation.post_recompile_agent_readiness_replay_packet_v1 import validate_packet

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "post_recompile_agent_readiness_replay_packet_v1"


def test_builds_valid_packet_from_synthetic_inactive_rows_fixture() -> None:
    packet = build_replay_packet_from_fixture(FIXTURE_DIR / "inactive_guardrail_bundle_promotion_candidate_rows.json")

    assert validate_packet(packet) == []
    assert packet["source_kind"] == "synthetic_inactive_guardrail_bundle_promotion_candidate_rows"
    assert packet["exact_offline_validation_commands"] == EXACT_OFFLINE_VALIDATION_COMMANDS
    assert packet["validation_commands"] == [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]]


def test_committed_valid_packet_fixture_is_valid() -> None:
    packet = json.loads((FIXTURE_DIR / "valid_packet.json").read_text(encoding="utf-8"))

    assert validate_packet(packet) == []


def test_rejects_live_or_mutating_claims() -> None:
    packet = json.loads((FIXTURE_DIR / "valid_packet.json").read_text(encoding="utf-8"))
    packet["non_mutation_flags"]["active_guardrail_change"] = True
    packet["notes"] = "Opened DevHub and stored browser state."

    errors = validate_packet(packet)

    assert "non_mutation_flags must exactly deny active mutations, live DevHub, crawling, private artifacts, and official actions" in errors
    assert any("opened devhub" in error for error in errors)
    assert any("browser state" in error for error in errors)
    assert any("forbidden active/live/private/official mutation flag" in error for error in errors)


def test_rejects_missing_required_replay_coverage() -> None:
    packet = build_replay_packet(
        [
            {
                "row_type": "inactive_guardrail_bundle_promotion_candidate",
                "row_id": "candidate-row-001",
                "candidate_label": "Synthetic inactive bundle row candidate",
                "synthetic": True,
                "candidate_state": "inactive",
                "citation_placeholder_ids": ["citation-placeholder-001"],
            }
        ]
    )
    packet["replay_cases"][0]["missing_information_prompts"] = []
    packet["replay_cases"][0]["blocked_action_decisions"][0]["decision"] = "allowed"
    packet["citation_placeholder_coverage"]["placeholder_ids"] = []

    errors = validate_packet(packet)

    assert "replay_cases[0].missing_information_prompts must be non-empty" in errors
    assert "replay_cases[0].blocked_action_decisions[0].decision must be blocked" in errors
    assert "citation_placeholder_coverage.placeholder_ids must exactly match replay case citation placeholders" in errors


def test_rejects_missing_inactive_candidate_reference_and_required_checks() -> None:
    packet = build_replay_packet(
        [
            {
                "row_type": "inactive_guardrail_bundle_promotion_candidate",
                "row_id": "candidate-row-001",
                "candidate_label": "Synthetic inactive bundle row candidate",
                "synthetic": True,
                "candidate_state": "inactive",
                "citation_placeholder_ids": ["citation-placeholder-001"],
            }
        ]
    )
    case = packet["replay_cases"][0]
    case["source_row_id"] = "missing-row"
    case["source_candidate_label"] = "synthetic row"
    case["missing_information_prompts"][0]["prompt_kind"] = "general_question"
    case["missing_information_prompts"][0]["expected_prompt"] = ""
    case["blocked_action_decisions"][0]["reason"] = ""
    case["reversible_draft_eligibility_decisions"][0]["eligible"] = False
    case["reversible_draft_eligibility_decisions"][0]["requires_user_attendance"] = True
    case["reversible_draft_eligibility_decisions"][0]["forbidden_escalation"] = ""
    case["exact_confirmation_warnings"][0]["warning"] = ""
    case["refused_action_explanations"][0]["expected_explanation"] = ""
    case["regression_notes"][0]["note"] = ""
    case["reviewer_holds"][0]["status"] = "released"
    case["reviewer_holds"][0]["reason"] = ""
    case["rollback_notes"][0]["note"] = ""

    errors = validate_packet(packet)

    assert "replay_cases[0].source_row_id must reference consumed_row_ids" in errors
    assert "replay_cases[0].source_candidate_label must identify an inactive promotion candidate" in errors
    assert "replay_cases[0].missing_information_prompts[0].prompt_kind must be missing_information" in errors
    assert "replay_cases[0].missing_information_prompts[0].expected_prompt must be non-empty" in errors
    assert "replay_cases[0].blocked_action_decisions[0].reason must be non-empty" in errors
    assert "replay_cases[0].reversible_draft_eligibility_decisions[0].eligible must be true" in errors
    assert "replay_cases[0].reversible_draft_eligibility_decisions[0].requires_user_attendance must be false" in errors
    assert "replay_cases[0].reversible_draft_eligibility_decisions[0].forbidden_escalation must be non-empty" in errors
    assert "replay_cases[0].exact_confirmation_warnings[0].warning must be non-empty" in errors
    assert "replay_cases[0].refused_action_explanations[0].expected_explanation must be non-empty" in errors
    assert "replay_cases[0].regression_notes[0].note must be non-empty" in errors
    assert "replay_cases[0].reviewer_holds[0].status must be held_for_manual_review" in errors
    assert "replay_cases[0].reviewer_holds[0].reason must be non-empty" in errors
    assert "replay_cases[0].rollback_notes[0].note must be non-empty" in errors


def test_rejects_private_raw_downloaded_live_mutation_completion_and_guarantee_claims() -> None:
    packet = json.loads((FIXTURE_DIR / "valid_packet.json").read_text(encoding="utf-8"))
    packet["raw_downloaded_artifact"] = "tmp/private/downloaded.pdf"
    packet["live_crawl_started"] = True
    packet["official_action_completed"] = True
    packet["claims"] = [
        "Live crawl finished against public sources.",
        "Downloaded document was retained for review.",
        "Updated active prompt and mutated active guardrail.",
        "Official action completed after submission.",
        "Permit will be approved as a legal guarantee.",
    ]

    errors = validate_packet(packet)

    assert any("raw_downloaded_artifact" in error for error in errors)
    assert any("live_crawl_started" in error for error in errors)
    assert any("official_action_completed" in error for error in errors)
    assert any("live crawl" in error for error in errors)
    assert any("downloaded document" in error for error in errors)
    assert any("updated active prompt" in error for error in errors)
    assert any("mutated active guardrail" in error for error in errors)
    assert any("official action completed" in error for error in errors)
    assert any("permit will be approved" in error for error in errors)
    assert any("legal guarantee" in error for error in errors)


def test_builder_rejects_non_synthetic_or_active_rows() -> None:
    bad_rows = [
        {
            "row_type": "inactive_guardrail_bundle_promotion_candidate",
            "row_id": "candidate-row-001",
            "synthetic": False,
            "candidate_state": "active",
            "citation_placeholder_ids": ["citation-placeholder-001"],
        }
    ]

    try:
        build_replay_packet(bad_rows)
    except ValueError as exc:
        message = str(exc)
    else:
        raise AssertionError("expected ValueError")

    assert "must be marked synthetic" in message
