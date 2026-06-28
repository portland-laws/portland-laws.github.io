from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from ppd.devhub.read_only_observation_packet import assert_devhub_read_only_observation_packet
from ppd.devhub.surface_registry_update_candidate import assert_valid_surface_registry_update_candidate_packet


REQUIRED_PACKET_TYPE = "ppd.devhub_read_only_surface_drift_comparison_packet.v1"
REQUIRED_MODE = "fixture_first_devhub_read_only_surface_drift_comparison"
REQUIRED_ATTESTATIONS = (
    "no_devhub_launch",
    "no_playwright_launch",
    "no_browser_artifacts",
    "no_registry_mutation",
    "no_active_surface_map_change",
    "no_selector_confidence_upgrade",
    "no_consequential_controls_enabled",
    "no_official_actions_completed",
)
FORBIDDEN_MUTATION_KEYS = {
    "active_surface_map_changed",
    "active_surface_maps_changed",
    "applied_to_registry",
    "applied_to_surface_map",
    "changed_active_surface_map",
    "launches_devhub",
    "launches_playwright",
    "mutates_active_surface_maps",
    "registry_mutated",
    "selector_confidence_upgraded",
    "surface_map_mutated",
    "writes_surface_registry",
}


def load_json_packet(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("packet must be a JSON object")
    return data


def build_read_only_surface_drift_comparison_packet(
    read_only_observation_packet: Mapping[str, Any],
    surface_registry_update_candidate: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a synthetic comparison packet from fixture inputs only."""

    assert_devhub_read_only_observation_packet(read_only_observation_packet)
    assert_valid_surface_registry_update_candidate_packet(surface_registry_update_candidate)

    observation_packet_id = _text(read_only_observation_packet.get("packet_id"))
    candidate_packet_id = _text(surface_registry_update_candidate.get("packet_id"))
    observations = _observations_by_surface(read_only_observation_packet)
    comparisons = []

    for candidate in _sequence(surface_registry_update_candidate.get("registry_update_candidates")):
        if not isinstance(candidate, Mapping):
            continue
        surface_id = _text(candidate.get("surface_id"))
        observation = observations.get(surface_id, {})
        comparisons.append(_comparison_for_surface(candidate, observation, observation_packet_id, candidate_packet_id))

    return {
        "packet_id": "devhub-read-only-surface-drift-comparison-synthetic-v1",
        "packet_type": REQUIRED_PACKET_TYPE,
        "mode": REQUIRED_MODE,
        "fixture_first": True,
        "launches_devhub": False,
        "launches_playwright": False,
        "stores_browser_artifacts": False,
        "writes_surface_registry": False,
        "mutates_active_surface_maps": False,
        "source_packets": {
            "devhub_read_only_observation_packet": {
                "packet_id": observation_packet_id,
                "consumed": True,
            },
            "devhub_surface_registry_update_candidate": {
                "packet_id": candidate_packet_id,
                "consumed": True,
            },
        },
        "surface_comparisons": comparisons,
        "reviewer_owners": [
            {
                "owner": "ppd-devhub-reviewer",
                "owns": ["route_differences", "heading_differences"],
                "reason": "Route and heading drift remain synthetic until attended review cites live evidence.",
            },
            {
                "owner": "ppd-selector-reviewer",
                "owns": ["selector_confidence_notes"],
                "reason": "Selector confidence may be noted but not upgraded from fixture-only comparison.",
            },
            {
                "owner": "ppd-action-guardrail-reviewer",
                "owns": ["action_differences", "unsupported_drift_deferrals"],
                "reason": "Consequential controls remain disabled and any unsupported drift is deferred.",
            },
        ],
        "unsupported_drift_deferrals": _unsupported_deferrals(comparisons, candidate_packet_id),
        "no_registry_mutation_attestations": {name: True for name in REQUIRED_ATTESTATIONS},
    }


def assert_valid_read_only_surface_drift_comparison_packet(packet: Mapping[str, Any]) -> None:
    errors = validate_read_only_surface_drift_comparison_packet(packet)
    if errors:
        raise AssertionError("; ".join(errors))


def validate_read_only_surface_drift_comparison_packet(packet: Mapping[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    _require(errors, packet.get("packet_type") == REQUIRED_PACKET_TYPE, f"packet_type must be {REQUIRED_PACKET_TYPE}")
    _require(errors, packet.get("mode") == REQUIRED_MODE, f"mode must be {REQUIRED_MODE}")
    _require(errors, packet.get("fixture_first") is True, "fixture_first must be true")
    _require(errors, packet.get("launches_devhub") is False, "launches_devhub must be false")
    _require(errors, packet.get("launches_playwright") is False, "launches_playwright must be false")
    _require(errors, packet.get("stores_browser_artifacts") is False, "stores_browser_artifacts must be false")
    _require(errors, packet.get("writes_surface_registry") is False, "writes_surface_registry must be false")
    _require(errors, packet.get("mutates_active_surface_maps") is False, "mutates_active_surface_maps must be false")
    _validate_no_mutation_claims(errors, packet)

    source_packets = _mapping(packet.get("source_packets"))
    for source_name in ("devhub_read_only_observation_packet", "devhub_surface_registry_update_candidate"):
        source = _mapping(source_packets.get(source_name))
        _require(errors, bool(_text(source.get("packet_id"))), f"source_packets.{source_name}.packet_id is required")
        _require(errors, source.get("consumed") is True, f"source_packets.{source_name}.consumed must be true")

    comparisons = _sequence(packet.get("surface_comparisons"))
    _require(errors, bool(comparisons), "surface_comparisons must not be empty")
    for index, comparison in enumerate(comparisons):
        _validate_comparison(errors, _mapping(comparison), f"surface_comparisons[{index}]")

    owners = _sequence(packet.get("reviewer_owners"))
    _require(errors, bool(owners), "reviewer_owners must not be empty")
    for index, owner in enumerate(owners):
        owner_mapping = _mapping(owner)
        _require(errors, bool(_text(owner_mapping.get("owner"))), f"reviewer_owners[{index}].owner is required")
        _require(errors, bool(_sequence(owner_mapping.get("owns"))), f"reviewer_owners[{index}].owns must not be empty")

    deferrals = _sequence(packet.get("unsupported_drift_deferrals"))
    _require(errors, bool(deferrals), "unsupported_drift_deferrals must not be empty")
    for index, deferral in enumerate(deferrals):
        deferral_mapping = _mapping(deferral)
        _require(errors, bool(_text(deferral_mapping.get("surface_id"))), f"unsupported_drift_deferrals[{index}].surface_id is required")
        _require(errors, _text(deferral_mapping.get("resolution")) == "defer_no_registry_mutation", f"unsupported_drift_deferrals[{index}].resolution must defer registry mutation")
        _require(errors, bool(_sequence(deferral_mapping.get("citations"))), f"unsupported_drift_deferrals[{index}].citations must not be empty")

    attestations = _mapping(packet.get("no_registry_mutation_attestations"))
    for name in REQUIRED_ATTESTATIONS:
        _require(errors, attestations.get(name) is True, f"no_registry_mutation_attestations.{name} must be true")

    return _dedupe(errors)


def _comparison_for_surface(
    candidate: Mapping[str, Any],
    observation: Mapping[str, Any],
    observation_packet_id: str,
    candidate_packet_id: str,
) -> dict[str, Any]:
    surface_id = _text(candidate.get("surface_id"))
    observed_route = _text(observation.get("route_pattern"))
    candidate_route = _text(candidate.get("route_pattern"))
    observed_heading = _text(observation.get("redacted_heading"))
    candidate_heading = _text(candidate.get("redacted_heading"))
    citations = [observation_packet_id, candidate_packet_id, surface_id]
    controls = [_text(control) for control in _sequence(candidate.get("disabled_consequential_controls"))]
    selector_delta = _mapping(candidate.get("selector_confidence_delta"))
    return {
        "surface_id": surface_id,
        "citations": citations,
        "route_differences": [
            {
                "field": "route_pattern",
                "observed": observed_route or "not_observed",
                "candidate": candidate_route,
                "status": _difference_status(observed_route, candidate_route),
                "citations": citations,
            }
        ],
        "heading_differences": [
            {
                "field": "redacted_heading",
                "observed": observed_heading or "not_observed",
                "candidate": candidate_heading,
                "status": _difference_status(observed_heading, candidate_heading),
                "citations": citations,
            }
        ],
        "action_differences": [
            {
                "field": "disabled_consequential_controls",
                "observed": _disabled_controls_from_observation(observation),
                "candidate": controls,
                "status": "disabled_controls_attested",
                "citations": citations,
            }
        ],
        "selector_confidence_notes": [
            {
                "previous_confidence": _text(selector_delta.get("previous_confidence")),
                "observed_confidence": _text(selector_delta.get("observed_confidence")),
                "proposed_confidence": _text(selector_delta.get("proposed_confidence")),
                "upgrade_requested": selector_delta.get("upgrade_requested") is True,
                "note": _text(selector_delta.get("delta_reason")) or "No selector-confidence change requested.",
                "citations": citations,
            }
        ],
        "unsupported_drift": _difference_status(observed_route, candidate_route) != "unchanged" or _difference_status(observed_heading, candidate_heading) != "unchanged",
    }


def _observations_by_surface(packet: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    observations = packet.get("observations") or packet.get("observed_surfaces") or packet.get("redacted_observed_surfaces")
    for observation in _sequence(observations):
        if isinstance(observation, Mapping):
            surface_id = _text(observation.get("surface_id"))
            if surface_id:
                result[surface_id] = observation
    return result


def _disabled_controls_from_observation(observation: Mapping[str, Any]) -> list[str]:
    controls = []
    for control in _sequence(observation.get("controls")):
        if not isinstance(control, Mapping):
            continue
        control_id = _text(control.get("control_id"))
        enabled = control.get("enabled") is True or control.get("allowed") is True
        if control_id and not enabled:
            controls.append(f"disabled:{control_id}")
    return controls


def _unsupported_deferrals(comparisons: Sequence[Mapping[str, Any]], candidate_packet_id: str) -> list[dict[str, Any]]:
    deferrals = []
    for comparison in comparisons:
        surface_id = _text(comparison.get("surface_id"))
        if comparison.get("unsupported_drift") is True:
            reason = "Fixture comparison found route or heading drift that requires attended review before registry mutation."
        else:
            reason = "Fixture-only comparison cannot promote active surface maps or selector confidence."
        deferrals.append(
            {
                "surface_id": surface_id,
                "reason": reason,
                "resolution": "defer_no_registry_mutation",
                "citations": [candidate_packet_id, surface_id],
            }
        )
    return deferrals


def _difference_status(observed: str, candidate: str) -> str:
    if not observed:
        return "not_observed"
    if observed == candidate:
        return "unchanged"
    return "synthetic_difference"


def _validate_comparison(errors: list[str], comparison: Mapping[str, Any], path: str) -> None:
    _require(errors, bool(_text(comparison.get("surface_id"))), f"{path}.surface_id is required")
    _require(errors, bool(_sequence(comparison.get("citations"))), f"{path}.citations must not be empty")
    for field_name in ("route_differences", "heading_differences", "action_differences", "selector_confidence_notes"):
        values = _sequence(comparison.get(field_name))
        _require(errors, bool(values), f"{path}.{field_name} must not be empty")
        for index, value in enumerate(values):
            value_mapping = _mapping(value)
            _require(errors, bool(_sequence(value_mapping.get("citations"))), f"{path}.{field_name}[{index}].citations must not be empty")
    for index, note in enumerate(_sequence(comparison.get("selector_confidence_notes"))):
        note_mapping = _mapping(note)
        _require(errors, note_mapping.get("upgrade_requested") is False, f"{path}.selector_confidence_notes[{index}].upgrade_requested must be false")
        _require(errors, _text(note_mapping.get("proposed_confidence")) == "attended_review_required", f"{path}.selector_confidence_notes[{index}].proposed_confidence must require attended review")


def _validate_no_mutation_claims(errors: list[str], value: Any, path: str = "packet") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = _text(key)
            nested_path = f"{path}.{key_text}"
            if key_text.lower() in FORBIDDEN_MUTATION_KEYS and nested is not False:
                errors.append(f"{nested_path} must not claim DevHub launch, registry mutation, or active surface map changes")
            _validate_no_mutation_claims(errors, nested, nested_path)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            _validate_no_mutation_claims(errors, item, f"{path}[{index}]")


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
