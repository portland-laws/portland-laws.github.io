from ppd.devhub.unsupported_path_escalation import (
    classify_unsupported_actions,
    escalate_unsupported_path,
    escalation_from_mapping,
)


def test_classifies_known_consequential_actions() -> None:
    actions = classify_unsupported_actions(
        "User asks the worker to upload corrections, certify the acknowledgement, and submit payment."
    )

    assert actions == ("certification", "payment", "upload")


def test_unknown_path_becomes_manual_unclear_escalation() -> None:
    escalation = escalate_unsupported_path(
        "unknown-devhub-branch",
        "DevHub displays a branch that is not in the supported public process model.",
        source_evidence_ids=("source:devhub-faq",),
    )

    assert escalation.blocked_actions == ("unsupported_or_unclear_path",)
    assert escalation.required_handoff == "manual_user_handoff"
    assert escalation.requires_attendance is True
    assert escalation.requires_exact_confirmation is True
    assert escalation.source_evidence_ids == ("source:devhub-faq",)

    journal_event = escalation.to_journal_event()
    assert journal_event["event_type"] == "manual_handoff"
    assert journal_event["blocked_actions"] == ["unsupported_or_unclear_path"]
    assert "private" not in journal_event


def test_mapping_input_keeps_record_redacted_and_deterministic() -> None:
    escalation = escalation_from_mapping(
        {
            "path_id": "fee-payment",
            "description": "Enter credit card details and submit payment in DevHub.",
            "explicit_actions": ["payment"],
            "source_evidence_ids": ["source:fee-payment-guide"],
        }
    )

    assert escalation.path_id == "fee-payment"
    assert escalation.blocked_actions == ("payment",)
    assert escalation.to_journal_event() == {
        "event_type": "manual_handoff",
        "path_id": "fee-payment",
        "reason": "Unsupported PP&D path requires manual handoff before payment: Enter credit card details and submit payment in DevHub.",
        "blocked_actions": ["payment"],
        "required_handoff": "manual_user_handoff",
        "requires_attendance": True,
        "requires_exact_confirmation": True,
        "next_safe_actions": [
            "explain why the path is unsupported for unattended automation",
            "ask the user to handle the official step directly in the live PP&D or DevHub surface",
            "continue only with source-backed read-only review or reversible local draft work",
        ],
        "source_evidence_ids": ["source:fee-payment-guide"],
    }


def test_path_id_is_required() -> None:
    try:
        escalate_unsupported_path(" ", "submit")
    except ValueError as exc:
        assert str(exc) == "path_id is required"
    else:
        raise AssertionError("expected ValueError")
