from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

PACKET_VERSION = 'public-refresh-normalized-document-extraction-readiness-packet-v1'
MODE = 'fixture_first_offline_validation_only'

VALIDATION_COMMANDS: tuple[tuple[str, ...], ...] = (
    ('python3', '-m', 'py_compile', 'ppd/agent_readiness/public_refresh_normalized_document_extraction_readiness_packet_v1.py'),
    ('python3', '-m', 'pytest', 'ppd/tests/test_public_refresh_normalized_document_extraction_readiness_packet_v1.py'),
    ('python3', 'ppd/daemon/ppd_daemon.py', '--self-test'),
)

REQUIRED_FALSE_FLAGS = (
    'live_extraction',
    'live_crawl',
    'document_download',
    'raw_output_stored',
    'devhub_accessed',
    'active_document_record_mutation',
    'official_action_completed',
    'legal_or_permitting_guarantee',
    'active_mutation',
)

SENSITIVE_KEYS = frozenset({
    'auth_state',
    'browser_trace',
    'cookie',
    'credential',
    'devhub_session',
    'downloaded_artifact',
    'downloaded_document',
    'downloaded_pdf',
    'har',
    'html_body',
    'private_artifact',
    'raw_artifact',
    'raw_body',
    'raw_crawl_output',
    'raw_download',
    'raw_html',
    'raw_output',
    'raw_pdf',
    'screenshot',
    'session_state',
    'trace',
    'warc_path',
})

PROHIBITED_PHRASES = frozenset({
    'active documentrecord mutation',
    'active document record mutation',
    'active mutation enabled',
    'certification completed',
    'devhub accessed',
    'devhub opened',
    'downloaded document',
    'guaranteed approval',
    'guaranteed permit',
    'legal advice',
    'live crawl completed',
    'live extraction completed',
    'official action completed',
    'payment completed',
    'permit guaranteed',
    'raw crawl output',
    'raw output stored',
    'submission completed',
    'upload completed',
})

ALLOWED_ROUTE_DECISIONS = frozenset({
    'extract_public_html_fixture_only',
    'extract_public_pdf_metadata_fixture_only',
    'hold_for_human_review',
    'skip_until_archive_preview_reviewed',
})


@dataclass(frozen=True)
class NormalizedDocumentExtractionReadinessIssue:
    code: str
    path: str
    message: str


class NormalizedDocumentExtractionReadinessError(ValueError):
    def __init__(self, issues: Sequence[NormalizedDocumentExtractionReadinessIssue]) -> None:
        self.issues = tuple(issues)
        super().__init__('; '.join(f'{issue.path}: {issue.code}: {issue.message}' for issue in self.issues))


def validate_public_refresh_normalized_document_extraction_readiness_packet_v1(packet: Mapping[str, Any]) -> list[NormalizedDocumentExtractionReadinessIssue]:
    issues: list[NormalizedDocumentExtractionReadinessIssue] = []
    if not isinstance(packet, Mapping):
        return [NormalizedDocumentExtractionReadinessIssue('invalid_packet', '$', 'packet must be an object')]

    if packet.get('packet_version') != PACKET_VERSION:
        _issue(issues, 'invalid_packet_version', '$.packet_version', f'packet_version must be {PACKET_VERSION}')
    if packet.get('mode') != MODE:
        _issue(issues, 'invalid_mode', '$.mode', f'mode must be {MODE}')
    if packet.get('fixture_first') is not True:
        _issue(issues, 'missing_fixture_first', '$.fixture_first', 'fixture_first must be true')

    for flag in REQUIRED_FALSE_FLAGS:
        if packet.get(flag) is not False:
            _issue(issues, 'unsafe_execution_or_mutation_flag', f'$.{flag}', f'{flag} must be false')

    archive_refs = _required_string_list(packet, 'inactive_archive_patch_preview_refs', issues)
    citation_refs = _required_string_list(packet, 'citation_impact_queue_refs', issues)
    candidates = _required_mapping_list(packet, 'normalized_document_extraction_candidates', issues)

    for index, candidate in enumerate(candidates):
        _validate_candidate(candidate, index, archive_refs, citation_refs, issues)

    if _commands(packet.get('validation_commands')) != VALIDATION_COMMANDS:
        _issue(issues, 'missing_validation_commands', '$.validation_commands', 'exact offline validation commands are required')

    _reject_private_runtime_or_unsafe_claims(packet, '$', issues)
    return _dedupe(issues)


def require_valid_public_refresh_normalized_document_extraction_readiness_packet_v1(packet: Mapping[str, Any]) -> None:
    issues = validate_public_refresh_normalized_document_extraction_readiness_packet_v1(packet)
    if issues:
        raise NormalizedDocumentExtractionReadinessError(issues)


def _validate_candidate(candidate: Mapping[str, Any], index: int, archive_refs: set[str], citation_refs: set[str], issues: list[NormalizedDocumentExtractionReadinessIssue]) -> None:
    path = f'$.normalized_document_extraction_candidates[{index}]'
    for key in (
        'candidate_id',
        'source_id',
        'canonical_url',
        'inactive_archive_patch_preview_ref',
        'citation_impact_queue_ref',
        'normalized_document_id_placeholder',
        'extraction_route_decision',
        'confidence_placeholder',
        'human_review_route',
        'stale_source_hold',
        'rollback_note',
    ):
        _required_text(candidate, key, f'{path}.{key}', issues)

    archive_ref = _text(candidate.get('inactive_archive_patch_preview_ref'))
    if archive_ref and archive_ref not in archive_refs:
        _issue(issues, 'missing_inactive_archive_patch_preview_reference', f'{path}.inactive_archive_patch_preview_ref', 'candidate must reference a declared inactive archive patch preview')

    citation_ref = _text(candidate.get('citation_impact_queue_ref'))
    if citation_ref and citation_ref not in citation_refs:
        _issue(issues, 'missing_citation_impact_queue_reference', f'{path}.citation_impact_queue_ref', 'candidate must reference a declared citation impact queue')

    placeholder = _text(candidate.get('normalized_document_id_placeholder'))
    if placeholder and not (placeholder.startswith('pending-normalized-document-') or placeholder.startswith('placeholder:')):
        _issue(issues, 'missing_normalized_document_placeholder_id', f'{path}.normalized_document_id_placeholder', 'normalized document id must remain a placeholder')

    route = _text(candidate.get('extraction_route_decision'))
    if route and route not in ALLOWED_ROUTE_DECISIONS:
        _issue(issues, 'invalid_extraction_route_decision', f'{path}.extraction_route_decision', 'extraction route decision is not allowed')

    if not _non_empty_list(candidate.get('citation_span_acceptance_checks')):
        _issue(issues, 'missing_citation_span_acceptance_checks', f'{path}.citation_span_acceptance_checks', 'citation-span acceptance checks are required')

    has_table_expectations = _non_empty_list(candidate.get('table_extraction_expectations'))
    has_file_rule_expectations = _non_empty_list(candidate.get('file_rule_extraction_expectations'))
    if not has_table_expectations and not has_file_rule_expectations:
        _issue(issues, 'missing_table_or_file_rule_extraction_expectations', path, 'table or file-rule extraction expectations are required')

    confidence = _text(candidate.get('confidence_placeholder'))
    if confidence and 'placeholder' not in confidence.lower():
        _issue(issues, 'missing_confidence_placeholder', f'{path}.confidence_placeholder', 'confidence must remain a placeholder')

    if _text(candidate.get('allowed_next_action')) != 'human_review_of_fixture_extraction_plan_only':
        _issue(issues, 'missing_human_review_routing', f'{path}.allowed_next_action', 'allowed next action must route to human review only')

    if candidate.get('agent_may_treat_source_as_current') is not False:
        _issue(issues, 'missing_stale_source_hold', f'{path}.agent_may_treat_source_as_current', 'stale-source hold must prevent treating source as current')

    for flag in REQUIRED_FALSE_FLAGS:
        if candidate.get(flag) is not False:
            _issue(issues, 'unsafe_execution_or_mutation_flag', f'{path}.{flag}', f'candidate {flag} must be false')


def _required_string_list(packet: Mapping[str, Any], key: str, issues: list[NormalizedDocumentExtractionReadinessIssue]) -> set[str]:
    value = packet.get(key)
    if not _non_empty_list(value):
        _issue(issues, f'missing_{key}', f'$.{key}', f'{key} must be a non-empty list of strings')
        return set()
    return {item.strip() for item in value if isinstance(item, str) and item.strip()}


def _required_mapping_list(packet: Mapping[str, Any], key: str, issues: list[NormalizedDocumentExtractionReadinessIssue]) -> list[Mapping[str, Any]]:
    value = packet.get(key)
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or not value:
        _issue(issues, f'missing_{key}', f'$.{key}', f'{key} must be a non-empty list')
        return []
    rows = []
    for index, item in enumerate(value):
        if isinstance(item, Mapping):
            rows.append(item)
        else:
            _issue(issues, 'invalid_candidate', f'$.{key}[{index}]', 'candidate must be an object')
    return rows


def _required_text(row: Mapping[str, Any], key: str, path: str, issues: list[NormalizedDocumentExtractionReadinessIssue]) -> str:
    value = _text(row.get(key))
    if not value:
        _issue(issues, f'missing_{key}', path, f'{key} is required')
    return value


def _reject_private_runtime_or_unsafe_claims(value: Any, path: str, issues: list[NormalizedDocumentExtractionReadinessIssue]) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = str(key).lower()
            child_path = f'{path}.{key}' if path != '$' else f'$.{key}'
            if key_text in SENSITIVE_KEYS and _has_content(nested):
                _issue(issues, 'private_raw_downloaded_or_runtime_artifact', child_path, 'private, raw, downloaded, browser, or session artifacts are not allowed')
            _reject_private_runtime_or_unsafe_claims(nested, child_path, issues)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, nested in enumerate(value):
            _reject_private_runtime_or_unsafe_claims(nested, f'{path}[{index}]', issues)
    elif isinstance(value, str) and '.validation_commands' not in path:
        normalized = ' '.join(value.lower().replace('_', ' ').replace('-', ' ').split())
        for phrase in PROHIBITED_PHRASES:
            if phrase in normalized:
                _issue(issues, 'prohibited_claim', path, f'prohibited claim phrase: {phrase}')


def _commands(value: Any) -> tuple[tuple[str, ...], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    commands: list[tuple[str, ...]] = []
    for command in value:
        if not isinstance(command, Sequence) or isinstance(command, (str, bytes)):
            return ()
        command_tuple = tuple(item for item in command if isinstance(item, str))
        if len(command_tuple) != len(command) or not command_tuple:
            return ()
        commands.append(command_tuple)
    return tuple(commands)


def _non_empty_list(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes)) and bool(value) and all(isinstance(item, str) and item.strip() for item in value)


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


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ''


def _issue(issues: list[NormalizedDocumentExtractionReadinessIssue], code: str, path: str, message: str) -> None:
    issues.append(NormalizedDocumentExtractionReadinessIssue(code, path, message))


def _dedupe(issues: Sequence[NormalizedDocumentExtractionReadinessIssue]) -> list[NormalizedDocumentExtractionReadinessIssue]:
    seen = set()
    output = []
    for issue in issues:
        key = (issue.code, issue.path, issue.message)
        if key not in seen:
            seen.add(key)
            output.append(issue)
    return output
