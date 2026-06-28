"""Fixture-first inactive guardrail activation rehearsal v6.

Consumes only post-recompile release decision packet v6 fixtures and stages
reviewer-controlled activation rehearsal rows. The packet never activates
guardrails, opens DevHub, crawls live sites, reads private documents, uploads,
submits, certifies, pays, schedules, or makes legal/permitting guarantees.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
import copy
import json
from pathlib import Path
import re
from typing import Any

from ppd.agent_readiness.post_recompile_release_decision_packet_v6 import (
    validate_post_recompile_release_decision_packet_v6,
)

PACKET_TYPE = "ppd.inactive_guardrail_activation_rehearsal.v6"
PACKET_VERSION = "v6"
MODE = "fixture_first_inactive_guardrail_activation_rehearsal_v6"
SOURCE_PACKET_TYPE = "ppd.post_recompile_release_decision_packet.v6"
FIXTURE_DIR = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "inactive_guardrail_activation_rehearsal_v6"
DEFAULT_DECISION_PACKET_FIXTURE = FIXTURE_DIR / "post_recompile_release_decision_packet_v6_fixture.json"
EXACT_OFFLINE_VALIDATION_COMMANDS = [
    ["python3", "-m", "py_compile", "ppd/agent_readiness/inactive_guardrail_activation_rehearsal_v6.py"],
    ["python3", "-m", "unittest", "ppd.tests.test_inactive_guardrail_activation_rehearsal_v6"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]
VALIDATION_COMMANDS = [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]]

_REQUIRED_TRUE_FLAGS = (
    "fixture_first",
    "inactive_rehearsal_only",
    "post_recompile_release_decision_packet_v6_fixture_only",
    "manual_reviewer_activation_control_required",
    "source_freshness_review_required",
    "unresolved_hold_carry_forward_required",
    "smoke_replay_review_required",
    "rollback_threshold_review_required",
    "agent_notification_review_required",
    "monitoring_watch_review_required",
)

_REQUIRED_FALSE_FLAGS = (
    "guardrails_activated",
    "active_guardrail_mutation",
    "active_release_state_mutation",
    "activation_executed",
    "opens_devhub",
    "crawls_live_sites",
    "reads_private_documents",
    "uploads",
    "submits",
    "certifies",
    "pays",
    "schedules",
    "legal_or_permitting_guarantee",
)

_REQUIRED_SECTIONS = (
    "source_fixture_refs",
    "reviewer_activation_checklist_rows",
    "pre_activation_source_freshness_requirements",
    "unresolved_hold_carry_forward_rules",
    "smoke_replay_expectations",
    "rollback_trigger_thresholds",
    "agent_notification_placeholders",
    "monitoring_watch_rows",
    "offline_validation_commands",
    "validation_commands",
)

_FORBIDDEN_KEY_RE = re.compile(
    r"(^|_)(auth|browser|cookie|credential|devhub[_-]?session|downloaded|har|password|payment|private|raw|screenshot|session|storage[_-]?state|token|trace)(_|$)",
    re.IGNORECASE,
)
_FORBIDDEN_TEXT_RULES = (
    ("active guardrail claim", re.compile(r"\b(?:activated guardrails|guardrails activated|release is active|promoted to active|active guardrails deployed)\b", re.IGNORECASE)),
    ("live crawl or DevHub claim", re.compile(r"\b(?:opened devhub|logged in|authenticated devhub|live crawl completed|ran live crawl|crawled live sites)\b", re.IGNORECASE)),
    ("private artifact claim", re.compile(r"\b(?:cookie|credential|password|private document|session token|storage state|trace file|har file|screenshot artifact|raw crawl output|downloaded document)\b", re.IGNORECASE)),
    ("official-action completion claim", re.compile(r"\b(?:submitted|uploaded to the official record|certified|paid fee|scheduled inspection|official action completed)\b", re.IGNORECASE)),
    ("legal or permitting guarantee", re.compile(r"\b(?:legal advice|permit approval guaranteed|guaranteed approval|will be approved|will receive a permit)\b", re.IGNORECASE)),
)


@dataclass(frozen=True)
class InactiveGuardrailActivationRehearsalV6Result:
    valid: bool
    problems: tuple[str, ...]


class InactiveGuardrailActivationRehearsalV6Error(ValueError):
    def __init__(self, problems: Iterable[str]) -> None:
        self.problems = tuple(problems)
        super().__init__("invalid inactive guardrail activation rehearsal v6: " + "; ".join(self.problems))


def load_post_recompile_release_decision_packet_v6_fixture(path: str | Path = DEFAULT_DECISION_PACKET_FIXTURE) -> dict[str, Any]:
    loaded = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("post-recompile release decision packet v6 fixture must be a JSON object")
    _assert_source_decision_packet(loaded)
    return loaded


def build_inactive_guardrail_activation_rehearsal_v6_from_fixture(
    decision_packet_fixture_path: str | Path = DEFAULT_DECISION_PACKET_FIXTURE,
) -> dict[str, Any]:
    fixture_path = Path(decision_packet_fixture_path)
    decision_packet = load_post_recompile_release_decision_packet_v6_fixture(fixture_path)
    return build_inactive_guardrail_activation_rehearsal_v6(decision_packet, decision_packet_fixture_ref=fixture_path.as_posix())


def build_inactive_guardrail_activation_rehearsal_v6(
    decision_packet: Mapping[str, Any], *, decision_packet_fixture_ref: str
) -> dict[str, Any]:
    _assert_source_decision_packet(decision_packet)
    hold_rows = _mapping_sequence(decision_packet.get("unresolved_hold_inventory"))
    go_no_go_rows = _mapping_sequence(decision_packet.get("go_no_go_rows"))

    packet = {
        "packet_type": PACKET_TYPE,
        "packet_version": PACKET_VERSION,
        "mode": MODE,
        "fixture_first": True,
        "inactive_rehearsal_only": True,
        "post_recompile_release_decision_packet_v6_fixture_only": True,
        "manual_reviewer_activation_control_required": True,
        "source_freshness_review_required": True,
        "unresolved_hold_carry_forward_required": True,
        "smoke_replay_review_required": True,
        "rollback_threshold_review_required": True,
        "agent_notification_review_required": True,
        "monitoring_watch_review_required": True,
        "guardrails_activated": False,
        "active_guardrail_mutation": False,
        "active_release_state_mutation": False,
        "activation_executed": False,
        "opens_devhub": False,
        "crawls_live_sites": False,
        "reads_private_documents": False,
        "uploads": False,
        "submits": False,
        "certifies": False,
        "pays": False,
        "schedules": False,
        "legal_or_permitting_guarantee": False,
        "source_fixture_refs": [
            {
                "fixture_role": "post_recompile_release_decision_packet_v6",
                "packet_type": SOURCE_PACKET_TYPE,
                "path": decision_packet_fixture_ref,
            }
        ],
        "consumes_only": {
            "post_recompile_release_decision_packet_v6_fixtures": True,
            "packet_type": SOURCE_PACKET_TYPE,
        },
        "reviewer_activation_checklist_rows": _reviewer_checklist_rows(decision_packet),
        "pre_activation_source_freshness_requirements": _source_freshness_rows(decision_packet),
        "unresolved_hold_carry_forward_rules": _hold_carry_forward_rows(hold_rows),
        "smoke_replay_expectations": _smoke_replay_rows(go_no_go_rows),
        "rollback_trigger_thresholds": _rollback_threshold_rows(decision_packet),
        "agent_notification_placeholders": _agent_notification_rows(decision_packet),
        "monitoring_watch_rows": _monitoring_watch_rows(decision_packet),
        "offline_validation_commands": copy.deepcopy(EXACT_OFFLINE_VALIDATION_COMMANDS),
        "validation_commands": copy.deepcopy(VALIDATION_COMMANDS),
    }
    assert_valid_inactive_guardrail_activation_rehearsal_v6(packet)
    return packet


def assert_valid_inactive_guardrail_activation_rehearsal_v6(packet: Mapping[str, Any]) -> None:
    result = validate_inactive_guardrail_activation_rehearsal_v6(packet)
    if not result.valid:
        raise InactiveGuardrailActivationRehearsalV6Error(result.problems)


def validate_inactive_guardrail_activation_rehearsal_v6(
    packet: Mapping[str, Any],
) -> InactiveGuardrailActivationRehearsalV6Result:
    if not isinstance(packet, Mapping):
        return InactiveGuardrailActivationRehearsalV6Result(False, ("packet must be an object",))

    problems: list[str] = []
    if packet.get("packet_type") != PACKET_TYPE:
        problems.append(f"packet_type must be {PACKET_TYPE}")
    if packet.get("packet_version") != PACKET_VERSION:
        problems.append("packet_version must be v6")
    if packet.get("mode") != MODE:
        problems.append(f"mode must be {MODE}")
    if packet.get("offline_validation_commands") != EXACT_OFFLINE_VALIDATION_COMMANDS:
        problems.append("offline_validation_commands must exactly match inactive guardrail activation rehearsal v6 commands")
    if packet.get("validation_commands") != VALIDATION_COMMANDS:
        problems.append("validation_commands must contain only the PP&D daemon self-test command")

    for key in _REQUIRED_TRUE_FLAGS:
        if packet.get(key) is not True:
            problems.append(f"{key} must be true")
    for key in _REQUIRED_FALSE_FLAGS:
        if packet.get(key) is not False:
            problems.append(f"{key} must be false")
    for section in _REQUIRED_SECTIONS:
        if not _non_empty_sequence(packet.get(section)):
            problems.append(f"{section} must be a non-empty list")

    _validate_source_refs(packet, problems)
    _validate_rows(packet, problems)
    _validate_forbidden_payload(packet, problems)
    return InactiveGuardrailActivationRehearsalV6Result(not problems, tuple(dict.fromkeys(problems)))


def _assert_source_decision_packet(packet: Mapping[str, Any]) -> None:
    result = validate_post_recompile_release_decision_packet_v6(packet)
    if not result.valid:
        raise ValueError("source decision packet v6 fixture is invalid: " + "; ".join(result.problems))
    if packet.get("packet_type") != SOURCE_PACKET_TYPE:
        raise ValueError(f"activation rehearsal v6 consumes only {SOURCE_PACKET_TYPE} fixtures")
    if packet.get("activation_executed") is not False or packet.get("opens_devhub") is not False:
        raise ValueError("source decision packet must be inactive and offline-only")


def _validate_source_refs(packet: Mapping[str, Any], problems: list[str]) -> None:
    refs = _mapping_sequence(packet.get("source_fixture_refs"))
    if not any(ref.get("fixture_role") == "post_recompile_release_decision_packet_v6" and ref.get("packet_type") == SOURCE_PACKET_TYPE and _text(ref.get("path")) for ref in refs):
        problems.append("source_fixture_refs must include a post-recompile release decision packet v6 fixture reference")
    consumes = packet.get("consumes_only")
    if not isinstance(consumes, Mapping) or consumes.get("post_recompile_release_decision_packet_v6_fixtures") is not True:
        problems.append("consumes_only must require post-recompile release decision packet v6 fixtures")
    if isinstance(consumes, Mapping) and consumes.get("packet_type") != SOURCE_PACKET_TYPE:
        problems.append(f"consumes_only.packet_type must be {SOURCE_PACKET_TYPE}")


def _validate_rows(packet: Mapping[str, Any], problems: list[str]) -> None:
    row_rules = (
        ("reviewer_activation_checklist_rows", "checklist_row_id", "reviewer_controlled", True),
        ("pre_activation_source_freshness_requirements", "freshness_requirement_id", "blocks_rehearsed_activation", True),
        ("unresolved_hold_carry_forward_rules", "carry_forward_rule_id", "carry_forward_required", True),
        ("smoke_replay_expectations", "smoke_replay_expectation_id", "must_pass_before_activation_review", True),
        ("rollback_trigger_thresholds", "rollback_threshold_id", "reviewer_threshold_required", True),
        ("agent_notification_placeholders", "notification_placeholder_id", "sent", False),
        ("monitoring_watch_rows", "monitoring_watch_id", "watch_required", True),
    )
    for section, id_key, status_key, expected in row_rules:
        value = packet.get(section)
        if _non_empty_sequence(value) and len(_mapping_sequence(value)) != len(value):
            problems.append(f"{section} must contain only object rows")
        for index, row in enumerate(_mapping_sequence(value)):
            prefix = f"{section}[{index}]"
            if not _text(row.get(id_key)):
                problems.append(f"{prefix}.{id_key} is required")
            if row.get(status_key) != expected:
                problems.append(f"{prefix}.{status_key} must be {expected!r}")
            if row.get("activation_allowed") is not False:
                problems.append(f"{prefix}.activation_allowed must be False")


def _reviewer_checklist_rows(decision_packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    recommendation = _text(decision_packet.get("overall_recommendation")) or "manual_review_required"
    return [
        {
            "checklist_row_id": "activation-checklist::reviewer-disposition",
            "source_decision_packet": SOURCE_PACKET_TYPE,
            "source_recommendation": recommendation,
            "reviewer_controlled": True,
            "activation_allowed": False,
            "required_reviewer_action": "Confirm the decision packet, holds, freshness, smoke replay, rollback thresholds, notifications, and monitoring rows in a separate manual review.",
        },
        {
            "checklist_row_id": "activation-checklist::consequential-action-boundary",
            "source_decision_packet": SOURCE_PACKET_TYPE,
            "reviewer_controlled": True,
            "activation_allowed": False,
            "required_reviewer_action": "Keep upload, submission, certification, payment, scheduling, and official-change paths outside this rehearsal.",
        },
    ]


def _source_freshness_rows(decision_packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    source_rows = _mapping_sequence(decision_packet.get("citation_continuity_summaries"))
    statuses = []
    for row in source_rows:
        row_statuses = row.get("evidence_statuses")
        if isinstance(row_statuses, Sequence) and not isinstance(row_statuses, (str, bytes, bytearray)):
            statuses.extend(str(value) for value in row_statuses)
    return [
        {
            "freshness_requirement_id": "source-freshness::public-citation-review",
            "source_decision_packet": SOURCE_PACKET_TYPE,
            "evidence_statuses": sorted(set(statuses)) or ["manual_review_required"],
            "required_before_activation_review": "Reviewer must confirm public source freshness from approved offline evidence before any separate activation review.",
            "blocks_rehearsed_activation": True,
            "activation_allowed": False,
        }
    ]


def _hold_carry_forward_rows(hold_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = hold_rows or [{"hold_id": "hold::manual-review-placeholder", "hold_status": "placeholder_pending_manual_release_review"}]
    return [
        {
            "carry_forward_rule_id": f"carry-forward::{_text(row.get('hold_id')) or 'manual-review-placeholder'}",
            "source_hold_id": _text(row.get("hold_id")) or "hold::manual-review-placeholder",
            "source_hold_status": _text(row.get("hold_status")) or "manual_review_required",
            "carry_forward_required": True,
            "activation_allowed": False,
            "rule": "Carry this hold into reviewer activation control until a separate reviewer disposition resolves it.",
        }
        for row in rows
    ]


def _smoke_replay_rows(go_no_go_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    source_ids = [_text(row.get("row_id")) for row in go_no_go_rows if _text(row.get("row_id"))]
    return [
        {
            "smoke_replay_expectation_id": "smoke-replay::post-release-decision-v6",
            "source_go_no_go_row_ids": source_ids,
            "expected_scope": "Replay fixture-only missing-information, stale-evidence, reversible-draft, confirmation, refusal, rollback, notification, and manual-handoff paths before any separate review.",
            "must_pass_before_activation_review": True,
            "activation_allowed": False,
        }
    ]


def _rollback_threshold_rows(decision_packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    rollback_rows = _mapping_sequence(decision_packet.get("rollback_owner_placeholders"))
    owner_statuses = [_text(row.get("owner_assignment_status")) for row in rollback_rows if _text(row.get("owner_assignment_status"))]
    return [
        {
            "rollback_threshold_id": "rollback-threshold::manual-owner-and-hold-stop",
            "source_owner_assignment_statuses": owner_statuses or ["pending_manual_assignment"],
            "threshold": "Any unresolved hold, missing rollback owner, failed smoke replay, stale source, or unexpected agent response keeps activation disallowed.",
            "reviewer_threshold_required": True,
            "activation_allowed": False,
        }
    ]


def _agent_notification_rows(decision_packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    recommendation = _text(decision_packet.get("overall_recommendation")) or "manual_review_required"
    return [
        {
            "notification_placeholder_id": "agent-notification::inactive-rehearsal-v6",
            "source_recommendation": recommendation,
            "draft_message_kind": "reviewer_controlled_activation_rehearsal_notice",
            "sent": False,
            "activation_allowed": False,
            "message_placeholder": "Notify agents only after reviewer approval in a separate process; this row is a placeholder and sends nothing.",
        }
    ]


def _monitoring_watch_rows(decision_packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    monitoring_rows = _mapping_sequence(decision_packet.get("monitoring_handoff_reminders"))
    reminder_ids = [_text(row.get("monitoring_reminder_id")) for row in monitoring_rows if _text(row.get("monitoring_reminder_id"))]
    return [
        {
            "monitoring_watch_id": "monitoring-watch::inactive-activation-rehearsal-v6",
            "source_monitoring_reminder_ids": reminder_ids,
            "watch_required": True,
            "activation_allowed": False,
            "watch_scope": "Watch source freshness, unresolved holds, smoke replay outcomes, rollback owner assignment, and agent notification readiness after reviewer review.",
        }
    ]


def _validate_forbidden_payload(packet: Mapping[str, Any], problems: list[str]) -> None:
    allowed_path_keys = {"packet.source_fixture_refs[0].path"}
    allowed_command_keys = {"validation_commands", "offline_validation_commands"}
    for path, key, value in _walk(packet):
        normalized_key = key.lower().replace("-", "_")
        if normalized_key in _REQUIRED_FALSE_FLAGS and value is not False:
            problems.append(f"{path} must be false")
        if normalized_key not in allowed_command_keys and path not in allowed_path_keys:
            if _FORBIDDEN_KEY_RE.search(normalized_key) and _truthy(value):
                problems.append(f"{path} must not include private, session, auth, raw, browser, trace, payment, or downloaded artifacts")
        if isinstance(value, str):
            for label, pattern in _FORBIDDEN_TEXT_RULES:
                if pattern.search(value):
                    problems.append(f"{path} contains forbidden {label}")


def _walk(value: Any, prefix: str = "packet", key: str = "packet") -> Iterable[tuple[str, str, Any]]:
    if isinstance(value, Mapping):
        for child_key, child_value in value.items():
            child_key_text = str(child_key)
            child_path = f"{prefix}.{child_key_text}"
            yield child_path, child_key_text, child_value
            yield from _walk(child_value, child_path, child_key_text)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child_value in enumerate(value):
            child_path = f"{prefix}[{index}]"
            yield child_path, key, child_value
            yield from _walk(child_value, child_path, key)


def _mapping_sequence(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _non_empty_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)) and bool(value)


def _truthy(value: Any) -> bool:
    if value is None or value is False or value == "":
        return False
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)) and not value:
        return False
    if isinstance(value, Mapping) and not value:
        return False
    return True


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""
