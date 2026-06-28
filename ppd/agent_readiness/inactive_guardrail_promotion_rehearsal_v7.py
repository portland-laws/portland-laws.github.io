"""Fixture-first inactive guardrail promotion rehearsal v7.

This packet consumes only post-recompile release decision packet v7 fixtures and
assembles reviewer-controlled inactive promotion rehearsal rows. It does not
activate guardrails or perform portal, crawl, upload, submission, certification,
payment, scheduling, or legal/permitting outcome work.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
import copy
import json
from pathlib import Path
import re
from typing import Any

from ppd.agent_readiness.post_recompile_release_decision_packet_v7 import (
    PACKET_TYPE as RELEASE_DECISION_PACKET_TYPE,
    PACKET_VERSION as RELEASE_DECISION_PACKET_VERSION,
    assert_valid_post_recompile_release_decision_packet_v7,
)

PACKET_TYPE = "ppd.inactive_guardrail_promotion_rehearsal.v7"
PACKET_VERSION = "v7"
MODE = "fixture_first_inactive_guardrail_promotion_rehearsal_v7"
INACTIVE_STATUS = "inactive_rehearsal_only"
FIXTURE_DIR = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "inactive_guardrail_promotion_rehearsal_v7"
DEFAULT_RELEASE_DECISION_FIXTURE = FIXTURE_DIR / "post_recompile_release_decision_packet_v7.json"

EXACT_OFFLINE_VALIDATION_COMMANDS = [
    ["python3", "-m", "py_compile", "ppd/agent_readiness/inactive_guardrail_promotion_rehearsal_v7.py"],
    ["python3", "-m", "unittest", "ppd.tests.test_inactive_guardrail_promotion_rehearsal_v7"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]
VALIDATION_COMMANDS = [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]]

_REQUIRED_TRUE_FLAGS = (
    "fixture_first",
    "inactive_guardrail_promotion_rehearsal_only",
    "post_recompile_release_decision_packet_v7_fixtures_only",
    "reviewer_controlled_checklist_required",
    "unresolved_hold_carry_forward_required",
    "pre_promotion_source_freshness_required",
    "agent_notification_placeholders_required",
    "rollback_checkpoint_references_required",
    "monitoring_watch_required",
    "manual_reviewer_signoff_required",
)

_REQUIRED_FALSE_FLAGS = (
    "active_guardrail_mutation",
    "active_guardrail_bundle_mutation",
    "active_prompt_mutation",
    "active_process_model_mutation",
    "active_requirement_mutation",
    "active_source_mutation",
    "active_devhub_surface_mutation",
    "active_release_state_mutation",
    "active_mutation",
    "guardrails_changed",
    "guardrail_bundles_changed",
    "promotion_executed",
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

_REQUIRED_LISTS = (
    "source_fixture_refs",
    "reviewer_controlled_promotion_checklist_rows",
    "unresolved_hold_carry_forward_conditions",
    "pre_promotion_source_freshness_reminders",
    "agent_notification_placeholders",
    "rollback_checkpoint_references",
    "monitoring_watch_rows",
    "offline_validation_commands",
    "validation_commands",
)

_PRIVATE_KEY_RE = re.compile(
    r"(^|_)(auth|browser|cookie|credential|devhub[_-]?session|download|downloaded|har|password|payment|private|raw|screenshot|session|storage[_-]?state|token|trace)(_|$)",
    re.IGNORECASE,
)
_FORBIDDEN_TEXT_RULES = (
    ("activation claim", re.compile(r"\b(?:activated|release is active|promoted to active|active guardrails deployed)\b", re.IGNORECASE)),
    ("live system claim", re.compile(r"\b(?:live crawl|opened devhub|logged in|authenticated devhub|live browser)\b", re.IGNORECASE)),
    ("artifact claim", re.compile(r"\b(?:cookie|credential|password|private document|session token|storage state|trace file|har file|screenshot artifact|raw crawl output|downloaded document)\b", re.IGNORECASE)),
    ("official action claim", re.compile(r"\b(?:submitted|uploaded to the official record|certified|paid fee|scheduled inspection|official action completed)\b", re.IGNORECASE)),
    ("guarantee claim", re.compile(r"\b(?:legal advice|permit approval guaranteed|guaranteed approval|will be approved|will receive a permit)\b", re.IGNORECASE)),
)


@dataclass(frozen=True)
class InactiveGuardrailPromotionRehearsalV7Result:
    valid: bool
    problems: tuple[str, ...]


class InactiveGuardrailPromotionRehearsalV7Error(ValueError):
    def __init__(self, problems: Iterable[str]) -> None:
        self.problems = tuple(problems)
        super().__init__("invalid inactive guardrail promotion rehearsal v7: " + "; ".join(self.problems))


def load_json(path: str | Path) -> dict[str, Any]:
    loaded = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("inactive guardrail promotion rehearsal v7 fixture must be a JSON object")
    return loaded


def build_inactive_guardrail_promotion_rehearsal_v7_from_fixture(
    release_decision_fixture_path: str | Path = DEFAULT_RELEASE_DECISION_FIXTURE,
) -> dict[str, Any]:
    fixture_path = Path(release_decision_fixture_path)
    release_decision = load_json(fixture_path)
    return build_inactive_guardrail_promotion_rehearsal_v7(
        release_decision,
        release_decision_fixture_ref=fixture_path.as_posix(),
    )


def build_inactive_guardrail_promotion_rehearsal_v7(
    release_decision: Mapping[str, Any], *, release_decision_fixture_ref: str
) -> dict[str, Any]:
    assert_valid_post_recompile_release_decision_packet_v7(release_decision)
    if release_decision.get("packet_type") != RELEASE_DECISION_PACKET_TYPE:
        raise ValueError("inactive promotion rehearsal v7 consumes only post-recompile release decision packet v7 fixtures")
    if release_decision.get("packet_version") != RELEASE_DECISION_PACKET_VERSION:
        raise ValueError("post-recompile release decision packet fixture must be v7")

    checklist_rows = _checklist_rows(release_decision)
    packet = {
        "packet_type": PACKET_TYPE,
        "packet_version": PACKET_VERSION,
        "mode": MODE,
        "fixture_first": True,
        "inactive_guardrail_promotion_rehearsal_only": True,
        "post_recompile_release_decision_packet_v7_fixtures_only": True,
        "reviewer_controlled_checklist_required": True,
        "unresolved_hold_carry_forward_required": True,
        "pre_promotion_source_freshness_required": True,
        "agent_notification_placeholders_required": True,
        "rollback_checkpoint_references_required": True,
        "monitoring_watch_required": True,
        "manual_reviewer_signoff_required": True,
        "active_guardrail_mutation": False,
        "active_guardrail_bundle_mutation": False,
        "active_prompt_mutation": False,
        "active_process_model_mutation": False,
        "active_requirement_mutation": False,
        "active_source_mutation": False,
        "active_devhub_surface_mutation": False,
        "active_release_state_mutation": False,
        "active_mutation": False,
        "guardrails_changed": False,
        "guardrail_bundles_changed": False,
        "promotion_executed": False,
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
            {"fixture_role": "post_recompile_release_decision_packet_v7", "path": release_decision_fixture_ref}
        ],
        "consumes_only": {
            "post_recompile_release_decision_packet_v7_fixtures": True,
            "packet_type": RELEASE_DECISION_PACKET_TYPE,
            "packet_version": RELEASE_DECISION_PACKET_VERSION,
        },
        "source_release_recommendation": release_decision.get("overall_recommendation"),
        "reviewer_controlled_promotion_checklist_rows": checklist_rows,
        "unresolved_hold_carry_forward_conditions": _hold_rows(checklist_rows, release_decision),
        "pre_promotion_source_freshness_reminders": _freshness_rows(checklist_rows, release_decision),
        "agent_notification_placeholders": _agent_rows(checklist_rows, release_decision),
        "rollback_checkpoint_references": _rollback_rows(checklist_rows, release_decision),
        "monitoring_watch_rows": _monitoring_rows(checklist_rows, release_decision),
        "offline_validation_commands": copy.deepcopy(EXACT_OFFLINE_VALIDATION_COMMANDS),
        "validation_commands": copy.deepcopy(VALIDATION_COMMANDS),
    }
    assert_valid_inactive_guardrail_promotion_rehearsal_v7(packet)
    return packet


def load_inactive_guardrail_promotion_rehearsal_v7(path: str | Path) -> dict[str, Any]:
    loaded = load_json(path)
    assert_valid_inactive_guardrail_promotion_rehearsal_v7(loaded)
    return loaded


def assert_valid_inactive_guardrail_promotion_rehearsal_v7(packet: Mapping[str, Any]) -> None:
    result = validate_inactive_guardrail_promotion_rehearsal_v7(packet)
    if not result.valid:
        raise InactiveGuardrailPromotionRehearsalV7Error(result.problems)


def validate_inactive_guardrail_promotion_rehearsal_v7(packet: Mapping[str, Any]) -> InactiveGuardrailPromotionRehearsalV7Result:
    if not isinstance(packet, Mapping):
        return InactiveGuardrailPromotionRehearsalV7Result(False, ("packet must be an object",))

    problems: list[str] = []
    if packet.get("packet_type") != PACKET_TYPE:
        problems.append(f"packet_type must be {PACKET_TYPE}")
    if packet.get("packet_version") != PACKET_VERSION:
        problems.append("packet_version must be v7")
    if packet.get("mode") != MODE:
        problems.append(f"mode must be {MODE}")
    if packet.get("offline_validation_commands") != EXACT_OFFLINE_VALIDATION_COMMANDS:
        problems.append("offline_validation_commands must exactly match inactive promotion rehearsal v7 commands")
    if packet.get("validation_commands") != VALIDATION_COMMANDS:
        problems.append("validation_commands must contain only the PP&D daemon self-test command")

    consumes = packet.get("consumes_only")
    if not isinstance(consumes, Mapping) or consumes.get("post_recompile_release_decision_packet_v7_fixtures") is not True:
        problems.append("consumes_only must require post-recompile release decision packet v7 fixtures")
    if isinstance(consumes, Mapping) and consumes.get("packet_type") != RELEASE_DECISION_PACKET_TYPE:
        problems.append("consumes_only.packet_type must reference post-recompile release decision packet v7")
    if isinstance(consumes, Mapping) and consumes.get("packet_version") != RELEASE_DECISION_PACKET_VERSION:
        problems.append("consumes_only.packet_version must be v7")

    for key in _REQUIRED_TRUE_FLAGS:
        if packet.get(key) is not True:
            problems.append(f"{key} must be true")
    for key in _REQUIRED_FALSE_FLAGS:
        if packet.get(key) is not False:
            problems.append(f"{key} must be false")
    for key in _REQUIRED_LISTS:
        if not _non_empty_sequence(packet.get(key)):
            problems.append(f"{key} must be a non-empty list")

    _validate_source_fixture_refs(packet.get("source_fixture_refs"), problems)
    _validate_rows(packet, problems)
    _validate_forbidden_payload(packet, problems)
    return InactiveGuardrailPromotionRehearsalV7Result(not problems, tuple(dict.fromkeys(problems)))


def _checklist_rows(release_decision: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(_mapping_sequence(release_decision.get("go_no_go_rows")), start=1):
        source_row_id = _text(row.get("row_id")) or f"go-no-go-{index}"
        rows.append(
            {
                "checklist_row_id": f"promotion-check::{source_row_id}",
                "source_go_no_go_row_id": source_row_id,
                "scenario": _text(row.get("scenario")) or "manual_review",
                "source_recommendation": _text(row.get("recommendation")) or "NO_GO",
                "rehearsal_status": INACTIVE_STATUS,
                "reviewer_controlled": True,
                "manual_reviewer_decision_required": True,
                "promotion_allowed": False,
                "activation_allowed": False,
            }
        )
    return rows


def _hold_rows(checklist_rows: Sequence[Mapping[str, Any]], release_decision: Mapping[str, Any]) -> list[dict[str, Any]]:
    source_holds = _mapping_sequence(release_decision.get("unresolved_hold_inventory"))
    rows = []
    for checklist in checklist_rows:
        for hold in source_holds:
            rows.append(
                {
                    "carry_forward_id": f"hold-carry::{checklist['checklist_row_id']}::{hold.get('hold_id')}",
                    "checklist_row_id": checklist["checklist_row_id"],
                    "source_hold_id": _text(hold.get("hold_id")) or "hold::manual-review",
                    "carry_forward_status": "unresolved_pending_reviewer_disposition",
                    "promotion_blocked": True,
                    "activation_allowed": False,
                }
            )
    return rows or [
        {
            "carry_forward_id": "hold-carry::manual-review-placeholder",
            "checklist_row_id": checklist_rows[0]["checklist_row_id"],
            "source_hold_id": "hold::manual-review-placeholder",
            "carry_forward_status": "placeholder_pending_reviewer_disposition",
            "promotion_blocked": True,
            "activation_allowed": False,
        }
    ]


def _freshness_rows(checklist_rows: Sequence[Mapping[str, Any]], release_decision: Mapping[str, Any]) -> list[dict[str, Any]]:
    continuity_ids = [_text(row.get("citation_summary_id")) for row in _mapping_sequence(release_decision.get("citation_continuity_summaries"))]
    continuity_ids = [item for item in continuity_ids if item]
    return [
        {
            "freshness_reminder_id": f"freshness-reminder::{row['checklist_row_id']}",
            "checklist_row_id": row["checklist_row_id"],
            "source_citation_summary_ids": continuity_ids,
            "freshness_status": "pending_pre_promotion_public_source_review",
            "all_sources_confirmed_fresh": False,
            "activation_allowed": False,
        }
        for row in checklist_rows
    ]


def _agent_rows(checklist_rows: Sequence[Mapping[str, Any]], release_decision: Mapping[str, Any]) -> list[dict[str, Any]]:
    note_ids = [_text(row.get("compatibility_note_id")) for row in _mapping_sequence(release_decision.get("agent_compatibility_notes"))]
    note_ids = [item for item in note_ids if item]
    return [
        {
            "agent_notification_placeholder_id": f"agent-notice::{row['checklist_row_id']}",
            "checklist_row_id": row["checklist_row_id"],
            "source_compatibility_note_ids": note_ids,
            "notification_status": "placeholder_pending_reviewer_text",
            "active_agent_change_allowed": False,
            "activation_allowed": False,
        }
        for row in checklist_rows
    ]


def _rollback_rows(checklist_rows: Sequence[Mapping[str, Any]], release_decision: Mapping[str, Any]) -> list[dict[str, Any]]:
    rollback_ids = [_text(row.get("rollback_owner_placeholder_id")) for row in _mapping_sequence(release_decision.get("rollback_owner_placeholders"))]
    rollback_ids = [item for item in rollback_ids if item]
    return [
        {
            "rollback_checkpoint_reference_id": f"rollback-ref::{row['checklist_row_id']}",
            "checklist_row_id": row["checklist_row_id"],
            "source_rollback_placeholder_ids": rollback_ids,
            "checkpoint_status": "reference_only_not_executed",
            "active_state_changed": False,
            "activation_allowed": False,
        }
        for row in checklist_rows
    ]


def _monitoring_rows(checklist_rows: Sequence[Mapping[str, Any]], release_decision: Mapping[str, Any]) -> list[dict[str, Any]]:
    reminder_ids = [_text(row.get("monitoring_reminder_id")) for row in _mapping_sequence(release_decision.get("monitoring_handoff_reminders"))]
    reminder_ids = [item for item in reminder_ids if item]
    return [
        {
            "monitoring_watch_id": f"monitoring-watch::{row['checklist_row_id']}",
            "checklist_row_id": row["checklist_row_id"],
            "source_monitoring_reminder_ids": reminder_ids,
            "watch_status": "planned_offline_watch_only",
            "watch_inputs": [
                "unresolved_hold_carry_forward_conditions",
                "pre_promotion_source_freshness_reminders",
                "rollback_checkpoint_references",
            ],
            "activation_allowed": False,
        }
        for row in checklist_rows
    ]


def _validate_source_fixture_refs(value: Any, problems: list[str]) -> None:
    refs = _mapping_sequence(value)
    if not any(ref.get("fixture_role") == "post_recompile_release_decision_packet_v7" and _text(ref.get("path")) for ref in refs):
        problems.append("source_fixture_refs must include a post-recompile release decision packet v7 fixture path")


def _validate_rows(packet: Mapping[str, Any], problems: list[str]) -> None:
    checklist_ids = set()
    for index, row in enumerate(_mapping_sequence(packet.get("reviewer_controlled_promotion_checklist_rows"))):
        prefix = f"reviewer_controlled_promotion_checklist_rows[{index}]"
        checklist_id = _text(row.get("checklist_row_id"))
        if not checklist_id:
            problems.append(f"{prefix}.checklist_row_id is required")
        checklist_ids.add(checklist_id)
        if row.get("rehearsal_status") != INACTIVE_STATUS:
            problems.append(f"{prefix}.rehearsal_status must remain inactive_rehearsal_only")
        if row.get("reviewer_controlled") is not True:
            problems.append(f"{prefix}.reviewer_controlled must be true")
        if row.get("manual_reviewer_decision_required") is not True:
            problems.append(f"{prefix}.manual_reviewer_decision_required must be true")
        if row.get("promotion_allowed") is not False:
            problems.append(f"{prefix}.promotion_allowed must be false")
        if row.get("activation_allowed") is not False:
            problems.append(f"{prefix}.activation_allowed must be false")

    _validate_section(packet, "unresolved_hold_carry_forward_conditions", "carry_forward_id", checklist_ids, problems)
    _validate_section(packet, "pre_promotion_source_freshness_reminders", "freshness_reminder_id", checklist_ids, problems)
    _validate_section(packet, "agent_notification_placeholders", "agent_notification_placeholder_id", checklist_ids, problems)
    _validate_section(packet, "rollback_checkpoint_references", "rollback_checkpoint_reference_id", checklist_ids, problems)
    _validate_section(packet, "monitoring_watch_rows", "monitoring_watch_id", checklist_ids, problems)

    for index, row in enumerate(_mapping_sequence(packet.get("unresolved_hold_carry_forward_conditions"))):
        if row.get("promotion_blocked") is not True:
            problems.append(f"unresolved_hold_carry_forward_conditions[{index}].promotion_blocked must be true")
        if row.get("activation_allowed") is not False:
            problems.append(f"unresolved_hold_carry_forward_conditions[{index}].activation_allowed must be false")
    for index, row in enumerate(_mapping_sequence(packet.get("pre_promotion_source_freshness_reminders"))):
        if row.get("all_sources_confirmed_fresh") is not False:
            problems.append(f"pre_promotion_source_freshness_reminders[{index}].all_sources_confirmed_fresh must be false")
    for index, row in enumerate(_mapping_sequence(packet.get("agent_notification_placeholders"))):
        if row.get("active_agent_change_allowed") is not False:
            problems.append(f"agent_notification_placeholders[{index}].active_agent_change_allowed must be false")
    for index, row in enumerate(_mapping_sequence(packet.get("rollback_checkpoint_references"))):
        if row.get("checkpoint_status") != "reference_only_not_executed":
            problems.append(f"rollback_checkpoint_references[{index}].checkpoint_status must be reference_only_not_executed")
        if row.get("active_state_changed") is not False:
            problems.append(f"rollback_checkpoint_references[{index}].active_state_changed must be false")
    for index, row in enumerate(_mapping_sequence(packet.get("monitoring_watch_rows"))):
        if row.get("watch_status") != "planned_offline_watch_only":
            problems.append(f"monitoring_watch_rows[{index}].watch_status must be planned_offline_watch_only")


def _validate_section(packet: Mapping[str, Any], section: str, id_key: str, checklist_ids: set[str], problems: list[str]) -> None:
    value = packet.get(section)
    if _non_empty_sequence(value) and len(_mapping_sequence(value)) != len(value):
        problems.append(f"{section} must contain only object rows")
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"{section}[{index}]"
        if not _text(row.get(id_key)):
            problems.append(f"{prefix}.{id_key} is required")
        if _text(row.get("checklist_row_id")) not in checklist_ids:
            problems.append(f"{prefix}.checklist_row_id must reference reviewer_controlled_promotion_checklist_rows")


def _validate_forbidden_payload(packet: Mapping[str, Any], problems: list[str]) -> None:
    allowed_keys = {"source_fixture_refs", "source_go_no_go_row_id", "source_release_recommendation"}
    allowed_command_keys = {"validation_commands", "offline_validation_commands"}
    for path, key, value in _walk(packet):
        normalized_key = key.lower().replace("-", "_")
        if normalized_key in _REQUIRED_FALSE_FLAGS and value is not False:
            problems.append(f"{path} must be false")
        if "active_mutation" in normalized_key and _truthy(value):
            problems.append(f"{path} contains an active mutation flag")
        if normalized_key not in allowed_keys and normalized_key not in allowed_command_keys:
            if _PRIVATE_KEY_RE.search(normalized_key) and _truthy(value):
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
