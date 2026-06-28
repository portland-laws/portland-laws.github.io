from __future__ import annotations

from dataclasses import dataclass
from ipaddress import ip_address
from typing import Any, Mapping, Sequence
from urllib.parse import urlparse

MANIFEST_TYPE = 'ppd.public_crawl_dry_run_promotion_manifest.v1'

ALLOWED_PUBLIC_HOSTS = frozenset({
    'www.portland.gov',
    'devhub.portlandoregon.gov',
    'www.portlandoregon.gov',
    'www.portlandmaps.com',
})

ALLOWED_ROBOTS_STATUSES = frozenset({'allowed', 'permitted', 'public_allowed'})
ALLOWED_POLICY_STATUSES = frozenset({'approved', 'allowed', 'public', 'public_allowed'})

REQUIRED_ABORT_CONDITIONS = frozenset({
    'private_or_authenticated_url',
    'non_allowlisted_host',
    'raw_body_or_download_requested',
    'robots_or_policy_missing',
    'live_network_execution_requested',
    'processor_handoff_intent_missing',
    'real_crawl_or_download_claimed',
})

PRIVATE_PATH_MARKERS = (
    '/account', '/accounts', '/admin', '/application', '/applications',
    '/auth', '/cart', '/dashboard', '/document', '/documents',
    '/inspection', '/inspections', '/login', '/logout', '/my', '/oauth',
    '/payment', '/payments', '/permit/', '/permits/', '/private',
    '/secure', '/session', '/signin', '/sign-in', '/sso', '/upload',
    '/uploads', '/user/',
)

AUTH_QUERY_MARKERS = (
    'access_token', 'api_key', 'auth', 'bearer', 'client_secret', 'code',
    'jwt', 'key', 'oauth', 'password', 'private_key', 'secret', 'session',
    'sid', 'signature', 'signed', 'token',
)

FORBIDDEN_ARTIFACT_KEYS = frozenset({
    'archive_artifact_path', 'archive_path', 'auth_state', 'body', 'content',
    'cookie', 'credentials', 'download_path', 'download_paths',
    'downloaded_document_path', 'downloaded_document_paths', 'document_body',
    'document_path', 'document_paths', 'full_html', 'full_text', 'har_path',
    'html', 'local_archive_path', 'local_document_path', 'local_path',
    'page_body', 'password', 'pdf_body', 'raw_archive_path',
    'raw_archive_ref', 'raw_body', 'raw_content', 'raw_html', 'raw_pdf',
    'raw_text', 'response_body', 'saved_path', 'screenshot_path',
    'session_state', 'storage_state', 'text', 'trace_path', 'warc_path',
})

LIVE_EXECUTION_KEYS = frozenset({
    'allow_live_network', 'allow_network', 'browser_invoked',
    'download_invoked', 'execute_live', 'fetched', 'live_crawl',
    'live_network', 'network_enabled', 'network_invoked', 'processor_invoked',
    'real_crawl_performed', 'real_download_performed', 'request_executed',
    'run_live', 'url_fetched', 'use_live_network',
})

FORBIDDEN_TEXT_MARKERS = (
    '/home/', '/users/', 'c:\\users\\', '.har', '.warc', 'auth-state',
    'bearer ', 'cookie=', 'downloaded document', 'password=',
    'real crawl was performed', 'real download was performed',
    'response body', 'storage-state', 'token=', 'trace.zip',
)


@dataclass(frozen=True)
class PublicDryRunPromotionSummary:
    manifest_id: str
    target_count: int
    abort_condition_count: int
    ready_for_live_execution: bool


def build_public_dry_run_promotion_summary(manifest: Mapping[str, Any]) -> PublicDryRunPromotionSummary:
    errors = validate_public_dry_run_promotion_manifest(manifest)
    if errors:
        raise ValueError('invalid public dry-run promotion manifest: ' + '; '.join(errors))
    return PublicDryRunPromotionSummary(
        manifest_id=str(manifest['manifest_id']),
        target_count=len(_sequence(manifest.get('promotion_targets'))),
        abort_condition_count=len(_sequence(manifest.get('abort_conditions'))),
        ready_for_live_execution=False,
    )


def assert_public_dry_run_promotion_manifest(manifest: Mapping[str, Any]) -> PublicDryRunPromotionSummary:
    return build_public_dry_run_promotion_summary(manifest)


def validate_public_dry_run_promotion_manifest(manifest: Mapping[str, Any]) -> list[str]:
    if not isinstance(manifest, Mapping):
        return ['manifest must be an object']

    errors: list[str] = []
    _scan_for_forbidden_values(manifest, '$', errors)

    if manifest.get('manifest_type') != MANIFEST_TYPE:
        errors.append('manifest_type must be ' + MANIFEST_TYPE)
    if not _required_text(manifest.get('manifest_id')):
        errors.append('manifest_id is required')

    for key in ('fixture_first', 'dry_run_only', 'metadata_only', 'no_raw_body_persistence'):
        if manifest.get(key) is not True:
            errors.append(key + ' must be true')
    for key in ('live_network_invoked', 'processor_invoked', 'ready_for_live_execution', 'real_crawl_performed', 'real_download_performed'):
        if manifest.get(key) is not False:
            errors.append(key + ' must be false')

    targets = _sequence(manifest.get('promotion_targets'))
    if not targets:
        errors.append('promotion_targets must be a non-empty list')
    target_ids: set[str] = set()
    for index, target in enumerate(targets):
        record = _mapping(target)
        location = 'promotion_targets[' + str(index) + ']'
        source_id = _required_text(record.get('source_id'))
        if not source_id:
            errors.append(location + '.source_id is required')
        else:
            target_ids.add(source_id)
        url = _required_text(record.get('canonical_url') or record.get('url'))
        if not url:
            errors.append(location + '.canonical_url is required')
        else:
            errors.extend(_url_policy_errors(url, location + '.canonical_url'))
        if record.get('selected_for_promotion') is not True:
            errors.append(location + '.selected_for_promotion must be true')
        if record.get('dry_run_only') is not True:
            errors.append(location + '.dry_run_only must be true')
        if record.get('no_raw_body_persistence') is not True:
            errors.append(location + '.no_raw_body_persistence must be true')
        if record.get('real_crawl_performed') is not False:
            errors.append(location + '.real_crawl_performed must be false')
        if record.get('real_download_performed') is not False:
            errors.append(location + '.real_download_performed must be false')

    prerequisites = _sequence(manifest.get('robots_policy_prerequisites'))
    if len(prerequisites) != len(targets):
        errors.append('robots_policy_prerequisites must have one row per promotion target')
    for index, prerequisite in enumerate(prerequisites):
        record = _mapping(prerequisite)
        location = 'robots_policy_prerequisites[' + str(index) + ']'
        _validate_known_source(record, target_ids, location, errors)
        robots_status = _normalized_status(record.get('robots_status') or record.get('robots'))
        policy_status = _normalized_status(record.get('policy_status') or record.get('policy'))
        if robots_status not in ALLOWED_ROBOTS_STATUSES:
            errors.append(location + '.robots_status must be explicitly allowed')
        if policy_status not in ALLOWED_POLICY_STATUSES:
            errors.append(location + '.policy_status must be explicitly approved')
        if record.get('required_before_live_run') is not True:
            errors.append(location + '.required_before_live_run must be true')

    handoffs = _sequence(manifest.get('processor_handoff_intent'))
    if len(handoffs) != len(targets):
        errors.append('processor_handoff_intent must have one row per promotion target')
    for index, handoff in enumerate(handoffs):
        record = _mapping(handoff)
        location = 'processor_handoff_intent[' + str(index) + ']'
        _validate_known_source(record, target_ids, location, errors)
        if record.get('intent') not in {'deferred_metadata_handoff', 'metadata_only_handoff'}:
            errors.append(location + '.intent must declare deferred metadata handoff')
        if record.get('processor_invoked') is not False:
            errors.append(location + '.processor_invoked must be false')
        if record.get('network_invoked') is not False:
            errors.append(location + '.network_invoked must be false')
        if record.get('raw_body_persistence') is not False:
            errors.append(location + '.raw_body_persistence must be false')
        if not _required_text(record.get('expected_archive_manifest_id')):
            errors.append(location + '.expected_archive_manifest_id is required')

    abort_ids = {str(item.get('condition_id')) for item in _sequence(manifest.get('abort_conditions')) if isinstance(item, Mapping)}
    for condition_id in sorted(REQUIRED_ABORT_CONDITIONS - abort_ids):
        errors.append('abort_conditions missing ' + condition_id)

    return list(dict.fromkeys(errors))


def _validate_known_source(record: Mapping[str, Any], target_ids: set[str], location: str, errors: list[str]) -> None:
    source_id = _required_text(record.get('source_id'))
    if not source_id:
        errors.append(location + '.source_id is required')
    elif source_id not in target_ids:
        errors.append(location + ' references unknown source_id ' + source_id)


def _url_policy_errors(url: str, path: str) -> list[str]:
    parsed = urlparse(url)
    errors: list[str] = []
    if parsed.scheme != 'https':
        errors.append(path + ' must use https')
    if parsed.username or parsed.password:
        errors.append(path + ' must not include credentials')
    host_lower = (parsed.hostname or '').lower()
    if not host_lower:
        errors.append(path + ' must include a host')
    elif host_lower not in ALLOWED_PUBLIC_HOSTS:
        errors.append(path + ' host must be allowlisted')
    if host_lower in {'localhost', 'localhost.localdomain'} or host_lower.endswith('.local'):
        errors.append(path + ' host must not be local or private')
    try:
        address = ip_address(host_lower)
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        errors.append(path + ' host must not be private or non-public')
    if any(marker in parsed.path.lower() for marker in PRIVATE_PATH_MARKERS):
        errors.append(path + ' must not reference private or authenticated paths')
    if any(marker in parsed.query.lower() for marker in AUTH_QUERY_MARKERS):
        errors.append(path + ' query must not contain authentication material')
    return errors


def _scan_for_forbidden_values(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized_key = key_text.lower()
            child_path = path + '.' + key_text
            if normalized_key in FORBIDDEN_ARTIFACT_KEYS and child not in (False, None, '', [], {}):
                errors.append(child_path + ' must not include raw bodies, downloads, session state, or archive paths')
            if normalized_key in LIVE_EXECUTION_KEYS and child is not False:
                errors.append(child_path + ' must not claim live network, processor, crawl, or download execution')
            _scan_for_forbidden_values(child, child_path, errors)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, child in enumerate(value):
            _scan_for_forbidden_values(child, path + '[' + str(index) + ']', errors)
        return
    if isinstance(value, str):
        if _is_abort_condition_text(path):
            return
        lowered = value.lower()
        if any(marker in lowered for marker in FORBIDDEN_TEXT_MARKERS):
            errors.append(path + ' contains forbidden raw, private, download, archive, or live-execution text')


def _is_abort_condition_text(path: str) -> bool:
    return path.startswith('$.abort_conditions[') and (
        path.endswith('.condition_id') or path.endswith('.abort_when')
    )


def _normalized_status(value: Any) -> str:
    if isinstance(value, Mapping):
        for key in ('status', 'state', 'decision'):
            status = _normalized_status(value.get(key))
            if status:
                return status
        return ''
    if not isinstance(value, str):
        return ''
    return value.strip().lower().replace('-', '_').replace(' ', '_')


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _required_text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ''
