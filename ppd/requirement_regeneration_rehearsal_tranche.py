from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

REQUIRED_ATTESTATIONS = (
    'fixture_first_inputs_only',
    'metadata_only_outputs',
    'no_live_extraction_performed',
    'no_processor_invoked',
    'no_requirement_mutation_performed',
    'no_process_mutation_performed',
    'no_guardrail_mutation_performed',
)
RAW_KEYS = {
    'archive_path', 'archive_ref', 'archive_url', 'body', 'body_html', 'download_path',
    'download_ref', 'download_url', 'downloaded_document_path', 'raw_archive',
    'raw_archive_path', 'raw_body', 'raw_content', 'raw_html', 'response_body', 'warc_path',
}
RAW_MARKERS = ('raw_body', 'raw html', 'raw_html', 'response_body', 'download_path', 'download url', 'download_url', 'archive_path', 'archive url', 'archive_url', 'warc', '/download', '/archive')
RAW_SUFFIXES = ('.warc', '.zip', '.tar', '.tgz', '.gz')
PRIVATE_MARKERS = ('access_token', 'authorization', 'bearer ', 'cookie', 'devhub_session', 'indexeddb', 'localstorage', 'password', 'private case fact', 'private_case_fact', 'refresh_token', 'sessionid', 'storage_state', 'trace.zip', '.har', '/tmp/', '/var/folders/')
LIVE_MARKERS = ('live extraction', 'extracted live', 'live extractor', 'ran extraction', 'executed extraction', 'processor ran', 'processor executed', 'processor invoked', 'ran the processor', 'ran processor', 'processor execution', 'live processor', 'live crawl', 'crawler ran', 'crawler executed', 'crawler invoked', 'fetched url', 'downloaded document')
GUARANTEE_MARKERS = ('approval is guaranteed', 'approval guaranteed', 'guaranteed approval', 'guarantee permit', 'guarantees permit', 'permit will be approved', 'permit is approved', 'permitting outcome guaranteed', 'legal outcome guaranteed', 'legal determination', 'legally sufficient', 'compliance guaranteed', 'entitled to approval')
MUTATION_KEYS = {
    'active_guardrail_mutation', 'active_process_mutation', 'active_prompt_mutation',
    'active_release_state_mutation', 'active_requirement_mutation',
    'apply_to_live_guardrails', 'apply_to_live_processes', 'apply_to_live_prompts',
    'apply_to_live_release_state', 'apply_to_live_requirements',
    'guardrail_mutation_enabled', 'process_mutation_enabled', 'prompt_mutation_enabled',
    'release_state_mutation_enabled', 'requirement_mutation_enabled',
    'mutates_active_guardrail', 'mutates_active_guardrails', 'mutates_active_process',
    'mutates_active_processes', 'mutates_active_prompt', 'mutates_active_prompts',
    'mutates_active_release_state', 'mutates_active_requirement', 'mutates_active_requirements',
    'writes_live_guardrail', 'writes_live_guardrails', 'writes_live_process',
    'writes_live_processes', 'writes_live_prompt', 'writes_live_prompts',
    'writes_live_release_state', 'writes_live_requirement', 'writes_live_requirements',
}

@dataclass(frozen=True)
class SyntheticRerunCase:
    case_id: str
    order: int
    requirement_id: str
    source_id: str
    rerun_step_ref: str
    expected_output_ref: str
    expected_output_kind: str
    affected_process_ids: tuple[str, ...]
    affected_guardrail_ids: tuple[str, ...]
    source_evidence_ids: tuple[str, ...]
    reviewer_owner: str
    disposition: str

    def to_dict(self) -> dict[str, Any]:
        return {
            'case_id': self.case_id,
            'order': self.order,
            'requirement_id': self.requirement_id,
            'source_id': self.source_id,
            'rerun_step_ref': self.rerun_step_ref,
            'expected_output': {
                'output_ref': self.expected_output_ref,
                'output_kind': self.expected_output_kind,
                'metadata_only': True,
            },
            'affected_requirement_ids': [self.requirement_id],
            'affected_process_ids': list(self.affected_process_ids),
            'affected_guardrail_ids': list(self.affected_guardrail_ids),
            'source_evidence_ids': list(self.source_evidence_ids),
            'reviewer_owner': self.reviewer_owner,
            'reviewer_disposition': self.disposition,
        }

def build_requirement_regeneration_rehearsal_tranche_packet(packet: Mapping[str, Any]) -> dict[str, Any]:
    _reject_unsafe_content(packet, 'input_packet')
    disposition_packet = _mapping(packet, 'evidence_freshness_watchlist_reviewer_disposition_packet')
    work_queue_packet = _mapping(packet, 'requirement_rerun_work_queue_packet')
    traceability_packet = _mapping(packet, 'requirement_guardrail_traceability_review_packet')
    dispositions = _dispositions_by_source(disposition_packet)
    traceability = _traceability_by_requirement(traceability_packet)
    requirement_ids = _required_text_list(work_queue_packet, 'requirement_ids')
    citations = _mapping(work_queue_packet, 'citations')
    rerun_steps = _ordered_rerun_steps(work_queue_packet)
    owners = _required_text_list(work_queue_packet, 'reviewer_owners')
    cases: list[SyntheticRerunCase] = []
    for index, requirement_id in enumerate(requirement_ids, start=1):
        trace = traceability.get(requirement_id, {})
        source_id = _source_id_for_requirement(requirement_id, citations, dispositions)
        disposition = dispositions.get(source_id, {})
        step = rerun_steps[min(index - 1, len(rerun_steps) - 1)]
        evidence_ids = _ordered_unique(_text_list(citations.get(requirement_id)) + _text_list(trace.get('source_evidence_ids')) + _text_list(disposition.get('source_evidence_ids')))
        cases.append(SyntheticRerunCase(
            case_id='requirement-regeneration-case-' + _slug(requirement_id),
            order=index,
            requirement_id=requirement_id,
            source_id=source_id,
            rerun_step_ref=_required_text(step, 'name'),
            expected_output_ref='metadata://requirement-regeneration/' + _slug(requirement_id),
            expected_output_kind='requirement_delta_review_metadata',
            affected_process_ids=tuple(_ordered_unique(_text_list(trace.get('process_ids')) or _text_list(work_queue_packet.get('affected_process_refs')))),
            affected_guardrail_ids=tuple(_ordered_unique(_text_list(trace.get('guardrail_ids')) or _text_list(work_queue_packet.get('affected_guardrail_refs')))),
            source_evidence_ids=tuple(evidence_ids),
            reviewer_owner=_reviewer_owner(requirement_id, trace, disposition, owners),
            disposition=_disposition_value(disposition),
        ))
    tranche = {
        'packet_type': 'ppd_requirement_regeneration_rehearsal_tranche_packet',
        'packet_version': '1.0',
        'tranche_id': _required_text(packet, 'tranche_id'),
        'tranche_status': 'metadata_only_rehearsal_ready_for_review',
        'consumes_packet_ids': [_required_text(disposition_packet, 'packet_id'), _required_text(work_queue_packet, 'packet_id'), _required_text(traceability_packet, 'packet_id')],
        'ordered_synthetic_rerun_cases': [case.to_dict() for case in cases],
        'expected_metadata_only_outputs': [{
            'case_id': case.case_id,
            'output_ref': case.expected_output_ref,
            'output_kind': case.expected_output_kind,
            'metadata_only': True,
            'no_requirement_record_written': True,
            'no_process_model_written': True,
            'no_guardrail_bundle_written': True,
        } for case in cases],
        'reviewer_owner_fields_required': True,
        'attestations': {key: True for key in REQUIRED_ATTESTATIONS},
    }
    validate_requirement_regeneration_rehearsal_tranche_packet(tranche)
    return tranche

def validate_requirement_regeneration_rehearsal_tranche_packet(packet: Mapping[str, Any]) -> None:
    if packet.get('packet_type') != 'ppd_requirement_regeneration_rehearsal_tranche_packet':
        raise ValueError('unexpected packet_type')
    if packet.get('tranche_status') != 'metadata_only_rehearsal_ready_for_review':
        raise ValueError('tranche_status must remain metadata-only review')
    attestations = _mapping(packet, 'attestations')
    for key in REQUIRED_ATTESTATIONS:
        if attestations.get(key) is not True:
            raise ValueError(f'required attestation is missing or false: {key}')
    if not _text_list(packet.get('consumes_packet_ids')):
        raise ValueError('consumes_packet_ids must be a non-empty list of strings')
    cases = packet.get('ordered_synthetic_rerun_cases')
    if not isinstance(cases, list) or not cases:
        raise ValueError('ordered_synthetic_rerun_cases must be a non-empty list')
    expected_orders = list(range(1, len(cases) + 1))
    actual_orders: list[int] = []
    seen_case_ids: set[str] = set()
    output_refs_by_case: dict[str, str] = {}
    for case in cases:
        if not isinstance(case, Mapping):
            raise ValueError('ordered_synthetic_rerun_cases entries must be objects')
        case_id = _required_text(case, 'case_id')
        if case_id in seen_case_ids:
            raise ValueError(f'duplicate case_id: {case_id}')
        seen_case_ids.add(case_id)
        order = case.get('order')
        if not isinstance(order, int) or isinstance(order, bool):
            raise ValueError('case order must be an integer')
        actual_orders.append(order)
        requirement_id = _required_text(case, 'requirement_id')
        _required_text(case, 'source_id')
        _required_text(case, 'rerun_step_ref')
        _required_text(case, 'reviewer_owner')
        affected_requirement_ids = _required_text_list(case, 'affected_requirement_ids')
        if requirement_id not in affected_requirement_ids:
            raise ValueError('affected_requirement_ids must include requirement_id')
        _required_text_list(case, 'affected_process_ids')
        _required_text_list(case, 'affected_guardrail_ids')
        evidence_ids = _required_text_list(case, 'source_evidence_ids')
        if not any(_looks_cited(item) for item in evidence_ids):
            raise ValueError('uncited rerun case: source_evidence_ids must contain cited evidence references')
        expected_output = _mapping(case, 'expected_output')
        output_ref = _required_text(expected_output, 'output_ref')
        _required_text(expected_output, 'output_kind')
        output_refs_by_case[case_id] = output_ref
        if expected_output.get('metadata_only') is not True:
            raise ValueError('case expected_output.metadata_only must be true')
    if actual_orders != expected_orders:
        raise ValueError(f'ordered_synthetic_rerun_cases must be ordered as {expected_orders}, got {actual_orders}')
    outputs = packet.get('expected_metadata_only_outputs')
    if not isinstance(outputs, list) or len(outputs) != len(cases):
        raise ValueError('expected_metadata_only_outputs must match the case count')
    seen_output_case_ids: set[str] = set()
    for output in outputs:
        if not isinstance(output, Mapping):
            raise ValueError('expected_metadata_only_outputs entries must be objects')
        case_id = _required_text(output, 'case_id')
        output_ref = _required_text(output, 'output_ref')
        if output_refs_by_case.get(case_id) != output_ref:
            raise ValueError('expected metadata output must reference a case output_ref')
        seen_output_case_ids.add(case_id)
        _required_text(output, 'output_kind')
        if output.get('metadata_only') is not True:
            raise ValueError('expected metadata output must be metadata_only')
        for key in ('no_requirement_record_written', 'no_process_model_written', 'no_guardrail_bundle_written'):
            if output.get(key) is not True:
                raise ValueError(f'expected metadata output must attest {key}')
    if seen_output_case_ids != seen_case_ids:
        raise ValueError('expected_metadata_only_outputs must cover every rerun case')
    _reject_unsafe_content(packet, 'packet')

def _dispositions_by_source(packet: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    rows = packet.get('watchlist_item_dispositions') or packet.get('source_dispositions')
    if not isinstance(rows, list) or not rows:
        raise ValueError('watchlist dispositions must be a non-empty list')
    indexed: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError('watchlist disposition entries must be objects')
        indexed[_required_text(row, 'source_id')] = row
    return indexed

def _traceability_by_requirement(packet: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    rows = packet.get('requirement_to_process_to_guardrail_links')
    if not isinstance(rows, list) or not rows:
        raise ValueError('traceability links must be a non-empty list')
    indexed: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError('traceability link entries must be objects')
        indexed[_required_text(row, 'requirement_id')] = row
    return indexed

def _ordered_rerun_steps(packet: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    rows = packet.get('rerun_steps')
    if not isinstance(rows, list) or not rows:
        raise ValueError('rerun_steps must be a non-empty list')
    ordered = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError('rerun_steps entries must be objects')
        if not isinstance(row.get('order'), int) or isinstance(row.get('order'), bool):
            raise ValueError('rerun_steps.order must be an integer')
        ordered.append(row)
    ordered.sort(key=lambda item: item['order'])
    return ordered

def _source_id_for_requirement(requirement_id: str, citations: Mapping[str, Any], dispositions: Mapping[str, Mapping[str, Any]]) -> str:
    evidence_text = ' '.join(_text_list(citations.get(requirement_id))).lower()
    for source_id in dispositions:
        tokens = [token for token in _slug(source_id).split('-') if token and token not in {'ppd', 'source'}]
        if any(token in evidence_text for token in tokens):
            return source_id
    return next(iter(dispositions))

def _reviewer_owner(requirement_id: str, trace: Mapping[str, Any], disposition: Mapping[str, Any], owners: Sequence[str]) -> str:
    fields = trace.get('reviewer_owner_fields')
    if isinstance(fields, Mapping):
        for value in fields.values():
            if isinstance(value, str) and value.strip():
                return value
    for key in ('reviewer_owner', 'reviewer', 'owner'):
        value = disposition.get(key)
        if isinstance(value, str) and value.strip():
            return value
    if owners:
        return owners[0]
    raise ValueError(f'reviewer owner is required for {requirement_id}')

def _disposition_value(disposition: Mapping[str, Any]) -> str:
    for key in ('decision', 'reviewer_disposition'):
        value = disposition.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return 'metadata_rehearsal_review_required'

def _mapping(value: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    child = value.get(key)
    if not isinstance(child, Mapping):
        raise ValueError(f'{key} must be an object')
    return child

def _required_text(value: Mapping[str, Any], key: str) -> str:
    child = value.get(key)
    if not isinstance(child, str) or not child.strip():
        raise ValueError(f'{key} must be a non-empty string')
    return child

def _required_text_list(value: Mapping[str, Any], key: str) -> list[str]:
    result = _text_list(value.get(key))
    if not result:
        raise ValueError(f'{key} must be a non-empty list of strings')
    return result

def _text_list(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    result = [item for item in value if isinstance(item, str) and item.strip()]
    if len(result) != len(value):
        return []
    return result

def _ordered_unique(items: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result

def _reject_unsafe_content(value: Any, path: str) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            key_lower = key_text.lower()
            child_path = f'{path}.{key_text}'
            if key_lower in RAW_KEYS:
                raise ValueError(f'raw body/download/archive reference is not allowed: {child_path}')
            if key_lower in MUTATION_KEYS and not _falsey_claim(child):
                raise ValueError(f'active requirement/process/guardrail/prompt/release-state mutation flag is not allowed: {child_path}')
            if any(marker in key_lower for marker in PRIVATE_MARKERS):
                raise ValueError(f'private case facts are not allowed: {child_path}')
            _reject_unsafe_content(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_unsafe_content(child, f'{path}[{index}]')
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in RAW_MARKERS) or lowered.endswith(RAW_SUFFIXES):
            raise ValueError(f'raw body/download/archive reference is not allowed: {path}')
        if any(marker in lowered for marker in PRIVATE_MARKERS):
            raise ValueError(f'private case facts are not allowed: {path}')
        if any(marker in lowered for marker in LIVE_MARKERS):
            raise ValueError(f'live extraction or processor execution claim is not allowed: {path}')
        if any(marker in lowered for marker in GUARANTEE_MARKERS):
            raise ValueError(f'legal or permitting outcome guarantee is not allowed: {path}')

def _falsey_claim(value: Any) -> bool:
    return value is False or value is None or value in {'', 'false', 'not_applied', 'metadata_only', 'proposed_only', 'review_only'}

def _looks_cited(value: str) -> bool:
    return ':' in value or value.startswith(('citation-', 'evidence-', 'source-', 'trace-'))

def _slug(value: str) -> str:
    chars = []
    previous_dash = False
    for char in value.lower():
        if char.isalnum():
            chars.append(char)
            previous_dash = False
        elif not previous_dash:
            chars.append('-')
            previous_dash = True
    return ''.join(chars).strip('-') or 'item'
