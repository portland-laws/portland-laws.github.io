"""Fixture-first release decision packet v5.

This module consumes only inactive guardrail promotion candidate v5 fixtures and
assembles an offline reviewer decision packet. It does not activate guardrails,
open DevHub, read private documents, upload, submit, certify, pay, schedule, or
make legal or permitting guarantees.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
import copy
import json
from pathlib import Path
import re
from typing import Any

from ppd.agent_readiness.inactive_guardrail_bundle_promotion_candidate_v5 import (
    PACKET_TYPE as CANDIDATE_PACKET_TYPE,
    load_inactive_guardrail_bundle_promotion_candidate_v5,
    validate_inactive_guardrail_bundle_promotion_candidate_v5,
)

PACKET_TYPE = "ppd.release_decision_packet.v5"
PACKET_VERSION = "v5"
MODE = "fixture_first_release_decision_v5"
EXACT_OFFLINE_VALIDATION_COMMANDS = [
    ["python3", "-m", "py_compile", "ppd/agent_readiness/release_decision_packet_v5.py"],
    ["python3", "-m", "unittest", "ppd.tests.test_release_decision_packet_v5"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]
VALIDATION_COMMANDS = [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]]

_REQUIRED_LISTS = (
    "source_fixture_refs",
    "reviewer_go_no_go_recommendation",
    "unresolved_hold_inventory",
    "source_freshness_clearance_status",
    "agent_api_compatibility_caveats",
    "rollback_owner_placeholders",
    "post_decision_smoke_replay_plan",
    "agent_notification_notes",
    "offline_validation_commands",
    "validation_commands",
)

_REQUIRED_TRUE_FLAGS = (
    "fixture_first",
    "inactive_candidate_fixture_only",
    "manual_reviewer_decision_required",
    "unresolved_holds_review_required",
    "source_freshness_clearance_required",
    "agent_api_compatibility_review_required",
    "rollback_owner_assignment_required",
    "post_decision_smoke_replay_required",
    "agent_notification_notes_required",
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
    "reads_private_documents",
    "uploads",
    "submits",
    "certifies",
    "pays",
    "schedules",
    "legal_or_permitting_guarantee",
)

_PRIVATE_KEY_RE = re.compile(
    r"(^|_)(auth|browser|cookie|credential|devhub[_-]?session|download|downloaded|har|password|payment|private|raw|screenshot|session|storage[_-]?state|token|trace)(_|$)",
    re.IGNORECASE,
)
_FORBIDDEN_TEXT_RE = re.compile(
    r"(activated guardrail|active guardrail was mutated|certified|guarantee approval|guaranteed approval|legal advice|opened devhub|paid fee|private document|scheduled inspection|submitted|uploaded to the official record)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ReleaseDecisionPacketV5Result:
    valid: bool
    problems: tuple[str, ...]


class ReleaseDecisionPacketV5Error(ValueError):
    def __init__(self, problems: Iterable[str]) -> None:
        self.problems = tuple(problems)
        super().__init__("invalid release decision packet v5: " + "; ".join(self.problems))


def build_release_decision_packet_v5_from_candidate_fixture(candidate_fixture_path: str | Path) -> dict[str, Any]:
    candidate_path = Path(candidate_fixture_path)
    candidate = load_inactive_guardrail_bundle_promotion_candidate_v5(candidate_path)
    return build_release_decision_packet_v5(candidate, candidate_fixture_ref=candidate_path.as_posix())


def build_release_decision_packet_v5(candidate_packet: Mapping[str, Any], *, candidate_fixture_ref: str) -> dict[str, Any]:
    candidate_result = validate_inactive_guardrail_bundle_promotion_candidate_v5(candidate_packet)
    if not candidate_result.valid:
        raise ValueError("release decision packet v5 consumes only valid inactive guardrail promotion candidate v5 fixtures")

    candidate_rows = _mapping_sequence(candidate_packet.get("inactive_promotion_rows"))
    hold_rows = _mapping_sequence(candidate_packet.get("unresolved_hold_inventory"))
    freshness_rows = _mapping_sequence(candidate_packet.get("source_freshness_clearance_criteria"))
    rollback_rows = _mapping_sequence(candidate_packet.get("rollback_checkpoint_rows"))
    notification_rows = _mapping_sequence(candidate_packet.get("agent_notification_notes"))
    blocked_hold_count = sum(1 for row in hold_rows if row.get("promotion_blocked") is True)
    pending_freshness_count = sum(1 for row in freshness_rows if row.get("activation_allowed") is False)
    recommendation = "NO_GO" if blocked_hold_count or pending_freshness_count else "GO_WITH_CAVEATS"

    packet = {
        "packet_type": PACKET_TYPE,
        "packet_version": PACKET_VERSION,
        "mode": MODE,
        "fixture_first": True,
        "inactive_candidate_fixture_only": True,
        "manual_reviewer_decision_required": True,
        "unresolved_holds_review_required": True,
        "source_freshness_clearance_required": True,
        "agent_api_compatibility_review_required": True,
        "rollback_owner_assignment_required": True,
        "post_decision_smoke_replay_required": True,
        "agent_notification_notes_required": True,
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
        "reads_private_documents": False,
        "uploads": False,
        "submits": False,
        "certifies": False,
        "pays": False,
        "schedules": False,
        "legal_or_permitting_guarantee": False,
        "source_fixture_refs": [
            {"fixture_role": "inactive_guardrail_promotion_candidate_v5", "path": candidate_fixture_ref}
        ],
        "consumes_only": {
            "inactive_guardrail_promotion_candidate_v5_fixtures": True,
            "candidate_packet_type": CANDIDATE_PACKET_TYPE,
        },
        "reviewer_go_no_go_recommendation": [
            {
                "recommendation_id": "reviewer-release-decision-v5",
                "recommendation": recommendation,
                "activation_allowed": False,
                "manual_reviewer_final_decision_required": True,
                "candidate_count": len(candidate_rows),
                "unresolved_hold_count": blocked_hold_count,
                "pending_source_freshness_count": pending_freshness_count,
                "basis": "Inactive candidate fixture still carries holds, source freshness clearance requirements, and manual review placeholders.",
            }
        ],
        "unresolved_hold_inventory": [_hold_decision_row(row) for row in hold_rows],
        "source_freshness_clearance_status": [_freshness_status_row(row) for row in freshness_rows],
        "agent_api_compatibility_caveats": _agent_api_caveats(candidate_rows),
        "rollback_owner_placeholders": [_rollback_owner_row(row) for row in rollback_rows],
        "post_decision_smoke_replay_plan": _smoke_replay_plan(recommendation),
        "agent_notification_notes": [_notification_row(row) for row in notification_rows],
        "offline_validation_commands": copy.deepcopy(EXACT_OFFLINE_VALIDATION_COMMANDS),
        "validation_commands": copy.deepcopy(VALIDATION_COMMANDS),
    }
    assert_valid_release_decision_packet_v5(packet)
    return packet


def load_release_decision_packet_v5(path: str | Path) -> dict[str, Any]:
    loaded = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("release decision packet v5 fixture must be a JSON object")
    assert_valid_release_decision_packet_v5(loaded)
    return loaded


def assert_valid_release_decision_packet_v5(packet: Mapping[str, Any]) -> None:
    result = validate_release_decision_packet_v5(packet)
    if not result.valid:
        raise ReleaseDecisionPacketV5Error(result.problems)


def validate_release_decision_packet_v5(packet: Mapping[str, Any]) -> ReleaseDecisionPacketV5Result:
    if not isinstance(packet, Mapping):
        return ReleaseDecisionPacketV5Result(False, ("packet must be an object",))

    problems: list[str] = []
    if packet.get("packet_type") != PACKET_TYPE:
        problems.append(f"packet_type must be {PACKET_TYPE}")
    if packet.get("packet_version") != PACKET_VERSION:
        problems.append("packet_version must be v5")
    if packet.get("mode") != MODE:
        problems.append(f"mode must be {MODE}")
    if packet.get("offline_validation_commands") != EXACT_OFFLINE_VALIDATION_COMMANDS:
        problems.append("offline_validation_commands must exactly match the release decision v5 offline validation commands")
    if packet.get("validation_commands") != VALIDATION_COMMANDS:
        problems.append("validation_commands must contain only the PP&D daemon self-test command")

    for key in _REQUIRED_TRUE_FLAGS:
        if packet.get(key) is not True:
            problems.append(f"{key} must be true")
    for key in _REQUIRED_FALSE_FLAGS:
        if packet.get(key) is not False:
            problems.append(f"{key} must be false")
    for key in _REQUIRED_LISTS:
        if not _non_empty_sequence(packet.get(key)):
            problems.append(f"{key} must be a non-empty list")

    consumes = packet.get("consumes_only")
    if not isinstance(consumes, Mapping) or consumes.get("inactive_guardrail_promotion_candidate_v5_fixtures") is not True:
        problems.append("consumes_only must require inactive guardrail promotion candidate v5 fixtures")
    if isinstance(consumes, Mapping) and consumes.get("candidate_packet_type") != CANDIDATE_PACKET_TYPE:
        problems.append("consumes_only.candidate_packet_type must reference inactive guardrail promotion candidate v5")

    _validate_rows(packet, problems)
    _validate_forbidden_payload(packet, problems)
    return ReleaseDecisionPacketV5Result(not problems, tuple(dict.fromkeys(problems)))


def _validate_rows(packet: Mapping[str, Any], problems: list[str]) -> None:
    recommendations = _mapping_sequence(packet.get("reviewer_go_no_go_recommendation"))
    for index, row in enumerate(recommendations):
        prefix = f"reviewer_go_no_go_recommendation[{index}]"
        if row.get("recommendation") not in {"NO_GO", "GO_WITH_CAVEATS"}:
            problems.append(f"{prefix}.recommendation must be NO_GO or GO_WITH_CAVEATS")
        if row.get("activation_allowed") is not False:
            problems.append(f"{prefix}.activation_allowed must be false")
        if row.get("manual_reviewer_final_decision_required") is not True:
            problems.append(f"{prefix}.manual_reviewer_final_decision_required must be true")

    section_rules = (
        ("unresolved_hold_inventory", "hold_id", "promotion_blocked", True),
        ("source_freshness_clearance_status", "clearance_id", "activation_allowed", False),
        ("agent_api_compatibility_caveats", "caveat_id", "requires_manual_review", True),
        ("rollback_owner_placeholders", "rollback_owner_placeholder_id", "active_state_changed", False),
        ("post_decision_smoke_replay_plan", "smoke_replay_step_id", "activation_allowed", False),
        ("agent_notification_notes", "note_id", "notification_status", "draft_note_only"),
    )
    for section, id_key, status_key, expected in section_rules:
        for index, row in enumerate(_mapping_sequence(packet.get(section))):
            prefix = f"{section}[{index}]"
            if not _text(row.get(id_key)):
                problems.append(f"{prefix}.{id_key} is required")
            if row.get(status_key) != expected:
                problems.append(f"{prefix}.{status_key} must be {expected!r}")


def _hold_decision_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "hold_id": _text(row.get("hold_id")),
        "candidate_id": _text(row.get("candidate_id")),
        "hold_status": _text(row.get("hold_status")) or "unresolved_pending_manual_review",
        "promotion_blocked": True,
        "reviewer_disposition": "hold_until_resolved",
        "stale_evidence_block": bool(row.get("stale_evidence_block")),
        "conflicting_evidence_block": bool(row.get("conflicting_evidence_block")),
        "refused_actions_present": bool(row.get("refused_actions_present")),
    }


def _freshness_status_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "clearance_id": _text(row.get("clearance_id")),
        "candidate_id": _text(row.get("candidate_id")),
        "clearance_status": _text(row.get("clearance_status")) or "pending_public_source_freshness_review",
        "all_citations_have_fresh_source_review": False,
        "stale_or_conflicting_evidence_resolved": False,
        "activation_allowed": False,
    }


def _agent_api_caveats(candidate_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(candidate_rows):
        candidate_id = _text(row.get("candidate_id")) or f"candidate-{index + 1}"
        rows.append(
            {
                "caveat_id": f"agent-api-caveat::{candidate_id}",
                "candidate_id": candidate_id,
                "compatibility_status": "caveat_pending_agent_consumer_review",
                "requires_manual_review": True,
                "note": "Agent consumers must treat this decision packet as inactive fixture data and continue blocking activation paths.",
            }
        )
    return rows


def _rollback_owner_row(row: Mapping[str, Any]) -> dict[str, Any]:
    checkpoint_id = _text(row.get("checkpoint_id"))
    return {
        "rollback_owner_placeholder_id": f"owner::{checkpoint_id}",
        "checkpoint_id": checkpoint_id,
        "candidate_id": _text(row.get("candidate_id")),
        "owner": "",
        "owner_assignment_status": "pending_manual_assignment",
        "rollback_target": _text(row.get("rollback_target")) or "discard_inactive_candidate_only",
        "active_state_changed": False,
    }


def _smoke_replay_plan(recommendation: str) -> list[dict[str, Any]]:
    return [
        {
            "smoke_replay_step_id": "post-decision-smoke-v5::go-no-go-outcome",
            "expected_outcome": recommendation,
            "activation_allowed": False,
            "command": ["python3", "-m", "unittest", "ppd.tests.test_release_decision_packet_v5"],
        },
        {
            "smoke_replay_step_id": "post-decision-smoke-v5::daemon-self-test",
            "expected_outcome": "offline_validation_only",
            "activation_allowed": False,
            "command": ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
        },
    ]


def _notification_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "note_id": _text(row.get("note_id")),
        "candidate_id": _text(row.get("candidate_id")),
        "notification_status": "draft_note_only",
        "message": "Release decision packet v5 is fixture-only; reviewers must resolve holds and freshness caveats before any separate activation review.",
    }


def _validate_forbidden_payload(packet: Mapping[str, Any], problems: list[str]) -> None:
    allowed_keys = {"source_fixture_refs", "validation_commands", "offline_validation_commands", "command"}
    for path, key, value in _walk(packet):
        normalized_key = key.lower().replace("-", "_")
        if normalized_key in _REQUIRED_FALSE_FLAGS and value is not False:
            problems.append(f"{path} must be false")
        if normalized_key not in allowed_keys and _PRIVATE_KEY_RE.search(normalized_key) and _truthy(value):
            problems.append(f"{path} must not include private, session, auth, raw, browser, trace, payment, or downloaded artifacts")
        if isinstance(value, str) and _FORBIDDEN_TEXT_RE.search(value):
            problems.append(f"{path} must not claim guardrail activation, DevHub access, private document reads, official actions, or guarantees")


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
