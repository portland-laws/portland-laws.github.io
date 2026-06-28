'''Fixture-first release readiness checks for PP&D agent guardrail APIs.

The checklist intentionally proves non-readiness for consequential actions unless
fixture-backed guardrail responses cite the boundary and classify the action.
'''

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping, Sequence

SAFE_PROMPT = 'allowed_user_prompt'
LOCAL_PREVIEW = 'local_preview'
REVERSIBLE_DRAFT = 'reversible_draft_preview'
REFUSED_ACTION = 'refused_action'
MANUAL_HANDOFF = 'manual_handoff'
REVIEW_BLOCKER = 'unresolved_review_blocker'
NOT_READY = 'not_ready'

CONSEQUENTIAL_ACTIONS = (
    'payment',
    'certification',
    'upload',
    'submission',
    'cancellation',
    'scheduling',
)
EXPLICIT_NOT_READY_ACTIONS = ('submission', 'payment', 'upload', 'scheduling')
BLOCKING_DECISIONS = {REFUSED_ACTION, MANUAL_HANDOFF, REVIEW_BLOCKER, NOT_READY}
REQUIRED_SECTIONS = (
    SAFE_PROMPT,
    LOCAL_PREVIEW,
    REVERSIBLE_DRAFT,
    REFUSED_ACTION,
    MANUAL_HANDOFF,
    REVIEW_BLOCKER,
    NOT_READY,
)

_CONSEQUENTIAL_ALIASES = {
    'cancel': 'cancellation',
    'cancel_inspection': 'cancellation',
    'certify': 'certification',
    'certification_review': 'certification',
    'correction_upload': 'upload',
    'final_payment': 'payment',
    'inspection_scheduling': 'scheduling',
    'official_submit': 'submission',
    'schedule_inspection': 'scheduling',
    'submit_application': 'submission',
}
_PRIVATE_KEYS = {
    'auth_state',
    'card_number',
    'cookie',
    'credentials',
    'cvv',
    'email',
    'entered_value',
    'field_value',
    'file_path',
    'local_file_path',
    'local_path',
    'password',
    'payment_details',
    'phone',
    'private_value',
    'raw_value',
    'secret',
    'session_state',
    'ssn',
    'token',
    'user_input',
    'user_value',
    'value',
}
_STALE_STATUSES = {'expired', 'needs_refresh', 'stale', 'unknown', 'unknown_stale'}
_UNSUPPORTED_READY_LABELS = {
    'payment_ready',
    'ready_for_cancellation',
    'ready_for_certification',
    'ready_for_payment',
    'ready_for_scheduling',
    'ready_for_submission',
    'ready_for_upload',
    'ready_to_cancel',
    'ready_to_certify',
    'ready_to_pay',
    'ready_to_schedule',
    'ready_to_submit',
    'ready_to_upload',
    'submission_ready',
    'upload_ready',
}


@dataclass(frozen=True)
class ChecklistItem:
    '''One cited release-readiness mapping from a guardrail API response.'''

    section: str
    response_id: str
    prompt_or_action: str
    decision: str
    citation_ids: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class ReleaseChecklist:
    '''Validated readiness report derived only from deterministic fixtures.'''

    checklist_id: str
    fixture_name: str
    ready_for_agent_release: bool
    ready_for_submission: bool
    ready_for_payment: bool
    ready_for_upload: bool
    ready_for_scheduling: bool
    items: tuple[ChecklistItem, ...]
    blockers: tuple[str, ...]

    def items_for_section(self, section: str) -> tuple[ChecklistItem, ...]:
        return tuple(item for item in self.items if item.section == section)

    def readiness_flags(self) -> dict[str, bool]:
        return {
            'ready_for_agent_release': self.ready_for_agent_release,
            'ready_for_submission': self.ready_for_submission,
            'ready_for_payment': self.ready_for_payment,
            'ready_for_upload': self.ready_for_upload,
            'ready_for_scheduling': self.ready_for_scheduling,
        }


def build_release_checklist(fixture: Mapping[str, Any]) -> ReleaseChecklist:
    '''Build a release checklist from a committed guardrail response fixture.'''

    citations = _citation_ids(fixture.get('citations', ()))
    responses = _response_by_id(fixture.get('guardrail_api_responses', ()))
    _raise_if_problems(_privacy_problems(fixture))
    _raise_if_problems(_stale_guardrail_bundle_problems(fixture))
    _raise_if_problems(_unsupported_ready_label_problems(fixture))
    _raise_if_problems(_guardrail_response_problems(responses.values(), citations))

    raw_sections = fixture.get('release_checklist', {})
    if not isinstance(raw_sections, Mapping):
        raise ValueError('release_checklist must be an object')

    items: list[ChecklistItem] = []
    blockers: list[str] = []
    for section in REQUIRED_SECTIONS:
        raw_items = raw_sections.get(section)
        if not isinstance(raw_items, Sequence) or isinstance(raw_items, (str, bytes)):
            raise ValueError(f'release_checklist.{section} must be a list')
        if not raw_items:
            raise ValueError(f'release_checklist.{section} must include unresolved fixture-backed items')
        for raw_item in raw_items:
            item = _parse_item(section, raw_item, responses, citations)
            _raise_if_problems(_item_policy_problems(item))
            items.append(item)
            if section == REVIEW_BLOCKER:
                blockers.append(item.reason)

    not_ready_actions = {item.prompt_or_action for item in items if item.section == NOT_READY and item.decision == NOT_READY}
    for action in EXPLICIT_NOT_READY_ACTIONS:
        if action not in not_ready_actions:
            raise ValueError(f'missing explicit non-readiness for {action}')

    refused_actions = {item.prompt_or_action for item in items if item.section == REFUSED_ACTION}
    for action in ('captcha', 'mfa', 'account_creation', 'final_payment', 'official_submit'):
        if action not in refused_actions:
            raise ValueError(f'missing refused-action fixture for {action}')

    manual_handoffs = {item.prompt_or_action for item in items if item.section == MANUAL_HANDOFF}
    for action in ('login', 'certification_review', 'ambiguous_devhub_path'):
        if action not in manual_handoffs:
            raise ValueError(f'missing manual-handoff fixture for {action}')

    return ReleaseChecklist(
        checklist_id=str(fixture.get('checklist_id', 'ppd-agent-readiness-release-checklist')),
        fixture_name=str(fixture.get('fixture_name', 'unknown')),
        ready_for_agent_release=False,
        ready_for_submission=False,
        ready_for_payment=False,
        ready_for_upload=False,
        ready_for_scheduling=False,
        items=tuple(items),
        blockers=tuple(blockers),
    )


def assert_fixture_release_checklist(fixture: Mapping[str, Any]) -> ReleaseChecklist:
    '''Validate a fixture and return the checklist for tests and self-checks.'''

    checklist = build_release_checklist(fixture)
    if checklist.ready_for_agent_release:
        raise AssertionError('fixture must preserve unresolved blockers before release')
    for name, expected in {
        'ready_for_submission': False,
        'ready_for_payment': False,
        'ready_for_upload': False,
        'ready_for_scheduling': False,
    }.items():
        if checklist.readiness_flags()[name] is not expected:
            raise AssertionError(f'{name} must be {expected}')
    for section in REQUIRED_SECTIONS:
        if not checklist.items_for_section(section):
            raise AssertionError(f'missing checklist section: {section}')
    return checklist


def _citation_ids(raw_citations: Any) -> set[str]:
    if not isinstance(raw_citations, Sequence) or isinstance(raw_citations, (str, bytes)):
        raise ValueError('citations must be a list')
    citation_ids: set[str] = set()
    for citation in raw_citations:
        if not isinstance(citation, Mapping):
            raise ValueError('each citation must be an object')
        citation_id = citation.get('citation_id')
        if not isinstance(citation_id, str) or not citation_id:
            raise ValueError('each citation requires citation_id')
        citation_ids.add(citation_id)
    return citation_ids


def _response_by_id(raw_responses: Any) -> dict[str, Mapping[str, Any]]:
    if not isinstance(raw_responses, Sequence) or isinstance(raw_responses, (str, bytes)):
        raise ValueError('guardrail_api_responses must be a list')
    responses: dict[str, Mapping[str, Any]] = {}
    for response in raw_responses:
        if not isinstance(response, Mapping):
            raise ValueError('each guardrail response must be an object')
        response_id = response.get('response_id')
        if not isinstance(response_id, str) or not response_id:
            raise ValueError('each guardrail response requires response_id')
        responses[response_id] = response
    return responses


def _parse_item(section: str, raw_item: Any, responses: Mapping[str, Mapping[str, Any]], citation_ids: Iterable[str]) -> ChecklistItem:
    if not isinstance(raw_item, Mapping):
        raise ValueError(f'release_checklist.{section} entries must be objects')
    response_id = _required_string(raw_item, 'response_id')
    prompt_or_action = _required_string(raw_item, 'prompt_or_action')
    decision = _required_string(raw_item, 'decision')
    reason = _required_string(raw_item, 'reason')
    response = responses.get(response_id)
    if response is None:
        raise ValueError(f'{response_id} is not present in guardrail_api_responses')

    item_citations = _required_string_list(raw_item, 'citation_ids')
    missing = sorted(citation_id for citation_id in item_citations if citation_id not in set(citation_ids))
    if missing:
        raise ValueError(f'{response_id} cites unknown evidence: {', '.join(missing)}')

    response_citations = set(_required_string_list(response, 'citation_ids'))
    uncited_by_response = sorted(set(item_citations) - response_citations)
    if uncited_by_response:
        raise ValueError(f'{response_id} checklist item cites evidence not returned by response: ' + ', '.join(uncited_by_response))
    if response.get('decision') != decision:
        raise ValueError(f'{response_id} decision mismatch: checklist={decision} response={response.get('decision')}')
    if response.get('prompt_or_action') != prompt_or_action:
        raise ValueError(f'{response_id} prompt_or_action mismatch')

    return ChecklistItem(section, response_id, prompt_or_action, decision, tuple(item_citations), reason)


def _guardrail_response_problems(responses: Iterable[Mapping[str, Any]], citation_ids: set[str]) -> list[str]:
    problems: list[str] = []
    for response in responses:
        response_id = str(response.get('response_id', 'unknown'))
        response_citations = _string_list_or_empty(response.get('citation_ids'))
        if _has_answer_text(response) and not response_citations:
            problems.append(f'{response_id} answer lacks citation_ids')
        missing = sorted(citation_id for citation_id in response_citations if citation_id not in citation_ids)
        if missing:
            problems.append(f'{response_id} cites unknown evidence: {', '.join(missing)}')
        decision = str(response.get('decision', '')).lower()
        action = str(response.get('prompt_or_action', '')).lower()
        if _consequential_action_name(action) and decision not in BLOCKING_DECISIONS:
            problems.append(f'{response_id} consequential action {action} must be blocked or manual handoff')
    return problems


def _item_policy_problems(item: ChecklistItem) -> list[str]:
    if _consequential_action_name(item.prompt_or_action) and item.decision not in BLOCKING_DECISIONS:
        return [f'{item.response_id} consequential action {item.prompt_or_action} must be blocked or manual handoff']
    return []


def _privacy_problems(value: Any, path: str = '$', key_name: str = '') -> list[str]:
    problems: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_key = str(key)
            child_path = f'{path}.{child_key}'
            if child_key.lower() in _PRIVATE_KEYS and child not in (None, '', [], {}):
                problems.append(f'private value field is not allowed at {child_path}')
            problems.extend(_privacy_problems(child, child_path, child_key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            problems.extend(_privacy_problems(child, f'{path}[{index}]', key_name))
    elif isinstance(value, str) and key_name.lower() != 'source_url' and _looks_like_private_local_path(value):
        problems.append(f'local private path is not allowed at {path}')
    return problems


def _stale_guardrail_bundle_problems(fixture: Mapping[str, Any]) -> list[str]:
    bundles: list[Mapping[str, Any]] = []
    raw_one = fixture.get('guardrail_bundle')
    raw_many = fixture.get('guardrail_bundles')
    if isinstance(raw_one, Mapping):
        bundles.append(raw_one)
    if isinstance(raw_many, Sequence) and not isinstance(raw_many, (str, bytes)):
        bundles.extend(bundle for bundle in raw_many if isinstance(bundle, Mapping))

    problems: list[str] = []
    for index, bundle in enumerate(bundles):
        bundle_id = str(bundle.get('guardrail_bundle_id') or bundle.get('bundle_id') or f'index-{index}')
        for key in ('freshness_status', 'validation_status', 'status'):
            status = str(bundle.get(key, '')).lower()
            if status in _STALE_STATUSES:
                problems.append(f'guardrail bundle {bundle_id} is stale: {key}={status}')
        checked_at = bundle.get('last_verified_at') or bundle.get('compiled_at') or bundle.get('updated_at')
        if isinstance(checked_at, str) and _parse_datetime(checked_at) is None:
            problems.append(f'guardrail bundle {bundle_id} has invalid freshness timestamp')
    return problems


def _unsupported_ready_label_problems(value: Any, path: str = '$', key_name: str = '') -> list[str]:
    problems: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            problems.extend(_unsupported_ready_label_problems(child, f'{path}.{key}', str(key)))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            problems.extend(_unsupported_ready_label_problems(child, f'{path}[{index}]', key_name))
    elif isinstance(value, str) and value.strip().lower() in _UNSUPPORTED_READY_LABELS:
        problems.append(f'unsupported ready label {value.strip().lower()} at {path}')
    elif isinstance(value, bool) and value is True and key_name.lower() in _UNSUPPORTED_READY_LABELS:
        problems.append(f'unsupported ready flag {key_name} at {path}')
    return problems


def _has_answer_text(response: Mapping[str, Any]) -> bool:
    return any(isinstance(response.get(key), str) and response[key].strip() for key in ('answer', 'response', 'message'))


def _consequential_action_name(name: str) -> str | None:
    normalized = name.strip().lower().replace('-', '_')
    if normalized in CONSEQUENTIAL_ACTIONS:
        return normalized
    if normalized in _CONSEQUENTIAL_ALIASES:
        return _CONSEQUENTIAL_ALIASES[normalized]
    for action in CONSEQUENTIAL_ACTIONS:
        if action in normalized:
            return action
    return None


def _looks_like_private_local_path(value: str) -> bool:
    lowered = value.strip().lower()
    return lowered.startswith(('file://', '/home/', '/users/', '/var/folders/', 'c:/', 'c:\\'))


def _parse_datetime(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _raise_if_problems(problems: Sequence[str]) -> None:
    if problems:
        raise ValueError('; '.join(problems))


def _required_string(mapping: Mapping[str, Any], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f'{key} must be a non-empty string')
    return value


def _required_string_list(mapping: Mapping[str, Any], key: str) -> tuple[str, ...]:
    value = mapping.get(key)
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or not value:
        raise ValueError(f'{key} must be a non-empty list of strings')
    result: list[str] = []
    for entry in value:
        if not isinstance(entry, str) or not entry:
            raise ValueError(f'{key} must contain only non-empty strings')
        result.append(entry)
    return tuple(result)


def _string_list_or_empty(value: Any) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(entry for entry in value if isinstance(entry, str) and entry)
