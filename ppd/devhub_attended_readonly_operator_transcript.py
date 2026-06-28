"""Fixture-first DevHub attended read-only pilot operator transcript packet.

This module intentionally performs no browser automation, authentication, screenshotting,
tracing, network access, or official DevHub action. It transforms a committed launch
readiness fixture into a deterministic simulated operator transcript packet.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

REQUIRED_ATTESTATIONS = (
    "no_browser_launched",
    "no_auth_state_created_or_read",
    "no_private_devhub_data_read",
    "no_screenshots_captured",
    "no_traces_captured",
    "no_downloads_created",
    "no_official_action_taken",
)


def _require_mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be a mapping")
    return value


def _require_list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    return value


def _validate_attestations(attestations: Mapping[str, Any]) -> dict[str, bool]:
    normalized: dict[str, bool] = {}
    for key in REQUIRED_ATTESTATIONS:
        if attestations.get(key) is not True:
            raise ValueError(f"required attestation missing or false: {key}")
        normalized[key] = True
    return normalized


def build_operator_transcript_packet(launch_readiness_packet: Mapping[str, Any]) -> dict[str, Any]:
    """Build a deterministic simulated operator transcript from readiness data."""

    packet = _require_mapping(launch_readiness_packet, "launch_readiness_packet")
    attestations = _validate_attestations(
        _require_mapping(packet.get("guardrail_attestations"), "guardrail_attestations")
    )
    reviewer_owner_fields = dict(
        _require_mapping(packet.get("reviewer_owner_fields"), "reviewer_owner_fields")
    )
    checkpoints = _require_list(
        packet.get("manual_user_attendance_checkpoints"),
        "manual_user_attendance_checkpoints",
    )
    page_states = _require_list(
        packet.get("redacted_page_state_summaries"),
        "redacted_page_state_summaries",
    )
    selector_confirmations = _require_list(
        packet.get("selector_confidence_confirmations"),
        "selector_confidence_confirmations",
    )

    observations: list[dict[str, Any]] = []
    sequence = 1
    for checkpoint in checkpoints:
        checkpoint_map = _require_mapping(checkpoint, "manual_user_attendance_checkpoints[]")
        observations.append(
            {
                "sequence": sequence,
                "kind": "manual_user_attendance_checkpoint",
                "checkpoint_id": checkpoint_map["checkpoint_id"],
                "operator_observation": checkpoint_map["operator_observation"],
                "requires_live_user_presence": True,
                "simulated_only": True,
            }
        )
        sequence += 1

    for page_state in page_states:
        page_state_map = _require_mapping(page_state, "redacted_page_state_summaries[]")
        observations.append(
            {
                "sequence": sequence,
                "kind": "redacted_page_state_summary",
                "page_state_id": page_state_map["page_state_id"],
                "page_label": page_state_map["page_label"],
                "redacted_summary": page_state_map["redacted_summary"],
                "redactions_applied": list(page_state_map.get("redactions_applied", [])),
                "contains_private_devhub_data": False,
                "simulated_only": True,
            }
        )
        sequence += 1

    for confirmation in selector_confirmations:
        confirmation_map = _require_mapping(
            confirmation,
            "selector_confidence_confirmations[]",
        )
        observations.append(
            {
                "sequence": sequence,
                "kind": "selector_confidence_confirmation",
                "selector_id": confirmation_map["selector_id"],
                "confidence": confirmation_map["confidence"],
                "basis": confirmation_map["basis"],
                "requires_live_verification_before_use": True,
                "simulated_only": True,
            }
        )
        sequence += 1

    return {
        "packet_type": "devhub_attended_readonly_pilot_operator_transcript_packet",
        "packet_version": 1,
        "source_packet_type": packet.get("packet_type"),
        "source_packet_id": packet.get("packet_id"),
        "pilot_id": packet.get("pilot_id"),
        "mode": "fixture_first_attended_readonly_simulation",
        "reviewer_owner_fields": reviewer_owner_fields,
        "ordered_operator_observations": observations,
        "guardrail_attestations": attestations,
        "prohibited_artifacts": {
            "browser_sessions": [],
            "auth_state_files": [],
            "screenshots": [],
            "traces": [],
            "raw_crawl_outputs": [],
            "downloaded_documents": [],
        },
        "source_launch_readiness_packet": deepcopy(dict(packet)),
    }


def validate_operator_transcript_packet(packet: Mapping[str, Any]) -> None:
    """Validate the narrow contract required by the attended read-only pilot."""

    transcript = _require_mapping(packet, "packet")
    if transcript.get("packet_type") != "devhub_attended_readonly_pilot_operator_transcript_packet":
        raise ValueError("unexpected transcript packet_type")
    _validate_attestations(
        _require_mapping(transcript.get("guardrail_attestations"), "guardrail_attestations")
    )
    observations = _require_list(
        transcript.get("ordered_operator_observations"),
        "ordered_operator_observations",
    )
    expected_sequence = list(range(1, len(observations) + 1))
    actual_sequence = [obs.get("sequence") for obs in observations if isinstance(obs, Mapping)]
    if actual_sequence != expected_sequence:
        raise ValueError("operator observations must be ordered with contiguous sequence values")
    for observation in observations:
        observation_map = _require_mapping(observation, "ordered_operator_observations[]")
        if observation_map.get("simulated_only") is not True:
            raise ValueError("each observation must be marked simulated_only")
