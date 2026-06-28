from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable, Mapping

MATRIX_CHECKS = (
    'missing_facts',
    'stale_evidence',
    'allowed_local_previews',
    'refused_consequential_actions',
    'manual_handoffs',
)

_EXPECTED_PAIRINGS = {
    'missing_facts': ('missing_fact_prompt', 'missing_facts'),
    'stale_evidence': ('stale_evidence_warning', 'stale_evidence'),
    'allowed_local_previews': ('allowed_local_preview', 'local_preview'),
    'refused_consequential_actions': ('refused_consequential_action', 'consequential_action'),
    'manual_handoffs': ('manual_handoff_response', 'manual_handoff'),
}

_SAFE_PREVIEW_CLASSES = {'local_preview', 'read_only', 'reversible_draft'}
_CONSEQUENTIAL_CLASSES = {
    'cancellation',
    'certification',
    'financial',
    'inspection_scheduling',
    'payment',
    'scheduling',
    'submission',
    'upload',
    'upload_to_official_record',
}
_MANUAL_HANDOFF_CLASSES = {'account_creation', 'captcha', 'mfa', 'password_recovery', 'manual_handoff'}
_PRIVATE_OR_LIVE_KEYS = {
    'access_token',
    'auth_state',
    'body',
    'card_number',
    'cookie',
    'cookies',
    'credential',
    'credentials',
    'cvv',
    'downloaded_document',
    'email',
    'field_value',
    'har',
    'html',
    'local_path',
    'page_text',
    'password',
    'payment_details',
    'phone',
    'private_value',
    'raw_body',
    'raw_crawl_output',
    'raw_html',
    'raw_text',
    'raw_value',
    'refresh_token',
    'screenshot',
    'secret',
    'session_cookie',
    'session_state',
    'ssn',
    'token',
    'trace',
    'user_input',
    'value',
}
_LIVE_LLM_FLAGS = {
    'llm_called',
    'llm_executed',
    'live_llm_called',
    'live_llm_execution',
    'model_called',
    'prompt_sent',
}
_DEVHUB_AUTOMATION_FLAGS = {
    'browser_automation_called',
    'devhub_automated',
    'devhub_called',
    'devhub_login_automated',
    'playwright_called',
}
_EXPECTED_RESPONSE_KEYS = {'expected_agent_response', 'expected_decision', 'expected_response', 'expected_response_text'}


class AgentApiContractConformanceMatrixError(ValueError):
    def __init__(self, problems: Iterable[str]) -> None:
        self.problems = tuple(problems)
        super().__init__('invalid agent API contract conformance matrix: ' + '; '.join(self.problems))


def load_agent_api_contract_conformance_fixture(path: str | Path) -> dict[str, Any]:
    raw = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(raw, dict):
        raise AgentApiContractConformanceMatrixError(['fixture must be a JSON object'])
    return build_agent_api_contract_conformance_matrix(
        agent_readiness_examples=_required_mapping(raw, 'agent_readiness_examples'),
        synthetic_guardrail_api_requests=_required_list(raw, 'synthetic_guardrail_api_requests'),
    )


def build_agent_api_contract_conformance_matrix(
    *,
    agent_readiness_examples: Mapping[str, Any],
    synthetic_guardrail_api_requests: list[Any],
) -> dict[str, Any]:
    examples_packet = deepcopy(dict(agent_readiness_examples))
    requests = deepcopy(synthetic_guardrail_api_requests)
    input_problems = _input_problems(examples_packet, requests)
    if input_problems:
        raise AgentApiContractConformanceMatrixError(input_problems)

    examples_by_type = {
        str(example.get('response_type') or ''): example
        for example in _mapping_items(examples_packet.get('api_examples'))
    }
    requests_by_type = {
        str(request.get('request_type') or ''): request
        for request in _mapping_items(requests)
    }

    rows = []
    for check_id in MATRIX_CHECKS:
        example_type, request_type = _EXPECTED_PAIRINGS[check_id]
        rows.append(_build_row(check_id, examples_by_type[example_type], requests_by_type[request_type]))

    matrix = {
        'packet_type': 'ppd.agent_api_contract_conformance_matrix.v1',
        'fixture_first': True,
        'synthetic': True,
        'llm_called': False,
        'devhub_called': False,
        'live_services_called': False,
        'metadata_only': True,
        'source_packet_type': examples_packet.get('packet_type'),
        'source_registry_promotion_id': examples_packet.get('source_registry_promotion_id'),
        'guardrail_promotion_id': examples_packet.get('guardrail_promotion_id'),
        'case_id': examples_packet.get('case_id'),
        'process_id': examples_packet.get('process_id'),
        'matrix_order': list(MATRIX_CHECKS),
        'rows': rows,
        'summary': {
            'checks_total': len(rows),
            'checks_passed': sum(1 for row in rows if row.get('conformance_status') == 'pass'),
            'checks_failed': sum(1 for row in rows if row.get('conformance_status') != 'pass'),
        },
    }

    matrix_problems = validate_agent_api_contract_conformance_matrix(matrix)
    if matrix_problems:
        raise AgentApiContractConformanceMatrixError(matrix_problems)
    return matrix


def validate_agent_api_contract_conformance_matrix(packet: Mapping[str, Any]) -> list[str]:
    problems: list[str] = []
    if packet.get('packet_type') != 'ppd.agent_api_contract_conformance_matrix.v1':
        problems.append('packet_type must be ppd.agent_api_contract_conformance_matrix.v1')
    for key in ('fixture_first', 'synthetic', 'metadata_only'):
        if packet.get(key) is not True:
            problems.append(f'{key} must be true')
    for key in ('llm_called', 'devhub_called', 'live_services_called'):
        if packet.get(key) is not False:
            problems.append(f'{key} must be false')
    if packet.get('matrix_order') != list(MATRIX_CHECKS):
        problems.append('matrix_order must list the five conformance checks')

    rows = packet.get('rows')
    if not isinstance(rows, list):
        problems.append('rows must be a list')
        rows = []
    row_ids = [row.get('check_id') for row in rows if isinstance(row, Mapping)]
    if row_ids != list(MATRIX_CHECKS):
        problems.append('rows must appear in deterministic matrix_order')
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            problems.append(f'rows[{index}] must be an object')
            continue
        problems.extend(_row_problems(row, f'rows[{index}]'))

    summary = packet.get('summary')
    if not isinstance(summary, Mapping):
        problems.append('summary must be an object')
    else:
        if summary.get('checks_total') != len(MATRIX_CHECKS):
            problems.append('summary.checks_total must equal matrix check count')
        if summary.get('checks_failed') != 0:
            problems.append('summary.checks_failed must be zero for committed fixture conformance')
        if summary.get('checks_passed') != len(MATRIX_CHECKS):
            problems.append('summary.checks_passed must equal matrix check count')

    problems.extend(_contract_safety_problems(packet))
    return _dedupe(problems)


def _input_problems(examples_packet: Mapping[str, Any], requests: list[Any]) -> list[str]:
    problems: list[str] = []
    if examples_packet.get('packet_type') != 'ppd.agent_readiness_contract_examples.v1':
        problems.append('agent_readiness_examples.packet_type must be ppd.agent_readiness_contract_examples.v1')
    for key in ('fixture_first', 'synthetic', 'metadata_only'):
        if examples_packet.get(key) is not True:
            problems.append(f'agent_readiness_examples.{key} must be true')
    for key in ('llm_called', 'devhub_called', 'live_services_called'):
        if examples_packet.get(key) is not False:
            problems.append(f'agent_readiness_examples.{key} must be false')

    examples = _mapping_items(examples_packet.get('api_examples'))
    example_types = [str(example.get('response_type') or '') for example in examples]
    expected_example_types = [pair[0] for pair in _EXPECTED_PAIRINGS.values()]
    if example_types != expected_example_types:
        problems.append('agent readiness examples must cover the five expected response types in order')
    for index, example in enumerate(examples):
        prefix = f'agent_readiness_examples.api_examples[{index}]'
        if not _citation_ids(example):
            problems.append(f'{prefix} expected response must include citations')

    request_items = _mapping_items(requests)
    request_types = [str(request.get('request_type') or '') for request in request_items]
    expected_request_types = [pair[1] for pair in _EXPECTED_PAIRINGS.values()]
    if request_types != expected_request_types:
        problems.append('synthetic guardrail API requests must cover the five expected request types in order')
    for index, request in enumerate(request_items):
        prefix = f'synthetic_guardrail_api_requests[{index}]'
        if request.get('synthetic') is not True:
            problems.append(f'{prefix}.synthetic must be true')
        for key in ('llm_called', 'devhub_called', 'live_services_called'):
            if request.get(key) is not False:
                problems.append(f'{prefix}.{key} must be false')
        if request.get('metadata_only') is not True:
            problems.append(f'{prefix}.metadata_only must be true')
        if not _non_empty_text(request.get('request_id')):
            problems.append(f'{prefix}.request_id is required')
        if not _string_list(request.get('source_evidence_ids')):
            problems.append(f'{prefix} expected response must be source-cited')

    problems.extend(_contract_safety_problems({'agent_readiness_examples': examples_packet}))
    problems.extend(_contract_safety_problems({'synthetic_guardrail_api_requests': requests}))
    return _dedupe(problems)


def _build_row(check_id: str, example: Mapping[str, Any], request: Mapping[str, Any]) -> dict[str, Any]:
    assertions = _assertions_for_check(check_id, example, request)
    passed = all(assertion['passed'] for assertion in assertions)
    return {
        'check_id': check_id,
        'readiness_response_type': example.get('response_type'),
        'readiness_response_id': example.get('response_id'),
        'guardrail_request_type': request.get('request_type'),
        'guardrail_request_id': request.get('request_id'),
        'conformance_status': 'pass' if passed else 'fail',
        'source_evidence_ids': sorted(set(_citation_ids(example)).union(_string_list(request.get('source_evidence_ids')))),
        'assertions': assertions,
    }


def _assertions_for_check(check_id: str, example: Mapping[str, Any], request: Mapping[str, Any]) -> list[dict[str, Any]]:
    if check_id == 'missing_facts':
        return [
            _assertion('readiness prompts for missing facts', bool(_mapping_items(example.get('prompt_fields')))),
            _assertion('request declares missing facts', bool(_string_list(request.get('missing_facts')))),
            _assertion('guardrail decision blocks automation until facts are supplied', request.get('expected_decision') in {'ask_missing_facts', 'blocked_missing_information'}),
        ]
    if check_id == 'stale_evidence':
        return [
            _assertion('readiness names stale evidence', bool(_string_list(example.get('stale_evidence_ids')))),
            _assertion('request names stale evidence', bool(_string_list(request.get('stale_evidence_ids')))),
            _assertion('readiness blocks until refresh', example.get('status') == 'blocked_until_refresh'),
            _assertion('guardrail decision requires refresh', request.get('expected_decision') == 'blocked_until_refresh'),
        ]
    if check_id == 'allowed_local_previews':
        allowed_actions = _mapping_items(example.get('allowed_actions'))
        return [
            _assertion('readiness exposes allowed local preview actions', bool(allowed_actions)),
            _assertion('allowed actions stay local and safe', all(_safe_allowed_action(action) for action in allowed_actions)),
            _assertion('request asks only for local preview', _action_class(request) == 'local_preview'),
            _assertion('guardrail decision allows local preview', request.get('expected_decision') == 'allowed_local_preview'),
        ]
    if check_id == 'refused_consequential_actions':
        refused_actions = _mapping_items(example.get('refused_actions'))
        return [
            _assertion('readiness refuses consequential actions', bool(refused_actions)),
            _assertion('refusals require exact confirmation and handoff', all(_safe_refusal(action) for action in refused_actions)),
            _assertion('request is consequential', _action_class(request) in _CONSEQUENTIAL_CLASSES),
            _assertion('guardrail decision refuses the action', request.get('expected_decision') == 'refused'),
        ]
    if check_id == 'manual_handoffs':
        handoffs = _mapping_items(example.get('manual_handoff_actions'))
        return [
            _assertion('readiness provides manual handoff actions', bool(handoffs)),
            _assertion('handoffs pause automation and require attendance', all(_safe_handoff(action) for action in handoffs)),
            _assertion('request is a manual handoff class', _action_class(request) in _MANUAL_HANDOFF_CLASSES),
            _assertion('guardrail decision routes to manual handoff', request.get('expected_decision') == 'manual_handoff'),
        ]
    return [_assertion('known matrix check', False, 'unsupported check')]


def _row_problems(row: Mapping[str, Any], path: str) -> list[str]:
    problems: list[str] = []
    if row.get('check_id') not in MATRIX_CHECKS:
        problems.append(f'{path}.check_id is unsupported')
    if row.get('conformance_status') != 'pass':
        problems.append(f'{path}.conformance_status must be pass')
    assertions = row.get('assertions')
    if not isinstance(assertions, list) or not assertions:
        problems.append(f'{path}.assertions must be a non-empty list')
    else:
        for index, assertion in enumerate(assertions):
            if not isinstance(assertion, Mapping):
                problems.append(f'{path}.assertions[{index}] must be an object')
                continue
            if not _non_empty_text(assertion.get('assertion')):
                problems.append(f'{path}.assertions[{index}].assertion is required')
            if assertion.get('passed') is not True:
                problems.append(f'{path}.assertions[{index}].passed must be true')
    if not _string_list(row.get('source_evidence_ids')):
        problems.append(f'{path}.source_evidence_ids must be non-empty')
    return problems


def _contract_safety_problems(packet: Any) -> list[str]:
    problems: list[str] = []
    problems.extend(_unsafe_key_problems(packet))
    problems.extend(_live_execution_flag_problems(packet))
    problems.extend(_expected_response_citation_problems(packet))
    problems.extend(_stale_marked_current_problems(packet))
    problems.extend(_blocked_action_downgrade_problems(packet))
    problems.extend(_manual_handoff_expectation_problems(packet))
    return _dedupe(problems)


def _expected_response_citation_problems(item: Any, path: str = 'packet') -> list[str]:
    problems: list[str] = []
    if isinstance(item, Mapping):
        has_expected = any(key in item for key in _EXPECTED_RESPONSE_KEYS)
        if has_expected and not _has_local_citation(item):
            problems.append(f'{path} expected response must include source citations')
        for key, nested in item.items():
            problems.extend(_expected_response_citation_problems(nested, f'{path}.{key}'))
    elif isinstance(item, list):
        for index, nested in enumerate(item):
            problems.extend(_expected_response_citation_problems(nested, f'{path}[{index}]'))
    return problems


def _stale_marked_current_problems(item: Any, path: str = 'packet') -> list[str]:
    problems: list[str] = []
    if isinstance(item, Mapping):
        stale_ids = set(_string_list(item.get('stale_source_ids')) + _string_list(item.get('stale_evidence_ids')))
        current_ids = set(_string_list(item.get('current_source_ids')) + _string_list(item.get('current_evidence_ids')))
        for source_id in sorted(stale_ids.intersection(current_ids)):
            problems.append(f'{path} marks stale source id {source_id} as current')
        source_id = item.get('source_id') or item.get('evidence_id')
        if isinstance(source_id, str) and source_id in stale_ids and item.get('freshness_status') == 'current':
            problems.append(f'{path} marks stale source id {source_id} as current')
        for key in ('source_freshness', 'evidence_freshness', 'source_statuses'):
            statuses = item.get(key)
            if isinstance(statuses, Mapping):
                for source_id, status in statuses.items():
                    if source_id in stale_ids and status == 'current':
                        problems.append(f'{path}.{key} marks stale source id {source_id} as current')
        for key, nested in item.items():
            problems.extend(_stale_marked_current_problems(nested, f'{path}.{key}'))
    elif isinstance(item, list):
        for index, nested in enumerate(item):
            problems.extend(_stale_marked_current_problems(nested, f'{path}[{index}]'))
    return problems


def _blocked_action_downgrade_problems(item: Any, path: str = 'packet') -> list[str]:
    problems: list[str] = []
    if isinstance(item, Mapping):
        classification = str(item.get('classification') or item.get('action_class') or '')
        status = str(item.get('status') or item.get('expected_decision') or '')
        action_id = str(item.get('action_id') or item.get('requested_action_id') or path)
        if classification in _CONSEQUENTIAL_CLASSES and status in {'allowed', 'allowed_local_preview', 'safe', 'next_safe_action'}:
            problems.append(f'{path} downgrades blocked consequential action {action_id} to allowed')
        if item.get('blocked') is True and item.get('allowed') is True:
            problems.append(f'{path} downgrades blocked action {action_id} to allowed')
        if item.get('requires_exact_confirmation') is True and item.get('allowed') is True:
            problems.append(f'{path} allows action {action_id} despite exact-confirmation requirement')
        for key, nested in item.items():
            problems.extend(_blocked_action_downgrade_problems(nested, f'{path}.{key}'))
    elif isinstance(item, list):
        for index, nested in enumerate(item):
            problems.extend(_blocked_action_downgrade_problems(nested, f'{path}[{index}]'))
    return problems


def _manual_handoff_expectation_problems(item: Any, path: str = 'packet') -> list[str]:
    problems: list[str] = []
    if isinstance(item, Mapping):
        classification = str(item.get('classification') or item.get('action_class') or '')
        action_id = str(item.get('action_id') or item.get('requested_action_id') or path)
        if classification in _CONSEQUENTIAL_CLASSES and item.get('status') in {'refused', 'blocked'}:
            if item.get('requires_manual_handoff') is not True:
                problems.append(f'{path} missing manual-handoff expectation for blocked action {action_id}')
        if classification in _MANUAL_HANDOFF_CLASSES:
            if item.get('requires_user_attendance') is False or item.get('automation_paused') is False:
                problems.append(f'{path} missing manual-handoff attendance expectation for {action_id}')
            decision = item.get('expected_decision')
            if decision is not None and decision != 'manual_handoff':
                problems.append(f'{path} manual handoff action {action_id} cannot expect {decision}')
        for key, nested in item.items():
            problems.extend(_manual_handoff_expectation_problems(nested, f'{path}.{key}'))
    elif isinstance(item, list):
        for index, nested in enumerate(item):
            problems.extend(_manual_handoff_expectation_problems(nested, f'{path}[{index}]'))
    return problems


def _live_execution_flag_problems(item: Any, path: str = 'packet') -> list[str]:
    problems: list[str] = []
    if isinstance(item, Mapping):
        for key, nested in item.items():
            key_text = str(key).lower()
            nested_path = f'{path}.{key}'
            if key_text in _LIVE_LLM_FLAGS and nested is not False:
                problems.append(f'{nested_path} must be false; live LLM execution is not allowed')
            if key_text in _DEVHUB_AUTOMATION_FLAGS and nested is not False:
                problems.append(f'{nested_path} must be false; DevHub automation claims are not allowed')
            problems.extend(_live_execution_flag_problems(nested, nested_path))
    elif isinstance(item, list):
        for index, nested in enumerate(item):
            problems.extend(_live_execution_flag_problems(nested, f'{path}[{index}]'))
    return problems


def _safe_allowed_action(action: Mapping[str, Any]) -> bool:
    return action.get('allowed') is True and action.get('devhub_called') is False and str(action.get('classification') or '') in _SAFE_PREVIEW_CLASSES


def _safe_refusal(action: Mapping[str, Any]) -> bool:
    return str(action.get('classification') or '') in _CONSEQUENTIAL_CLASSES and action.get('status') == 'refused' and action.get('requires_exact_confirmation') is True and action.get('requires_manual_handoff') is True


def _safe_handoff(action: Mapping[str, Any]) -> bool:
    return action.get('requires_user_attendance') is True and action.get('automation_paused') is True


def _action_class(request: Mapping[str, Any]) -> str:
    action = request.get('requested_action')
    if isinstance(action, Mapping):
        return str(action.get('classification') or '')
    return ''


def _assertion(name: str, passed: bool, detail: str = '') -> dict[str, Any]:
    return {'assertion': name, 'passed': bool(passed), 'detail': detail}


def _citation_ids(example: Mapping[str, Any]) -> list[str]:
    ids = []
    for citation in _mapping_items(example.get('citations')):
        evidence_id = citation.get('evidence_id')
        if isinstance(evidence_id, str) and evidence_id:
            ids.append(evidence_id)
    return ids


def _has_local_citation(item: Mapping[str, Any]) -> bool:
    return bool(
        _mapping_items(item.get('citations'))
        or _string_list(item.get('source_evidence_ids'))
        or _string_list(item.get('evidence_ids'))
        or _string_list(item.get('source_ids'))
    )


def _required_mapping(fixture: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    item = fixture.get(key)
    if not isinstance(item, Mapping):
        raise AgentApiContractConformanceMatrixError([f'fixture is missing {key}'])
    return item


def _required_list(fixture: Mapping[str, Any], key: str) -> list[Any]:
    item = fixture.get(key)
    if not isinstance(item, list):
        raise AgentApiContractConformanceMatrixError([f'fixture is missing {key}'])
    return item


def _mapping_items(items: Any) -> list[Mapping[str, Any]]:
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, Mapping)]


def _string_list(items: Any) -> list[str]:
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, str) and item]


def _non_empty_text(item: Any) -> bool:
    return isinstance(item, str) and bool(item.strip())


def _unsafe_key_problems(item: Any, path: str = 'packet') -> list[str]:
    problems: list[str] = []
    if isinstance(item, Mapping):
        for key, nested in item.items():
            nested_path = f'{path}.{key}'
            if str(key).lower() in _PRIVATE_OR_LIVE_KEYS:
                problems.append(f'{nested_path} is a private or live artifact field')
            problems.extend(_unsafe_key_problems(nested, nested_path))
    elif isinstance(item, list):
        for index, nested in enumerate(item):
            problems.extend(_unsafe_key_problems(nested, f'{path}[{index}]'))
    elif isinstance(item, str):
        lowered = item.lower()
        private_path_markers = ('file://', '/home/', '/users/', '\\users\\', 'c:\\users\\', '/private/')
        if any(marker in lowered for marker in private_path_markers):
            problems.append(f'{path} contains a private local path')
    return problems


def _dedupe(problems: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for problem in problems:
        if problem not in seen:
            seen.add(problem)
            result.append(problem)
    return result
