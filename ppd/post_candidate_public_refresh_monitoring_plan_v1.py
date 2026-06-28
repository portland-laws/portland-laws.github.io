'''Fixture-first post-candidate public-refresh monitoring plan v1 validation.'''

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import re
from typing import Any

PACKET_TYPE = 'ppd.post_candidate_public_refresh_monitoring_plan.v1'
VALIDATION_COMMANDS = [['python3', 'ppd/daemon/ppd_daemon.py', '--self-test']]

REQUIRED_CATEGORIES = {
    'official_ppd_anchors': 'official PP&D anchors',
    'file_preparation_guidance': 'file-preparation guidance',
    'fee_payment_guidance': 'fee/payment guidance',
    'devhub_public_guidance': 'DevHub public guidance',
    'forms_index': 'forms index',
    'linked_portland_maps_references': 'linked Portland Maps references',
}

_PRIVATE_FIELD_RE = re.compile(r'(auth|browser|cookie|credential|download|har|private|raw|screenshot|session|storage_state|token|trace)', re.IGNORECASE)
_PRIVATE_TEXT_RE = re.compile(r'(^file://)|(^/home/[^/]+/)|(^/Users/[^/]+/)|(^/root/)|(^/tmp/)|(auth[_ -]?state|browser[_ -]?(profile|state)|cookie|credential|downloaded?[_ -]?(document|file|pdf)|har\b|private[_ -]?(file|path|value)|raw[_ -]?(body|capture|crawl|data|download|html|pdf)|screenshot|session[_ -]?(state|storage)|storage[_ -]?state|token|trace)', re.IGNORECASE)
_LIVE_TEXT_RE = re.compile(r'\b(live\s+(crawl|crawler|devhub|browser|fetch|monitor|run)|ran\s+(crawl|crawler|devhub|browser|fetch|monitor)|opened\s+(devhub|a browser)|accessed\s+devhub|logged\s+in\s+to\s+devhub|downloaded\s+(a\s+)?document)\b', re.IGNORECASE)
_SCHEDULER_FIELD_RE = re.compile(r'(scheduler|schedule|cron|job|timer).*(mutation|mutating|update|write|enable|activation|active)|(mutates|updates|writes|enables|activates).*(scheduler|schedule|cron|job|timer)', re.IGNORECASE)
_ACTIVE_FIELD_RE = re.compile(r'(active_)?(source|archive|document|requirement|process|process_model|guardrail|prompt|release|crawler|daemon|scheduler|monitoring).*(mutation|mutating|update|write|promotion|refresh|state)|(mutates|updates|promotes|refreshes|writes).*(sources|archives|documents|requirements|processes|guardrails|prompts|releases|crawlers|daemons)', re.IGNORECASE)
_ACTIVE_TEXT_RE = re.compile(r'\b(mutates?|updates?|writes?|promotes?|refreshes?|enables?|activates?)\s+(active\s+)?(source|archive|document|requirement|process|process-model|guardrail|prompt|release|crawler|daemon|scheduler|schedule|monitoring)\b', re.IGNORECASE)


@dataclass(frozen=True)
class PostCandidatePublicRefreshMonitoringPlanV1Result:
    ready: bool
    problems: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {'ready': self.ready, 'problems': list(self.problems)}


def validate_post_candidate_public_refresh_monitoring_plan_v1(packet: Mapping[str, Any]) -> PostCandidatePublicRefreshMonitoringPlanV1Result:
    problems: list[str] = []
    if packet.get('packet_type') != PACKET_TYPE:
        problems.append(f'packet_type must be {PACKET_TYPE}')
    if packet.get('validation_commands') != VALIDATION_COMMANDS:
        problems.append('validation_commands must contain only the exact PP&D daemon self-test command')

    covered = _covered_categories(packet)
    for category, label in REQUIRED_CATEGORIES.items():
        if category not in covered:
            problems.append(f'missing {label} coverage')

    checks = _mapping_sequence(packet.get('synthetic_follow_up_freshness_checks'))
    if not checks:
        problems.append('synthetic_follow_up_freshness_checks must include scheduled fixture-first checks')

    scheduled: set[str] = set()
    for index, check in enumerate(checks):
        path = f'synthetic_follow_up_freshness_checks[{index}]'
        if not _nonempty_text(check.get('check_id')):
            problems.append(f'{path} lacks check_id')
        if not _nonempty_text(check.get('schedule')):
            problems.append(f'{path} lacks schedule')
        if not _text_list(check.get('source_evidence_ids')):
            problems.append(f'{path} lacks source_evidence_ids')
        if not _nonempty_mapping(check.get('hold_thresholds')):
            problems.append(f'{path} lacks hold thresholds')
        if not _has_reviewer_routing(check):
            problems.append(f'{path} lacks reviewer routing')
        scheduled.update(_categories_from_value(check.get('coverage_categories')))

    for category, label in REQUIRED_CATEGORIES.items():
        if category not in scheduled:
            problems.append(f'missing scheduled synthetic check for {label}')

    if not _has_reviewer_routing(packet):
        problems.append('packet lacks reviewer routing')
    problems.extend(_safety_problems(packet))
    return PostCandidatePublicRefreshMonitoringPlanV1Result(ready=not problems, problems=tuple(problems))


def require_post_candidate_public_refresh_monitoring_plan_v1(packet: Mapping[str, Any]) -> None:
    result = validate_post_candidate_public_refresh_monitoring_plan_v1(packet)
    if not result.ready:
        raise ValueError('invalid_post_candidate_public_refresh_monitoring_plan_v1: ' + '; '.join(result.problems))


def _covered_categories(packet: Mapping[str, Any]) -> set[str]:
    found: set[str] = set()
    for key in ('coverage', 'coverage_matrix', 'monitoring_coverage', 'required_coverage', 'normalized_source_evidence'):
        found.update(_categories_from_value(packet.get(key)))
    return found


def _categories_from_value(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = _category_name(str(key))
            if normalized in REQUIRED_CATEGORIES and child not in (None, False, '', [], {}):
                found.add(normalized)
            if str(key) in {'coverage_categories', 'coverage_tags', 'categories', 'source_roles', 'required_coverage'}:
                found.update(_categories_from_value(child))
            elif isinstance(child, (Mapping, list, tuple)):
                found.update(_categories_from_value(child))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            found.update(_categories_from_value(item))
    elif isinstance(value, str):
        normalized = _category_name(value)
        if normalized in REQUIRED_CATEGORIES:
            found.add(normalized)
    return found


def _category_name(value: str) -> str:
    return value.strip().lower().replace('-', '_').replace(' ', '_')


def _safety_problems(value: Any, path: str = '$') -> list[str]:
    problems: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f'{path}.{key}'
            key_text = str(key)
            if _PRIVATE_FIELD_RE.search(key_text) and child not in (None, False, '', [], {}):
                problems.append(f'private, live, raw, browser, or downloaded artifact field is not allowed at {child_path}')
            if _SCHEDULER_FIELD_RE.search(key_text) and child not in (None, False, '', [], {}):
                problems.append(f'scheduler-state mutation claim is not allowed at {child_path}')
            if _ACTIVE_FIELD_RE.search(key_text) and child is True:
                problems.append(f'active PP&D state mutation flag is not allowed at {child_path}')
            problems.extend(_safety_problems(child, child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            problems.extend(_safety_problems(item, f'{path}[{index}]'))
    elif isinstance(value, str):
        if _PRIVATE_TEXT_RE.search(value):
            problems.append(f'private, live, raw, browser, or downloaded artifact text is not allowed at {path}')
        if _LIVE_TEXT_RE.search(value):
            problems.append(f'live crawl, DevHub, browser, or download claim is not allowed at {path}')
        if _ACTIVE_TEXT_RE.search(value):
            problems.append(f'active PP&D state mutation claim is not allowed at {path}')
    return problems


def _has_reviewer_routing(value: Mapping[str, Any]) -> bool:
    routing = value.get('reviewer_routing') or value.get('reviewer_route') or value.get('reviewer_owner')
    if isinstance(routing, str):
        return bool(routing.strip())
    if isinstance(routing, Mapping):
        return any(_nonempty_text(routing.get(key)) for key in ('primary_reviewer', 'reviewer_owner', 'escalation_reviewer', 'route_id'))
    if isinstance(routing, Sequence) and not isinstance(routing, (str, bytes, bytearray)):
        return any(item not in (None, False, '', [], {}) for item in routing)
    return False


def _mapping_sequence(value: Any) -> list[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        return [value]
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [item for item in value if isinstance(item, Mapping)]
    return []


def _text_list(value: Any) -> list[str]:
    if isinstance(value, str) and value.strip():
        return [value]
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [item for item in value if isinstance(item, str) and item.strip()]
    return []


def _nonempty_mapping(value: Any) -> bool:
    return isinstance(value, Mapping) and bool(value)


def _nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())
