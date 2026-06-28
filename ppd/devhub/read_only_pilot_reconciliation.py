from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


REQUIRED_PACKET_TYPE = "ppd.devhub.read_only_pilot_post_observation_reconciliation.v1"
REQUIRED_MODE = "fixture_first_devhub_read_only_pilot_post_observation_reconciliation"

FORBIDDEN_KEYS = {
    "auth_state",
    "auth_state_path",
    "browser_context",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "field_value",
    "har",
    "har_path",
    "local_private_file_path",
    "password",
    "private_value",
    "raw_authenticated_text",
    "raw_dom",
    "screenshot",
    "screenshot_path",
    "session_state",
    "storage_state",
    "storage_state_path",
    "trace",
    "trace_path",
}
FORBIDDEN_TEXT_PATTERNS = (
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    re.compile(r"\b\d{3}[-. ]\d{3}[-. ]\d{4}\b"),
    re.compile(r"/(?:home|Users|tmp|var/tmp)/"),
    re.compile(r"\b(?:auth_state\.json|storage_state\.json|trace\.zip)\b", re.IGNORECASE),
    re.compile(r"\.har\b", re.IGNORECASE),
)
CONSEQUENTIAL_TERMS = (
    "upload",
    "submit",
    "certify",
    "payment",
    "pay",
    "purchase",
    "schedule",
    "cancel",
    "withdraw",
    "extension",
    "reactivate",
)
TRUE_ENABLEMENT_KEYS = {"enabled", "allowed", "completed", "performed", "executed", "official_action_completed"}
NO_MUTATION_ATTESTATIONS = (
    "no_active_surface_registry_read_or_write",
    "no_active_surface_registry_mutation",
    "no_active_surface_map_replacement",
    "no_selector_confidence_promotion",
    "no_agent_state_read_or_write",
    "no_agent_state_mutation",
    "no_devhub_browser_launch",
    "no_auth_state_or_browser_artifact_storage",
)


@dataclass(frozen=True)
class ReconciliationValidationResult:
    packet_id: str
    ok: bool
    errors: tuple[str, ...]


class ReconciliationPacketError(ValueError):
    """Raised when a read-only pilot reconciliation packet is not commit-safe."""


def load_json_packet(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ReconciliationPacketError("packet fixture must be a JSON object")
    return data


def load_reconciliation_packet(path: str | Path) -> dict[str, Any]:
    return load_json_packet(path)


def build_post_observation_reconciliation_packet(
    operator_transcript_packet: Mapping[str, Any],
    surface_registry_reviewer_approval_packet: Mapping[str, Any],
    observation_redaction_review_packet: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a reconciliation packet from committed, already-redacted fixtures only."""

    _assert_source_packet(operator_transcript_packet, "operator transcript")
    _assert_source_packet(surface_registry_reviewer_approval_packet, "surface registry reviewer approval")
    _assert_source_packet(observation_redaction_review_packet, "observation redaction review")

    transcript_id = _text(operator_transcript_packet.get("packet_id"))
    approval_id = _text(surface_registry_reviewer_approval_packet.get("packet_id"))
    redaction_id = _text(observation_redaction_review_packet.get("packet_id"))

    packet = {
        "packet_id": "devhub-read-only-pilot-post-observation-reconciliation-synthetic-v1",
        "packet_type": REQUIRED_PACKET_TYPE,
        "mode": REQUIRED_MODE,
        "fixture_first": True,
        "offline_only": True,
        "read_only_only": True,
        "launches_devhub": False,
        "launches_playwright": False,
        "stores_private_values": False,
        "stores_browser_artifacts": False,
        "writes_surface_registry": False,
        "mutates_active_surface_registry": False,
        "mutates_agent_state": False,
        "source_packets": {
            "operator_transcript": {
                "packet_id": transcript_id,
                "packet_type": _text(operator_transcript_packet.get("packet_type")),
                "consumed": True,
            },
            "surface_registry_reviewer_approval": {
                "packet_id": approval_id,
                "packet_type": _text(surface_registry_reviewer_approval_packet.get("packet_type")),
                "consumed": True,
            },
            "observation_redaction_review": {
                "packet_id": redaction_id,
                "packet_type": _text(observation_redaction_review_packet.get("packet_type")),
                "consumed": True,
            },
        },
        "observed_surface_deltas": _observed_surface_deltas(operator_transcript_packet, surface_registry_reviewer_approval_packet, transcript_id, approval_id),
        "kept_decisions": _kept_decisions(surface_registry_reviewer_approval_packet, approval_id),
        "manual_handoff_decisions": _manual_handoff_decisions(surface_registry_reviewer_approval_packet, operator_transcript_packet, approval_id, transcript_id),
        "redaction_follow_ups": _redaction_follow_ups(observation_redaction_review_packet, redaction_id),
        "reviewer_owner_fields": _reviewer_owner_fields(operator_transcript_packet, surface_registry_reviewer_approval_packet, observation_redaction_review_packet, transcript_id, approval_id, redaction_id),
        "no_active_surface_registry_no_agent_state_mutation_attestations": {name: True for name in NO_MUTATION_ATTESTATIONS},
    }
    assert_valid_reconciliation_packet(packet)
    return packet


def assert_valid_reconciliation_packet(packet: Mapping[str, Any], *unused_source_packets: Mapping[str, Any]) -> None:
    result = validate_reconciliation_packet(packet, *unused_source_packets)
    if not result.ok:
        raise AssertionError("; ".join(result.errors))


def validate_reconciliation_packet(packet: Mapping[str, Any], *unused_source_packets: Mapping[str, Any]) -> ReconciliationValidationResult:
    errors: list[str] = []
    if not isinstance(packet, Mapping):
        return ReconciliationValidationResult(packet_id="", ok=False, errors=("packet must be a JSON object",))

    packet_id = _text(packet.get("packet_id"))
    _require(errors, packet.get("packet_type") == REQUIRED_PACKET_TYPE, f"packet_type must be {REQUIRED_PACKET_TYPE}")
    _require(errors, packet.get("mode") == REQUIRED_MODE, f"mode must be {REQUIRED_MODE}")
    for field in ("fixture_first", "offline_only", "read_only_only"):
        _require(errors, packet.get(field) is True, f"{field} must be true")
    for field in (
        "launches_devhub",
        "launches_playwright",
        "stores_private_values",
        "stores_browser_artifacts",
        "writes_surface_registry",
        "mutates_active_surface_registry",
        "mutates_agent_state",
    ):
        _require(errors, packet.get(field) is False, f"{field} must be false")

    _validate_source_packets(errors, packet.get("source_packets"))
    _validate_cited_rows(errors, packet.get("observed_surface_deltas"), "observed_surface_deltas", ("delta_id", "surface_id", "decision"))
    _validate_cited_rows(errors, packet.get("kept_decisions"), "kept_decisions", ("decision_id", "surface_id", "reason"))
    _validate_cited_rows(errors, packet.get("manual_handoff_decisions"), "manual_handoff_decisions", ("handoff_id", "surface_id", "reason"))
    _validate_cited_rows(errors, packet.get("redaction_follow_ups"), "redaction_follow_ups", ("follow_up_id", "owner", "action"))
    _validate_reviewer_owner_fields(errors, packet.get("reviewer_owner_fields"))
    _validate_attestations(errors, packet.get("no_active_surface_registry_no_agent_state_mutation_attestations"))
    _scan_for_forbidden_content(errors, packet, "packet")
    _scan_for_enabled_consequential_controls(errors, packet, "packet")

    return ReconciliationValidationResult(packet_id=packet_id, ok=not errors, errors=tuple(_dedupe(errors)))


def _assert_source_packet(packet: Mapping[str, Any], label: str) -> None:
    if not isinstance(packet, Mapping):
        raise ReconciliationPacketError(f"{label} packet must be a JSON object")
    errors: list[str] = []
    _require(errors, bool(_text(packet.get("packet_id"))), f"{label} packet_id is required")
    _require(errors, bool(_text(packet.get("packet_type"))), f"{label} packet_type is required")
    _scan_for_forbidden_content(errors, packet, label)
    _scan_for_enabled_consequential_controls(errors, packet, label)
    if errors:
        raise ReconciliationPacketError("; ".join(_dedupe(errors)))


def _observed_surface_deltas(transcript: Mapping[str, Any], approval: Mapping[str, Any], transcript_id: str, approval_id: str) -> list[dict[str, Any]]:
    observations = [item for item in _sequence(transcript.get("ordered_operator_observations")) if _text(_mapping(item).get("kind")) == "redacted_page_state_summary"]
    approvals_by_surface = {_text(_mapping(item).get("surface_id")): _mapping(item) for item in _sequence(approval.get("selector_delta_approval_items"))}
    rows: list[dict[str, Any]] = []
    for index, raw_observation in enumerate(observations, start=1):
        observation = _mapping(raw_observation)
        surface_id = _text(observation.get("surface_id")) or _text(observation.get("page_state_id"))
        approval_item = approvals_by_surface.get(surface_id, {})
        rows.append(
            {
                "delta_id": f"observed-surface-delta-{index}",
                "surface_id": surface_id,
                "source_observation_id": _text(observation.get("page_state_id")) or f"operator-observation-{index}",
                "observed_change": _text(observation.get("redacted_summary")) or "redacted page-state summary consumed",
                "decision": "keep_as_redacted_observation_delta",
                "active_registry_mutation": False,
                "agent_state_mutation": False,
                "citations": _dedupe([transcript_id, approval_id, _text(approval_item.get("selector_delta_id"))]),
            }
        )
    return rows


def _kept_decisions(approval: Mapping[str, Any], approval_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(_sequence(approval.get("selector_delta_approval_items")), start=1):
        item_map = _mapping(item)
        rows.append(
            {
                "decision_id": f"kept-decision-{index}",
                "surface_id": _text(item_map.get("surface_id")),
                "reason": "Reviewer approval packet keeps the candidate as review-pending and does not promote it to the active registry.",
                "status": "kept_for_reviewer_packet_only",
                "active_registry_mutation": False,
                "agent_state_mutation": False,
                "citations": _dedupe([approval_id, _text(item_map.get("selector_delta_id"))] + list(_text_list(item_map.get("citations")))),
            }
        )
    return rows


def _manual_handoff_decisions(approval: Mapping[str, Any], transcript: Mapping[str, Any], approval_id: str, transcript_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    carryovers = _sequence(approval.get("manual_handoff_carryovers"))
    for index, item in enumerate(carryovers, start=1):
        item_map = _mapping(item)
        rows.append(
            {
                "handoff_id": f"manual-handoff-{index}",
                "surface_id": _text(item_map.get("surface_id")) or "devhub-read-only-pilot",
                "reason": _text(item_map.get("reason")) or "Live DevHub verification remains attended/manual before any official action.",
                "decision": "manual_handoff_required",
                "attended_operator_required": True,
                "live_devhub_launch_allowed_by_packet": False,
                "citations": _dedupe([approval_id, transcript_id] + list(_text_list(item_map.get("citations")))),
            }
        )
    if rows:
        return rows
    return [
        {
            "handoff_id": "manual-handoff-1",
            "surface_id": "devhub-read-only-pilot",
            "reason": "No live DevHub use is authorized by the simulated transcript; attended verification is required before use.",
            "decision": "manual_handoff_required",
            "attended_operator_required": True,
            "live_devhub_launch_allowed_by_packet": False,
            "citations": (approval_id, transcript_id),
        }
    ]


def _redaction_follow_ups(redaction: Mapping[str, Any], redaction_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_field in ("abort_prompts", "private_artifact_prohibitions", "redaction_rules"):
        for item in _sequence(redaction.get(source_field)):
            item_map = _mapping(item)
            owner = _text(item_map.get("owner_id")) or _text(item_map.get("owner")) or "devhub_pilot_operator"
            action = _text(item_map.get("prompt")) or _text(item_map.get("prohibition")) or _text(item_map.get("rule")) or _text(item_map.get("target"))
            if action:
                rows.append(
                    {
                        "follow_up_id": f"redaction-follow-up-{len(rows) + 1}",
                        "owner": owner,
                        "action": action,
                        "source_section": source_field,
                        "status": "open_for_reviewer_follow_up",
                        "citations": _dedupe([redaction_id] + list(_text_list(item_map.get("citations")))),
                    }
                )
    return rows[:6]


def _reviewer_owner_fields(transcript: Mapping[str, Any], approval: Mapping[str, Any], redaction: Mapping[str, Any], transcript_id: str, approval_id: str, redaction_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    fields = _mapping(transcript.get("reviewer_owner_fields"))
    if fields:
        rows.append(
            {
                "owner_id": _text(fields.get("owner")) or "devhub_pilot_owner",
                "reviewer_id": _text(fields.get("reviewer")) or "devhub_pilot_reviewer",
                "responsibility": "operator transcript reconciliation review",
                "approval_required_before_live_use": fields.get("approval_required_before_live_use") is not False,
                "citations": (transcript_id,),
            }
        )
    for slot in _sequence(approval.get("reviewer_signoff_slots")):
        slot_map = _mapping(slot)
        rows.append(
            {
                "owner_id": _text(slot_map.get("owner")) or _text(slot_map.get("owner_id")) or "surface_registry_owner",
                "reviewer_id": _text(slot_map.get("reviewer")) or _text(slot_map.get("reviewer_id")) or "surface_registry_reviewer",
                "responsibility": _text(slot_map.get("scope")) or "surface registry reviewer approval",
                "approval_required_before_live_use": True,
                "citations": _dedupe([approval_id] + list(_text_list(slot_map.get("citations")))),
            }
        )
    for owner in _sequence(redaction.get("reviewer_owners")):
        owner_map = _mapping(owner)
        rows.append(
            {
                "owner_id": _text(owner_map.get("owner_id")) or "redaction_owner",
                "reviewer_id": _text(owner_map.get("reviewer_id")) or _text(owner_map.get("reviewer")) or "redaction_reviewer",
                "responsibility": _text(owner_map.get("responsibility")) or "observation redaction follow-up",
                "approval_required_before_live_use": True,
                "citations": _dedupe([redaction_id] + list(_text_list(owner_map.get("citations")))),
            }
        )
    return rows


def _validate_source_packets(errors: list[str], value: Any) -> None:
    sources = _mapping(value)
    for key in ("operator_transcript", "surface_registry_reviewer_approval", "observation_redaction_review"):
        source = _mapping(sources.get(key))
        _require(errors, bool(_text(source.get("packet_id"))), f"source_packets.{key}.packet_id is required")
        _require(errors, bool(_text(source.get("packet_type"))), f"source_packets.{key}.packet_type is required")
        _require(errors, source.get("consumed") is True, f"source_packets.{key}.consumed must be true")


def _validate_cited_rows(errors: list[str], value: Any, field_name: str, required_fields: Sequence[str]) -> None:
    rows = _sequence(value)
    if not rows:
        errors.append(f"{field_name} must be non-empty")
        return
    for index, row in enumerate(rows):
        item = _mapping(row)
        path = f"{field_name}[{index}]"
        for field in required_fields:
            _require(errors, bool(_text(item.get(field))), f"{path}.{field} is required")
        _require(errors, bool(_text_list(item.get("citations"))), f"{path}.citations must be non-empty")
        if "active_registry_mutation" in item:
            _require(errors, item.get("active_registry_mutation") is False, f"{path}.active_registry_mutation must be false")
        if "agent_state_mutation" in item:
            _require(errors, item.get("agent_state_mutation") is False, f"{path}.agent_state_mutation must be false")


def _validate_reviewer_owner_fields(errors: list[str], value: Any) -> None:
    rows = _sequence(value)
    if not rows:
        errors.append("reviewer_owner_fields must be non-empty")
        return
    for index, row in enumerate(rows):
        item = _mapping(row)
        path = f"reviewer_owner_fields[{index}]"
        for field in ("owner_id", "reviewer_id", "responsibility"):
            _require(errors, bool(_text(item.get(field))), f"{path}.{field} is required")
        _require(errors, item.get("approval_required_before_live_use") is True, f"{path}.approval_required_before_live_use must be true")
        _require(errors, bool(_text_list(item.get("citations"))), f"{path}.citations must be non-empty")


def _validate_attestations(errors: list[str], value: Any) -> None:
    attestations = _mapping(value)
    for name in NO_MUTATION_ATTESTATIONS:
        _require(errors, attestations.get(name) is True, f"no_active_surface_registry_no_agent_state_mutation_attestations.{name} must be true")


def _scan_for_forbidden_content(errors: list[str], value: Any, path: str) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if key_text.casefold() in FORBIDDEN_KEYS:
                errors.append(f"{path}.{key_text} contains forbidden private/session field")
            _scan_for_forbidden_content(errors, child, f"{path}.{key_text}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _scan_for_forbidden_content(errors, child, f"{path}[{index}]")
    elif isinstance(value, str):
        for pattern in FORBIDDEN_TEXT_PATTERNS:
            if pattern.search(value):
                errors.append(f"{path} contains private value or browser artifact reference")
                break


def _scan_for_enabled_consequential_controls(errors: list[str], value: Any, path: str) -> None:
    if isinstance(value, Mapping):
        lowered_values = " ".join(_text(child).casefold() for child in value.values() if isinstance(child, str))
        has_consequential_term = any(term in lowered_values for term in CONSEQUENTIAL_TERMS)
        if has_consequential_term:
            for key, child in value.items():
                if str(key).casefold() in TRUE_ENABLEMENT_KEYS and child is True:
                    errors.append(f"{path} must not enable consequential DevHub controls")
        for key, child in value.items():
            _scan_for_enabled_consequential_controls(errors, child, f"{path}.{key}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _scan_for_enabled_consequential_controls(errors, child, f"{path}[{index}]")


def _mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    return {}


def _sequence(value: Any) -> tuple[Any, ...]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(value)
    return ()


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    return ""


def _text_list(value: Any) -> tuple[str, ...]:
    return tuple(item.strip() for item in _sequence(value) if isinstance(item, str) and item.strip())


def _require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def _dedupe(values: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return tuple(result)
