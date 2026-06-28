"""Fixture-first inactive guardrail promotion rehearsal v6.

This packet consumes only post-gap release readiness packet v6 fixtures and describes
inactive promotion candidate rehearsal rows. It does not activate guardrails or
perform live DevHub, crawl, upload, submission, certification, payment, scheduling,
or legal/permitting outcome work.
"""

from __future__ import annotations

import copy
import json
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ppd.agent_readiness.post_gap_release_readiness_packet_v6 import (
    PACKET_TYPE as POST_GAP_PACKET_TYPE,
    PACKET_VERSION as POST_GAP_PACKET_VERSION,
    assert_valid_post_gap_release_readiness_packet_v6,
)

PACKET_TYPE = "ppd.inactive_guardrail_promotion_rehearsal.v6"
PACKET_VERSION = "v6"
MODE = "fixture_first_inactive_guardrail_promotion_rehearsal_v6"
INACTIVE_STATUS = "inactive_candidate_only"

EXACT_OFFLINE_VALIDATION_COMMANDS = [
    ["python3", "-m", "py_compile", "ppd/agent_readiness/inactive_guardrail_promotion_rehearsal_v6.py"],
    ["python3", "-m", "py_compile", "ppd/tests/test_inactive_guardrail_promotion_rehearsal_v6.py"],
    ["python3", "-m", "pytest", "ppd/tests/test_inactive_guardrail_promotion_rehearsal_v6.py"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]
VALIDATION_COMMANDS = [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]]

_REQUIRED_TRUE_FLAGS = (
    "fixture_first",
    "inactive_candidate_only",
    "post_gap_release_readiness_packet_v6_fixtures_only",
    "manual_reviewer_signoff_required",
    "source_freshness_clearance_required",
    "unresolved_hold_propagation_required",
    "rollback_checkpoints_required",
    "post_promotion_smoke_replay_required",
    "agent_api_compatibility_reminders_required",
    "monitoring_handoff_required",
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

_REQUIRED_LIST_FIELDS = (
    "source_fixture_refs",
    "inactive_promotion_candidate_rows",
    "reviewer_controlled_signoff_placeholders",
    "source_freshness_clearance_prerequisites",
    "unresolved_hold_propagation_rows",
    "rollback_checkpoint_rows",
    "post_promotion_smoke_replay_expectations",
    "agent_api_compatibility_reminders",
    "monitoring_handoff_rows",
    "offline_validation_commands",
    "validation_commands",
)

_FORBIDDEN_TEXT_RE = re.compile(
    r"(guardrails activated|release activated|live crawl|opened devhub|submitted permit|uploaded correction|certified acknowledgement|paid fee|scheduled inspection|approval guaranteed|permit guaranteed|legal advice|private document|session cookie|auth state|bearer token|password|credential)",
    re.IGNORECASE,
)
_PRIVATE_KEY_RE = re.compile(
    r"(^|_)(auth|browser|cookie|credential|devhub[_-]?session|download|downloaded|har|password|payment|private|raw|screenshot|session|storage[_-]?state|token|trace)(_|$)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class InactiveGuardrailPromotionRehearsalV6Result:
    valid: bool
    problems: tuple[str, ...]


class InactiveGuardrailPromotionRehearsalV6Error(ValueError):
    def __init__(self, problems: Iterable[str]) -> None:
        self.problems = tuple(problems)
        super().__init__("invalid inactive guardrail promotion rehearsal v6: " + "; ".join(self.problems))


def load_json(path: str | Path) -> dict[str, Any]:
    loaded = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("inactive guardrail promotion rehearsal v6 fixture must be a JSON object")
    return loaded


def build_inactive_guardrail_promotion_rehearsal_v6_from_fixture(post_gap_packet_path: str | Path) -> dict[str, Any]:
    fixture_path = Path(post_gap_packet_path)
    post_gap_packet = load_json(fixture_path)
    return build_inactive_guardrail_promotion_rehearsal_v6(post_gap_packet, post_gap_fixture_ref=fixture_path.as_posix())


def build_inactive_guardrail_promotion_rehearsal_v6(
    post_gap_packet: Mapping[str, Any], *, post_gap_fixture_ref: str
) -> dict[str, Any]:
    assert_valid_post_gap_release_readiness_packet_v6(post_gap_packet)
    if post_gap_packet.get("packet_type") != POST_GAP_PACKET_TYPE or post_gap_packet.get("packet_version") != POST_GAP_PACKET_VERSION:
        raise ValueError("inactive promotion rehearsal v6 consumes only post-gap release readiness packet v6 fixtures")

    readiness_rows = _mapping_sequence(post_gap_packet.get("reviewer_go_no_go_rows"))
    holds = _mapping_sequence(post_gap_packet.get("unresolved_hold_inventory"))
    citations = _mapping_sequence(post_gap_packet.get("citation_coverage_notes"))
    agent_notices = _mapping_sequence(post_gap_packet.get("agent_notification_rows"))
    journal_refs = _mapping_sequence(post_gap_packet.get("journal_dry_run_coverage_refs"))

    candidate_rows = _candidate_rows(readiness_rows, holds, citations)
    packet = {
        "packet_type": PACKET_TYPE,
        "packet_version": PACKET_VERSION,
        "mode": MODE,
        "fixture_first": True,
        "inactive_candidate_only": True,
        "post_gap_release_readiness_packet_v6_fixtures_only": True,
        "manual_reviewer_signoff_required": True,
        "source_freshness_clearance_required": True,
        "unresolved_hold_propagation_required": True,
        "rollback_checkpoints_required": True,
        "post_promotion_smoke_replay_required": True,
        "agent_api_compatibility_reminders_required": True,
        "monitoring_handoff_required": True,
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
            {"fixture_role": "post_gap_release_readiness_packet_v6", "path": post_gap_fixture_ref}
        ],
        "consumes_only": {
            "post_gap_release_readiness_packet_v6_fixtures": True,
            "packet_type": POST_GAP_PACKET_TYPE,
            "packet_version": POST_GAP_PACKET_VERSION,
        },
        "inactive_promotion_candidate_rows": candidate_rows,
        "reviewer_controlled_signoff_placeholders": _signoff_rows(candidate_rows),
        "source_freshness_clearance_prerequisites": _freshness_rows(candidate_rows, citations),
        "unresolved_hold_propagation_rows": _hold_rows(candidate_rows, holds),
        "rollback_checkpoint_rows": _rollback_rows(candidate_rows),
        "post_promotion_smoke_replay_expectations": _smoke_rows(candidate_rows, journal_refs),
        "agent_api_compatibility_reminders": _api_rows(candidate_rows, agent_notices),
        "monitoring_handoff_rows": _monitoring_rows(candidate_rows, post_gap_packet),
        "offline_validation_commands": copy.deepcopy(EXACT_OFFLINE_VALIDATION_COMMANDS),
        "validation_commands": copy.deepcopy(VALIDATION_COMMANDS),
    }
    assert_valid_inactive_guardrail_promotion_rehearsal_v6(packet)
    return packet


def load_inactive_guardrail_promotion_rehearsal_v6(path: str | Path) -> dict[str, Any]:
    loaded = load_json(path)
    assert_valid_inactive_guardrail_promotion_rehearsal_v6(loaded)
    return loaded


def assert_valid_inactive_guardrail_promotion_rehearsal_v6(packet: Mapping[str, Any]) -> None:
    result = validate_inactive_guardrail_promotion_rehearsal_v6(packet)
    if not result.valid:
        raise InactiveGuardrailPromotionRehearsalV6Error(result.problems)


def validate_inactive_guardrail_promotion_rehearsal_v6(packet: Mapping[str, Any]) -> InactiveGuardrailPromotionRehearsalV6Result:
    if not isinstance(packet, Mapping):
        return InactiveGuardrailPromotionRehearsalV6Result(False, ("packet must be an object",))

    problems: list[str] = []
    if packet.get("packet_type") != PACKET_TYPE:
        problems.append(f"packet_type must be {PACKET_TYPE}")
    if packet.get("packet_version") != PACKET_VERSION:
        problems.append("packet_version must be v6")
    if packet.get("mode") != MODE:
        problems.append(f"mode must be {MODE}")
    if packet.get("offline_validation_commands") != EXACT_OFFLINE_VALIDATION_COMMANDS:
        problems.append("offline_validation_commands must exactly match inactive promotion rehearsal v6 commands")
    if packet.get("validation_commands") != VALIDATION_COMMANDS:
        problems.append("validation_commands must contain only the PP&D daemon self-test command")

    consumes = packet.get("consumes_only")
    if not isinstance(consumes, Mapping) or consumes.get("post_gap_release_readiness_packet_v6_fixtures") is not True:
        problems.append("consumes_only must require post-gap release readiness packet v6 fixtures")
    if isinstance(consumes, Mapping) and consumes.get("packet_type") != POST_GAP_PACKET_TYPE:
        problems.append("consumes_only.packet_type must reference post-gap release readiness packet v6")
    if isinstance(consumes, Mapping) and consumes.get("packet_version") != POST_GAP_PACKET_VERSION:
        problems.append("consumes_only.packet_version must be v6")

    for key in _REQUIRED_TRUE_FLAGS:
        if packet.get(key) is not True:
            problems.append(f"{key} must be true")
    for key in _REQUIRED_FALSE_FLAGS:
        if packet.get(key) is not False:
            problems.append(f"{key} must be false")
    for key in _REQUIRED_LIST_FIELDS:
        if not _non_empty_sequence(packet.get(key)):
            problems.append(f"{key} must be a non-empty list")

    _validate_source_fixture_refs(packet.get("source_fixture_refs"), problems)
    _validate_candidate_rows(packet.get("inactive_promotion_candidate_rows"), problems)
    candidate_ids = {_text(row.get("candidate_id")) for row in _mapping_sequence(packet.get("inactive_promotion_candidate_rows"))}
    _validate_cross_section_rows(packet.get("reviewer_controlled_signoff_placeholders"), "reviewer_controlled_signoff_placeholders", "placeholder_id", candidate_ids, problems)
    _validate_cross_section_rows(packet.get("source_freshness_clearance_prerequisites"), "source_freshness_clearance_prerequisites", "prerequisite_id", candidate_ids, problems)
    _validate_cross_section_rows(packet.get("unresolved_hold_propagation_rows"), "unresolved_hold_propagation_rows", "propagation_id", candidate_ids, problems)
    _validate_cross_section_rows(packet.get("rollback_checkpoint_rows"), "rollback_checkpoint_rows", "checkpoint_id", candidate_ids, problems)
    _validate_cross_section_rows(packet.get("post_promotion_smoke_replay_expectations"), "post_promotion_smoke_replay_expectations", "expectation_id", candidate_ids, problems)
    _validate_cross_section_rows(packet.get("agent_api_compatibility_reminders"), "agent_api_compatibility_reminders", "reminder_id", candidate_ids, problems)
    _validate_cross_section_rows(packet.get("monitoring_handoff_rows"), "monitoring_handoff_rows", "handoff_id", candidate_ids, problems)
    _validate_specific_row_controls(packet, problems)
    _validate_forbidden_payload(packet, problems)
    return InactiveGuardrailPromotionRehearsalV6Result(not problems, tuple(dict.fromkeys(problems)))


def _candidate_rows(readiness_rows: Sequence[Mapping[str, Any]], holds: Sequence[Mapping[str, Any]], citations: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    unresolved_count = len(holds)
    citation_count = len(citations)
    for index, row in enumerate(readiness_rows, start=1):
        row_id = _text(row.get("row_id")) or f"post-gap-reviewer-row-{index}"
        candidate_id = f"inactive-promotion-v6::{row_id}"
        rows.append(
            {
                "candidate_id": candidate_id,
                "source_reviewer_row_id": row_id,
                "candidate_status": INACTIVE_STATUS,
                "activation_allowed": False,
                "promotion_allowed": False,
                "derived_from_post_gap_release_readiness_v6": True,
                "source_recommendation": row.get("recommendation"),
                "source_unresolved_hold_count": row.get("unresolved_hold_count", unresolved_count),
                "source_fixture_citation_count": citation_count,
                "manual_reviewer_final_decision_required": True,
            }
        )
    return rows


def _signoff_rows(candidate_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "placeholder_id": f"signoff::{row['candidate_id']}",
            "candidate_id": row["candidate_id"],
            "signoff_status": "pending_manual_review",
            "reviewer": "REVIEWER_TBD",
            "reviewed_at": "",
            "activation_allowed": False,
        }
        for row in candidate_rows
    ]


def _freshness_rows(candidate_rows: Sequence[Mapping[str, Any]], citations: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    citation_refs = [_text(row.get("url")) or _text(row.get("label")) for row in citations]
    citation_refs = [item for item in citation_refs if item]
    return [
        {
            "prerequisite_id": f"freshness::{row['candidate_id']}",
            "candidate_id": row["candidate_id"],
            "clearance_status": "pending_public_source_freshness_review",
            "fixture_citation_refs": citation_refs,
            "all_sources_confirmed_fresh": False,
            "activation_allowed": False,
        }
        for row in candidate_rows
    ]


def _hold_rows(candidate_rows: Sequence[Mapping[str, Any]], holds: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for candidate in candidate_rows:
        for hold in holds:
            rows.append(
                {
                    "propagation_id": f"hold::{candidate['candidate_id']}::{hold.get('hold_id')}",
                    "candidate_id": candidate["candidate_id"],
                    "source_hold_id": hold.get("hold_id"),
                    "hold_type": hold.get("hold_type"),
                    "hold_status": "propagated_unresolved",
                    "promotion_blocked": True,
                    "reviewer_disposition_required": True,
                }
            )
    return rows


def _rollback_rows(candidate_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "checkpoint_id": f"rollback::{row['candidate_id']}",
            "candidate_id": row["candidate_id"],
            "checkpoint_status": "planned_not_executed",
            "rollback_target": "discard_inactive_rehearsal_candidate_only",
            "active_state_changed": False,
        }
        for row in candidate_rows
    ]


def _smoke_rows(candidate_rows: Sequence[Mapping[str, Any]], journal_refs: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    expected_events = [_text(row.get("journal_event")) for row in journal_refs if _text(row.get("journal_event"))]
    return [
        {
            "expectation_id": f"smoke::{row['candidate_id']}",
            "candidate_id": row["candidate_id"],
            "smoke_status": "planned_not_run_for_inactive_candidate",
            "requires_separate_post_promotion_task": True,
            "expected_journal_events": expected_events,
            "activation_allowed": False,
        }
        for row in candidate_rows
    ]


def _api_rows(candidate_rows: Sequence[Mapping[str, Any]], agent_notices: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    reminder_count = sum(len(row.get("manual_handoff_reminders", [])) for row in agent_notices)
    return [
        {
            "reminder_id": f"agent-api::{row['candidate_id']}",
            "candidate_id": row["candidate_id"],
            "compatibility_status": "reminder_only_pending_reviewer_acceptance",
            "preserve_missing_information_contract": True,
            "preserve_refused_action_contract": True,
            "preserve_citation_payload_contract": True,
            "manual_handoff_reminder_count": reminder_count,
            "active_api_change_allowed": False,
        }
        for row in candidate_rows
    ]


def _monitoring_rows(candidate_rows: Sequence[Mapping[str, Any]], post_gap_packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "handoff_id": f"monitoring::{row['candidate_id']}",
            "candidate_id": row["candidate_id"],
            "handoff_status": "planned_not_started",
            "monitoring_inputs": [
                "source_freshness_clearance_prerequisites",
                "unresolved_hold_propagation_rows",
                "post_promotion_smoke_replay_expectations",
            ],
            "source_packet_mode": post_gap_packet.get("mode"),
            "activation_allowed": False,
        }
        for row in candidate_rows
    ]


def _validate_source_fixture_refs(value: Any, problems: list[str]) -> None:
    refs = _mapping_sequence(value)
    if not any(ref.get("fixture_role") == "post_gap_release_readiness_packet_v6" and _text(ref.get("path")) for ref in refs):
        problems.append("source_fixture_refs must include a post_gap_release_readiness_packet_v6 fixture path")


def _validate_candidate_rows(value: Any, problems: list[str]) -> None:
    seen: set[str] = set()
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"inactive_promotion_candidate_rows[{index}]"
        candidate_id = _text(row.get("candidate_id"))
        if not candidate_id:
            problems.append(f"{prefix}.candidate_id is required")
        if candidate_id in seen:
            problems.append(f"{prefix}.candidate_id must be unique")
        seen.add(candidate_id)
        if row.get("candidate_status") != INACTIVE_STATUS:
            problems.append(f"{prefix}.candidate_status must remain inactive_candidate_only")
        if row.get("activation_allowed") is not False:
            problems.append(f"{prefix}.activation_allowed must be false")
        if row.get("promotion_allowed") is not False:
            problems.append(f"{prefix}.promotion_allowed must be false")
        if row.get("derived_from_post_gap_release_readiness_v6") is not True:
            problems.append(f"{prefix}.derived_from_post_gap_release_readiness_v6 must be true")
        if row.get("manual_reviewer_final_decision_required") is not True:
            problems.append(f"{prefix}.manual_reviewer_final_decision_required must be true")


def _validate_cross_section_rows(value: Any, section: str, id_key: str, candidate_ids: set[str], problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"{section}[{index}]"
        if not _text(row.get(id_key)):
            problems.append(f"{prefix}.{id_key} is required")
        candidate_id = _text(row.get("candidate_id"))
        if candidate_id not in candidate_ids:
            problems.append(f"{prefix}.candidate_id must reference inactive_promotion_candidate_rows")


def _validate_specific_row_controls(packet: Mapping[str, Any], problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(packet.get("reviewer_controlled_signoff_placeholders"))):
        if row.get("signoff_status") != "pending_manual_review":
            problems.append(f"reviewer_controlled_signoff_placeholders[{index}].signoff_status must be pending_manual_review")
        if row.get("activation_allowed") is not False:
            problems.append(f"reviewer_controlled_signoff_placeholders[{index}].activation_allowed must be false")
    for index, row in enumerate(_mapping_sequence(packet.get("source_freshness_clearance_prerequisites"))):
        if row.get("clearance_status") != "pending_public_source_freshness_review":
            problems.append(f"source_freshness_clearance_prerequisites[{index}].clearance_status must be pending_public_source_freshness_review")
        if row.get("all_sources_confirmed_fresh") is not False:
            problems.append(f"source_freshness_clearance_prerequisites[{index}].all_sources_confirmed_fresh must be false")
        if row.get("activation_allowed") is not False:
            problems.append(f"source_freshness_clearance_prerequisites[{index}].activation_allowed must be false")
    for index, row in enumerate(_mapping_sequence(packet.get("unresolved_hold_propagation_rows"))):
        if row.get("hold_status") != "propagated_unresolved":
            problems.append(f"unresolved_hold_propagation_rows[{index}].hold_status must be propagated_unresolved")
        if row.get("promotion_blocked") is not True:
            problems.append(f"unresolved_hold_propagation_rows[{index}].promotion_blocked must be true")
    for index, row in enumerate(_mapping_sequence(packet.get("rollback_checkpoint_rows"))):
        if row.get("checkpoint_status") != "planned_not_executed":
            problems.append(f"rollback_checkpoint_rows[{index}].checkpoint_status must be planned_not_executed")
        if row.get("active_state_changed") is not False:
            problems.append(f"rollback_checkpoint_rows[{index}].active_state_changed must be false")
    for index, row in enumerate(_mapping_sequence(packet.get("post_promotion_smoke_replay_expectations"))):
        if row.get("requires_separate_post_promotion_task") is not True:
            problems.append(f"post_promotion_smoke_replay_expectations[{index}].requires_separate_post_promotion_task must be true")
        if row.get("activation_allowed") is not False:
            problems.append(f"post_promotion_smoke_replay_expectations[{index}].activation_allowed must be false")
    for index, row in enumerate(_mapping_sequence(packet.get("agent_api_compatibility_reminders"))):
        if row.get("active_api_change_allowed") is not False:
            problems.append(f"agent_api_compatibility_reminders[{index}].active_api_change_allowed must be false")
    for index, row in enumerate(_mapping_sequence(packet.get("monitoring_handoff_rows"))):
        if row.get("handoff_status") != "planned_not_started":
            problems.append(f"monitoring_handoff_rows[{index}].handoff_status must be planned_not_started")
        if row.get("activation_allowed") is not False:
            problems.append(f"monitoring_handoff_rows[{index}].activation_allowed must be false")


def _validate_forbidden_payload(packet: Mapping[str, Any], problems: list[str]) -> None:
    allowed_keys = {"source_fixture_refs", "source_reviewer_row_id", "source_packet_mode", "fixture_citation_refs"}
    for path, key, value in _walk(packet):
        normalized_key = key.lower().replace("-", "_")
        if normalized_key in _REQUIRED_FALSE_FLAGS and value is not False:
            problems.append(f"{path} must be false")
        if normalized_key not in allowed_keys and _PRIVATE_KEY_RE.search(normalized_key) and _truthy(value):
            problems.append(f"{path} must not include private, auth, browser, trace, raw, payment, or downloaded artifacts")
        if isinstance(value, str) and _FORBIDDEN_TEXT_RE.search(value):
            problems.append(f"{path} must not claim live activation, DevHub access, official actions, private documents, or guarantees")


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
