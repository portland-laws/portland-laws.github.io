from __future__ import annotations

from typing import Any, Iterable, Mapping
from urllib.parse import urlparse

from ppd.extraction.source_freshness_drift import validate_source_freshness_drift_digest
from ppd.post_decision_release_readiness_digest import validate_digest as validate_post_decision_digest

PACKET_TYPE = 'ppd.public_recrawl_execution_rehearsal_plan.v1'
ALLOWED_PUBLIC_HOSTS = frozenset({
    'www.portland.gov',
    'devhub.portlandoregon.gov',
    'www.portlandoregon.gov',
    'www.portlandmaps.com',
})
PUBLIC_SOURCE_TYPES = frozenset({'public_html', 'public_pdf', 'public_form', 'devhub_public', 'external_reference'})
PRIVATE_PATH_MARKERS = (
    '/account', '/accounts', '/application', '/applications', '/cart', '/dashboard',
    '/document', '/documents', '/inspection', '/inspections', '/login', '/logout',
    '/my', '/oauth', '/payment', '/payments', '/permit/', '/permits/', '/private',
    '/secure', '/session', '/signin', '/sign-in', '/upload', '/uploads',
)
FORBIDDEN_KEYS = frozenset({
    'archive_artifact_ref', 'auth_state', 'body', 'content', 'cookie', 'credentials',
    'download_path', 'downloaded_document_path', 'har_path', 'html', 'local_path',
    'password', 'raw_archive_ref', 'raw_body', 'raw_content', 'raw_html',
    'response_body', 'screenshot_path', 'session_state', 'storage_state', 'text',
    'trace_path', 'warc_path',
})
LIVE_KEYS = frozenset({
    'allow_live_network', 'execute_live', 'invoke_processor', 'live_crawl',
    'live_network', 'network_enabled', 'processor_invoked', 'run_live',
})
REQUIRED_ABORT_IDS = frozenset({
    'robots_or_policy_not_approved',
    'target_outside_allowlist',
    'raw_body_persistence_requested',
    'live_network_or_processor_invocation_requested',
})


def build_public_recrawl_execution_rehearsal_plan(
    post_decision_digest: Mapping[str, Any],
    source_freshness_drift_digest: Mapping[str, Any],
    *,
    generated_at: str,
) -> dict[str, Any]:
    post_errors = validate_post_decision_digest(post_decision_digest)
    if post_errors:
        raise ValueError('post-decision release readiness digest failed validation: ' + '; '.join(post_errors))

    drift_result = validate_source_freshness_drift_digest(source_freshness_drift_digest)
    if not drift_result.valid:
        codes = '; '.join(issue.code for issue in drift_result.issues)
        raise ValueError('source freshness drift digest failed validation: ' + codes)

    targets = _select_public_targets(source_freshness_drift_digest)
    plan = {
        'packet_type': PACKET_TYPE,
        'packet_id': 'ppd-public-recrawl-rehearsal-2026-05-28',
        'fixture_first': True,
        'metadata_only': True,
        'dry_run_only': True,
        'generated_at': generated_at,
        'consumed_digests': [
            {
                'role': 'post_decision_release_readiness_digest',
                'packet_id': _text(post_decision_digest.get('packet_id')),
                'release_status': _text(post_decision_digest.get('release_status')),
            },
            {
                'role': 'source_freshness_drift_digest',
                'packet_id': _text(source_freshness_drift_digest.get('packet_id') or source_freshness_drift_digest.get('digest_id')),
                'changed_claim_count': len(_sequence(source_freshness_drift_digest.get('changed_source_claims'))),
            },
        ],
        'selection_policy': {
            'allowed_hosts': sorted(ALLOWED_PUBLIC_HOSTS),
            'public_source_types': sorted(PUBLIC_SOURCE_TYPES),
            'exclude_authenticated_or_private_paths': True,
            'persist_raw_body': False,
        },
        'metadata_targets': [_target_record(target) for target in targets],
        'robots_policy_prerequisites': [_robots_record(target) for target in targets],
        'processor_handoff_intent': [_processor_record(target) for target in targets],
        'rate_limit_notes': [_rate_limit_record(target) for target in targets],
        'dry_run_command_descriptors': [_command_descriptor(target) for target in targets],
        'expected_archive_manifest_ids': [_manifest_id(target['source_id']) for target in targets],
        'archive_manifest_expectations': [_archive_manifest_expectation(target) for target in targets],
        'abort_conditions': _abort_conditions(),
        'no_raw_body_persistence': True,
        'live_network_invoked': False,
        'processor_invoked': False,
    }
    errors = validate_public_recrawl_execution_rehearsal_plan(plan)
    if errors:
        raise ValueError('public recrawl execution rehearsal plan failed validation: ' + '; '.join(errors))
    return plan


def validate_public_recrawl_execution_rehearsal_plan(plan: Mapping[str, Any]) -> list[str]:
    if not isinstance(plan, Mapping):
        return ['plan must be a mapping']

    errors: list[str] = []
    if plan.get('packet_type') != PACKET_TYPE:
        errors.append('packet_type must be ' + PACKET_TYPE)
    for key in ('fixture_first', 'metadata_only', 'dry_run_only', 'no_raw_body_persistence'):
        if plan.get(key) is not True:
            errors.append(key + ' must be true')
    for key in ('live_network_invoked', 'processor_invoked'):
        if plan.get(key) is not False:
            errors.append(key + ' must be false')

    roles = {item.get('role') for item in _sequence(plan.get('consumed_digests')) if isinstance(item, Mapping)}
    for role in ('post_decision_release_readiness_digest', 'source_freshness_drift_digest'):
        if role not in roles:
            errors.append('consumed_digests missing ' + role)

    targets = _sequence(plan.get('metadata_targets'))
    if not targets:
        errors.append('metadata_targets must be non-empty')
    target_ids = set()
    for index, target in enumerate(targets):
        record = _mapping(target)
        source_id = _text(record.get('source_id'))
        target_ids.add(source_id)
        if record.get('selected') is not True:
            errors.append(f'metadata_targets[{index}].selected must be true')
        if record.get('metadata_only') is not True:
            errors.append(f'metadata_targets[{index}].metadata_only must be true')
        if record.get('no_raw_body_persistence') is not True:
            errors.append(f'metadata_targets[{index}].no_raw_body_persistence must be true')
        errors.extend(_url_policy_errors(_text(record.get('canonical_url')), f'metadata_targets[{index}].canonical_url'))

    for section in ('robots_policy_prerequisites', 'processor_handoff_intent', 'rate_limit_notes', 'dry_run_command_descriptors', 'archive_manifest_expectations'):
        rows = _sequence(plan.get(section))
        if len(rows) != len(targets):
            errors.append(section + ' must have one row per metadata target')
        for index, row in enumerate(rows):
            source_id = _text(_mapping(row).get('source_id'))
            if source_id not in target_ids:
                errors.append(f'{section}[{index}] references unknown source_id {source_id}')

    for index, row in enumerate(_sequence(plan.get('robots_policy_prerequisites'))):
        record = _mapping(row)
        if record.get('required_before_live_run') is not True:
            errors.append(f'robots_policy_prerequisites[{index}].required_before_live_run must be true')
        if not _text(record.get('robots_prerequisite')) or not _text(record.get('policy_prerequisite')):
            errors.append(f'robots_policy_prerequisites[{index}] must record robots and policy prerequisites')

    for index, row in enumerate(_sequence(plan.get('processor_handoff_intent'))):
        record = _mapping(row)
        if record.get('intent') != 'deferred_metadata_handoff':
            errors.append(f'processor_handoff_intent[{index}].intent must be deferred_metadata_handoff')
        if record.get('processor_invoked') is not False:
            errors.append(f'processor_handoff_intent[{index}].processor_invoked must be false')
        if record.get('raw_body_persistence') is not False:
            errors.append(f'processor_handoff_intent[{index}].raw_body_persistence must be false')
        if not _text(record.get('expected_archive_manifest_id')):
            errors.append(f'processor_handoff_intent[{index}] missing expected_archive_manifest_id')

    for index, row in enumerate(_sequence(plan.get('dry_run_command_descriptors'))):
        record = _mapping(row)
        if record.get('dry_run_only') is not True:
            errors.append(f'dry_run_command_descriptors[{index}].dry_run_only must be true')
        if record.get('network_invoked') is not False:
            errors.append(f'dry_run_command_descriptors[{index}].network_invoked must be false')
        if record.get('processor_invoked') is not False:
            errors.append(f'dry_run_command_descriptors[{index}].processor_invoked must be false')
        if record.get('persists_raw_body') is not False:
            errors.append(f'dry_run_command_descriptors[{index}].persists_raw_body must be false')

    expected_ids = [_text(item) for item in _sequence(plan.get('expected_archive_manifest_ids'))]
    if len(expected_ids) != len(set(expected_ids)):
        errors.append('expected_archive_manifest_ids must be unique')
    for index, row in enumerate(_sequence(plan.get('archive_manifest_expectations'))):
        record = _mapping(row)
        if _text(record.get('manifest_id')) not in expected_ids:
            errors.append(f'archive_manifest_expectations[{index}] manifest_id is not listed in expected_archive_manifest_ids')
        if record.get('no_raw_body_persisted') is not True:
            errors.append(f'archive_manifest_expectations[{index}].no_raw_body_persisted must be true')

    abort_ids = {item.get('condition_id') for item in _sequence(plan.get('abort_conditions')) if isinstance(item, Mapping)}
    for condition_id in sorted(REQUIRED_ABORT_IDS - abort_ids):
        errors.append('abort_conditions missing ' + condition_id)

    errors.extend(_forbidden_value_errors(plan, '$'))
    return list(dict.fromkeys(errors))


def _select_public_targets(drift_digest: Mapping[str, Any]) -> list[dict[str, Any]]:
    references: dict[str, Mapping[str, Any]] = {}
    for source_ref in _sequence(drift_digest.get('source_references') or drift_digest.get('sources')):
        if isinstance(source_ref, Mapping):
            source_id = _text(source_ref.get('source_id'))
            if source_id:
                references[source_id] = source_ref

    claims_by_source: dict[str, list[Mapping[str, Any]]] = {}
    for claim in _sequence(drift_digest.get('changed_source_claims') or drift_digest.get('claims') or drift_digest.get('changes')):
        if isinstance(claim, Mapping) and claim.get('changed') is not False:
            source_id = _text(claim.get('source_id'))
            if source_id:
                claims_by_source.setdefault(source_id, []).append(claim)

    targets: list[dict[str, Any]] = []
    for source_id in sorted(claims_by_source):
        source_ref = references.get(source_id, {})
        source_type = _text(source_ref.get('source_type') or source_ref.get('type') or 'public_html')
        canonical_url = _text(source_ref.get('canonical_url') or source_ref.get('url') or source_ref.get('requested_url'))
        if source_type not in PUBLIC_SOURCE_TYPES or _url_policy_errors(canonical_url, 'canonical_url'):
            continue
        claims = claims_by_source[source_id]
        targets.append({
            'source_id': source_id,
            'canonical_url': canonical_url,
            'source_type': source_type,
            'changed_claim_ids': _unique_texts(claim.get('claim_id') for claim in claims),
            'affected_requirement_ids': _unique_texts(value for claim in claims for value in _sequence(claim.get('affected_requirement_ids') or claim.get('affected_requirements') or claim.get('requirement_ids'))),
            'affected_guardrail_bundle_ids': _unique_texts(value for claim in claims for value in _sequence(claim.get('affected_guardrail_bundle_ids') or claim.get('affected_guardrails') or claim.get('guardrail_bundle_ids'))),
        })
    if not targets:
        raise ValueError('source freshness drift digest did not contain any allowlisted public metadata targets')
    return targets


def _target_record(target: Mapping[str, Any]) -> dict[str, Any]:
    parsed = urlparse(_text(target.get('canonical_url')))
    return {
        'source_id': target['source_id'],
        'canonical_url': target['canonical_url'],
        'host': parsed.netloc.lower(),
        'source_type': target['source_type'],
        'selected': True,
        'selection_reason': 'changed public metadata source with affected requirement and guardrail links',
        'changed_claim_ids': list(target['changed_claim_ids']),
        'affected_requirement_ids': list(target['affected_requirement_ids']),
        'affected_guardrail_bundle_ids': list(target['affected_guardrail_bundle_ids']),
        'metadata_only': True,
        'no_raw_body_persistence': True,
    }


def _robots_record(target: Mapping[str, Any]) -> dict[str, Any]:
    return {
        'source_id': target['source_id'],
        'canonical_url': target['canonical_url'],
        'robots_prerequisite': 'confirm robots.txt allows the exact metadata request path before any live run',
        'policy_prerequisite': 'confirm PP&D public crawl policy and host allowlist approval before any live run',
        'required_before_live_run': True,
        'record_only_in_rehearsal': True,
    }


def _processor_record(target: Mapping[str, Any]) -> dict[str, Any]:
    return {
        'source_id': target['source_id'],
        'intent': 'deferred_metadata_handoff',
        'processor_family': 'ipfs_datasets_py.web_archive',
        'processor_invoked': False,
        'handoff_payload_scope': 'url, headers, status, content hash, mime type, normalized document reference',
        'raw_body_persistence': False,
        'expected_archive_manifest_id': _manifest_id(_text(target['source_id'])),
    }


def _rate_limit_record(target: Mapping[str, Any]) -> dict[str, Any]:
    return {
        'source_id': target['source_id'],
        'host': urlparse(_text(target.get('canonical_url'))).netloc.lower(),
        'note': 'Use one-at-a-time public metadata requests with at least a 10 second host delay unless robots or policy requires a slower interval.',
        'minimum_delay_seconds': 10,
        'parallel_requests': 1,
        'burst_requests': 1,
    }


def _command_descriptor(target: Mapping[str, Any]) -> dict[str, Any]:
    return {
        'source_id': target['source_id'],
        'descriptor_id': 'dry-run-descriptor.' + _slug(_text(target['source_id'])),
        'command_family': 'ppd_public_metadata_recrawl_rehearsal',
        'intent': 'validate fixtures and render processor handoff metadata without fetching the URL',
        'arguments': [
            {'name': 'source_id', 'value': target['source_id']},
            {'name': 'canonical_url', 'value': target['canonical_url']},
            {'name': 'dry_run_only', 'value': 'true'},
        ],
        'dry_run_only': True,
        'network_invoked': False,
        'processor_invoked': False,
        'persists_raw_body': False,
    }


def _archive_manifest_expectation(target: Mapping[str, Any]) -> dict[str, Any]:
    return {
        'source_id': target['source_id'],
        'manifest_id': _manifest_id(_text(target['source_id'])),
        'canonical_url': target['canonical_url'],
        'expected_fields': [
            'manifest_id', 'source_id', 'canonical_url', 'http_status', 'content_type',
            'content_hash', 'processor_name', 'processor_version', 'normalized_document_id',
            'no_raw_body_persisted',
        ],
        'no_raw_body_persisted': True,
    }


def _abort_conditions() -> list[dict[str, Any]]:
    return [
        {'condition_id': 'robots_or_policy_not_approved', 'abort_when': 'robots.txt, published policy, or local PP&D crawl policy does not explicitly allow the metadata request'},
        {'condition_id': 'target_outside_allowlist', 'abort_when': 'canonical URL host or path falls outside the public allowlist'},
        {'condition_id': 'raw_body_persistence_requested', 'abort_when': 'any rehearsal or handoff step asks to store raw HTML, PDF bytes, WARC, HAR, screenshots, traces, or downloaded documents'},
        {'condition_id': 'live_network_or_processor_invocation_requested', 'abort_when': 'a descriptor attempts live HTTP, browser automation, authenticated DevHub access, or processor execution during rehearsal'},
    ]


def _manifest_id(source_id: str) -> str:
    return 'archive-manifest.' + _slug(source_id) + '.20260528T000000Z'


def _url_policy_errors(url: str, path: str) -> list[str]:
    parsed = urlparse(url)
    errors: list[str] = []
    if parsed.scheme != 'https':
        errors.append(path + ' must use https')
    if parsed.netloc.lower() not in ALLOWED_PUBLIC_HOSTS:
        errors.append(path + ' host must be allowlisted')
    lowered_path = parsed.path.lower()
    if any(marker in lowered_path for marker in PRIVATE_PATH_MARKERS):
        errors.append(path + ' must not reference private or authenticated paths')
    return errors


def _forbidden_value_errors(value: Any, path: str) -> list[str]:
    errors: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized = key_text.lower()
            child_path = path + '.' + key_text
            if normalized in FORBIDDEN_KEYS and child not in (False, None, ''):
                errors.append(child_path + ' uses forbidden raw, private, or downloaded artifact field')
            if normalized in LIVE_KEYS and child is not False:
                errors.append(child_path + ' requests live network or processor execution')
            errors.extend(_forbidden_value_errors(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_forbidden_value_errors(child, f'{path}[{index}]'))
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in ('/home/', '/users/', '.warc', '.har', 'trace.zip', 'storage_state', 'raw-body', 'raw_body')):
            errors.append(path + ' contains forbidden raw, private, or downloaded artifact text')
    return errors


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ''


def _unique_texts(values: Iterable[Any]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(text for text in (_text(value) for value in values) if text))


def _slug(value: str) -> str:
    return ''.join(character if character.isalnum() else '-' for character in value.lower()).strip('-')
