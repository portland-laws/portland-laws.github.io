from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ppd.agent_readiness.devhub_read_only_agent_impact_replay_v3 import (
    PACKET_VERSION as IMPACT_REPLAY_PACKET_VERSION,
    assert_valid_devhub_read_only_agent_impact_replay_v3,
)

PACKET_TYPE = 'ppd.devhub_read_only_release_decision_packet.v3'
MODE = 'fixture-first-read-only-inactive'
DEFAULT_IMPACT_REPLAY_FIXTURE_REF = 'ppd/tests/fixtures/devhub_read_only_release_decision_packet_v3/agent_impact_replay_v3.json'
EXACT_OFFLINE_VALIDATION_COMMANDS = [
    ['python3', '-m', 'py_compile', 'ppd/agent_readiness/devhub_read_only_release_decision_packet_v3.py'],
    ['python3', '-m', 'py_compile', 'ppd/tests/test_devhub_read_only_release_decision_packet_v3.py'],
    ['python3', '-m', 'pytest', 'ppd/tests/test_devhub_read_only_release_decision_packet_v3.py'],
    ['python3', 'ppd/daemon/ppd_daemon.py', '--self-test'],
]

_REQUIRED_FALSE_ATTESTATIONS = (
    'devhub_opened',
    'login_performed',
    'auth_or_session_artifact_stored',
    'screenshot_trace_or_har_stored',
    'private_value_stored',
    'raw_devhub_output_stored',
    'active_surface_map_mutation',
    'form_fill_performed',
    'upload_or_submission_action_performed',
    'payment_or_scheduling_action_performed',
    'official_action_performed',
)
_MUTATION_KEY_TOKENS = (
    'active_surface_map_mutation',
    'active_release_state_mutation',
    'active_guardrail_mutation',
    'active_prompt_mutation',
    'active_process_mutation',
    'mutates_',
    'mutation_enabled',
)
_PRIVATE_KEY_TOKENS = (
    'auth',
    'browser',
    'cookie',
    'credential',
    'har',
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
_FORBIDDEN_TEXT_TOKENS = (
    'approval guaranteed',
    'browser state',
    'cookie',
    'credential',
    'filled form',
    'guaranteed issuance',
    'legal advice',
    'live devhub',
    'logged in',
    'paid fee',
    'password',
    'permit issued',
    'private value',
    'raw authenticated',
    'scheduled inspection',
    'screenshot',
    'session state',
    'storage state',
    'submitted application',
    'submitted payment',
    'trace file',
    'uploaded file',
)


@dataclass(frozen=True)
class DevHubReadOnlyReleaseDecisionPacketV3Result:
    valid: bool
    problems: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {'valid': self.valid, 'problems': list(self.problems)}


class DevHubReadOnlyReleaseDecisionPacketV3Error(ValueError):
    pass


def build_devhub_read_only_release_decision_packet_v3(
    agent_impact_replay_packet: Mapping[str, Any],
    *,
    packet_id: str = 'devhub-read-only-release-decision-packet-v3',
    impact_replay_fixture_ref: str = DEFAULT_IMPACT_REPLAY_FIXTURE_REF,
) -> dict[str, Any]:
    assert_valid_devhub_read_only_agent_impact_replay_v3(agent_impact_replay_packet)
    _raise_for_unsafe_content(agent_impact_replay_packet)

    stale_holds = _stale_evidence_holds(agent_impact_replay_packet)
    blocked_actions = _mapping_sequence(agent_impact_replay_packet.get('blocked_consequential_actions'))
    safe_actions = _mapping_sequence(agent_impact_replay_packet.get('affected_safe_read_only_actions'))
    packet = {
        'packet_type': PACKET_TYPE,
        'packet_id': packet_id,
        'mode': MODE,
        'fixture_only': True,
        'read_only': True,
        'inactive_release_decision': True,
        'consumes_only': {'agent_impact_replay_packet': IMPACT_REPLAY_PACKET_VERSION},
        'source_fixture_refs': [impact_replay_fixture_ref],
        'inactive_promotion_recommendation': {
            'status': 'hold',
            'recommendation': 'do_not_activate',
            'basis': 'Agent impact replay v3 fixture contains unresolved holds and consequential action blocks.',
            'safe_read_only_action_count': len(safe_actions),
            'blocked_consequential_action_count': len(blocked_actions),
            'stale_evidence_hold_count': len(stale_holds),
        },
        'reviewer_signoff_placeholders': _reviewer_signoff_placeholders(),
        'stale_evidence_holds': stale_holds,
        'activation_prerequisites': _activation_prerequisites(stale_holds, blocked_actions),
        'rollback_plan': _rollback_plan(agent_impact_replay_packet),
        'post_decision_smoke_checks': _post_decision_smoke_checks(),
        'offline_validation_commands': EXACT_OFFLINE_VALIDATION_COMMANDS,
        'attestations': {key: False for key in _REQUIRED_FALSE_ATTESTATIONS},
    }
    assert_valid_devhub_read_only_release_decision_packet_v3(packet)
    return packet


def validate_devhub_read_only_release_decision_packet_v3(packet: Mapping[str, Any]) -> DevHubReadOnlyReleaseDecisionPacketV3Result:
    problems: list[str] = []
    if packet.get('packet_type') != PACKET_TYPE:
        problems.append(f'packet_type must be {PACKET_TYPE}')
    if packet.get('mode') != MODE:
        problems.append(f'mode must be {MODE}')
    if packet.get('fixture_only') is not True:
        problems.append('fixture_only must be true')
    if packet.get('read_only') is not True:
        problems.append('read_only must be true')
    if packet.get('inactive_release_decision') is not True:
        problems.append('inactive_release_decision must be true')
    consumes = packet.get('consumes_only') if isinstance(packet.get('consumes_only'), Mapping) else {}
    if consumes.get('agent_impact_replay_packet') != IMPACT_REPLAY_PACKET_VERSION:
        problems.append('consumes_only.agent_impact_replay_packet must reference agent impact replay v3')
    _validate_source_fixture_refs(packet.get('source_fixture_refs'), problems)
    _validate_recommendation(packet.get('inactive_promotion_recommendation'), problems)
    _validate_rows(packet.get('reviewer_signoff_placeholders'), 'reviewer_signoff_placeholders', ('reviewer_role', 'status', 'required_before_activation'), problems)
    _validate_rows(packet.get('stale_evidence_holds'), 'stale_evidence_holds', ('hold_id', 'status', 'reason', 'source_evidence_ids'), problems)
    _validate_rows(packet.get('activation_prerequisites'), 'activation_prerequisites', ('prerequisite_id', 'status', 'description'), problems)
    _validate_rows(packet.get('rollback_plan'), 'rollback_plan', ('rollback_step_id', 'description', 'expected_result'), problems)
    _validate_rows(packet.get('post_decision_smoke_checks'), 'post_decision_smoke_checks', ('smoke_check_id', 'command', 'expected_result'), problems)
    if packet.get('offline_validation_commands') != EXACT_OFFLINE_VALIDATION_COMMANDS:
        problems.append('offline_validation_commands must match exact offline validation commands')
    _validate_attestations(packet.get('attestations'), problems)
    _scan_for_forbidden_payload(packet, problems)
    return DevHubReadOnlyReleaseDecisionPacketV3Result(not problems, tuple(problems))


def assert_valid_devhub_read_only_release_decision_packet_v3(packet: Mapping[str, Any]) -> None:
    result = validate_devhub_read_only_release_decision_packet_v3(packet)
    if not result.valid:
        raise DevHubReadOnlyReleaseDecisionPacketV3Error('; '.join(result.problems))


def _reviewer_signoff_placeholders() -> list[dict[str, str]]:
    return [
        {
            'reviewer_role': 'release_reviewer',
            'status': 'placeholder_pending',
            'required_before_activation': 'independent approval of inactive recommendation and hold list',
        },
        {
            'reviewer_role': 'ppd_policy_reviewer',
            'status': 'placeholder_pending',
            'required_before_activation': 'confirmation that consequential DevHub paths remain blocked',
        },
        {
            'reviewer_role': 'operator',
            'status': 'placeholder_pending',
            'required_before_activation': 'confirmation that exact offline validation commands passed',
        },
    ]


def _stale_evidence_holds(agent_impact_replay_packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    holds: list[dict[str, Any]] = []
    for index, prompt in enumerate(_mapping_sequence(agent_impact_replay_packet.get('missing_information_prompts'))):
        missing_key = _text(prompt.get('missing_information_key')) or 'unknown_missing_information'
        holds.append(
            {
                'hold_id': f'stale-evidence-hold-{index + 1}',
                'status': 'hold',
                'reason': f'Fixture replay still requires {missing_key} before activation can be considered.',
                'source_evidence_ids': [_text(prompt.get('request_id')) or 'agent-impact-replay-v3'],
            }
        )
    if not holds:
        holds.append(
            {
                'hold_id': 'stale-evidence-hold-1',
                'status': 'hold',
                'reason': 'No reviewer refresh evidence is present in the agent impact replay fixture.',
                'source_evidence_ids': ['agent-impact-replay-v3'],
            }
        )
    return holds


def _activation_prerequisites(stale_holds: Sequence[Mapping[str, Any]], blocked_actions: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            'prerequisite_id': 'activation-prerequisite-offline-validation',
            'status': 'pending',
            'description': 'Run every exact offline validation command and attach the result to a separate human review record.',
        },
        {
            'prerequisite_id': 'activation-prerequisite-stale-hold-reconciliation',
            'status': 'pending' if stale_holds else 'ready_for_review',
            'description': 'Resolve every stale evidence hold using a later reviewed fixture packet before activation.',
        },
        {
            'prerequisite_id': 'activation-prerequisite-consequential-action-review',
            'status': 'pending' if blocked_actions else 'ready_for_review',
            'description': 'Confirm that blocked consequential actions remain excluded from read-only release behavior.',
        },
        {
            'prerequisite_id': 'activation-prerequisite-reviewer-signoff',
            'status': 'pending',
            'description': 'Replace all reviewer placeholders with explicit human dispositions in a later packet.',
        },
    ]


def _rollback_plan(agent_impact_replay_packet: Mapping[str, Any]) -> list[dict[str, str]]:
    rows = []
    for index, note in enumerate(_mapping_sequence(agent_impact_replay_packet.get('rollback_notes'))):
        rows.append(
            {
                'rollback_step_id': f'rollback-step-{index + 1}',
                'description': _text(note.get('rollback_note')) or 'Discard inactive fixture replay output.',
                'expected_result': 'Active PP&D release artifacts remain unchanged.',
            }
        )
    if not rows:
        rows.append(
            {
                'rollback_step_id': 'rollback-step-1',
                'description': 'Discard this inactive decision packet.',
                'expected_result': 'Active PP&D release artifacts remain unchanged.',
            }
        )
    return rows


def _post_decision_smoke_checks() -> list[dict[str, Any]]:
    return [
        {
            'smoke_check_id': 'smoke-check-py-compile-module',
            'command': EXACT_OFFLINE_VALIDATION_COMMANDS[0],
            'expected_result': 'release decision packet module compiles',
        },
        {
            'smoke_check_id': 'smoke-check-py-compile-test',
            'command': EXACT_OFFLINE_VALIDATION_COMMANDS[1],
            'expected_result': 'release decision packet tests compile',
        },
        {
            'smoke_check_id': 'smoke-check-focused-pytest',
            'command': EXACT_OFFLINE_VALIDATION_COMMANDS[2],
            'expected_result': 'focused fixture-first packet tests pass',
        },
        {
            'smoke_check_id': 'smoke-check-daemon-self-test',
            'command': EXACT_OFFLINE_VALIDATION_COMMANDS[3],
            'expected_result': 'PP&D daemon self-test passes',
        },
    ]


def _validate_source_fixture_refs(value: Any, problems: list[str]) -> None:
    refs = _string_sequence(value)
    if refs != [DEFAULT_IMPACT_REPLAY_FIXTURE_REF]:
        problems.append('source_fixture_refs must contain only the committed agent impact replay v3 fixture')


def _validate_recommendation(value: Any, problems: list[str]) -> None:
    if not isinstance(value, Mapping):
        problems.append('inactive_promotion_recommendation must be an object')
        return
    if value.get('status') != 'hold':
        problems.append('inactive_promotion_recommendation.status must be hold')
    if value.get('recommendation') != 'do_not_activate':
        problems.append('inactive_promotion_recommendation.recommendation must be do_not_activate')
    if not _text(value.get('basis')):
        problems.append('inactive_promotion_recommendation.basis is required')


def _validate_rows(value: Any, field: str, required_keys: Sequence[str], problems: list[str]) -> None:
    rows = _mapping_sequence(value)
    if not rows:
        problems.append(f'{field} must be a non-empty list')
        return
    for index, row in enumerate(rows):
        for key in required_keys:
            child = row.get(key)
            if isinstance(child, list):
                if not _string_sequence(child):
                    problems.append(f'{field}[{index}].{key} is required')
            elif not _text(child) and not isinstance(child, list):
                problems.append(f'{field}[{index}].{key} is required')


def _validate_attestations(value: Any, problems: list[str]) -> None:
    attestations = value if isinstance(value, Mapping) else {}
    if not attestations:
        problems.append('attestations must be present')
    for key in _REQUIRED_FALSE_ATTESTATIONS:
        if attestations.get(key) is not False:
            problems.append(f'attestations.{key} must be false')


def _raise_for_unsafe_content(value: Any) -> None:
    problems: list[str] = []
    _scan_for_forbidden_payload(value, problems)
    if problems:
        raise DevHubReadOnlyReleaseDecisionPacketV3Error('; '.join(problems))


def _scan_for_forbidden_payload(value: Any, problems: list[str], path: str = 'packet', key: str = 'packet') -> None:
    normalized_key = key.lower().replace('-', '_')
    if any(token in normalized_key for token in _MUTATION_KEY_TOKENS) and value is not False:
        problems.append(f'{path} must not include active mutation flags')
    if any(token in normalized_key for token in _PRIVATE_KEY_TOKENS) and _truthy(value):
        problems.append(f'{path} must not include private, credential, browser, trace, HAR, or state artifacts')
    if isinstance(value, str):
        normalized_text = ' '.join(value.lower().replace('_', ' ').replace('-', ' ').split())
        if any(token in normalized_text for token in _FORBIDDEN_TEXT_TOKENS):
            problems.append(f'{path} must not include unsafe live, private, consequential, or guarantee claims')
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
