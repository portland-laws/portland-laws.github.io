"""Fixture-first agent gap-analysis delta packet v1.

This module replays committed synthetic user cases against inactive delta packet
fixtures and records only changed gap-analysis outputs. It does not crawl,
access DevHub, fill forms, upload, submit, certify, pay, schedule, or mutate
active prompts, guardrails, process models, requirements, contracts, sources,
DevHub surfaces, release state, or daemon state.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PACKET_TYPE = "ppd.fixture_first_agent_gap_analysis_delta_packet.v1"
PACKET_VERSION = "v1"
MODE = "offline_fixture_replay_only"

EXACT_OFFLINE_VALIDATION_COMMANDS = [
    ["python3", "-m", "py_compile", "ppd/agent_readiness/agent_gap_analysis_delta_packet_v1.py"],
    ["python3", "-m", "pytest", "ppd/tests/test_agent_gap_analysis_delta_packet_v1.py"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]

REQUIRED_BOUNDARIES = {
    "fixture_first": True,
    "synthetic_user_cases_only": True,
    "no_private_user_facts": True,
    "no_live_crawling": True,
    "no_devhub_access": True,
    "no_form_filling": True,
    "no_uploads": True,
    "no_submissions": True,
    "no_certifications": True,
    "no_payments": True,
    "no_scheduling": True,
    "no_active_prompt_mutation": True,
    "no_active_guardrail_mutation": True,
    "no_active_process_model_mutation": True,
    "no_active_requirement_mutation": True,
    "no_active_contract_mutation": True,
    "no_active_source_mutation": True,
    "no_devhub_surface_mutation": True,
    "no_release_state_mutation": True,
    "no_daemon_state_mutation": True,
}

REQUIRED_INPUT_PACKET_KEYS = (
    "source_freshness_delta_packet",
    "requirement_delta_packet",
    "process_dependency_delta_packet",
    "guardrail_impact_delta_packet",
)

REQUIRED_REPLAY_FIELDS = (
    "case_id",
    "changed_missing_facts",
    "changed_missing_documents",
    "changed_stale_evidence",
    "changed_conflicting_evidence",
    "required_confirmations",
    "blocked_actions",
    "next_safe_actions",
    "citation_references",
    "reviewer_holds",
    "offline_validation_commands",
)

REQUIRED_NON_EMPTY_REPLAY_LISTS = (
    "changed_missing_facts",
    "changed_missing_documents",
    "changed_stale_evidence",
    "changed_conflicting_evidence",
    "required_confirmations",
    "blocked_actions",
    "next_safe_actions",
    "citation_references",
    "reviewer_holds",
)

PRIVATE_KEY_TOKENS = (
    "address",
    "applicant",
    "auth",
    "browser",
    "card",
    "cookie",
    "credential",
    "cvv",
    "download",
    "downloaded",
    "email",
    "har",
    "name",
    "password",
    "payment",
    "phone",
    "private",
    "raw",
    "screenshot",
    "session",
    "site_address",
    "storage_state",
    "tax_account",
    "token",
    "trace",
)

PRIVATE_VALUE_TOKENS = (
    "/home/",
    "/users/",
    "c:\\users\\",
    "auth state",
    "browser state",
    "cookie",
    "credential",
    "downloaded artifact",
    "downloaded document",
    "har file",
    "password",
    "payment detail",
    "private devhub",
    "private user",
    "raw authenticated",
    "raw crawl",
    "raw downloaded",
    "screenshot",
    "session state",
    "storage state",
    "trace.zip",
)

FORBIDDEN_ACTION_TOKENS = (
    "certify",
    "click submit",
    "final submit",
    "pay fee",
    "payment",
    "purchase permit",
    "schedule inspection",
    "submit application",
    "submit permit",
    "upload correction",
    "upload document",
)

FORBIDDEN_LIVE_OR_DEVHUB_CLAIMS = (
    "accessed devhub",
    "authenticated devhub",
    "devhub session",
    "live crawl",
    "opened devhub",
    "ran crawl",
    "started crawl",
    "visited devhub",
)

FORBIDDEN_GUARANTEES = (
    "application will be accepted",
    "approval guaranteed",
    "guarantee approval",
    "guaranteed approval",
    "inspection will pass",
    "legal determination",
    "permit will be approved",
    "permit will be issued",
    "permitting guarantee",
)

FORBIDDEN_COMPLETION_CLAIMS = (
    "certification completed",
    "fee paid",
    "inspection scheduled",
    "official action completed",
    "payment submitted",
    "permit purchased",
    "submitted application",
    "submitted permit",
    "upload completed",
    "uploaded correction",
)

ACTIVE_MUTATION_KEY_TOKENS = (
    "active_contract_mutation",
    "active_daemon_state_mutation",
    "active_devhub_surface_mutation",
    "active_guardrail_mutation",
    "active_process_model_mutation",
    "active_prompt_mutation",
    "active_release_state_mutation",
    "active_requirement_mutation",
    "active_source_mutation",
    "apply_active",
    "mutate_active",
    "writes_active",
)


@dataclass(frozen=True)
class AgentGapAnalysisDeltaPacketV1ValidationResult:
    valid: bool
    problems: tuple[str, ...]


class AgentGapAnalysisDeltaPacketV1Error(ValueError):
    def __init__(self, problems: Iterable[str]) -> None:
        self.problems = tuple(problems)
        super().__init__("invalid agent gap-analysis delta packet v1: " + "; ".join(self.problems))


def load_json_object(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object at {path}")
    return value


def build_agent_gap_analysis_delta_packet_v1_from_file(path: str | Path) -> dict[str, Any]:
    return build_agent_gap_analysis_delta_packet_v1(load_json_object(path))


def build_agent_gap_analysis_delta_packet_v1(fixture: Mapping[str, Any]) -> dict[str, Any]:
    """Build a deterministic offline replay packet from synthetic fixtures."""

    _assert_valid_input_fixture(fixture)
    input_packets = fixture["input_delta_packets"]
    cases = _mapping_sequence(fixture.get("synthetic_user_cases"))

    source_changes = _index_changes(input_packets["source_freshness_delta_packet"], "source_id")
    requirement_changes = _index_changes(input_packets["requirement_delta_packet"], "requirement_id")
    process_changes = _index_changes(input_packets["process_dependency_delta_packet"], "dependency_id")
    guardrail_changes = _index_changes(input_packets["guardrail_impact_delta_packet"], "guardrail_rule_id")

    replay_results = []
    for case in cases:
        replay_results.append(
            _replay_case(
                case=case,
                source_changes=source_changes,
                requirement_changes=requirement_changes,
                process_changes=process_changes,
                guardrail_changes=guardrail_changes,
            )
        )

    packet = {
        "packet_type": PACKET_TYPE,
        "packet_version": PACKET_VERSION,
        "mode": MODE,
        "boundaries": dict(REQUIRED_BOUNDARIES),
        "input_delta_packet_refs": {
            key: _text(input_packets[key].get("packet_id"), default=key) for key in REQUIRED_INPUT_PACKET_KEYS
        },
        "synthetic_replay_results": replay_results,
        "validation_commands": [list(command) for command in EXACT_OFFLINE_VALIDATION_COMMANDS],
    }
    assert_valid_agent_gap_analysis_delta_packet_v1(packet)
    return packet


def validate_agent_gap_analysis_delta_packet_v1(packet: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if packet.get("packet_type") != PACKET_TYPE:
        errors.append(f"packet_type must be {PACKET_TYPE}")
    if packet.get("packet_version") != PACKET_VERSION:
        errors.append("packet_version must be v1")
    if packet.get("mode") != MODE:
        errors.append(f"mode must be {MODE}")

    boundaries = packet.get("boundaries")
    if not isinstance(boundaries, Mapping):
        errors.append("boundaries must be an object")
    else:
        for key, expected in REQUIRED_BOUNDARIES.items():
            if boundaries.get(key) is not expected:
                errors.append(f"boundaries.{key} must be {str(expected).lower()}")

    refs = packet.get("input_delta_packet_refs")
    if not isinstance(refs, Mapping):
        errors.append("input_delta_packet_refs must be an object")
    else:
        for key in REQUIRED_INPUT_PACKET_KEYS:
            if not isinstance(refs.get(key), str) or not refs.get(key):
                errors.append(f"input_delta_packet_refs.{key} must be a non-empty string")

    results = packet.get("synthetic_replay_results")
    if not isinstance(results, list) or not results:
        errors.append("synthetic_replay_results must be a non-empty list")
        results = []

    seen_cases: set[str] = set()
    for index, result in enumerate(results):
        if not isinstance(result, Mapping):
            errors.append(f"synthetic_replay_results[{index}] must be an object")
            continue
        case_id = _text(result.get("case_id"))
        if not case_id:
            errors.append(f"synthetic_replay_results[{index}].case_id must be a non-empty string")
        if case_id in seen_cases:
            errors.append(f"synthetic_replay_results[{index}].case_id must be unique")
        seen_cases.add(case_id)
        errors.extend(_validate_replay_result(result, f"synthetic_replay_results[{index}]"))

    if packet.get("validation_commands") != EXACT_OFFLINE_VALIDATION_COMMANDS:
        errors.append("validation_commands must contain only the exact offline validation commands")

    errors.extend(_scan_for_private_or_live_content(packet))
    return errors


def assert_valid_agent_gap_analysis_delta_packet_v1(packet: Mapping[str, Any]) -> None:
    errors = validate_agent_gap_analysis_delta_packet_v1(packet)
    if errors:
        raise AgentGapAnalysisDeltaPacketV1Error(errors)


def validation_result(packet: Mapping[str, Any]) -> AgentGapAnalysisDeltaPacketV1ValidationResult:
    problems = tuple(validate_agent_gap_analysis_delta_packet_v1(packet))
    return AgentGapAnalysisDeltaPacketV1ValidationResult(valid=not problems, problems=problems)


def _assert_valid_input_fixture(fixture: Mapping[str, Any]) -> None:
    problems: list[str] = []
    packets = fixture.get("input_delta_packets")
    if not isinstance(packets, Mapping):
        problems.append("input_delta_packets must be an object")
    else:
        for key in REQUIRED_INPUT_PACKET_KEYS:
            packet = packets.get(key)
            if not isinstance(packet, Mapping):
                problems.append(f"input_delta_packets.{key} must be an object")
            elif not isinstance(packet.get("changes"), list):
                problems.append(f"input_delta_packets.{key}.changes must be a list")

    cases = fixture.get("synthetic_user_cases")
    if not isinstance(cases, list) or not cases:
        problems.append("synthetic_user_cases must be a non-empty list")
    else:
        for index, case in enumerate(cases):
            path = f"synthetic_user_cases[{index}]"
            if not isinstance(case, Mapping):
                problems.append(f"{path} must be an object")
                continue
            for field in ("case_id", "process_id", "source_ids", "requirement_ids", "dependency_ids", "guardrail_rule_ids"):
                if field not in case:
                    problems.append(f"{path}.{field} is required")

    problems.extend(_scan_for_private_or_live_content(fixture))
    if problems:
        raise AgentGapAnalysisDeltaPacketV1Error(problems)


def _replay_case(
    *,
    case: Mapping[str, Any],
    source_changes: Mapping[str, Mapping[str, Any]],
    requirement_changes: Mapping[str, Mapping[str, Any]],
    process_changes: Mapping[str, Mapping[str, Any]],
    guardrail_changes: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    matched_source_changes = [_change for ref in _string_sequence(case.get("source_ids")) if (_change := source_changes.get(ref))]
    matched_requirement_changes = [_change for ref in _string_sequence(case.get("requirement_ids")) if (_change := requirement_changes.get(ref))]
    matched_process_changes = [_change for ref in _string_sequence(case.get("dependency_ids")) if (_change := process_changes.get(ref))]
    matched_guardrail_changes = [_change for ref in _string_sequence(case.get("guardrail_rule_ids")) if (_change := guardrail_changes.get(ref))]

    citation_references = _unique_strings(
        _flatten_strings(change.get("citation_references") for change in matched_source_changes)
        + _flatten_strings(change.get("citation_references") for change in matched_requirement_changes)
        + _flatten_strings(change.get("citation_references") for change in matched_process_changes)
        + _flatten_strings(change.get("citation_references") for change in matched_guardrail_changes)
    )

    result = {
        "case_id": _text(case.get("case_id")),
        "process_id": _text(case.get("process_id")),
        "changed_missing_facts": _unique_strings(
            _flatten_strings(change.get("changed_missing_facts") for change in matched_requirement_changes)
            + _flatten_strings(change.get("changed_missing_facts") for change in matched_process_changes)
        ),
        "changed_missing_documents": _unique_strings(
            _flatten_strings(change.get("changed_missing_documents") for change in matched_requirement_changes)
            + _flatten_strings(change.get("changed_missing_documents") for change in matched_process_changes)
        ),
        "changed_stale_evidence": _unique_strings(
            _flatten_strings(change.get("changed_stale_evidence") for change in matched_source_changes)
        ),
        "changed_conflicting_evidence": _unique_strings(
            _flatten_strings(change.get("changed_conflicting_evidence") for change in matched_source_changes)
            + _flatten_strings(change.get("changed_conflicting_evidence") for change in matched_requirement_changes)
        ),
        "required_confirmations": _unique_strings(
            _flatten_strings(change.get("required_confirmations") for change in matched_guardrail_changes)
            + _flatten_strings(change.get("required_confirmations") for change in matched_process_changes)
        ),
        "blocked_actions": _blocked_actions(matched_guardrail_changes),
        "next_safe_actions": _next_safe_actions(case, citation_references),
        "citation_references": citation_references,
        "reviewer_holds": _reviewer_holds(matched_source_changes, matched_requirement_changes, matched_process_changes, matched_guardrail_changes),
        "offline_validation_commands": [list(command) for command in EXACT_OFFLINE_VALIDATION_COMMANDS],
    }
    return result


def _blocked_actions(changes: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    actions = []
    for change in changes:
        citations = _string_sequence(change.get("citation_references"))
        for action in _string_sequence(change.get("blocked_actions")):
            actions.append(
                {
                    "action": action,
                    "blocked": True,
                    "requires_human_confirmation_before_unblock": True,
                    "official_action_performed": False,
                    "citation_references": citations,
                }
            )
    return _unique_mapping_list(actions, "action")


def _next_safe_actions(case: Mapping[str, Any], citation_references: Sequence[str]) -> list[dict[str, Any]]:
    return [
        {
            "action": "review_fixture_gap_delta",
            "case_id": _text(case.get("case_id")),
            "uses_only_committed_fixtures": True,
            "requires_live_crawl": False,
            "requires_devhub": False,
            "fills_form": False,
            "uploads": False,
            "submits": False,
            "certifies": False,
            "pays_fee": False,
            "schedules": False,
            "citation_references": list(citation_references),
        }
    ]


def _reviewer_holds(*change_groups: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    holds = []
    for group in change_groups:
        for change in group:
            citations = _string_sequence(change.get("citation_references"))
            for hold in _string_sequence(change.get("reviewer_holds")):
                holds.append({"hold": hold, "status": "pending_human_review", "citation_references": citations})
    return _unique_mapping_list(holds, "hold")


def _validate_replay_result(result: Mapping[str, Any], path: str) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_REPLAY_FIELDS:
        if field not in result:
            errors.append(f"{path}.{field} is required")

    for field in REQUIRED_NON_EMPTY_REPLAY_LISTS:
        value = result.get(field)
        if not isinstance(value, list):
            errors.append(f"{path}.{field} must be a list")
        elif not value:
            errors.append(f"{path}.{field} must contain at least one row")

    for field in (
        "changed_missing_facts",
        "changed_missing_documents",
        "changed_stale_evidence",
        "changed_conflicting_evidence",
        "required_confirmations",
        "citation_references",
    ):
        for index, row in enumerate(result.get(field, [])):
            if not isinstance(row, str) or not row.strip():
                errors.append(f"{path}.{field}[{index}] must be a non-empty string")

    for index, action in enumerate(result.get("blocked_actions", [])):
        if not isinstance(action, Mapping):
            errors.append(f"{path}.blocked_actions[{index}] must be an object")
            continue
        if not _text(action.get("action")):
            errors.append(f"{path}.blocked_actions[{index}].action must be a non-empty string")
        if action.get("blocked") is not True:
            errors.append(f"{path}.blocked_actions[{index}].blocked must be true")
        if action.get("requires_human_confirmation_before_unblock") is not True:
            errors.append(f"{path}.blocked_actions[{index}] must require human confirmation before unblock")
        if action.get("official_action_performed") is not False:
            errors.append(f"{path}.blocked_actions[{index}].official_action_performed must be false")
        if not _string_sequence(action.get("citation_references")):
            errors.append(f"{path}.blocked_actions[{index}].citation_references must contain at least one citation")

    for index, action in enumerate(result.get("next_safe_actions", [])):
        if not isinstance(action, Mapping):
            errors.append(f"{path}.next_safe_actions[{index}] must be an object")
            continue
        if not _text(action.get("action")):
            errors.append(f"{path}.next_safe_actions[{index}].action must be a non-empty string")
        for flag in ("requires_live_crawl", "requires_devhub", "fills_form", "uploads", "submits", "certifies", "pays_fee", "schedules"):
            if action.get(flag) is not False:
                errors.append(f"{path}.next_safe_actions[{index}].{flag} must be false")
        if action.get("uses_only_committed_fixtures") is not True:
            errors.append(f"{path}.next_safe_actions[{index}].uses_only_committed_fixtures must be true")
        if not _string_sequence(action.get("citation_references")):
            errors.append(f"{path}.next_safe_actions[{index}].citation_references must contain at least one citation")

    for index, hold in enumerate(result.get("reviewer_holds", [])):
        if not isinstance(hold, Mapping):
            errors.append(f"{path}.reviewer_holds[{index}] must be an object")
            continue
        if not _text(hold.get("hold")):
            errors.append(f"{path}.reviewer_holds[{index}].hold must be a non-empty string")
        if hold.get("status") != "pending_human_review":
            errors.append(f"{path}.reviewer_holds[{index}].status must be pending_human_review")
        if not _string_sequence(hold.get("citation_references")):
            errors.append(f"{path}.reviewer_holds[{index}].citation_references must contain at least one citation")

    if result.get("offline_validation_commands") != EXACT_OFFLINE_VALIDATION_COMMANDS:
        errors.append(f"{path}.offline_validation_commands must contain only exact offline validation commands")
    return errors


def _index_changes(packet: Mapping[str, Any], key: str) -> dict[str, Mapping[str, Any]]:
    indexed: dict[str, Mapping[str, Any]] = {}
    for change in _mapping_sequence(packet.get("changes")):
        ref = _text(change.get(key))
        if ref:
            indexed[ref] = change
    return indexed


def _mapping_sequence(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _string_sequence(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_text(item) for item in value if _text(item)]


def _flatten_strings(values: Iterable[Any]) -> list[str]:
    flattened: list[str] = []
    for value in values:
        flattened.extend(_string_sequence(value))
    return flattened


def _unique_strings(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        text = _text(value)
        if text and text not in seen:
            seen.add(text)
            unique.append(text)
    return unique


def _unique_mapping_list(values: Iterable[Mapping[str, Any]], key: str) -> list[dict[str, Any]]:
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for value in values:
        marker = _text(value.get(key))
        if marker and marker not in seen:
            seen.add(marker)
            unique.append(dict(value))
    return unique


def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def _scan_for_private_or_live_content(value: Any, path: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = str(key)
            key_lower = key_text.lower()
            nested_path = f"{path}.{key_text}"
            if any(token == key_lower or token in key_lower for token in PRIVATE_KEY_TOKENS):
                errors.append(f"{nested_path} uses a private-data key")
            if any(token == key_lower or token in key_lower for token in ACTIVE_MUTATION_KEY_TOKENS) and nested is not False:
                errors.append(f"{nested_path} contains an active mutation flag")
            errors.extend(_scan_for_private_or_live_content(nested, nested_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            errors.extend(_scan_for_private_or_live_content(nested, f"{path}[{index}]"))
    elif isinstance(value, str):
        lower = value.lower()
        if any(token in lower for token in PRIVATE_VALUE_TOKENS):
            errors.append(f"{path} contains private or live-session content")
        if any(token in lower for token in FORBIDDEN_LIVE_OR_DEVHUB_CLAIMS):
            errors.append(f"{path} contains a live crawl or DevHub access claim")
        if any(token in lower for token in FORBIDDEN_GUARANTEES):
            errors.append(f"{path} contains a legal or permitting guarantee")
        if any(token in lower for token in FORBIDDEN_COMPLETION_CLAIMS):
            errors.append(f"{path} contains an official-action completion claim")
        if any(token in lower for token in FORBIDDEN_ACTION_TOKENS) and "blocked" not in lower and "hold" not in lower:
            errors.append(f"{path} contains an unblocked official-action phrase")
    return errors
