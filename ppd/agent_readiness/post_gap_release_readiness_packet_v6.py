"""Fixture-first post-gap release readiness packet v6."""

from __future__ import annotations

import copy
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PACKET_TYPE = "ppd.post_gap_release_readiness_packet.v6"
PACKET_VERSION = "v6"
MODE = "fixture_first_post_gap_release_readiness_v6"
REPLAY_PACKET_VERSION = "post_gap_agent_readiness_replay_v6"

EXACT_OFFLINE_VALIDATION_COMMANDS = [
    ["python3", "-m", "py_compile", "ppd/agent_readiness/post_gap_release_readiness_packet_v6.py"],
    ["python3", "-m", "py_compile", "ppd/tests/test_post_gap_release_readiness_packet_v6.py"],
    ["python3", "-m", "pytest", "ppd/tests/test_post_gap_release_readiness_packet_v6.py"],
]

_REQUIRED_TRUE_FLAGS = (
    "fixture_first",
    "post_gap_readiness_replay_fixtures_only",
    "manual_reviewer_decision_required",
    "unresolved_missing_fact_hold_required",
    "stale_evidence_hold_required",
    "rollback_owner_assignment_required",
)

_REQUIRED_FALSE_FLAGS = (
    "active_guardrail_mutation",
    "active_release_state_mutation",
    "active_mutation",
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

_REQUIRED_LIST_FIELDS = (
    "source_fixture_refs",
    "reviewer_go_no_go_rows",
    "unresolved_hold_inventory",
    "reversible_draft_readiness_summaries",
    "local_pdf_preview_readiness_summaries",
    "refused_consequential_action_summaries",
    "refused_financial_action_summaries",
    "journal_dry_run_coverage_refs",
    "citation_coverage_notes",
    "rollback_owner_placeholders",
    "agent_notification_rows",
    "offline_validation_commands",
)

_FORBIDDEN_TEXT_MARKERS = (
    ("live_activation_claim", ("live activation enabled", "activated live automation", "live crawl enabled", "guardrails activated", "release activated")),
    ("private_session_auth_artifact", ("session cookie", "auth state", "bearer token", "private token", "devhub session", "password", "credential")),
    ("official_action_completion_claim", ("submitted permit", "uploaded correction", "certified acknowledgement", "paid fee", "scheduled inspection", "official action completed")),
    ("legal_or_permitting_guarantee", ("legal guarantee", "permit guaranteed", "approval guaranteed", "guaranteed approval", "permitting guarantee")),
    ("active_mutation_flag", ("active mutation enabled", "write mode enabled", "live mutation", "mutation enabled")),
)

_ACTIVE_MUTATION_KEYS = {"active_mutation", "active_guardrail_mutation", "active_release_state_mutation", "mutates_live_state", "write_mode_enabled"}
_PRIVATE_PATH_MARKERS = ("/home/", "/users/", "c:\\users\\", "session", "auth", "cookie", "trace", "har")


@dataclass(frozen=True)
class PostGapReleaseReadinessPacketV6Result:
    valid: bool
    problems: tuple[str, ...]


class PostGapReleaseReadinessPacketV6Error(ValueError):
    def __init__(self, problems: Iterable[str]) -> None:
        self.problems = tuple(problems)
        super().__init__("invalid post-gap release readiness packet v6: " + "; ".join(self.problems))


def load_json(path: str | Path) -> dict[str, Any]:
    loaded = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("post-gap release readiness fixture must be a JSON object")
    return loaded


def build_post_gap_release_readiness_packet_v6_from_fixture(replay_fixture_path: str | Path) -> dict[str, Any]:
    replay_path = Path(replay_fixture_path)
    return build_post_gap_release_readiness_packet_v6(load_json(replay_path), replay_fixture_ref=replay_path.as_posix())


def build_post_gap_release_readiness_packet_v6(replay: Mapping[str, Any], *, replay_fixture_ref: str) -> dict[str, Any]:
    _validate_replay_fixture(replay)
    responses = _mapping_sequence(replay.get("responses"))
    missing_fact_holds = _missing_fact_holds(responses)
    stale_holds = _stale_evidence_holds(responses)
    unresolved_hold_count = len(missing_fact_holds) + len(stale_holds)

    packet = {
        "packet_type": PACKET_TYPE,
        "packet_version": PACKET_VERSION,
        "mode": MODE,
        "fixture_first": True,
        "post_gap_readiness_replay_fixtures_only": True,
        "manual_reviewer_decision_required": True,
        "unresolved_missing_fact_hold_required": True,
        "stale_evidence_hold_required": True,
        "rollback_owner_assignment_required": True,
        "active_guardrail_mutation": False,
        "active_release_state_mutation": False,
        "active_mutation": False,
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
            {"fixture_role": "post_gap_agent_readiness_replay_v6", "path": replay_fixture_ref}
        ],
        "consumes_only": {
            "post_gap_agent_readiness_replay_v6_fixtures": True,
            "replay_packet_version": REPLAY_PACKET_VERSION,
        },
        "reviewer_go_no_go_rows": [
            {
                "row_id": "post-gap-release-readiness-v6-reviewer-row",
                "recommendation": "NO_GO" if unresolved_hold_count else "GO_WITH_CAVEATS",
                "activation_allowed": False,
                "manual_reviewer_final_decision_required": True,
                "unresolved_hold_count": unresolved_hold_count,
                "basis": "Fixture replay still requires reviewer disposition of missing facts, stale evidence, refused official actions, rollback ownership, and agent notices.",
            }
        ],
        "unresolved_hold_inventory": missing_fact_holds + stale_holds,
        "reversible_draft_readiness_summaries": _route_summaries(responses, "reversible_local_draft_preview", "draft_preview"),
        "local_pdf_preview_readiness_summaries": _route_summaries(responses, "local_pdf_preview_only", "pdf_preview"),
        "refused_consequential_action_summaries": _refused_action_summaries(responses, "consequential"),
        "refused_financial_action_summaries": _refused_action_summaries(responses, "financial"),
        "journal_dry_run_coverage_refs": _journal_coverage_refs(replay, responses),
        "citation_coverage_notes": _citation_coverage_notes(responses),
        "rollback_owner_placeholders": [
            {
                "placeholder_id": "rollback-owner-post-gap-release-readiness-v6",
                "owner": "REVIEWER_TBD",
                "assignment_required_before": "release_signoff",
                "active_state_changed": False,
            }
        ],
        "agent_notification_rows": _agent_notification_rows(responses),
        "offline_validation_commands": copy.deepcopy(EXACT_OFFLINE_VALIDATION_COMMANDS),
    }
    assert_valid_post_gap_release_readiness_packet_v6(packet)
    return packet


def assert_valid_post_gap_release_readiness_packet_v6(packet: Mapping[str, Any]) -> None:
    result = validate_post_gap_release_readiness_packet_v6(packet)
    if not result.valid:
        raise PostGapReleaseReadinessPacketV6Error(result.problems)


def validate_post_gap_release_readiness_packet_v6(packet: Mapping[str, Any]) -> PostGapReleaseReadinessPacketV6Result:
    if not isinstance(packet, Mapping):
        return PostGapReleaseReadinessPacketV6Result(False, ("packet must be an object",))

    problems: list[str] = []
    if packet.get("packet_type") != PACKET_TYPE:
        problems.append(f"packet_type must be {PACKET_TYPE}")
    if packet.get("packet_version") != PACKET_VERSION:
        problems.append("packet_version must be v6")
    if packet.get("mode") != MODE:
        problems.append(f"mode must be {MODE}")
    if packet.get("offline_validation_commands") != EXACT_OFFLINE_VALIDATION_COMMANDS:
        problems.append("offline_validation_commands must exactly match post-gap release readiness v6 commands")

    consumes = packet.get("consumes_only")
    if not isinstance(consumes, Mapping) or consumes.get("post_gap_agent_readiness_replay_v6_fixtures") is not True:
        problems.append("consumes_only must require post-gap agent readiness replay v6 fixtures")
    if isinstance(consumes, Mapping) and consumes.get("replay_packet_version") != REPLAY_PACKET_VERSION:
        problems.append("consumes_only.replay_packet_version must reference post-gap agent readiness replay v6")

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
    _validate_reviewer_rows(packet.get("reviewer_go_no_go_rows"), problems)
    _validate_hold_inventory(packet.get("unresolved_hold_inventory"), problems)
    _validate_preview_summaries(packet.get("reversible_draft_readiness_summaries"), "reversible_draft_readiness_summaries", "reversible_local_draft_preview", problems)
    _validate_preview_summaries(packet.get("local_pdf_preview_readiness_summaries"), "local_pdf_preview_readiness_summaries", "local_pdf_preview_only", problems)
    _validate_refused_summaries(packet.get("refused_consequential_action_summaries"), "refused_consequential_action_summaries", "consequential", problems)
    _validate_refused_summaries(packet.get("refused_financial_action_summaries"), "refused_financial_action_summaries", "financial", problems)
    _validate_journal_refs(packet.get("journal_dry_run_coverage_refs"), problems)
    _validate_citation_notes(packet.get("citation_coverage_notes"), problems)
    _validate_rollback_placeholders(packet.get("rollback_owner_placeholders"), problems)
    _validate_agent_notifications(packet.get("agent_notification_rows"), problems)
    _scan_for_forbidden_content(packet, problems, "$", parent_key="")

    return PostGapReleaseReadinessPacketV6Result(not problems, tuple(dict.fromkeys(problems)))


def _validate_source_fixture_refs(value: Any, problems: list[str]) -> None:
    refs = _mapping_sequence(value)
    if not any(ref.get("fixture_role") == "post_gap_agent_readiness_replay_v6" and _text(ref.get("path")) for ref in refs):
        problems.append("source_fixture_refs must include post_gap_agent_readiness_replay_v6 fixture path")


def _validate_reviewer_rows(value: Any, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"reviewer_go_no_go_rows[{index}]"
        if row.get("recommendation") not in {"NO_GO", "GO_WITH_CAVEATS"}:
            problems.append(f"{prefix}.recommendation must be NO_GO or GO_WITH_CAVEATS")
        if row.get("activation_allowed") is not False:
            problems.append(f"{prefix}.activation_allowed must be false")
        if row.get("manual_reviewer_final_decision_required") is not True:
            problems.append(f"{prefix}.manual_reviewer_final_decision_required must be true")
        if not isinstance(row.get("unresolved_hold_count"), int):
            problems.append(f"{prefix}.unresolved_hold_count must be an integer")


def _validate_hold_inventory(value: Any, problems: list[str]) -> None:
    rows = _mapping_sequence(value)
    hold_types = {row.get("hold_type") for row in rows}
    if "missing_fact" not in hold_types:
        problems.append("unresolved_hold_inventory must include a missing_fact hold")
    if "stale_evidence" not in hold_types:
        problems.append("unresolved_hold_inventory must include a stale_evidence hold")
    for index, row in enumerate(rows):
        prefix = f"unresolved_hold_inventory[{index}]"
        if not _text(row.get("hold_id")):
            problems.append(f"{prefix}.hold_id is required")
        if row.get("reviewer_disposition_required") is not True:
            problems.append(f"{prefix}.reviewer_disposition_required must be true")
        if row.get("release_blocked") is not True:
            problems.append(f"{prefix}.release_blocked must be true")


def _validate_preview_summaries(value: Any, field: str, expected_route: str, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"{field}[{index}]"
        if row.get("route") != expected_route:
            problems.append(f"{prefix}.route must be {expected_route}")
        if row.get("ready_for_reviewer_preview_only") is not True:
            problems.append(f"{prefix}.ready_for_reviewer_preview_only must be true")
        if row.get("official_action_allowed") is not False:
            problems.append(f"{prefix}.official_action_allowed must be false")


def _validate_refused_summaries(value: Any, field: str, category: str, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"{field}[{index}]"
        if row.get("action_category") != category:
            problems.append(f"{prefix}.action_category must be {category}")
        if row.get("refused") is not True:
            problems.append(f"{prefix}.refused must be true")
        if row.get("manual_handoff_required") is not True:
            problems.append(f"{prefix}.manual_handoff_required must be true")
        if row.get("official_action_completed") is not False:
            problems.append(f"{prefix}.official_action_completed must be false")


def _validate_journal_refs(value: Any, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"journal_dry_run_coverage_refs[{index}]"
        if not _text(row.get("journal_event")):
            problems.append(f"{prefix}.journal_event is required")
        if row.get("dry_run_only") is not True:
            problems.append(f"{prefix}.dry_run_only must be true")


def _validate_citation_notes(value: Any, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"citation_coverage_notes[{index}]"
        if not _text(row.get("url")) and not _text(row.get("label")):
            problems.append(f"{prefix} must include a citation label or url")
        if row.get("fixture_citation_only") is not True:
            problems.append(f"{prefix}.fixture_citation_only must be true")
        if row.get("coverage_status") != "present":
            problems.append(f"{prefix}.coverage_status must be present")


def _validate_rollback_placeholders(value: Any, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"rollback_owner_placeholders[{index}]"
        if row.get("owner") != "REVIEWER_TBD":
            problems.append(f"{prefix}.owner must be REVIEWER_TBD")
        if not _text(row.get("assignment_required_before")):
            problems.append(f"{prefix}.assignment_required_before is required")
        if row.get("active_state_changed") is not False:
            problems.append(f"{prefix}.active_state_changed must be false")


def _validate_agent_notifications(value: Any, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"agent_notification_rows[{index}]"
        if row.get("notification_status") != "draft_note_only":
            problems.append(f"{prefix}.notification_status must be draft_note_only")
        if row.get("send_or_submit_allowed") is not False:
            problems.append(f"{prefix}.send_or_submit_allowed must be false")
        if not isinstance(row.get("manual_handoff_reminders"), Sequence) or isinstance(row.get("manual_handoff_reminders"), (str, bytes)):
            problems.append(f"{prefix}.manual_handoff_reminders must be a list")


def _scan_for_forbidden_content(value: Any, problems: list[str], path: str, *, parent_key: str) -> None:
    key_name = parent_key.lower()
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_key = str(key)
            child_path = f"{path}.{child_key}"
            if child_key.lower() in _ACTIVE_MUTATION_KEYS and child is not False:
                problems.append(f"active mutation flag is not allowed at {child_path}")
            _scan_for_forbidden_content(child, problems, child_path, parent_key=child_key)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, child in enumerate(value):
            _scan_for_forbidden_content(child, problems, f"{path}[{index}]", parent_key=parent_key)
        return
    if not isinstance(value, str):
        return

    lowered = value.lower()
    for code, markers in _FORBIDDEN_TEXT_MARKERS:
        if any(marker in lowered for marker in markers):
            problems.append(f"{code} is not allowed at {path}")
    if any(marker in key_name for marker in ("path", "artifact", "session", "auth")) and any(marker in lowered for marker in _PRIVATE_PATH_MARKERS):
        problems.append(f"private/session/auth artifact is not allowed at {path}")


def _validate_replay_fixture(replay: Mapping[str, Any]) -> None:
    if replay.get("packet_version") != REPLAY_PACKET_VERSION:
        raise ValueError("post-gap release readiness packet v6 consumes only post-gap agent readiness replay v6 fixtures")
    if replay.get("fixture_only") is not True:
        raise ValueError("post-gap readiness replay fixture must be fixture_only")
    if not _mapping_sequence(replay.get("responses")):
        raise ValueError("post-gap readiness replay fixture must include response rows")


def _missing_fact_holds(responses: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    holds: list[dict[str, Any]] = []
    seen: set[str] = set()
    for response in responses:
        for prompt in _mapping_sequence(response.get("missing_information_prompts")):
            prompt_id = _text(prompt.get("id"))
            if prompt_id and prompt_id not in seen:
                seen.add(prompt_id)
                holds.append(
                    {
                        "hold_id": f"missing-fact-{prompt_id}",
                        "hold_type": "missing_fact",
                        "source_prompt_id": prompt_id,
                        "reviewer_disposition_required": True,
                        "release_blocked": True,
                    }
                )
    return holds


def _stale_evidence_holds(responses: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    holds: list[dict[str, Any]] = []
    seen: set[str] = set()
    for response in responses:
        for limitation in _mapping_sequence(response.get("evidence_limitations")):
            if limitation.get("kind") != "stale":
                continue
            evidence_id = _text(limitation.get("evidence_id"))
            if evidence_id and evidence_id not in seen:
                seen.add(evidence_id)
                holds.append(
                    {
                        "hold_id": f"stale-evidence-{evidence_id}",
                        "hold_type": "stale_evidence",
                        "evidence_id": evidence_id,
                        "reason": _text(limitation.get("explanation")),
                        "reviewer_disposition_required": True,
                        "release_blocked": True,
                    }
                )
    return holds


def _route_summaries(responses: Sequence[Mapping[str, Any]], route: str, summary_kind: str) -> list[dict[str, Any]]:
    rows = []
    for response in responses:
        if response.get("route") == route:
            rows.append(
                {
                    "summary_id": f"{summary_kind}-{response.get('request_id')}",
                    "request_id": response.get("request_id"),
                    "route": route,
                    "ready_for_reviewer_preview_only": True,
                    "official_action_allowed": False,
                }
            )
    return rows


def _refused_action_summaries(responses: Sequence[Mapping[str, Any]], category: str) -> list[dict[str, Any]]:
    rows = []
    for response in responses:
        if response.get("refused") is True and response.get("action_category") == category:
            rows.append(
                {
                    "summary_id": f"refused-{category}-{response.get('request_id')}",
                    "request_id": response.get("request_id"),
                    "action_kind": response.get("action_kind"),
                    "action_category": category,
                    "refused": True,
                    "manual_handoff_required": True,
                    "official_action_completed": False,
                }
            )
    return rows


def _journal_coverage_refs(replay: Mapping[str, Any], responses: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    expected_events = [str(item) for item in replay.get("expected_journal_events", [])]
    rows = []
    for event in expected_events:
        covered_by = [str(response.get("request_id")) for response in responses if event in response.get("journal_events", [])]
        rows.append({"journal_event": event, "covered_by_request_ids": covered_by, "dry_run_only": True})
    return rows


def _citation_coverage_notes(responses: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for response in responses:
        for citation in _mapping_sequence(response.get("citations")):
            key = _text(citation.get("url")) or _text(citation.get("label"))
            if key and key not in seen:
                seen.add(key)
                rows.append(
                    {
                        "citation_note_id": f"citation-{len(rows) + 1:02d}",
                        "label": citation.get("label"),
                        "url": citation.get("url"),
                        "fixture_citation_only": True,
                        "coverage_status": "present",
                    }
                )
    return rows


def _agent_notification_rows(responses: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for response in responses:
        rows.append(
            {
                "notification_id": f"agent-notice-{response.get('request_id')}",
                "request_id": response.get("request_id"),
                "notification_status": "draft_note_only",
                "manual_handoff_reminders": list(response.get("manual_handoff_reminders", [])),
                "send_or_submit_allowed": False,
            }
        )
    return rows


def _mapping_sequence(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _non_empty_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes)) and bool(value)


def _text(value: Any) -> str:
    return value if isinstance(value, str) else ""
