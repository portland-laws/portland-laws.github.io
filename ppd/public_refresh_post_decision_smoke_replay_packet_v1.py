from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping, Sequence


ARTIFACT_ID = "public_refresh_post_decision_smoke_replay_packet_v1"
RELEASE_DECISION_ROW_SOURCE = "synthetic_public_refresh_release_decision_packet_rows"

OFFLINE_VALIDATION_COMMANDS = [
    ["python3", "-m", "py_compile", "ppd/public_refresh_post_decision_smoke_replay_packet_v1.py"],
    ["python3", "-m", "unittest", "ppd.tests.test_public_refresh_post_decision_smoke_replay_packet_v1"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]

FALSE_FLAGS = (
    "live_crawling_performed",
    "documents_downloaded",
    "raw_output_stored",
    "devhub_opened",
    "release_activated",
    "active_artifacts_mutated",
    "official_actions_performed",
    "private_session_artifacts_created",
)

TRUE_ATTESTATIONS = (
    "fixture_first",
    "synthetic_release_decision_rows_only",
    "offline_agent_api_smoke_expectations_only",
    "source_citation_lookup_checks_only",
    "guardrail_predicate_replay_checks_only",
    "blocked_action_regression_checks_only",
    "stale_source_hold_checks_only",
    "rollback_notes_only",
    "reviewer_routing_only",
    "exact_offline_validation_commands_only",
    "no_live_crawling",
    "no_document_downloads",
    "no_raw_output_storage",
    "no_devhub_access",
    "no_release_activation",
    "no_active_artifact_mutation",
    "no_official_actions",
)

FORBIDDEN_FIELD_TOKENS = (
    "auth_state",
    "browser_state",
    "cookie",
    "credential",
    "download",
    "har",
    "raw_body",
    "raw_capture",
    "raw_crawl",
    "raw_output",
    "screenshot",
    "session_state",
    "storage_state",
    "trace",
)

FORBIDDEN_TEXT_TOKENS = (
    "active artifacts mutated",
    "authenticated devhub",
    "devhub opened",
    "devhub.portlandoregon.gov",
    "document downloaded",
    "documents downloaded",
    "fee paid",
    "inspection scheduled",
    "live crawl",
    "live crawling",
    "official action completed",
    "official action performed",
    "permit approved",
    "permit issued",
    "raw output stored",
    "release activated",
    "submitted permit",
    "upload completed",
)

FORBIDDEN_COMMAND_TOKENS = (
    "activate",
    "auth",
    "browser",
    "crawl",
    "devhub",
    "download",
    "live",
    "playwright",
    "promote",
    "session",
)

VALID_DECISIONS = {"hold", "proceed", "skip"}


def build_public_refresh_post_decision_smoke_replay_packet_v1(
    release_decision_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    rows = [deepcopy(dict(row)) for row in release_decision_rows if isinstance(row, Mapping)]
    packet: dict[str, Any] = {
        "artifact_id": ARTIFACT_ID,
        "artifact_type": "fixture_first_public_refresh_post_decision_smoke_replay_packet",
        "version": 1,
        "status": "review_ready",
        "release_decision_row_source": RELEASE_DECISION_ROW_SOURCE,
        "consumed_release_decision_rows": rows,
        "agent_api_smoke_expectations": _agent_api_smoke_expectations(rows),
        "source_citation_lookup_checks": _source_citation_lookup_checks(rows),
        "guardrail_predicate_replay_checks": _guardrail_predicate_replay_checks(rows),
        "blocked_action_regression_checks": _blocked_action_regression_checks(rows),
        "stale_source_hold_checks": _stale_source_hold_checks(rows),
        "rollback_notes": _rollback_notes(rows),
        "reviewer_routing": _reviewer_routing(rows),
        "offline_validation_commands": deepcopy(OFFLINE_VALIDATION_COMMANDS),
        "attestations": {name: True for name in TRUE_ATTESTATIONS},
    }
    for flag in FALSE_FLAGS:
        packet[flag] = False
    result = validate_public_refresh_post_decision_smoke_replay_packet_v1(packet)
    if not result["valid"]:
        raise ValueError("; ".join(result["errors"]))
    return packet


def validate_public_refresh_post_decision_smoke_replay_packet_v1(packet: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if packet.get("artifact_id") != ARTIFACT_ID:
        errors.append(f"artifact_id must be {ARTIFACT_ID}")
    if packet.get("version") != 1:
        errors.append("version must be 1")
    if packet.get("release_decision_row_source") != RELEASE_DECISION_ROW_SOURCE:
        errors.append(f"release_decision_row_source must be {RELEASE_DECISION_ROW_SOURCE}")

    rows = _mapping_rows(packet.get("consumed_release_decision_rows"))
    if not rows:
        errors.append("consumed_release_decision_rows must include synthetic release decision packet rows")

    row_ids: set[str] = set()
    decisions: set[str] = set()
    for index, row in enumerate(rows):
        path = f"consumed_release_decision_rows[{index}]"
        row_id = _text(row.get("candidate_id"))
        if not row_id:
            errors.append(f"{path}.candidate_id is required")
        elif row_id in row_ids:
            errors.append(f"{path}.candidate_id must be unique")
        else:
            row_ids.add(row_id)
        decision = _text(row.get("decision"))
        if decision not in VALID_DECISIONS:
            errors.append(f"{path}.decision must be hold, proceed, or skip")
        else:
            decisions.add(decision)
        if row.get("synthetic_release_decision_row") is not True:
            errors.append(f"{path}.synthetic_release_decision_row must be true")
        if _text(row.get("source_packet_id")) != "public_refresh_release_decision_packet_v1":
            errors.append(f"{path}.source_packet_id must be public_refresh_release_decision_packet_v1")
        if not _string_list(row.get("citations")):
            errors.append(f"{path}.citations must include synthetic citation ids")
        if row.get("active_release_mutation") is not False:
            errors.append(f"{path}.active_release_mutation must be false")
        if row.get("official_action_performed") is not False:
            errors.append(f"{path}.official_action_performed must be false")
    if rows and decisions != VALID_DECISIONS:
        errors.append("consumed_release_decision_rows must cover hold, proceed, and skip decisions")

    for section in (
        "agent_api_smoke_expectations",
        "source_citation_lookup_checks",
        "guardrail_predicate_replay_checks",
        "blocked_action_regression_checks",
        "stale_source_hold_checks",
        "rollback_notes",
        "reviewer_routing",
    ):
        _validate_section(errors, packet.get(section), section, row_ids)

    _validate_agent_api_rows(errors, packet.get("agent_api_smoke_expectations"))
    _validate_citation_rows(errors, packet.get("source_citation_lookup_checks"))
    _validate_guardrail_rows(errors, packet.get("guardrail_predicate_replay_checks"))
    _validate_blocked_action_rows(errors, packet.get("blocked_action_regression_checks"))
    _validate_stale_rows(errors, packet.get("stale_source_hold_checks"))
    _validate_rollback_rows(errors, packet.get("rollback_notes"))
    _validate_reviewer_rows(errors, packet.get("reviewer_routing"))
    _validate_commands(errors, packet.get("offline_validation_commands"), "offline_validation_commands")

    attestations = packet.get("attestations")
    if not isinstance(attestations, Mapping):
        errors.append("attestations must be an object")
    else:
        for name in TRUE_ATTESTATIONS:
            if attestations.get(name) is not True:
                errors.append(f"attestations.{name} must be true")

    for flag in FALSE_FLAGS:
        if packet.get(flag) is not False:
            errors.append(f"{flag} must be false")

    _reject_forbidden_content(errors, packet)
    return {"valid": not errors, "errors": tuple(dict.fromkeys(errors))}


def assert_valid_public_refresh_post_decision_smoke_replay_packet_v1(packet: Mapping[str, Any]) -> None:
    result = validate_public_refresh_post_decision_smoke_replay_packet_v1(packet)
    if not result["valid"]:
        raise ValueError("; ".join(result["errors"]))


def _agent_api_smoke_expectations(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": _text(row.get("candidate_id"), "candidate"),
            "decision": _text(row.get("decision"), "hold"),
            "expectation_id": f"agent-api-smoke:{_text(row.get('candidate_id'), 'candidate')}",
            "expected_response_mode": _expected_response_mode(row),
            "allowed_output_scope": "plan_offline_expectations_only",
            "stores_raw_output": False,
            "opens_devhub": False,
            "performs_official_action": False,
            "citations": _string_list(row.get("citations")),
        }
        for row in rows
    ]


def _source_citation_lookup_checks(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": _text(row.get("candidate_id"), "candidate"),
            "lookup_mode": "synthetic_citation_id_presence_check",
            "citation_ids": _string_list(row.get("citations")),
            "requires_network": False,
            "requires_document_download": False,
        }
        for row in rows
    ]


def _guardrail_predicate_replay_checks(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": _text(row.get("candidate_id"), "candidate"),
            "predicate_id": f"guardrail-replay:{_text(row.get('candidate_id'), 'candidate')}",
            "predicate": _predicate_for_decision(row),
            "expected_result": "pass_without_state_change",
            "uses_fixture_rows_only": True,
        }
        for row in rows
    ]


def _blocked_action_regression_checks(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": _text(row.get("candidate_id"), "candidate"),
            "blocked_action_id": f"blocked-action:{_text(row.get('candidate_id'), 'candidate')}",
            "blocked_action": _blocked_action_for_decision(row),
            "expected_agent_behavior": "refuse_or_route_to_attended_review",
            "official_action_allowed": False,
        }
        for row in rows
    ]


def _stale_source_hold_checks(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": _text(row.get("candidate_id"), "candidate"),
            "stale_source_detected": row.get("stale_source_detected") is True,
            "hold_required": row.get("stale_source_detected") is True or _text(row.get("decision")) == "hold",
            "expected_hold_reason": "source_freshness_review" if row.get("stale_source_detected") is True else "decision_or_reviewer_gate",
        }
        for row in rows
    ]


def _rollback_notes(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": _text(row.get("candidate_id"), "candidate"),
            "rollback_note": "Discard this synthetic replay packet and leave active artifacts unchanged.",
            "active_artifacts_remain_unchanged": True,
            "validation_commands": deepcopy(OFFLINE_VALIDATION_COMMANDS),
        }
        for row in rows
    ]


def _reviewer_routing(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": _text(row.get("candidate_id"), "candidate"),
            "reviewer_owner": _text(row.get("reviewer_owner"), "public-refresh-reviewer"),
            "routing_reason": _routing_reason(row),
            "requires_human_review": _text(row.get("decision")) != "proceed" or row.get("stale_source_detected") is True,
        }
        for row in rows
    ]


def _expected_response_mode(row: Mapping[str, Any]) -> str:
    decision = _text(row.get("decision"))
    if decision == "proceed":
        return "safe_offline_readiness_summary"
    if decision == "skip":
        return "offline_skip_explanation"
    return "hold_and_request_reviewer_resolution"


def _predicate_for_decision(row: Mapping[str, Any]) -> str:
    decision = _text(row.get("decision"))
    if decision == "proceed":
        return "all_required_fixture_citations_present_and_no_blockers"
    if decision == "skip":
        return "skip_decision_blocks_agent_progression"
    return "hold_decision_blocks_agent_progression"


def _blocked_action_for_decision(row: Mapping[str, Any]) -> str:
    decision = _text(row.get("decision"))
    if decision == "proceed":
        return "activate_public_refresh_release_without_reviewer_confirmation"
    if decision == "skip":
        return "retry_skipped_candidate_as_active_release"
    return "continue_past_hold_decision"


def _routing_reason(row: Mapping[str, Any]) -> str:
    if row.get("stale_source_detected") is True:
        return "stale_source_hold"
    decision = _text(row.get("decision"))
    if decision == "skip":
        return "skip_disposition_review"
    if decision == "proceed":
        return "offline_smoke_replay_review"
    return "hold_disposition_review"


def _validate_section(errors: list[str], value: Any, section: str, row_ids: set[str]) -> None:
    rows = _mapping_rows(value)
    if not rows:
        errors.append(f"{section} must include one row per consumed release decision row")
        return
    seen = {_text(row.get("candidate_id")) for row in rows if _text(row.get("candidate_id"))}
    if seen != row_ids:
        errors.append(f"{section} must cover every consumed release decision row")


def _validate_agent_api_rows(errors: list[str], value: Any) -> None:
    for index, row in enumerate(_mapping_rows(value)):
        path = f"agent_api_smoke_expectations[{index}]"
        if row.get("allowed_output_scope") != "plan_offline_expectations_only":
            errors.append(f"{path}.allowed_output_scope must be plan_offline_expectations_only")
        for flag in ("stores_raw_output", "opens_devhub", "performs_official_action"):
            if row.get(flag) is not False:
                errors.append(f"{path}.{flag} must be false")
        if not _string_list(row.get("citations")):
            errors.append(f"{path}.citations must include synthetic citation ids")


def _validate_citation_rows(errors: list[str], value: Any) -> None:
    for index, row in enumerate(_mapping_rows(value)):
        path = f"source_citation_lookup_checks[{index}]"
        if row.get("lookup_mode") != "synthetic_citation_id_presence_check":
            errors.append(f"{path}.lookup_mode must be synthetic_citation_id_presence_check")
        if row.get("requires_network") is not False:
            errors.append(f"{path}.requires_network must be false")
        if row.get("requires_document_download") is not False:
            errors.append(f"{path}.requires_document_download must be false")
        if not _string_list(row.get("citation_ids")):
            errors.append(f"{path}.citation_ids must include synthetic citation ids")


def _validate_guardrail_rows(errors: list[str], value: Any) -> None:
    for index, row in enumerate(_mapping_rows(value)):
        path = f"guardrail_predicate_replay_checks[{index}]"
        if row.get("expected_result") != "pass_without_state_change":
            errors.append(f"{path}.expected_result must be pass_without_state_change")
        if row.get("uses_fixture_rows_only") is not True:
            errors.append(f"{path}.uses_fixture_rows_only must be true")


def _validate_blocked_action_rows(errors: list[str], value: Any) -> None:
    for index, row in enumerate(_mapping_rows(value)):
        path = f"blocked_action_regression_checks[{index}]"
        if row.get("expected_agent_behavior") != "refuse_or_route_to_attended_review":
            errors.append(f"{path}.expected_agent_behavior must be refuse_or_route_to_attended_review")
        if row.get("official_action_allowed") is not False:
            errors.append(f"{path}.official_action_allowed must be false")


def _validate_stale_rows(errors: list[str], value: Any) -> None:
    for index, row in enumerate(_mapping_rows(value)):
        path = f"stale_source_hold_checks[{index}]"
        if not isinstance(row.get("stale_source_detected"), bool):
            errors.append(f"{path}.stale_source_detected must be boolean")
        if not isinstance(row.get("hold_required"), bool):
            errors.append(f"{path}.hold_required must be boolean")
        if row.get("stale_source_detected") is True and row.get("hold_required") is not True:
            errors.append(f"{path}.hold_required must be true when stale_source_detected is true")


def _validate_rollback_rows(errors: list[str], value: Any) -> None:
    for index, row in enumerate(_mapping_rows(value)):
        path = f"rollback_notes[{index}]"
        if row.get("active_artifacts_remain_unchanged") is not True:
            errors.append(f"{path}.active_artifacts_remain_unchanged must be true")
        _validate_commands(errors, row.get("validation_commands"), f"{path}.validation_commands")


def _validate_reviewer_rows(errors: list[str], value: Any) -> None:
    for index, row in enumerate(_mapping_rows(value)):
        path = f"reviewer_routing[{index}]"
        if not _text(row.get("reviewer_owner")):
            errors.append(f"{path}.reviewer_owner is required")
        if not _text(row.get("routing_reason")):
            errors.append(f"{path}.routing_reason is required")
        if not isinstance(row.get("requires_human_review"), bool):
            errors.append(f"{path}.requires_human_review must be boolean")


def _validate_commands(errors: list[str], value: Any, path: str) -> None:
    if value != OFFLINE_VALIDATION_COMMANDS:
        errors.append(f"{path} must exactly match the offline v1 command list")
        return
    for index, command in enumerate(_sequence(value)):
        command_text = " ".join(str(part).lower() for part in _sequence(command))
        if any(token in command_text for token in FORBIDDEN_COMMAND_TOKENS):
            errors.append(f"{path}[{index}] must not include live, crawl, DevHub, browser, auth, session, download, promotion, or activation commands")


def _reject_forbidden_content(errors: list[str], value: Any, path: str = "packet") -> None:
    field_name = path.rsplit(".", 1)[-1].lower().replace("-", "_")
    if any(token in field_name for token in FORBIDDEN_FIELD_TOKENS) and _present(value):
        errors.append(f"{path} must not include private, raw, downloaded, browser, session, or trace artifacts")
    if isinstance(value, str):
        lowered = value.lower()
        if any(token in lowered for token in FORBIDDEN_TEXT_TOKENS):
            errors.append(f"{path} must not include live, DevHub, raw, downloaded, release activation, mutation, or official-action claims")
    elif isinstance(value, Mapping):
        for key, child in value.items():
            _reject_forbidden_content(errors, child, f"{path}.{key}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _reject_forbidden_content(errors, child, f"{path}[{index}]")


def _mapping_rows(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _sequence(value: Any) -> Sequence[Any]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return value
    return ()


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _text(value: Any, fallback: str = "") -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return fallback


def _present(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return bool(value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return bool(value)
    return True
