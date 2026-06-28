from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from ppd.devhub.attended_read_only_pilot_runbook import assert_valid_runbook_packet
from ppd.devhub.read_only_observation_redaction_review import assert_valid_read_only_observation_redaction_review_packet
from ppd.devhub.read_only_pilot_evidence_review import assert_read_only_pilot_evidence_packet
from ppd.devhub.surface_registry_reviewer_approval_packet import assert_valid_surface_registry_reviewer_approval_packet


REQUIRED_PACKET_ID = "devhub-attended-read-only-pilot-launch-readiness-v1"
REQUIRED_PACKET_TYPE = "ppd.devhub.attended_read_only_pilot_launch_readiness_packet.v1"
REQUIRED_MODE = "fixture_first_devhub_attended_read_only_pilot_launch_readiness"
REQUIRED_SOURCE_KEYS = (
    "devhub_attended_read_only_pilot_runbook",
    "devhub_surface_registry_reviewer_approval_packet",
    "devhub_read_only_pilot_evidence_review_packet",
    "devhub_observation_redaction_review_packet",
)
REQUIRED_SECTIONS = (
    "attendance_prerequisites",
    "manual_stop_points",
    "redaction_checklist_items",
    "selector_confidence_notes",
    "reviewer_owner_signoff_slots",
)
REQUIRED_ATTESTATIONS_TRUE = (
    "no_browser_execution",
    "no_auth_state_saved",
    "no_session_state_saved",
    "no_screenshots_saved",
    "no_traces_saved",
    "no_har_files_saved",
    "no_raw_authenticated_values_saved",
    "no_downloads_saved",
    "no_official_action_taken",
    "no_registry_mutation",
)
REQUIRED_FALSE_FLAGS = (
    "launches_browser",
    "launches_playwright",
    "uses_stored_auth_state",
    "stores_auth_state",
    "stores_session_state",
    "stores_screenshots",
    "stores_traces",
    "stores_har_files",
    "stores_raw_authenticated_values",
    "takes_official_action",
    "mutates_surface_registry",
)
FORBIDDEN_KEYS = {
    "auth_state",
    "auth_state_path",
    "browser_state",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "download_path",
    "downloaded_document",
    "har",
    "har_path",
    "password",
    "private_value",
    "raw_authenticated_value",
    "raw_authenticated_values",
    "raw_dom",
    "screenshot",
    "screenshot_path",
    "session_state",
    "storage_state",
    "storage_state_path",
    "trace",
    "trace_path",
}
PRIVATE_ARTIFACT_VALUE_RE = re.compile(
    r"(/home/|/users/|c:\\\\users\\\\|file://|~/|trace\\.zip|\\.har\\b|storage[_ -]?state\\.json|auth[_ -]?state\\.json|screenshot\\.(?:png|jpe?g|webp))",
    re.IGNORECASE,
)
LIVE_EXECUTION_RE = re.compile(
    r"\\b(launched|ran|executed|clicked|filled|captured|stored)\\b.{0,80}\\b(live browser|playwright|devhub session|auth state|screenshot|trace|har)\\b|"
    r"\\b(live browser|playwright|devhub session)\\b.{0,80}\\b(launched|ran|executed|clicked|filled|captured|stored)\\b",
    re.IGNORECASE,
)
AUTH_AUTOMATION_RE = re.compile(
    r"\\b(automated|bypassed|solved|handled by automation|completed by automation)\\b.{0,80}\\b(captcha|mfa|multi-factor|multifactor|account creation)\\b|"
    r"\\b(captcha|mfa|multi-factor|multifactor|account creation)\\b.{0,80}\\b(automated|bypassed|solved|handled by automation|completed by automation)\\b",
    re.IGNORECASE,
)
CONSEQUENTIAL_ACTION_TERMS = (
    "submit",
    "submission",
    "upload",
    "certify",
    "payment",
    "pay",
    "purchase",
    "schedule",
    "cancel",
    "withdraw",
    "reactivate",
    "extension",
)


def load_json_packet(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("packet fixture must be a JSON object")
    return data


def build_attended_read_only_pilot_launch_readiness_packet(
    runbook_packet: Mapping[str, Any],
    surface_registry_reviewer_approval_packet: Mapping[str, Any],
    pilot_evidence_review_packet: Mapping[str, Any],
    observation_redaction_review_packet: Mapping[str, Any],
) -> dict[str, Any]:
    """Build the fixture-first attended read-only launch readiness packet."""

    assert_valid_runbook_packet(runbook_packet)
    assert_valid_surface_registry_reviewer_approval_packet(surface_registry_reviewer_approval_packet)
    assert_read_only_pilot_evidence_packet(dict(pilot_evidence_review_packet))
    assert_valid_read_only_observation_redaction_review_packet(observation_redaction_review_packet)

    runbook_id = _text(runbook_packet.get("packet_id"))
    approval_id = _text(surface_registry_reviewer_approval_packet.get("packet_id"))
    evidence_id = _text(pilot_evidence_review_packet.get("packet_id"))
    redaction_id = _text(observation_redaction_review_packet.get("packet_id"))

    packet = {
        "packet_id": REQUIRED_PACKET_ID,
        "packet_type": REQUIRED_PACKET_TYPE,
        "mode": REQUIRED_MODE,
        "fixture_first": True,
        "offline_only": True,
        "read_only_only": True,
        "manual_attendance_required": True,
        "launches_browser": False,
        "launches_playwright": False,
        "uses_stored_auth_state": False,
        "stores_auth_state": False,
        "stores_session_state": False,
        "stores_screenshots": False,
        "stores_traces": False,
        "stores_har_files": False,
        "stores_raw_authenticated_values": False,
        "takes_official_action": False,
        "mutates_surface_registry": False,
        "source_packets": {
            "devhub_attended_read_only_pilot_runbook": {"packet_id": runbook_id, "consumed": True},
            "devhub_surface_registry_reviewer_approval_packet": {"packet_id": approval_id, "consumed": True},
            "devhub_read_only_pilot_evidence_review_packet": {"packet_id": evidence_id, "consumed": True},
            "devhub_observation_redaction_review_packet": {"packet_id": redaction_id, "consumed": True},
        },
        "attendance_prerequisites": _attendance_prerequisites(runbook_packet, runbook_id, evidence_id),
        "manual_stop_points": _manual_stop_points(runbook_packet, observation_redaction_review_packet, runbook_id, redaction_id),
        "redaction_checklist_items": _redaction_checklist_items(runbook_packet, observation_redaction_review_packet, runbook_id, redaction_id),
        "selector_confidence_notes": _selector_confidence_notes(pilot_evidence_review_packet, surface_registry_reviewer_approval_packet, evidence_id, approval_id),
        "reviewer_owner_signoff_slots": _reviewer_owner_signoff_slots(surface_registry_reviewer_approval_packet, observation_redaction_review_packet, approval_id, redaction_id),
        "launch_attestations": {name: True for name in REQUIRED_ATTESTATIONS_TRUE},
    }
    assert_valid_attended_read_only_pilot_launch_readiness_packet(packet)
    return packet


def validate_attended_read_only_pilot_launch_readiness_packet(packet: Mapping[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    if not isinstance(packet, Mapping):
        return ("packet must be a JSON object",)

    _require(errors, packet.get("packet_id") == REQUIRED_PACKET_ID, f"packet_id must be {REQUIRED_PACKET_ID}")
    _require(errors, packet.get("packet_type") == REQUIRED_PACKET_TYPE, f"packet_type must be {REQUIRED_PACKET_TYPE}")
    _require(errors, packet.get("mode") == REQUIRED_MODE, f"mode must be {REQUIRED_MODE}")
    for field in ("fixture_first", "offline_only", "read_only_only", "manual_attendance_required"):
        _require(errors, packet.get(field) is True, f"{field} must be true")
    for field in REQUIRED_FALSE_FLAGS:
        _require(errors, packet.get(field) is False, f"{field} must be false")

    sources = _mapping(packet.get("source_packets"))
    for key in REQUIRED_SOURCE_KEYS:
        source = _mapping(sources.get(key))
        _require(errors, bool(_text(source.get("packet_id"))), f"source_packets.{key}.packet_id is required")
        _require(errors, source.get("consumed") is True, f"source_packets.{key}.consumed must be true")

    for section in REQUIRED_SECTIONS:
        rows = _sequence(packet.get(section))
        _require(errors, bool(rows), f"{section} must be non-empty")
        for index, row in enumerate(rows):
            item = _mapping(row)
            _require(errors, bool(_sequence(item.get("citations"))), f"{section}[{index}].citations must be non-empty")

    for index, row in enumerate(_sequence(packet.get("attendance_prerequisites"))):
        item = _mapping(row)
        prefix = f"attendance_prerequisites[{index}]"
        _require(errors, item.get("required_before_launch") is True, f"{prefix}.required_before_launch must be true")
        _require(errors, item.get("operator_present") is True, f"{prefix}.operator_present must be true")
        _require(errors, item.get("agent_may_request_credentials") is False, f"{prefix}.agent_may_request_credentials must be false")
        _require(errors, item.get("browser_state_storage_allowed") is False, f"{prefix}.browser_state_storage_allowed must be false")

    for index, row in enumerate(_sequence(packet.get("manual_stop_points"))):
        item = _mapping(row)
        prefix = f"manual_stop_points[{index}]"
        _require(errors, _text(item.get("agent_action")) == "stop_and_record_commit_safe_refusal", f"{prefix}.agent_action must stop")
        _require(errors, item.get("official_action_allowed_after_stop") is False, f"{prefix}.official_action_allowed_after_stop must be false")

    for index, row in enumerate(_sequence(packet.get("redaction_checklist_items"))):
        item = _mapping(row)
        prefix = f"redaction_checklist_items[{index}]"
        _require(errors, item.get("required") is True, f"{prefix}.required must be true")
        _require(errors, item.get("private_value_allowed") is False, f"{prefix}.private_value_allowed must be false")
        _require(errors, item.get("raw_value_allowed") is False, f"{prefix}.raw_value_allowed must be false")

    for index, row in enumerate(_sequence(packet.get("selector_confidence_notes"))):
        item = _mapping(row)
        prefix = f"selector_confidence_notes[{index}]"
        _require(errors, bool(_text(item.get("surface_id")) or _text(item.get("selector"))), f"{prefix}.surface_id or selector is required")
        _require(errors, _text(item.get("launch_effect")) == "notes_only_no_registry_promotion", f"{prefix}.launch_effect must be notes_only_no_registry_promotion")

    for index, row in enumerate(_sequence(packet.get("reviewer_owner_signoff_slots"))):
        item = _mapping(row)
        prefix = f"reviewer_owner_signoff_slots[{index}]"
        _require(errors, bool(_text(item.get("owner"))), f"{prefix}.owner is required")
        _require(errors, _text(item.get("status")) == "pending", f"{prefix}.status must be pending")
        _require(errors, item.get("can_enable_official_action") is False, f"{prefix}.can_enable_official_action must be false")

    attestations = _mapping(packet.get("launch_attestations"))
    for name in REQUIRED_ATTESTATIONS_TRUE:
        _require(errors, attestations.get(name) is True, f"launch_attestations.{name} must be true")

    _scan_for_unsafe_content(errors, packet)
    _scan_for_enabled_consequential_controls(errors, packet)
    return _dedupe(errors)


def assert_valid_attended_read_only_pilot_launch_readiness_packet(packet: Mapping[str, Any]) -> None:
    errors = validate_attended_read_only_pilot_launch_readiness_packet(packet)
    if errors:
        raise AssertionError("; ".join(errors))


def _attendance_prerequisites(runbook: Mapping[str, Any], runbook_id: str, evidence_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for boundary in _sequence(runbook.get("manual_login_boundaries")):
        item = _mapping(boundary)
        rows.append(
            {
                "prerequisite_id": _text(item.get("boundary_id")) or "manual_login_boundary",
                "description": _text(item.get("prompt")) or "Operator attendance is required for manual DevHub login and security prompts.",
                "required_before_launch": True,
                "operator_present": item.get("human_operator_required") is True,
                "agent_may_request_credentials": False,
                "agent_may_store_credentials": False,
                "agent_may_automate_mfa_or_captcha": False,
                "account_creation_allowed": False,
                "browser_state_storage_allowed": False,
                "citations": _dedupe([runbook_id] + [_text(value) for value in _sequence(item.get("source_packet_ids"))]),
            }
        )
    rows.append(
        {
            "prerequisite_id": "pilot_evidence_review_available",
            "description": "Read-only pilot evidence review must be available before launch review starts.",
            "required_before_launch": True,
            "operator_present": True,
            "agent_may_request_credentials": False,
            "agent_may_store_credentials": False,
            "agent_may_automate_mfa_or_captcha": False,
            "account_creation_allowed": False,
            "browser_state_storage_allowed": False,
            "citations": [evidence_id],
        }
    )
    return rows


def _manual_stop_points(runbook: Mapping[str, Any], redaction: Mapping[str, Any], runbook_id: str, redaction_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, prompt in enumerate(_sequence(runbook.get("abort_prompts"))):
        rows.append(
            {
                "stop_id": f"runbook-abort-{index + 1}",
                "trigger": _text(prompt),
                "agent_action": "stop_and_record_commit_safe_refusal",
                "official_action_allowed_after_stop": False,
                "citations": [runbook_id],
            }
        )
    for index, prompt in enumerate(_sequence(redaction.get("abort_prompts"))):
        item = _mapping(prompt)
        rows.append(
            {
                "stop_id": _text(item.get("prompt_id")) or f"redaction-abort-{index + 1}",
                "trigger": _text(item.get("prompt")) or _text(prompt),
                "agent_action": "stop_and_record_commit_safe_refusal",
                "official_action_allowed_after_stop": False,
                "citations": _citations(item, redaction_id),
            }
        )
    return rows


def _redaction_checklist_items(runbook: Mapping[str, Any], redaction: Mapping[str, Any], runbook_id: str, redaction_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for check in _sequence(runbook.get("redaction_checks")):
        item = _mapping(check)
        rows.append(
            {
                "check_id": _text(item.get("check_id")),
                "required": item.get("required") is True,
                "raw_value_allowed": False,
                "private_value_allowed": False,
                "passes_when": _text(item.get("passes_when")),
                "citations": _dedupe([runbook_id] + [_text(value) for value in _sequence(item.get("source_packet_ids"))]),
            }
        )
    for prohibition in _sequence(redaction.get("private_artifact_prohibitions")):
        item = _mapping(prohibition)
        check_id = _slug(_text(item.get("prohibition"))) or "redaction-prohibition"
        rows.append(
            {
                "check_id": f"redaction-review-{check_id}",
                "required": True,
                "raw_value_allowed": False,
                "private_value_allowed": False,
                "passes_when": _text(item.get("review_rule")) or _text(item.get("prohibition")),
                "citations": _citations(item, redaction_id),
            }
        )
    return rows


def _selector_confidence_notes(evidence: Mapping[str, Any], approval: Mapping[str, Any], evidence_id: str, approval_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for note in _sequence(evidence.get("selector_confidence_notes")):
        item = _mapping(note)
        rows.append(
            {
                "note_id": _text(item.get("note_id")) or f"evidence-selector-{len(rows) + 1}",
                "surface_id": _text(item.get("surface_id")),
                "selector": _text(item.get("selector")),
                "confidence": _text(item.get("confidence")),
                "rationale": _text(item.get("rationale")),
                "launch_effect": "notes_only_no_registry_promotion",
                "citations": _citations(item, evidence_id),
            }
        )
    for approval_item in _sequence(approval.get("selector_delta_approval_items")):
        item = _mapping(approval_item)
        rows.append(
            {
                "note_id": _text(item.get("selector_delta_id")) or f"approval-selector-{len(rows) + 1}",
                "surface_id": _text(item.get("surface_id")),
                "selector": _text(item.get("candidate_selector_confidence")),
                "confidence": _text(item.get("candidate_selector_confidence")) or "pending_reviewer_approval",
                "rationale": "Reviewer approval packet keeps selector deltas pending and does not promote registry state.",
                "launch_effect": "notes_only_no_registry_promotion",
                "citations": _citations(item, approval_id),
            }
        )
    return rows


def _reviewer_owner_signoff_slots(approval: Mapping[str, Any], redaction: Mapping[str, Any], approval_id: str, redaction_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for slot in _sequence(approval.get("reviewer_signoff_slots")):
        item = _mapping(slot)
        owner = _text(item.get("owner"))
        if owner and owner not in seen:
            seen.add(owner)
            rows.append(
                {
                    "slot_id": f"approval-{_slug(owner)}",
                    "owner": owner,
                    "status": "pending",
                    "decision": "",
                    "signed_at": "",
                    "can_enable_official_action": False,
                    "citations": _citations(item, approval_id),
                }
            )
    for owner_row in _sequence(redaction.get("reviewer_owners")):
        item = _mapping(owner_row)
        owner = _text(item.get("owner_id")) or _text(item.get("owner"))
        if owner and owner not in seen:
            seen.add(owner)
            rows.append(
                {
                    "slot_id": f"redaction-{_slug(owner)}",
                    "owner": owner,
                    "status": "pending",
                    "decision": "",
                    "signed_at": "",
                    "can_enable_official_action": False,
                    "citations": _citations(item, redaction_id),
                }
            )
    return rows


def _scan_for_unsafe_content(errors: list[str], value: Any, path: str = "$", parent_key: str = "") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = _text(key)
            child_path = f"{path}.{key_text}"
            if key_text.lower() in FORBIDDEN_KEYS:
                errors.append(f"{child_path} must not contain private DevHub artifact keys")
            _scan_for_unsafe_content(errors, child, child_path, key_text)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _scan_for_unsafe_content(errors, child, f"{path}[{index}]", parent_key)
        return
    if isinstance(value, str):
        if PRIVATE_ARTIFACT_VALUE_RE.search(value):
            errors.append(f"{path} must not contain private artifact paths or filenames")
        if LIVE_EXECUTION_RE.search(value):
            errors.append(f"{path} must not claim live browser execution or artifact capture")
        if AUTH_AUTOMATION_RE.search(value):
            errors.append(f"{path} must not claim CAPTCHA, MFA, or account-creation automation")


def _scan_for_enabled_consequential_controls(errors: list[str], packet: Mapping[str, Any]) -> None:
    controls = packet.get("controls", [])
    if isinstance(controls, Mapping):
        controls = [{"control_id": key, "enabled": value} for key, value in controls.items()]
    if not isinstance(controls, Sequence) or isinstance(controls, (str, bytes, bytearray)):
        return
    for index, control in enumerate(controls):
        item = _mapping(control)
        enabled = item.get("enabled") is True or item.get("state") == "enabled" or item.get("allowed") is True
        label = " ".join(_text(item.get(key)) for key in ("control_id", "name", "label", "action")).lower()
        if enabled and any(term in label for term in CONSEQUENTIAL_ACTION_TERMS):
            errors.append(f"controls[{index}] must not enable consequential DevHub controls")


def _citations(item: Mapping[str, Any], fallback: str) -> list[str]:
    raw = item.get("citations", item.get("source_packet_ids", []))
    citations = [_text(value) for value in _sequence(raw)]
    return _dedupe([fallback] + citations)


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: Any) -> Sequence[Any]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return value
    return ()


def _text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def _dedupe(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = _text(value)
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result
