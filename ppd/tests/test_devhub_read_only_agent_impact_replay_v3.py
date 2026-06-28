from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from ppd.agent_readiness.devhub_read_only_agent_impact_replay_v3 import (
    EXACT_OFFLINE_VALIDATION_COMMANDS,
    DevHubReadOnlyAgentImpactReplayV3Error,
    assert_valid_devhub_read_only_agent_impact_replay_v3,
    build_devhub_read_only_agent_impact_replay_v3,
    validate_devhub_read_only_agent_impact_replay_v3,
)

FIXTURE_DIR = Path(__file__).parent / 'fixtures' / 'devhub_read_only_agent_impact_replay_v3'


def _load(name: str) -> dict[str, Any]:
    value = json.loads((FIXTURE_DIR / name).read_text(encoding='utf-8'))
    assert isinstance(value, dict)
    return value


def _packet() -> dict[str, Any]:
    return build_devhub_read_only_agent_impact_replay_v3(_load('inactive_surface_map_delta_reviewer_packet_v3.json'), _load('synthetic_agent_requests_v3.json'))


def _problems(packet: dict[str, Any]) -> str:
    return '; '.join(validate_devhub_read_only_agent_impact_replay_v3(packet).problems)


def test_builds_fixture_first_post_decision_replay_packet() -> None:
    packet = _packet()

    assert packet['packet_version'] == 'devhub_read_only_agent_impact_replay_v3'
    assert packet['post_decision_smoke_replay'] is True
    assert packet['validation_commands'] == EXACT_OFFLINE_VALIDATION_COMMANDS
    assert packet['release_decision_references']
    assert 'inactive_surface_map_delta_reviewer_packet_v3.json' in ' '.join(packet['source_fixture_refs'])
    assert 'synthetic_agent_requests_v3.json' in ' '.join(packet['source_fixture_refs'])
    assert {row['action_id'] for row in packet['affected_safe_read_only_actions']} == {'review_status', 'review_notice'}
    assert {row['action_id'] for row in packet['blocked_consequential_actions']} == {'complete_record', 'attach_record_material'}
    assert {row['action_id'] for row in packet['read_only_route_lookup_checks']} == {'review_status', 'review_notice'}
    assert {row['action_id'] for row in packet['exact_confirmation_gate_checks']} == {'complete_record', 'attach_record_material'}
    assert {row['missing_information_key'] for row in packet['missing_information_prompts']} == {'permit_number', 'review_group'}
    assert packet['synthetic_surface_map_placeholders']
    assert packet['action_classification_checks']
    assert packet['manual_handoff_gate_checks']
    assert packet['reviewer_holds']
    assert packet['rollback_readiness']
    assert_valid_devhub_read_only_agent_impact_replay_v3(packet)


def test_rejects_validation_command_drift() -> None:
    packet = _packet()
    packet['validation_commands'] = [['python3', 'ppd/daemon/ppd_daemon.py', '--self-test']]

    assert 'validation_commands must match exact offline replay validation commands' in _problems(packet)


@pytest.mark.parametrize(
    ('field', 'expected'),
    [
        ('release_decision_references', 'release_decision_references must be a non-empty list'),
        ('synthetic_surface_map_placeholders', 'synthetic_surface_map_placeholders must be a non-empty list'),
        ('read_only_route_lookup_checks', 'read_only_route_lookup_checks must be a non-empty list'),
        ('action_classification_checks', 'action_classification_checks must be a non-empty list'),
        ('affected_safe_read_only_actions', 'affected_safe_read_only_actions must be a non-empty list'),
        ('blocked_consequential_actions', 'blocked_consequential_actions must be a non-empty list'),
        ('missing_information_prompts', 'missing_information_prompts must be a non-empty list'),
        ('exact_confirmation_gate_checks', 'exact_confirmation_gate_checks must be a non-empty list'),
        ('manual_handoff_gate_checks', 'manual_handoff_gate_checks must be a non-empty list'),
        ('reviewer_holds', 'reviewer_holds must be a non-empty list'),
        ('rollback_readiness', 'rollback_readiness must be a non-empty list'),
    ],
)
def test_rejects_missing_required_post_decision_sections(field: str, expected: str) -> None:
    packet = _packet()
    packet[field] = []

    assert expected in _problems(packet)


@pytest.mark.parametrize(
    ('field', 'row_key', 'expected'),
    [
        ('release_decision_references', 'decision_packet', 'release_decision_references[0].decision_packet is required'),
        ('synthetic_surface_map_placeholders', 'placeholder_kind', 'synthetic_surface_map_placeholders[0].placeholder_kind is required'),
        ('read_only_route_lookup_checks', 'route_lookup', 'read_only_route_lookup_checks[0].route_lookup is required'),
        ('action_classification_checks', 'classification', 'action_classification_checks[0].classification is required'),
        ('affected_safe_read_only_actions', 'summary', 'affected_safe_read_only_actions[0].summary is required'),
        ('blocked_consequential_actions', 'summary', 'blocked_consequential_actions[0].summary is required'),
        ('missing_information_prompts', 'prompt', 'missing_information_prompts[0].prompt is required'),
        ('exact_confirmation_gate_checks', 'gate_result', 'exact_confirmation_gate_checks[0].gate_result is required'),
        ('manual_handoff_gate_checks', 'reminder', 'manual_handoff_gate_checks[0].reminder is required'),
        ('reviewer_holds', 'hold_status', 'reviewer_holds[0].hold_status is required'),
        ('rollback_readiness', 'rollback_note', 'rollback_readiness[0].rollback_note is required'),
    ],
)
def test_rejects_missing_required_row_text(field: str, row_key: str, expected: str) -> None:
    packet = _packet()
    packet[field][0][row_key] = ''

    assert expected in _problems(packet)


def test_rejects_required_boolean_gate_drift() -> None:
    packet = _packet()
    packet['synthetic_surface_map_placeholders'][0]['active_surface_map_mutation'] = True
    packet['read_only_route_lookup_checks'][0]['devhub_opened'] = True
    packet['read_only_route_lookup_checks'][0]['read_only_route_confirmed'] = False
    packet['exact_confirmation_gate_checks'][0]['exact_confirmation_performed'] = True
    packet['exact_confirmation_gate_checks'][0]['requires_exact_confirmation'] = False
    packet['manual_handoff_gate_checks'][0]['manual_handoff_required'] = False
    packet['manual_handoff_gate_checks'][0]['manual_handoff_performed'] = True
    packet['reviewer_holds'][0]['release_activation_allowed'] = True
    packet['rollback_readiness'][0]['ready_to_discard_replay'] = False
    packet['rollback_readiness'][0]['active_surface_map_mutation'] = True

    problems = _problems(packet)

    assert 'synthetic_surface_map_placeholders[0].active_surface_map_mutation must be false' in problems
    assert 'read_only_route_lookup_checks[0].devhub_opened must be false' in problems
    assert 'read_only_route_lookup_checks[0].read_only_route_confirmed must be true' in problems
    assert 'exact_confirmation_gate_checks[0].exact_confirmation_performed must be false' in problems
    assert 'exact_confirmation_gate_checks[0].requires_exact_confirmation must be true' in problems
    assert 'manual_handoff_gate_checks[0].manual_handoff_required must be true' in problems
    assert 'manual_handoff_gate_checks[0].manual_handoff_performed must be false' in problems
    assert 'reviewer_holds[0].release_activation_allowed must be false' in problems
    assert 'rollback_readiness[0].ready_to_discard_replay must be true' in problems
    assert 'rollback_readiness[0].active_surface_map_mutation must be false' in problems


def test_rejects_missing_reviewer_packet_reference() -> None:
    packet = _packet()
    packet['consumes']['surface_delta_reviewer_packet'] = ''
    packet['source_fixture_refs'] = ['ppd/tests/fixtures/devhub_read_only_agent_impact_replay_v3/synthetic_agent_requests_v3.json']

    problems = _problems(packet)

    assert 'consumes.surface_delta_reviewer_packet must reference inactive surface-map delta reviewer packet v3' in problems
    assert 'source_fixture_refs must include inactive surface-map delta reviewer packet fixture' in problems


def test_rejects_missing_synthetic_request_fixture_reference() -> None:
    packet = _packet()
    packet['consumes']['synthetic_agent_requests'] = ''
    packet['source_fixture_refs'] = ['ppd/tests/fixtures/devhub_read_only_agent_impact_replay_v3/inactive_surface_map_delta_reviewer_packet_v3.json']

    problems = _problems(packet)

    assert 'consumes.synthetic_agent_requests must reference synthetic agent requests v3' in problems
    assert 'source_fixture_refs must include synthetic agent request fixture' in problems


def test_rejects_empty_source_fixture_refs() -> None:
    packet = _packet()
    packet['source_fixture_refs'] = []

    assert 'source_fixture_refs must include committed reviewer and synthetic request fixture references' in _problems(packet)


def test_rejects_forbidden_artifacts_and_attestation_drift() -> None:
    packet = _packet()
    packet['attestations']['devhub_opened'] = True
    packet['browser_state_path'] = 'state.json'
    packet['note'] = 'opened DevHub with session state'

    problems = _problems(packet)

    assert 'attestations.devhub_opened must be false' in problems
    assert 'must not include auth, session, browser' in problems
    assert 'must not reference private/session/auth artifacts' in problems
    assert 'must not reference live DevHub interaction claims' in problems


@pytest.mark.parametrize(
    ('key', 'value', 'expected'),
    [
        ('trace_note', 'trace file exists for this replay', 'must not include auth, session, browser, screenshot, trace, HAR'),
        ('claim', 'live DevHub interaction confirmed the row', 'must not reference live DevHub interaction claims'),
        ('active_surface_map_mutation', True, 'must not include active mutation flags'),
        ('claim', 'active surface-map mutation updated the route', 'must not include active surface-map mutation claims'),
        ('claim', 'filled form and uploaded file', 'must not include form-fill or upload claims'),
        ('claim', 'official action completed after submitted permit', 'must not include official-action completion claims'),
        ('claim', 'permit will be issued and approval guaranteed', 'must not include legal or permitting guarantees'),
        ('mutates_surface_map', True, 'must not include active mutation flags'),
    ],
)
def test_rejects_forbidden_claim_categories(key: str, value: object, expected: str) -> None:
    packet = _packet()
    packet[key] = value

    assert expected in _problems(packet)


def test_rejects_unrecognized_action_classification() -> None:
    packet = _packet()
    packet['action_classification_checks'][0]['classification'] = 'draft_fill'

    assert 'action_classification_checks[0].classification must be recognized as read-only or blocked consequential' in _problems(packet)


def test_rejects_non_inactive_surface_fixture() -> None:
    surface = _load('inactive_surface_map_delta_reviewer_packet_v3.json')
    requests = _load('synthetic_agent_requests_v3.json')
    surface['inactive_only'] = False

    with pytest.raises(DevHubReadOnlyAgentImpactReplayV3Error, match='inactive surface-map'):
        build_devhub_read_only_agent_impact_replay_v3(surface, requests)


def test_rejects_input_fixture_refs_missing() -> None:
    surface = _load('inactive_surface_map_delta_reviewer_packet_v3.json')
    requests = _load('synthetic_agent_requests_v3.json')
    requests['source_fixture_refs'] = []

    with pytest.raises(DevHubReadOnlyAgentImpactReplayV3Error, match='source_fixture_refs'):
        build_devhub_read_only_agent_impact_replay_v3(surface, requests)
