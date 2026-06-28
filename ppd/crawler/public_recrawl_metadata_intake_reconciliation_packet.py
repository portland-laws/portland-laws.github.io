from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping, Sequence
from urllib.parse import urlsplit

from ppd.crawler.processor_handoff_rehearsal_packet import PACKET_TYPE as HANDOFF_PACKET_TYPE
from ppd.source_registry_coverage_gap_packet import PACKET_TYPE as COVERAGE_GAP_PACKET_TYPE

PACKET_TYPE = 'ppd_public_recrawl_metadata_intake_reconciliation_packet'
SCHEMA_VERSION = 1
MODE = 'fixture_first_public_recrawl_metadata_intake_reconciliation'

_ALLOWED_HOSTS = {'www.portland.gov', 'devhub.portlandoregon.gov', 'www.portlandoregon.gov', 'www.portlandmaps.com'}
_PRIVATE_TARGET_MARKERS = ('/account', '/admin', '/api/private', '/dashboard', '/login', '/my-permits', '/private', '/signin', '/sign-in', '/user/', 'auth=', 'session=', 'token=')
_FORBIDDEN_TRUE_KEYS = {'activeRegistryMutated', 'activeRegistryWriteAllowed', 'activeRegistryWritesAllowed', 'activeSourceRegistryMutated', 'archiveArtifactRefPresent', 'archiveArtifactWriteAllowed', 'archiveArtifactWritesAllowed', 'archiveArtifactWritten', 'archiveMutationAllowed', 'archiveWriteAllowed', 'documentsDownloaded', 'downloadedDocuments', 'fetchedLive', 'liveFetchClaimed', 'liveFetchUsed', 'liveNetworkUsed', 'processorExecuted', 'processorExecutionClaimed', 'processorInvocationAllowed', 'processorInvoked', 'rawBodiesPersisted', 'rawBodyPersisted', 'registryMutationAllowed'}
_FORBIDDEN_VALUE_MARKERS = ('auth_state', 'bearer ', 'cookies.json', 'credential', 'download_ref', 'download_url', 'downloaded_document', 'downloaded_documents', 'file://', 'localstorage.json', 'password', 'raw body', 'raw_body', 'raw_html', 'response_body', 's3://', 'session_cookie', 'storage_state', 'trace.zip', 'warc://')


@dataclass(frozen=True)
class PublicRecrawlMetadataIntakeReconciliationValidationResult:
    valid: bool
    errors: tuple[str, ...]


class PublicRecrawlMetadataIntakeReconciliationPacketError(ValueError):
    pass


def build_public_recrawl_metadata_intake_reconciliation_packet(processor_handoff_manifest_rehearsal_packet: Mapping[str, Any], public_source_registry_coverage_gap_packet: Mapping[str, Any], *, generated_at: str) -> dict[str, Any]:
    handoff_packet = deepcopy(dict(processor_handoff_manifest_rehearsal_packet))
    coverage_packet = deepcopy(dict(public_source_registry_coverage_gap_packet))
    _require_consumable_input_packets(handoff_packet, coverage_packet)
    manifests_by_source = {_text(row.get('source_id')): row for row in _sequence(handoff_packet.get('expectedMetadataOnlyArchiveManifests')) if isinstance(row, Mapping) and _text(row.get('source_id'))}
    prerequisites_by_source = {_text(row.get('source_id')): row for row in _sequence(handoff_packet.get('syntheticProcessorPrerequisites')) if isinstance(row, Mapping) and _text(row.get('source_id'))}
    intake_rows: list[dict[str, Any]] = []
    manifest_refs: list[dict[str, Any]] = []
    missing_manifest_aborts: list[dict[str, Any]] = []
    for source in _sequence(coverage_packet.get('citedCoveredAnchors')):
        if not isinstance(source, Mapping):
            continue
        source_id = _text(source.get('source_id'))
        canonical_url = _text(source.get('canonical_url'))
        manifest = manifests_by_source.get(source_id)
        prerequisite = prerequisites_by_source.get(source_id, {})
        if manifest is None:
            missing_manifest_aborts.append({'abort_id': 'missing-expected-manifest-' + _stable_token(source_id or canonical_url), 'source_id': source_id, 'canonical_url': canonical_url, 'note': 'Abort because the covered source has no expected metadata-only manifest reference in the processor handoff rehearsal packet.', 'abortBeforeLiveFetch': True, 'processorInvocationAllowed': False})
            continue
        manifest_id = _text(manifest.get('manifest_id'))
        intake_rows.append({'intake_id': 'metadata-intake-' + _stable_token(source_id or canonical_url), 'source_id': source_id, 'canonical_url': canonical_url, 'requested_url': _text(prerequisite.get('requested_url'), canonical_url), 'source_evidence_ids': _text_list(source.get('source_evidence_ids')), 'freshness_badge_id': _text(source.get('freshness_badge_id')), 'expected_manifest_id': manifest_id, 'normalized_document_id': _text(manifest.get('normalized_document_id')), 'content_type': _text(manifest.get('content_type'), 'expected_metadata_only_pending_capture'), 'http_status': _text(manifest.get('http_status'), 'expected_metadata_only_not_fetched'), 'intake_status': 'ready_for_metadata_only_rehearsal', 'fixtureSynthetic': True, 'metadataOnly': True, 'liveFetchUsed': False, 'processorInvoked': False, 'archiveArtifactWritten': False, 'noRawBodyPersisted': True})
        manifest_refs.append({'manifest_ref_id': 'manifest-ref-' + _stable_token(manifest_id), 'manifest_id': manifest_id, 'source_id': source_id, 'canonical_url': canonical_url, 'normalized_document_id': _text(manifest.get('normalized_document_id')), 'archive_artifact_ref_present': False, 'metadataOnly': True})
    review_queues = _changed_source_review_queues(coverage_packet)
    badge_candidates = _freshness_badge_update_candidates(coverage_packet)
    abort_notes = _abort_notes(handoff_packet, coverage_packet, missing_manifest_aborts)
    packet = {'schemaVersion': SCHEMA_VERSION, 'packetType': PACKET_TYPE, 'mode': MODE, 'generatedAt': generated_at, 'fixtureFirst': True, 'metadataOnly': True, 'liveNetworkUsed': False, 'fetchedLive': False, 'processorInvoked': False, 'archiveArtifactWritten': False, 'rawBodiesPersisted': False, 'documentsDownloaded': False, 'activeRegistryMutated': False, 'inputPacketRefs': {'processorHandoffPacketType': _text(handoff_packet.get('packetType')), 'processorHandoffMode': _text(handoff_packet.get('mode')), 'coverageGapPacketType': _text(coverage_packet.get('packetType')), 'coverageGapSourceMode': _text(coverage_packet.get('sourceMode'))}, 'syntheticMetadataOnlyIntakeRows': intake_rows, 'expectedManifestReferences': manifest_refs, 'changedSourceReviewQueues': review_queues, 'freshnessBadgeUpdateCandidates': badge_candidates, 'abortNotes': abort_notes, 'reconciliationSummary': {'syntheticIntakeRowCount': len(intake_rows), 'expectedManifestReferenceCount': len(manifest_refs), 'changedSourceReviewQueueCount': len(review_queues), 'freshnessBadgeUpdateCandidateCount': len(badge_candidates), 'abortNoteCount': len(abort_notes), 'liveNetworkUsed': False, 'processorInvoked': False, 'archiveArtifactWritten': False}}
    require_valid_public_recrawl_metadata_intake_reconciliation_packet(packet)
    return packet


def validate_public_recrawl_metadata_intake_reconciliation_packet(packet: Mapping[str, Any]) -> PublicRecrawlMetadataIntakeReconciliationValidationResult:
    errors: list[str] = []
    _collect_forbidden_content(packet, '$', errors)
    _collect_url_like_values(packet, '$', errors)
    if packet.get('schemaVersion') != SCHEMA_VERSION:
        errors.append('schemaVersion must be 1')
    if packet.get('packetType') != PACKET_TYPE:
        errors.append('packetType must be ' + PACKET_TYPE)
    if packet.get('mode') != MODE:
        errors.append('mode must be ' + MODE)
    if not str(packet.get('generatedAt', '')).endswith('Z'):
        errors.append('generatedAt must be an ISO UTC timestamp ending in Z')
    for key in ('fixtureFirst', 'metadataOnly'):
        if packet.get(key) is not True:
            errors.append(f'{key} must be true')
    for key in ('liveNetworkUsed', 'fetchedLive', 'processorInvoked', 'archiveArtifactWritten', 'rawBodiesPersisted', 'documentsDownloaded', 'activeRegistryMutated'):
        if packet.get(key) is not False:
            errors.append(f'{key} must be false')
    rows = _require_list(packet.get('syntheticMetadataOnlyIntakeRows'), 'syntheticMetadataOnlyIntakeRows', errors)
    refs = _require_list(packet.get('expectedManifestReferences'), 'expectedManifestReferences', errors)
    queues = _require_list(packet.get('changedSourceReviewQueues'), 'changedSourceReviewQueues', errors)
    candidates = _require_list(packet.get('freshnessBadgeUpdateCandidates'), 'freshnessBadgeUpdateCandidates', errors)
    aborts = _require_list(packet.get('abortNotes'), 'abortNotes', errors)
    intake_manifest_ids = _validate_intake_rows(rows, errors)
    ref_manifest_ids = _validate_manifest_refs(refs, errors)
    _validate_review_queues(queues, errors)
    _validate_badge_candidates(candidates, errors)
    _validate_abort_notes(aborts, errors)
    if not rows:
        errors.append('syntheticMetadataOnlyIntakeRows must include at least one row')
    if intake_manifest_ids != ref_manifest_ids:
        errors.append('expectedManifestReferences must match intake expected_manifest_id values')
    if not queues:
        errors.append('changedSourceReviewQueues must include stale or missing source review work')
    if not candidates:
        errors.append('freshnessBadgeUpdateCandidates must include at least one stale source candidate')
    if not aborts:
        errors.append('abortNotes must include handoff, coverage, and policy abort notes')
    _validate_abort_note_coverage(aborts, errors)
    summary = packet.get('reconciliationSummary')
    if not isinstance(summary, Mapping):
        errors.append('reconciliationSummary must be an object')
    else:
        expected_counts = {'syntheticIntakeRowCount': len(rows), 'expectedManifestReferenceCount': len(refs), 'changedSourceReviewQueueCount': len(queues), 'freshnessBadgeUpdateCandidateCount': len(candidates), 'abortNoteCount': len(aborts)}
        for key, expected in expected_counts.items():
            if summary.get(key) != expected:
                errors.append(f'reconciliationSummary.{key} must be {expected}')
        for key in ('liveNetworkUsed', 'processorInvoked', 'archiveArtifactWritten'):
            if summary.get(key) is not False:
                errors.append(f'reconciliationSummary.{key} must be false')
    return PublicRecrawlMetadataIntakeReconciliationValidationResult(valid=not errors, errors=tuple(errors))


def require_valid_public_recrawl_metadata_intake_reconciliation_packet(packet: Mapping[str, Any]) -> None:
    result = validate_public_recrawl_metadata_intake_reconciliation_packet(packet)
    if not result.valid:
        raise PublicRecrawlMetadataIntakeReconciliationPacketError('; '.join(result.errors))


def _require_consumable_input_packets(handoff_packet: Mapping[str, Any], coverage_packet: Mapping[str, Any]) -> None:
    errors: list[str] = []
    if handoff_packet.get('packetType') != HANDOFF_PACKET_TYPE:
        errors.append('processor handoff input packetType must be ' + HANDOFF_PACKET_TYPE)
    if coverage_packet.get('packetType') != COVERAGE_GAP_PACKET_TYPE:
        errors.append('coverage input packetType must be ' + COVERAGE_GAP_PACKET_TYPE)
    for packet_name, packet in (('processor handoff', handoff_packet), ('coverage gap', coverage_packet)):
        _collect_forbidden_content(packet, packet_name, errors)
        if packet.get('fixtureFirst') is not True:
            errors.append(packet_name + ' packet must be fixtureFirst')
        if packet.get('metadataOnly') is not True:
            errors.append(packet_name + ' packet must be metadataOnly')
    if not _sequence(handoff_packet.get('expectedMetadataOnlyArchiveManifests')):
        errors.append('processor handoff packet must include expectedMetadataOnlyArchiveManifests')
    if not _sequence(coverage_packet.get('citedCoveredAnchors')):
        errors.append('coverage gap packet must include citedCoveredAnchors')
    if errors:
        raise PublicRecrawlMetadataIntakeReconciliationPacketError('; '.join(errors))


def _changed_source_review_queues(coverage_packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in _sequence(coverage_packet.get('staleSourceNotes')):
        if isinstance(source, Mapping):
            source_id = _text(source.get('source_id'))
            canonical_url = _text(source.get('canonical_url'))
            rows.append({'queue_id': 'changed-source-review-' + _stable_token(source_id or canonical_url), 'source_id': source_id, 'canonical_url': canonical_url, 'queue_reason': 'stale_freshness_badge', 'freshness_status': _text(source.get('freshness_status')), 'reviewer_owner': _text(source.get('reviewer_owner')), 'source_evidence_ids': _text_list(source.get('source_evidence_ids')), 'changedSourceReviewRequired': True, 'activeRegistryWriteAllowed': False})
    for source in _sequence(coverage_packet.get('missingAnchors')):
        if isinstance(source, Mapping):
            source_id = _text(source.get('source_id'))
            canonical_url = _text(source.get('canonical_url'))
            rows.append({'queue_id': 'missing-source-review-' + _stable_token(source_id or canonical_url), 'source_id': source_id, 'canonical_url': canonical_url, 'queue_reason': _text(source.get('missing_reason'), 'missing_anchor'), 'freshness_status': 'missing_or_uncited', 'reviewer_owner': _text(source.get('reviewer_owner')), 'source_evidence_ids': _text_list(source.get('source_evidence_ids')), 'changedSourceReviewRequired': True, 'activeRegistryWriteAllowed': False})
    return rows


def _freshness_badge_update_candidates(coverage_packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in _sequence(coverage_packet.get('staleSourceNotes')):
        if isinstance(source, Mapping):
            source_id = _text(source.get('source_id'))
            canonical_url = _text(source.get('canonical_url'))
            rows.append({'candidate_id': 'freshness-badge-candidate-' + _stable_token(source_id or canonical_url), 'source_id': source_id, 'canonical_url': canonical_url, 'current_freshness_status': _text(source.get('freshness_status'), 'unknown'), 'proposed_next_status': 'needs_review_before_recrawl', 'source_evidence_ids': _text_list(source.get('source_evidence_ids')), 'reviewer_owner': _text(source.get('reviewer_owner')), 'updateRequiresHumanReview': True, 'activeRegistryWriteAllowed': False})
    return rows


def _abort_notes(handoff_packet: Mapping[str, Any], coverage_packet: Mapping[str, Any], missing_manifest_aborts: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, abort in enumerate(_sequence(handoff_packet.get('abortConditions')), start=1):
        if isinstance(abort, Mapping):
            rows.append({'abort_id': _text(abort.get('abort_id'), f'processor-handoff-abort-{index:02d}'), 'source': 'processor_handoff_manifest_rehearsal_packet', 'note': _text(abort.get('condition'), 'Processor handoff rehearsal abort condition.'), 'abortBeforeLiveFetch': True, 'processorInvocationAllowed': False, 'archiveArtifactWriteAllowed': False})
    for source in _sequence(coverage_packet.get('missingAnchors')):
        if isinstance(source, Mapping):
            source_id = _text(source.get('source_id'))
            canonical_url = _text(source.get('canonical_url'))
            rows.append({'abort_id': 'coverage-gap-missing-anchor-' + _stable_token(source_id or canonical_url), 'source': 'public_source_registry_coverage_gap_packet', 'source_id': source_id, 'canonical_url': canonical_url, 'note': _text(source.get('missing_reason'), 'Missing source coverage blocks live recrawl promotion.'), 'abortBeforeLiveFetch': True, 'processorInvocationAllowed': False, 'archiveArtifactWriteAllowed': False})
    rows.extend(dict(row) for row in missing_manifest_aborts)
    rows.append({'abort_id': 'fixture-reconciliation-live-fetch-requested', 'source': 'public_recrawl_metadata_intake_reconciliation_policy', 'note': 'Abort this packet if any implementation attempts live fetches, processor invocation, registry mutation, document download, or archive artifact writes.', 'abortBeforeLiveFetch': True, 'processorInvocationAllowed': False, 'archiveArtifactWriteAllowed': False})
    return rows


def _validate_intake_rows(rows: Sequence[Any], errors: list[str]) -> set[str]:
    manifest_ids: set[str] = set()
    seen: set[str] = set()
    for index, row in enumerate(rows):
        prefix = f'syntheticMetadataOnlyIntakeRows[{index}]'
        if not isinstance(row, Mapping):
            errors.append(prefix + ' must be an object')
            continue
        for key in ('intake_id', 'source_id', 'canonical_url', 'requested_url', 'expected_manifest_id', 'normalized_document_id', 'intake_status'):
            if not _text(row.get(key)):
                errors.append(f'{prefix}.{key} is required')
        intake_id = _text(row.get('intake_id'))
        if intake_id in seen:
            errors.append(f'{prefix}.intake_id must be unique')
        seen.add(intake_id)
        manifest_id = _text(row.get('expected_manifest_id'))
        if manifest_id:
            manifest_ids.add(manifest_id)
        _validate_public_url(_text(row.get('canonical_url')), prefix + '.canonical_url', errors)
        _validate_public_url(_text(row.get('requested_url')), prefix + '.requested_url', errors)
        if not _text_list(row.get('source_evidence_ids')):
            errors.append(f'{prefix}.source_evidence_ids must cite at least one evidence id')
        for key in ('fixtureSynthetic', 'metadataOnly', 'noRawBodyPersisted'):
            if row.get(key) is not True:
                errors.append(f'{prefix}.{key} must be true')
        for key in ('liveFetchUsed', 'processorInvoked', 'archiveArtifactWritten'):
            if row.get(key) is not False:
                errors.append(f'{prefix}.{key} must be false')
    return manifest_ids


def _validate_manifest_refs(rows: Sequence[Any], errors: list[str]) -> set[str]:
    manifest_ids: set[str] = set()
    for index, row in enumerate(rows):
        prefix = f'expectedManifestReferences[{index}]'
        if not isinstance(row, Mapping):
            errors.append(prefix + ' must be an object')
            continue
        for key in ('manifest_ref_id', 'manifest_id', 'source_id', 'canonical_url', 'normalized_document_id'):
            if not _text(row.get(key)):
                errors.append(f'{prefix}.{key} is required')
        manifest_id = _text(row.get('manifest_id'))
        if manifest_id:
            manifest_ids.add(manifest_id)
        _validate_public_url(_text(row.get('canonical_url')), prefix + '.canonical_url', errors)
        if row.get('archive_artifact_ref_present') is not False:
            errors.append(f'{prefix}.archive_artifact_ref_present must be false')
        if row.get('metadataOnly') is not True:
            errors.append(f'{prefix}.metadataOnly must be true')
    return manifest_ids


def _validate_review_queues(rows: Sequence[Any], errors: list[str]) -> None:
    for index, row in enumerate(rows):
        prefix = f'changedSourceReviewQueues[{index}]'
        if not isinstance(row, Mapping):
            errors.append(prefix + ' must be an object')
            continue
        for key in ('queue_id', 'source_id', 'canonical_url', 'queue_reason', 'freshness_status', 'reviewer_owner'):
            if not _text(row.get(key)):
                errors.append(f'{prefix}.{key} is required')
        _validate_public_url(_text(row.get('canonical_url')), prefix + '.canonical_url', errors)
        if row.get('changedSourceReviewRequired') is not True:
            errors.append(f'{prefix}.changedSourceReviewRequired must be true')
        if row.get('activeRegistryWriteAllowed') is not False:
            errors.append(f'{prefix}.activeRegistryWriteAllowed must be false')


def _validate_badge_candidates(rows: Sequence[Any], errors: list[str]) -> None:
    for index, row in enumerate(rows):
        prefix = f'freshnessBadgeUpdateCandidates[{index}]'
        if not isinstance(row, Mapping):
            errors.append(prefix + ' must be an object')
            continue
        for key in ('candidate_id', 'source_id', 'canonical_url', 'current_freshness_status', 'proposed_next_status', 'reviewer_owner'):
            if not _text(row.get(key)):
                errors.append(f'{prefix}.{key} is required')
        _validate_public_url(_text(row.get('canonical_url')), prefix + '.canonical_url', errors)
        if not _text_list(row.get('source_evidence_ids')):
            errors.append(f'{prefix}.source_evidence_ids must cite at least one evidence id')
        if row.get('updateRequiresHumanReview') is not True:
            errors.append(f'{prefix}.updateRequiresHumanReview must be true')
        if row.get('activeRegistryWriteAllowed') is not False:
            errors.append(f'{prefix}.activeRegistryWriteAllowed must be false')


def _validate_abort_notes(rows: Sequence[Any], errors: list[str]) -> None:
    for index, row in enumerate(rows):
        prefix = f'abortNotes[{index}]'
        if not isinstance(row, Mapping):
            errors.append(prefix + ' must be an object')
            continue
        for key in ('abort_id', 'note'):
            if not _text(row.get(key)):
                errors.append(f'{prefix}.{key} is required')
        if row.get('abortBeforeLiveFetch') is not True:
            errors.append(f'{prefix}.abortBeforeLiveFetch must be true')
        if row.get('processorInvocationAllowed') is not False:
            errors.append(f'{prefix}.processorInvocationAllowed must be false')
        if 'archiveArtifactWriteAllowed' in row and row.get('archiveArtifactWriteAllowed') is not False:
            errors.append(f'{prefix}.archiveArtifactWriteAllowed must be false')


def _validate_abort_note_coverage(rows: Sequence[Any], errors: list[str]) -> None:
    combined = ' '.join(' '.join(_text(row.get(key)) for key in ('abort_id', 'note', 'source')) for row in rows if isinstance(row, Mapping)).lower()
    for marker, message in {'live fetch': 'abortNotes must include a live-fetch abort note', 'processor': 'abortNotes must include a processor execution abort note', 'archive': 'abortNotes must include an archive mutation abort note'}.items():
        if marker not in combined:
            errors.append(message)


def _require_list(value: Any, field: str, errors: list[str]) -> list[Any]:
    if not isinstance(value, list):
        errors.append(f'{field} must be a list')
        return []
    return value


def _collect_forbidden_content(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if key_text in _FORBIDDEN_TRUE_KEYS and child not in (None, '', [], {}, False):
                errors.append(f'{path}.{key_text} must be false or empty')
            _collect_forbidden_content(child, f'{path}.{key_text}', errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _collect_forbidden_content(child, f'{path}[{index}]', errors)
    elif isinstance(value, str):
        lower_value = value.lower()
        for marker in _FORBIDDEN_VALUE_MARKERS:
            if marker in lower_value:
                errors.append(f'{path} contains forbidden private, raw, or artifact marker {marker}')


def _collect_url_like_values(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            _collect_url_like_values(child, f'{path}.{key}', errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _collect_url_like_values(child, f'{path}[{index}]', errors)
    elif isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith(('http://', 'https://')):
            _validate_public_url(stripped, path, errors)


def _validate_public_url(url: str, path: str, errors: list[str]) -> None:
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or parsed.netloc.lower() not in _ALLOWED_HOSTS:
        errors.append(path + ' must be an HTTPS allowlisted public URL')
    combined = (parsed.path + '?' + parsed.query).lower()
    if any(marker in combined for marker in _PRIVATE_TARGET_MARKERS):
        errors.append(path + ' must not be private or authenticated')


def _sequence(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []


def _text_list(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [_text(item) for item in value if _text(item)]


def _stable_token(value: str) -> str:
    lowered = value.strip().lower()
    chars = [character if character.isalnum() else '-' for character in lowered]
    return '-'.join(part for part in ''.join(chars).split('-') if part) or 'unknown'


def _text(value: Any, default: str = '') -> str:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else default
    return default


__all__ = ['PACKET_TYPE', 'PublicRecrawlMetadataIntakeReconciliationPacketError', 'PublicRecrawlMetadataIntakeReconciliationValidationResult', 'build_public_recrawl_metadata_intake_reconciliation_packet', 'require_valid_public_recrawl_metadata_intake_reconciliation_packet', 'validate_public_recrawl_metadata_intake_reconciliation_packet']
