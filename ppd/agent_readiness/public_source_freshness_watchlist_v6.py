from __future__ import annotations

from datetime import date, datetime, timezone
import json
from pathlib import Path
from typing import Any, Mapping

PACKET_VERSION = 'public-source-freshness-watchlist-v6'
REGISTRY_VERSION = 'committed-public-source-registry-v6'
PRIOR_REFRESH_FIXTURE_VERSION = 'prior-refresh-fixture-references-v6'

OFFLINE_VALIDATION_COMMANDS = [
    ['python3', '-m', 'py_compile', 'ppd/agent_readiness/public_source_freshness_watchlist_v6.py'],
    ['python3', '-m', 'pytest', 'ppd/tests/test_public_source_freshness_watchlist_v6.py'],
    ['python3', 'ppd/daemon/ppd_daemon.py', '--self-test'],
]

FRESHNESS_THRESHOLDS_DAYS = {
    'daily': 2,
    'every_few_days': 5,
    'weekly': 14,
    'monthly': 45,
    'quarterly': 120,
}

PRIORITY_SOURCE_GROUPS = {
    'devhub_public_guidance': {
        'priority': 1,
        'reviewer_owner': 'devhub-public-guidance-reviewer',
        'reason': 'DevHub public guidance can affect account, upload, payment, correction, and inspection guardrails.',
    },
    'file_preparation_and_upload_guidance': {
        'priority': 2,
        'reviewer_owner': 'public-content-reviewer',
        'reason': 'File preparation rules affect document package completeness and upload readiness checks.',
    },
    'fee_payment_public_guidance': {
        'priority': 3,
        'reviewer_owner': 'forms-and-pdf-reviewer',
        'reason': 'Fee payment guidance is financial-workflow evidence and must stay exact-confirmation gated.',
    },
    'forms_index_and_public_forms': {
        'priority': 4,
        'reviewer_owner': 'forms-and-pdf-reviewer',
        'reason': 'Forms index changes can affect required document and permit application references.',
    },
}

PROHIBITED_ACTIONS = [
    'live_crawl',
    'document_download',
    'raw_body_capture',
    'devhub_open',
    'private_document_read',
    'upload',
    'submit',
    'certify',
    'payment',
    'schedule',
    'legal_or_permitting_guarantee',
]

REQUIRED_SOURCE_BOUNDARIES = {
    'live_crawl',
    'document_download',
    'raw_body_storage',
    'devhub_opened',
    'private_documents_read',
    'official_action_taken',
    'legal_or_permitting_guarantee',
}

BLOCKED_ARTIFACT_KEY_PARTS = (
    'raw_crawl',
    'downloaded_document',
    'downloaded_pdf',
    'private_document',
    'session_cookie',
    'auth_state',
    'storage_state',
    'browser_state',
    'trace',
    'har',
    'screenshot',
)

BLOCKED_EXACT_KEYS = {
    'raw_body',
    'raw_html',
    'raw_pdf',
    'active_mutation',
    'mutation_enabled',
    'mutations_enabled',
    'write_enabled',
    'official_action_completion_claim',
    'completion_claim',
    'submitted',
    'uploaded',
    'certified',
    'paid',
    'scheduled',
}

POLICY_KEYS_ALLOWED_TO_MENTION_RAW_BODY = {
    'no_raw_body_capture_policy',
    'no_raw_body_capture_policy_reminders',
}


def load_json_object(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(payload, dict):
        raise ValueError(f'fixture must be a JSON object: {path}')
    return payload


def build_watchlist_from_files(registry_path: str | Path, prior_refresh_path: str | Path, *, as_of_date: str = '2026-06-01') -> dict[str, Any]:
    return build_watchlist(load_json_object(registry_path), load_json_object(prior_refresh_path), as_of_date=as_of_date)


def build_watchlist(registry: Mapping[str, Any], prior_refresh: Mapping[str, Any], *, as_of_date: str = '2026-06-01') -> dict[str, Any]:
    _validate_registry(registry)
    _validate_prior_refresh(prior_refresh)
    as_of = date.fromisoformat(as_of_date)
    prior_by_source = {
        item['source_id']: item
        for item in prior_refresh['source_observations']
        if isinstance(item, dict) and isinstance(item.get('source_id'), str)
    }

    rows = []
    for source in registry['sources']:
        rows.append(_watchlist_row(source, prior_by_source.get(source['source_id'], {}), as_of=as_of))

    rows.sort(key=lambda row: (row['priority'], -row['days_since_last_seen'], row['source_id']))
    for index, row in enumerate(rows, start=1):
        row['rank'] = index

    packet = {
        'packet_version': PACKET_VERSION,
        'fixture_first': True,
        'as_of_date': as_of.isoformat(),
        'consumed_fixture_versions': [registry['registry_version'], prior_refresh['fixture_version']],
        'source_boundaries': {
            'live_crawl': False,
            'document_download': False,
            'raw_body_storage': False,
            'devhub_opened': False,
            'private_documents_read': False,
            'official_action_taken': False,
            'legal_or_permitting_guarantee': False,
        },
        'freshness_thresholds_days': dict(FRESHNESS_THRESHOLDS_DAYS),
        'priority_source_groups': PRIORITY_SOURCE_GROUPS,
        'watchlist_rows': rows,
        'no_raw_body_capture_policy_reminders': [
            'Persist metadata, normalized public text references, checksums, and citations only.',
            'Do not commit raw HTML, raw PDF bytes, screenshots, HAR files, traces, browser state, or downloaded documents.',
            'Any future raw-body capture requires a separate non-git local run policy and reviewer approval.',
        ],
        'crawl_deferral_notes': [
            'This packet is a fixture-first watchlist only; it does not authorize a crawl.',
            'Future public refresh work must run allowlist, robots, no-raw-body, and reviewer preflight before fetching.',
            'DevHub authenticated pages, private documents, payments, submissions, uploads, certifications, and scheduling remain out of scope.',
        ],
        'prohibited_actions': PROHIBITED_ACTIONS,
        'offline_validation_commands': OFFLINE_VALIDATION_COMMANDS,
    }
    validate_watchlist(packet)
    return packet


def validate_watchlist(packet: Mapping[str, Any]) -> None:
    if packet.get('packet_version') != PACKET_VERSION:
        raise ValueError('unexpected packet_version')
    if packet.get('fixture_first') is not True:
        raise ValueError('watchlist must be fixture_first')
    _reject_blocked_claims_and_artifacts(packet, '$packet')
    _validate_required_packet_sections(packet)

    rows = packet.get('watchlist_rows')
    if not isinstance(rows, list) or not rows:
        raise ValueError('watchlist_rows must be a non-empty list')
    ranks = [row.get('rank') for row in rows if isinstance(row, Mapping)]
    if ranks != list(range(1, len(rows) + 1)):
        raise ValueError('watchlist row ranks must be contiguous')
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError('watchlist row must be an object')
        _validate_row(row, packet)


def _validate_required_packet_sections(packet: Mapping[str, Any]) -> None:
    if packet.get('offline_validation_commands') != OFFLINE_VALIDATION_COMMANDS:
        raise ValueError('offline validation commands must match the exact v6 command set')
    if packet.get('freshness_thresholds_days') != FRESHNESS_THRESHOLDS_DAYS:
        raise ValueError('freshness_thresholds_days must include the dated v6 threshold set')
    if packet.get('priority_source_groups') != PRIORITY_SOURCE_GROUPS:
        raise ValueError('priority_source_groups must include the required v6 source groups')
    if packet.get('prohibited_actions') != PROHIBITED_ACTIONS:
        raise ValueError('prohibited_actions must include the required v6 action prohibitions')
    _require_non_empty_string_list(packet, 'no_raw_body_capture_policy_reminders')
    _require_non_empty_string_list(packet, 'crawl_deferral_notes')

    boundaries = packet.get('source_boundaries')
    if not isinstance(boundaries, Mapping):
        raise ValueError('source_boundaries must be an object')
    if set(boundaries) != REQUIRED_SOURCE_BOUNDARIES:
        raise ValueError('source_boundaries must include the required v6 false boundary claims')
    for key, value in boundaries.items():
        if value is not False:
            raise ValueError(f'source boundary must remain false: {key}')


def _watchlist_row(source: Mapping[str, Any], prior: Mapping[str, Any], *, as_of: date) -> dict[str, Any]:
    frequency = str(source['crawl_frequency'])
    threshold_days = FRESHNESS_THRESHOLDS_DAYS[frequency]
    last_seen = _parse_date(str(source['last_seen_at']))
    days_since_last_seen = (as_of - last_seen).days
    group_id = str(source['priority_source_group'])
    group = PRIORITY_SOURCE_GROUPS[group_id]
    stale_by_age = days_since_last_seen > threshold_days
    prior_hold = bool(prior.get('stale_source_hold'))
    changed_risk = str(prior.get('changed_requirement_risk', source.get('changed_requirement_risk', 'unknown')))
    hold_triggered = stale_by_age or prior_hold or changed_risk in {'high', 'medium'}

    return {
        'rank': 0,
        'source_id': source['source_id'],
        'canonical_url': source['canonical_url'],
        'source_type': source['source_type'],
        'priority_source_group': group_id,
        'priority': group['priority'],
        'days_since_last_seen': days_since_last_seen,
        'freshness_threshold': {
            'as_of_date': as_of.isoformat(),
            'last_seen_at': source['last_seen_at'],
            'crawl_frequency': frequency,
            'threshold_days': threshold_days,
            'days_since_last_seen': days_since_last_seen,
            'is_stale_by_age': stale_by_age,
        },
        'stale_source_hold_trigger': {
            'triggered': hold_triggered,
            'reasons': _hold_reasons(stale_by_age, prior_hold, changed_risk),
            'agent_effect': 'hold affected currentness claims and consequential PP&D actions until reviewer disposition',
        },
        'affected_requirement_ids': _string_list(prior.get('affected_requirement_ids')),
        'affected_guardrail_bundle_ids': _string_list(prior.get('affected_guardrail_bundle_ids')),
        'reviewer_escalation': {
            'reviewer_owner': str(prior.get('reviewer_routing') or group['reviewer_owner']),
            'escalation_row_id': f"freshness-v6::{source['source_id']}",
            'priority': group['priority'],
            'required_disposition': ['confirm_fixture', 'keep_hold', 'approve_future_public_refresh_preflight'],
        },
        'no_raw_body_capture_policy': 'metadata_normalized_text_checksums_and_citations_only',
        'crawl_deferral_note': 'defer any crawl until separate public preflight confirms allowlist, robots, no-raw-body persistence, and reviewer approval',
        'source_registry_reference': str(source['registry_reference']),
        'prior_refresh_fixture_reference': str(prior.get('fixture_reference', '')),
    }


def _hold_reasons(stale_by_age: bool, prior_hold: bool, changed_risk: str) -> list[str]:
    reasons = []
    if stale_by_age:
        reasons.append('dated_freshness_threshold_exceeded')
    if prior_hold:
        reasons.append('prior_refresh_fixture_stale_source_hold')
    if changed_risk in {'high', 'medium'}:
        reasons.append(f'changed_requirement_risk_{changed_risk}')
    if not reasons:
        reasons.append('watch_only_no_hold')
    return reasons


def _validate_registry(registry: Mapping[str, Any]) -> None:
    if registry.get('registry_version') != REGISTRY_VERSION:
        raise ValueError('unexpected registry fixture version')
    sources = registry.get('sources')
    if not isinstance(sources, list) or not sources:
        raise ValueError('registry fixture must include non-empty sources')
    _reject_blocked_claims_and_artifacts(registry, '$registry')
    for source in sources:
        if not isinstance(source, Mapping):
            raise ValueError('registry source must be an object')
        for key in ('source_id', 'canonical_url', 'source_type', 'crawl_frequency', 'last_seen_at', 'registry_reference'):
            if not isinstance(source.get(key), str) or not source[key]:
                raise ValueError(f'registry source missing string field: {key}')
        if source.get('priority_source_group') not in PRIORITY_SOURCE_GROUPS:
            raise ValueError('registry source missing known priority_source_group')
        if source.get('crawl_frequency') not in FRESHNESS_THRESHOLDS_DAYS:
            raise ValueError('registry source missing known dated freshness threshold')
        _parse_date(source['last_seen_at'])


def _validate_prior_refresh(prior_refresh: Mapping[str, Any]) -> None:
    if prior_refresh.get('fixture_version') != PRIOR_REFRESH_FIXTURE_VERSION:
        raise ValueError('unexpected prior refresh fixture version')
    if prior_refresh.get('fixture_first') is not True:
        raise ValueError('prior refresh fixture must be fixture_first')
    observations = prior_refresh.get('source_observations')
    if not isinstance(observations, list) or not observations:
        raise ValueError('prior refresh fixture must include source_observations')
    _reject_blocked_claims_and_artifacts(prior_refresh, '$prior_refresh')
    for observation in observations:
        if not isinstance(observation, Mapping):
            raise ValueError('prior refresh observation must be an object')
        for key in ('source_id', 'fixture_reference', 'reviewer_routing'):
            if not isinstance(observation.get(key), str) or not observation[key]:
                raise ValueError(f'prior refresh observation missing {key}')
        if not isinstance(observation.get('stale_source_hold'), bool):
            raise ValueError('prior refresh observation missing stale_source_hold')
        _require_non_empty_string_list(observation, 'affected_requirement_ids')
        _require_non_empty_string_list(observation, 'affected_guardrail_bundle_ids')


def _validate_row(row: Mapping[str, Any], packet: Mapping[str, Any]) -> None:
    for key in (
        'source_id',
        'canonical_url',
        'source_type',
        'priority_source_group',
        'no_raw_body_capture_policy',
        'crawl_deferral_note',
        'source_registry_reference',
        'prior_refresh_fixture_reference',
    ):
        if not isinstance(row.get(key), str) or not row[key]:
            raise ValueError(f'watchlist row missing string field: {key}')
    groups = packet.get('priority_source_groups')
    if not isinstance(groups, Mapping) or row['priority_source_group'] not in groups:
        raise ValueError('watchlist row missing known priority source group')
    if not isinstance(row.get('priority'), int):
        raise ValueError('watchlist row missing integer priority')
    _validate_freshness_threshold(row.get('freshness_threshold'), row)
    _validate_stale_source_hold_trigger(row.get('stale_source_hold_trigger'))
    _require_non_empty_string_list(row, 'affected_requirement_ids')
    _require_non_empty_string_list(row, 'affected_guardrail_bundle_ids')
    _validate_reviewer_escalation(row.get('reviewer_escalation'), row)


def _validate_freshness_threshold(value: Any, row: Mapping[str, Any]) -> None:
    if not isinstance(value, Mapping):
        raise ValueError('freshness_threshold must be an object')
    for key in ('as_of_date', 'last_seen_at', 'crawl_frequency'):
        if not isinstance(value.get(key), str) or not value[key]:
            raise ValueError(f'freshness_threshold missing string field: {key}')
    frequency = value['crawl_frequency']
    if frequency not in FRESHNESS_THRESHOLDS_DAYS:
        raise ValueError('freshness_threshold missing known dated threshold')
    if value.get('threshold_days') != FRESHNESS_THRESHOLDS_DAYS[frequency]:
        raise ValueError('freshness_threshold threshold_days does not match dated v6 thresholds')
    if not isinstance(value.get('days_since_last_seen'), int):
        raise ValueError('freshness_threshold missing integer field: days_since_last_seen')
    if value.get('days_since_last_seen') != row.get('days_since_last_seen'):
        raise ValueError('freshness_threshold days_since_last_seen must match row')
    if not isinstance(value.get('is_stale_by_age'), bool):
        raise ValueError('freshness_threshold missing is_stale_by_age boolean')
    _parse_date(value['as_of_date'])
    _parse_date(value['last_seen_at'])


def _validate_stale_source_hold_trigger(value: Any) -> None:
    if not isinstance(value, Mapping):
        raise ValueError('stale_source_hold_trigger must be an object')
    if not isinstance(value.get('triggered'), bool):
        raise ValueError('stale_source_hold_trigger must include triggered boolean')
    _require_non_empty_string_list(value, 'reasons')
    if not isinstance(value.get('agent_effect'), str) or not value['agent_effect']:
        raise ValueError('stale_source_hold_trigger missing agent_effect')


def _validate_reviewer_escalation(value: Any, row: Mapping[str, Any]) -> None:
    if not isinstance(value, Mapping):
        raise ValueError('reviewer_escalation must be an object')
    for key in ('reviewer_owner', 'escalation_row_id'):
        if not isinstance(value.get(key), str) or not value[key]:
            raise ValueError(f'reviewer_escalation missing string field: {key}')
    if not str(value['escalation_row_id']).endswith(str(row['source_id'])):
        raise ValueError('reviewer_escalation row must reference the source_id')
    if value.get('priority') != row.get('priority'):
        raise ValueError('reviewer_escalation priority must match row priority')
    _require_non_empty_string_list(value, 'required_disposition')


def _require_non_empty_string_list(parent: Mapping[str, Any], key: str) -> None:
    value = parent.get(key)
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
        raise ValueError(f'{key} must be a non-empty list of strings')


def _reject_blocked_claims_and_artifacts(value: Any, path: str) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key).lower()
            child_path = f'{path}.{key}'
            allowed_policy_key = key_text in POLICY_KEYS_ALLOWED_TO_MENTION_RAW_BODY
            if not allowed_policy_key and key_text in BLOCKED_EXACT_KEYS and child not in (None, False, '', []):
                raise ValueError(f'active mutation, completion claim, raw artifact, or official action flag is not allowed at {child_path}')
            if not allowed_policy_key and any(part in key_text for part in BLOCKED_ARTIFACT_KEY_PARTS) and child not in (None, False, '', []):
                raise ValueError(f'raw, downloaded, private, session, auth, trace, or crawl artifact is not allowed at {child_path}')
            _reject_blocked_claims_and_artifacts(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_blocked_claims_and_artifacts(child, f'{path}[{index}]')


def _parse_date(value: str) -> date:
    normalized = value.replace('Z', '+00:00')
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.date()


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]
