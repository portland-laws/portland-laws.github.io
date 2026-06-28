from __future__ import annotations

import pytest

from ppd.guardrails.reviewer_packet_v6 import (
    REQUIRED_FIELDS,
    assert_guardrail_recompile_reviewer_packet_v6,
    validate_guardrail_recompile_reviewer_packet_v6,
)


def valid_packet() -> dict[str, object]:
    return {
        "staging_packet_references": ["ppd/tests/fixtures/reviewer_packet_v6/staging_packet.json"],
        "reviewer_comparison_rows": [{"predicate": "fixture-only", "expected": "inactive", "actual": "inactive"}],
        "inactive_guardrail_status_notes": ["Guardrail remains inactive pending review."],
        "source_evidence_continuity_checks": ["Fixture source identifiers match the staging packet references."],
        "deterministic_predicate_review_prompts": ["Confirm predicate output from committed fixtures only."],
        "exact_confirmation_or_refused_action_preservation_summary": "Exact confirmations and refused actions are preserved as review notes only.",
        "stale_evidence_hold_propagation": ["Stale evidence keeps the packet on hold."],
        "rollback_checkpoint_placeholders": ["rollback-owner: TBD", "rollback-command: TBD"],
        "signoff_owner_placeholders": ["legal-review-owner: TBD", "engineering-review-owner: TBD"],
        "validation_commands": [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]],
    }


@pytest.mark.parametrize("field,message", REQUIRED_FIELDS.items())
def test_reviewer_packet_v6_rejects_missing_required_sections(field: str, message: str) -> None:
    packet = valid_packet()
    packet[field] = []

    errors = validate_guardrail_recompile_reviewer_packet_v6(packet)

    assert message in errors


@pytest.mark.parametrize(
    "text,message",
    [
        ("activation complete", "active activation claims"),
        ("executed live crawl", "live crawl execution claims"),
        ("raw crawl artifact", "downloaded or raw crawl artifacts"),
        ("session cookie", "private/session/auth artifacts"),
        ("permit submitted", "official-action completion claims"),
        ("approval guaranteed", "legal or permitting guarantees"),
        ("mutate: true", "active mutation flags"),
    ],
)
def test_reviewer_packet_v6_rejects_forbidden_claims(text: str, message: str) -> None:
    packet = valid_packet()
    packet["inactive_guardrail_status_notes"] = [text]

    errors = validate_guardrail_recompile_reviewer_packet_v6(packet)

    assert message in errors


def test_reviewer_packet_v6_accepts_fixture_only_inactive_packet() -> None:
    assert validate_guardrail_recompile_reviewer_packet_v6(valid_packet()) == []


def test_reviewer_packet_v6_assertion_raises_all_errors() -> None:
    packet = valid_packet()
    packet["validation_commands"] = []
    packet["reviewer_comparison_rows"] = ["dry_run: false"]

    with pytest.raises(ValueError) as excinfo:
        assert_guardrail_recompile_reviewer_packet_v6(packet)

    message = str(excinfo.value)
    assert "missing validation commands" in message
    assert "active mutation flags" in message
