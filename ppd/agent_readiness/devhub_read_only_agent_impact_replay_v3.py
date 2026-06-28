from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

PACKET_VERSION = 'devhub_read_only_agent_impact_replay_v3'
SURFACE_PACKET_VERSION = 'devhub_read_only_surface_map_delta_reviewer_packet_v3'
REQUEST_PACKET_VERSION = 'synthetic_devhub_agent_requests_v3'

EXACT_OFFLINE_VALIDATION_COMMANDS = [
    ['python3', '-m', 'py_compile', 'ppd/agent_readiness/devhub_read_only_agent_impact_replay_v3.py'],
    ['python3', '-m', 'py_compile', 'ppd/tests/test_devhub_read_only_agent_impact_replay_v3.py'],
    ['python3', '-m', 'pytest', 'ppd/tests/test_devhub_read_only_agent_impact_replay_v3.py'],
    ['python3', 'ppd/daemon/ppd_daemon.py', '--self-test'],
]

_REQUIRED_FALSE_ATTESTATIONS = (
    'active_surface_map_mutation',
    'devhub_opened',
    'auth_or_session_artifact_stored',
    'screenshot_trace_or_har_stored',
    'private_value_stored',
    'raw_devhub_output_stored',
    'form_fill_performed',
    'upload_or_submission_action_performed',
    'payment_or_scheduling_action_performed',
    'official_action_performed',
)

_SAFE_CLASSES = frozenset({'safe_read_only', 'read_only', 'status_review', 'notice_review'})
_BLOCKED_CLASSES = frozenset({'consequential_official', 'official', 'upload', 'submission', 'payment', 'scheduling', 'certification'})
_MUTATION_KEY_TOKENS = (
    'active_contract_mutation',
    'active_guardrail_mutation',
    'active_process_mutation',
    'active_prompt_mutation',
    'active_release_state_mutation',
    'active_requirement_mutation',
    'active_source_mutation',
    'active_surface_map_mutation',
    'mutation_enabled',
    'mutates_',
)
_FORBIDDEN_KEY_TOKENS = (
    'auth',
    'browser',
    'captcha',
    'cookie',
    'credential',
    'har',
    'local_path',
    'mfa',
    'password',
    'private',
    'raw_devhub',
    'screenshot',
    'secret',
    'session',
    'storage_state',
    'token',
    'trace',
)
_PRIVATE_TEXT_TOKENS = (
    'auth state',
    'browser artifact',
    'browser state',
    'cookie',
    'credential',
    'har file',
    'local private path',
    'password',
    'private artifact',
    'private value',
    'raw authenticated',
    'screenshot',
    'session artifact',
    'session state',
    'storage state',
    'trace file',
)
_LIVE_DEVHUB_TEXT_TOKENS = (
    'devhub was opened',
    'executed in devhub',
    'live devhub',
    'logged in',
    'opened devhub',
    'ran against devhub',
    'used authenticated devhub',
)
_SURFACE_MUTATION_TEXT_TOKENS = (
    'active surface map mutation',
    'active surface-map mutation',
    'mutated surface map',
    'mutated surface-map',
    'surface map updated',
    'surface-map updated',
)
_FORM_OR_UPLOAD_TEXT_TOKENS = (
    'attached file',
    'filled devhub form',
    'filled form',
    'form fill performed',
    'uploaded correction',
    'uploaded file',
    'upload performed',
)
_OFFICIAL_ACTION_TEXT_TOKENS = (
    'certification submitted',
    'official action completed',
    'paid fee',
    'permit submitted',
    'scheduled inspection',
    'submitted application',
    'submitted payment',
    'submitted permit',
)
_GUARANTEE_TEXT_TOKENS = (
    'approval guaranteed',
    'guarantee approval',
    'guaranteed issuance',
    'guaranteed permit',
    'legal advice',
    'legally compliant',
    'permit approved',
    'permit guaranteed',
    'permit issued',
    'will be approved',
    'will be issued',
)


@dataclass(frozen=True)
class DevHubReadOnlyAgentImpactReplayV3Result:
    valid: bool
    problems: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {'valid': self.valid, 'problems': list(self.problems)}


class DevHubReadOnlyAgentImpactReplayV3Error(ValueError):
    pass


def build_devhub_read_only_agent_impact_replay_v3(surface_packet: Mapping[str, Any], request_packet: Mapping[str, Any]) -> dict[str, Any]:
    _assert_fixture_inputs(surface_packet, request_packet)
    actions_by_surface = _actions_by_surface(surface_packet)
    safe_actions: list[dict[str, Any]] = []
    blocked_actions: list[dict[str, Any]] = []
    prompts: list[dict[str, Any]] = []
    route_checks: list[dict[str, Any]] = []
    classification_checks: list[dict[str, Any]] = []
    exact_confirmation_checks: list[dict[str, Any]] = []

    for request in _mapping_sequence(request_packet.get('requests')):
        request_id = _required_text(request, 'request_id')
        surface_id = _required_text(request, 'surface_id')
        requested = set(_string_sequence(request.get('requested_action_ids')))
        known = set(_string_sequence(request.get('known_information')))
        for action in actions_by_surface.get(surface_id, []):
            action_id = _required_text(action, 'action_id')
            if requested and action_id not in requested:
                continue
            base = {
                'request_id': request_id,
                'surface_id': surface_id,
                'surface_delta_id': _required_text(action, 'surface_delta_id'),
                'action_id': action_id,
                'action_label': _required_text(action, 'action_label'),
            }
            classification = _required_text(action, 'classification')
            classification_checks.append({
                **base,
                'classification': classification,
                'allowed_for_read_only_replay': classification in _SAFE_CLASSES,
                'blocked_as_consequential': classification in _BLOCKED_CLASSES,
            })
            if classification in _SAFE_CLASSES:
                safe_actions.append({
                    **base,
                    'impact': 'allowed_read_only_replay',
                    'summary': 'Offline replay may summarize this read-only DevHub action path without opening DevHub.',
                    'devhub_opened': False,
                })
                route_checks.append({
                    **base,
                    'route_lookup': 'fixture_surface_id_to_inactive_delta_only',
                    'read_only_route_confirmed': True,
                    'devhub_opened': False,
                })
            if classification in _BLOCKED_CLASSES:
                blocked_actions.append({
                    **base,
                    'impact': 'blocked_consequential_action',
                    'summary': 'Replay blocks this consequential action and requires manual handoff before any attended step.',
                    'requires_manual_handoff': True,
                })
                exact_confirmation_checks.append({
                    **base,
                    'requires_exact_confirmation': True,
                    'exact_confirmation_performed': False,
                    'gate_result': 'blocked_until_attended_exact_confirmation',
                })
            for fact in _string_sequence(action.get('required_missing_information')):
                if fact not in known:
                    prompts.append({
                        **base,
                        'missing_information_key': fact,
                        'prompt': f'Ask the user for {fact} before relying on this DevHub action path.',
                    })

    surface_placeholders = []
    handoff_checks = []
    reviewer_holds = []
    rollback_notes = []
    rollback_readiness = []
    for delta in _mapping_sequence(surface_packet.get('inactive_surface_map_deltas')):
        delta_id = _required_text(delta, 'delta_id')
        surface_id = _required_text(delta, 'surface_id')
        reminder = _text(delta.get('manual_handoff_reminder')) or 'Manual handoff remains required before any attended DevHub step.'
        rollback_note = _text(delta.get('rollback_note')) or 'Discard this replay and leave active surface maps unchanged.'
        surface_placeholders.append({
            'surface_delta_id': delta_id,
            'surface_id': surface_id,
            'placeholder_kind': 'synthetic_inactive_surface_map_delta',
            'active_surface_map_mutation': False,
        })
        handoff_checks.append({
            'surface_delta_id': delta_id,
            'surface_id': surface_id,
            'manual_handoff_required': True,
            'manual_handoff_performed': False,
            'reminder': reminder,
        })
        reviewer_holds.append({
            'surface_delta_id': delta_id,
            'surface_id': surface_id,
            'hold_status': 'held_for_reviewer_disposition',
            'release_activation_allowed': False,
        })
        rollback_notes.append({
            'surface_delta_id': delta_id,
            'surface_id': surface_id,
            'rollback_note': rollback_note,
        })
        rollback_readiness.append({
            'surface_delta_id': delta_id,
            'surface_id': surface_id,
            'ready_to_discard_replay': True,
            'active_surface_map_mutation': False,
            'rollback_note': rollback_note,
        })

    packet = {
        'packet_version': PACKET_VERSION,
        'fixture_only': True,
        'read_only': True,
        'post_decision_smoke_replay': True,
        'consumes': {'surface_delta_reviewer_packet': SURFACE_PACKET_VERSION, 'synthetic_agent_requests': REQUEST_PACKET_VERSION},
        'release_decision_references': [
            {'decision_packet': 'devhub_read_only_release_decision_packet_v3', 'decision': 'reviewer_hold_required'},
        ],
        'source_fixture_refs': _string_sequence(surface_packet.get('source_fixture_refs')) + _string_sequence(request_packet.get('source_fixture_refs')),
        'synthetic_surface_map_placeholders': surface_placeholders,
        'read_only_route_lookup_checks': route_checks,
        'action_classification_checks': classification_checks,
        'affected_safe_read_only_actions': safe_actions,
        'blocked_consequential_actions': blocked_actions,
        'missing_information_prompts': prompts,
        'exact_confirmation_gate_checks': exact_confirmation_checks,
        'manual_handoff_gate_checks': handoff_checks,
        'manual_handoff_reminders': handoff_checks,
        'reviewer_holds': reviewer_holds,
        'rollback_notes': rollback_notes,
        'rollback_readiness': rollback_readiness,
        'attestations': {key: False for key in _REQUIRED_FALSE_ATTESTATIONS},
        'validation_commands': EXACT_OFFLINE_VALIDATION_COMMANDS,
    }
    assert_valid_devhub_read_only_agent_impact_replay_v3(packet)
    return packet


def validate_devhub_read_only_agent_impact_replay_v3(packet: Mapping[str, Any]) -> DevHubReadOnlyAgentImpactReplayV3Result:
    problems: list[str] = []
    if not isinstance(packet, Mapping):
        return DevHubReadOnlyAgentImpactReplayV3Result(False, ('packet must be an object',))
    if packet.get('packet_version') != PACKET_VERSION:
        problems.append(f'packet_version must be {PACKET_VERSION}')
    if packet.get('fixture_only') is not True:
        problems.append('fixture_only must be true')
    if packet.get('read_only') is not True:
        problems.append('read_only must be true')
    if packet.get('post_decision_smoke_replay') is not True:
        problems.append('post_decision_smoke_replay must be true')
    consumes = packet.get('consumes') if isinstance(packet.get('consumes'), Mapping) else {}
    if consumes.get('surface_delta_reviewer_packet') != SURFACE_PACKET_VERSION:
        problems.append('consumes.surface_delta_reviewer_packet must reference inactive surface-map delta reviewer packet v3')
    if consumes.get('synthetic_agent_requests') != REQUEST_PACKET_VERSION:
        problems.append('consumes.synthetic_agent_requests must reference synthetic agent requests v3')
    _validate_release_decision_references(packet.get('release_decision_references'), problems)
    _validate_source_fixture_refs(packet.get('source_fixture_refs'), problems)
    _validate_surface_placeholders(packet.get('synthetic_surface_map_placeholders'), problems)
    _validate_route_checks(packet.get('read_only_route_lookup_checks'), problems)
    _validate_classification_checks(packet.get('action_classification_checks'), problems)
    _validate_action_summaries(packet.get('affected_safe_read_only_actions'), 'affected_safe_read_only_actions', problems)
    _validate_action_summaries(packet.get('blocked_consequential_actions'), 'blocked_consequential_actions', problems)
    _validate_missing_information_prompts(packet.get('missing_information_prompts'), problems)
    _validate_exact_confirmation_checks(packet.get('exact_confirmation_gate_checks'), problems)
    _validate_manual_handoff_checks(packet.get('manual_handoff_gate_checks'), problems)
    _validate_reviewer_holds(packet.get('reviewer_holds'), problems)
    _validate_rollback_notes(packet.get('rollback_notes'), problems)
    _validate_rollback_readiness(packet.get('rollback_readiness'), problems)
    _validate_attestations(packet.get('attestations'), problems)
    if packet.get('validation_commands') != EXACT_OFFLINE_VALIDATION_COMMANDS:
        problems.append('validation_commands must match exact offline replay validation commands')
    _scan_for_forbidden_payload(packet, problems)
    return DevHubReadOnlyAgentImpactReplayV3Result(not problems, tuple(problems))


def assert_valid_devhub_read_only_agent_impact_replay_v3(packet: Mapping[str, Any]) -> None:
    result = validate_devhub_read_only_agent_impact_replay_v3(packet)
    if not result.valid:
        raise DevHubReadOnlyAgentImpactReplayV3Error('; '.join(result.problems))


def _assert_fixture_inputs(surface_packet: Mapping[str, Any], request_packet: Mapping[str, Any]) -> None:
    problems: list[str] = []
    if surface_packet.get('packet_version') != SURFACE_PACKET_VERSION or surface_packet.get('fixture_only') is not True or surface_packet.get('inactive_only') is not True:
        problems.append('surface input must be a fixture-only inactive surface-map delta reviewer packet v3')
    if request_packet.get('packet_version') != REQUEST_PACKET_VERSION or request_packet.get('fixture_only') is not True or request_packet.get('synthetic_only') is not True:
        problems.append('request input must be a fixture-only synthetic agent request packet v3')
    _validate_source_fixture_refs(surface_packet.get('source_fixture_refs'), problems, require_surface=True, require_request=False)
    _validate_source_fixture_refs(request_packet.get('source_fixture_refs'), problems, require_surface=False, require_request=True)
    for source in (surface_packet, request_packet):
        _scan_for_forbidden_payload(source, problems)
    if problems:
        raise DevHubReadOnlyAgentImpactReplayV3Error('; '.join(problems))


def _actions_by_surface(surface_packet: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for delta in _mapping_sequence(surface_packet.get('inactive_surface_map_deltas')):
        delta_id = _required_text(delta, 'delta_id')
        surface_id = _required_text(delta, 'surface_id')
        for action in _mapping_sequence(delta.get('actions')):
            row = dict(action)
            row['surface_delta_id'] = delta_id
            result.setdefault(surface_id, []).append(row)
    return result


def _validate_release_decision_references(value: Any, problems: list[str]) -> None:
    rows = _mapping_sequence(value)
    if not rows:
        problems.append('release_decision_references must be a non-empty list')
        return
    for index, row in enumerate(rows):
        prefix = f'release_decision_references[{index}]'
        if not _text(row.get('decision_packet')):
            problems.append(f'{prefix}.decision_packet is required')
        if not _text(row.get('decision')):
            problems.append(f'{prefix}.decision is required')


def _validate_source_fixture_refs(value: Any, problems: list[str], require_surface: bool = True, require_request: bool = True) -> None:
    refs = _string_sequence(value)
    if not refs:
        problems.append('source_fixture_refs must include committed reviewer and synthetic request fixture references')
        return
    joined = ' '.join(refs)
    if require_surface and 'inactive_surface_map_delta_reviewer_packet_v3.json' not in joined:
        problems.append('source_fixture_refs must include inactive surface-map delta reviewer packet fixture')
    if require_request and 'synthetic_agent_requests_v3.json' not in joined:
        problems.append('source_fixture_refs must include synthetic agent request fixture')


def _validate_surface_placeholders(value: Any, problems: list[str]) -> None:
    rows = _mapping_sequence(value)
    if not rows:
        problems.append('synthetic_surface_map_placeholders must be a non-empty list')
        return
    for index, row in enumerate(rows):
        prefix = f'synthetic_surface_map_placeholders[{index}]'
        for key in ('surface_delta_id', 'surface_id', 'placeholder_kind'):
            if not _text(row.get(key)):
                problems.append(f'{prefix}.{key} is required')
        if row.get('active_surface_map_mutation') is not False:
            problems.append(f'{prefix}.active_surface_map_mutation must be false')


def _validate_route_checks(value: Any, problems: list[str]) -> None:
    rows = _mapping_sequence(value)
    if not rows:
        problems.append('read_only_route_lookup_checks must be a non-empty list')
        return
    for index, row in enumerate(rows):
        prefix = f'read_only_route_lookup_checks[{index}]'
        for key in ('request_id', 'surface_id', 'surface_delta_id', 'action_id', 'route_lookup'):
            if not _text(row.get(key)):
                problems.append(f'{prefix}.{key} is required')
        if row.get('read_only_route_confirmed') is not True:
            problems.append(f'{prefix}.read_only_route_confirmed must be true')
        if row.get('devhub_opened') is not False:
            problems.append(f'{prefix}.devhub_opened must be false')


def _validate_classification_checks(value: Any, problems: list[str]) -> None:
    rows = _mapping_sequence(value)
    if not rows:
        problems.append('action_classification_checks must be a non-empty list')
        return
    for index, row in enumerate(rows):
        prefix = f'action_classification_checks[{index}]'
        classification = _text(row.get('classification'))
        for key in ('request_id', 'surface_id', 'surface_delta_id', 'action_id', 'action_label'):
            if not _text(row.get(key)):
                problems.append(f'{prefix}.{key} is required')
        if not classification:
            problems.append(f'{prefix}.classification is required')
        if classification in _SAFE_CLASSES and row.get('allowed_for_read_only_replay') is not True:
            problems.append(f'{prefix}.allowed_for_read_only_replay must be true for read-only actions')
        if classification in _BLOCKED_CLASSES and row.get('blocked_as_consequential') is not True:
            problems.append(f'{prefix}.blocked_as_consequential must be true for consequential actions')
        if classification not in _SAFE_CLASSES and classification not in _BLOCKED_CLASSES:
            problems.append(f'{prefix}.classification must be recognized as read-only or blocked consequential')


def _validate_action_summaries(value: Any, field: str, problems: list[str]) -> None:
    rows = _mapping_sequence(value)
    if not rows:
        problems.append(f'{field} must be a non-empty list')
        return
    for index, row in enumerate(rows):
        prefix = f'{field}[{index}]'
        for key in ('request_id', 'surface_id', 'surface_delta_id', 'action_id', 'action_label', 'impact', 'summary'):
            if not _text(row.get(key)):
                problems.append(f'{prefix}.{key} is required')


def _validate_missing_information_prompts(value: Any, problems: list[str]) -> None:
    rows = _mapping_sequence(value)
    if not rows:
        problems.append('missing_information_prompts must be a non-empty list')
        return
    for index, row in enumerate(rows):
        prefix = f'missing_information_prompts[{index}]'
        for key in ('request_id', 'surface_id', 'surface_delta_id', 'action_id', 'missing_information_key', 'prompt'):
            if not _text(row.get(key)):
                problems.append(f'{prefix}.{key} is required')


def _validate_exact_confirmation_checks(value: Any, problems: list[str]) -> None:
    rows = _mapping_sequence(value)
    if not rows:
        problems.append('exact_confirmation_gate_checks must be a non-empty list')
        return
    for index, row in enumerate(rows):
        prefix = f'exact_confirmation_gate_checks[{index}]'
        for key in ('request_id', 'surface_id', 'surface_delta_id', 'action_id', 'gate_result'):
            if not _text(row.get(key)):
                problems.append(f'{prefix}.{key} is required')
        if row.get('requires_exact_confirmation') is not True:
            problems.append(f'{prefix}.requires_exact_confirmation must be true')
        if row.get('exact_confirmation_performed') is not False:
            problems.append(f'{prefix}.exact_confirmation_performed must be false')


def _validate_manual_handoff_checks(value: Any, problems: list[str]) -> None:
    rows = _mapping_sequence(value)
    if not rows:
        problems.append('manual_handoff_gate_checks must be a non-empty list')
        return
    for index, row in enumerate(rows):
        prefix = f'manual_handoff_gate_checks[{index}]'
        for key in ('surface_delta_id', 'surface_id', 'reminder'):
            if not _text(row.get(key)):
                problems.append(f'{prefix}.{key} is required')
        if row.get('manual_handoff_required') is not True:
            problems.append(f'{prefix}.manual_handoff_required must be true')
        if row.get('manual_handoff_performed') is not False:
            problems.append(f'{prefix}.manual_handoff_performed must be false')


def _validate_reviewer_holds(value: Any, problems: list[str]) -> None:
    rows = _mapping_sequence(value)
    if not rows:
        problems.append('reviewer_holds must be a non-empty list')
        return
    for index, row in enumerate(rows):
        prefix = f'reviewer_holds[{index}]'
        for key in ('surface_delta_id', 'surface_id', 'hold_status'):
            if not _text(row.get(key)):
                problems.append(f'{prefix}.{key} is required')
        if row.get('release_activation_allowed') is not False:
            problems.append(f'{prefix}.release_activation_allowed must be false')


def _validate_rollback_notes(value: Any, problems: list[str]) -> None:
    rows = _mapping_sequence(value)
    if not rows:
        problems.append('rollback_notes must be a non-empty list')
        return
    for index, row in enumerate(rows):
        prefix = f'rollback_notes[{index}]'
        for key in ('surface_delta_id', 'surface_id', 'rollback_note'):
            if not _text(row.get(key)):
                problems.append(f'{prefix}.{key} is required')


def _validate_rollback_readiness(value: Any, problems: list[str]) -> None:
    rows = _mapping_sequence(value)
    if not rows:
        problems.append('rollback_readiness must be a non-empty list')
        return
    for index, row in enumerate(rows):
        prefix = f'rollback_readiness[{index}]'
        for key in ('surface_delta_id', 'surface_id', 'rollback_note'):
            if not _text(row.get(key)):
                problems.append(f'{prefix}.{key} is required')
        if row.get('ready_to_discard_replay') is not True:
            problems.append(f'{prefix}.ready_to_discard_replay must be true')
        if row.get('active_surface_map_mutation') is not False:
            problems.append(f'{prefix}.active_surface_map_mutation must be false')


def _validate_attestations(value: Any, problems: list[str]) -> None:
    attestations = value if isinstance(value, Mapping) else {}
    if not attestations:
        problems.append('attestations must be present')
    for key in _REQUIRED_FALSE_ATTESTATIONS:
        if attestations.get(key) is not False:
            problems.append(f'attestations.{key} must be false')


def _scan_for_forbidden_payload(value: Any, problems: list[str], path: str = 'packet', key: str = 'packet') -> None:
    normalized_key = key.lower().replace('-', '_')
    if any(token in normalized_key for token in _MUTATION_KEY_TOKENS) and value is not False:
        problems.append(f'{path} must not include active mutation flags')
    if any(token in normalized_key for token in _FORBIDDEN_KEY_TOKENS) and _truthy(value):
        problems.append(f'{path} must not include auth, session, browser, screenshot, trace, HAR, private, or credential artifacts')
    if isinstance(value, str):
        text = ' '.join(value.lower().replace('_', ' ').replace('-', ' ').split())
        if any(token in text for token in _PRIVATE_TEXT_TOKENS):
            problems.append(f'{path} must not reference private/session/auth artifacts, screenshots, traces, or HAR files')
        if any(token in text for token in _LIVE_DEVHUB_TEXT_TOKENS):
            problems.append(f'{path} must not reference live DevHub interaction claims')
        if any(token in text for token in _SURFACE_MUTATION_TEXT_TOKENS):
            problems.append(f'{path} must not include active surface-map mutation claims')
        if any(token in text for token in _FORM_OR_UPLOAD_TEXT_TOKENS):
            problems.append(f'{path} must not include form-fill or upload claims')
        if any(token in text for token in _OFFICIAL_ACTION_TEXT_TOKENS):
            problems.append(f'{path} must not include official-action completion claims')
        if any(token in text for token in _GUARANTEE_TEXT_TOKENS):
            problems.append(f'{path} must not include legal or permitting guarantees')
    if isinstance(value, Mapping):
        for child_key, child in value.items():
            _scan_for_forbidden_payload(child, problems, f'{path}.{child_key}', str(child_key))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _scan_for_forbidden_payload(child, problems, f'{path}[{index}]', key)


def _mapping_sequence(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _string_sequence(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _required_text(row: Mapping[str, Any], key: str) -> str:
    value = _text(row.get(key))
    if not value:
        raise DevHubReadOnlyAgentImpactReplayV3Error(f'{key} is required')
    return value


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) and value.strip() else ''


def _truthy(value: Any) -> bool:
    if value in (None, False, ''):
        return False
    if isinstance(value, Mapping) and not value:
        return False
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)) and not value:
        return False
    return True
