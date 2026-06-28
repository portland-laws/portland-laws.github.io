from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import urlparse

from ppd.crawler.processor_handoff_readiness import validate_processor_handoff_readiness

ALLOWLISTED_HOSTS = frozenset({
    'www.portland.gov',
    'devhub.portlandoregon.gov',
    'www.portlandoregon.gov',
    'www.portlandmaps.com',
})

PREREQUISITE_KEYS = ('prerequisite_links', 'prerequisites', 'policy_prerequisite_links', 'robots_policy_prerequisites')
TARGET_KEYS = ('targets', 'target_urls', 'source_targets', 'handoff_targets')
SKIPPED_KEYS = ('skipped_targets', 'skips', 'skipped_urls')
FRESHNESS_SOURCE_KEYS = ('sources', 'reviewed_sources', 'source_reviews', 'freshness_reviews')
URL_KEYS = ('url', 'href', 'target_url', 'canonical_url', 'requested_url')
SOURCE_ID_KEYS = ('source_id', 'sourceId', 'id', 'target_id')
SKIP_REASON_KEYS = ('skipped_reason', 'reason', 'policy_reason')

PRIVATE_PATH_MARKERS = (
    '/account', '/accounts', '/auth', '/dashboard', '/login', '/oauth', '/payment', '/payments',
    '/permit/', '/permits/', '/private', '/session', '/signin', '/sign-in', '/upload',
)
RAW_DOWNLOAD_ARCHIVE_MARKERS = ('.har', '.warc', '.zip', '/archive', '/download', '/raw')
FORBIDDEN_TRUE_KEYS = frozenset({
    'allow_live_network', 'archive_artifact_produced', 'archive_artifacts_produced', 'archive_produced',
    'archive_written', 'artifacts_written', 'execute_processor', 'invoke_processor',
    'live_processor_execution', 'processor_executed', 'processor_invoked', 'run_processor',
    'start_processor', 'write_archive_artifacts',
})
FORBIDDEN_VALUE_KEYS = frozenset({
    'archive_artifact_ref', 'archive_artifacts', 'download_path', 'downloaded_document_ref',
    'har_path', 'raw_body', 'raw_body_ref', 'raw_content', 'raw_html', 'screenshot_path',
    'trace_path', 'warc_path',
})
FORBIDDEN_STATUS_VALUES = frozenset({
    'archive_artifact_produced', 'archive_artifacts_produced', 'archive_written',
    'processor_executed', 'processor_invoked',
})

DEFAULT_PROCESSOR_CAPABILITIES = (
    'ipfs_datasets_py import path is available to the later processor runner',
    'metadata-only URL capture is supported by the selected processor adapter',
    'processor runner can return manifest identifiers without committing raw archives',
    'runner configuration keeps persistRawBody=false and downloadDocuments=false',
)
DEFAULT_ABORT_CONDITIONS = (
    'Abort if any readiness validation issue is present.',
    'Abort if any freshness review marks a target stale, missing, or unresolved.',
    'Abort if a target URL leaves the PP&D public allowlist or appears authenticated.',
    'Abort if the operator is asked to invoke a processor from this checklist.',
    'Abort if raw body persistence, archive writing, screenshots, traces, HAR files, or downloaded documents are requested.',
    'Abort if rate-limit guidance for the target host is missing or conflicts with public crawl policy.',
)


@dataclass(frozen=True)
class OperatorChecklistIssue:
    code: str
    message: str
    path: str = '$'


def build_processor_handoff_operator_checklist(
    readiness_packet: Mapping[str, Any],
    freshness_review_packet: Mapping[str, Any],
    *,
    generated_at: str,
    operator_role: str = 'manual_ppd_operator',
) -> dict[str, Any]:
    readiness = validate_processor_handoff_readiness(readiness_packet)
    targets = _collect_targets(readiness_packet)
    skipped_targets = _collect_skipped_targets(readiness_packet)
    freshness_reviews = _collect_freshness_reviews(freshness_review_packet)
    packet = {
        'schema_version': 1,
        'checklist_id': _checklist_id(targets, generated_at),
        'generated_at': generated_at,
        'operator_role': operator_role,
        'source_packets': {
            'readiness_packet_id': str(readiness_packet.get('packet_id', 'processor-handoff-readiness-fixture')),
            'freshness_review_packet_id': str(freshness_review_packet.get('packet_id', 'public-source-freshness-review-fixture')),
        },
        'prerequisite_links': _collect_prerequisite_links(readiness_packet, freshness_review_packet),
        'handoff_targets': targets,
        'manual_operator_prompts': _manual_prompts(targets, skipped_targets, freshness_reviews),
        'expected_manifest_ids': [_expected_manifest_id(target) for target in targets],
        'processor_capability_prerequisites': list(DEFAULT_PROCESSOR_CAPABILITIES),
        'no_raw_body_attestations': {
            'readiness_packet_attests_no_raw_body': _readiness_attests_no_raw_body(readiness_packet),
            'checklist_persists_raw_body': False,
            'operator_prompt': 'Confirm the later processor run remains metadata-only and does not persist raw response bodies.',
        },
        'skipped_target_reasons': skipped_targets,
        'rate_limit_cautions': _rate_limit_cautions(targets),
        'freshness_review_prompts': _freshness_prompts(freshness_reviews),
        'abort_conditions': list(DEFAULT_ABORT_CONDITIONS),
        'processor_invocation': {
            'allowed': False,
            'status': 'manual_checklist_only',
            'operator_instruction': 'Do not run processors from this checklist artifact.',
        },
        'archive_artifact_writes': {'allowed': False, 'status': 'no_archive_artifacts_written'},
        'validation_summary': {
            'readiness_ok': readiness.ok,
            'readiness_issue_codes': [issue.code for issue in readiness.issues],
            'freshness_review_count': len(freshness_reviews),
            'target_count': len(targets),
            'skipped_target_count': len(skipped_targets),
        },
    }
    issues = validate_processor_handoff_operator_checklist(packet)
    if issues:
        raise ValueError('processor handoff operator checklist failed validation: ' + _render_issues(issues))
    return packet


def validate_processor_handoff_operator_checklist(packet: Mapping[str, Any]) -> list[OperatorChecklistIssue]:
    if not isinstance(packet, Mapping):
        return [OperatorChecklistIssue('invalid_packet', 'checklist must be a mapping')]

    issues: list[OperatorChecklistIssue] = []
    if packet.get('schema_version') != 1:
        issues.append(OperatorChecklistIssue('invalid_schema_version', 'schema_version must be 1', '$.schema_version'))
    if not _non_empty_list(packet.get('prerequisite_links')):
        issues.append(OperatorChecklistIssue('missing_prerequisite_links', 'prerequisite links are required', '$.prerequisite_links'))
    else:
        _validate_public_url_entries(packet.get('prerequisite_links'), '$.prerequisite_links', issues)
    if not _non_empty_list(packet.get('handoff_targets')):
        issues.append(OperatorChecklistIssue('missing_handoff_targets', 'handoff targets are required', '$.handoff_targets'))
    else:
        _validate_public_url_entries(packet.get('handoff_targets'), '$.handoff_targets', issues)
    if not _non_empty_list(packet.get('manual_operator_prompts')):
        issues.append(OperatorChecklistIssue('missing_manual_prompts', 'manual operator prompts are required', '$.manual_operator_prompts'))
    if not _non_empty_list(packet.get('expected_manifest_ids')):
        issues.append(OperatorChecklistIssue('missing_expected_manifest_ids', 'expected manifest IDs are required', '$.expected_manifest_ids'))
    if not _non_empty_list(packet.get('processor_capability_prerequisites')):
        issues.append(OperatorChecklistIssue('missing_processor_capability_prerequisites', 'processor capability prerequisites are required', '$.processor_capability_prerequisites'))
    if not _non_empty_list(packet.get('abort_conditions')):
        issues.append(OperatorChecklistIssue('missing_abort_conditions', 'abort conditions are required', '$.abort_conditions'))

    attestations = packet.get('no_raw_body_attestations')
    if not isinstance(attestations, Mapping) or attestations.get('checklist_persists_raw_body') is not False:
        issues.append(OperatorChecklistIssue('missing_no_raw_body_attestation', 'checklist must attest that it does not persist raw bodies', '$.no_raw_body_attestations'))
    if not isinstance(attestations, Mapping) or attestations.get('readiness_packet_attests_no_raw_body') is not True:
        issues.append(OperatorChecklistIssue('missing_readiness_no_raw_body_attestation', 'checklist must carry the readiness packet no-raw-body attestation', '$.no_raw_body_attestations.readiness_packet_attests_no_raw_body'))

    skipped = packet.get('skipped_target_reasons')
    if not _non_empty_list(skipped):
        issues.append(OperatorChecklistIssue('missing_skipped_target_reasons', 'skipped target reasons are required', '$.skipped_target_reasons'))
    elif isinstance(skipped, list):
        for index, entry in enumerate(skipped):
            if not isinstance(entry, Mapping) or not _has_value(entry.get('reason')):
                issues.append(OperatorChecklistIssue('missing_skipped_target_reason', 'each skipped target must include a reason', f'$.skipped_target_reasons[{index}].reason'))

    invocation = packet.get('processor_invocation')
    if not isinstance(invocation, Mapping) or invocation.get('allowed') is not False:
        issues.append(OperatorChecklistIssue('processor_invocation_allowed', 'operator checklist must explicitly disallow processor invocation', '$.processor_invocation.allowed'))
    archive_writes = packet.get('archive_artifact_writes')
    if not isinstance(archive_writes, Mapping) or archive_writes.get('allowed') is not False:
        issues.append(OperatorChecklistIssue('archive_artifact_writes_allowed', 'operator checklist must explicitly disallow archive artifact writes', '$.archive_artifact_writes.allowed'))

    _scan_for_forbidden_claims(packet, '$', issues)
    return _dedupe_issues(issues)


def assert_processor_handoff_operator_checklist_is_safe(packet: Mapping[str, Any]) -> None:
    issues = validate_processor_handoff_operator_checklist(packet)
    if issues:
        raise ValueError(_render_issues(issues))


def issue_codes(issues: Iterable[OperatorChecklistIssue]) -> set[str]:
    return {issue.code for issue in issues}


def _collect_prerequisite_links(*packets: Mapping[str, Any]) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    for packet in packets:
        for index, entry in enumerate(_collect_entries(packet, PREREQUISITE_KEYS)):
            url = _entry_url(entry)
            if url:
                links.append({'source_id': _entry_source_id(entry) or f'prerequisite-{len(links) + index + 1:03d}', 'url': url, 'host': _host(url)})
    return links


def _collect_targets(packet: Mapping[str, Any]) -> list[dict[str, str]]:
    targets: list[dict[str, str]] = []
    for index, entry in enumerate(_collect_entries(packet, TARGET_KEYS)):
        url = _entry_url(entry)
        if url:
            source_id = _entry_source_id(entry) or f'target-{index + 1:03d}'
            targets.append({'source_id': source_id, 'url': url, 'host': _host(url)})
    return targets


def _collect_skipped_targets(packet: Mapping[str, Any]) -> list[dict[str, str]]:
    skipped: list[dict[str, str]] = []
    for index, entry in enumerate(_collect_entries(packet, SKIPPED_KEYS)):
        if not isinstance(entry, Mapping):
            continue
        reason = ''
        for key in SKIP_REASON_KEYS:
            value = entry.get(key)
            if isinstance(value, str) and value.strip():
                reason = value.strip()
                break
        skipped.append({'target_id': _entry_source_id(entry) or f'skipped-{index + 1:03d}', 'url': _entry_url(entry) or 'unknown', 'reason': reason or 'operator review required before handoff'})
    return skipped


def _collect_freshness_reviews(packet: Mapping[str, Any]) -> list[dict[str, str]]:
    reviews: list[dict[str, str]] = []
    for index, entry in enumerate(_collect_entries(packet, FRESHNESS_SOURCE_KEYS)):
        if isinstance(entry, Mapping):
            reviews.append({
                'source_id': _entry_source_id(entry) or f'freshness-{index + 1:03d}',
                'url': _entry_url(entry) or 'unknown',
                'freshness_status': _first_text(entry, ('freshness_status', 'freshnessStatus', 'status')) or 'unknown',
                'reviewed_at': _first_text(entry, ('reviewed_at', 'reviewedAt', 'last_reviewed_at')) or 'unreviewed',
            })
    return reviews


def _manual_prompts(targets: Sequence[Mapping[str, str]], skipped_targets: Sequence[Mapping[str, str]], freshness_reviews: Sequence[Mapping[str, str]]) -> list[str]:
    prompts = [
        'Review each target URL against the readiness packet before any processor runner is opened.',
        'Confirm expected manifest IDs are placeholders for later metadata manifests, not existing archive artifacts.',
        'Confirm processor prerequisites are satisfied by the later runner while this checklist remains side-effect free.',
        'Confirm persistRawBody=false, downloadDocuments=false, and no screenshots, HAR files, traces, or WARC files are requested.',
    ]
    for target in targets:
        prompts.append(f"Confirm target {target['source_id']} remains public and ready for metadata-only processor handoff: {target['url']}")
    for skipped in skipped_targets:
        prompts.append(f"Confirm skipped target {skipped['target_id']} stays out of processor handoff because: {skipped['reason']}")
    for review in freshness_reviews:
        prompts.append(f"Confirm freshness review for {review['source_id']} is acceptable before handoff; status={review['freshness_status']}.")
    return prompts


def _freshness_prompts(freshness_reviews: Sequence[Mapping[str, str]]) -> list[str]:
    prompts = [f"Check freshness status for {review['source_id']} at {review['url']}; reviewed_at={review['reviewed_at']}." for review in freshness_reviews]
    return prompts or ['Confirm a public source freshness review packet exists before handoff continues.']


def _rate_limit_cautions(targets: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    hosts = sorted({target.get('host', 'unknown') for target in targets if target.get('host')})
    return [{'bucket': f'public-host:{host}', 'caution': 'Use the public crawl policy rate limit for this host; do not retry aggressively or bypass robots/policy decisions.'} for host in hosts]


def _expected_manifest_id(target: Mapping[str, str]) -> str:
    return f"ppd-processor-manifest-{_slug(target.get('source_id', 'target'))}"


def _checklist_id(targets: Sequence[Mapping[str, str]], generated_at: str) -> str:
    first = _slug(targets[0]['source_id']) if targets else 'empty'
    return f"processor-handoff-operator-checklist-{first}-{_slug(generated_at.replace('Z', ''))}"


def _readiness_attests_no_raw_body(packet: Mapping[str, Any]) -> bool:
    attestations = packet.get('attestations')
    if packet.get('no_raw_body_persisted') is True or packet.get('no_raw_body_attestation') is True:
        return True
    if isinstance(attestations, Mapping):
        return attestations.get('no_raw_body_persisted') is True or attestations.get('no_raw_body_attestation') is True
    return False


def _collect_entries(packet: Mapping[str, Any], keys: Sequence[str]) -> list[Any]:
    entries: list[Any] = []
    for key in keys:
        value = packet.get(key)
        if value is None:
            continue
        if isinstance(value, Mapping) or isinstance(value, str):
            entries.append(value)
        elif isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
            entries.extend(value)
    return entries


def _entry_url(entry: Any) -> str | None:
    if isinstance(entry, str):
        return entry.strip() or None
    if isinstance(entry, Mapping):
        for key in URL_KEYS:
            value = entry.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None


def _entry_source_id(entry: Any) -> str | None:
    if isinstance(entry, Mapping):
        for key in SOURCE_ID_KEYS:
            value = entry.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None


def _first_text(entry: Mapping[str, Any], keys: Sequence[str]) -> str | None:
    for key in keys:
        value = entry.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _validate_public_url_entries(value: Any, path: str, issues: list[OperatorChecklistIssue]) -> None:
    if not isinstance(value, list):
        return
    for index, entry in enumerate(value):
        url = _entry_url(entry)
        entry_path = f'{path}[{index}]'
        if not url:
            issues.append(OperatorChecklistIssue('missing_target_url', 'URL is required', entry_path))
            continue
        parsed = urlparse(url)
        host = parsed.hostname.lower() if parsed.hostname else ''
        lowered_path = parsed.path.lower()
        if parsed.scheme != 'https' or not host:
            issues.append(OperatorChecklistIssue('invalid_public_target_url', 'target URLs must be absolute HTTPS URLs', entry_path))
        if host not in ALLOWLISTED_HOSTS:
            issues.append(OperatorChecklistIssue('non_allowlisted_target', 'target host is outside the PP&D public allowlist', entry_path))
        if parsed.username or parsed.password or any(marker in lowered_path for marker in PRIVATE_PATH_MARKERS):
            issues.append(OperatorChecklistIssue('private_or_authenticated_target', 'target appears private, authenticated, or account-scoped', entry_path))
        if any(marker in lowered_path for marker in RAW_DOWNLOAD_ARCHIVE_MARKERS):
            issues.append(OperatorChecklistIssue('raw_download_or_archive_target', 'target must not be a raw crawl, download, or archive reference', entry_path))


def _scan_for_forbidden_claims(value: Any, path: str, issues: list[OperatorChecklistIssue]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized = key_text.strip().lower().replace('-', '_')
            child_path = f'{path}.{key_text}'
            if normalized in FORBIDDEN_TRUE_KEYS and child is True:
                issues.append(OperatorChecklistIssue('forbidden_execution_or_archive_write_claim', 'checklist must not enable live processor execution or archive artifact writes', child_path))
            if normalized in FORBIDDEN_VALUE_KEYS and _has_value(child):
                issues.append(OperatorChecklistIssue('forbidden_raw_or_archive_reference', 'checklist must not contain raw body, downloaded document, trace, HAR, screenshot, WARC, or archive artifact references', child_path))
            if isinstance(child, str) and normalized in {'status', 'state', 'result'} and child.strip().lower() in FORBIDDEN_STATUS_VALUES:
                issues.append(OperatorChecklistIssue('forbidden_execution_or_archive_write_claim', 'checklist must not claim live processor execution or produced archive artifacts', child_path))
            _scan_for_forbidden_claims(child, child_path, issues)
    elif isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        for index, child in enumerate(value):
            _scan_for_forbidden_claims(child, f'{path}[{index}]', issues)


def _host(url: str) -> str:
    parsed = urlparse(url)
    return parsed.hostname.lower() if parsed.hostname else 'unknown'


def _slug(value: str) -> str:
    chars: list[str] = []
    previous_dash = False
    for char in value.strip().lower():
        if char.isalnum():
            chars.append(char)
            previous_dash = False
        elif not previous_dash:
            chars.append('-')
            previous_dash = True
    return ''.join(chars).strip('-') or 'unknown'


def _non_empty_list(value: Any) -> bool:
    return isinstance(value, list) and any(_has_value(item) for item in value)


def _has_value(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return bool(value)
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        return bool(value)
    return True


def _dedupe_issues(issues: Sequence[OperatorChecklistIssue]) -> list[OperatorChecklistIssue]:
    seen: set[tuple[str, str]] = set()
    unique: list[OperatorChecklistIssue] = []
    for issue in issues:
        key = (issue.code, issue.path)
        if key not in seen:
            seen.add(key)
            unique.append(issue)
    return unique


def _render_issues(issues: Sequence[OperatorChecklistIssue]) -> str:
    return '; '.join(f'{issue.code} at {issue.path}: {issue.message}' for issue in issues)
