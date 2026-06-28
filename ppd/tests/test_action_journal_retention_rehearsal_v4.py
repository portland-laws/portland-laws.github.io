from __future__ import annotations

import copy
from pathlib import Path

import pytest

from ppd.action_journal_retention_rehearsal_v4 import (
    EXACT_OFFLINE_VALIDATION_COMMANDS,
    REQUIRED_EVENT_TYPES,
    SOURCE_FIXTURE_REFS,
    assert_action_journal_retention_rehearsal_v4,
    load_action_journal_retention_rehearsal_v4,
    validate_action_journal_retention_rehearsal_v4,
)

FIXTURE_PATH = Path(__file__).parent / 'fixtures' / 'action_journal_retention_rehearsal_v4' / 'packet.json'


def valid_packet() -> dict:
    return load_action_journal_retention_rehearsal_v4(FIXTURE_PATH)


def assert_rejected(packet: dict, expected: str) -> None:
    result = validate_action_journal_retention_rehearsal_v4(packet)
    assert not result.ok
    assert any(expected in problem for problem in result.problems), result.problems


def test_fixture_packet_is_valid_and_complete() -> None:
    packet = valid_packet()
    result = validate_action_journal_retention_rehearsal_v4(packet)
    assert result.ok, result.problems
    assert result.event_types == REQUIRED_EVENT_TYPES
    assert result.event_count == len(REQUIRED_EVENT_TYPES)
    assert packet['source_fixture_refs'] == list(SOURCE_FIXTURE_REFS)
    assert packet['exact_offline_validation_commands'] == EXACT_OFFLINE_VALIDATION_COMMANDS
    assert_action_journal_retention_rehearsal_v4(packet)


def test_fixture_path_is_test_local() -> None:
    assert 'ppd/tests/fixtures/action_journal_retention_rehearsal_v4' in FIXTURE_PATH.as_posix()


def test_rejects_missing_agent_api_compat_source_fixture_reference() -> None:
    packet = valid_packet()
    packet['source_fixture_refs'] = []
    assert_rejected(packet, 'source_fixture_refs must contain only')


def test_rejects_non_agent_api_compat_source_fixture() -> None:
    packet = valid_packet()
    packet['source_fixture_refs'] = ['ppd/tests/fixtures/other.json']
    assert_rejected(packet, 'source_fixture_refs must contain only')


def test_rejects_missing_commit_safe_journal_event_examples() -> None:
    packet = valid_packet()
    packet['journal_event_examples'] = []
    assert_rejected(packet, 'commit-safe journal event examples')


@pytest.mark.parametrize(
    'event_type, expected',
    [
        ('exact_confirmation_checkpoint', 'exact-confirmation checkpoint row'),
        ('manual_handoff', 'manual handoff row'),
        ('refused_action', 'refused-action row'),
        ('rollback_trigger', 'rollback trigger row'),
    ],
)
def test_rejects_missing_required_journal_rows(event_type: str, expected: str) -> None:
    packet = valid_packet()
    packet['journal_event_examples'] = [
        event for event in packet['journal_event_examples'] if event['event_type'] != event_type
    ]
    assert_rejected(packet, expected)


def test_rejects_missing_required_event_type_order() -> None:
    packet = valid_packet()
    packet['journal_event_examples'][4]['event_type'] = 'devhub_attempted_action'
    assert_rejected(packet, 'journal_event_examples must include required v4 event types')


def test_rejects_missing_redaction_evidence() -> None:
    packet = valid_packet()
    del packet['journal_event_examples'][0]['redaction_evidence']
    assert_rejected(packet, 'redaction_evidence')


def test_rejects_unredacted_example_material() -> None:
    packet = valid_packet()
    packet['journal_event_examples'][0]['redaction_evidence']['redacted_examples']['url_example'] = 'https://example.invalid/raw'
    assert_rejected(packet, 'explicit redaction marker')


def test_rejects_missing_validation_commands() -> None:
    packet = valid_packet()
    del packet['exact_offline_validation_commands']
    assert_rejected(packet, 'exact_offline_validation_commands must contain only')


def test_rejects_non_exact_validation_commands() -> None:
    packet = valid_packet()
    packet['journal_event_examples'][8]['exact_offline_validation_commands'] = [['python3', '-m', 'pytest']]
    assert_rejected(packet, 'exact_offline_validation_commands must contain only')


@pytest.mark.parametrize(
    'patch, expected',
    [
        ({'journal_event_examples': [{'credentials': 'none'}]}, 'prohibited sensitive key'),
        ({'journal_event_examples': [{'cookies': 'none'}]}, 'prohibited sensitive key'),
        ({'journal_event_examples': [{'auth_state': 'none'}]}, 'prohibited sensitive key'),
        ({'journal_event_examples': [{'raw_crawl_output': 'none'}]}, 'prohibited sensitive key'),
        ({'journal_event_examples': [{'screenshots': 'none'}]}, 'prohibited sensitive key'),
        ({'journal_event_examples': [{'trace_file': 'none'}]}, 'prohibited sensitive key'),
        ({'journal_event_examples': [{'har_file': 'none'}]}, 'prohibited sensitive key'),
        ({'journal_event_examples': [{'downloaded_document': 'none'}]}, 'prohibited sensitive key'),
        ({'journal_event_examples': [{'private_values': 'none'}]}, 'prohibited sensitive key'),
        ({'journal_event_examples': [{'payment_details': 'none'}]}, 'prohibited sensitive key'),
        ({'journal_event_examples': [{'active_mutation': False}]}, 'prohibited sensitive key'),
        ({'journal_event_examples': [{'safe_note': 'Bearer abc123'}]}, 'credential material'),
        ({'journal_event_examples': [{'safe_note': 'cookie jar retained'}]}, 'credential material'),
        ({'journal_event_examples': [{'safe_note': 'screenshot captured'}]}, 'browser artifact'),
        ({'journal_event_examples': [{'safe_note': 'trace retained'}]}, 'browser artifact'),
        ({'journal_event_examples': [{'safe_note': 'HAR file attached'}]}, 'browser artifact'),
        ({'journal_event_examples': [{'safe_note': '/home/person/private.pdf'}]}, 'local private path'),
        ({'journal_event_examples': [{'safe_note': '4111 1111 1111 1111'}]}, 'payment number'),
        ({'journal_event_examples': [{'safe_note': 'raw private field retained'}]}, 'private value claim'),
        ({'journal_event_examples': [{'safe_note': 'full html body retained'}]}, 'raw material'),
        ({'journal_event_examples': [{'safe_note': 'downloaded document retained'}]}, 'downloaded document claim'),
        ({'journal_event_examples': [{'safe_note': 'permit issued'}]}, 'restricted action claim'),
        ({'journal_event_examples': [{'safe_note': 'permit will be approved'}]}, 'legal or permitting guarantee'),
        ({'journal_event_examples': [{'safe_note': 'active mutation enabled'}]}, 'active mutation claim'),
    ],
)
def test_rejects_restricted_material_keys_and_values(patch: dict, expected: str) -> None:
    packet = valid_packet()
    candidate = copy.deepcopy(packet)
    candidate['journal_event_examples'][0].update(patch['journal_event_examples'][0])
    assert_rejected(candidate, expected)


def test_rejects_compat_fixture_that_no_longer_validates() -> None:
    packet = valid_packet()
    packet['consumed_agent_api_compatibility_rehearsal_v4']['source_citation_payloads'] = []
    assert_rejected(packet, 'agent_api_compatibility_rehearsal_v4')
