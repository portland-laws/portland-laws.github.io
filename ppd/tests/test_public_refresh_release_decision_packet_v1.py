from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from ppd.public_refresh_release_decision_packet_v1 import (
    build_public_refresh_release_decision_packet_v1,
    validate_public_refresh_release_decision_packet_v1,
)


FIXTURE_PATH = Path(__file__).parent / 'fixtures' / 'public_refresh_release_decision_packet_v1' / 'candidate_rows.json'


def _candidate_rows() -> list[dict]:
    return json.loads(FIXTURE_PATH.read_text(encoding='utf-8'))['candidate_rows']


def _valid_packet() -> dict:
    return build_public_refresh_release_decision_packet_v1(_candidate_rows())


def _errors(packet: dict) -> tuple[str, ...]:
    return validate_public_refresh_release_decision_packet_v1(packet)['errors']


def test_builds_fixture_first_public_refresh_release_decision_packet() -> None:
    packet = _valid_packet()

    assert validate_public_refresh_release_decision_packet_v1(packet)['valid'] is True
    assert packet['artifact_id'] == 'public_refresh_release_decision_packet_v1'
    assert packet['candidate_rows_source'] == 'synthetic_inactive_promotion_candidate_rows'
    assert len(packet['consumed_candidate_rows']) == 3
    assert {row['decision'] for row in packet['release_decisions']} == {'hold', 'proceed', 'skip'}


def test_packet_contains_required_release_decision_sections() -> None:
    packet = _valid_packet()

    for section in (
        'unresolved_reviewer_blocker_summaries',
        'validation_evidence_references',
        'stale_source_hold_outcomes',
        'rollback_decision_points',
        'post_decision_smoke_expectations',
    ):
        assert section in packet
        assert packet[section]

    hold = next(row for row in packet['release_decisions'] if row['candidate_id'] == 'public-refresh-candidate-hold-002')
    stale = next(row for row in packet['stale_source_hold_outcomes'] if row['candidate_id'] == 'public-refresh-candidate-hold-002')
    assert hold['decision'] == 'hold'
    assert 'stale source' in hold['decision_reason']
    assert stale['outcome'] == 'hold_for_freshness_review'


def test_packet_uses_exact_offline_validation_commands_only() -> None:
    packet = _valid_packet()

    expected = [
        ['python3', '-m', 'py_compile', 'ppd/public_refresh_release_decision_packet_v1.py'],
        ['python3', '-m', 'pytest', 'ppd/tests/test_public_refresh_release_decision_packet_v1.py'],
        ['python3', 'ppd/daemon/ppd_daemon.py', '--self-test'],
    ]
    assert packet['offline_validation_commands'] == expected
    for smoke in packet['post_decision_smoke_expectations']:
        assert smoke['commands'] == expected
    for rollback in packet['rollback_decision_points']:
        assert rollback['rollback_validation_commands'] == expected


def test_packet_keeps_live_devhub_release_and_artifact_mutation_flags_false() -> None:
    packet = _valid_packet()

    for flag_name in (
        'live_source_crawl_performed',
        'documents_downloaded',
        'raw_output_stored',
        'devhub_opened',
        'release_activated',
        'active_artifacts_mutated',
        'official_action_performed',
        'private_session_artifacts_created',
    ):
        assert packet[flag_name] is False


def test_rejects_non_synthetic_or_active_candidate_rows() -> None:
    packet = _valid_packet()
    packet['consumed_candidate_rows'][0]['synthetic'] = False
    packet['consumed_candidate_rows'][1]['inactive'] = False
    packet['consumed_candidate_rows'][2]['source_fixture_ref'] = 'tests/fixtures/wrong-root.json'

    errors = _errors(packet)

    assert any('synthetic must be true' in error for error in errors)
    assert any('inactive must be true' in error for error in errors)
    assert any('source_fixture_ref must stay under ppd/tests/fixtures/' in error for error in errors)


def test_rejects_missing_required_decision_sections_and_changed_command_list() -> None:
    packet = _valid_packet()
    packet['unresolved_reviewer_blocker_summaries'] = []
    packet['validation_evidence_references'] = []
    packet['stale_source_hold_outcomes'] = []
    packet['rollback_decision_points'] = []
    packet['post_decision_smoke_expectations'] = []
    packet['offline_validation_commands'] = [['python3', 'ppd/daemon/ppd_daemon.py', '--self-test']]

    errors = _errors(packet)

    assert any('unresolved_reviewer_blocker_summaries must include' in error for error in errors)
    assert any('validation_evidence_references must include' in error for error in errors)
    assert any('stale_source_hold_outcomes must include' in error for error in errors)
    assert any('rollback_decision_points must include' in error for error in errors)
    assert any('post_decision_smoke_expectations must include' in error for error in errors)
    assert any('offline_validation_commands must exactly match' in error for error in errors)


def test_rejects_missing_inactive_candidate_reference_and_missing_decision_modes() -> None:
    packet = _valid_packet()
    packet['consumed_candidate_rows'] = packet['consumed_candidate_rows'][:2]
    packet['release_decisions'] = [row for row in packet['release_decisions'] if row['decision'] != 'skip']

    errors = _errors(packet)

    assert any('release_decisions must include hold, proceed, and skip decisions' in error for error in errors)
    assert any('must cover every inactive promotion candidate' in error for error in errors)


def test_rejects_missing_validation_evidence_references() -> None:
    packet = _valid_packet()
    packet['consumed_candidate_rows'][0]['validation_evidence_refs'] = []
    packet['validation_evidence_references'][0]['evidence_refs'] = []

    errors = _errors(packet)

    assert any('validation_evidence_refs must include' in error for error in errors)
    assert any('evidence_refs must include validation evidence references' in error for error in errors)


def test_rejects_live_private_raw_or_consequential_values() -> None:
    base = _valid_packet()

    bad_values = (
        'https://www.portland.gov/ppd/live',
        'devhub.portlandoregon.gov private session',
        'storage_state file',
        'raw html capture',
        'downloaded document',
        'live extraction completed',
        'live crawl completed',
        'release activated',
        'active artifacts mutated',
        'official action completed',
        'submitted permit',
        'permit will be approved',
    )
    for bad_value in bad_values:
        packet = deepcopy(base)
        packet['bad_value'] = bad_value
        assert _errors(packet), bad_value


def test_rejects_active_mutation_flags_anywhere() -> None:
    base = _valid_packet()

    for key in (
        'active_mutation',
        'active_artifact_mutation',
        'mutates_active_artifacts',
        'release_state_updated',
    ):
        packet = deepcopy(base)
        packet[key] = True
        assert any('active mutation flags' in error for error in _errors(packet)), key
