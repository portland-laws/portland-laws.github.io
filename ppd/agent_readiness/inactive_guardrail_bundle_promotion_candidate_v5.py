from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
import json
import re
from pathlib import Path
from typing import Any

from ppd.agent_readiness_replay_v5 import replay_agent_readiness_v5

PACKET_TYPE = "ppd.inactive_guardrail_promotion_candidate.v5"
PACKET_VERSION = "v5"
REPLAY_VERSION = "agent_readiness_replay_v5"
INACTIVE_STATUS = "inactive_candidate_only"
VALIDATION_COMMANDS = [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]]
OFFLINE_VALIDATION_COMMANDS = [
    ["python3", "-m", "py_compile", "ppd/agent_readiness/inactive_guardrail_bundle_promotion_candidate_v5.py"],
    ["python3", "-m", "unittest", "ppd.tests.test_inactive_guardrail_bundle_promotion_candidate_v5"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]

_REQUIRED_LISTS = (
    "replay_fixture_inputs",
    "inactive_promotion_rows",
    "activation_prerequisites",
    "unresolved_hold_inventory",
    "reviewer_signoff_placeholders",
    "source_freshness_clearance_criteria",
    "rollback_checkpoint_rows",
    "post_promotion_smoke_checks",
    "agent_notification_notes",
    "offline_validation_commands",
    "validation_commands",
)

_REQUIRED_TRUE_FLAGS = (
    "fixture_first",
    "inactive_candidate_only",
    "post_recompile_agent_readiness_replay_v5_fixtures_only",
    "manual_reviewer_signoff_required",
    "source_freshness_clearance_required",
    "rollback_checkpoints_required",
    "post_promotion_smoke_required",
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
    r"(activated guardrail|active guardrail was mutated|certified|guarantee approval|legal advice|paid fee|opened devhub|private document|submitted|uploaded to the official record)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class InactiveGuardrailBundlePromotionCandidateV5Result:
    valid: bool
    problems: tuple[str, ...]


class InactiveGuardrailBundlePromotionCandidateV5Error(ValueError):
    def __init__(self, problems: Iterable[str]) -> None:
        self.problems = tuple(problems)
        super().__init__("invalid inactive guardrail promotion candidate v5: " + "; ".join(self.problems))


def build_inactive_guardrail_bundle_promotion_candidate_v5_from_replay_fixtures(
    reviewer_packet_path: str | Path,
    synthetic_requests_path: str | Path,
) -> dict[str, Any]:
    reviewer_path = Path(reviewer_packet_path)
    requests_path = Path(synthetic_requests_path)
    replay = replay_agent_readiness_v5(reviewer_path, requests_path)
    if replay.get("version") != REPLAY_VERSION:
        raise ValueError("candidate v5 consumes only post-recompile agent readiness replay v5 fixtures")

    rows = []
    prerequisites = []
    holds = []
    signoffs = []
    freshness = []
    rollback = []
    smoke = []
    notes = []

    for response in replay["responses"]:
        candidate_id = f"inactive-promotion-v5::{response['id']}"
        row_id = f"row::{response['id']}"
        rows.append(
            {
                "candidate_id": candidate_id,
                "row_id": row_id,
                "source_replay_response_id": response["id"],
                "candidate_status": INACTIVE_STATUS,
                "activation_allowed": False,
                "derived_from_replay_v5": True,
                "missing_information_prompt_count": len(response["missing_information_prompts"]),
                "refused_action_count": len(response["refused_actions"]),
                "citation_count": len(response["citation_payloads"]),
            }
        )
        prerequisites.append(
            {
                "prerequisite_id": f"prereq::{response['id']}",
                "candidate_id": candidate_id,
                "requires_replay_v5_response": True,
                "requires_manual_reviewer_signoff": True,
                "requires_unresolved_hold_clearance": True,
                "requires_source_freshness_clearance": True,
                "requires_rollback_checkpoint": True,
                "requires_post_promotion_smoke_plan": True,
                "activation_allowed": False,
            }
        )
        holds.append(
            {
                "hold_id": f"hold::{response['id']}",
                "candidate_id": candidate_id,
                "hold_status": "unresolved_pending_manual_review",
                "promotion_blocked": True,
                "stale_evidence_block": response["stale_evidence_block"],
                "conflicting_evidence_block": response["conflicting_evidence_block"],
                "refused_actions_present": bool(response["refused_actions"]),
            }
        )
        signoffs.append(
            {
                "placeholder_id": f"signoff::{response['id']}",
                "candidate_id": candidate_id,
                "signoff_status": "pending_manual_review",
                "reviewer": "",
                "signed_at": "",
            }
        )
        freshness.append(
            {
                "clearance_id": f"freshness::{response['id']}",
                "candidate_id": candidate_id,
                "clearance_status": "pending_public_source_freshness_review",
                "all_citations_have_fresh_source_review": False,
                "stale_or_conflicting_evidence_resolved": False,
                "activation_allowed": False,
            }
        )
        rollback.append(
            {
                "checkpoint_id": f"rollback::{response['id']}",
                "candidate_id": candidate_id,
                "checkpoint_status": "planned_not_executed",
                "rollback_target": "discard_inactive_candidate_only",
                "active_state_changed": False,
            }
        )
        smoke.append(
            {
                "smoke_check_id": f"smoke::{response['id']}",
                "candidate_id": candidate_id,
                "smoke_status": "planned_not_run_for_inactive_candidate",
                "requires_separate_post_promotion_task": True,
                "checks_agent_readiness_replay": True,
            }
        )
        notes.append(
            {
                "note_id": f"notify::{response['id']}",
                "candidate_id": candidate_id,
                "notification_status": "draft_note_only",
                "message": "Inactive candidate assembled from replay v5 fixtures; keep guardrails inactive until manual review, freshness clearance, rollback checkpoint review, and post-promotion smoke planning are complete.",
            }
        )

    packet = {
        "packet_type": PACKET_TYPE,
        "packet_version": PACKET_VERSION,
        "fixture_first": True,
        "inactive_candidate_only": True,
        "post_recompile_agent_readiness_replay_v5_fixtures_only": True,
        "manual_reviewer_signoff_required": True,
        "source_freshness_clearance_required": True,
        "rollback_checkpoints_required": True,
        "post_promotion_smoke_required": True,
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
        "replay_fixture_inputs": [
            {"fixture_role": "reviewer_packet_v5", "path": reviewer_path.as_posix()},
            {"fixture_role": "synthetic_agent_requests_v5", "path": requests_path.as_posix()},
        ],
        "replay_source_versions": list(replay["source_versions"]),
        "inactive_promotion_rows": rows,
        "activation_prerequisites": prerequisites,
        "unresolved_hold_inventory": holds,
        "reviewer_signoff_placeholders": signoffs,
        "source_freshness_clearance_criteria": freshness,
        "rollback_checkpoint_rows": rollback,
        "post_promotion_smoke_checks": smoke,
        "agent_notification_notes": notes,
        "offline_validation_commands": OFFLINE_VALIDATION_COMMANDS,
        "validation_commands": VALIDATION_COMMANDS,
    }
    assert_valid_inactive_guardrail_bundle_promotion_candidate_v5(packet)
    return packet


def load_inactive_guardrail_bundle_promotion_candidate_v5(path: str | Path) -> dict[str, Any]:
    loaded = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("inactive guardrail promotion candidate v5 fixture must be a JSON object")
    assert_valid_inactive_guardrail_bundle_promotion_candidate_v5(loaded)
    return loaded


def assert_valid_inactive_guardrail_bundle_promotion_candidate_v5(packet: Mapping[str, Any]) -> None:
    result = validate_inactive_guardrail_bundle_promotion_candidate_v5(packet)
    if not result.valid:
        raise InactiveGuardrailBundlePromotionCandidateV5Error(result.problems)


def validate_inactive_guardrail_bundle_promotion_candidate_v5(packet: Mapping[str, Any]) -> InactiveGuardrailBundlePromotionCandidateV5Result:
    if not isinstance(packet, Mapping):
        return InactiveGuardrailBundlePromotionCandidateV5Result(False, ("packet must be an object",))

    problems: list[str] = []
    if packet.get("packet_type") != PACKET_TYPE:
        problems.append(f"packet_type must be {PACKET_TYPE}")
    if packet.get("packet_version") != PACKET_VERSION:
        problems.append("packet_version must be v5")
    if packet.get("offline_validation_commands") != OFFLINE_VALIDATION_COMMANDS:
        problems.append("offline_validation_commands must exactly match the v5 offline validation command bundle")
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

    _validate_rows(packet, problems)
    _validate_forbidden_payload(packet, problems)
    return InactiveGuardrailBundlePromotionCandidateV5Result(not problems, tuple(problems))


def _validate_rows(packet: Mapping[str, Any], problems: list[str]) -> None:
    candidate_ids = {_text(row.get("candidate_id")) for row in _mapping_sequence(packet.get("inactive_promotion_rows"))}
    for index, row in enumerate(_mapping_sequence(packet.get("inactive_promotion_rows"))):
        prefix = f"inactive_promotion_rows[{index}]"
        if not _text(row.get("candidate_id")):
            problems.append(f"{prefix}.candidate_id is required")
        if row.get("candidate_status") != INACTIVE_STATUS:
            problems.append(f"{prefix}.candidate_status must remain inactive_candidate_only")
        if row.get("activation_allowed") is not False:
            problems.append(f"{prefix}.activation_allowed must be false")
        if row.get("derived_from_replay_v5") is not True:
            problems.append(f"{prefix}.derived_from_replay_v5 must be true")

    section_rules = (
        ("activation_prerequisites", "prerequisite_id", "activation_allowed", False),
        ("unresolved_hold_inventory", "hold_id", "promotion_blocked", True),
        ("reviewer_signoff_placeholders", "placeholder_id", "signoff_status", "pending_manual_review"),
        ("source_freshness_clearance_criteria", "clearance_id", "activation_allowed", False),
        ("rollback_checkpoint_rows", "checkpoint_id", "active_state_changed", False),
        ("post_promotion_smoke_checks", "smoke_check_id", "requires_separate_post_promotion_task", True),
        ("agent_notification_notes", "note_id", "notification_status", "draft_note_only"),
    )
    for section, id_key, status_key, expected in section_rules:
        for index, row in enumerate(_mapping_sequence(packet.get(section))):
            prefix = f"{section}[{index}]"
            if not _text(row.get(id_key)):
                problems.append(f"{prefix}.{id_key} is required")
            candidate_id = _text(row.get("candidate_id"))
            if not candidate_id or candidate_id not in candidate_ids:
                problems.append(f"{prefix}.candidate_id must reference inactive_promotion_rows")
            if row.get(status_key) != expected:
                problems.append(f"{prefix}.{status_key} must be {expected!r}")


def _validate_forbidden_payload(packet: Mapping[str, Any], problems: list[str]) -> None:
    allowed_replay_keys = {"replay_fixture_inputs", "source_replay_response_id", "replay_source_versions"}
    for path, key, value in _walk(packet):
        normalized_key = key.lower().replace("-", "_")
        if normalized_key in _REQUIRED_FALSE_FLAGS and value is not False:
            problems.append(f"{path} must be false")
        if normalized_key not in allowed_replay_keys and _PRIVATE_KEY_RE.search(normalized_key) and _truthy(value):
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
