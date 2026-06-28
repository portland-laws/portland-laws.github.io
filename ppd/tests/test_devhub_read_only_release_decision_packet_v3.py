from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from ppd.agent_readiness.devhub_read_only_release_decision_packet_v3 import (
    DEFAULT_IMPACT_REPLAY_FIXTURE_REF,
    EXACT_OFFLINE_VALIDATION_COMMANDS,
    DevHubReadOnlyReleaseDecisionPacketV3Error,
    assert_valid_devhub_read_only_release_decision_packet_v3,
    build_devhub_read_only_release_decision_packet_v3,
    validate_devhub_read_only_release_decision_packet_v3,
)

FIXTURE_DIR = Path(__file__).parent / 'fixtures' / 'devhub_read_only_release_decision_packet_v3'


def _load(name: str) -> dict[str, Any]:
    value = json.loads((FIXTURE_DIR / name).read_text(encoding='utf-8'))
    assert isinstance(value, dict)
    return value


def _packet() -> dict[str, Any]:
    return build_devhub_read_only_release_decision_packet_v3(_load('agent_impact_replay_v3.json'))


def _problems(packet: dict[str, Any]) -> str:
    return '; '.join(validate_devhub_read_only_release_decision_packet_v3(packet).problems)


def test_builds_fixture_first_inactive_release_decision_packet_v3() -> None:
    packet = _packet()

    assert packet['packet_type'] == 'ppd.devhub_read_only_release_decision_packet.v3'
    assert packet['mode'] == 'fixture-first-read-only-inactive'
    assert packet['fixture_only'] is True
    assert packet['read_only'] is True
    assert packet['inactive_release_decision'] is True
    assert packet['source_fixture_refs'] == [DEFAULT_IMPACT_REPLAY_FIXTURE_REF]
    assert packet['consumes_only'] == {'agent_impact_replay_packet': 'devhub_read_only_agent_impact_replay_v3'}
    assert packet['inactive_promotion_recommendation']['status'] == 'hold'
    assert packet['inactive_promotion_recommendation']['recommendation'] == 'do_not_activate'
    assert packet['reviewer_signoff_placeholders']
    assert {row['status'] for row in packet['stale_evidence_holds']} == {'hold'}
    assert {row['status'] for row in packet['activation_prerequisites']} == {'pending'}
    assert packet['rollback_plan']
    assert packet['post_decision_smoke_checks']
    assert packet['offline_validation_commands'] == EXACT_OFFLINE_VALIDATION_COMMANDS
    assert all(value is False for value in packet['attestations'].values())
    assert_valid_devhub_read_only_release_decision_packet_v3(packet)


def test_consumes_only_agent_impact_replay_fixture_ref() -> None:
    packet = _packet()
    packet['source_fixture_refs'] = [
        'ppd/tests/fixtures/devhub_read_only_agent_impact_replay_v3/inactive_surface_map_delta_reviewer_packet_v3.json',
        DEFAULT_IMPACT_REPLAY_FIXTURE_REF,
    ]

    assert 'source_fixture_refs must contain only the committed agent impact replay v3 fixture' in _problems(packet)


def test_rejects_validation_command_drift() -> None:
    packet = _packet()
    packet['offline_validation_commands'] = [['python3', 'ppd/daemon/ppd_daemon.py', '--self-test']]

    assert 'offline_validation_commands must match exact offline validation commands' in _problems(packet)


@pytest.mark.parametrize(
    ('field', 'expected'),
    [
        ('reviewer_signoff_placeholders', 'reviewer_signoff_placeholders must be a non-empty list'),
        ('stale_evidence_holds', 'stale_evidence_holds must be a non-empty list'),
        ('activation_prerequisites', 'activation_prerequisites must be a non-empty list'),
        ('rollback_plan', 'rollback_plan must be a non-empty list'),
        ('post_decision_smoke_checks', 'post_decision_smoke_checks must be a non-empty list'),
    ],
)
def test_rejects_missing_required_sections(field: str, expected: str) -> None:
    packet = _packet()
    packet[field] = []

    assert expected in _problems(packet)


def test_rejects_attestation_drift_and_private_artifact_fields() -> None:
    packet = _packet()
    packet['attestations']['devhub_opened'] = True
    packet['browser_state_path'] = 'state.json'

    problems = _problems(packet)

    assert 'attestations.devhub_opened must be false' in problems
    assert 'must not include private, credential, browser, trace, HAR, or state artifacts' in problems


@pytest.mark.parametrize(
    ('key', 'value', 'expected'),
    [
        ('active_surface_map_mutation', True, 'must not include active mutation flags'),
        ('note', 'live DevHub confirmed this packet', 'must not include unsafe live, private, consequential, or guarantee claims'),
        ('note', 'uploaded file after filled form', 'must not include unsafe live, private, consequential, or guarantee claims'),
        ('note', 'approval guaranteed and legal advice supplied', 'must not include unsafe live, private, consequential, or guarantee claims'),
    ],
)
def test_rejects_forbidden_claim_categories(key: str, value: object, expected: str) -> None:
    packet = _packet()
    packet[key] = value

    assert expected in _problems(packet)


def test_rejects_non_agent_impact_replay_input() -> None:
    replay = _load('agent_impact_replay_v3.json')
    replay['packet_version'] = 'wrong-version'

    with pytest.raises(Exception):
        build_devhub_read_only_release_decision_packet_v3(replay)


def test_rejects_unsafe_input_fixture_before_building() -> None:
    replay = _load('agent_impact_replay_v3.json')
    replay['claim'] = 'live DevHub confirmed this packet'

    with pytest.raises(DevHubReadOnlyReleaseDecisionPacketV3Error):
        build_devhub_read_only_release_decision_packet_v3(replay)
