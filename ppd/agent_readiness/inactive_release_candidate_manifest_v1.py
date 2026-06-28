from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PACKET_TYPE = 'ppd.inactive_release_candidate_manifest.v1'
PACKET_VERSION = 'v1'
EXPECTED_INPUT_TYPE = 'ppd.synthetic_approved_delta_references.v1'
REQUIRED_DELTA_SECTIONS = (
    'source_delta_refs',
    'requirement_delta_refs',
    'process_delta_refs',
    'guardrail_delta_refs',
    'agent_gap_analysis_delta_refs',
)
EXACT_OFFLINE_VALIDATION_COMMANDS = [
    ['python3', '-m', 'py_compile', 'ppd/agent_readiness/inactive_release_candidate_manifest_v1.py'],
    ['python3', '-m', 'pytest', 'ppd/tests/test_inactive_release_candidate_manifest_v1.py'],
    ['python3', 'ppd/daemon/ppd_daemon.py', '--self-test'],
]

PRIVATE_OR_RAW_KEY_TOKENS = (
    'auth', 'browser', 'cookie', 'credential', 'devhub_session', 'download', 'downloaded', 'har',
    'password', 'private', 'raw', 'screenshot', 'session', 'storage_state', 'token', 'trace', 'upload', 'warc',
)
PRIVATE_OR_RAW_VALUE_TOKENS = (
    'auth state', 'browser state', 'cookie jar', 'downloaded document', 'har file', 'private devhub',
    'raw body', 'raw crawl', 'raw html', 'raw pdf', 'session storage', 'storage state', 'trace.zip', 'warc payload',
)
LIVE_OR_PROMOTION_TOKENS = (
    'active release', 'activated release', 'crawler started', 'devhub access', 'live crawl', 'live release',
    'promoted to active', 'release activated', 'release promoted',
)
OFFICIAL_ACTION_TOKENS = (
    'certification completed', 'certified acknowledgement', 'certify acknowledgement', 'click submit',
    'fee payment completed', 'final action completed', 'inspection scheduled', 'official action completed',
    'official action performed', 'pay fees', 'payment completed', 'permit submitted', 'schedule inspection',
    'submit payment', 'submit permit', 'submission completed', 'upload completed', 'upload corrections',
    'uploaded corrections', 'uploaded plans',
)
GUARANTEE_TOKENS = (
    'approval guaranteed', 'approval is certain', 'compliance guaranteed', 'guaranteed approval',
    'guaranteed issuance', 'legal advice', 'legal guarantee', 'legal outcome guaranteed',
    'permit approval is certain', 'permit will be approved', 'permit will be issued', 'permitting guarantee',
    'will be approved', 'will be issued',
)
MUTATION_FLAGS = {
    'active_agent_gap_analysis_mutation', 'active_archive_mutation', 'active_contract_mutation',
    'active_crawler_mutation', 'active_daemon_state_mutation', 'active_devhub_surface_mutation',
    'active_document_mutation', 'active_guardrail_mutation', 'active_process_mutation', 'active_prompt_mutation',
    'active_release_mutation', 'active_requirement_mutation', 'active_source_mutation', 'active_surface_mutation',
    'release_activation_enabled', 'release_promotion_enabled',
}


@dataclass(frozen=True)
class InactiveReleaseCandidateManifestV1ValidationResult:
    valid: bool
    problems: tuple[str, ...]


class InactiveReleaseCandidateManifestV1Error(ValueError):
    def __init__(self, problems: Iterable[str]) -> None:
        self.problems = tuple(problems)
        super().__init__('invalid inactive release candidate manifest v1: ' + '; '.join(self.problems))


def load_json_object(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise ValueError(f'expected JSON object at {path}')
    return value


def build_inactive_release_candidate_manifest_v1_from_file(path: str | Path) -> dict[str, Any]:
    return build_inactive_release_candidate_manifest_v1(load_json_object(path))


def build_inactive_release_candidate_manifest_v1(delta_packet: Mapping[str, Any]) -> dict[str, Any]:
    problems = _validate_input_packet(delta_packet)
    if problems:
        raise InactiveReleaseCandidateManifestV1Error(problems)
    evidence_ids = _collect_evidence_ids(delta_packet)
    manifest: dict[str, Any] = {
        'packet_type': PACKET_TYPE,
        'packet_version': PACKET_VERSION,
        'mode': 'fixture_first_inactive_release_candidate_manifest_only',
        'manifest_id': str(delta_packet.get('manifest_id')),
        'candidate_status': 'inactive_pending_reviewer_signoff',
        'fixture_only': True,
        'candidate_only': True,
        'metadata_only': True,
        'immutable_evidence_ids': evidence_ids,
        'inactive_candidate_summary': {
            'summary_id': f'inactive-summary:{delta_packet.get("manifest_id")}',
            'source_delta_count': len(_mapping_sequence(delta_packet.get('source_delta_refs'))),
            'requirement_delta_count': len(_mapping_sequence(delta_packet.get('requirement_delta_refs'))),
            'process_delta_count': len(_mapping_sequence(delta_packet.get('process_delta_refs'))),
            'guardrail_delta_count': len(_mapping_sequence(delta_packet.get('guardrail_delta_refs'))),
            'agent_gap_analysis_delta_count': len(_mapping_sequence(delta_packet.get('agent_gap_analysis_delta_refs'))),
            'release_activation_enabled': False,
            'release_promotion_enabled': False,
        },
        'delta_references': {section: [_manifest_ref(section, row) for row in _mapping_sequence(delta_packet.get(section))] for section in REQUIRED_DELTA_SECTIONS},
        'migration_notes': [_note_ref('migration', row) for row in _mapping_sequence(delta_packet.get('migration_notes'))],
        'rollback_notes': [_note_ref('rollback', row) for row in _mapping_sequence(delta_packet.get('rollback_notes'))],
        'reviewer_signoff_placeholders': _reviewer_signoff_placeholders(evidence_ids),
        'exact_offline_validation_commands': EXACT_OFFLINE_VALIDATION_COMMANDS,
        'side_effect_boundaries': {
            'live_crawl_performed': False,
            'devhub_accessed': False,
            'private_file_accessed': False,
            'form_filled': False,
            'official_action_performed': False,
            'release_activated': False,
            'release_promoted': False,
            'active_source_mutation': False,
            'active_requirement_mutation': False,
            'active_process_mutation': False,
            'active_guardrail_mutation': False,
            'active_agent_gap_analysis_mutation': False,
            'active_prompt_mutation': False,
            'active_contract_mutation': False,
            'active_archive_mutation': False,
            'active_document_mutation': False,
            'active_devhub_surface_mutation': False,
            'active_surface_mutation': False,
            'active_crawler_mutation': False,
            'active_daemon_state_mutation': False,
        },
    }
    assert_valid_inactive_release_candidate_manifest_v1(manifest)
    return manifest


def validate_inactive_release_candidate_manifest_v1(packet: Mapping[str, Any]) -> InactiveReleaseCandidateManifestV1ValidationResult:
    problems: list[str] = []
    if not isinstance(packet, Mapping):
        return InactiveReleaseCandidateManifestV1ValidationResult(False, ('manifest must be an object',))
    if packet.get('packet_type') != PACKET_TYPE:
        problems.append(f'packet_type must be {PACKET_TYPE}')
    if packet.get('packet_version') != PACKET_VERSION:
        problems.append('packet_version must be v1')
    if packet.get('mode') != 'fixture_first_inactive_release_candidate_manifest_only':
        problems.append('mode must be fixture_first_inactive_release_candidate_manifest_only')
    if packet.get('candidate_status') != 'inactive_pending_reviewer_signoff':
        problems.append('candidate_status must remain inactive_pending_reviewer_signoff')
    for key in ('fixture_only', 'candidate_only', 'metadata_only'):
        if packet.get(key) is not True:
            problems.append(f'{key} must be true')
    if packet.get('exact_offline_validation_commands') != EXACT_OFFLINE_VALIDATION_COMMANDS:
        problems.append('exact_offline_validation_commands must match the required offline commands exactly')

    evidence_ids = _string_sequence(packet.get('immutable_evidence_ids'))
    evidence_id_set = set(evidence_ids)
    if not evidence_ids:
        problems.append('immutable_evidence_ids must be a non-empty list')
    if len(evidence_ids) != len(evidence_id_set):
        problems.append('immutable_evidence_ids must be unique')
    for evidence_id in evidence_ids:
        if not _is_immutable_evidence_id(evidence_id):
            problems.append(f'immutable evidence id is not valid: {evidence_id}')

    summary = _mapping(packet.get('inactive_candidate_summary'))
    if not summary:
        problems.append('inactive_candidate_summary is required')
    if summary.get('release_activation_enabled') is not False:
        problems.append('inactive_candidate_summary.release_activation_enabled must be false')
    if summary.get('release_promotion_enabled') is not False:
        problems.append('inactive_candidate_summary.release_promotion_enabled must be false')

    delta_references = _mapping(packet.get('delta_references'))
    for section in REQUIRED_DELTA_SECTIONS:
        rows = _mapping_sequence(delta_references.get(section))
        if not rows:
            problems.append(f'delta_references.{section} must be a non-empty list')
        for index, row in enumerate(rows):
            _validate_manifest_ref(section, index, row, evidence_id_set, problems)

    for note_section in ('migration_notes', 'rollback_notes'):
        rows = _mapping_sequence(packet.get(note_section))
        if not rows:
            problems.append(f'{note_section} must be a non-empty list')
        for index, row in enumerate(rows):
            prefix = f'{note_section}[{index}]'
            if not _text(row.get('note_id')):
                problems.append(f'{prefix}.note_id is required')
            if not _text(row.get('note')):
                problems.append(f'{prefix}.note is required')
            _validate_known_evidence(prefix, row, evidence_id_set, problems)

    signoff_rows = _mapping_sequence(packet.get('reviewer_signoff_placeholders'))
    if not signoff_rows:
        problems.append('reviewer_signoff_placeholders must be a non-empty list')
    for index, row in enumerate(signoff_rows):
        prefix = f'reviewer_signoff_placeholders[{index}]'
        for field in ('signoff_id', 'role', 'reviewer', 'reviewed_at', 'decision', 'notes', 'source_evidence_ids'):
            if field not in row:
                problems.append(f'{prefix}.{field} is required')
        if row.get('decision') != 'pending_manual_review':
            problems.append(f'{prefix}.decision must be pending_manual_review')
        if row.get('reviewer') != '' or row.get('reviewed_at') != '' or row.get('notes') != '':
            problems.append(f'{prefix} must remain an unsigned reviewer placeholder')
        _validate_known_evidence(prefix, row, evidence_id_set, problems)

    boundaries = _mapping(packet.get('side_effect_boundaries'))
    if not boundaries:
        problems.append('side_effect_boundaries is required')
    for key, value in boundaries.items():
        if value is not False:
            problems.append(f'side_effect_boundaries.{key} must be false')

    _validate_no_forbidden_payload(packet, problems)
    return InactiveReleaseCandidateManifestV1ValidationResult(not problems, tuple(problems))


def assert_valid_inactive_release_candidate_manifest_v1(packet: Mapping[str, Any]) -> None:
    result = validate_inactive_release_candidate_manifest_v1(packet)
    if not result.valid:
        raise InactiveReleaseCandidateManifestV1Error(result.problems)


def _validate_input_packet(packet: Mapping[str, Any]) -> list[str]:
    problems: list[str] = []
    if not isinstance(packet, Mapping):
        return ['synthetic approved delta references must be an object']
    if packet.get('packet_type') != EXPECTED_INPUT_TYPE:
        problems.append(f'input packet_type must be {EXPECTED_INPUT_TYPE}')
    if not _text(packet.get('manifest_id')):
        problems.append('manifest_id is required')
    for section in REQUIRED_DELTA_SECTIONS:
        rows = _mapping_sequence(packet.get(section))
        if not rows:
            problems.append(f'{section} must be a non-empty list')
        for index, row in enumerate(rows):
            prefix = f'{section}[{index}]'
            if row.get('approval_status') != 'approved_for_inactive_release_candidate_manifest_v1':
                problems.append(f'{prefix}.approval_status must approve inactive release candidate manifest v1')
            if not _text(row.get('delta_id')):
                problems.append(f'{prefix}.delta_id is required')
            if not _string_sequence(row.get('source_evidence_ids')):
                problems.append(f'{prefix}.source_evidence_ids must be non-empty')
    if not _mapping_sequence(packet.get('migration_notes')):
        problems.append('migration_notes must be a non-empty list')
    if not _mapping_sequence(packet.get('rollback_notes')):
        problems.append('rollback_notes must be a non-empty list')
    for evidence_id in _collect_evidence_ids(packet):
        if not _is_immutable_evidence_id(evidence_id):
            problems.append(f'immutable evidence id is not valid: {evidence_id}')
    _validate_no_forbidden_payload(packet, problems)
    return problems


def _manifest_ref(section: str, row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        'reference_id': f'inactive-release-ref:{section}:{row.get("delta_id")}',
        'delta_id': _text(row.get('delta_id')),
        'delta_type': section.removesuffix('_refs'),
        'candidate_status': 'inactive_reference_only',
        'source_evidence_ids': _string_sequence(row.get('source_evidence_ids')),
        'summary': _text(row.get('summary')),
        'active_mutation': False,
    }


def _note_ref(note_type: str, row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        'note_id': _text(row.get('note_id')),
        'note_type': note_type,
        'applies_to_delta_ids': _string_sequence(row.get('applies_to_delta_ids')),
        'source_evidence_ids': _string_sequence(row.get('source_evidence_ids')),
        'note': _text(row.get('note')),
        'requires_manual_review_before_any_future_activation': True,
    }


def _reviewer_signoff_placeholders(evidence_ids: Sequence[str]) -> list[dict[str, Any]]:
    roles = ('source_registry_reviewer', 'requirement_reviewer', 'process_model_reviewer', 'guardrail_reviewer', 'agent_gap_analysis_reviewer', 'release_manager')
    return [{'signoff_id': f'inactive-release-candidate-manifest-v1:{role}', 'role': role, 'reviewer': '', 'reviewed_at': '', 'decision': 'pending_manual_review', 'notes': '', 'source_evidence_ids': list(evidence_ids)} for role in roles]


def _validate_manifest_ref(section: str, index: int, row: Mapping[str, Any], evidence_ids: set[str], problems: list[str]) -> None:
    prefix = f'delta_references.{section}[{index}]'
    if not _text(row.get('reference_id')):
        problems.append(f'{prefix}.reference_id is required')
    if not _text(row.get('delta_id')):
        problems.append(f'{prefix}.delta_id is required')
    if row.get('candidate_status') != 'inactive_reference_only':
        problems.append(f'{prefix}.candidate_status must be inactive_reference_only')
    if row.get('active_mutation') is not False:
        problems.append(f'{prefix}.active_mutation must be false')
    _validate_known_evidence(prefix, row, evidence_ids, problems)


def _validate_known_evidence(prefix: str, row: Mapping[str, Any], evidence_ids: set[str], problems: list[str]) -> None:
    refs = _string_sequence(row.get('source_evidence_ids'))
    if not refs:
        problems.append(f'{prefix}.source_evidence_ids must be non-empty')
    for evidence_id in refs:
        if evidence_id not in evidence_ids:
            problems.append(f'{prefix}.source_evidence_ids contains unknown evidence id: {evidence_id}')


def _collect_evidence_ids(packet: Mapping[str, Any]) -> list[str]:
    evidence_ids: set[str] = set()
    for section in REQUIRED_DELTA_SECTIONS:
        for row in _mapping_sequence(packet.get(section)):
            evidence_ids.update(_string_sequence(row.get('source_evidence_ids')))
    for section in ('migration_notes', 'rollback_notes'):
        for row in _mapping_sequence(packet.get(section)):
            evidence_ids.update(_string_sequence(row.get('source_evidence_ids')))
    return sorted(evidence_ids)


def _validate_no_forbidden_payload(packet: Mapping[str, Any], problems: list[str]) -> None:
    for path, key, value in _walk(packet):
        normalized_key = key.lower().replace('-', '_')
        if normalized_key in MUTATION_FLAGS and value is not False:
            problems.append(f'{path} must be false')
        if any(token in normalized_key for token in PRIVATE_OR_RAW_KEY_TOKENS) and _truthy(value):
            problems.append(f'{path} must not include private, session, browser, raw, downloaded, upload, or authenticated artifacts')
        if isinstance(value, str):
            text = value.lower()
            if any(token in text for token in PRIVATE_OR_RAW_VALUE_TOKENS):
                problems.append(f'{path} must not reference private, session, browser, raw, downloaded, or authenticated artifacts')
            if any(token in text for token in LIVE_OR_PROMOTION_TOKENS):
                problems.append(f'{path} must not claim live execution or release promotion')
            if any(token in text for token in GUARANTEE_TOKENS):
                problems.append(f'{path} must not guarantee legal or permitting outcomes')
            if any(token in text for token in OFFICIAL_ACTION_TOKENS):
                problems.append(f'{path} must not include official-action completion language')


def _walk(value: Any, prefix: str = 'packet', key: str = 'packet') -> Iterable[tuple[str, str, Any]]:
    if isinstance(value, Mapping):
        for child_key, child_value in value.items():
            child_key_text = str(child_key)
            child_path = f'{prefix}.{child_key_text}'
            yield child_path, child_key_text, child_value
            yield from _walk(child_value, child_path, child_key_text)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, child_value in enumerate(value):
            child_path = f'{prefix}[{index}]'
            yield child_path, key, child_value
            yield from _walk(child_value, child_path, key)


def _is_immutable_evidence_id(value: str) -> bool:
    prefix = 'ev:ppd-fixture:'
    marker = ':sha256:'
    if not value.startswith(prefix) or marker not in value:
        return False
    slug, digest = value[len(prefix):].rsplit(marker, 1)
    return bool(slug) and all(ch.islower() or ch.isdigit() or ch == '-' for ch in slug) and len(digest) == 64 and all(ch in '0123456789abcdef' for ch in digest)


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _mapping_sequence(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _string_sequence(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _truthy(value: Any) -> bool:
    if value is None or value is False or value == '':
        return False
    if isinstance(value, Mapping) and not value:
        return False
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) and not value:
        return False
    return True


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ''
