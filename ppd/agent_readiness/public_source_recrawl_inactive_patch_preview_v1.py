from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

PACKET_VERSION = 'public_source_recrawl_inactive_patch_preview_v1'
REVIEWER_PACKET_VERSION = 'public_source_recrawl_reviewer_disposition_packet_v1'
DRY_RUN_MANIFEST_VERSION = 'public_source_recrawl_dry_run_manifest_v1'
APPROVED_DECISION = 'approve_for_metadata_only_recrawl'
INACTIVE_STATE = 'inactive_preview_only'
NOT_PROMOTED = 'not_promoted'

VALIDATION_COMMANDS = (
    ('python3', 'ppd/daemon/ppd_daemon.py', '--self-test'),
    ('python3', '-m', 'unittest', 'ppd.tests.test_public_source_recrawl_inactive_patch_preview_v1'),
)

FALSE_FLAGS = (
    'live_network_invoked',
    'crawl_executed',
    'recrawl_executed',
    'documents_downloaded',
    'payloads_stored',
    'raw_response_bodies_stored',
    'raw_crawl_data_stored',
    'pdf_payloads_stored',
    'devhub_accessed',
    'authenticated_session_used',
    'browser_artifacts_created',
    'active_artifacts_mutated',
    'active_source_artifacts_mutated',
    'active_archive_artifacts_mutated',
    'active_process_artifacts_mutated',
    'active_requirement_artifacts_mutated',
    'active_guardrail_artifacts_mutated',
    'active_prompt_artifacts_mutated',
    'active_release_state_mutated',
    'active_release_artifacts_mutated',
    'prompt_mutation_requested',
    'release_state_mutation_requested',
    'guardrail_mutation_requested',
)

UNSAFE_KEYS = {
    'auth_state_ref',
    'authenticated_session_ref',
    'browser_artifact_ref',
    'browser_trace_ref',
    'cookie_artifact_ref',
    'downloaded_data_ref',
    'downloaded_document_ref',
    'downloaded_documents',
    'downloaded_pdf_ref',
    'har_artifact_ref',
    'private_artifact_ref',
    'raw_crawl_artifact_ref',
    'raw_crawl_output_ref',
    'raw_download_ref',
    'raw_pdf_ref',
    'session_artifact_ref',
    'session_storage_ref',
}

UNSAFE_TEXT = {
    'private_or_session_artifact_claim': (
        'authenticated session',
        'auth state',
        'browser trace',
        'cookie jar',
        'devhub session',
        'har file',
        'private devhub',
        'session storage',
    ),
    'payload_or_download_claim': (
        'downloaded document',
        'downloaded pdf',
        'pdf payload',
        'raw crawl',
        'raw download',
        'raw response',
        'response body retained',
    ),
    'live_execution_claim': (
        'accessed devhub',
        'crawl was executed',
        'live crawl completed',
        'live devhub',
        'live network',
        'network request executed',
        'recrawl was executed',
    ),
    'consequential_devhub_action_language': (
        'cancel inspection',
        'certify acknowledgement',
        'final payment',
        'pay fee',
        'purchase permit',
        'schedule inspection',
        'submit application',
        'submit permit',
        'upload correction',
        'upload plans',
    ),
    'official_action_completion_claim': (
        'cancelled permit',
        'certified acknowledgement',
        'official action completed',
        'paid fee',
        'payment completed',
        'permit submitted',
        'scheduled inspection',
        'submitted application',
        'submitted permit',
        'uploaded correction',
        'withdrew permit',
    ),
    'legal_or_permitting_outcome_guarantee': (
        'approval is guaranteed',
        'approval guaranteed',
        'guarantee permit approval',
        'guaranteed permit',
        'legal advice',
        'legal determination',
        'permit will be approved',
        'will pass inspection',
    ),
    'active_promotion_claim': (
        'active archive promotion',
        'active source promotion',
        'promoted archive manifest',
        'promoted source registry',
        'promoted to active',
        'production promotion',
        'released to active',
    ),
    'active_mutation_claim': (
        'active artifact mutation',
        'active guardrail mutation',
        'active prompt mutation',
        'active release-state mutation',
        'mutate active artifact',
        'mutate guardrail',
        'mutate prompt',
        'mutate release state',
    ),
}

TEXT_SCAN_SKIP_SUFFIXES = (
    '.validation_commands',
    '.forbidden_artifacts',
)


@dataclass(frozen=True)
class PublicSourceRecrawlInactivePatchPreviewIssue:
    code: str
    path: str
    message: str


class PublicSourceRecrawlInactivePatchPreviewError(ValueError):
    def __init__(self, issues: Sequence[PublicSourceRecrawlInactivePatchPreviewIssue]) -> None:
        self.issues = tuple(issues)
        super().__init__('; '.join(f'{issue.path}: {issue.code}: {issue.message}' for issue in self.issues))


def build_public_source_recrawl_inactive_patch_preview_v1(disposition_packet: Mapping[str, Any]) -> dict[str, Any]:
    manifest_ref = disposition_packet.get('dry_run_manifest_ref')
    if not isinstance(manifest_ref, Mapping):
        manifest_ref = {}

    decisions = [row for row in _rows(disposition_packet.get('reviewer_decisions'))]
    approved = [row for row in decisions if _text(row.get('decision')) == APPROVED_DECISION]
    held = [row for row in decisions if _text(row.get('decision')) != APPROVED_DECISION]
    skipped_by_source = _skipped_reason_by_source(disposition_packet.get('skipped_source_explanations'))

    registry = []
    archive = []
    documents = []
    freshness = []
    for row in approved:
        source_id = _text(row.get('source_id'))
        url = _text(row.get('canonical_url'))
        registry.append({
            'delta_id': f'inactive-source-registry-delta-{source_id}',
            'source_id': source_id,
            'canonical_url': url,
            'inactive_patch_state': INACTIVE_STATE,
            'operation': 'metadata_placeholder_delta_after_future_review',
            'privacy_classification': 'public_metadata_only',
            'metadata_only_artifact_expectation_id': _text(row.get('metadata_only_artifact_expectation_id')),
            'active_source_promotion_state': NOT_PROMOTED,
        })
        archive.append({
            'delta_id': f'inactive-archive-manifest-delta-{source_id}',
            'source_id': source_id,
            'canonical_url': url,
            'inactive_patch_state': INACTIVE_STATE,
            'requested_url_placeholder': url,
            'redirect_chain_placeholder': ['pending_redirect_metadata_or_no_redirect'],
            'expected_http_status': 'pending_future_metadata_capture',
            'expected_content_type': 'pending_future_metadata_capture',
            'content_hash_placeholder': f'pending-content-hash-{source_id}',
            'processor_name_placeholder': 'pending_processor_suite_metadata_adapter',
            'normalized_document_id_placeholder': f'pending-normalized-document-{source_id}',
            'skipped_reason_handling': 'not_applicable_to_approved_metadata_only_preview',
            'no_raw_body_persisted': True,
            'no_payload_persisted': True,
            'active_archive_promotion_state': NOT_PROMOTED,
        })
        documents.append({
            'document_reference_id': f'inactive-normalized-document-ref-{source_id}',
            'source_id': source_id,
            'canonical_url': url,
            'inactive_patch_state': INACTIVE_STATE,
            'document_id_placeholder': f'pending-normalized-document-{source_id}',
            'title_placeholder': f'Pending normalized public document metadata for {source_id}',
            'citation_span_placeholder': f'citation-placeholder-{source_id}',
        })
        freshness.append({
            'replay_note_id': f'inactive-freshness-replay-note-{source_id}',
            'source_id': source_id,
            'source_freshness_update_placeholder_id': _text(row.get('source_freshness_update_placeholder_id')),
            'inactive_patch_state': INACTIVE_STATE,
            'expected_replay_note': 'Replay reviewer disposition and metadata placeholders before any later active gate.',
        })

    held_notes = []
    rollback_notes = []
    for row in held:
        source_id = _text(row.get('source_id'))
        skip_reason = skipped_by_source.get(source_id) or 'reviewer_hold_without_inactive_delta'
        held_notes.append({
            'source_id': source_id,
            'canonical_url': _text(row.get('canonical_url')),
            'decision': _text(row.get('decision')),
            'reason_codes': tuple(_string_list(row.get('reason_codes'))),
            'skipped_reason_code': skip_reason,
            'reviewer_hold_placeholder': f'Reviewer hold remains unresolved for {source_id}.',
            'inactive_patch_state': INACTIVE_STATE,
            'preview_effect': 'excluded_from_inactive_delta_placeholders',
            'rollback_note': f'Keep {source_id} out of inactive SourceRegistry and ArchiveManifest previews until reviewer hold is cleared.',
        })
        rollback_notes.append({
            'source_id': source_id,
            'rollback_note': f'Remove any later inactive placeholder for {source_id} if the hold remains or source metadata changes before review.',
        })

    if not rollback_notes:
        rollback_notes.append({
            'source_id': 'approved-preview-set',
            'rollback_note': 'Discard this inactive preview if reviewer disposition, dry-run metadata plan, canonical URL, redirect, HTTP status, or content-type expectations change before review.',
        })

    packet: dict[str, Any] = {
        'packet_version': PACKET_VERSION,
        'fixture_first': True,
        'inactive_patch_preview': True,
        'metadata_only': True,
        'reviewer_disposition_packet_ref': {
            'packet_version': _text(disposition_packet.get('packet_version')) or REVIEWER_PACKET_VERSION,
            'dry_run_manifest_id': _text(manifest_ref.get('manifest_id')),
            'dry_run_manifest_version': _text(manifest_ref.get('manifest_version')),
        },
        'metadata_dry_run_plan_ref': {
            'manifest_id': _text(manifest_ref.get('manifest_id')),
            'manifest_version': _text(manifest_ref.get('manifest_version')) or DRY_RUN_MANIFEST_VERSION,
            'metadata_only': True,
        },
        'approved_reviewer_disposition_rows': tuple(dict(row) for row in approved),
        'source_registry_delta_placeholders': registry,
        'archive_manifest_delta_placeholders': archive,
        'normalized_document_reference_placeholders': documents,
        'freshness_monitor_replay_notes': freshness,
        'held_or_skipped_reviewer_disposition_notes': held_notes,
        'rollback_notes': rollback_notes,
        'validation_commands': VALIDATION_COMMANDS,
    }
    for flag in FALSE_FLAGS:
        packet[flag] = False
    return packet


def validate_public_source_recrawl_inactive_patch_preview_v1(packet: Mapping[str, Any]) -> list[PublicSourceRecrawlInactivePatchPreviewIssue]:
    issues: list[PublicSourceRecrawlInactivePatchPreviewIssue] = []
    if not isinstance(packet, Mapping):
        return [PublicSourceRecrawlInactivePatchPreviewIssue('invalid_packet', '$', 'packet must be an object')]
    if packet.get('packet_version') != PACKET_VERSION:
        issues.append(PublicSourceRecrawlInactivePatchPreviewIssue('invalid_packet_version', '$.packet_version', f'packet_version must be {PACKET_VERSION}'))
    for key in ('fixture_first', 'inactive_patch_preview', 'metadata_only'):
        if packet.get(key) is not True:
            issues.append(PublicSourceRecrawlInactivePatchPreviewIssue('missing_required_true_flag', f'$.{key}', f'{key} must be true'))
    for flag in FALSE_FLAGS:
        if packet.get(flag) is not False:
            issues.append(PublicSourceRecrawlInactivePatchPreviewIssue('unsafe_execution_or_mutation_flag', f'$.{flag}', 'execution, DevHub access, payload storage, and active mutation flags must be false'))

    _validate_reviewer_ref(packet.get('reviewer_disposition_packet_ref'), issues)
    _validate_metadata_dry_run_plan_ref(packet.get('metadata_dry_run_plan_ref'), issues)

    approved_rows = _rows(packet.get('approved_reviewer_disposition_rows'))
    approved = _source_ids(packet.get('approved_reviewer_disposition_rows'), '$.approved_reviewer_disposition_rows', issues)
    approved_by_source = {_text(row.get('source_id')): row for row in approved_rows if _text(row.get('source_id'))}
    held_source_ids = {_text(row.get('source_id')) for row in approved_rows if _text(row.get('decision')) != APPROVED_DECISION and _text(row.get('source_id'))}

    registry_ids = _source_ids(packet.get('source_registry_delta_placeholders'), '$.source_registry_delta_placeholders', issues)
    archive_ids = _source_ids(packet.get('archive_manifest_delta_placeholders'), '$.archive_manifest_delta_placeholders', issues)
    document_ids = _source_ids(packet.get('normalized_document_reference_placeholders'), '$.normalized_document_reference_placeholders', issues)
    freshness_ids = _source_ids(packet.get('freshness_monitor_replay_notes'), '$.freshness_monitor_replay_notes', issues)

    for key, ids in (
        ('source_registry_delta_placeholders', registry_ids),
        ('archive_manifest_delta_placeholders', archive_ids),
        ('normalized_document_reference_placeholders', document_ids),
        ('freshness_monitor_replay_notes', freshness_ids),
    ):
        if approved and ids != approved:
            issues.append(PublicSourceRecrawlInactivePatchPreviewIssue('placeholder_source_mismatch', f'$.{key}', 'placeholder source_ids must exactly match approved reviewer disposition rows'))

    _validate_source_registry_rows(packet.get('source_registry_delta_placeholders'), approved_by_source, issues)
    _validate_archive_manifest_rows(packet.get('archive_manifest_delta_placeholders'), approved_by_source, issues)
    _validate_generic_inactive_rows(packet.get('normalized_document_reference_placeholders'), '$.normalized_document_reference_placeholders', issues)
    _validate_generic_inactive_rows(packet.get('freshness_monitor_replay_notes'), '$.freshness_monitor_replay_notes', issues)
    _validate_held_or_skipped_notes(packet.get('held_or_skipped_reviewer_disposition_notes'), held_source_ids, issues)
    _validate_rollback_notes(packet.get('rollback_notes'), issues)

    if _commands(packet.get('validation_commands')) != VALIDATION_COMMANDS:
        issues.append(PublicSourceRecrawlInactivePatchPreviewIssue('missing_validation_commands', '$.validation_commands', 'exact offline validation commands are required'))
    _scan(packet, '$', issues)
    return _dedupe(issues)


def require_valid_public_source_recrawl_inactive_patch_preview_v1(packet: Mapping[str, Any]) -> None:
    issues = validate_public_source_recrawl_inactive_patch_preview_v1(packet)
    if issues:
        raise PublicSourceRecrawlInactivePatchPreviewError(issues)


def _validate_reviewer_ref(value: Any, issues: list[PublicSourceRecrawlInactivePatchPreviewIssue]) -> None:
    if not isinstance(value, Mapping):
        issues.append(PublicSourceRecrawlInactivePatchPreviewIssue('missing_reviewer_disposition_ref', '$.reviewer_disposition_packet_ref', 'reviewer disposition packet reference is required'))
        return
    if _text(value.get('packet_version')) != REVIEWER_PACKET_VERSION:
        issues.append(PublicSourceRecrawlInactivePatchPreviewIssue('missing_reviewer_disposition_ref', '$.reviewer_disposition_packet_ref.packet_version', f'packet_version must be {REVIEWER_PACKET_VERSION}'))
    if not _text(value.get('dry_run_manifest_id')):
        issues.append(PublicSourceRecrawlInactivePatchPreviewIssue('missing_reviewer_disposition_ref', '$.reviewer_disposition_packet_ref.dry_run_manifest_id', 'reviewer disposition manifest id is required'))
    if not _text(value.get('dry_run_manifest_version')):
        issues.append(PublicSourceRecrawlInactivePatchPreviewIssue('missing_reviewer_disposition_ref', '$.reviewer_disposition_packet_ref.dry_run_manifest_version', 'reviewer disposition manifest version is required'))


def _validate_metadata_dry_run_plan_ref(value: Any, issues: list[PublicSourceRecrawlInactivePatchPreviewIssue]) -> None:
    if not isinstance(value, Mapping):
        issues.append(PublicSourceRecrawlInactivePatchPreviewIssue('missing_metadata_dry_run_plan_ref', '$.metadata_dry_run_plan_ref', 'metadata dry-run plan reference is required'))
        return
    if not _text(value.get('manifest_id')):
        issues.append(PublicSourceRecrawlInactivePatchPreviewIssue('missing_metadata_dry_run_plan_ref', '$.metadata_dry_run_plan_ref.manifest_id', 'metadata dry-run plan manifest id is required'))
    if not _text(value.get('manifest_version')):
        issues.append(PublicSourceRecrawlInactivePatchPreviewIssue('missing_metadata_dry_run_plan_ref', '$.metadata_dry_run_plan_ref.manifest_version', 'metadata dry-run plan manifest version is required'))
    if value.get('metadata_only') is not True:
        issues.append(PublicSourceRecrawlInactivePatchPreviewIssue('missing_metadata_dry_run_plan_ref', '$.metadata_dry_run_plan_ref.metadata_only', 'metadata dry-run plan must be metadata-only'))


def _validate_source_registry_rows(value: Any, approved_by_source: Mapping[str, Mapping[str, Any]], issues: list[PublicSourceRecrawlInactivePatchPreviewIssue]) -> None:
    for index, row in enumerate(_rows(value)):
        path = f'$.source_registry_delta_placeholders[{index}]'
        _require_inactive(row, path, issues)
        _require_text(row, 'canonical_url', path, 'missing_canonical_url', issues)
        _require_text(row, 'operation', path, 'missing_source_registry_patch_preview_row', issues)
        _require_text(row, 'privacy_classification', path, 'missing_source_registry_patch_preview_row', issues)
        _require_text(row, 'metadata_only_artifact_expectation_id', path, 'missing_source_registry_patch_preview_row', issues)
        if _text(row.get('active_source_promotion_state')) != NOT_PROMOTED:
            issues.append(PublicSourceRecrawlInactivePatchPreviewIssue('active_source_promotion_claim', f'{path}.active_source_promotion_state', 'inactive preview must explicitly avoid active SourceRegistry promotion'))
        source_id = _text(row.get('source_id'))
        expected = approved_by_source.get(source_id)
        if expected and _text(row.get('canonical_url')) != _text(expected.get('canonical_url')):
            issues.append(PublicSourceRecrawlInactivePatchPreviewIssue('canonical_url_mismatch', f'{path}.canonical_url', 'SourceRegistry canonical_url must match approved reviewer disposition row'))


def _validate_archive_manifest_rows(value: Any, approved_by_source: Mapping[str, Mapping[str, Any]], issues: list[PublicSourceRecrawlInactivePatchPreviewIssue]) -> None:
    for index, row in enumerate(_rows(value)):
        path = f'$.archive_manifest_delta_placeholders[{index}]'
        _require_inactive(row, path, issues)
        _require_text(row, 'canonical_url', path, 'missing_canonical_url', issues)
        _require_text(row, 'requested_url_placeholder', path, 'missing_canonical_url', issues)
        if not _is_non_empty_text_list(row.get('redirect_chain_placeholder')):
            issues.append(PublicSourceRecrawlInactivePatchPreviewIssue('missing_redirect_placeholder', f'{path}.redirect_chain_placeholder', 'redirect placeholder list is required'))
        if not _text(row.get('expected_http_status')) and not _text(row.get('http_status_placeholder')):
            issues.append(PublicSourceRecrawlInactivePatchPreviewIssue('missing_http_status_expectation', path, 'HTTP status expectation or placeholder is required'))
        if not _text(row.get('expected_content_type')) and not _text(row.get('content_type_placeholder')):
            issues.append(PublicSourceRecrawlInactivePatchPreviewIssue('missing_content_type_expectation', path, 'content-type expectation or placeholder is required'))
        _require_text(row, 'content_hash_placeholder', path, 'missing_archive_manifest_patch_preview_row', issues)
        _require_text(row, 'processor_name_placeholder', path, 'missing_archive_manifest_patch_preview_row', issues)
        _require_text(row, 'normalized_document_id_placeholder', path, 'missing_archive_manifest_patch_preview_row', issues)
        _require_text(row, 'skipped_reason_handling', path, 'missing_skipped_reason_handling', issues)
        if row.get('no_raw_body_persisted') is not True or row.get('no_payload_persisted') is not True:
            issues.append(PublicSourceRecrawlInactivePatchPreviewIssue('missing_payload_exclusion', path, 'archive preview must set no_raw_body_persisted and no_payload_persisted true'))
        if _text(row.get('active_archive_promotion_state')) != NOT_PROMOTED:
            issues.append(PublicSourceRecrawlInactivePatchPreviewIssue('active_archive_promotion_claim', f'{path}.active_archive_promotion_state', 'inactive preview must explicitly avoid active ArchiveManifest promotion'))
        source_id = _text(row.get('source_id'))
        expected = approved_by_source.get(source_id)
        if expected and _text(row.get('canonical_url')) != _text(expected.get('canonical_url')):
            issues.append(PublicSourceRecrawlInactivePatchPreviewIssue('canonical_url_mismatch', f'{path}.canonical_url', 'ArchiveManifest canonical_url must match approved reviewer disposition row'))


def _validate_generic_inactive_rows(value: Any, path: str, issues: list[PublicSourceRecrawlInactivePatchPreviewIssue]) -> None:
    for index, row in enumerate(_rows(value)):
        _require_inactive(row, f'{path}[{index}]', issues)


def _validate_held_or_skipped_notes(value: Any, held_source_ids: set[str], issues: list[PublicSourceRecrawlInactivePatchPreviewIssue]) -> None:
    if held_source_ids and (not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or not value):
        issues.append(PublicSourceRecrawlInactivePatchPreviewIssue('missing_reviewer_holds', '$.held_or_skipped_reviewer_disposition_notes', 'held reviewer disposition rows require held/skipped notes'))
        return
    note_source_ids: set[str] = set()
    for index, row in enumerate(_rows(value)):
        path = f'$.held_or_skipped_reviewer_disposition_notes[{index}]'
        source_id = _text(row.get('source_id'))
        if source_id:
            note_source_ids.add(source_id)
        _require_text(row, 'decision', path, 'missing_reviewer_holds', issues)
        _require_text(row, 'skipped_reason_code', path, 'missing_skipped_reason_handling', issues)
        _require_text(row, 'reviewer_hold_placeholder', path, 'missing_reviewer_holds', issues)
        _require_text(row, 'rollback_note', path, 'missing_rollback_notes', issues)
        _require_inactive(row, path, issues)
    for source_id in sorted(held_source_ids - note_source_ids):
        issues.append(PublicSourceRecrawlInactivePatchPreviewIssue('missing_reviewer_holds', '$.held_or_skipped_reviewer_disposition_notes', f'held reviewer disposition for {source_id} requires a hold note'))


def _validate_rollback_notes(value: Any, issues: list[PublicSourceRecrawlInactivePatchPreviewIssue]) -> None:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or not value:
        issues.append(PublicSourceRecrawlInactivePatchPreviewIssue('missing_rollback_notes', '$.rollback_notes', 'rollback notes are required'))
        return
    for index, row in enumerate(value):
        path = f'$.rollback_notes[{index}]'
        if not isinstance(row, Mapping):
            issues.append(PublicSourceRecrawlInactivePatchPreviewIssue('missing_rollback_notes', path, 'rollback note row must be an object'))
            continue
        _require_text(row, 'rollback_note', path, 'missing_rollback_notes', issues)


def _source_ids(value: Any, path: str, issues: list[PublicSourceRecrawlInactivePatchPreviewIssue]) -> set[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or not value:
        issues.append(PublicSourceRecrawlInactivePatchPreviewIssue('missing_placeholder_rows', path, 'placeholder rows must be a non-empty list'))
        return set()
    ids = set()
    for index, row in enumerate(value):
        if not isinstance(row, Mapping):
            issues.append(PublicSourceRecrawlInactivePatchPreviewIssue('invalid_placeholder_row', f'{path}[{index}]', 'row must be an object'))
            continue
        source_id = _text(row.get('source_id'))
        if source_id:
            ids.add(source_id)
        else:
            issues.append(PublicSourceRecrawlInactivePatchPreviewIssue('missing_source_id', f'{path}[{index}].source_id', 'source_id is required'))
    return ids


def _require_inactive(row: Mapping[str, Any], path: str, issues: list[PublicSourceRecrawlInactivePatchPreviewIssue]) -> None:
    if _text(row.get('inactive_patch_state')) != INACTIVE_STATE:
        issues.append(PublicSourceRecrawlInactivePatchPreviewIssue('not_inactive_preview', f'{path}.inactive_patch_state', 'placeholder row must be inactive_preview_only'))


def _require_text(row: Mapping[str, Any], field: str, path: str, code: str, issues: list[PublicSourceRecrawlInactivePatchPreviewIssue]) -> None:
    if not _text(row.get(field)):
        issues.append(PublicSourceRecrawlInactivePatchPreviewIssue(code, f'{path}.{field}', f'{field} is required'))


def _scan(value: Any, path: str, issues: list[PublicSourceRecrawlInactivePatchPreviewIssue]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f'{path}.{key_text}' if path != '$' else f'$.{key_text}'
            if key_text.lower() in UNSAFE_KEYS and _has_content(child):
                issues.append(PublicSourceRecrawlInactivePatchPreviewIssue('unsafe_artifact_reference', child_path, 'private, authenticated, session, browser, raw crawl, PDF, or downloaded artifacts are not allowed'))
            _scan(child, child_path, issues)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, child in enumerate(value):
            _scan(child, f'{path}[{index}]', issues)
        return
    if isinstance(value, str) and not _skip_text_scan(path):
        lowered = ' '.join(value.lower().split())
        for code, patterns in UNSAFE_TEXT.items():
            if any(pattern in lowered for pattern in patterns):
                issues.append(PublicSourceRecrawlInactivePatchPreviewIssue(code, path, 'preview text must not claim unsafe artifacts, execution, outcomes, consequential DevHub action, active promotion, or active mutation'))


def _skip_text_scan(path: str) -> bool:
    return any(path.endswith(suffix) or suffix in path for suffix in TEXT_SCAN_SKIP_SUFFIXES)


def _rows(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _commands(value: Any) -> tuple[tuple[str, ...], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    commands = []
    for command in value:
        if not isinstance(command, Sequence) or isinstance(command, (str, bytes)):
            return ()
        command_tuple = tuple(item for item in command if isinstance(item, str))
        if not command_tuple:
            return ()
        commands.append(command_tuple)
    return tuple(commands)


def _skipped_reason_by_source(value: Any) -> dict[str, str]:
    reasons: dict[str, str] = {}
    for row in _rows(value):
        source_id = _text(row.get('source_id'))
        reason = _text(row.get('skip_reason_code')) or _text(row.get('skipped_reason'))
        if source_id and reason:
            reasons[source_id] = reason
    return reasons


def _has_content(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return bool(value)
    if isinstance(value, Mapping):
        return bool(value)
    return True


def _is_non_empty_text_list(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes)) and bool(value) and all(_text(item) for item in value)


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ''


def _dedupe(issues: Sequence[PublicSourceRecrawlInactivePatchPreviewIssue]) -> list[PublicSourceRecrawlInactivePatchPreviewIssue]:
    seen = set()
    deduped = []
    for issue in issues:
        key = (issue.code, issue.path, issue.message)
        if key not in seen:
            seen.add(key)
            deduped.append(issue)
    return deduped
