from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ppd.agent_regression_rerun_plan import (
    assert_valid_agent_regression_rerun_plan,
    compile_agent_regression_rerun_plan,
)

FIXTURE_PATH = Path(__file__).parent / 'fixtures' / 'agent_regression_rerun_plan' / 'stale_predicate_cases.json'


def _load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding='utf-8'))


def test_rerun_plan_selects_only_synthetic_cases_affected_by_candidate() -> None:
    plan = compile_agent_regression_rerun_plan(_load_fixture())

    assert plan['plan_status'] == 'fixture_only_no_llm_no_devhub_no_private_file_reads'
    assert plan['selected_case_count'] == 2
    assert {case['case_id'] for case in plan['selected_cases']} == {
        'synthetic-single-pdf-upload-staging',
        'synthetic-final-submit-refusal',
    }
    assert plan['excluded_case_ids'] == ['synthetic-unaffected-status-review']


def test_rerun_plan_lists_expected_agent_outputs_for_each_selected_case() -> None:
    plan = compile_agent_regression_rerun_plan(_load_fixture())

    for case in plan['selected_cases']:
        assert case['remediation_links']
        assert case['expected_allowed_prompts']
        assert case['refused_actions']
        assert case['manual_handoffs']
        assert case['stale_evidence_warnings']
        assert case['local_preview_boundaries']['calls_llm'] is False
        assert case['local_preview_boundaries']['launches_devhub'] is False
        assert case['local_preview_boundaries']['reads_private_files'] is False
        assert case['local_preview_boundaries']['writes_private_session_artifacts'] is False

    submit_case = next(case for case in plan['selected_cases'] if case['case_id'] == 'synthetic-final-submit-refusal')
    refused_ids = {action['action_id'] for action in submit_case['refused_actions']}
    assert {'submit permit application', 'certify acknowledgement'}.issubset(refused_ids)


def test_rerun_plan_has_global_no_llm_no_devhub_no_private_boundaries() -> None:
    plan = compile_agent_regression_rerun_plan(_load_fixture())

    assert plan['execution_boundaries'] == {
        'calls_llm': False,
        'launches_devhub': False,
        'uses_authenticated_session': False,
        'reads_private_files': False,
        'writes_private_artifacts': False,
        'source': 'committed PP&D test fixtures only',
    }
    assert_valid_agent_regression_rerun_plan(plan)


def test_rerun_plan_rejects_llm_devhub_and_private_file_inputs() -> None:
    fixture = _load_fixture()
    fixture['call_llm'] = True
    with pytest.raises(ValueError):
        compile_agent_regression_rerun_plan(fixture)

    fixture = _load_fixture()
    fixture['launch_devhub'] = True
    with pytest.raises(ValueError):
        compile_agent_regression_rerun_plan(fixture)

    fixture = _load_fixture()
    fixture['synthetic_cases'][0]['private_path'] = '/home/example/private/devhub/session.json'
    with pytest.raises(ValueError):
        compile_agent_regression_rerun_plan(fixture)


def test_rerun_plan_validation_rejects_missing_remediation_links() -> None:
    plan = compile_agent_regression_rerun_plan(_load_fixture())
    plan['selected_cases'][0]['remediation_links'] = []

    with pytest.raises(ValueError, match='remediation_links'):
        assert_valid_agent_regression_rerun_plan(plan)


def test_rerun_plan_validation_rejects_uncited_expected_outcomes() -> None:
    plan = compile_agent_regression_rerun_plan(_load_fixture())
    plan['selected_cases'][0]['expected_allowed_prompts'][0].pop('source_evidence_ids')

    with pytest.raises(ValueError, match='uncited'):
        assert_valid_agent_regression_rerun_plan(plan)


def test_rerun_plan_validation_rejects_private_values_and_live_execution_flags() -> None:
    plan = compile_agent_regression_rerun_plan(_load_fixture())
    with_private_value = copy.deepcopy(plan)
    with_private_value['selected_cases'][0]['private_value'] = 'synthetic private owner phone number'
    with pytest.raises(ValueError, match='private'):
        assert_valid_agent_regression_rerun_plan(with_private_value)

    with_live_flag = copy.deepcopy(plan)
    with_live_flag['execution_boundaries']['live_llm_execution'] = True
    with pytest.raises(ValueError, match='LLM|DevHub'):
        assert_valid_agent_regression_rerun_plan(with_live_flag)

    with_devhub_flag = copy.deepcopy(plan)
    with_devhub_flag['selected_cases'][0]['devhub_execution_enabled'] = True
    with pytest.raises(ValueError, match='LLM|DevHub'):
        assert_valid_agent_regression_rerun_plan(with_devhub_flag)


def test_rerun_plan_validation_rejects_blocked_action_downgrades() -> None:
    plan = compile_agent_regression_rerun_plan(_load_fixture())
    plan['selected_cases'][0]['allowed_actions'] = [
        {
            'action_id': 'upload supporting documents',
            'classification': 'allowed',
            'source_evidence_ids': ['evidence-submit-plans-single-pdf-rule'],
        }
    ]

    with pytest.raises(ValueError, match='downgrades'):
        assert_valid_agent_regression_rerun_plan(plan)


def test_rerun_plan_validation_rejects_missing_manual_handoff_expectations_for_consequential_workflows() -> None:
    plan = compile_agent_regression_rerun_plan(_load_fixture())
    for handoff in plan['selected_cases'][1]['manual_handoffs']:
        handoff['requires_attendance'] = False
        handoff['requires_exact_confirmation'] = False

    with pytest.raises(ValueError, match='manual-handoff'):
        assert_valid_agent_regression_rerun_plan(plan)
