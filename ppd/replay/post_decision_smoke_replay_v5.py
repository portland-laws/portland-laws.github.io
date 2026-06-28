"""Fixture-first PP&D post-decision smoke replay v5.

This module consumes only committed release decision packet v5 fixtures and
inactive guardrail placeholder fixtures. It does not activate guardrails, open
DevHub, read private documents, upload, submit, certify, pay, schedule, or make
legal/permitting guarantees.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

REPLAY_VERSION = "post_decision_smoke_replay_v5"
DECISION_PACKET_VERSION = "release_decision_packet_v5"
PLACEHOLDER_FIXTURE_VERSION = "inactive_guardrail_placeholder_fixture_v5"
EXPECTED_OFFLINE_VALIDATION_COMMANDS = [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]]

PROHIBITED_TRUE_FLAGS = {
    "activate_guardrails",
    "guardrails_activated",
    "open_devhub",
    "opened_devhub",
    "read_private_documents",
    "upload",
    "uploaded",
    "submit",
    "submitted",
    "certify",
    "certified",
    "pay",
    "paid",
    "schedule",
    "scheduled",
    "legal_or_permitting_guarantee",
}

PROHIBITED_KEYS = {
    "auth_state",
    "browser_state",
    "cookie",
    "cookies",
    "credentials",
    "devhub_session",
    "downloaded_document",
    "har",
    "password",
    "payment_details",
    "private_document",
    "raw_crawl_output",
    "screenshot",
    "session_token",
    "trace",
    "upload_file",
}

PROHIBITED_TEXT = (
    "activated guardrail",
    "certified the application",
    "guarantee approval",
    "guarantee permit",
    "legal advice",
    "opened devhub",
    "paid the fee",
    "permit is guaranteed",
    "submitted the application",
    "uploaded to the official record",
)


@dataclass(frozen=True)
class ReplayFinding:
    check: str
    ok: bool
    detail: str

    def as_dict(self) -> dict[str, Any]:
        return {"check": self.check, "ok": self.ok, "detail": self.detail}


def load_json_fixture(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"fixture must contain a JSON object: {path}")
    return value


def replay_from_fixture_paths(decision_packet_path: Path, placeholder_fixture_path: Path) -> dict[str, Any]:
    return replay_post_decision_smoke_v5(
        load_json_fixture(decision_packet_path),
        load_json_fixture(placeholder_fixture_path),
    )


def replay_post_decision_smoke_v5(
    decision_packet: Mapping[str, Any], placeholder_fixture: Mapping[str, Any]
) -> dict[str, Any]:
    _reject_prohibited_content(decision_packet, "decision_packet")
    _reject_prohibited_content(placeholder_fixture, "placeholder_fixture")

    findings = [
        _check_packet_versions(decision_packet, placeholder_fixture),
        _check_fixture_scope(decision_packet, placeholder_fixture),
        _check_go_no_go(decision_packet),
        _check_unresolved_holds(decision_packet, placeholder_fixture),
        _check_source_freshness_caveats(decision_packet),
        _check_agent_api_notes(decision_packet),
        _check_rollback_owner_placeholders(decision_packet),
        _check_manual_handoff_reminders(decision_packet),
        _check_agent_notification_rows(decision_packet),
        _check_exact_offline_validation_commands(decision_packet),
    ]

    return {
        "version": REPLAY_VERSION,
        "ok": all(finding.ok for finding in findings),
        "fixture_inputs": {
            "decision_packet_version": decision_packet.get("version"),
            "placeholder_fixture_version": placeholder_fixture.get("version"),
        },
        "go_no_go_outcome": decision_packet.get("go_no_go"),
        "unresolved_holds": list(decision_packet.get("unresolved_holds", [])),
        "source_freshness_caveats": list(decision_packet.get("source_freshness_caveats", [])),
        "agent_api_compatibility_notes": list(decision_packet.get("agent_api_compatibility_notes", [])),
        "rollback_owner_placeholders": list(decision_packet.get("rollback_owner_placeholders", [])),
        "manual_handoff_reminders": list(decision_packet.get("manual_handoff_reminders", [])),
        "post_decision_agent_notification_rows": list(decision_packet.get("post_decision_agent_notification_rows", [])),
        "offline_validation_commands": list(decision_packet.get("offline_validation_commands", [])),
        "side_effects": {
            "activated_guardrails": False,
            "opened_devhub": False,
            "read_private_documents": False,
            "uploaded": False,
            "submitted": False,
            "certified": False,
            "paid": False,
            "scheduled": False,
            "legal_or_permitting_guarantee": False,
        },
        "findings": [finding.as_dict() for finding in findings],
    }


def _check_packet_versions(packet: Mapping[str, Any], placeholders: Mapping[str, Any]) -> ReplayFinding:
    ok = packet.get("version") == DECISION_PACKET_VERSION and placeholders.get("version") == PLACEHOLDER_FIXTURE_VERSION
    return ReplayFinding(
        "fixture_versions",
        ok,
        f"decision={packet.get('version')!r}; placeholders={placeholders.get('version')!r}",
    )


def _check_fixture_scope(packet: Mapping[str, Any], placeholders: Mapping[str, Any]) -> ReplayFinding:
    decision_scope = packet.get("fixture_scope") == "release_decision_packet_only"
    placeholder_scope = placeholders.get("fixture_scope") == "inactive_guardrail_placeholders_only"
    return ReplayFinding("fixture_only_inputs", decision_scope and placeholder_scope, f"decision_scope={decision_scope}; placeholder_scope={placeholder_scope}")


def _check_go_no_go(packet: Mapping[str, Any]) -> ReplayFinding:
    value = packet.get("go_no_go")
    ok = isinstance(value, Mapping) and value.get("outcome") in {"go", "no_go", "hold"} and value.get("activation_allowed") is False
    return ReplayFinding("go_no_go_outcome_handling", ok, repr(value))


def _check_unresolved_holds(packet: Mapping[str, Any], placeholders: Mapping[str, Any]) -> ReplayFinding:
    holds = packet.get("unresolved_holds")
    rows = placeholders.get("placeholder_rows")
    if not isinstance(holds, list) or not holds or not isinstance(rows, list) or not rows:
        return ReplayFinding("unresolved_hold_propagation", False, "missing holds or placeholder rows")
    row_ids = {row.get("placeholder_id") for row in rows if isinstance(row, Mapping)}
    propagated = [hold for hold in holds if isinstance(hold, Mapping) and hold.get("placeholder_id") in row_ids and hold.get("status") == "unresolved"]
    return ReplayFinding("unresolved_hold_propagation", len(propagated) == len(holds), f"propagated={len(propagated)}; holds={len(holds)}")


def _check_source_freshness_caveats(packet: Mapping[str, Any]) -> ReplayFinding:
    caveats = packet.get("source_freshness_caveats")
    ok = isinstance(caveats, list) and bool(caveats) and all(
        isinstance(item, Mapping) and item.get("display_to_agent") is True and item.get("blocks_activation") is True
        for item in caveats
    )
    return ReplayFinding("source_freshness_caveat_display", ok, repr(caveats))


def _check_agent_api_notes(packet: Mapping[str, Any]) -> ReplayFinding:
    notes = packet.get("agent_api_compatibility_notes")
    ok = isinstance(notes, list) and bool(notes) and all(
        isinstance(item, Mapping) and item.get("compatible") in {True, "with_holds"} and item.get("activates_guardrails") is False
        for item in notes
    )
    return ReplayFinding("agent_api_compatibility_notes", ok, repr(notes))


def _check_rollback_owner_placeholders(packet: Mapping[str, Any]) -> ReplayFinding:
    rows = packet.get("rollback_owner_placeholders")
    ok = isinstance(rows, list) and bool(rows) and all(
        isinstance(item, Mapping) and item.get("owner_placeholder") and item.get("assignment_status") == "pending_manual_assignment"
        for item in rows
    )
    return ReplayFinding("rollback_owner_placeholders", ok, repr(rows))


def _check_manual_handoff_reminders(packet: Mapping[str, Any]) -> ReplayFinding:
    reminders = packet.get("manual_handoff_reminders")
    required_terms = ("upload", "submit", "certify", "pay", "schedule")
    text = " ".join(item for item in reminders if isinstance(item, str)).lower() if isinstance(reminders, list) else ""
    ok = isinstance(reminders, list) and bool(reminders) and all(term in text for term in required_terms)
    return ReplayFinding("manual_handoff_reminders", ok, text)


def _check_agent_notification_rows(packet: Mapping[str, Any]) -> ReplayFinding:
    rows = packet.get("post_decision_agent_notification_rows")
    ok = isinstance(rows, list) and bool(rows) and all(
        isinstance(item, Mapping)
        and item.get("notification_status") == "draft_row_only"
        and item.get("sent") is False
        and item.get("includes_go_no_go") is True
        and item.get("includes_unresolved_holds") is True
        for item in rows
    )
    return ReplayFinding("post_decision_agent_notification_rows", ok, repr(rows))


def _check_exact_offline_validation_commands(packet: Mapping[str, Any]) -> ReplayFinding:
    commands = packet.get("offline_validation_commands")
    return ReplayFinding("exact_offline_validation_commands_only", commands == EXPECTED_OFFLINE_VALIDATION_COMMANDS, repr(commands))


def _reject_prohibited_content(value: Any, path: str) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized_key = key_text.lower().replace("-", "_")
            child_path = f"{path}.{key_text}"
            if normalized_key in PROHIBITED_KEYS and _present(child):
                raise ValueError(f"prohibited private or session artifact at {child_path}")
            if normalized_key in PROHIBITED_TRUE_FLAGS and child is True:
                raise ValueError(f"prohibited side effect flag at {child_path}")
            _reject_prohibited_content(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_prohibited_content(child, f"{path}[{index}]")
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in PROHIBITED_TEXT):
            raise ValueError(f"prohibited side effect or guarantee text at {path}")


def _present(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, dict, set, frozenset)):
        return bool(value)
    return True
