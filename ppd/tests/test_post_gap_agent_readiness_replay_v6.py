import json
from pathlib import Path

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "post_gap_agent_readiness_v6"
GAP_PACKET_PATH = FIXTURE_DIR / "user_gap_analysis_packet_v6.json"
JOURNAL_PACKET_PATH = FIXTURE_DIR / "action_journal_dry_run_packet_v6.json"


def load_fixture(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def replay_agent_response(gap_packet, dry_run_packet, request):
    events = [
        "gap_packet_loaded",
        "dry_run_packet_loaded",
        "synthetic_request_received",
    ]
    questions = sorted(gap_packet["missing_information_questions"], key=lambda item: item["order"])
    events.append("missing_information_questions_ordered")

    limitations = []
    citations = []
    for evidence in gap_packet["evidence"]:
        citation = evidence.get("citation", {})
        citations.append(citation)
        if evidence.get("status") == "stale":
            limitations.append(
                {
                    "evidence_id": evidence["id"],
                    "kind": "stale",
                    "explanation": evidence["stale_reason"],
                }
            )
        if evidence.get("status") == "conflicting":
            limitations.append(
                {
                    "evidence_id": evidence["id"],
                    "kind": "conflicting",
                    "explanation": evidence["conflict_reason"],
                }
            )
    events.append("evidence_limitations_explained")
    events.append("citation_payload_attached")

    refused = request["action_kind"] in dry_run_packet["refused_action_kinds"]
    if refused:
        route = "refused_manual_handoff"
    elif request["action_kind"] == "draft_preview":
        route = dry_run_packet["allowed_routes"]["draft_preview"]
    elif request["action_kind"] == "pdf_preview":
        route = dry_run_packet["allowed_routes"]["pdf_preview"]
    else:
        route = "manual_handoff_only"
    events.append("route_selected")
    events.append("manual_handoff_reminder_attached")
    events.append("offline_validation_commands_reported")

    return {
        "request_id": request["id"],
        "route": route,
        "refused": refused,
        "questions": questions,
        "limitations": limitations,
        "citations": citations,
        "manual_handoff_reminders": gap_packet["manual_handoff_reminders"],
        "journal_events": events,
        "offline_validation_commands": dry_run_packet["offline_validation_commands"],
        "activated_guardrails": False,
        "opened_devhub": False,
        "read_private_documents": False,
        "uploaded": False,
        "submitted": False,
        "certified": False,
        "paid": False,
        "scheduled": False,
        "made_legal_or_permitting_guarantee": False,
    }


def synthetic_requests():
    return [
        {"id": "req_questions", "action_kind": "ask_missing_information"},
        {"id": "req_draft", "action_kind": "draft_preview"},
        {"id": "req_pdf", "action_kind": "pdf_preview"},
        {"id": "req_submit", "action_kind": "submit"},
        {"id": "req_pay", "action_kind": "pay"},
        {"id": "req_financial", "action_kind": "financial_commitment"},
    ]


def test_post_gap_agent_readiness_replay_v6_fixture_first_contract():
    gap_packet = load_fixture(GAP_PACKET_PATH)
    dry_run_packet = load_fixture(JOURNAL_PACKET_PATH)

    responses = [replay_agent_response(gap_packet, dry_run_packet, request) for request in synthetic_requests()]
    by_id = {response["request_id"]: response for response in responses}

    question_ids = [item["id"] for item in by_id["req_questions"]["questions"]]
    assert question_ids == [
        "q01_property_address",
        "q02_scope_summary",
        "q03_existing_use",
        "q04_documents_available",
    ]

    limitations = by_id["req_questions"]["limitations"]
    assert {item["kind"] for item in limitations} == {"stale", "conflicting"}
    assert all(item["explanation"] for item in limitations)

    assert by_id["req_draft"]["route"] == "reversible_local_draft_preview"
    assert by_id["req_pdf"]["route"] == "local_pdf_preview_only"
    assert by_id["req_submit"]["route"] == "refused_manual_handoff"
    assert by_id["req_pay"]["route"] == "refused_manual_handoff"
    assert by_id["req_financial"]["route"] == "refused_manual_handoff"
    assert by_id["req_submit"]["refused"] is True
    assert by_id["req_pay"]["refused"] is True
    assert by_id["req_financial"]["refused"] is True

    for response in responses:
        assert response["journal_events"] == dry_run_packet["expected_journal_events"]
        assert response["manual_handoff_reminders"] == gap_packet["manual_handoff_reminders"]
        assert response["offline_validation_commands"] == [
            ["python3", "-m", "py_compile", "ppd/tests/test_post_gap_agent_readiness_replay_v6.py"],
            ["python3", "-m", "pytest", "ppd/tests/test_post_gap_agent_readiness_replay_v6.py"],
        ]
        assert response["activated_guardrails"] is False
        assert response["opened_devhub"] is False
        assert response["read_private_documents"] is False
        assert response["uploaded"] is False
        assert response["submitted"] is False
        assert response["certified"] is False
        assert response["paid"] is False
        assert response["scheduled"] is False
        assert response["made_legal_or_permitting_guarantee"] is False

        for citation in response["citations"]:
            assert set(gap_packet["citation_payload_required_keys"]).issubset(citation)
            assert citation["url"].startswith("fixture://")


def test_post_gap_agent_readiness_replay_v6_validation_commands_are_offline_only():
    dry_run_packet = load_fixture(JOURNAL_PACKET_PATH)
    commands = dry_run_packet["offline_validation_commands"]
    flattened = " ".join(part for command in commands for part in command)

    assert commands == [
        ["python3", "-m", "py_compile", "ppd/tests/test_post_gap_agent_readiness_replay_v6.py"],
        ["python3", "-m", "pytest", "ppd/tests/test_post_gap_agent_readiness_replay_v6.py"],
    ]
    for forbidden in [
        "curl",
        "wget",
        "playwright",
        "devhub",
        "upload",
        "submit",
        "certify",
        "pay",
        "schedule",
        "captcha",
        "mfa",
    ]:
        assert forbidden not in flattened.lower()
