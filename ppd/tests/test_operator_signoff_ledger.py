import json
from pathlib import Path

from ppd.operator_signoff_ledger import validate_operator_signoff_ledger_packet


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "operator_signoff_ledger_packets"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_valid_operator_signoff_ledger_packet_passes() -> None:
    result = validate_operator_signoff_ledger_packet(load_fixture("valid_packet.json"))

    assert result.ok
    assert result.errors == ()


def test_operator_signoff_ledger_rejects_missing_review_prompts() -> None:
    packet = load_fixture("valid_packet.json")
    packet["reviewer_prompts"] = []

    result = validate_operator_signoff_ledger_packet(packet)

    assert not result.ok
    assert "missing reviewer prompts" in result.errors


def test_operator_signoff_ledger_rejects_missing_prerequisite_links() -> None:
    packet = load_fixture("valid_packet.json")
    packet["prerequisite_packet_links"] = []

    result = validate_operator_signoff_ledger_packet(packet)

    assert not result.ok
    assert "missing prerequisite packet links" in result.errors


def test_operator_signoff_ledger_rejects_unsafe_artifact_references() -> None:
    packet = load_fixture("valid_packet.json")
    packet["artifacts"] = [{"kind": "trace", "ref": "redacted-browser-recording"}]

    result = validate_operator_signoff_ledger_packet(packet)

    assert not result.ok
    assert any(error.startswith("unsafe artifact references:") for error in result.errors)


def test_operator_signoff_ledger_rejects_unresolved_blocker_marked_approved() -> None:
    packet = load_fixture("valid_packet.json")
    packet["blockers"] = [{"blocker_id": "missing-source", "status": "open", "approved": True}]

    result = validate_operator_signoff_ledger_packet(packet)

    assert not result.ok
    assert "unresolved blocker marked approved" in result.errors


def test_operator_signoff_ledger_rejects_unsigned_production_promotion() -> None:
    packet = load_fixture("valid_packet.json")
    packet["production_promotion"]["signatures"] = {"operator": "fixture-operator"}

    result = validate_operator_signoff_ledger_packet(packet)

    assert not result.ok
    assert "unsigned production promotion" in result.errors


def test_operator_signoff_ledger_rejects_forbidden_official_action_enablement() -> None:
    packet = load_fixture("valid_packet.json")
    packet["action_enablements"] = [
        {"action": "payment_detail_entry", "enabled": True},
        {"action": "upload_corrections", "allowed": True},
        {"action": "permit_submission", "state": "enabled"},
        {"action": "inspection_scheduling", "enabled": True},
        {"action": "permit_cancellation", "enabled": True},
        {"action": "application_certification", "enabled": True}
    ]

    result = validate_operator_signoff_ledger_packet(packet)

    assert not result.ok
    matching_errors = [error for error in result.errors if error.startswith("forbidden official-action enablement:")]
    assert matching_errors
    message = matching_errors[0]
    assert "payment_detail_entry" in message
    assert "upload_corrections" in message
    assert "permit_submission" in message
    assert "inspection_scheduling" in message
    assert "permit_cancellation" in message
    assert "application_certification" in message
