from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ppd.validation.public_refresh_reviewer_handoff_packet_v1 import (
    REQUIREMENTS,
    validate_public_refresh_reviewer_handoff_packet_v1,
)

FIXTURE = Path(__file__).parent / "fixtures" / "public_refresh_reviewer_handoff_packet_v1.json"


def load_packet() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_accepts_complete_metadata_only_handoff_packet() -> None:
    assert validate_public_refresh_reviewer_handoff_packet_v1(load_packet()) == []


@pytest.mark.parametrize("field", [requirement.field for requirement in REQUIREMENTS])
def test_rejects_missing_required_handoff_references(field: str) -> None:
    packet = load_packet()
    packet.pop(field)

    errors = validate_public_refresh_reviewer_handoff_packet_v1(packet)

    assert any(field in error for error in errors)


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("notes", "contains private artifact", "private artifacts are not allowed"),
        ("notes", "contains raw artifact", "raw artifacts are not allowed"),
        ("notes", "contains downloaded artifact", "downloaded artifacts are not allowed"),
        ("notes", "contains downloaded document", "downloaded documents are not allowed"),
        ("notes", "claims live crawl completed", "live crawl claims are not allowed"),
        ("notes", "claims DevHub source was checked", "DevHub claims are not allowed"),
        ("notes", "claims release activation", "release activation claims are not allowed"),
        ("notes", "claims official action completed", "official-action completion claims are not allowed"),
        ("notes", "offers legal guarantee", "legal guarantees are not allowed"),
        ("notes", "offers permitting guarantee", "permitting guarantees are not allowed"),
        ("active_mutation", True, "active mutation flag is not allowed: active_mutation"),
    ],
)
def test_rejects_prohibited_claims_and_flags(field: str, value: object, expected: str) -> None:
    packet = load_packet()
    packet[field] = value

    errors = validate_public_refresh_reviewer_handoff_packet_v1(packet)

    assert expected in errors


def test_rejects_nested_active_mutation_flags() -> None:
    packet = load_packet()
    packet["owner_routing"] = copy.deepcopy(packet["owner_routing"])
    packet["owner_routing"][0]["mutation_enabled"] = True

    errors = validate_public_refresh_reviewer_handoff_packet_v1(packet)

    assert "active mutation flag is not allowed: mutation_enabled" in errors
