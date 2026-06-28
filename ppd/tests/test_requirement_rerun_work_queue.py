from __future__ import annotations

import copy
import json
from pathlib import Path

from ppd.daemon.requirement_rerun_work_queue import (
    require_requirement_rerun_work_queue_packet,
    validate_requirement_rerun_work_queue_packet,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "requirement_rerun_work_queue" / "packets.json"


def _fixtures() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_accepts_cited_review_owned_planning_packet() -> None:
    packet = _fixtures()["valid"]

    result = validate_requirement_rerun_work_queue_packet(packet)  # type: ignore[arg-type]

    assert result.valid is True
    assert result.errors == ()
    assert require_requirement_rerun_work_queue_packet(packet) == packet  # type: ignore[arg-type]


def test_rejects_uncited_requirement_ids() -> None:
    packet = copy.deepcopy(_fixtures()["valid"])
    packet["requirement_ids"].append("REQ-uncited")

    result = validate_requirement_rerun_work_queue_packet(packet)

    assert result.valid is False
    assert any("REQ-uncited" in error and "citation" in error for error in result.errors)


def test_rejects_missing_affected_process_or_guardrail_refs() -> None:
    packet = copy.deepcopy(_fixtures()["valid"])
    packet["affected_process_refs"] = []
    packet["affected_guardrail_refs"] = []

    result = validate_requirement_rerun_work_queue_packet(packet)

    assert result.valid is False
    assert "affected_process_refs must include at least one process reference" in result.errors
    assert "affected_guardrail_refs must include at least one guardrail reference" in result.errors


def test_rejects_unordered_rerun_steps() -> None:
    packet = copy.deepcopy(_fixtures()["valid"])
    packet["rerun_steps"] = [
        {"order": 2, "name": "compile"},
        {"order": 1, "name": "review"},
    ]

    result = validate_requirement_rerun_work_queue_packet(packet)

    assert result.valid is False
    assert any("rerun_steps must be ordered" in error for error in result.errors)


def test_rejects_missing_reviewer_owners() -> None:
    packet = copy.deepcopy(_fixtures()["valid"])
    packet["reviewer_owners"] = []

    result = validate_requirement_rerun_work_queue_packet(packet)

    assert result.valid is False
    assert "reviewer_owners must include at least one owner" in result.errors


def test_rejects_raw_download_archive_live_processor_outcome_and_mutation_claims() -> None:
    for case in _fixtures()["invalid_claims"]:
        result = validate_requirement_rerun_work_queue_packet(case)

        assert result.valid is False, case
        assert result.errors, case
