"""Fixture-first post-recompile release decision packet v6.

This module consumes only post-recompile agent readiness replay v6 fixture
payloads. It assembles offline reviewer rows and placeholders without activating
guardrails, opening DevHub, crawling live sites, reading private documents,
uploading, submitting, certifying, paying, scheduling, or making legal or
permitting guarantees.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
import copy
import json
from pathlib import Path
import re
from typing import Any

PACKET_TYPE = "ppd.post_recompile_release_decision_packet.v6"
PACKET_VERSION = "v6"
MODE = "fixture_first_post_recompile_release_decision_v6"
REPLAY_ID = "post_recompile_agent_readiness_replay_v6"
FIXTURE_DIR = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "post_recompile_release_decision_packet_v6"
DEFAULT_REPLAY_FIXTURE = FIXTURE_DIR / "post_recompile_agent_readiness_replay_v6_fixture.json"
EXACT_OFFLINE_VALIDATION_COMMANDS = [
    ["python3", "-m", "py_compile", "ppd/agent_readiness/post_recompile_release_decision_packet_v6.py"],
    ["python3", "-m", "unittest", "ppd.tests.test_post_recompile_release_decision_packet_v6"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]
VALIDATION_COMMANDS = [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]]

_REQUIRED_TRUE_FLAGS = (
    "fixture_first",
    "post_recompile_replay_fixture_only",
    "manual_reviewer_decision_required",
    "unresolved_holds_review_required",
    "citation_continuity_review_required",
    "agent_compatibility_review_required",
    "inactive_guardrail_promotion_eligibility_review_required",
    "rollback_owner_assignment_required",
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

_REQUIRED_LISTS = (
    "source_fixture_refs",
    "go_no_go_rows",
    "unresolved_hold_inventory",
    "citation_continuity_summaries",
    "agent_compatibility_notes",
    "inactive_guardrail_promotion_eligibility_placeholders",
    "rollback_owner_placeholders",
    "monitoring_handoff_reminders",
    "offline_validation_commands",
    "validation_commands",
)

_PRIVATE_KEY_RE = re.compile(
    r"(^|_)(auth|browser|cookie|credential|devhub[_-]?session|download|downloaded|har|password|payment|private|raw|screenshot|session|storage[_-]?state|token|trace)(_|$)",
    re.IGNORECASE,
)
_FORBIDDEN_TEXT_RULES = (
    ("active activation claim", re.compile(r"\b(?:activated|activation completed|release is active|promoted to active|active guardrail(?:s)? deployed)\b", re.IGNORECASE)),
    ("live crawl execution claim", re.compile(r"\b(?:live crawl completed|ran live crawl|executed live crawl|crawled live sites|opened devhub|logged in|authenticated devhub|live browser)\b", re.IGNORECASE)),
    ("private/session/auth artifact claim", re.compile(r"\b(?:cookie|credential|password|private document|session token|storage state|trace file|har file|screenshot artifact|raw crawl output|downloaded document)\b", re.IGNORECASE)),
    ("official-action completion claim", re.compile(r"\b(?:submitted|uploaded to the official record|certified|paid fee|scheduled inspection|cancelled permit|withdrew application|official action completed)\b", re.IGNORECASE)),
    ("legal or permitting guarantee", re.compile(r"\b(?:legal advice|legally sufficient|permit approval guaranteed|guaranteed approval|will be approved|will receive a permit)\b", re.IGNORECASE)),
    ("active mutation claim", re.compile(r"\b(?:active mutation|mutated active|changed active|production mutation|active state changed)\b", re.IGNORECASE)),
)


@dataclass(frozen=True)
class PostRecompileReleaseDecisionPacketV6Result:
    valid: bool
    problems: tuple[str, ...]


class PostRecompileReleaseDecisionPacketV6Error(ValueError):
    def __init__(self, problems: Iterable[str]) -> None:
        self.problems = tuple(problems)
        super().__init__("invalid post-recompile release decision packet v6: " + "; ".join(self.problems))


def load_post_recompile_agent_readiness_replay_v6_fixture(path: str | Path = DEFAULT_REPLAY_FIXTURE) -> dict[str, Any]:
    loaded = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("post-recompile agent readiness replay v6 fixture must be a JSON object")
    _assert_replay_fixture(loaded)
    return loaded


def build_post_recompile_release_decision_packet_v6_from_fixture(
    replay_fixture_path: str | Path = DEFAULT_REPLAY_FIXTURE,
) -> dict[str, Any]:
    replay_path = Path(replay_fixture_path)
    replay = load_post_recompile_agent_readiness_replay_v6_fixture(replay_path)
    return build_post_recompile_release_decision_packet_v6(replay, replay_fixture_ref=replay_path.as_posix())


def build_post_recompile_release_decision_packet_v6(
    replay: Mapping[str, Any], *, replay_fixture_ref: str
) -> dict[str, Any]:
    _assert_replay_fixture(replay)
    cases = _mapping_sequence(replay.get("cases"))
    hold_rows = [_hold_row(case) for case in cases if _case_requires_hold(case)]
    go_no_go_rows = [_go_no_go_row(case) for case in cases]
    recommendation = "NO_GO" if hold_rows else "GO_WITH_CAVEATS"

    packet = {
        "packet_type": PACKET_TYPE,
        "packet_version": PACKET_VERSION,
        "mode": MODE,
        "fixture_first": True,
        "post_recompile_replay_fixture_only": True,
        "manual_reviewer_decision_required": True,
        "unresolved_holds_review_required": True,
        "citation_continuity_review_required": True,
        "agent_compatibility_review_required": True,
        "inactive_guardrail_promotion_eligibility_review_required": True,
        "rollback_owner_assignment_required": True,
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
            {
                "fixture_role": "post_recompile_agent_readiness_replay_v6",
                "path": replay_fixture_ref,
                "replay": REPLAY_ID,
            }
        ],
        "consumes_only": {
            "post_recompile_agent_readiness_replay_v6_fixtures": True,
            "replay": REPLAY_ID,
        },
        "overall_recommendation": recommendation,
        "go_no_go_rows": go_no_go_rows,
        "unresolved_hold_inventory": hold_rows or [_no_open_hold_placeholder()],
        "citation_continuity_summaries": _citation_continuity_rows(cases),
        "agent_compatibility_notes": _agent_compatibility_rows(cases),
        "inactive_guardrail_promotion_eligibility_placeholders": _inactive_promotion_placeholders(recommendation),
        "rollback_owner_placeholders": _rollback_owner_placeholders(),
        "monitoring_handoff_reminders": _monitoring_handoff_reminders(),
        "offline_validation_commands": copy.deepcopy(EXACT_OFFLINE_VALIDATION_COMMANDS),
        "validation_commands": copy.deepcopy(VALIDATION_COMMANDS),
    }
    assert_valid_post_recompile_release_decision_packet_v6(packet)
    return packet


def load_post_recompile_release_decision_packet_v6(path: str | Path) -> dict[str, Any]:
    loaded = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("post-recompile release decision packet v6 fixture must be a JSON object")
    assert_valid_post_recompile_release_decision_packet_v6(loaded)
    return loaded


def assert_valid_post_recompile_release_decision_packet_v6(packet: Mapping[str, Any]) -> None:
    result = validate_post_recompile_release_decision_packet_v6(packet)
    if not result.valid:
        raise PostRecompileReleaseDecisionPacketV6Error(result.problems)


def validate_post_recompile_release_decision_packet_v6(
    packet: Mapping[str, Any],
) -> PostRecompileReleaseDecisionPacketV6Result:
    if not isinstance(packet, Mapping):
        return PostRecompileReleaseDecisionPacketV6Result(False, ("packet must be an object",))

    problems: list[str] = []
    if packet.get("packet_type") != PACKET_TYPE:
        problems.append(f"packet_type must be {PACKET_TYPE}")
    if packet.get("packet_version") != PACKET_VERSION:
        problems.append("packet_version must be v6")
    if packet.get("mode") != MODE:
        problems.append(f"mode must be {MODE}")
    if packet.get("offline_validation_commands") != EXACT_OFFLINE_VALIDATION_COMMANDS:
        problems.append("offline_validation_commands must exactly match the post-recompile release decision v6 commands")
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

    _validate_replay_references(packet, problems)
    _validate_rows(packet, problems)
    _validate_forbidden_payload(packet, problems)
    return PostRecompileReleaseDecisionPacketV6Result(not problems, tuple(dict.fromkeys(problems)))


def _assert_replay_fixture(replay: Mapping[str, Any]) -> None:
    if replay.get("replay") != REPLAY_ID:
        raise ValueError(f"release decision packet v6 consumes only {REPLAY_ID} fixtures")
    if replay.get("mode") != "fixture_first_offline_only":
        raise ValueError("post-recompile replay fixture must be fixture-first offline-only")
    if replay.get("guardrails_active") is not False:
        raise ValueError("post-recompile replay fixture must keep guardrails inactive")
    if replay.get("opened_devhub") is not False or replay.get("live_sites_crawled") is not False:
        raise ValueError("post-recompile replay fixture must not open DevHub or crawl live sites")
    if replay.get("private_documents_read") is not False:
        raise ValueError("post-recompile replay fixture must not read private documents")
    if not _non_empty_sequence(replay.get("cases")):
        raise ValueError("post-recompile replay fixture must include cases")


def _validate_replay_references(packet: Mapping[str, Any], problems: list[str]) -> None:
    refs = _mapping_sequence(packet.get("source_fixture_refs"))
    if len(refs) != len(packet.get("source_fixture_refs", [])) if isinstance(packet.get("source_fixture_refs"), Sequence) and not isinstance(packet.get("source_fixture_refs"), (str, bytes, bytearray)) else False:
        problems.append("source_fixture_refs must contain only object rows")
    if not any(ref.get("fixture_role") == "post_recompile_agent_readiness_replay_v6" and ref.get("replay") == REPLAY_ID and _text(ref.get("path")) for ref in refs):
        problems.append("source_fixture_refs must include a post-recompile agent readiness replay v6 reference")

    consumes = packet.get("consumes_only")
    if not isinstance(consumes, Mapping) or consumes.get("post_recompile_agent_readiness_replay_v6_fixtures") is not True:
        problems.append("consumes_only must require post-recompile agent readiness replay v6 fixtures")
    if isinstance(consumes, Mapping) and consumes.get("replay") != REPLAY_ID:
        problems.append(f"consumes_only.replay must be {REPLAY_ID}")


def _validate_rows(packet: Mapping[str, Any], problems: list[str]) -> None:
    _require_mapping_rows(packet, "go_no_go_rows", problems)
    for index, row in enumerate(_mapping_sequence(packet.get("go_no_go_rows"))):
        prefix = f"go_no_go_rows[{index}]"
        for key in ("row_id", "scenario", "source_fixture", "response_type", "evidence_status", "basis"):
            if not _text(row.get(key)):
                problems.append(f"{prefix}.{key} is required")
        if row.get("recommendation") not in {"NO_GO", "GO_WITH_CAVEATS"}:
            problems.append(f"{prefix}.recommendation must be NO_GO or GO_WITH_CAVEATS")
        if row.get("activation_allowed") is not False:
            problems.append(f"{prefix}.activation_allowed must be false")
        if row.get("manual_reviewer_decision_required") is not True:
            problems.append(f"{prefix}.manual_reviewer_decision_required must be true")

    section_rules = (
        ("unresolved_hold_inventory", "hold_id", "promotion_blocked", True),
        ("citation_continuity_summaries", "citation_summary_id", "requires_manual_review", True),
        ("agent_compatibility_notes", "compatibility_note_id", "requires_manual_review", True),
        ("inactive_guardrail_promotion_eligibility_placeholders", "eligibility_placeholder_id", "activation_allowed", False),
        ("rollback_owner_placeholders", "rollback_owner_placeholder_id", "active_state_changed", False),
        ("monitoring_handoff_reminders", "monitoring_reminder_id", "handoff_required", True),
    )
    for section, id_key, status_key, expected in section_rules:
        _require_mapping_rows(packet, section, problems)
        for index, row in enumerate(_mapping_sequence(packet.get(section))):
            prefix = f"{section}[{index}]"
            if not _text(row.get(id_key)):
                problems.append(f"{prefix}.{id_key} is required")
            if row.get(status_key) != expected:
                problems.append(f"{prefix}.{status_key} must be {expected!r}")


def _require_mapping_rows(packet: Mapping[str, Any], section: str, problems: list[str]) -> None:
    value = packet.get(section)
    if not _non_empty_sequence(value):
        return
    if len(_mapping_sequence(value)) != len(value):
        problems.append(f"{section} must contain only object rows")


def _go_no_go_row(case: Mapping[str, Any]) -> dict[str, Any]:
    scenario = _text(case.get("scenario")) or "unknown_scenario"
    requires_hold = _case_requires_hold(case)
    return {
        "row_id": f"go-no-go::{scenario}",
        "scenario": scenario,
        "source_fixture": _text(case.get("source_fixture")),
        "response_type": _text(case.get("response_type")),
        "evidence_status": _text(case.get("evidence_status")),
        "recommendation": "NO_GO" if requires_hold else "GO_WITH_CAVEATS",
        "activation_allowed": False,
        "manual_reviewer_decision_required": True,
        "basis": _decision_basis(requires_hold),
    }


def _hold_row(case: Mapping[str, Any]) -> dict[str, Any]:
    scenario = _text(case.get("scenario")) or "unknown_scenario"
    evidence_status = _text(case.get("evidence_status")) or "review_required"
    return {
        "hold_id": f"hold::{scenario}",
        "scenario": scenario,
        "hold_status": "unresolved_pending_manual_review",
        "promotion_blocked": True,
        "reviewer_disposition": "hold_until_replay_case_is_resolved_or_accepted",
        "evidence_status": evidence_status,
        "response_type": _text(case.get("response_type")),
        "source_fixture": _text(case.get("source_fixture")),
    }


def _no_open_hold_placeholder() -> dict[str, Any]:
    return {
        "hold_id": "hold::manual-review-placeholder",
        "scenario": "manual_reviewer_final_decision",
        "hold_status": "placeholder_pending_manual_release_review",
        "promotion_blocked": True,
        "reviewer_disposition": "confirm_no_unresolved_holds_before_separate_activation_review",
        "evidence_status": "manual_review_required",
        "response_type": "placeholder",
        "source_fixture": REPLAY_ID,
    }


def _citation_continuity_rows(cases: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    statuses = sorted({_text(case.get("evidence_status")) or "unspecified" for case in cases})
    return [
        {
            "citation_summary_id": "citation-continuity::post-recompile-replay-v6",
            "source_replay": REPLAY_ID,
            "case_count": len(cases),
            "evidence_statuses": statuses,
            "continuity_status": "fixture_replay_continuity_only_pending_public_source_review",
            "requires_manual_review": True,
            "note": "This packet summarizes replay fixture evidence status only and does not recrawl, refresh, or certify public citations.",
        }
    ]


def _agent_compatibility_rows(cases: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    response_types = sorted({_text(case.get("response_type")) or "unspecified" for case in cases})
    return [
        {
            "compatibility_note_id": "agent-compatibility::post-recompile-replay-v6",
            "source_replay": REPLAY_ID,
            "response_types_seen": response_types,
            "requires_manual_review": True,
            "activation_allowed": False,
            "note": "Agent consumers must continue treating these rows as inactive offline fixture outputs until a separate reviewed promotion packet exists.",
        }
    ]


def _inactive_promotion_placeholders(recommendation: str) -> list[dict[str, Any]]:
    return [
        {
            "eligibility_placeholder_id": "inactive-promotion-eligibility::reviewer-disposition",
            "recommendation": recommendation,
            "eligibility_status": "placeholder_pending_manual_reviewer_disposition",
            "activation_allowed": False,
            "promotion_executed": False,
            "required_next_review": "Resolve holds, citation continuity, agent compatibility, rollback owners, and monitoring handoff before any separate promotion review.",
        }
    ]


def _rollback_owner_placeholders() -> list[dict[str, Any]]:
    return [
        {
            "rollback_owner_placeholder_id": "rollback-owner::post-recompile-release-v6",
            "owner": "",
            "owner_assignment_status": "pending_manual_assignment",
            "rollback_target": "discard_fixture_first_release_decision_packet_only",
            "active_state_changed": False,
            "note": "No active guardrail, prompt, source, requirement, process model, DevHub surface, or release state is changed by this packet.",
        }
    ]


def _monitoring_handoff_reminders() -> list[dict[str, Any]]:
    return [
        {
            "monitoring_reminder_id": "monitoring-handoff::post-recompile-release-v6",
            "handoff_required": True,
            "handoff_status": "draft_reminder_only",
            "activation_allowed": False,
            "reminder": "Prepare offline monitoring notes for reviewer follow-up; do not use DevHub, public crawlers, official actions, payments, or outcome promises.",
        }
    ]


def _case_requires_hold(case: Mapping[str, Any]) -> bool:
    scenario = _text(case.get("scenario"))
    response_type = _text(case.get("response_type"))
    evidence_status = _text(case.get("evidence_status")).lower()
    return (
        response_type == "refusal"
        or scenario in {"stale_evidence", "exact_confirmation_checkpoint", "rollback_visibility", "manual_handoff"}
        or "stale" in evidence_status
        or "conflict" in evidence_status
        or "review" in evidence_status
    )


def _decision_basis(requires_hold: bool) -> str:
    if requires_hold:
        return "Replay case requires manual reviewer disposition before any separate promotion review."
    return "Replay case is compatible with fixture-only release review, with activation still disallowed."


def _validate_forbidden_payload(packet: Mapping[str, Any], problems: list[str]) -> None:
    allowed_private_key_paths = {"packet.source_fixture_refs[0].path"}
    allowed_command_keys = {"validation_commands", "offline_validation_commands"}
    for path, key, value in _walk(packet):
        normalized_key = key.lower().replace("-", "_")
        if normalized_key in _REQUIRED_FALSE_FLAGS and value is not False:
            problems.append(f"{path} must be false")
        if "active_mutation" in normalized_key and _truthy(value):
            problems.append(f"{path} contains an active mutation flag")
        if normalized_key not in allowed_command_keys and path not in allowed_private_key_paths:
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
