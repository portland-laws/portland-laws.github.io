from __future__ import annotations

import copy
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from ppd.agent_readiness.promotion_audit_log_candidate_packet import (
    build_promotion_audit_log_candidate_packet,
    validate_operator_promotion_approval_packet,
    validate_promotion_audit_log_candidate_packet,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "agent_readiness"


def _load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def _valid_packet() -> dict[str, Any]:
    dry_run_packet = _load_fixture("dry_run_promotion_sequence_packet_fixture.json")
    approval_packet = _load_fixture("operator_promotion_approval_packet_fixture.json")
    return build_promotion_audit_log_candidate_packet(dry_run_packet, approval_packet)


def test_builds_fixture_first_promotion_audit_log_candidate_packet() -> None:
    dry_run_packet = _load_fixture("dry_run_promotion_sequence_packet_fixture.json")
    approval_packet = _load_fixture("operator_promotion_approval_packet_fixture.json")

    approval_result = validate_operator_promotion_approval_packet(approval_packet)
    assert approval_result.valid, approval_result.problems

    packet = build_promotion_audit_log_candidate_packet(dry_run_packet, approval_packet)
    result = validate_promotion_audit_log_candidate_packet(packet)

    assert result.valid, result.problems
    assert packet["candidate_status"] == "candidate_entries_not_written"
    assert packet["audit_log_policy"]["writes_operational_audit_log"] is False
    assert packet["audit_log_policy"]["promotes_artifacts"] is False

    entries = packet["audit_entry_candidates"]
    assert len(entries) == len(dry_run_packet["ordered_synthetic_promotion_steps"])
    for entry in entries:
        assert entry["synthetic_only"] is True
        assert entry["writes_operational_audit_log"] is False
        assert entry["promotes_artifacts"] is False
        assert entry["cited_prerequisites"]
        assert entry["affected_artifact_refs"]
        assert entry["reviewer_owner_fields"]
        assert entry["rollback_links"]
        assert entry["retention_notes"]
        assert entry["source_evidence_ids"]
        assert all(ref["source_evidence_ids"] for ref in entry["affected_artifact_refs"])


def test_rejects_operational_audit_log_write_claim() -> None:
    packet = _valid_packet()

    packet["audit_log_policy"]["writes_operational_audit_log"] = True
    packet["audit_entry_candidates"][0]["writes_operational_audit_log"] = True

    result = validate_promotion_audit_log_candidate_packet(packet)
    assert not result.valid
    assert any("writes_operational_audit_log" in problem for problem in result.problems)


def test_rejects_approval_packet_that_does_not_cite_dry_run_source() -> None:
    dry_run_packet = _load_fixture("dry_run_promotion_sequence_packet_fixture.json")
    approval_packet = _load_fixture("operator_promotion_approval_packet_fixture.json")
    approval_packet["approved_source_packet_ids"] = ["different-packet"]

    with pytest.raises(ValueError, match="must cite the dry-run promotion sequence packet"):
        build_promotion_audit_log_candidate_packet(dry_run_packet, approval_packet)


@pytest.mark.parametrize(
    ("mutate", "expected_problem"),
    [
        (
            lambda packet: packet["audit_entry_candidates"][0].update({"source_evidence_ids": []}),
            "is uncited",
        ),
        (
            lambda packet: packet["audit_entry_candidates"][0].update({"reviewer_owner_fields": []}),
            "reviewer_owner_fields must be a non-empty list",
        ),
        (
            lambda packet: packet["audit_entry_candidates"][0].update({"rollback_links": []}),
            "rollback_links must be a non-empty list",
        ),
        (
            lambda packet: packet["audit_entry_candidates"][0]["rollback_links"][0].update({"source_evidence_ids": []}),
            "rollback_links[0] lacks source_evidence_ids",
        ),
        (
            lambda packet: packet["audit_entry_candidates"][0].update({"diagnostic_ref": "/home/alex/private/devhub-session.json"}),
            "private or runtime artifact reference",
        ),
        (
            lambda packet: packet["audit_entry_candidates"][0].update({"raw_reference": "raw crawl output from a downloaded document"}),
            "raw crawl/download/archive reference",
        ),
        (
            lambda packet: packet["audit_entry_candidates"][0].update({"event_summary": "Operational audit log written for this candidate."}),
            "live execution or operational audit claim",
        ),
        (
            lambda packet: packet["audit_entry_candidates"][0].update({"active_artifact_mutation": True}),
            "mutation or live-operation flag",
        ),
        (
            lambda packet: packet["audit_entry_candidates"][0].update({"event_summary": "Permit approval guaranteed after this review."}),
            "legal or permitting outcome guarantee",
        ),
    ],
)
def test_rejects_unsafe_or_incomplete_audit_entry_mutations(
    mutate: Callable[[dict[str, Any]], None], expected_problem: str
) -> None:
    packet = copy.deepcopy(_valid_packet())

    mutate(packet)

    result = validate_promotion_audit_log_candidate_packet(packet)
    assert not result.valid
    assert any(expected_problem in problem for problem in result.problems)
