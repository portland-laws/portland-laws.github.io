from __future__ import annotations

import re
from copy import deepcopy
from typing import Any, Iterable, Mapping, Sequence


ARTIFACT_ID = 'public_refresh_release_decision_packet_v1'
CANDIDATE_ROW_SOURCE = 'synthetic_inactive_promotion_candidate_rows'
DECISIONS = {'hold', 'proceed', 'skip'}

OFFLINE_VALIDATION_COMMANDS = [
    ['python3', '-m', 'py_compile', 'ppd/public_refresh_release_decision_packet_v1.py'],
    ['python3', '-m', 'pytest', 'ppd/tests/test_public_refresh_release_decision_packet_v1.py'],
    ['python3', 'ppd/daemon/ppd_daemon.py', '--self-test'],
]

FALSE_FLAGS = [
    'live_source_crawl_performed',
    'documents_downloaded',
    'raw_output_stored',
    'devhub_opened',
    'release_activated',
    'active_artifacts_mutated',
    'official_action_performed',
    'private_session_artifacts_created',
]

TRUE_ATTESTATIONS = [
    'fixture_first',
    'synthetic_rows_only',
    'inactive_candidates_only',
    'offline_validation_commands_only',
    'no_live_crawling',
    'no_document_downloads',
    'no_raw_output_storage',
    'no_devhub_access',
    'no_release_activation',
    'no_active_artifact_mutation',
    'no_official_actions',
]

_ACTIVE_MUTATION_FIELD_RE = re.compile(
    r'(^|_)(active_)?(artifact|artifacts|mutation|mutations|release|release_state|fixture|fixtures|guardrail|guardrails|prompt|prompts|agent_state)_(mutation|mutations|mutated|mutating|update|updated|write|writes|promotion|promoted|activation|activated)(_|$)|'
    r'(^|_)(mutates|mutated|updates|updated|writes|promotes|promoted|activates|activated)_(active_)?(artifact|artifacts|release|release_state|fixture|fixtures|guardrail|guardrails|prompt|prompts|agent_state)(_|$)',
    re.IGNORECASE,
)
_PRIVATE_FIELD_RE = re.compile(
    r'(auth[_-]?state|browser[_-]?(artifact|state)?|cookie|credential|download(ed)?|har|private|raw[_-]?(artifact|body|capture|crawl|data|download|html|output|pdf)?|screenshot|session[_-]?(artifact|state|storage)?|storage[_-]?state|token|trace)',
    re.IGNORECASE,
)
_PRIVATE_TEXT_RE = re.compile(
    r'(^file://)|(^/home/[^/]+/)|(^/Users/[^/]+/)|(^/tmp/)|\b(auth[_ -]?state|browser[_ -]?(artifact|state)|cookie|credential|downloaded[_ -]?(artifact|document|file|pdf)|downloaded\s+documents?|har\b|password|private[_ -]?(artifact|file|path|value)|raw[_ -]?(artifact|body|capture|crawl|data|download|html|output|pdf)|screenshot|session[_ -]?(artifact|state|storage)|storage[_ -]?state|token|trace[_ -]?(file|zip)?)\b',
    re.IGNORECASE,
)
_LIVE_TEXT_RE = re.compile(
    r'\b(live\s+(crawl|crawling|extraction|extractor|browser|devhub|execution|processor|run)|crawl(ed|ing)?\s+live|extracted\s+live|access(ed)?\s+devhub|logged\s+in\s+to\s+devhub|devhub\.portlandoregon\.gov|authenticated\s+devhub|used\s+authenticated\s+session)\b',
    re.IGNORECASE,
)
_RELEASE_TEXT_RE = re.compile(
    r'\b(release\s+(activated|activation\s+complete|promoted|promotion\s+complete|state\s+updated|enabled)|activated\s+release|promoted\s+(fixtures|release|to\s+active)|production\s+release\s+complete|active\s+release\s+enabled)\b',
    re.IGNORECASE,
)
_ARTIFACT_MUTATION_TEXT_RE = re.compile(
    r'\b(active\s+artifact(s)?\s+(mutated|updated|changed|written)|mutated\s+active\s+artifact(s)?|updated\s+active\s+artifact(s)?|changed\s+active\s+artifact(s)?)\b',
    re.IGNORECASE,
)
_OFFICIAL_ACTION_TEXT_RE = re.compile(
    r'\b(official\s+action\s+(completed|performed)|submitted\s+(the\s+)?permit|permit\s+submitted|submission\s+completed|paid\s+(the\s+)?fee|payment\s+completed|scheduled\s+(an?\s+)?inspection|cancel(l)?ed\s+(an?\s+)?inspection|certified\s+(the\s+)?application|uploaded\s+(corrections|plans|documents))\b',
    re.IGNORECASE,
)
_GUARANTEE_TEXT_RE = re.compile(
    r'\b(guaranteed\s+(approval|issuance|permit\s+outcome)|permit\s+will\s+be\s+(approved|issued)|approval\s+is\s+guaranteed|issuance\s+is\s+guaranteed|legal\s+(advice|guarantee)|permitting\s+guarantee)\b',
    re.IGNORECASE,
)
_COMMAND_FORBIDDEN_RE = re.compile(r'\b(live|crawl|crawler|extract|extraction|devhub|playwright|browser|network|auth|session|download|promote|activate)\b', re.IGNORECASE)


def build_public_refresh_release_decision_packet_v1(candidate_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    rows = [deepcopy(dict(row)) for row in candidate_rows if isinstance(row, Mapping)]
    decisions = [_decision_for_row(row) for row in rows]
    packet: dict[str, Any] = {
        'artifact_id': ARTIFACT_ID,
        'artifact_type': 'fixture_first_public_refresh_release_decision_packet',
        'version': 1,
        'status': 'review_ready',
        'candidate_rows_source': CANDIDATE_ROW_SOURCE,
        'consumed_candidate_rows': rows,
        'release_decisions': decisions,
        'unresolved_reviewer_blocker_summaries': _reviewer_blocker_summaries(rows),
        'validation_evidence_references': _validation_evidence_references(rows),
        'stale_source_hold_outcomes': _stale_source_hold_outcomes(rows, decisions),
        'rollback_decision_points': _rollback_decision_points(rows, decisions),
        'post_decision_smoke_expectations': _post_decision_smoke_expectations(decisions),
        'offline_validation_commands': deepcopy(OFFLINE_VALIDATION_COMMANDS),
        'attestations': {name: True for name in TRUE_ATTESTATIONS},
    }
    for flag in FALSE_FLAGS:
        packet[flag] = False
    result = validate_public_refresh_release_decision_packet_v1(packet)
    if not result['valid']:
        raise ValueError('; '.join(result['errors']))
    return packet


def validate_public_refresh_release_decision_packet_v1(packet: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if packet.get('artifact_id') != ARTIFACT_ID:
        errors.append(f'artifact_id must be {ARTIFACT_ID}')
    if packet.get('version') != 1:
        errors.append('version must be 1')
    if packet.get('candidate_rows_source') != CANDIDATE_ROW_SOURCE:
        errors.append(f'candidate_rows_source must be {CANDIDATE_ROW_SOURCE}')

    rows = _sequence(packet.get('consumed_candidate_rows'))
    decisions = _sequence(packet.get('release_decisions'))
    if not rows:
        errors.append('consumed_candidate_rows must include synthetic inactive promotion candidate references')
    if len(rows) != len(decisions):
        errors.append('release_decisions must include one decision per consumed candidate row')

    candidate_ids: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            errors.append(f'consumed_candidate_rows[{index}] must be an object')
            continue
        candidate_id = _text(row.get('candidate_id'))
        if not candidate_id:
            errors.append(f'consumed_candidate_rows[{index}].candidate_id is required')
        elif candidate_id in candidate_ids:
            errors.append(f'consumed_candidate_rows[{index}].candidate_id must be unique')
        else:
            candidate_ids.add(candidate_id)
        if row.get('synthetic') is not True:
            errors.append(f'consumed_candidate_rows[{index}].synthetic must be true')
        if row.get('inactive') is not True:
            errors.append(f'consumed_candidate_rows[{index}].inactive must be true')
        fixture_ref = _text(row.get('source_fixture_ref'))
        if not fixture_ref.startswith('ppd/tests/fixtures/'):
            errors.append(f'consumed_candidate_rows[{index}].source_fixture_ref must stay under ppd/tests/fixtures/')
        if not _string_list(row.get('validation_evidence_refs')):
            errors.append(f'consumed_candidate_rows[{index}].validation_evidence_refs must include fixture validation evidence references')

    decision_candidate_ids: set[str] = set()
    decision_values: set[str] = set()
    for index, row in enumerate(decisions):
        if not isinstance(row, Mapping):
            errors.append(f'release_decisions[{index}] must be an object')
            continue
        candidate_id = _text(row.get('candidate_id'))
        decision_candidate_ids.add(candidate_id)
        if candidate_id not in candidate_ids:
            errors.append(f'release_decisions[{index}].candidate_id must reference a consumed candidate row')
        decision = row.get('decision')
        if decision not in DECISIONS:
            errors.append(f'release_decisions[{index}].decision must be hold, proceed, or skip')
        else:
            decision_values.add(str(decision))
        if not _text(row.get('decision_reason')):
            errors.append(f'release_decisions[{index}].decision_reason is required')
        if row.get('active_release_mutation') is not False:
            errors.append(f'release_decisions[{index}].active_release_mutation must be false')
        if row.get('official_action_performed') is not False:
            errors.append(f'release_decisions[{index}].official_action_performed must be false')
        if not _string_list(row.get('citations')):
            errors.append(f'release_decisions[{index}].citations must include fixture citations')
    missing_decisions = DECISIONS - decision_values
    if missing_decisions:
        errors.append('release_decisions must include hold, proceed, and skip decisions')
    if candidate_ids and decision_candidate_ids != candidate_ids:
        errors.append('release_decisions must cover every inactive promotion candidate reference exactly once')

    _validate_blocker_summaries(errors, packet.get('unresolved_reviewer_blocker_summaries'), candidate_ids)
    _validate_validation_evidence(errors, packet.get('validation_evidence_references'), candidate_ids)
    _validate_stale_source_outcomes(errors, packet.get('stale_source_hold_outcomes'), candidate_ids)
    _validate_rollback_points(errors, packet.get('rollback_decision_points'), candidate_ids)
    _validate_smoke_expectations(errors, packet.get('post_decision_smoke_expectations'), candidate_ids)
    _validate_commands(errors, packet.get('offline_validation_commands'), 'offline_validation_commands')

    attestations = packet.get('attestations')
    if not isinstance(attestations, Mapping):
        errors.append('attestations must be an object')
    else:
        for name in TRUE_ATTESTATIONS:
            if attestations.get(name) is not True:
                errors.append(f'attestations.{name} must be true')

    for flag in FALSE_FLAGS:
        if packet.get(flag) is not False:
            errors.append(f'{flag} must be false')

    _reject_forbidden_content(errors, packet)
    return {'valid': not errors, 'errors': tuple(errors)}


def assert_valid_public_refresh_release_decision_packet_v1(packet: Mapping[str, Any]) -> None:
    result = validate_public_refresh_release_decision_packet_v1(packet)
    if not result['valid']:
        raise ValueError('; '.join(result['errors']))


def _decision_for_row(row: Mapping[str, Any]) -> dict[str, Any]:
    candidate_id = _text(row.get('candidate_id'), 'candidate')
    blockers = _string_list(row.get('unresolved_reviewer_blockers'))
    evidence_refs = _string_list(row.get('validation_evidence_refs'))
    stale = row.get('stale_source_detected') is True
    requested_decision = _text(row.get('requested_decision')).lower()
    if requested_decision == 'skip':
        decision = 'skip'
        reason = 'candidate row is explicitly marked for offline skip disposition'
    elif stale:
        decision = 'hold'
        reason = 'stale source signal requires reviewer hold before any release action'
    elif blockers:
        decision = 'hold'
        reason = 'unresolved reviewer blockers require hold disposition'
    elif not evidence_refs:
        decision = 'hold'
        reason = 'validation evidence references are missing'
    else:
        decision = 'proceed'
        reason = 'synthetic inactive row has evidence references and no unresolved blockers'
    return {
        'candidate_id': candidate_id,
        'decision': decision,
        'decision_reason': reason,
        'reviewer_owner': _text(row.get('reviewer_owner'), 'public-refresh-reviewer'),
        'active_release_mutation': False,
        'official_action_performed': False,
        'citations': [f'public-refresh-release-decision:v1:{candidate_id}'],
    }


def _reviewer_blocker_summaries(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            'candidate_id': _text(row.get('candidate_id'), 'candidate'),
            'unresolved_blocker_count': len(_string_list(row.get('unresolved_reviewer_blockers'))),
            'unresolved_blockers': _string_list(row.get('unresolved_reviewer_blockers')),
            'blocker_status': 'unresolved' if _string_list(row.get('unresolved_reviewer_blockers')) else 'none',
            'reviewer_owner': _text(row.get('reviewer_owner'), 'public-refresh-reviewer'),
            'citations': [f'public-refresh-reviewer-blocker-summary:v1:{_text(row.get("candidate_id"), "candidate")}'],
        }
        for row in rows
    ]


def _validation_evidence_references(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            'candidate_id': _text(row.get('candidate_id'), 'candidate'),
            'evidence_refs': _string_list(row.get('validation_evidence_refs')),
            'evidence_mode': 'synthetic_fixture_reference_only',
            'raw_output_stored': False,
            'citations': [f'public-refresh-validation-evidence:v1:{_text(row.get("candidate_id"), "candidate")}'],
        }
        for row in rows
    ]


def _stale_source_hold_outcomes(rows: Sequence[Mapping[str, Any]], decisions: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    decision_by_id = {_text(row.get('candidate_id')): row.get('decision') for row in decisions}
    outcomes = []
    for row in rows:
        candidate_id = _text(row.get('candidate_id'), 'candidate')
        stale = row.get('stale_source_detected') is True
        outcomes.append(
            {
                'candidate_id': candidate_id,
                'stale_source_detected': stale,
                'hold_required': stale,
                'decision': decision_by_id.get(candidate_id, 'hold' if stale else 'proceed'),
                'outcome': 'hold_for_freshness_review' if stale else 'no_stale_source_hold',
                'citations': [f'public-refresh-stale-source-hold:v1:{candidate_id}'],
            }
        )
    return outcomes


def _rollback_decision_points(rows: Sequence[Mapping[str, Any]], decisions: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    decision_by_id = {_text(row.get('candidate_id')): row.get('decision') for row in decisions}
    return [
        {
            'candidate_id': _text(row.get('candidate_id'), 'candidate'),
            'decision': decision_by_id.get(_text(row.get('candidate_id')), 'hold'),
            'rollback_point': 'discard synthetic packet and keep active artifacts unchanged',
            'rollback_validation_commands': deepcopy(OFFLINE_VALIDATION_COMMANDS),
            'citations': [f'public-refresh-rollback-decision-point:v1:{_text(row.get("candidate_id"), "candidate")}'],
        }
        for row in rows
    ]


def _post_decision_smoke_expectations(decisions: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            'candidate_id': _text(row.get('candidate_id'), 'candidate'),
            'decision': _text(row.get('decision'), 'hold'),
            'expected_smoke_result': 'offline_validation_passes_without_state_change',
            'commands': deepcopy(OFFLINE_VALIDATION_COMMANDS),
            'citations': [f'public-refresh-post-decision-smoke:v1:{_text(row.get("candidate_id"), "candidate")}'],
        }
        for row in decisions
    ]


def _validate_blocker_summaries(errors: list[str], value: Any, candidate_ids: set[str]) -> None:
    rows = _mapping_rows(value)
    if not rows:
        errors.append('unresolved_reviewer_blocker_summaries must include one row per inactive promotion candidate')
        return
    seen = _candidate_id_set(rows)
    if seen != candidate_ids:
        errors.append('unresolved_reviewer_blocker_summaries must cover every inactive promotion candidate')
    for index, row in enumerate(rows):
        path = f'unresolved_reviewer_blocker_summaries[{index}]'
        if not isinstance(row.get('unresolved_blocker_count'), int):
            errors.append(f'{path}.unresolved_blocker_count is required')
        if not isinstance(row.get('unresolved_blockers'), list):
            errors.append(f'{path}.unresolved_blockers must be a list')
        if row.get('blocker_status') not in {'none', 'unresolved'}:
            errors.append(f'{path}.blocker_status must be none or unresolved')
        if not _text(row.get('reviewer_owner')):
            errors.append(f'{path}.reviewer_owner is required')


def _validate_validation_evidence(errors: list[str], value: Any, candidate_ids: set[str]) -> None:
    rows = _mapping_rows(value)
    if not rows:
        errors.append('validation_evidence_references must include one row per inactive promotion candidate')
        return
    seen = _candidate_id_set(rows)
    if seen != candidate_ids:
        errors.append('validation_evidence_references must cover every inactive promotion candidate')
    for index, row in enumerate(rows):
        path = f'validation_evidence_references[{index}]'
        if not _string_list(row.get('evidence_refs')):
            errors.append(f'{path}.evidence_refs must include validation evidence references')
        if row.get('evidence_mode') != 'synthetic_fixture_reference_only':
            errors.append(f'{path}.evidence_mode must be synthetic_fixture_reference_only')
        if row.get('raw_output_stored') is not False:
            errors.append(f'{path}.raw_output_stored must be false')


def _validate_stale_source_outcomes(errors: list[str], value: Any, candidate_ids: set[str]) -> None:
    rows = _mapping_rows(value)
    if not rows:
        errors.append('stale_source_hold_outcomes must include one row per inactive promotion candidate')
        return
    seen = _candidate_id_set(rows)
    if seen != candidate_ids:
        errors.append('stale_source_hold_outcomes must cover every inactive promotion candidate')
    for index, row in enumerate(rows):
        path = f'stale_source_hold_outcomes[{index}]'
        if not isinstance(row.get('stale_source_detected'), bool):
            errors.append(f'{path}.stale_source_detected must be boolean')
        if not isinstance(row.get('hold_required'), bool):
            errors.append(f'{path}.hold_required must be boolean')
        if row.get('outcome') not in {'hold_for_freshness_review', 'no_stale_source_hold'}:
            errors.append(f'{path}.outcome must be hold_for_freshness_review or no_stale_source_hold')
        if row.get('stale_source_detected') is True and row.get('outcome') != 'hold_for_freshness_review':
            errors.append(f'{path}.outcome must hold stale sources for freshness review')
        if row.get('stale_source_detected') is True and row.get('decision') != 'hold':
            errors.append(f'{path}.decision must be hold when stale_source_detected is true')


def _validate_rollback_points(errors: list[str], value: Any, candidate_ids: set[str]) -> None:
    rows = _mapping_rows(value)
    if not rows:
        errors.append('rollback_decision_points must include one row per inactive promotion candidate')
        return
    seen = _candidate_id_set(rows)
    if seen != candidate_ids:
        errors.append('rollback_decision_points must cover every inactive promotion candidate')
    for index, row in enumerate(rows):
        path = f'rollback_decision_points[{index}]'
        if not _text(row.get('rollback_point')):
            errors.append(f'{path}.rollback_point is required')
        _validate_commands(errors, row.get('rollback_validation_commands'), f'{path}.rollback_validation_commands')


def _validate_smoke_expectations(errors: list[str], value: Any, candidate_ids: set[str]) -> None:
    rows = _mapping_rows(value)
    if not rows:
        errors.append('post_decision_smoke_expectations must include one row per inactive promotion candidate')
        return
    seen = _candidate_id_set(rows)
    if seen != candidate_ids:
        errors.append('post_decision_smoke_expectations must cover every inactive promotion candidate')
    for index, row in enumerate(rows):
        path = f'post_decision_smoke_expectations[{index}]'
        if row.get('expected_smoke_result') != 'offline_validation_passes_without_state_change':
            errors.append(f'{path}.expected_smoke_result must be offline_validation_passes_without_state_change')
        _validate_commands(errors, row.get('commands'), f'{path}.commands')


def _validate_commands(errors: list[str], value: Any, path: str) -> None:
    if value != OFFLINE_VALIDATION_COMMANDS:
        errors.append(f'{path} must exactly match the offline v1 command list')
        return
    for index, command in enumerate(_sequence(value)):
        if not _string_list(command) or _COMMAND_FORBIDDEN_RE.search(' '.join(command)):
            errors.append(f'{path}[{index}] must be an offline validation argv list without live, crawl, extraction, DevHub, browser, auth, session, download, promotion, or activation commands')


def _reject_forbidden_content(errors: list[str], value: Any) -> None:
    for path, child in _walk_values(value):
        name = _path_name(path).lower().replace('-', '_')
        if name and not name.startswith('no_') and _ACTIVE_MUTATION_FIELD_RE.search(name) and _active_value(child):
            errors.append(f'{path} must not include active mutation flags')
        if name and not name.startswith('no_') and _PRIVATE_FIELD_RE.search(name) and _present_value(child):
            errors.append(f'{path} must not include private, raw, downloaded, browser, session, or trace artifacts')
        if isinstance(child, str):
            if _PRIVATE_TEXT_RE.search(child):
                errors.append(f'{path} must not include private, raw, downloaded, browser, session, or trace artifact claims')
            if _LIVE_TEXT_RE.search(child):
                errors.append(f'{path} must not include live extraction, live crawl, or DevHub claims')
            if _RELEASE_TEXT_RE.search(child):
                errors.append(f'{path} must not include release activation claims')
            if _ARTIFACT_MUTATION_TEXT_RE.search(child):
                errors.append(f'{path} must not include active artifact mutation claims')
            if _OFFICIAL_ACTION_TEXT_RE.search(child):
                errors.append(f'{path} must not include official-action completion claims')
            if _GUARANTEE_TEXT_RE.search(child):
                errors.append(f'{path} must not include legal or permitting guarantees')


def _walk_values(value: Any, path: str = 'packet') -> Iterable[tuple[str, Any]]:
    yield path, value
    if isinstance(value, Mapping):
        for key, child in value.items():
            yield from _walk_values(child, f'{path}.{key}')
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            yield from _walk_values(child, f'{path}[{index}]')


def _mapping_rows(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _candidate_id_set(rows: Sequence[Mapping[str, Any]]) -> set[str]:
    return {_text(row.get('candidate_id')) for row in rows if _text(row.get('candidate_id'))}


def _sequence(value: Any) -> Sequence[Any]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return value
    return ()


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _text(value: Any, fallback: str = '') -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return fallback


def _path_name(path: str) -> str:
    if not path:
        return ''
    return path.rsplit('.', 1)[-1].split('[', 1)[0]


def _active_value(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, str):
        return value.strip().lower() in {'1', 'active', 'enabled', 'true', 'yes'}
    if isinstance(value, Mapping):
        return bool(value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return bool(value)
    return False


def _present_value(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return bool(value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return bool(value)
    return True
