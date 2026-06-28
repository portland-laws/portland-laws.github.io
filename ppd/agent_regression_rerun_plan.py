from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

PRIVATE_FIELD_NAMES = {
    'api_key',
    'auth_state',
    'authorization',
    'cookie',
    'cookies',
    'credential',
    'credentials',
    'cvv',
    'devhub_session',
    'email',
    'har',
    'password',
    'payment_detail',
    'payment_details',
    'private_file',
    'private_path',
    'private_value',
    'raw_private_file',
    'refresh_token',
    'secret',
    'session_state',
    'ssn',
    'token',
    'trace',
}

PRIVATE_PATH_MARKERS = (
    '/home/',
    '/Users/',
    'C:/Users/',
    'file://',
    'devhub/session',
    'auth_state',
    '.har',
    'trace.zip',
)

LIVE_OR_MODEL_KEYS = {
    'call_llm',
    'calls_llm',
    'devhub_enabled',
    'devhub_execution_enabled',
    'execute_in_devhub',
    'execute_live_devhub',
    'execute_live_llm',
    'execute_with_llm',
    'launch_devhub',
    'launches_devhub',
    'live_devhub',
    'live_devhub_execution',
    'live_execution',
    'live_llm',
    'live_llm_execution',
    'llm_execution_enabled',
    'model_invocation',
    'open_browser',
    'playwright_enabled',
    'read_private_files',
    'reads_private_files',
    'run_devhub',
    'run_llm',
    'uses_authenticated_session',
    'uses_devhub',
    'uses_llm',
}

CONSEQUENTIAL_ACTION_TOKENS = {
    'cancel',
    'certify',
    'certify_acknowledgement',
    'enter_payment_details',
    'official_upload',
    'pay_fee',
    'purchase_trade_permit',
    'reactivate',
    'request_extension',
    'schedule_inspection',
    'submit_application',
    'submit_payment',
    'submit_permit_application',
    'submit_permit_request',
    'upload_correction',
    'upload_supporting_documents',
    'withdraw',
}

DOWNGRADED_ACTION_STATES = {'allowed', 'safe', 'read_only', 'readonly', 'reversible', 'draft', 'local_preview'}

DEFAULT_LOCAL_PREVIEW_BOUNDARIES = {
    'calls_llm': False,
    'launches_devhub': False,
    'reads_private_files': False,
    'writes_private_session_artifacts': False,
    'allowed_scope': 'committed_fixture_metadata_only',
}


def compile_agent_regression_rerun_plan(packet: Mapping[str, Any]) -> dict[str, Any]:
    '''Build a deterministic rerun plan for affected synthetic cases only.'''

    _reject_private_or_live_inputs(packet)

    candidate = _mapping(packet.get('stale_predicate_remediation_candidate') or packet.get('candidate'))
    candidate_id = str(candidate.get('candidate_id') or candidate.get('packet_id') or 'stale-predicate-remediation-candidate')
    affected_predicate_ids = _candidate_predicate_ids(candidate)
    affected_case_tags = set(_string_list(candidate.get('affected_case_tags')))

    selected_cases: list[dict[str, Any]] = []
    for case in _sequence_of_mappings(packet.get('synthetic_cases')):
        if not bool(case.get('synthetic', True)):
            continue
        if not _case_is_affected(case, affected_predicate_ids, affected_case_tags):
            continue
        selected_cases.append(_compile_case_plan(case, candidate_id, affected_predicate_ids, affected_case_tags))

    plan = {
        'plan_id': str(packet.get('plan_id') or 'fixture-first-agent-regression-rerun-plan'),
        'plan_status': 'fixture_only_no_llm_no_devhub_no_private_file_reads',
        'candidate_id': candidate_id,
        'affected_predicate_ids': sorted(affected_predicate_ids),
        'selected_case_count': len(selected_cases),
        'selected_cases': selected_cases,
        'excluded_case_ids': _excluded_case_ids(packet.get('synthetic_cases'), selected_cases),
        'execution_boundaries': {
            'calls_llm': False,
            'launches_devhub': False,
            'uses_authenticated_session': False,
            'reads_private_files': False,
            'writes_private_artifacts': False,
            'source': 'committed PP&D test fixtures only',
        },
    }
    assert_valid_agent_regression_rerun_plan(plan)
    return plan


def assert_valid_agent_regression_rerun_plan(plan: Mapping[str, Any]) -> None:
    '''Raise ValueError if a compiled rerun plan violates PP&D fixture-first rules.'''

    _reject_private_or_live_inputs(plan)
    if plan.get('plan_status') != 'fixture_only_no_llm_no_devhub_no_private_file_reads':
        raise ValueError('rerun plan must be fixture-only')
    boundaries = _mapping(plan.get('execution_boundaries'))
    for key in ('calls_llm', 'launches_devhub', 'uses_authenticated_session', 'reads_private_files', 'writes_private_artifacts'):
        if boundaries.get(key) is not False:
            raise ValueError('rerun plan boundary is not explicitly disabled: ' + key)
    for case in _sequence_of_mappings(plan.get('selected_cases')):
        _require_non_empty_list(case, 'remediation_links')
        _require_non_empty_list(case, 'expected_allowed_prompts')
        _require_non_empty_list(case, 'refused_actions')
        _require_non_empty_list(case, 'manual_handoffs')
        _require_non_empty_list(case, 'stale_evidence_warnings')
        _validate_remediation_links(case)
        _validate_cited_expected_outcomes(case)
        _validate_no_blocked_action_downgrades(case)
        _validate_manual_handoffs_for_consequential_workflows(case)
        local_boundaries = _mapping(case.get('local_preview_boundaries'))
        for key in ('calls_llm', 'launches_devhub', 'reads_private_files', 'writes_private_session_artifacts'):
            if local_boundaries.get(key) is not False:
                raise ValueError('local preview boundary is not explicitly disabled: ' + key)


def _compile_case_plan(
    case: Mapping[str, Any],
    candidate_id: str,
    affected_predicate_ids: set[str],
    affected_case_tags: set[str],
) -> dict[str, Any]:
    case_id = str(case.get('case_id') or case.get('id') or 'synthetic-case')
    case_predicates = set(_string_list(case.get('predicate_ids') or case.get('affected_predicate_ids')))
    case_tags = set(_string_list(case.get('case_tags') or case.get('tags')))
    intersecting_predicates = sorted(case_predicates & affected_predicate_ids) or sorted(case_predicates)
    intersecting_tags = sorted(case_tags & affected_case_tags)

    stale_warnings = _list_of_mappings(case.get('stale_evidence_warnings'))
    if not stale_warnings:
        stale_warnings = [
            {
                'evidence_id': evidence_id,
                'warning': 'Fixture evidence is stale; do not rely on it silently in the rerun.',
            }
            for evidence_id in _string_list(case.get('stale_evidence'))
        ]
    default_citations = _case_default_citations(case, stale_warnings)

    local_preview_boundaries = dict(DEFAULT_LOCAL_PREVIEW_BOUNDARIES)
    local_preview_boundaries.update(_mapping(case.get('local_preview_boundaries')))

    result = {
        'case_id': case_id,
        'selection_reason': 'synthetic_case_affected_by_stale_predicate_candidate',
        'remediation_links': _remediation_links(case, candidate_id, intersecting_predicates, intersecting_tags, default_citations),
        'affected_predicate_ids': intersecting_predicates,
        'affected_case_tags': intersecting_tags,
        'expected_allowed_prompts': _with_default_citations(case.get('expected_allowed_prompts'), default_citations),
        'refused_actions': _with_default_citations(case.get('refused_actions'), default_citations),
        'manual_handoffs': _with_default_citations(case.get('manual_handoffs'), default_citations),
        'stale_evidence_warnings': stale_warnings,
        'local_preview_boundaries': local_preview_boundaries,
    }
    _require_complete_case_plan(result)
    return result


def _require_complete_case_plan(case_plan: Mapping[str, Any]) -> None:
    assert_valid_agent_regression_rerun_plan({
        'plan_status': 'fixture_only_no_llm_no_devhub_no_private_file_reads',
        'selected_cases': [case_plan],
        'execution_boundaries': {
            'calls_llm': False,
            'launches_devhub': False,
            'uses_authenticated_session': False,
            'reads_private_files': False,
            'writes_private_artifacts': False,
        },
    })


def _require_non_empty_list(mapping: Mapping[str, Any], key: str) -> None:
    value = mapping.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError('rerun plan case must list ' + key)


def _validate_remediation_links(case: Mapping[str, Any]) -> None:
    for link in _sequence_of_mappings(case.get('remediation_links')):
        if not _text(link.get('candidate_id')):
            raise ValueError('rerun plan remediation link must include candidate_id')
        if not (_text(link.get('predicate_id')) or _text(link.get('fix_id')) or _string_list(link.get('source_evidence_ids'))):
            raise ValueError('rerun plan remediation link must identify a predicate, fix, or source evidence')


def _validate_cited_expected_outcomes(case: Mapping[str, Any]) -> None:
    for group_name in ('expected_allowed_prompts', 'refused_actions', 'manual_handoffs'):
        for index, outcome in enumerate(_sequence_of_mappings(case.get(group_name))):
            if not _string_list(outcome.get('source_evidence_ids')):
                raise ValueError(f'rerun plan expected outcome is uncited: {group_name}[{index}]')
    for index, warning in enumerate(_sequence_of_mappings(case.get('stale_evidence_warnings'))):
        if not _text(warning.get('evidence_id')):
            raise ValueError(f'rerun plan stale evidence warning is uncited: stale_evidence_warnings[{index}]')


def _validate_no_blocked_action_downgrades(case: Mapping[str, Any]) -> None:
    for group_name in ('allowed_actions', 'safe_actions', 'next_safe_actions', 'reversible_actions'):
        for action in _sequence_of_mappings(case.get(group_name)):
            if _is_consequential_action(action) and str(action.get('classification', group_name)).lower() in DOWNGRADED_ACTION_STATES:
                raise ValueError('rerun plan downgrades a consequential blocked action')
    for action in _sequence_of_mappings(case.get('blocked_actions')):
        if _is_consequential_action(action) and str(action.get('classification', '')).lower() in DOWNGRADED_ACTION_STATES:
            raise ValueError('rerun plan downgrades a consequential blocked action')
    for action in _sequence_of_mappings(case.get('refused_actions')):
        if _is_consequential_action(action):
            if action.get('requires_attendance') is not True:
                raise ValueError('rerun plan consequential refusal must require attendance')
            if action.get('requires_exact_confirmation') is not True:
                raise ValueError('rerun plan consequential refusal must require exact confirmation')


def _validate_manual_handoffs_for_consequential_workflows(case: Mapping[str, Any]) -> None:
    consequential = [action for action in _sequence_of_mappings(case.get('refused_actions')) if _is_consequential_action(action)]
    consequential.extend(action for action in _sequence_of_mappings(case.get('blocked_actions')) if _is_consequential_action(action))
    if not consequential:
        return
    handoffs = _sequence_of_mappings(case.get('manual_handoffs'))
    if not any(handoff.get('requires_attendance') is True and handoff.get('requires_exact_confirmation') is True for handoff in handoffs):
        raise ValueError('rerun plan consequential workflow must include manual-handoff expectations')


def _is_consequential_action(action: Mapping[str, Any]) -> bool:
    values = [action.get('action'), action.get('action_id'), action.get('kind'), action.get('workflow'), action.get('control')]
    normalized = {_normalize_action(value) for value in values if _text(value)}
    return any(token in CONSEQUENTIAL_ACTION_TOKENS for token in normalized) or any(
        any(token in normalized_value for token in CONSEQUENTIAL_ACTION_TOKENS)
        for normalized_value in normalized
    )


def _normalize_action(value: Any) -> str:
    return re.sub(r'[^a-z0-9]+', '_', str(value).strip().lower()).strip('_')


def _candidate_predicate_ids(candidate: Mapping[str, Any]) -> set[str]:
    predicate_ids = set(_string_list(candidate.get('affected_predicate_ids')))
    for change in _sequence_of_mappings(candidate.get('proposed_predicate_changes')):
        predicate_ids.update(_string_list(change.get('target_item_ids')))
        predicate_id = change.get('predicate_id')
        if isinstance(predicate_id, str) and predicate_id:
            predicate_ids.add(predicate_id)
    for evidence in _sequence_of_mappings(candidate.get('normalized_citation_evidence')):
        predicate_ids.update(_string_list(evidence.get('target_item_ids')))
    return predicate_ids


def _case_is_affected(case: Mapping[str, Any], affected_predicate_ids: set[str], affected_case_tags: set[str]) -> bool:
    if case.get('affected_by_candidate') is True:
        return True
    case_predicates = set(_string_list(case.get('predicate_ids') or case.get('affected_predicate_ids')))
    if affected_predicate_ids and case_predicates & affected_predicate_ids:
        return True
    case_tags = set(_string_list(case.get('case_tags') or case.get('tags')))
    return bool(affected_case_tags and case_tags & affected_case_tags)


def _excluded_case_ids(cases_value: Any, selected_cases: Sequence[Mapping[str, Any]]) -> list[str]:
    selected_ids = {str(case.get('case_id')) for case in selected_cases}
    excluded: list[str] = []
    for case in _sequence_of_mappings(cases_value):
        case_id = str(case.get('case_id') or case.get('id') or 'synthetic-case')
        if case_id not in selected_ids:
            excluded.append(case_id)
    return sorted(excluded)


def _remediation_links(
    case: Mapping[str, Any],
    candidate_id: str,
    predicate_ids: Sequence[str],
    case_tags: Sequence[str],
    default_citations: Sequence[str],
) -> list[dict[str, Any]]:
    existing = _list_of_mappings(case.get('remediation_links'))
    if existing:
        return existing
    if predicate_ids:
        return [
            {
                'candidate_id': candidate_id,
                'predicate_id': predicate_id,
                'source_evidence_ids': list(default_citations),
            }
            for predicate_id in predicate_ids
        ]
    return [
        {
            'candidate_id': candidate_id,
            'case_tags': list(case_tags),
            'source_evidence_ids': list(default_citations),
        }
    ]


def _case_default_citations(case: Mapping[str, Any], stale_warnings: Sequence[Mapping[str, Any]]) -> list[str]:
    citations = _string_list(case.get('source_evidence_ids'))
    for prompt in _sequence_of_mappings(case.get('expected_allowed_prompts')):
        citations.extend(_string_list(prompt.get('source_evidence_ids')))
    citations.extend(str(warning.get('evidence_id')) for warning in stale_warnings if _text(warning.get('evidence_id')))
    return sorted(set(citations)) or ['fixture-source-evidence-required']


def _with_default_citations(value: Any, default_citations: Sequence[str]) -> list[dict[str, Any]]:
    rows = _list_of_mappings(value)
    for row in rows:
        if not _string_list(row.get('source_evidence_ids')):
            row['source_evidence_ids'] = list(default_citations)
    return rows


def _reject_private_or_live_inputs(value: Any) -> None:
    for key, nested in _walk(value):
        normalized_key = key.lower()
        if normalized_key in LIVE_OR_MODEL_KEYS and _has_value(nested):
            raise ValueError('rerun plan fixtures must not request LLM, DevHub, browser, or private-file access')
        if normalized_key in PRIVATE_FIELD_NAMES and _has_value(nested):
            raise ValueError('rerun plan fixtures must not include private fields')
        if isinstance(nested, str) and any(marker in nested for marker in PRIVATE_PATH_MARKERS):
            raise ValueError('rerun plan fixtures must not include private local paths or runtime artifacts')


def _walk(value: Any, key: str = '') -> list[tuple[str, Any]]:
    items = [(key, value)]
    if isinstance(value, Mapping):
        for child_key, child_value in value.items():
            items.extend(_walk(child_value, str(child_key)))
    elif isinstance(value, list):
        for child in value:
            items.extend(_walk(child, key))
    return items


def _has_value(value: Any) -> bool:
    return value not in (False, None, '', [], {})


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _sequence_of_mappings(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _list_of_mappings(value: Any) -> list[dict[str, Any]]:
    return [dict(item) for item in _sequence_of_mappings(value)]


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if not isinstance(value, Sequence) or isinstance(value, (bytes, bytearray)):
        return []
    return [str(item) for item in value if str(item)]


__all__ = [
    'assert_valid_agent_regression_rerun_plan',
    'compile_agent_regression_rerun_plan',
]
