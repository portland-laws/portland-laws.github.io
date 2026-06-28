from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from ppd.crawler.public_recrawl_execution_rehearsal import (
    PACKET_TYPE,
    build_public_recrawl_execution_rehearsal_plan,
    validate_public_recrawl_execution_rehearsal_plan,
)
from ppd.post_decision_release_readiness_digest import build_post_decision_release_readiness_digest

FIXTURE_DIR = Path(__file__).parent / 'fixtures'
POST_DECISION_INPUTS = FIXTURE_DIR / 'post_decision_release_readiness_digest' / 'input_packets.json'
DRIFT_DIGEST = FIXTURE_DIR / 'source_freshness_drift' / 'valid_digest.json'
EXPECTED = FIXTURE_DIR / 'public_recrawl_execution_rehearsal' / 'expected_plan_summary.json'


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def _post_decision_digest() -> dict:
    return build_post_decision_release_readiness_digest(_load(POST_DECISION_INPUTS))


def test_builds_fixture_first_public_recrawl_execution_rehearsal_plan() -> None:
    plan = build_public_recrawl_execution_rehearsal_plan(
        _post_decision_digest(),
        _load(DRIFT_DIGEST),
        generated_at='2026-05-28T18:45:00Z',
    )
    expected = _load(EXPECTED)

    assert plan['packet_type'] == PACKET_TYPE == expected['packet_type']
    assert plan['fixture_first'] is True
    assert plan['metadata_only'] is True
    assert plan['dry_run_only'] is True
    assert plan['no_raw_body_persistence'] is True
    assert plan['live_network_invoked'] is False
    assert plan['processor_invoked'] is False
    assert [target['source_id'] for target in plan['metadata_targets']] == ['ppd-devhub-faq']
    assert plan['metadata_targets'][0]['canonical_url'] == expected['metadata_targets'][0]['canonical_url']
    assert plan['metadata_targets'][0]['host'] == expected['metadata_targets'][0]['host']
    assert plan['processor_handoff_intent'][0]['intent'] == 'deferred_metadata_handoff'
    assert plan['processor_handoff_intent'][0]['processor_invoked'] is False
    assert plan['processor_handoff_intent'][0]['raw_body_persistence'] is False
    assert plan['expected_archive_manifest_ids'] == [expected['metadata_targets'][0]['expected_archive_manifest_id']]
    assert {item['condition_id'] for item in plan['abort_conditions']} == set(expected['required_abort_condition_ids'])
    assert validate_public_recrawl_execution_rehearsal_plan(plan) == []


def test_rehearsal_selects_only_allowlisted_public_metadata_targets() -> None:
    drift = _load(DRIFT_DIGEST)
    drift['source_references'][0]['canonical_url'] = 'https://example.com/private/path'

    with pytest.raises(ValueError, match='allowlisted public metadata targets'):
        build_public_recrawl_execution_rehearsal_plan(
            _post_decision_digest(),
            drift,
            generated_at='2026-05-28T18:45:00Z',
        )


def test_rehearsal_validation_rejects_raw_body_or_live_processor_intent() -> None:
    plan = build_public_recrawl_execution_rehearsal_plan(
        _post_decision_digest(),
        _load(DRIFT_DIGEST),
        generated_at='2026-05-28T18:45:00Z',
    )
    unsafe = deepcopy(plan)
    unsafe['processor_handoff_intent'][0]['raw_body_persistence'] = True
    unsafe['dry_run_command_descriptors'][0]['processor_invoked'] = True

    errors = validate_public_recrawl_execution_rehearsal_plan(unsafe)

    assert 'processor_handoff_intent[0].raw_body_persistence must be false' in errors
    assert 'dry_run_command_descriptors[0].processor_invoked must be false' in errors
    assert any('requests live network or processor execution' in error for error in errors)
