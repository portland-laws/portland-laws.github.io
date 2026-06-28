from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Mapping

from ppd.agent_api_compat_rehearsal_v4 import validate_agent_api_compatibility_rehearsal_v4

PACKET_VERSION = 'fixture-first-action-journal-retention-rehearsal-v4'
SOURCE_FIXTURE_REFS = ('ppd/tests/fixtures/agent_api_compat_rehearsal_v4_valid.json',)
EXACT_OFFLINE_VALIDATION_COMMANDS = [['python3', 'ppd/daemon/ppd_daemon.py', '--self-test']]
REQUIRED_EVENT_TYPES = (
    'public_crawl_preflight',
    'requirement_extraction',
    'gap_analysis',
    'reversible_draft_plan',
    'exact_confirmation_checkpoint',
    'manual_handoff',
    'refused_action',
    'rollback_trigger',
    'completion_evidence_placeholder',
)
_REQUIRED_EVENT_ROW_LABELS = {
    'public_crawl_preflight': 'public crawl preflight row',
    'requirement_extraction': 'requirement extraction row',
    'gap_analysis': 'gap analysis row',
    'reversible_draft_plan': 'reversible draft plan row',
    'exact_confirmation_checkpoint': 'exact-confirmation checkpoint row',
    'manual_handoff': 'manual handoff row',
    'refused_action': 'refused-action row',
    'rollback_trigger': 'rollback trigger row',
    'completion_evidence_placeholder': 'completion evidence placeholder row',
}
ALLOWED_RETENTION_LABELS = frozenset({
    'commit_safe_public_preflight_90d',
    'commit_safe_requirement_summary_180d',
    'commit_safe_gap_summary_180d',
    'commit_safe_reversible_draft_summary_90d',
    'commit_safe_confirmation_checkpoint_90d',
    'commit_safe_manual_handoff_90d',
    'commit_safe_refusal_summary_180d',
    'commit_safe_rollback_trigger_180d',
    'commit_safe_completion_placeholder_180d',
})
_REQUIRED_PACKET_FLAGS = {
    'fixture_first': True,
    'source_fixtures_only': True,
    'live_crawl_performed': False,
    'browser_opened': False,
    'browser_artifacts_stored': False,
    'private_files_read': False,
    'official_action_attempted': False,
    'active_journal_mutated': False,
}
_REQUIRED_EVENT_FIELDS = frozenset({
    'event_id',
    'event_type',
    'compat_fixture_refs',
    'example_status',
    'retention_label',
    'redaction_evidence',
    'commit_safe_reason',
    'exact_offline_validation_commands',
})
_PROHIBITED_KEY_TERMS = frozenset({
    'absolute_path', 'account_number', 'active_mutation', 'auth', 'auth_artifact', 'auth_state',
    'authorization', 'bank', 'browser_state', 'card', 'cookie', 'cookies', 'credential',
    'credentials', 'csrf', 'cvv', 'downloaded_document', 'downloaded_documents',
    'downloaded_file', 'downloaded_files', 'field_value', 'field_values', 'form_value',
    'form_values', 'har', 'har_file', 'legal_guarantee', 'live_mutation', 'local_path',
    'local_private_path', 'mutates_live_systems', 'page_value', 'page_values', 'password',
    'payment', 'payment_detail', 'payment_details', 'permitting_guarantee', 'private_path',
    'private_value', 'private_values', 'raw_crawl_output', 'raw_download', 'raw_downloads',
    'secret', 'session', 'session_file', 'session_state', 'screenshot', 'screenshots',
    'storage_state', 'trace', 'trace_file', 'traces', 'token', 'upload_payload',
})
_PROHIBITED_VALUE_PATTERNS = {
    'browser artifact': re.compile(r'\b(?:screenshot|trace|har file|har archive|browser artifact)\b|\.(?:har|trace|png|jpe?g|webp|zip)\b', re.IGNORECASE),
    'credential material': re.compile(r'\b(?:auth state|bearer\s+[A-Za-z0-9._~-]+|cookie jar|password|set-cookie|sessionid|xsrf|csrf|api[_ -]?key)\b', re.IGNORECASE),
    'downloaded document claim': re.compile(r'\b(?:downloaded document|downloaded file|saved pdf|downloaded pdf|retained document download)\b', re.IGNORECASE),
    'legal or permitting guarantee': re.compile(r'\b(?:guaranteed approval|legal guarantee|permitting guarantee|permit will be approved|will be approved|approval is guaranteed)\b', re.IGNORECASE),
    'local private path': re.compile(r'(?:file://|/(?:home|Users|private|tmp|var/folders)/[^\s]+|[A-Za-z]:\\\\[^\s]+)'),
    'payment number': re.compile(r'\b(?:\d[ -]*?){13,19}\b'),
    'private value claim': re.compile(r'\b(?:private value|private case value|raw private field|unredacted user value)\b', re.IGNORECASE),
    'raw material': re.compile(r'\b(?:raw crawl output|raw download|full html body|full pdf text|raw crawler output)\b', re.IGNORECASE),
    'restricted action claim': re.compile(r'\b(?:submitted|uploaded|scheduled|paid|certified|permit issued|inspection scheduled)\b', re.IGNORECASE),
    'active mutation claim': re.compile(r'\b(?:active mutation|mutates live systems|live mutation enabled|guardrails activated|active journal mutated)\b', re.IGNORECASE),
}
_REDACTION_MARKER = re.compile(r'^\[REDACTED:[a-z0-9_.-]+\]$')


@dataclass(frozen=True)
class RetentionRehearsalV4Result:
    ok: bool
    problems: tuple[str, ...]
    event_count: int
    event_types: tuple[str, ...]


def load_action_journal_retention_rehearsal_v4(path: str | Path) -> dict[str, Any]:
    parsed = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(parsed, dict):
        raise ValueError('retention rehearsal fixture must contain a JSON object')
    return parsed


def validate_action_journal_retention_rehearsal_v4(packet: Mapping[str, Any]) -> RetentionRehearsalV4Result:
    if not isinstance(packet, Mapping):
        return RetentionRehearsalV4Result(False, ('packet must be an object',), 0, ())

    problems: list[str] = []
    if packet.get('packet_version') != PACKET_VERSION:
        problems.append(f'packet_version must be {PACKET_VERSION}')
    if tuple(packet.get('source_fixture_refs', ())) != SOURCE_FIXTURE_REFS:
        problems.append('source_fixture_refs must contain only the agent API compatibility rehearsal v4 fixture')
    if packet.get('exact_offline_validation_commands') != EXACT_OFFLINE_VALIDATION_COMMANDS:
        problems.append('exact_offline_validation_commands must contain only the daemon self-test command')
    for field, expected in _REQUIRED_PACKET_FLAGS.items():
        if packet.get(field) is not expected:
            problems.append(f'{field} must be {expected!r}')

    compat_payload = packet.get('consumed_agent_api_compatibility_rehearsal_v4')
    if not isinstance(compat_payload, Mapping):
        problems.append('consumed_agent_api_compatibility_rehearsal_v4 must be an object')
    else:
        for error in validate_agent_api_compatibility_rehearsal_v4(dict(compat_payload)):
            problems.append(f'agent_api_compatibility_rehearsal_v4: {error}')

    events = packet.get('journal_event_examples')
    if not isinstance(events, list):
        problems.append('journal_event_examples must be a list')
        events = []
    elif not events:
        problems.append('journal_event_examples must include commit-safe journal event examples')

    seen_ids: set[str] = set()
    seen_types: list[str] = []
    for index, event in enumerate(events):
        path = f'journal_event_examples[{index}]'
        if not isinstance(event, Mapping):
            problems.append(f'{path} must be an object')
            continue
        problems.extend(_validate_event(event, path, seen_ids))
        event_type = event.get('event_type')
        if isinstance(event_type, str):
            seen_types.append(event_type)

    seen_type_set = set(seen_types)
    for required_type in REQUIRED_EVENT_TYPES:
        if required_type not in seen_type_set:
            problems.append(f'journal_event_examples missing {_REQUIRED_EVENT_ROW_LABELS[required_type]}')
    if tuple(seen_types) != REQUIRED_EVENT_TYPES:
        problems.append('journal_event_examples must include required v4 event types in deterministic order')

    problems.extend(_walk_for_restricted_material(packet, 'packet'))
    return RetentionRehearsalV4Result(not problems, tuple(dict.fromkeys(problems)), len(events), tuple(seen_types))


def assert_action_journal_retention_rehearsal_v4(packet: Mapping[str, Any]) -> None:
    result = validate_action_journal_retention_rehearsal_v4(packet)
    if not result.ok:
        raise AssertionError('invalid action journal retention rehearsal v4:\n' + '\n'.join(result.problems))


def _validate_event(event: Mapping[str, Any], path: str, seen_ids: set[str]) -> list[str]:
    problems: list[str] = []
    for field in sorted(_REQUIRED_EVENT_FIELDS.difference(event)):
        problems.append(f'{path}.{field} is required')
    event_id = event.get('event_id')
    if not _is_non_empty_string(event_id):
        problems.append(f'{path}.event_id must be a non-empty string')
    elif str(event_id) in seen_ids:
        problems.append(f'{path}.event_id is duplicated')
    else:
        seen_ids.add(str(event_id))
    if event.get('event_type') not in REQUIRED_EVENT_TYPES:
        problems.append(f'{path}.event_type is unsupported')
    if tuple(event.get('compat_fixture_refs', ())) != SOURCE_FIXTURE_REFS:
        problems.append(f'{path}.compat_fixture_refs must reference only the agent API compatibility rehearsal v4 fixture')
    if event.get('example_status') not in {'placeholder_only', 'draft_only', 'blocked'}:
        problems.append(f'{path}.example_status is unsupported')
    if event.get('retention_label') not in ALLOWED_RETENTION_LABELS:
        problems.append(f'{path}.retention_label is unsupported')
    if not _is_non_empty_string(event.get('commit_safe_reason')):
        problems.append(f'{path}.commit_safe_reason must be a non-empty string')
    if event.get('exact_offline_validation_commands') != EXACT_OFFLINE_VALIDATION_COMMANDS:
        problems.append(f'{path}.exact_offline_validation_commands must contain only the daemon self-test command')
    problems.extend(_validate_redaction_evidence(event.get('redaction_evidence'), f'{path}.redaction_evidence'))
    return problems


def _validate_redaction_evidence(value: Any, path: str) -> list[str]:
    if not isinstance(value, Mapping):
        return [f'{path} must be an object']
    problems: list[str] = []
    markers = value.get('redacted_examples')
    if not isinstance(markers, Mapping) or not markers:
        problems.append(f'{path}.redacted_examples must be a non-empty object')
    else:
        for key, marker in markers.items():
            if not _is_non_empty_string(key):
                problems.append(f'{path}.redacted_examples keys must be non-empty strings')
            if not isinstance(marker, str) or not _REDACTION_MARKER.match(marker):
                problems.append(f'{path}.redacted_examples.{key} must be an explicit redaction marker')
    for field in ('restricted_material_absent', 'offline_validation_only', 'compat_fixture_only'):
        if value.get(field) is not True:
            problems.append(f'{path}.{field} must be True')
    checks = value.get('checks')
    if not _is_non_empty_string_list(checks):
        problems.append(f'{path}.checks must be a non-empty list of strings')
    return problems


def _walk_for_restricted_material(value: Any, path: str) -> list[str]:
    problems: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f'{path}.{key}'
            if _is_prohibited_key(_normalize_key(str(key))):
                problems.append(f'{child_path} uses a prohibited sensitive key')
            problems.extend(_walk_for_restricted_material(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            problems.extend(_walk_for_restricted_material(child, f'{path}[{index}]'))
    elif isinstance(value, str):
        for reason, pattern in _PROHIBITED_VALUE_PATTERNS.items():
            if pattern.search(value):
                problems.append(f'{path} contains prohibited {reason}')
    return problems


def _is_prohibited_key(normalized_key: str) -> bool:
    parts = set(normalized_key.split('_'))
    return normalized_key in _PROHIBITED_KEY_TERMS or bool(parts.intersection(_PROHIBITED_KEY_TERMS))


def _normalize_key(value: str) -> str:
    return value.strip().lower().replace('-', '_').replace(' ', '_')


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_non_empty_string_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(_is_non_empty_string(item) for item in value)


__all__ = [
    'EXACT_OFFLINE_VALIDATION_COMMANDS',
    'PACKET_VERSION',
    'REQUIRED_EVENT_TYPES',
    'SOURCE_FIXTURE_REFS',
    'RetentionRehearsalV4Result',
    'assert_action_journal_retention_rehearsal_v4',
    'load_action_journal_retention_rehearsal_v4',
    'validate_action_journal_retention_rehearsal_v4',
]
