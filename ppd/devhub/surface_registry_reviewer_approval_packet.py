"""Fixture-first DevHub surface registry reviewer approval packets.

The packet assembled here is a review artifact only. It consumes already-redacted
fixture packets and never launches browsers, stores auth state, persists browser
artifacts, or mutates the active DevHub surface registry.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from ppd.devhub.read_only_pilot_evidence_review import assert_read_only_pilot_evidence_packet
from ppd.devhub.read_only_surface_drift_comparison_packet import assert_valid_read_only_surface_drift_comparison_packet
from ppd.devhub.surface_registry_promotion_candidate import assert_valid_surface_registry_promotion_candidate_packet


REQUIRED_PACKET_TYPE = "ppd.devhub_surface_registry_reviewer_approval_packet.v1"
REQUIRED_MODE = "fixture_first_devhub_surface_registry_reviewer_approval"
REQUIRED_NO_MUTATION_ATTESTATIONS = (
    "active_surface_registry_not_mutated",
    "active_surface_map_not_replaced",
    "selector_confidence_not_upgraded",
    "no_devhub_browser_launched",
    "no_auth_state_or_browser_artifacts_stored",
    "no_consequential_controls_enabled",
    "review_packet_only_no_promotion",
)
FORBIDDEN_KEYS = {
    "auth_state",
    "auth_state_path",
    "browser_state",
    "cookies",
    "har",
    "har_path",
    "password",
    "raw_authenticated_value",
    "raw_authenticated_values",
    "screenshot",
    "screenshot_path",
    "session_state",
    "storage_state",
    "storage_state_path",
    "trace",
    "trace_path",
}
FORBIDDEN_STRING_MARKERS = (
    "/home/",
    "/users/",
    "c:\\users\\",
    "file://",
    "~/",
    ".har",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    "trace.zip",
    "auth_state.json",
    "storage_state.json",
)
LIVE_BROWSER_MARKERS = (
    "clicked in devhub",
    "executed playwright",
    "launched browser",
    "live browser",
    "ran playwright",
    "real devhub session",
)
CONSEQUENTIAL_TERMS = ("cancel", "certif", "pay", "payment", "purchase", "schedule", "submit", "upload", "withdraw")
ACTIVE_MUTATION_KEYS = {
    "active_registry_mutation",
    "active_surface_registry_mutation",
    "applied_to_registry",
    "mutates_active_surface_registry",
    "registry_mutated",
    "writes_surface_registry",
}


def load_json_packet(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("packet fixture must be a JSON object")
    return data


def build_surface_registry_reviewer_approval_packet(
    promotion_candidate_packet: Mapping[str, Any],
    pilot_evidence_review_packet: Mapping[str, Any],
    surface_drift_comparison_packet: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a cited reviewer approval packet from fixture inputs only."""

    assert_valid_surface_registry_promotion_candidate_packet(promotion_candidate_packet)
    assert_read_only_pilot_evidence_packet(dict(pilot_evidence_review_packet))
    assert_valid_read_only_surface_drift_comparison_packet(surface_drift_comparison_packet)

    candidate_id = _text(promotion_candidate_packet.get("packet_id"))
    evidence_id = _text(pilot_evidence_review_packet.get("packet_id"))
    drift_id = _text(surface_drift_comparison_packet.get("packet_id"))
    packet = {
        "packet_id": "devhub-surface-registry-reviewer-approval-synthetic-v1",
        "packet_type": REQUIRED_PACKET_TYPE,
        "mode": REQUIRED_MODE,
        "fixture_first": True,
        "launches_devhub": False,
        "launches_playwright": False,
        "stores_browser_artifacts": False,
        "writes_surface_registry": False,
        "mutates_active_surface_registry": False,
        "source_packets": {
            "surface_registry_promotion_candidate": {"packet_id": candidate_id, "consumed": True},
            "devhub_read_only_pilot_evidence_review": {"packet_id": evidence_id, "consumed": True},
            "surface_drift_comparison": {"packet_id": drift_id, "consumed": True},
        },
        "selector_delta_approval_items": _selector_delta_approval_items(promotion_candidate_packet, candidate_id, drift_id),
        "reviewer_signoff_slots": _reviewer_signoff_slots(promotion_candidate_packet, surface_drift_comparison_packet, candidate_id, drift_id),
        "manual_handoff_carryovers": _manual_handoff_carryovers(promotion_candidate_packet, pilot_evidence_review_packet, candidate_id, evidence_id),
        "redaction_attestations": _redaction_attestations(promotion_candidate_packet, pilot_evidence_review_packet, candidate_id, evidence_id),
        "rollback_notes": _rollback_notes(surface_drift_comparison_packet, promotion_candidate_packet, candidate_id, drift_id),
        "no_active_surface_registry_mutation_attestations": {name: True for name in REQUIRED_NO_MUTATION_ATTESTATIONS},
    }
    assert_valid_surface_registry_reviewer_approval_packet(packet)
    return packet


def validate_surface_registry_reviewer_approval_packet(packet: Mapping[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    _require(errors, packet.get("packet_type") == REQUIRED_PACKET_TYPE, f"packet_type must be {REQUIRED_PACKET_TYPE}")
    _require(errors, packet.get("mode") == REQUIRED_MODE, f"mode must be {REQUIRED_MODE}")
    _require(errors, packet.get("fixture_first") is True, "fixture_first must be true")
    for flag in ("launches_devhub", "launches_playwright", "stores_browser_artifacts", "writes_surface_registry", "mutates_active_surface_registry"):
        _require(errors, packet.get(flag) is False, f"{flag} must be false")

    sources = _mapping(packet.get("source_packets"))
    for key in ("surface_registry_promotion_candidate", "devhub_read_only_pilot_evidence_review", "surface_drift_comparison"):
        source = _mapping(sources.get(key))
        _require(errors, bool(_text(source.get("packet_id"))), f"source_packets.{key}.packet_id is required")
        _require(errors, source.get("consumed") is True, f"source_packets.{key}.consumed must be true")

    items = _sequence(packet.get("selector_delta_approval_items"))
    _require(errors, bool(items), "selector_delta_approval_items must not be empty")
    for index, item in enumerate(items):
        item_map = _mapping(item)
        path = f"selector_delta_approval_items[{index}]"
        _require(errors, bool(_text(item_map.get("surface_id"))), f"{path}.surface_id is required")
        _require(errors, bool(_text(item_map.get("selector_delta_id"))), f"{path}.selector_delta_id is required")
        _require(errors, _text(item_map.get("approval_status")) == "pending_reviewer_approval", f"{path}.approval_status must be pending_reviewer_approval")
        _require(errors, item_map.get("active_registry_mutation") is False, f"{path}.active_registry_mutation must be false")
        _require(errors, bool(_sequence(item_map.get("citations"))), f"{path}.citations must not be empty")

    for field in ("reviewer_signoff_slots", "manual_handoff_carryovers", "redaction_attestations", "rollback_notes"):
        values = _sequence(packet.get(field))
        _require(errors, bool(values), f"{field} must not be empty")
        for index, value in enumerate(values):
            value_map = _mapping(value)
            _require(errors, bool(_sequence(value_map.get("citations"))), f"{field}[{index}].citations must not be empty")

    for index, slot in enumerate(_sequence(packet.get("reviewer_signoff_slots"))):
        slot_map = _mapping(slot)
        _require(errors, bool(_text(slot_map.get("owner"))), f"reviewer_signoff_slots[{index}].owner is required")
        _require(errors, _text(slot_map.get("status")) == "pending", f"reviewer_signoff_slots[{index}].status must be pending")

    attestations = _mapping(packet.get("no_active_surface_registry_mutation_attestations"))
    for name in REQUIRED_NO_MUTATION_ATTESTATIONS:
        _require(errors, attestations.get(name) is True, f"no_active_surface_registry_mutation_attestations.{name} must be true")

    _scan_for_forbidden_content(errors, packet)
    _scan_for_consequential_controls(errors, packet)
    _scan_for_active_mutation_flags(errors, packet)
    return _dedupe(errors)


def assert_valid_surface_registry_reviewer_approval_packet(packet: Mapping[str, Any]) -> None:
    errors = validate_surface_registry_reviewer_approval_packet(packet)
    if errors:
        raise AssertionError("; ".join(errors))


def _selector_delta_approval_items(candidate: Mapping[str, Any], candidate_id: str, drift_id: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    thresholds_by_surface: dict[str, list[Mapping[str, Any]]] = {}
    for threshold in _sequence(candidate.get("selector_confidence_thresholds")):
        threshold_map = _mapping(threshold)
        thresholds_by_surface.setdefault(_text(threshold_map.get("surface_id")), []).append(threshold_map)

    for delta in _sequence(candidate.get("synthetic_surface_map_deltas")):
        delta_map = _mapping(delta)
        surface_id = _text(delta_map.get("surface_id"))
        citations = _citations(delta_map, candidate_id, drift_id, surface_id)
        for index, threshold in enumerate(thresholds_by_surface.get(surface_id, []) or [{}]):
            threshold_map = _mapping(threshold)
            items.append(
                {
                    "selector_delta_id": f"selector-delta-approval-{surface_id}-{index + 1}",
                    "surface_id": surface_id,
                    "approval_status": "pending_reviewer_approval",
                    "approval_effect": "reviewer_packet_only_no_promotion",
                    "candidate_selector_confidence": _text(threshold_map.get("observed_confidence")) or "redacted_fixture_review",
                    "required_active_registry_confidence": _text(threshold_map.get("active_registry_confidence_required")) or "attended_review_required",
                    "route_delta_count": len(_sequence(delta_map.get("route_deltas"))),
                    "heading_delta_count": len(_sequence(delta_map.get("heading_deltas"))),
                    "action_delta_count": len(_sequence(delta_map.get("action_deltas"))),
                    "active_registry_mutation": False,
                    "citations": _citations(threshold_map, *citations),
                }
            )
    return items


def _reviewer_signoff_slots(candidate: Mapping[str, Any], drift: Mapping[str, Any], candidate_id: str, drift_id: str) -> list[dict[str, Any]]:
    slots: list[dict[str, Any]] = []
    seen: set[str] = set()
    for source, packet_id, raw_slots in (
        ("promotion_candidate", candidate_id, candidate.get("reviewer_signoff_slots")),
        ("surface_drift_comparison", drift_id, drift.get("reviewer_owners")),
    ):
        for raw_slot in _sequence(raw_slots):
            slot = _mapping(raw_slot)
            owner = _text(slot.get("owner"))
            if not owner or owner in seen:
                continue
            seen.add(owner)
            slots.append(
                {
                    "owner": owner,
                    "source": source,
                    "status": "pending",
                    "must_review": [_text(item) for item in _sequence(slot.get("must_review", slot.get("owns"))) if _text(item)],
                    "decision": "",
                    "signed_at": "",
                    "citations": _citations(slot, packet_id, owner),
                }
            )
    return slots


def _manual_handoff_carryovers(candidate: Mapping[str, Any], evidence: Mapping[str, Any], candidate_id: str, evidence_id: str) -> list[dict[str, Any]]:
    carryovers: list[dict[str, Any]] = []
    for item in _sequence(candidate.get("manual_handoff_carryovers")):
        item_map = _mapping(item)
        carryovers.append(
            {
                "carryover_id": _text(item_map.get("carryover_id")),
                "source": "surface_registry_promotion_candidate",
                "status": "carried_forward",
                "reason": _text(item_map.get("reason")),
                "citations": _citations(item_map, candidate_id),
            }
        )
    for checkpoint in _sequence(evidence.get("manual_handoff_checkpoints")):
        checkpoint_map = _mapping(checkpoint)
        carryovers.append(
            {
                "carryover_id": _text(checkpoint_map.get("checkpoint_id")),
                "source": "pilot_evidence_review",
                "status": "carried_forward",
                "reason": _text(checkpoint_map.get("reason")),
                "citations": [evidence_id, _text(checkpoint_map.get("checkpoint_id"))],
            }
        )
    return carryovers


def _redaction_attestations(candidate: Mapping[str, Any], evidence: Mapping[str, Any], candidate_id: str, evidence_id: str) -> list[dict[str, Any]]:
    attestations: list[dict[str, Any]] = []
    for name, accepted in _mapping(candidate.get("redaction_attestations")).items():
        attestations.append({"attestation_id": _text(name), "source": "promotion_candidate", "accepted": accepted is True, "citations": [candidate_id, _text(name)]})
    for name, accepted in _mapping(evidence.get("redaction_attestation")).items():
        if name == "redacted_fields":
            continue
        attestations.append({"attestation_id": _text(name), "source": "pilot_evidence_review", "accepted": accepted is True, "citations": [evidence_id, _text(name)]})
    return attestations


def _rollback_notes(drift: Mapping[str, Any], candidate: Mapping[str, Any], candidate_id: str, drift_id: str) -> list[dict[str, Any]]:
    notes: list[dict[str, Any]] = []
    for index, deferral in enumerate(_sequence(drift.get("unsupported_drift_deferrals"))):
        deferral_map = _mapping(deferral)
        notes.append(
            {
                "rollback_note_id": f"rollback-note-{index + 1}",
                "surface_id": _text(deferral_map.get("surface_id")),
                "rollback_trigger": "unsupported_drift_or_selector_delta_rejected_by_reviewer",
                "rollback_action": "leave_active_surface_registry_unchanged_and_return_to_manual_handoff",
                "active_rollback_executed": False,
                "citations": _citations(deferral_map, drift_id),
            }
        )
    notes.append(
        {
            "rollback_note_id": "rollback-note-no-active-promotion",
            "surface_id": "all_candidate_surfaces",
            "rollback_trigger": "reviewer_declines_approval_or_redaction_attestation_fails",
            "rollback_action": "discard reviewer packet output without active registry mutation",
            "active_rollback_executed": False,
            "citations": [candidate_id, "no_active_promotion_attestations"],
        }
    )
    return notes


def _scan_for_forbidden_content(errors: list[str], value: Any, path: str = "packet") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = _text(key)
            nested_path = f"{path}.{key_text}"
            if key_text.lower() in FORBIDDEN_KEYS and _present(nested):
                errors.append(f"{nested_path} must not contain private DevHub session, browser, screenshot, trace, HAR, or raw authenticated artifacts")
            _scan_for_forbidden_content(errors, nested, nested_path)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            _scan_for_forbidden_content(errors, item, f"{path}[{index}]")
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in FORBIDDEN_STRING_MARKERS):
            errors.append(f"{path} must not reference private paths or browser artifacts")
        if any(marker in lowered for marker in LIVE_BROWSER_MARKERS):
            errors.append(f"{path} must not claim live browser execution")
        if "raw authenticated value" in lowered:
            errors.append(f"{path} must not include raw authenticated values")


def _scan_for_consequential_controls(errors: list[str], value: Any, path: str = "packet") -> None:
    if isinstance(value, Mapping):
        enabled = value.get("enabled") is True or value.get("allowed") is True or _text(value.get("state")).lower() == "enabled"
        text = " ".join(_text(value.get(key)) for key in ("action", "control_id", "id", "label", "name", "type")).lower()
        if enabled and any(term in text for term in CONSEQUENTIAL_TERMS):
            errors.append(f"{path} must not enable consequential DevHub controls")
        for key, nested in value.items():
            _scan_for_consequential_controls(errors, nested, f"{path}.{_text(key)}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            _scan_for_consequential_controls(errors, item, f"{path}[{index}]")


def _scan_for_active_mutation_flags(errors: list[str], value: Any, path: str = "packet") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = _text(key)
            nested_path = f"{path}.{key_text}"
            if key_text.lower() in ACTIVE_MUTATION_KEYS and nested is not False:
                errors.append(f"{nested_path} must not enable active surface-registry mutation")
            _scan_for_active_mutation_flags(errors, nested, nested_path)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            _scan_for_active_mutation_flags(errors, item, f"{path}[{index}]")


def _citations(value: Mapping[str, Any], *fallback: str) -> list[str]:
    citations = [_text(item) for item in _sequence(value.get("citations")) if _text(item)]
    citations.extend(_text(item) for item in fallback if _text(item))
    return sorted(dict.fromkeys(citations))


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


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: Any) -> Sequence[Any]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return value
    return ()


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def _dedupe(errors: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for error in errors:
        if error not in seen:
            seen.add(error)
            result.append(error)
    return tuple(result)
