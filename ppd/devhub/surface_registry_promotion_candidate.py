from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from ppd.devhub.read_only_pilot_evidence_review import assert_read_only_pilot_evidence_packet
from ppd.devhub.read_only_surface_drift_comparison_packet import assert_valid_read_only_surface_drift_comparison_packet


REQUIRED_PACKET_TYPE = "ppd.devhub_surface_registry_promotion_candidate.v1"
REQUIRED_MODE = "fixture_first_devhub_surface_registry_promotion_candidate"
REQUIRED_REDACTION_ATTESTATIONS = (
    "raw_authenticated_values_absent",
    "private_browser_artifacts_absent",
    "committed_artifacts_metadata_only",
    "redacted_labels_only",
)
REQUIRED_NO_ACTIVE_PROMOTION_ATTESTATIONS = (
    "active_promotion_state_inactive",
    "active_surface_registry_not_mutated",
    "active_surface_map_not_replaced",
    "selector_confidence_not_upgraded",
    "consequential_controls_not_enabled",
)
FORBIDDEN_PRESENT_KEYS = {
    "auth_state",
    "auth_state_path",
    "browser_state",
    "browser_trace",
    "cookies",
    "har",
    "har_file",
    "har_path",
    "local_private_path",
    "password",
    "private_path",
    "private_value",
    "raw_authenticated_value",
    "raw_authenticated_values",
    "screenshot",
    "screenshot_path",
    "screenshots",
    "session_artifact",
    "session_file",
    "session_state",
    "stored_auth_state",
    "storage_state",
    "storage_state_path",
    "trace",
    "trace_path",
    "traces",
}
FORBIDDEN_PRIVATE_STRING_MARKERS = (
    "/home/",
    "/users/",
    "c:\\users\\",
    "file://",
    "~/",
    "/var/folders/",
    "/private/var/",
    ".har",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".trace",
    "trace.zip",
    "auth_state.json",
    "storage_state.json",
)
LIVE_BROWSER_CLAIMS = (
    "authenticated browser session",
    "clicked in devhub",
    "executed playwright",
    "filled in devhub",
    "launched browser",
    "live browser",
    "playwright executed",
    "ran playwright",
    "real devhub session",
)
RAW_AUTHENTICATED_VALUE_CLAIMS = (
    "raw authenticated value",
    "raw authenticated values",
    "unredacted account",
    "unredacted permit",
    "private devhub value",
)
CONSEQUENTIAL_ACTION_TERMS = (
    "cancel",
    "certif",
    "pay",
    "payment",
    "purchase",
    "reactivat",
    "schedule",
    "submit",
    "upload",
    "withdraw",
)
ACTIVE_MUTATION_KEYS = {
    "active_registry_mutation",
    "active_surface_registry_mutation",
    "applied_to_registry",
    "mutates_active_surface_map",
    "mutates_active_surface_maps",
    "mutates_active_surface_registry",
    "registry_mutated",
    "surface_registry_mutation_active",
    "writes_surface_registry",
}


def load_json_packet(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("packet fixture must be a JSON object")
    return data


def build_surface_registry_promotion_candidate_packet(
    pilot_evidence_review_packet: Mapping[str, Any],
    surface_drift_comparison_packet: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a review-only DevHub surface registry promotion candidate from fixtures."""

    assert_read_only_pilot_evidence_packet(dict(pilot_evidence_review_packet))
    assert_valid_read_only_surface_drift_comparison_packet(surface_drift_comparison_packet)

    evidence_packet_id = _text(pilot_evidence_review_packet.get("packet_id"))
    drift_packet_id = _text(surface_drift_comparison_packet.get("packet_id"))
    comparisons = [_mapping(item) for item in _sequence(surface_drift_comparison_packet.get("surface_comparisons"))]

    packet = {
        "packet_id": "devhub-surface-registry-promotion-candidate-synthetic-v1",
        "packet_type": REQUIRED_PACKET_TYPE,
        "mode": REQUIRED_MODE,
        "fixture_first": True,
        "active_promotion_state": "inactive",
        "stores_browser_artifacts": False,
        "stores_credentials_or_browser_state": False,
        "writes_surface_registry": False,
        "mutates_active_surface_registry": False,
        "mutates_active_surface_map": False,
        "source_packets": {
            "devhub_read_only_pilot_evidence_review": {"packet_id": evidence_packet_id, "consumed": True},
            "devhub_read_only_surface_drift_comparison": {"packet_id": drift_packet_id, "consumed": True},
        },
        "synthetic_surface_map_deltas": _surface_map_deltas(comparisons, evidence_packet_id, drift_packet_id),
        "selector_confidence_thresholds": _selector_confidence_thresholds(comparisons, drift_packet_id),
        "redaction_attestations": {name: True for name in REQUIRED_REDACTION_ATTESTATIONS},
        "manual_handoff_carryovers": _manual_handoff_carryovers(pilot_evidence_review_packet, surface_drift_comparison_packet),
        "reviewer_signoff_slots": _reviewer_signoff_slots(surface_drift_comparison_packet, drift_packet_id),
        "no_active_promotion_attestations": {name: True for name in REQUIRED_NO_ACTIVE_PROMOTION_ATTESTATIONS},
    }
    assert_valid_surface_registry_promotion_candidate_packet(packet)
    return packet


def validate_surface_registry_promotion_candidate_packet(packet: Mapping[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    _require(errors, packet.get("packet_type") == REQUIRED_PACKET_TYPE, f"packet_type must be {REQUIRED_PACKET_TYPE}")
    _require(errors, packet.get("mode") == REQUIRED_MODE, f"mode must be {REQUIRED_MODE}")
    _require(errors, packet.get("fixture_first") is True, "fixture_first must be true")
    _require(errors, _text(packet.get("active_promotion_state")) == "inactive", "active_promotion_state must be inactive")
    for flag in (
        "stores_browser_artifacts",
        "stores_credentials_or_browser_state",
        "writes_surface_registry",
        "mutates_active_surface_registry",
        "mutates_active_surface_map",
    ):
        _require(errors, packet.get(flag) is False, f"{flag} must be false")

    source_packets = _mapping(packet.get("source_packets"))
    for key in ("devhub_read_only_pilot_evidence_review", "devhub_read_only_surface_drift_comparison"):
        source = _mapping(source_packets.get(key))
        _require(errors, bool(_text(source.get("packet_id"))), f"source_packets.{key}.packet_id is required")
        _require(errors, source.get("consumed") is True, f"source_packets.{key}.consumed must be true")

    deltas = _sequence(packet.get("synthetic_surface_map_deltas"))
    _require(errors, bool(deltas), "synthetic_surface_map_deltas must not be empty")
    for index, delta in enumerate(deltas):
        delta_map = _mapping(delta)
        path = f"synthetic_surface_map_deltas[{index}]"
        _require(errors, bool(_text(delta_map.get("surface_id"))), f"{path}.surface_id is required")
        _require(errors, bool(_sequence(delta_map.get("citations"))), f"{path}.citations must not be empty")
        _require(errors, _text(delta_map.get("promotion_effect")) == "synthetic_delta_only", f"{path}.promotion_effect must be synthetic_delta_only")
        _require(errors, delta_map.get("active_registry_mutation") is False, f"{path}.active_registry_mutation must be false")
        _validate_cited_difference_items(errors, delta_map, path)

    thresholds = _sequence(packet.get("selector_confidence_thresholds"))
    _require(errors, bool(thresholds), "selector_confidence_thresholds must not be empty")
    for index, threshold in enumerate(thresholds):
        threshold_map = _mapping(threshold)
        path = f"selector_confidence_thresholds[{index}]"
        _require(errors, bool(_text(threshold_map.get("surface_id"))), f"{path}.surface_id is required")
        _require(errors, bool(_text(threshold_map.get("minimum_candidate_confidence"))), f"{path}.minimum_candidate_confidence is required")
        _require(errors, bool(_text(threshold_map.get("active_registry_confidence_required"))), f"{path}.active_registry_confidence_required is required")
        _require(errors, threshold_map.get("promotion_allowed") is False, f"{path}.promotion_allowed must be false")
        _require(errors, _text(threshold_map.get("threshold_action")) == "manual_handoff_before_active_registry", f"{path}.threshold_action must require manual handoff")
        _require(errors, bool(_sequence(threshold_map.get("citations"))), f"{path}.citations must not be empty")

    attestations = _mapping(packet.get("redaction_attestations"))
    for name in REQUIRED_REDACTION_ATTESTATIONS:
        _require(errors, attestations.get(name) is True, f"redaction_attestations.{name} must be true")

    carryovers = _sequence(packet.get("manual_handoff_carryovers"))
    _require(errors, bool(carryovers), "manual_handoff_carryovers must not be empty")
    for index, carryover in enumerate(carryovers):
        carryover_map = _mapping(carryover)
        _require(errors, bool(_text(carryover_map.get("carryover_id"))), f"manual_handoff_carryovers[{index}].carryover_id is required")
        _require(errors, _text(carryover_map.get("status")) == "carried_forward", f"manual_handoff_carryovers[{index}].status must be carried_forward")
        _require(errors, bool(_sequence(carryover_map.get("citations"))), f"manual_handoff_carryovers[{index}].citations must not be empty")

    signoffs = _sequence(packet.get("reviewer_signoff_slots"))
    _require(errors, bool(signoffs), "reviewer_signoff_slots must not be empty")
    for index, signoff in enumerate(signoffs):
        signoff_map = _mapping(signoff)
        _require(errors, bool(_text(signoff_map.get("owner"))), f"reviewer_signoff_slots[{index}].owner is required")
        _require(errors, _text(signoff_map.get("status")) == "pending", f"reviewer_signoff_slots[{index}].status must be pending")
        _require(errors, bool(_sequence(signoff_map.get("must_review"))), f"reviewer_signoff_slots[{index}].must_review must not be empty")
        _require(errors, bool(_sequence(signoff_map.get("citations"))), f"reviewer_signoff_slots[{index}].citations must not be empty")

    no_active = _mapping(packet.get("no_active_promotion_attestations"))
    for name in REQUIRED_NO_ACTIVE_PROMOTION_ATTESTATIONS:
        _require(errors, no_active.get(name) is True, f"no_active_promotion_attestations.{name} must be true")

    _scan_for_forbidden_artifacts(errors, packet)
    _scan_for_live_browser_claims(errors, packet)
    _scan_for_raw_authenticated_claims(errors, packet)
    _scan_for_enabled_consequential_controls(errors, packet)
    _scan_for_active_mutation_flags(errors, packet)
    _scan_for_uncited_selector_changes(errors, packet)
    return _dedupe(errors)


def assert_valid_surface_registry_promotion_candidate_packet(packet: Mapping[str, Any]) -> None:
    errors = validate_surface_registry_promotion_candidate_packet(packet)
    if errors:
        raise AssertionError("; ".join(errors))


def _surface_map_deltas(comparisons: Sequence[Mapping[str, Any]], evidence_packet_id: str, drift_packet_id: str) -> list[dict[str, Any]]:
    deltas = []
    for comparison in comparisons:
        surface_id = _text(comparison.get("surface_id"))
        citations = _citations(comparison, evidence_packet_id, drift_packet_id, surface_id)
        deltas.append(
            {
                "delta_id": f"surface-map-delta-{surface_id}",
                "surface_id": surface_id,
                "promotion_effect": "synthetic_delta_only",
                "active_registry_mutation": False,
                "route_deltas": _difference_items(comparison, "route_differences", citations),
                "heading_deltas": _difference_items(comparison, "heading_differences", citations),
                "action_deltas": _difference_items(comparison, "action_differences", citations),
                "unsupported_drift": comparison.get("unsupported_drift") is True,
                "citations": citations,
            }
        )
    return deltas


def _selector_confidence_thresholds(comparisons: Sequence[Mapping[str, Any]], drift_packet_id: str) -> list[dict[str, Any]]:
    thresholds = []
    for comparison in comparisons:
        surface_id = _text(comparison.get("surface_id"))
        for index, note in enumerate(_sequence(comparison.get("selector_confidence_notes"))):
            note_map = _mapping(note)
            thresholds.append(
                {
                    "threshold_id": f"selector-threshold-{surface_id}-{index + 1}",
                    "surface_id": surface_id,
                    "minimum_candidate_confidence": "redacted_fixture_review",
                    "active_registry_confidence_required": "attended_review_required",
                    "observed_confidence": _text(note_map.get("observed_confidence")),
                    "proposed_confidence": _text(note_map.get("proposed_confidence")),
                    "promotion_allowed": False,
                    "threshold_action": "manual_handoff_before_active_registry",
                    "rationale": _text(note_map.get("note")),
                    "citations": _citations(note_map, drift_packet_id, surface_id),
                }
            )
    return thresholds


def _manual_handoff_carryovers(evidence_packet: Mapping[str, Any], drift_packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    carryovers = []
    evidence_packet_id = _text(evidence_packet.get("packet_id"))
    drift_packet_id = _text(drift_packet.get("packet_id"))
    for checkpoint in _sequence(evidence_packet.get("manual_handoff_checkpoints")):
        checkpoint_map = _mapping(checkpoint)
        carryovers.append(
            {
                "carryover_id": _text(checkpoint_map.get("checkpoint_id")),
                "source": "pilot_evidence_review",
                "status": "carried_forward",
                "reason": _text(checkpoint_map.get("reason")),
                "citations": [evidence_packet_id, _text(checkpoint_map.get("checkpoint_id"))],
            }
        )
    for deferral in _sequence(drift_packet.get("unsupported_drift_deferrals")):
        deferral_map = _mapping(deferral)
        surface_id = _text(deferral_map.get("surface_id"))
        carryovers.append(
            {
                "carryover_id": f"unsupported-drift-{surface_id}",
                "source": "surface_drift_comparison",
                "status": "carried_forward",
                "reason": _text(deferral_map.get("reason")),
                "citations": _citations(deferral_map, drift_packet_id, surface_id),
            }
        )
    return carryovers


def _reviewer_signoff_slots(drift_packet: Mapping[str, Any], drift_packet_id: str) -> list[dict[str, Any]]:
    slots = []
    for owner in _sequence(drift_packet.get("reviewer_owners")):
        owner_map = _mapping(owner)
        slots.append(
            {
                "owner": _text(owner_map.get("owner")),
                "status": "pending",
                "must_review": [_text(item) for item in _sequence(owner_map.get("owns"))],
                "signoff_prompt": "Review cited synthetic deltas and thresholds before any separate active promotion decision.",
                "citations": [drift_packet_id, _text(owner_map.get("owner"))],
            }
        )
    return slots


def _difference_items(comparison: Mapping[str, Any], field: str, fallback_citations: Sequence[str]) -> list[dict[str, Any]]:
    items = []
    for item in _sequence(comparison.get(field)):
        item_map = _mapping(item)
        items.append(
            {
                "field": _text(item_map.get("field")),
                "status": _text(item_map.get("status")),
                "observed": item_map.get("observed"),
                "candidate": item_map.get("candidate"),
                "citations": _citations(item_map, *fallback_citations),
            }
        )
    return items


def _validate_cited_difference_items(errors: list[str], delta: Mapping[str, Any], path: str) -> None:
    for field_name in ("route_deltas", "heading_deltas", "action_deltas"):
        for index, item in enumerate(_sequence(delta.get(field_name))):
            item_map = _mapping(item)
            item_path = f"{path}.{field_name}[{index}]"
            _require(errors, bool(_text(item_map.get("field"))), f"{item_path}.field is required")
            _require(errors, bool(_text(item_map.get("status"))), f"{item_path}.status is required")
            _require(errors, bool(_sequence(item_map.get("citations"))), f"{item_path}.citations must not be empty")


def _scan_for_forbidden_artifacts(errors: list[str], value: Any, path: str = "packet") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = _text(key)
            key_lower = key_text.lower()
            nested_path = f"{path}.{key_text}"
            if key_lower in FORBIDDEN_PRESENT_KEYS and _present(nested):
                errors.append(f"{nested_path} must not store private DevHub or browser artifacts")
            _scan_for_forbidden_artifacts(errors, nested, nested_path)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            _scan_for_forbidden_artifacts(errors, item, f"{path}[{index}]")
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in FORBIDDEN_PRIVATE_STRING_MARKERS):
            errors.append(f"{path} must not reference private paths or browser artifacts")


def _scan_for_live_browser_claims(errors: list[str], value: Any, path: str = "packet", parent_key: str = "") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = _text(key)
            nested_path = f"{path}.{key_text}"
            if key_text.lower() in {"live_browser_execution", "live_browser_claimed", "browser_executed"} and nested is True:
                errors.append(f"{nested_path} must not claim live browser execution")
            _scan_for_live_browser_claims(errors, nested, nested_path, key_text.lower())
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            _scan_for_live_browser_claims(errors, item, f"{path}[{index}]", parent_key)
    elif isinstance(value, str):
        lowered = value.lower()
        if any(claim in lowered for claim in LIVE_BROWSER_CLAIMS):
            errors.append(f"{path} must not claim live browser execution")
        if parent_key in {"execution_mode", "browser_execution", "browser_mode"} and lowered in {"live", "headed", "playwright_live"}:
            errors.append(f"{path} must remain fixture-only or review-only")


def _scan_for_raw_authenticated_claims(errors: list[str], value: Any, path: str = "packet") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            _scan_for_raw_authenticated_claims(errors, nested, f"{path}.{_text(key)}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            _scan_for_raw_authenticated_claims(errors, item, f"{path}[{index}]")
    elif isinstance(value, str):
        lowered = value.lower()
        if any(claim in lowered for claim in RAW_AUTHENTICATED_VALUE_CLAIMS):
            errors.append(f"{path} must not include raw authenticated values")


def _scan_for_enabled_consequential_controls(errors: list[str], value: Any, path: str = "packet") -> None:
    if isinstance(value, Mapping):
        enabled = value.get("enabled") is True or _text(value.get("state")).lower() == "enabled" or value.get("allowed") is True
        control_text = " ".join(_text(value.get(key)) for key in ("action", "control_id", "id", "label", "name", "type")).lower()
        if enabled and any(term in control_text for term in CONSEQUENTIAL_ACTION_TERMS):
            errors.append(f"{path} must not enable consequential controls")
        for key, nested in value.items():
            _scan_for_enabled_consequential_controls(errors, nested, f"{path}.{_text(key)}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            _scan_for_enabled_consequential_controls(errors, item, f"{path}[{index}]")


def _scan_for_active_mutation_flags(errors: list[str], value: Any, path: str = "packet") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = _text(key)
            key_lower = key_text.lower()
            nested_path = f"{path}.{key_text}"
            if key_lower in ACTIVE_MUTATION_KEYS and nested is not False:
                errors.append(f"{nested_path} must not enable active surface-registry mutation")
            if key_lower in {"surface_registry_mutation", "active_surface_registry_mutation_flags"} and _present(nested):
                if not _is_safe_mutation_metadata(nested):
                    errors.append(f"{nested_path} must not include active surface-registry mutation flags")
            _scan_for_active_mutation_flags(errors, nested, nested_path)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            _scan_for_active_mutation_flags(errors, item, f"{path}[{index}]")


def _scan_for_uncited_selector_changes(errors: list[str], value: Any, path: str = "packet") -> None:
    if isinstance(value, Mapping):
        path_lower = path.lower()
        has_selector_context = "selector" in path_lower or any("selector" in _text(key).lower() for key in value.keys())
        if has_selector_context and _looks_like_selector_change(value) and not _sequence(value.get("citations")):
            errors.append(f"{path} selector changes must include citations")
        for key, nested in value.items():
            _scan_for_uncited_selector_changes(errors, nested, f"{path}.{_text(key)}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            _scan_for_uncited_selector_changes(errors, item, f"{path}[{index}]")


def _looks_like_selector_change(value: Mapping[str, Any]) -> bool:
    if "selector" in value and any(key in value for key in ("candidate", "observed", "proposed", "status")):
        return True
    if any(key in value for key in ("observed_confidence", "proposed_confidence", "previous_confidence", "upgrade_requested")):
        return True
    status = _text(value.get("status")).lower()
    return status in {"synthetic_difference", "changed", "upgrade_requested"}


def _is_safe_mutation_metadata(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_lower = _text(key).lower()
            if key_lower in {"active", "enabled", "requested", "allowed"} and nested is True:
                return False
            if key_lower == "mode" and _text(nested).lower() not in {"", "none", "read_only", "review_only", "inactive"}:
                return False
            if not _is_safe_mutation_metadata(nested):
                return False
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return not value or all(_is_safe_mutation_metadata(item) for item in value)
    return True


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


__all__ = [
    "REQUIRED_MODE",
    "REQUIRED_PACKET_TYPE",
    "assert_valid_surface_registry_promotion_candidate_packet",
    "build_surface_registry_promotion_candidate_packet",
    "load_json_packet",
    "validate_surface_registry_promotion_candidate_packet",
]
