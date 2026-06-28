from __future__ import annotations

import json
from pathlib import Path

from ppd.release_decision_packet_v5 import validate_release_decision_packet_v5

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    with (FIXTURES / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_release_decision_packet_v5_accepts_complete_inactive_packet() -> None:
    packet = load_fixture("release_decision_packet_v5_valid.json")

    assert validate_release_decision_packet_v5(packet) == []


def test_release_decision_packet_v5_rejects_missing_required_sections() -> None:
    packet = load_fixture("release_decision_packet_v5_valid.json")
    for field in (
        "inactive_promotion_candidate_references",
        "go_no_go_recommendation",
        "unresolved_hold_inventory",
        "source_freshness_clearance_status",
        "agent_api_compatibility_caveats",
        "rollback_owner_placeholders",
        "post_decision_smoke_replay_plan",
        "agent_notification_notes",
        "validation_commands",
    ):
        candidate = dict(packet)
        candidate.pop(field)

        errors = validate_release_decision_packet_v5(candidate)

        assert f"missing required field: {field}" in errors


def test_release_decision_packet_v5_rejects_forbidden_claims_and_artifacts() -> None:
    packet = load_fixture("release_decision_packet_v5_valid.json")
    packet.update(
        {
            "status_note": "Activation complete and permit issued with guaranteed approval.",
            "session_cookie": "do-not-commit",
            "mutation_enabled": True,
            "dry_run": False,
        }
    )

    errors = validate_release_decision_packet_v5(packet)
    joined = "\n".join(errors)

    assert "active activation claim is not allowed" in joined
    assert "official-action completion claim is not allowed" in joined
    assert "legal or permitting guarantee is not allowed" in joined
    assert "private/session/auth artifact field is not allowed: session_cookie" in joined
    assert "active mutation flag is not allowed: mutation_enabled" in joined
    assert "active mutation dry_run=false is not allowed: dry_run" in joined
