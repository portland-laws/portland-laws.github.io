from __future__ import annotations

import json
from pathlib import Path

from ppd.logic.unsupported_path_escalation import evaluate_unsupported_path_escalation


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "unsupported_paths"
    / "manual_review_permit_processes.json"
)


def _load_process(process_id: str) -> dict[str, object]:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    for process in fixture["processes"]:
        if process["process_id"] == process_id:
            return process
    raise AssertionError(f"fixture process not found: {process_id}")


def test_unsupported_email_or_manual_review_path_blocks_devhub_draft_automation() -> None:
    process = _load_process("fixture_ppd_unsupported_manual_review_appeal")

    decision = evaluate_unsupported_path_escalation(process, "devhub_draft_application")
    result = decision.to_dict()

    assert result["blocked"] is True
    assert result["blocked_actions"] == ["devhub_draft_application"]
    assert "DevHub draft" in result["user_visible_reason"]
    assert result["source_evidence_ids"] == [
        "ppd_source_apply_permits_email_path",
        "ppd_source_manual_review_required",
    ]
    assert result["manual_handoff_recommendations"] == [
        "Do not create or edit a DevHub draft application for this permit path.",
        "Show the user the cited PP&D guidance and prepare a manual handoff checklist for the email or staff-review process.",
        "Ask the user to complete any official email, staff intake, certification, payment, or submission step themselves.",
    ]
    assert "manual_handoff" in result["next_safe_actions"]
    assert "show_source_evidence" in result["next_safe_actions"]


def test_supported_process_is_not_blocked_by_unsupported_path_guardrail() -> None:
    process = _load_process("fixture_ppd_supported_devhub_trade_permit")

    decision = evaluate_unsupported_path_escalation(process, "devhub_draft_application")
    result = decision.to_dict()

    assert result["blocked"] is False
    assert result["blocked_actions"] == []
    assert result["source_evidence_ids"] == []
    assert result["manual_handoff_recommendations"] == []
    assert result["next_safe_actions"] == ["continue_guardrail_evaluation"]
