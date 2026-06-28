'''Fixture-first inactive process-model delta assembly plan v1 validation.'''

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PACKET_TYPE = 'ppd.inactive_process_model_delta_assembly_plan.v1'
PACKET_VERSION = 'v1'
VALIDATION_COMMANDS = [['python3', 'ppd/daemon/ppd_daemon.py', '--self-test']]
SYNTHETIC_QUEUE_SOURCE = 'synthetic_requirement_reextraction_candidate_queue'

REQUIRED_TOP_LEVEL_SEQUENCES = (
    'synthetic_requirement_reextraction_candidate_queue_rows',
    'inactive_process_model_patch_placeholders',
    'affected_process_stage_mappings',
    'required_user_fact_impact_mappings',
    'required_document_impact_mappings',
    'unsupported_path_notes',
    'reviewer_holds',
    'rollback_notes',
    'validation_commands',
)

ACTIVE_MUTATION_FLAGS = (
    'active_process_model_promotion',
    'active_process_model_mutation',
    'active_guardrail_mutation',
    'active_requirement_mutation',
    'active_source_registry_mutation',
    'active_release_state_mutation',
    'portal_opened',
    'private_artifacts_stored',
    'official_actions_performed',
)

REQUIRED_QUEUE_FIELDS = (
    'candidate_row_id',
    'queue_source',
    'requirement_candidate_id',
    'candidate_requirement_type',
    'candidate_subject',
    'candidate_action',
    'candidate_object',
    'candidate_process_stage',
    'synthetic_evidence_refs',
    'status',
)

REQUIRED_PLACEHOLDER_FIELDS = (
    'patch_placeholder_id',
    'process_id',
    'permit_type',
    'candidate_row_refs',
    'affected_stage_refs',
    'required_user_fact_impact_refs',
    'required_document_impact_refs',
    'unsupported_path_note_refs',
    'reviewer_hold_refs',
    'rollback_note_refs',
    'status',
    'promotion_blockers',
    'validation_commands',
)

FORBIDDEN_VALUE_TERMS = (
    'auth state',
    'authenticated session',
    'browser state',
    'captcha',
    'cookie',
    'credential',
    'downloaded artifact',
    'downloaded document',
    'har file',
    'live crawl',
    'live devhub',
    'opened devhub',
    'payment detail',
    'private artifact',
    'private file',
    'raw crawl',
    'raw downloaded',
    'raw portal',
    'session storage',
    'submitted',
    'uploaded',
)

FORBIDDEN_CLAIM_TERMS = (
    'active guardrail changed',
    'active process model promoted',
    'application submitted',
    'certified acknowledgement',
    'completed official action',
    'correction uploaded',
    'devhub observed',
    'devhub portal verified',
    'devhub verified',
    'inspection scheduled',
    'legal advice',
    'legally sufficient',
    'no legal risk',
    'official action completed',
    'payment submitted',
    'permit approval guaranteed',
    'permit guarantee',
    'permit submitted',
    'permit will be approved',
    'schedule inspection',
    'submit payment',
    'submit permit',
)


@dataclass(frozen=True)
class InactiveProcessModelDeltaAssemblyPlanV1ValidationResult:
    valid: bool
    problems: tuple[str, ...]


class InactiveProcessModelDeltaAssemblyPlanV1Error(ValueError):
    def __init__(self, problems: Iterable[str]) -> None:
        self.problems = tuple(problems)
        super().__init__('invalid inactive process-model delta assembly plan v1: ' + '; '.join(self.problems))


def load_inactive_process_model_delta_assembly_plan_v1(path: str | Path) -> dict[str, Any]:
    loaded = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(loaded, dict):
        raise ValueError('inactive process-model delta assembly plan v1 fixture must be a JSON object')
    assert_valid_inactive_process_model_delta_assembly_plan_v1(loaded)
    return loaded


def assert_valid_inactive_process_model_delta_assembly_plan_v1(packet: Mapping[str, Any]) -> None:
    result = validate_inactive_process_model_delta_assembly_plan_v1(packet)
    if not result.valid:
        raise InactiveProcessModelDeltaAssemblyPlanV1Error(result.problems)


def validate_inactive_process_model_delta_assembly_plan_v1(packet: Mapping[str, Any]) -> InactiveProcessModelDeltaAssemblyPlanV1ValidationResult:
    problems: list[str] = []
    if not isinstance(packet, Mapping):
        return InactiveProcessModelDeltaAssemblyPlanV1ValidationResult(False, ('packet must be an object',))

    if packet.get('packet_type') != PACKET_TYPE:
        problems.append(f'packet_type must be {PACKET_TYPE}')
    if packet.get('packet_version') != PACKET_VERSION:
        problems.append('packet_version must be v1')
    if packet.get('fixture_first') is not True:
        problems.append('fixture_first must be true')
    if packet.get('assembly_mode') != 'inactive_process_model_delta_patch_placeholders_only':
        problems.append('assembly_mode must be inactive_process_model_delta_patch_placeholders_only')
    if packet.get('candidate_input_policy') != 'synthetic_requirement_reextraction_candidate_queue_rows_only':
        problems.append('candidate_input_policy must be synthetic_requirement_reextraction_candidate_queue_rows_only')
    if packet.get('validation_commands') != VALIDATION_COMMANDS:
        problems.append('validation_commands must contain only the PP&D daemon self-test command')

    for key in REQUIRED_TOP_LEVEL_SEQUENCES:
        if not _non_empty_sequence(packet.get(key)):
            problems.append(f'{key} must be a non-empty list')

    for flag in ACTIVE_MUTATION_FLAGS:
        if packet.get(flag) is not False:
            problems.append(f'{flag} must be false')

    _validate_queue_rows(packet.get('synthetic_requirement_reextraction_candidate_queue_rows'), problems)
    _validate_placeholders(packet.get('inactive_process_model_patch_placeholders'), problems)
    _validate_status_rows(packet.get('affected_process_stage_mappings'), 'stage_mapping_id', 'inactive_stage_impact_placeholder', problems)
    _validate_status_rows(packet.get('required_user_fact_impact_mappings'), 'fact_impact_id', 'inactive_user_fact_impact_placeholder', problems)
    _validate_status_rows(packet.get('required_document_impact_mappings'), 'document_impact_id', 'inactive_document_impact_placeholder', problems)
    _validate_status_rows(packet.get('unsupported_path_notes'), 'unsupported_path_note_id', 'inactive_note_only', problems)
    _validate_status_rows(packet.get('reviewer_holds'), 'reviewer_hold_id', 'hold_active', problems)
    _validate_status_rows(packet.get('rollback_notes'), 'rollback_note_id', 'rollback_note_only', problems)
    _validate_cross_refs(packet, problems)
    _validate_no_forbidden_payload(packet, problems)
    return InactiveProcessModelDeltaAssemblyPlanV1ValidationResult(not problems, tuple(problems))


def _validate_queue_rows(value: Any, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f'synthetic_requirement_reextraction_candidate_queue_rows[{index}]'
        for field in REQUIRED_QUEUE_FIELDS:
            if field not in row:
                problems.append(f'{prefix}.{field} is required')
        if row.get('queue_source') != SYNTHETIC_QUEUE_SOURCE:
            problems.append(f'{prefix}.queue_source must be {SYNTHETIC_QUEUE_SOURCE}')
        if row.get('status') != 'synthetic_candidate_for_delta_assembly':
            problems.append(f'{prefix}.status must be synthetic_candidate_for_delta_assembly')
        if not _synthetic_refs(row.get('synthetic_evidence_refs')):
            problems.append(f'{prefix}.synthetic_evidence_refs must contain only synthetic or fixture evidence refs')


def _validate_placeholders(value: Any, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f'inactive_process_model_patch_placeholders[{index}]'
        for field in REQUIRED_PLACEHOLDER_FIELDS:
            if field not in row:
                problems.append(f'{prefix}.{field} is required')
        if row.get('status') != 'inactive_patch_placeholder_only':
            problems.append(f'{prefix}.status must be inactive_patch_placeholder_only')
        if row.get('validation_commands') != VALIDATION_COMMANDS:
            problems.append(f'{prefix}.validation_commands must contain only the PP&D daemon self-test command')
        if not _non_empty_sequence(row.get('promotion_blockers')):
            problems.append(f'{prefix}.promotion_blockers must be a non-empty list')


def _validate_status_rows(value: Any, id_field: str, expected_status: str, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f'{id_field}[{index}]'
        if not _text(row.get(id_field)):
            problems.append(f'{prefix}.{id_field} is required')
        if not _text(row.get('candidate_row_ref')):
            problems.append(f'{prefix}.candidate_row_ref is required')
        if row.get('status') != expected_status:
            problems.append(f'{prefix}.status must be {expected_status}')


def _validate_cross_refs(packet: Mapping[str, Any], problems: list[str]) -> None:
    ref_sets = {
        'candidate_row_refs': _ids(packet.get('synthetic_requirement_reextraction_candidate_queue_rows'), 'candidate_row_id'),
        'affected_stage_refs': _ids(packet.get('affected_process_stage_mappings'), 'stage_mapping_id'),
        'required_user_fact_impact_refs': _ids(packet.get('required_user_fact_impact_mappings'), 'fact_impact_id'),
        'required_document_impact_refs': _ids(packet.get('required_document_impact_mappings'), 'document_impact_id'),
        'unsupported_path_note_refs': _ids(packet.get('unsupported_path_notes'), 'unsupported_path_note_id'),
        'reviewer_hold_refs': _ids(packet.get('reviewer_holds'), 'reviewer_hold_id'),
        'rollback_note_refs': _ids(packet.get('rollback_notes'), 'rollback_note_id'),
    }
    candidate_ids = ref_sets['candidate_row_refs']
    for section_name in (
        'affected_process_stage_mappings',
        'required_user_fact_impact_mappings',
        'required_document_impact_mappings',
        'unsupported_path_notes',
        'reviewer_holds',
        'rollback_notes',
    ):
        for index, row in enumerate(_mapping_sequence(packet.get(section_name))):
            ref = _text(row.get('candidate_row_ref'))
            if ref and ref not in candidate_ids:
                problems.append(f'{section_name}[{index}].candidate_row_ref contains unknown ref {ref}')

    covered_candidate_refs: set[str] = set()
    for index, row in enumerate(_mapping_sequence(packet.get('inactive_process_model_patch_placeholders'))):
        prefix = f'inactive_process_model_patch_placeholders[{index}]'
        for field, allowed in ref_sets.items():
            refs = _require_refs(prefix, field, row.get(field), allowed, problems)
            if field == 'candidate_row_refs':
                covered_candidate_refs.update(refs)

    for ref in sorted(candidate_ids - covered_candidate_refs):
        problems.append(f'synthetic_requirement_reextraction_candidate_queue_rows contains unreferenced candidate row {ref}')


def _validate_no_forbidden_payload(value: Any, problems: list[str], path: str = 'packet') -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f'{path}.{key}'
            if key in ACTIVE_MUTATION_FLAGS and child is not False:
                problems.append(f'{child_path} must be false')
            _validate_no_forbidden_payload(child, problems, child_path)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _validate_no_forbidden_payload(child, problems, f'{path}[{index}]')
    elif isinstance(value, str):
        lowered = value.lower()
        if any(term in lowered for term in FORBIDDEN_VALUE_TERMS):
            problems.append(f'{path} must not contain private, raw, downloaded, portal, live crawl, live DevHub, upload, submit, or session artifacts')
        if any(term in lowered for term in FORBIDDEN_CLAIM_TERMS):
            problems.append(f'{path} must not contain live DevHub claims, promotion claims, official-action completion claims, legal guarantees, or permitting guarantees')


def _require_refs(prefix: str, field: str, value: Any, allowed: set[str], problems: list[str]) -> set[str]:
    refs = {item for item in _text_sequence(value) if item}
    if not refs:
        problems.append(f'{prefix}.{field} must be a non-empty list')
        return set()
    for ref in sorted(refs):
        if ref not in allowed:
            problems.append(f'{prefix}.{field} contains unknown ref {ref}')
    return refs


def _ids(value: Any, field: str) -> set[str]:
    return {_text(row.get(field)) for row in _mapping_sequence(value) if _text(row.get(field))}


def _mapping_sequence(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _text_sequence(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [item for item in (_text(item) for item in value) if item]


def _non_empty_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)) and len(value) > 0


def _text(value: Any) -> str:
    return value if isinstance(value, str) else ''


def _synthetic_refs(value: Any) -> bool:
    refs = _text_sequence(value)
    return bool(refs) and all(ref.startswith(('synthetic:', 'fixture-source:')) for ref in refs)
