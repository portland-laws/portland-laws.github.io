from __future__ import annotations

from copy import deepcopy

import pytest

from ppd.agent_readiness.conformance_matrix import (
    AgentApiContractConformanceMatrixError,
    build_agent_api_contract_conformance_matrix,
    validate_agent_api_contract_conformance_matrix,
)


def _example(response_type: str, response_id: str, **extra: object) -> dict:
    base = {
        'response_type': response_type,
        'response_id': response_id,
        'citations': [{'evidence_id': f'ev-{response_id}', 'freshness_status': 'current'}],
    }
    base.update(extra)
    return base


def _request(request_type: str, request_id: str, classification: str, expected_decision: str, **extra: object) -> dict:
    base = {
        'request_type': request_type,
        'request_id': request_id,
        'synthetic': True,
        'metadata_only': True,
        'llm_called': False,
        'devhub_called': False,
        'live_services_called': False,
        'requested_action': {'action_id': request_id, 'classification': classification},
        'expected_decision': expected_decision,
        'source_evidence_ids': [f'ev-{request_id}'],
    }
    base.update(extra)
    return base


def _fixture() -> dict:
    return {
        'agent_readiness_examples': {
            'packet_type': 'ppd.agent_readiness_contract_examples.v1',
            'fixture_first': True,
            'synthetic': True,
            'metadata_only': True,
            'llm_called': False,
            'devhub_called': False,
            'live_services_called': False,
            'source_registry_promotion_id': 'source-registry-synthetic',
            'guardrail_promotion_id': 'guardrail-synthetic',
            'case_id': 'case-synthetic',
            'process_id': 'single-pdf-process',
            'api_examples': [
                _example('missing_fact_prompt', 'missing-facts', prompt_fields=[{'field_id': 'project_scope'}]),
                _example('stale_evidence_warning', 'stale-evidence', status='blocked_until_refresh', stale_evidence_ids=['ev-stale']),
                _example('allowed_local_preview', 'local-preview', allowed_actions=[{'action_id': 'preview-pdf', 'classification': 'local_preview', 'allowed': True, 'devhub_called': False}]),
                _example('refused_consequential_action', 'refused-action', refused_actions=[{'action_id': 'submit-permit', 'classification': 'submission', 'status': 'refused', 'requires_exact_confirmation': True, 'requires_manual_handoff': True}]),
                _example('manual_handoff_response', 'manual-handoff', manual_handoff_actions=[{'action_id': 'mfa', 'classification': 'mfa', 'requires_user_attendance': True, 'automation_paused': True}]),
            ],
        },
        'synthetic_guardrail_api_requests': [
            _request('missing_facts', 'req-missing', 'read_only', 'ask_missing_facts', missing_facts=['project_scope']),
            _request('stale_evidence', 'req-stale', 'read_only', 'blocked_until_refresh', stale_evidence_ids=['ev-stale']),
            _request('local_preview', 'req-preview', 'local_preview', 'allowed_local_preview'),
            _request('consequential_action', 'req-submit', 'submission', 'refused'),
            _request('manual_handoff', 'req-mfa', 'mfa', 'manual_handoff'),
        ],
    }


def _build(fixture: dict) -> dict:
    return build_agent_api_contract_conformance_matrix(
        agent_readiness_examples=fixture['agent_readiness_examples'],
        synthetic_guardrail_api_requests=fixture['synthetic_guardrail_api_requests'],
    )


def test_builds_valid_fixture_first_conformance_matrix() -> None:
    matrix = _build(_fixture())

    assert matrix['packet_type'] == 'ppd.agent_api_contract_conformance_matrix.v1'
    assert matrix['summary']['checks_failed'] == 0
    assert validate_agent_api_contract_conformance_matrix(matrix) == []


def test_rejects_uncited_expected_responses() -> None:
    fixture = _fixture()
    fixture['agent_readiness_examples']['api_examples'][0]['citations'] = []

    with pytest.raises(AgentApiContractConformanceMatrixError) as excinfo:
        _build(fixture)

    assert any('expected response must include citations' in problem for problem in excinfo.value.problems)


def test_rejects_private_values_local_paths_and_live_artifact_fields() -> None:
    fixture = _fixture()
    fixture['synthetic_guardrail_api_requests'][0]['private_value'] = 'not for fixtures'
    fixture['synthetic_guardrail_api_requests'][1]['document_ref'] = '/home/alex/private/permit.pdf'

    with pytest.raises(AgentApiContractConformanceMatrixError) as excinfo:
        _build(fixture)

    problems = excinfo.value.problems
    assert any('private_value' in problem for problem in problems)
    assert any('private local path' in problem for problem in problems)


def test_rejects_stale_source_ids_marked_current() -> None:
    fixture = _fixture()
    fixture['synthetic_guardrail_api_requests'][1]['stale_source_ids'] = ['source-devhub-faq']
    fixture['synthetic_guardrail_api_requests'][1]['current_source_ids'] = ['source-devhub-faq']

    with pytest.raises(AgentApiContractConformanceMatrixError) as excinfo:
        _build(fixture)

    assert any('marks stale source id source-devhub-faq as current' in problem for problem in excinfo.value.problems)


def test_rejects_blocked_action_downgrades_and_missing_manual_handoff_expectations() -> None:
    fixture = _fixture()
    action = fixture['agent_readiness_examples']['api_examples'][3]['refused_actions'][0]
    action['allowed'] = True
    action['requires_manual_handoff'] = False

    with pytest.raises(AgentApiContractConformanceMatrixError) as excinfo:
        _build(fixture)

    problems = excinfo.value.problems
    assert any('allows action submit-permit despite exact-confirmation requirement' in problem for problem in problems)
    assert any('missing manual-handoff expectation' in problem for problem in problems)


def test_rejects_live_llm_flags_and_devhub_automation_claims() -> None:
    matrix = _build(_fixture())
    mutated = deepcopy(matrix)
    mutated['rows'][0]['live_llm_execution'] = True
    mutated['rows'][1]['devhub_automated'] = True

    errors = validate_agent_api_contract_conformance_matrix(mutated)

    assert any('live LLM execution is not allowed' in error for error in errors)
    assert any('DevHub automation claims are not allowed' in error for error in errors)
