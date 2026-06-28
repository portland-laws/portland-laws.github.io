from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

PACKET_VERSION = 'devhub_fixture_first_read_only_observation_seed_packet_v1'

_ALLOWED_INPUT_SOURCE_TYPES = frozenset({'synthetic_post_decision_smoke_replay'})
_ALLOWED_GUIDANCE_SOURCE_TYPES = frozenset({'official_devhub_guidance_placeholder'})
_ALLOWED_TARGET_CLASSIFICATIONS = frozenset({'safe_read_only', 'read_only_observation'})
_ALLOWED_REVIEWER_ROUTES = frozenset({'devhub_read_only_reviewer', 'ppd_guardrail_reviewer', 'manual_handoff_reviewer'})

_REQUIRED_SEQUENCE_KEYS = (
    'input_rows',
    'official_guidance_placeholders',
    'observation_targets',
    'authorization_prerequisites',
    'redaction_expectations',
    'fixture_only_capture_schema_updates',
    'unsupported_manual_handoff_reminders',
    'rollback_notes',
    'reviewer_routing',
    'validation_commands',
)

_ARTIFACT_POLICY_KEYS = (
    'opens_devhub',
    'logs_in',
    'performs_form_fills',
    'performs_official_actions',
    'stores_auth_artifacts',
    'stores_session_artifacts',
    'stores_screenshots',
    'stores_traces',
    'stores_har_files',
    'stores_private_values',
    'stores_raw_crawl_output',
    'downloads_documents',
)

_ALLOWED_VALIDATION_COMMANDS = (
    ('python3', '-m', 'py_compile', 'ppd/agent_readiness/devhub_fixture_first_read_only_observation_seed_packet_v1.py', 'ppd/tests/test_devhub_fixture_first_read_only_observation_seed_packet_v1.py'),
    ('python3', '-m', 'unittest', 'ppd.tests.test_devhub_fixture_first_read_only_observation_seed_packet_v1'),
    ('python3', 'ppd/daemon/ppd_daemon.py', '--self-test'),
)

_LIVE_ACCESS_TERMS = (
    'opened devhub',
    'logged in',
    'live devhub',
    'authenticated run',
    'browser session',
    'storage_state',
    'cookie captured',
    'screenshot saved',
    'trace saved',
    'har saved',
    'form filled',
    'submitted',
    'uploaded',
    'paid fee',
    'scheduled inspection',
)

_POLICY_CONTEXT_PARTS = (
    '.artifact_policy',
    '.prohibited_live_actions',
    '.unsupported_manual_handoff_reminders',
    '.rollback_notes',
    '.redaction_expectations',
)


@dataclass(frozen=True)
class SeedPacketIssue:
    code: str
    path: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {'code': self.code, 'path': self.path, 'message': self.message}


def validate_devhub_fixture_first_read_only_observation_seed_packet_v1(packet: Mapping[str, Any]) -> list[SeedPacketIssue]:
    issues: list[SeedPacketIssue] = []
    if not isinstance(packet, Mapping):
        return [SeedPacketIssue('invalid_packet', '$', 'packet must be an object')]

    if packet.get('packet_version') != PACKET_VERSION:
        _add(issues, 'invalid_packet_version', 'packet_version', f'packet_version must be {PACKET_VERSION}')

    for key in _REQUIRED_SEQUENCE_KEYS:
        _require_non_empty_sequence(packet, key, issues)

    input_row_ids = _validate_input_rows(packet.get('input_rows'), issues)
    placeholder_ids = _validate_guidance_placeholders(packet.get('official_guidance_placeholders'), issues)
    prerequisite_ids = _collect_ids(packet.get('authorization_prerequisites'), 'authorization_prerequisites', 'prerequisite_id', issues)
    redaction_ids = _collect_ids(packet.get('redaction_expectations'), 'redaction_expectations', 'redaction_id', issues)
    schema_update_ids = _validate_schema_updates(packet.get('fixture_only_capture_schema_updates'), issues)
    reviewer_route_ids = _validate_reviewer_routing(packet.get('reviewer_routing'), issues)
    _validate_targets(packet.get('observation_targets'), input_row_ids, placeholder_ids, prerequisite_ids, redaction_ids, schema_update_ids, reviewer_route_ids, issues)
    _validate_artifact_policy(packet.get('artifact_policy'), issues)
    _validate_validation_commands(packet.get('validation_commands'), issues)
    _scan_for_live_access_claims(packet, issues)
    return _dedupe(issues)


def validate_packet(packet: Mapping[str, Any]) -> list[SeedPacketIssue]:
    return validate_devhub_fixture_first_read_only_observation_seed_packet_v1(packet)


def assert_valid_devhub_fixture_first_read_only_observation_seed_packet_v1(packet: Mapping[str, Any]) -> None:
    issues = validate_devhub_fixture_first_read_only_observation_seed_packet_v1(packet)
    if issues:
        messages = '; '.join(f'{issue.path}: {issue.message}' for issue in issues)
        raise AssertionError('invalid DevHub fixture-first read-only observation seed packet v1: ' + messages)


def _validate_input_rows(value: Any, issues: list[SeedPacketIssue]) -> set[str]:
    row_ids = _collect_ids(value, 'input_rows', 'row_id', issues)
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return row_ids
    for index, row in enumerate(value):
        path = f'input_rows[{index}]'
        if not isinstance(row, Mapping):
            continue
        if row.get('source_type') not in _ALLOWED_INPUT_SOURCE_TYPES:
            _add(issues, 'invalid_input_source', f'{path}.source_type', 'input row must come from synthetic post-decision smoke replay data')
        if row.get('contains_live_devhub_data') is not False:
            _add(issues, 'live_data_not_allowed', f'{path}.contains_live_devhub_data', 'input row must declare no live DevHub data')
        if row.get('contains_private_values') is not False:
            _add(issues, 'private_values_not_allowed', f'{path}.contains_private_values', 'input row must declare no private values')
    return row_ids


def _validate_guidance_placeholders(value: Any, issues: list[SeedPacketIssue]) -> set[str]:
    placeholder_ids = _collect_ids(value, 'official_guidance_placeholders', 'placeholder_id', issues)
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return placeholder_ids
    for index, placeholder in enumerate(value):
        path = f'official_guidance_placeholders[{index}]'
        if not isinstance(placeholder, Mapping):
            continue
        if placeholder.get('source_type') not in _ALLOWED_GUIDANCE_SOURCE_TYPES:
            _add(issues, 'invalid_guidance_source', f'{path}.source_type', 'guidance source must be an official DevHub guidance placeholder')
        if placeholder.get('placeholder_status') != 'placeholder_only':
            _add(issues, 'invalid_placeholder_status', f'{path}.placeholder_status', 'guidance must remain placeholder_only')
        if placeholder.get('live_fetch_performed') is not False:
            _add(issues, 'live_fetch_not_allowed', f'{path}.live_fetch_performed', 'guidance placeholder must not perform live fetches')
    return placeholder_ids


def _validate_schema_updates(value: Any, issues: list[SeedPacketIssue]) -> set[str]:
    update_ids = _collect_ids(value, 'fixture_only_capture_schema_updates', 'schema_update_id', issues)
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return update_ids
    for index, update in enumerate(value):
        path = f'fixture_only_capture_schema_updates[{index}]'
        if not isinstance(update, Mapping):
            continue
        if update.get('fixture_only') is not True:
            _add(issues, 'schema_update_not_fixture_only', f'{path}.fixture_only', 'capture schema update must be fixture_only')
        fields = update.get('allowed_fixture_fields')
        if not _is_non_empty_sequence(fields):
            _add(issues, 'missing_allowed_fixture_fields', f'{path}.allowed_fixture_fields', 'allowed_fixture_fields must be a non-empty list')
        elif any(not isinstance(field, str) or not field.startswith('synthetic_') for field in fields):
            _add(issues, 'unsafe_fixture_field', f'{path}.allowed_fixture_fields', 'fixture capture fields must use synthetic_ prefixes')
    return update_ids


def _validate_reviewer_routing(value: Any, issues: list[SeedPacketIssue]) -> set[str]:
    route_ids = _collect_ids(value, 'reviewer_routing', 'route_id', issues)
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return route_ids
    for index, route in enumerate(value):
        path = f'reviewer_routing[{index}]'
        if not isinstance(route, Mapping):
            continue
        if route.get('reviewer_role') not in _ALLOWED_REVIEWER_ROUTES:
            _add(issues, 'invalid_reviewer_role', f'{path}.reviewer_role', 'reviewer_role must be a known PP&D read-only reviewer route')
    return route_ids


def _validate_targets(value: Any, row_ids: set[str], placeholder_ids: set[str], prerequisite_ids: set[str], redaction_ids: set[str], schema_update_ids: set[str], route_ids: set[str], issues: list[SeedPacketIssue]) -> None:
    target_ids = _collect_ids(value, 'observation_targets', 'target_id', issues)
    if len(target_ids) != len(value) if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) else False:
        _add(issues, 'duplicate_target_id', 'observation_targets', 'observation target ids must be unique')
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return
    for index, target in enumerate(value):
        path = f'observation_targets[{index}]'
        if not isinstance(target, Mapping):
            continue
        if target.get('classification') not in _ALLOWED_TARGET_CLASSIFICATIONS:
            _add(issues, 'invalid_target_classification', f'{path}.classification', 'observation target must be read-only')
        _require_refs(target, 'basis_row_ids', row_ids, f'{path}.basis_row_ids', issues)
        _require_refs(target, 'guidance_placeholder_ids', placeholder_ids, f'{path}.guidance_placeholder_ids', issues)
        _require_refs(target, 'authorization_prerequisite_ids', prerequisite_ids, f'{path}.authorization_prerequisite_ids', issues)
        _require_refs(target, 'redaction_expectation_ids', redaction_ids, f'{path}.redaction_expectation_ids', issues)
        _require_refs(target, 'capture_schema_update_ids', schema_update_ids, f'{path}.capture_schema_update_ids', issues)
        _require_refs(target, 'reviewer_route_ids', route_ids, f'{path}.reviewer_route_ids', issues)


def _validate_artifact_policy(value: Any, issues: list[SeedPacketIssue]) -> None:
    if not isinstance(value, Mapping):
        _add(issues, 'missing_artifact_policy', 'artifact_policy', 'artifact_policy must be an object')
        return
    for key in _ARTIFACT_POLICY_KEYS:
        if value.get(key) is not False:
            _add(issues, 'unsafe_artifact_policy', f'artifact_policy.{key}', f'artifact_policy.{key} must be false')


def _validate_validation_commands(value: Any, issues: list[SeedPacketIssue]) -> None:
    if not _is_non_empty_sequence(value):
        return
    normalized = []
    for index, command in enumerate(value):
        path = f'validation_commands[{index}]'
        if not isinstance(command, Sequence) or isinstance(command, (str, bytes)):
            _add(issues, 'invalid_validation_command', path, 'validation command must be an argv list')
            continue
        command_tuple = tuple(command)
        normalized.append(command_tuple)
        if command_tuple not in _ALLOWED_VALIDATION_COMMANDS:
            _add(issues, 'unsupported_validation_command', path, 'validation command must be one of the exact offline commands for this packet')
    if tuple(normalized) != _ALLOWED_VALIDATION_COMMANDS:
        _add(issues, 'incomplete_validation_commands', 'validation_commands', 'validation_commands must list the exact offline command set in order')


def _collect_ids(value: Any, sequence_path: str, id_key: str, issues: list[SeedPacketIssue]) -> set[str]:
    ids: set[str] = set()
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ids
    for index, item in enumerate(value):
        path = f'{sequence_path}[{index}]'
        if not isinstance(item, Mapping):
            _add(issues, 'invalid_row', path, 'row must be an object')
            continue
        item_id = item.get(id_key)
        if not isinstance(item_id, str) or not item_id.strip():
            _add(issues, 'missing_id', f'{path}.{id_key}', f'{id_key} must be a non-empty string')
        elif item_id in ids:
            _add(issues, 'duplicate_id', f'{path}.{id_key}', f'{id_key} must be unique')
        else:
            ids.add(item_id)
    return ids


def _require_refs(item: Mapping[str, Any], key: str, allowed: set[str], path: str, issues: list[SeedPacketIssue]) -> None:
    refs = item.get(key)
    if not _is_non_empty_sequence(refs):
        _add(issues, 'missing_refs', path, f'{key} must be a non-empty list')
        return
    for ref in refs:
        if ref not in allowed:
            _add(issues, 'unknown_ref', path, f'{ref!r} does not reference a declared row')


def _require_non_empty_sequence(packet: Mapping[str, Any], key: str, issues: list[SeedPacketIssue]) -> None:
    if not _is_non_empty_sequence(packet.get(key)):
        _add(issues, 'missing_required_section', key, f'{key} must be a non-empty list')


def _is_non_empty_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes)) and len(value) > 0


def _scan_for_live_access_claims(value: Any, issues: list[SeedPacketIssue], path: str = '$') -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            _scan_for_live_access_claims(nested, issues, f'{path}.{key}')
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, nested in enumerate(value):
            _scan_for_live_access_claims(nested, issues, f'{path}[{index}]')
        return
    if not isinstance(value, str):
        return
    if any(part in path for part in _POLICY_CONTEXT_PARTS):
        return
    text = value.lower()
    for term in _LIVE_ACCESS_TERMS:
        if term in text:
            _add(issues, 'live_access_claim', path, f'live access or official-action claim is not allowed: {term}')


def _add(issues: list[SeedPacketIssue], code: str, path: str, message: str) -> None:
    issues.append(SeedPacketIssue(code, path, message))


def _dedupe(issues: list[SeedPacketIssue]) -> list[SeedPacketIssue]:
    seen: set[tuple[str, str, str]] = set()
    deduped: list[SeedPacketIssue] = []
    for issue in issues:
        key = (issue.code, issue.path, issue.message)
        if key not in seen:
            seen.add(key)
            deduped.append(issue)
    return deduped
