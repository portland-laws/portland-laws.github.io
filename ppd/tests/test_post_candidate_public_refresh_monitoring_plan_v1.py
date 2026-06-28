from __future__ import annotations

import copy
import json
from pathlib import Path

from ppd.post_candidate_public_refresh_monitoring_plan_v1 import (
    require_post_candidate_public_refresh_monitoring_plan_v1,
    validate_post_candidate_public_refresh_monitoring_plan_v1,
)

FIXTURE_DIR = Path(__file__).parent / 'fixtures' / 'post_candidate_public_refresh_monitoring_plan_v1'
VALID_PACKET_PATH = FIXTURE_DIR / 'valid_packet.json'
REJECTION_CASES_PATH = FIXTURE_DIR / 'rejection_cases.json'


def _valid_packet() -> dict:
    return json.loads(VALID_PACKET_PATH.read_text(encoding='utf-8'))


def test_post_candidate_public_refresh_monitoring_plan_v1_accepts_valid_fixture() -> None:
    packet = _valid_packet()

    result = validate_post_candidate_public_refresh_monitoring_plan_v1(packet)

    assert result.ready, result.problems
    assert result.as_dict()['ready'] is True
    require_post_candidate_public_refresh_monitoring_plan_v1(packet)


def test_post_candidate_public_refresh_monitoring_plan_v1_rejects_fixture_cases() -> None:
    cases = json.loads(REJECTION_CASES_PATH.read_text(encoding='utf-8'))
    assert cases
    for case in cases:
        packet = _valid_packet()
        _deep_update(packet, case['patch'])

        result = validate_post_candidate_public_refresh_monitoring_plan_v1(packet)

        assert not result.ready, case['case_id']
        assert any(case['expected_problem'] in problem for problem in result.problems), (
            case['case_id'],
            result.problems,
        )


def test_post_candidate_public_refresh_monitoring_plan_v1_requires_all_coverage_categories() -> None:
    required = {
        'official_ppd_anchors': 'missing official PP&D anchors coverage',
        'file_preparation_guidance': 'missing file-preparation guidance coverage',
        'fee_payment_guidance': 'missing fee/payment guidance coverage',
        'devhub_public_guidance': 'missing DevHub public guidance coverage',
        'forms_index': 'missing forms index coverage',
        'linked_portland_maps_references': 'missing linked Portland Maps references coverage',
    }
    for category, expected_problem in required.items():
        packet = _valid_packet()
        packet['coverage'][category] = False
        packet['normalized_source_evidence'] = [
            item
            for item in packet['normalized_source_evidence']
            if category not in item.get('coverage_categories', [])
        ]

        result = validate_post_candidate_public_refresh_monitoring_plan_v1(packet)

        assert not result.ready, category
        assert any(expected_problem in problem for problem in result.problems), result.problems


def test_post_candidate_public_refresh_monitoring_plan_v1_requires_each_scheduled_category() -> None:
    packet = _valid_packet()
    packet['synthetic_follow_up_freshness_checks'] = [
        check
        for check in packet['synthetic_follow_up_freshness_checks']
        if 'forms_index' not in check.get('coverage_categories', [])
    ]

    result = validate_post_candidate_public_refresh_monitoring_plan_v1(packet)

    assert not result.ready
    assert any('missing scheduled synthetic check for forms index' in problem for problem in result.problems)


def _deep_update(target: dict, patch: dict) -> None:
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_update(target[key], value)
        else:
            target[key] = copy.deepcopy(value)
