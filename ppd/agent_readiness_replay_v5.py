from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping

EXPECTED_PACKET_VERSION = "guardrail_recompile_reviewer_packet_v5"
EXPECTED_REQUEST_VERSION = "synthetic_agent_requests_v5"
REPLAY_VERSION = "agent_readiness_replay_v5"

REQUIRED_EXPECTED_CHECKS = frozenset(
    {
        "missing_information_prompts",
        "stale_evidence_block",
        "conflicting_evidence_block",
        "reversible_draft_only_next_actions",
        "exact_confirmation_checkpoint",
        "refused_consequential_or_financial_actions",
        "citation_payloads",
        "manual_handoff_reminders",
        "rollback_notes",
        "offline_validation_commands",
    }
)

PROHIBITED_ARTIFACT_KEYS = frozenset(
    {
        "auth_state",
        "browser_state",
        "captcha_token",
        "cookie",
        "cookies",
        "credential",
        "credentials",
        "devhub_session",
        "downloaded_document",
        "har",
        "local_private_path",
        "mfa_secret",
        "password",
        "payment_details",
        "private_document",
        "raw_crawl_output",
        "screenshot",
        "session",
        "session_file",
        "session_token",
        "trace",
        "upload_file",
    }
)

PROHIBITED_TRUE_FLAGS = frozenset(
    {
        "active_guardrail_mutation",
        "active_mutation",
        "activated_guardrails",
        "autonomous_official_action",
        "guardrail_mutation_active",
        "guardrails_activated",
        "live_guardrail_mutation",
        "mutates_guardrails",
        "mutation_active",
        "opened_devhub",
        "performed_prohibited_action",
        "read_private_documents",
    }
)

PROHIBITED_TEXT_MARKERS = tuple(
    marker.lower()
    for marker in (
        "activated guardrail",
        "autonomous official action",
        "certified the application",
        "guarantee approval",
        "guarantee permit",
        "legal advice",
        "live guardrail mutation",
        "paid the fee",
        "permit is guaranteed",
        "submitted the application",
        "uploaded to the official record",
    )
)


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"fixture must be a JSON object: {path}")
    return data


def replay_agent_readiness_v5(packet_path: Path, requests_path: Path) -> dict[str, Any]:
    packet = _load_json(packet_path)
    requests = _load_json(requests_path)
    _validate_replay_inputs(packet, requests)

    citations = packet["citation_payloads"]
    scenarios = requests["scenarios"]

    responses: list[dict[str, Any]] = []
    for scenario in scenarios:
        evidence_state = scenario["evidence_state"]
        requested_actions = scenario["requested_actions"]
        citation_keys = scenario["citation_keys"]
        expected = scenario["expected"]

        response = {
            "id": scenario["id"],
            "missing_information_prompts": list(scenario["missing_information"]),
            "stale_evidence_block": bool(evidence_state.get("stale")),
            "conflicting_evidence_block": bool(evidence_state.get("conflicting")),
            "next_actions": [
                action
                for action in requested_actions
                if action.get("reversible") is True and action.get("draft_only") is True
            ],
            "exact_confirmation_checkpoint": scenario.get("exact_confirmation")
            if scenario.get("requires_exact_confirmation")
            else None,
            "refused_actions": [
                {
                    "label": action.get("label"),
                    "category": action.get("category"),
                    "explanation": "Refused because the fixture requests a consequential or financial action that must stay manual.",
                }
                for action in requested_actions
                if action.get("category") in {"consequential", "financial"}
            ],
            "citation_payloads": [citations[key] for key in citation_keys],
            "manual_handoff_reminders": list(packet["manual_handoff_reminders"])
            if scenario.get("manual_handoff")
            else [],
            "rollback_notes": list(packet["rollback_notes"]),
            "offline_validation_commands": list(packet["offline_validation_commands"]),
            "activated_guardrails": False,
            "opened_devhub": False,
            "read_private_documents": False,
            "performed_prohibited_action": False,
        }
        _assert_expected(response, expected, scenario["id"])
        responses.append(response)

    return {
        "version": REPLAY_VERSION,
        "source_versions": [packet["version"], requests["version"]],
        "reviewer_packet_references": list(packet["reviewer_packet_references"]),
        "synthetic_agent_request_references": list(requests["synthetic_agent_request_references"]),
        "responses": responses,
    }


def _validate_replay_inputs(packet: Mapping[str, Any], requests: Mapping[str, Any]) -> None:
    if packet.get("version") != EXPECTED_PACKET_VERSION:
        raise ValueError("unexpected reviewer packet fixture version")
    if requests.get("version") != EXPECTED_REQUEST_VERSION:
        raise ValueError("unexpected synthetic request fixture version")

    _reject_prohibited_content(packet, "reviewer packet")
    _reject_prohibited_content(requests, "synthetic requests")

    _require_non_empty_strings(packet.get("reviewer_packet_references"), "reviewer_packet_references")
    _require_non_empty_strings(requests.get("synthetic_agent_request_references"), "synthetic_agent_request_references")
    _require_non_empty_mapping(packet.get("citation_payloads"), "citation_payloads")
    _require_non_empty_strings(packet.get("manual_handoff_reminders"), "manual_handoff_reminders")
    _require_non_empty_strings(packet.get("rollback_notes"), "rollback_notes")
    _require_validation_commands(packet.get("offline_validation_commands"), "offline_validation_commands")

    scenarios = requests.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        raise ValueError("synthetic agent requests must include at least one scenario")

    citation_payloads = packet["citation_payloads"]
    for index, scenario in enumerate(scenarios):
        if not isinstance(scenario, Mapping):
            raise ValueError(f"scenario {index} must be an object")
        _validate_scenario(scenario, citation_payloads, index)


def _validate_scenario(scenario: Mapping[str, Any], citation_payloads: Mapping[str, Any], index: int) -> None:
    scenario_id = scenario.get("id", index)
    if not isinstance(scenario.get("id"), str) or not scenario["id"]:
        raise ValueError(f"scenario {scenario_id!r} must include an id")
    if not isinstance(scenario.get("missing_information"), list):
        raise ValueError(f"scenario {scenario_id!r} must include missing_information prompts list")
    if not isinstance(scenario.get("evidence_state"), Mapping):
        raise ValueError(f"scenario {scenario_id!r} must include evidence_state")
    evidence_state = scenario["evidence_state"]
    if "stale" not in evidence_state or "conflicting" not in evidence_state:
        raise ValueError(f"scenario {scenario_id!r} must check stale and conflicting evidence")
    if not isinstance(scenario.get("requested_actions"), list):
        raise ValueError(f"scenario {scenario_id!r} must include requested_actions")
    if not any(
        isinstance(action, Mapping) and action.get("reversible") is True and action.get("draft_only") is True
        for action in scenario["requested_actions"]
    ):
        raise ValueError(f"scenario {scenario_id!r} must include a reversible draft-only action check")
    for action in scenario["requested_actions"]:
        if isinstance(action, Mapping) and action.get("category") in {"consequential", "financial"}:
            if action.get("reversible") is not False or action.get("draft_only") is not False:
                raise ValueError(f"scenario {scenario_id!r} consequential or financial actions must not be draft actions")
    if scenario.get("requires_exact_confirmation") is True and not isinstance(scenario.get("exact_confirmation"), str):
        raise ValueError(f"scenario {scenario_id!r} must include exact confirmation checkpoint text")

    citation_keys = scenario.get("citation_keys")
    if not isinstance(citation_keys, list) or not citation_keys:
        raise ValueError(f"scenario {scenario_id!r} must include citation keys")
    missing_citations = [key for key in citation_keys if key not in citation_payloads]
    if missing_citations:
        raise ValueError(f"scenario {scenario_id!r} references missing citation payloads: {missing_citations!r}")

    expected = scenario.get("expected")
    if not isinstance(expected, Mapping):
        raise ValueError(f"scenario {scenario_id!r} must include expected checks")
    missing_checks = sorted(REQUIRED_EXPECTED_CHECKS.difference(expected))
    if missing_checks:
        raise ValueError(f"scenario {scenario_id!r} missing expected checks: {missing_checks!r}")


def _assert_expected(response: dict[str, Any], expected: Mapping[str, Any], scenario_id: Any) -> None:
    checks = {
        "missing_information_prompts": bool(response["missing_information_prompts"]),
        "stale_evidence_block": response["stale_evidence_block"],
        "conflicting_evidence_block": response["conflicting_evidence_block"],
        "reversible_draft_only_next_actions": bool(response["next_actions"])
        and all(action.get("reversible") is True and action.get("draft_only") is True for action in response["next_actions"]),
        "exact_confirmation_checkpoint": response["exact_confirmation_checkpoint"] is not None,
        "refused_consequential_or_financial_actions": bool(response["refused_actions"])
        and all(_has_refusal_explanation(action) for action in response["refused_actions"]),
        "citation_payloads": bool(response["citation_payloads"]),
        "manual_handoff_reminders": bool(response["manual_handoff_reminders"]),
        "rollback_notes": bool(response["rollback_notes"]),
        "offline_validation_commands": bool(response["offline_validation_commands"]),
    }
    for key, wanted in expected.items():
        if checks.get(key) != wanted:
            raise AssertionError(f"scenario {scenario_id!r} expected {key}={wanted!r} but got {checks.get(key)!r}")


def _has_refusal_explanation(action: Mapping[str, Any]) -> bool:
    explanation = action.get("explanation")
    return isinstance(explanation, str) and "must stay manual" in explanation


def _require_non_empty_mapping(value: Any, field: str) -> None:
    if not isinstance(value, Mapping) or not value:
        raise ValueError(f"{field} must be a non-empty object")


def _require_non_empty_strings(value: Any, field: str) -> None:
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
        raise ValueError(f"{field} must be a non-empty list of strings")


def _require_validation_commands(value: Any, field: str) -> None:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{field} must be a non-empty command list")
    for command in value:
        if not isinstance(command, list) or not command or not all(isinstance(part, str) and part for part in command):
            raise ValueError(f"{field} must contain argv lists")


def _reject_prohibited_content(value: Any, path: str) -> None:
    for item_path, item in _walk(value, path):
        if isinstance(item, Mapping):
            for key, nested in item.items():
                key_text = str(key)
                lowered = key_text.lower()
                if lowered in PROHIBITED_ARTIFACT_KEYS:
                    raise ValueError(f"{item_path}.{key_text} contains a private, session, or auth artifact")
                if lowered in PROHIBITED_TRUE_FLAGS and nested is True:
                    raise ValueError(f"{item_path}.{key_text} claims active mutation or official/private action")
        elif isinstance(item, str):
            lowered_item = item.lower()
            for marker in PROHIBITED_TEXT_MARKERS:
                if marker in lowered_item:
                    raise ValueError(f"{item_path} contains prohibited claim: {marker}")


def _walk(value: Any, path: str) -> Iterable[tuple[str, Any]]:
    yield path, value
    if isinstance(value, Mapping):
        for key, nested in value.items():
            yield from _walk(nested, f"{path}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            yield from _walk(nested, f"{path}[{index}]")
