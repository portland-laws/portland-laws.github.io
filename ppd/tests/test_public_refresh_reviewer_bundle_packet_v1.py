from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from ppd.public_refresh.reviewer_bundle_packet_v1 import (
    require_public_refresh_reviewer_bundle_packet_v1,
    validate_public_refresh_reviewer_bundle_packet_v1,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "public_refresh_reviewer_bundle_packet_v1"
VALID_PACKET_PATH = FIXTURE_DIR / "valid_packet.json"


def _valid_packet() -> dict[str, object]:
    with VALID_PACKET_PATH.open("r", encoding="utf-8") as handle:
        loaded = json.load(handle)
    assert isinstance(loaded, dict)
    return loaded


def _errors(packet: dict[str, object]) -> str:
    result = validate_public_refresh_reviewer_bundle_packet_v1(packet)
    assert not result.valid
    return "\n".join(result.errors)


def test_valid_public_refresh_reviewer_bundle_packet_v1_fixture_passes() -> None:
    packet = _valid_packet()
    result = validate_public_refresh_reviewer_bundle_packet_v1(packet)
    assert result.valid, result.errors
    require_public_refresh_reviewer_bundle_packet_v1(packet)


@pytest.mark.parametrize(
    ("field", "expected"),
    [
        ("process_model_delta_refs", "process_model_delta_refs must be a non-empty list"),
        ("guardrail_recompile_refs", "guardrail_recompile_refs must be a non-empty list"),
        ("agent_gap_analysis_replay_refs", "agent_gap_analysis_replay_refs must be a non-empty list"),
        ("owner_signoff_placeholders", "owner_signoff_placeholders must be a non-empty list"),
        ("dependency_sequence", "dependency_sequence must be a non-empty list"),
        ("release_blocker_notes", "release_blocker_notes must be a non-empty list"),
        ("rollback_checkpoints", "rollback_checkpoints must be a non-empty list"),
        ("validation_commands", "validation_commands must be a non-empty list"),
    ],
)
def test_rejects_missing_required_top_level_reviewer_bundle_sections(field: str, expected: str) -> None:
    packet = _valid_packet()
    packet[field] = []
    assert expected in _errors(packet)


@pytest.mark.parametrize("disposition_type", ["requirement", "process", "guardrail", "agent_impact"])
def test_rejects_missing_reviewer_ready_disposition_type(disposition_type: str) -> None:
    packet = _valid_packet()
    packet["reviewer_ready_dispositions"] = [
        item
        for item in packet["reviewer_ready_dispositions"]
        if isinstance(item, dict) and item.get("disposition_type") != disposition_type
    ]
    errors = _errors(packet)
    assert f"reviewer_ready_dispositions missing disposition types: {disposition_type}" in errors


@pytest.mark.parametrize(
    ("list_name", "missing_field"),
    [
        ("process_model_delta_refs", "delta_id"),
        ("guardrail_recompile_refs", "recompile_plan_id"),
        ("agent_gap_analysis_replay_refs", "replay_id"),
    ],
)
def test_rejects_incomplete_reference_records(list_name: str, missing_field: str) -> None:
    packet = _valid_packet()
    refs = packet[list_name]
    assert isinstance(refs, list)
    broken = deepcopy(refs[0])
    assert isinstance(broken, dict)
    broken.pop(missing_field)
    refs[0] = broken
    assert f"{list_name}[0].{missing_field} must be present" in _errors(packet)


def test_rejects_dependency_sequence_that_references_later_steps() -> None:
    packet = _valid_packet()
    sequence = packet["dependency_sequence"]
    assert isinstance(sequence, list)
    first = deepcopy(sequence[0])
    assert isinstance(first, dict)
    first["depends_on"] = ["owner-signoff-review"]
    sequence[0] = first
    assert "dependency_sequence[0].depends_on references later or missing dependencies: owner-signoff-review" in _errors(packet)


def test_rejects_validation_command_drift() -> None:
    packet = _valid_packet()
    packet["validation_commands"] = [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]]
    assert "validation_commands must match the allowed offline validation command list" in _errors(packet)


@pytest.mark.parametrize(
    ("path", "value", "expected"),
    [
        (("private_artifact_path",), "/home/example/private/session.json", "private, raw, downloaded, browser, session, or DevHub artifacts"),
        (("release_blocker_notes", 0, "note"), "live crawl executed for this refresh", "live extraction or crawl execution"),
        (("release_blocker_notes", 0, "note"), "DevHub was checked during review", "DevHub scope or activity"),
        (("release_blocker_notes", 0, "note"), "release activated for public refresh", "release activation"),
        (("release_blocker_notes", 0, "note"), "artifact mutated by reviewer packet", "active artifact mutation"),
        (("release_blocker_notes", 0, "note"), "official action completed", "official-action completion"),
        (("release_blocker_notes", 0, "note"), "permit will issue", "legal or permitting outcomes"),
        (("active_guardrail_mutation",), True, "active mutation flags"),
    ],
)
def test_rejects_forbidden_artifacts_claims_and_mutation_flags(path: tuple[object, ...], value: object, expected: str) -> None:
    packet = _valid_packet()
    target: object = packet
    for part in path[:-1]:
        if isinstance(part, int):
            assert isinstance(target, list)
            target = target[part]
        else:
            assert isinstance(target, dict)
            target = target.setdefault(part, {})
    last = path[-1]
    if isinstance(last, int):
        assert isinstance(target, list)
        target[last] = value
    else:
        assert isinstance(target, dict)
        target[last] = value
    assert expected in _errors(packet)


def test_require_raises_for_invalid_packet() -> None:
    packet = _valid_packet()
    packet["reviewer_ready_dispositions"] = []
    with pytest.raises(ValueError, match="invalid public refresh reviewer bundle packet v1"):
        require_public_refresh_reviewer_bundle_packet_v1(packet)
