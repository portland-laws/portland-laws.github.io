from __future__ import annotations

import copy
import json
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ppd.agent_readiness.public_refresh_authorization_packet_v6 import (
    assert_valid_public_refresh_authorization_packet_v6,
    build_public_refresh_authorization_packet_v6_from_fixture,
)

PACKET_TYPE = 'ppd.public_refresh_dry_run_execution_plan.v6'
PACKET_VERSION = 'v6'
MODE = 'fixture_first_public_refresh_dry_run_execution_plan_v6'
AUTH_PACKET_TYPE = 'ppd.public_refresh_authorization_packet.v6'

EXACT_OFFLINE_VALIDATION_COMMANDS = [
    ['python3', '-m', 'py_compile', 'ppd/agent_readiness/public_refresh_dry_run_execution_plan_v6.py'],
    ['python3', '-m', 'py_compile', 'ppd/tests/test_public_refresh_dry_run_execution_plan_v6.py'],
    ['python3', '-m', 'pytest', 'ppd/tests/test_public_refresh_dry_run_execution_plan_v6.py'],
    ['python3', 'ppd/daemon/ppd_daemon.py', '--self-test'],
]
VALIDATION_COMMANDS = [['python3', 'ppd/daemon/ppd_daemon.py', '--self-test']]

BOUNDARIES = {
    'fixture_first': True,
    'public_refresh_authorization_packet_v6_fixtures_only': True,
    'dry_run_execution_plan_only': True,
    'live_crawl_executed': False,
    'documents_downloaded': False,
    'raw_bodies_persisted': False,
    'devhub_opened': False,
    'private_documents_read': False,
    'uploads_performed': False,
    'submissions_performed': False,
    'certifications_performed': False,
    'payments_performed': False,
    'scheduling_performed': False,
    'legal_or_permitting_guarantees_made': False,
    'active_mutation': False,
}

FORBIDDEN_TRUE_KEYS = frozenset({
    'live_crawl_executed',
    'documents_downloaded',
    'raw_bodies_persisted',
    'devhub_opened',
    'private_documents_read',
    'uploads_performed',
    'submissions_performed',
    'certifications_performed',
    'payments_performed',
    'scheduling_performed',
    'legal_or_permitting_guarantees_made',
    'active_mutation',
    'crawl_started',
    'downloaded',
    'submitted',
    'uploaded',
    'certified',
    'paid',
    'scheduled',
})
PRIVATE_KEY_RE = re.compile(r'(^|_)(auth|browser|cookie|credential|download|har|password|payment|private|raw|screenshot|secret|session|storage_state|token|trace)(_|$)', re.IGNORECASE)
OFFICIAL_COMPLETION_KEY_RE = re.compile(r'(^|_)(official_action|submission|upload|certification|payment|schedule|cancellation|permit_issuance|approval)(_.*)?(complete|completed|performed|executed|succeeded|done|finalized)($|_)', re.IGNORECASE)
GUARANTEE_KEY_RE = re.compile(r'(^|_)(legal|permit|permitting|approval|issuance|compliance)(_.*)?(guarantee|guaranteed|assurance|assured)($|_)', re.IGNORECASE)
ACTIVE_MUTATION_KEY_RE = re.compile(r'(^|_)(active_mutation|mutation|write|crawl|download|upload|submit|certify|payment|schedule)(_.*)?(enabled|flag|mode|active|allowed)($|_)', re.IGNORECASE)
ALLOWED_PRIVATE_SHAPING_KEYS = {'no_raw_body_manifest_only_output_expectations', 'no_raw_body_persisted_required', 'raw_artifact_ref_allowed'}


@dataclass(frozen=True)
class PublicRefreshDryRunExecutionPlanV6Result:
    valid: bool
    problems: tuple[str, ...]


class PublicRefreshDryRunExecutionPlanV6Error(ValueError):
    def __init__(self, problems: Iterable[str]) -> None:
        self.problems = tuple(problems)
        super().__init__('invalid public refresh dry-run execution plan v6: ' + '; '.join(self.problems))


def load_json(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(payload, dict):
        raise ValueError('public refresh dry-run execution plan fixture must be a JSON object')
    return payload


def build_public_refresh_dry_run_execution_plan_v6_from_fixture(path: str | Path) -> dict[str, Any]:
    fixture_path = Path(path)
    fixture = load_json(fixture_path)
    auth_fixture = _resolve(fixture_path, _text(fixture.get('public_refresh_authorization_packet_v6_fixture')))
    authorization_packet = build_public_refresh_authorization_packet_v6_from_fixture(auth_fixture)
    return build_public_refresh_dry_run_execution_plan_v6(
        authorization_packet,
        source_fixture_refs=[{'fixture_role': 'public_refresh_authorization_packet_v6', 'path': _text(fixture.get('public_refresh_authorization_packet_v6_fixture'))}],
    )


def build_public_refresh_dry_run_execution_plan_v6(
    authorization_packet: Mapping[str, Any],
    *,
    source_fixture_refs: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    assert_valid_public_refresh_authorization_packet_v6(authorization_packet)
    source_refs = list(source_fixture_refs or []) or [{'fixture_role': 'public_refresh_authorization_packet_v6', 'path': 'fixture://public_refresh_authorization_packet_v6'}]
    seed_groups = _ordered_seed_groups(authorization_packet)
    plan = {
        'packet_type': PACKET_TYPE,
        'packet_version': PACKET_VERSION,
        'packet_id': 'public-refresh-dry-run-execution-plan-v6-fixture',
        'mode': MODE,
        'consumes_only': {'public_refresh_authorization_packet_v6_fixtures': True},
        'source_fixture_refs': source_refs,
        'authorization_packet_ref': {
            'packet_type': _text(authorization_packet.get('packet_type')),
            'packet_version': _text(authorization_packet.get('packet_version')),
            'packet_id': _text(authorization_packet.get('packet_id')),
        },
        'boundaries': copy.deepcopy(BOUNDARIES),
        'ordered_seed_groups': seed_groups,
        'deterministic_crawl_window_placeholders': _crawl_window_placeholders(seed_groups),
        'allowlist_and_robots_recheck_expectations': _recheck_expectations(authorization_packet),
        'processor_dry_run_handoff_rows': _processor_handoff_rows(authorization_packet),
        'no_raw_body_manifest_only_output_expectations': _manifest_only_expectations(authorization_packet),
        'abort_on_drift_conditions': _abort_conditions(authorization_packet),
        'reviewer_go_no_go_placeholders': _reviewer_placeholders(authorization_packet),
        'exact_offline_validation_commands': copy.deepcopy(EXACT_OFFLINE_VALIDATION_COMMANDS),
        'validation_commands': copy.deepcopy(VALIDATION_COMMANDS),
    }
    assert_valid_public_refresh_dry_run_execution_plan_v6(plan)
    return plan


def assert_valid_public_refresh_dry_run_execution_plan_v6(packet: Mapping[str, Any]) -> None:
    result = validate_public_refresh_dry_run_execution_plan_v6(packet)
    if not result.valid:
        raise PublicRefreshDryRunExecutionPlanV6Error(result.problems)


def validate_public_refresh_dry_run_execution_plan_v6(packet: Mapping[str, Any]) -> PublicRefreshDryRunExecutionPlanV6Result:
    if not isinstance(packet, Mapping):
        return PublicRefreshDryRunExecutionPlanV6Result(False, ('packet must be an object',))
    problems: list[str] = []
    if packet.get('packet_type') != PACKET_TYPE:
        problems.append(f'packet_type must be {PACKET_TYPE}')
    if packet.get('packet_version') != PACKET_VERSION:
        problems.append('packet_version must be v6')
    if packet.get('mode') != MODE:
        problems.append(f'mode must be {MODE}')
    if packet.get('consumes_only') != {'public_refresh_authorization_packet_v6_fixtures': True}:
        problems.append('consumes_only must allow only public refresh authorization packet v6 fixtures')

    authorization_ref = _mapping(packet.get('authorization_packet_ref'))
    if not authorization_ref:
        problems.append('authorization_packet_ref must be present and reference public refresh authorization packet v6')
    elif authorization_ref.get('packet_type') != AUTH_PACKET_TYPE:
        problems.append('authorization_packet_ref must reference public refresh authorization packet v6')
    for ref_key in ('packet_type', 'packet_version', 'packet_id'):
        if not _text(authorization_ref.get(ref_key)):
            problems.append(f'authorization_packet_ref.{ref_key} is required')

    if packet.get('boundaries') != BOUNDARIES:
        problems.append('boundaries must deny live crawl, downloads, raw bodies, DevHub, private documents, official actions, guarantees, and mutation')
    if not _non_empty_sequence(packet.get('exact_offline_validation_commands')):
        problems.append('exact_offline_validation_commands must be a non-empty list')
    elif packet.get('exact_offline_validation_commands') != EXACT_OFFLINE_VALIDATION_COMMANDS:
        problems.append('exact_offline_validation_commands must exactly match public refresh dry-run execution plan v6 commands')
    if not _non_empty_sequence(packet.get('validation_commands')):
        problems.append('validation_commands must be a non-empty list')
    elif packet.get('validation_commands') != VALIDATION_COMMANDS:
        problems.append('validation_commands must contain only the PP&D daemon self-test command')

    for key in (
        'source_fixture_refs',
        'ordered_seed_groups',
        'deterministic_crawl_window_placeholders',
        'allowlist_and_robots_recheck_expectations',
        'processor_dry_run_handoff_rows',
        'no_raw_body_manifest_only_output_expectations',
        'abort_on_drift_conditions',
        'reviewer_go_no_go_placeholders',
    ):
        if not _non_empty_sequence(packet.get(key)):
            problems.append(f'{key} must be a non-empty list')

    _validate_source_refs(packet.get('source_fixture_refs'), problems)
    _validate_seed_groups(packet.get('ordered_seed_groups'), problems)
    _validate_windows(packet.get('deterministic_crawl_window_placeholders'), problems)
    _validate_rechecks(packet.get('allowlist_and_robots_recheck_expectations'), problems)
    _validate_processor_rows(packet.get('processor_dry_run_handoff_rows'), problems)
    _validate_manifest_only(packet.get('no_raw_body_manifest_only_output_expectations'), problems)
    _validate_abort_conditions(packet.get('abort_on_drift_conditions'), problems)
    _validate_reviewers(packet.get('reviewer_go_no_go_placeholders'), problems)
    _scan_for_forbidden_payload(packet, 'packet', problems)
    return PublicRefreshDryRunExecutionPlanV6Result(not problems, tuple(dict.fromkeys(problems)))


def _ordered_seed_groups(authorization_packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    preflight_by_source = {_text(row.get('source_id')): row for row in _mapping_sequence(authorization_packet.get('robots_and_policy_preflight_checklist_rows'))}
    deferrals_by_source = {_text(row.get('source_id')): row for row in _mapping_sequence(authorization_packet.get('live_crawl_deferral_criteria'))}
    groups = []
    for index, group in enumerate(_mapping_sequence(authorization_packet.get('allowlisted_source_groups')), start=1):
        source_ids = sorted(
            source_id
            for source_id, preflight in preflight_by_source.items()
            if _group_matches_source(_text(group.get('group_id')), source_id, _text(preflight.get('canonical_url')))
        )
        if not source_ids:
            source_ids = sorted(preflight_by_source)
        groups.append({
            'seed_group_order': index,
            'group_id': _text(group.get('group_id')),
            'reviewer_owner': _text(group.get('reviewer_owner')),
            'allowlist_scope': _text(group.get('allowlist_scope')),
            'source_ids': source_ids,
            'canonical_urls': [_text(preflight_by_source[source_id].get('canonical_url')) for source_id in source_ids],
            'deferral_required_source_ids': [source_id for source_id in source_ids if deferrals_by_source.get(source_id, {}).get('deferral_required') is True],
            'live_crawl_authorized': False,
        })
    return groups


def _crawl_window_placeholders(seed_groups: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [{
        'window_id': f'crawl-window-placeholder::{_text(group.get("group_id"))}',
        'seed_group_order': group.get('seed_group_order'),
        'group_id': _text(group.get('group_id')),
        'placeholder_start_at': 'pending_manual_go_decision',
        'placeholder_end_at': 'pending_manual_go_decision',
        'rate_limit_profile': 'not_applicable_offline_fixture_plan',
        'crawl_window_determined': False,
        'live_crawl_authorized': False,
    } for group in seed_groups]


def _recheck_expectations(authorization_packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(_mapping_sequence(authorization_packet.get('robots_and_policy_preflight_checklist_rows')), start=1):
        rows.append({
            'recheck_order': index,
            'source_id': _text(row.get('source_id')),
            'canonical_url': _text(row.get('canonical_url')),
            'allowlist_recheck_required': row.get('allowlist_check_required') is True,
            'robots_recheck_required': row.get('robots_check_required') is True,
            'policy_recheck_required': row.get('policy_check_required') is True,
            'expected_no_raw_body_policy': _text(row.get('no_raw_body_policy')),
            'recheck_completed': False,
            'crawl_authorized': False,
        })
    return rows


def _processor_handoff_rows(authorization_packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(_mapping_sequence(authorization_packet.get('processor_handoff_manifest_expectations')), start=1):
        rows.append({
            'handoff_order': index,
            'source_id': _text(row.get('source_id')),
            'processor_mode': 'dry_run_manifest_handoff_only',
            'expected_manifest_fields': list(row.get('expected_manifest_fields', [])),
            'no_raw_body_persisted_required': row.get('no_raw_body_persisted_required') is True,
            'raw_artifact_ref_allowed': False,
            'handoff_executed': False,
        })
    return rows


def _manifest_only_expectations(authorization_packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    reminders = [str(item) for item in authorization_packet.get('no_raw_body_persistence_reminders', [])]
    rows = []
    for row in _mapping_sequence(authorization_packet.get('processor_handoff_manifest_expectations')):
        rows.append({
            'expectation_id': f'manifest-only::{_text(row.get("source_id"))}',
            'source_id': _text(row.get('source_id')),
            'allowed_outputs': ['metadata_manifest', 'normalized_document_reference', 'content_hash', 'citation_spans'],
            'disallowed_outputs': ['raw_html_body', 'raw_pdf_body', 'browser_trace', 'har', 'screenshot', 'private_document', 'downloaded_document'],
            'no_raw_body_persisted_required': True,
            'reminder_count': len(reminders),
            'manifest_written': False,
            'raw_body_written': False,
        })
    return rows


def _abort_conditions(authorization_packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    thresholds = _mapping(authorization_packet.get('abort_thresholds'))
    return [{
        'abort_condition_id': f'abort-on-drift::{key}',
        'condition': str(key),
        'threshold': value,
        'abort_required_on_threshold': True,
        'current_observed_count': 0,
        'condition_triggered': False,
    } for key, value in sorted(thresholds.items())]


def _reviewer_placeholders(authorization_packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(_mapping_sequence(authorization_packet.get('reviewer_authorization_placeholders')), start=1):
        rows.append({
            'go_no_go_id': f'go-no-go::{_text(row.get("source_id"))}',
            'decision_order': index,
            'source_id': _text(row.get('source_id')),
            'reviewer_owner': _text(row.get('reviewer_owner')),
            'decision_status': 'pending_manual_go_no_go',
            'go_authorized': False,
            'no_go_reason': 'pending_review',
            'decided_by': '',
            'decided_at': '',
        })
    return rows


def _validate_source_refs(value: Any, problems: list[str]) -> None:
    rows = _mapping_sequence(value)
    roles = {_text(row.get('fixture_role')) for row in rows}
    if roles != {'public_refresh_authorization_packet_v6'}:
        problems.append('source_fixture_refs must reference only public_refresh_authorization_packet_v6 fixtures')
    for index, row in enumerate(rows):
        if not _text(row.get('path')):
            problems.append(f'source_fixture_refs[{index}].path is required')


def _validate_seed_groups(value: Any, problems: list[str]) -> None:
    expected_order = 1
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f'ordered_seed_groups[{index}]'
        if row.get('seed_group_order') != expected_order:
            problems.append(f'{prefix}.seed_group_order must be deterministic and contiguous')
        expected_order += 1
        if not _non_empty_sequence(row.get('source_ids')):
            problems.append(f'{prefix}.source_ids must be non-empty')
        if row.get('live_crawl_authorized') is not False:
            problems.append(f'{prefix}.live_crawl_authorized must be false')


def _validate_windows(value: Any, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f'deterministic_crawl_window_placeholders[{index}]'
        if row.get('crawl_window_determined') is not False or row.get('live_crawl_authorized') is not False:
            problems.append(f'{prefix} must remain placeholder-only and unauthorized')
        if row.get('placeholder_start_at') != 'pending_manual_go_decision' or row.get('placeholder_end_at') != 'pending_manual_go_decision':
            problems.append(f'{prefix} must use pending manual go-decision placeholders')


def _validate_rechecks(value: Any, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f'allowlist_and_robots_recheck_expectations[{index}]'
        for key in ('allowlist_recheck_required', 'robots_recheck_required', 'policy_recheck_required'):
            if row.get(key) is not True:
                problems.append(f'{prefix}.{key} must be true')
        if row.get('recheck_completed') is not False or row.get('crawl_authorized') is not False:
            problems.append(f'{prefix} must remain incomplete and unauthorized')


def _validate_processor_rows(value: Any, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f'processor_dry_run_handoff_rows[{index}]'
        fields = row.get('expected_manifest_fields')
        if not isinstance(fields, list) or 'no_raw_body_persisted' not in fields:
            problems.append(f'{prefix}.expected_manifest_fields must include no_raw_body_persisted')
        if row.get('processor_mode') != 'dry_run_manifest_handoff_only':
            problems.append(f'{prefix}.processor_mode must be dry_run_manifest_handoff_only')
        if row.get('raw_artifact_ref_allowed') is not False or row.get('handoff_executed') is not False:
            problems.append(f'{prefix} must not allow raw artifacts or executed handoff')


def _validate_manifest_only(value: Any, problems: list[str]) -> None:
    required_disallowed = {'raw_html_body', 'raw_pdf_body', 'browser_trace', 'har', 'screenshot', 'private_document', 'downloaded_document'}
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f'no_raw_body_manifest_only_output_expectations[{index}]'
        if row.get('no_raw_body_persisted_required') is not True:
            problems.append(f'{prefix}.no_raw_body_persisted_required must be true')
        if row.get('manifest_written') is not False or row.get('raw_body_written') is not False:
            problems.append(f'{prefix} must be output-expectation only with no writes')
        if not required_disallowed.issubset(set(row.get('disallowed_outputs', []))):
            problems.append(f'{prefix}.disallowed_outputs must block raw, browser, and private artifacts')


def _validate_abort_conditions(value: Any, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f'abort_on_drift_conditions[{index}]'
        if row.get('abort_required_on_threshold') is not True:
            problems.append(f'{prefix}.abort_required_on_threshold must be true')
        if row.get('current_observed_count') != 0 or row.get('condition_triggered') is not False:
            problems.append(f'{prefix} must be an untriggered offline placeholder')


def _validate_reviewers(value: Any, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f'reviewer_go_no_go_placeholders[{index}]'
        if row.get('decision_status') != 'pending_manual_go_no_go':
            problems.append(f'{prefix}.decision_status must be pending_manual_go_no_go')
        if row.get('go_authorized') is not False:
            problems.append(f'{prefix}.go_authorized must be false')
        if row.get('decided_by') or row.get('decided_at'):
            problems.append(f'{prefix} must not include completed reviewer decision data')


def _group_matches_source(group_id: str, source_id: str, canonical_url: str) -> bool:
    combined = f'{source_id} {canonical_url}'.lower()
    tokens_by_group = {
        'devhub_public_guidance': ('devhub',),
        'file_preparation_and_upload_guidance': ('submit-plans', 'file', 'spp'),
        'fee_payment_public_guidance': ('fee', 'pay'),
        'forms_index_and_public_forms': ('forms', 'applications'),
    }
    return any(token in combined for token in tokens_by_group.get(group_id, (group_id.lower(),)))


def _resolve(base: Path, value: str) -> Path:
    if not value:
        raise ValueError('fixture path is required')
    path = Path(value)
    if path.exists():
        return path
    return (base.parent / path).resolve()


def _scan_for_forbidden_payload(value: Any, path: str, problems: list[str]) -> None:
    if isinstance(value, Mapping):
        for raw_key, child in value.items():
            key = str(raw_key)
            normalized = key.lower().replace('-', '_')
            child_path = f'{path}.{key}'
            if normalized in FORBIDDEN_TRUE_KEYS and child is True:
                problems.append(f'{child_path} must not be true')
            if normalized not in ALLOWED_PRIVATE_SHAPING_KEYS and PRIVATE_KEY_RE.search(normalized) and _truthy(child):
                problems.append(f'{child_path} must not contain private, auth, browser, trace, raw, payment, session, or downloaded artifacts')
            if OFFICIAL_COMPLETION_KEY_RE.search(normalized) and _truthy(child):
                problems.append(f'{child_path} must not claim official action completion')
            if GUARANTEE_KEY_RE.search(normalized) and _truthy(child):
                problems.append(f'{child_path} must not contain legal or permitting guarantees')
            if ACTIVE_MUTATION_KEY_RE.search(normalized) and child is True:
                problems.append(f'{child_path} must not enable active mutation')
            _scan_for_forbidden_payload(child, child_path, problems)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _scan_for_forbidden_payload(child, f'{path}[{index}]', problems)


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _mapping_sequence(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _non_empty_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)) and bool(value)


def _truthy(value: Any) -> bool:
    if value is None or value is False or value == '':
        return False
    if isinstance(value, Mapping) and not value:
        return False
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)) and not value:
        return False
    return True


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ''
