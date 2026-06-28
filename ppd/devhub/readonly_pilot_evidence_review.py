"""Fixture-first DevHub read-only pilot evidence review packets.

This module consumes already-redacted, synthetic pilot evidence. It performs no
browser automation and rejects private browser/session artifacts by contract.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PRIVATE_ARTIFACT_NAMES = {
    "auth_state",
    "cookies",
    "har_files",
    "raw_authenticated_values",
    "screenshots",
    "session_storage",
    "traces",
}

SAFE_REDACTION_STATES = {"redacted", "synthetic", "absent"}


def load_json_fixture(path: Path) -> dict[str, Any]:
    """Load one JSON fixture object from a test-local path."""

    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"fixture must contain a JSON object: {path}")
    return payload


def build_readonly_pilot_evidence_review_packet(
    runbook_candidate: dict[str, Any],
    redacted_observation_packet: dict[str, Any],
    surface_drift_comparison_packet: dict[str, Any],
) -> dict[str, Any]:
    """Build a deterministic read-only review packet from redacted fixtures."""

    _validate_no_private_artifacts(redacted_observation_packet)

    pilot_id = _same_pilot_id(
        runbook_candidate,
        redacted_observation_packet,
        surface_drift_comparison_packet,
    )
    observed_surfaces = _list(redacted_observation_packet.get("observed_surfaces"))
    drift_by_surface = {
        str(item.get("surface_id")): item
        for item in _list(surface_drift_comparison_packet.get("surface_diffs"))
    }

    findings = []
    selector_notes = []
    redaction_attestations = []
    registry_refs = []

    for surface in observed_surfaces:
        surface_id = str(surface.get("surface_id"))
        drift = drift_by_surface.get(surface_id, {})
        finding = _surface_finding(surface, drift, runbook_candidate, redacted_observation_packet, surface_drift_comparison_packet)
        findings.append(finding)
        selector_notes.extend(_selector_confidence_notes(surface, drift))
        redaction_attestations.append(_redaction_attestation(surface))
        ref = drift.get("candidate_registry_ref") or surface.get("registry_candidate_ref")
        if ref:
            registry_refs.append(
                {
                    "surface_id": surface_id,
                    "candidate_registry_ref": str(ref),
                    "evidence_ids": [
                        str(surface_drift_comparison_packet.get("comparison_id")),
                        str(redacted_observation_packet.get("observation_id")),
                    ],
                }
            )

    return {
        "packet_id": f"readonly-pilot-review-{pilot_id}",
        "pilot_id": pilot_id,
        "review_mode": "fixture_first_read_only",
        "browser_launched": False,
        "private_artifacts_persisted": False,
        "consumed_packets": {
            "runbook_candidate_id": str(runbook_candidate.get("runbook_candidate_id")),
            "observation_id": str(redacted_observation_packet.get("observation_id")),
            "surface_drift_comparison_id": str(surface_drift_comparison_packet.get("comparison_id")),
        },
        "synthetic_surface_review_findings": findings,
        "selector_confidence_notes": selector_notes,
        "redaction_attestations": redaction_attestations,
        "manual_handoff_checkpoints": _manual_handoff_checkpoints(runbook_candidate, findings),
        "surface_registry_candidate_references": registry_refs,
        "refused_artifacts": sorted(PRIVATE_ARTIFACT_NAMES),
    }


def _same_pilot_id(*packets: dict[str, Any]) -> str:
    pilot_ids = {str(packet.get("pilot_id")) for packet in packets if packet.get("pilot_id")}
    if len(pilot_ids) != 1:
        raise ValueError(f"expected exactly one pilot_id across packets, got {sorted(pilot_ids)}")
    return next(iter(pilot_ids))


def _validate_no_private_artifacts(packet: dict[str, Any]) -> None:
    if packet.get("browser_launched") is True:
        raise ValueError("read-only evidence review cannot launch a browser")
    if packet.get("raw_authenticated_values_present") is True:
        raise ValueError("raw authenticated values are not allowed in review evidence")

    artifacts = packet.get("captured_artifacts", {})
    if not isinstance(artifacts, dict):
        raise ValueError("captured_artifacts must be an object")
    for name in PRIVATE_ARTIFACT_NAMES:
        value = artifacts.get(name)
        if value not in (None, False, [], {}, ""):
            raise ValueError(f"private artifact is not allowed: {name}")


def _surface_finding(
    surface: dict[str, Any],
    drift: dict[str, Any],
    runbook: dict[str, Any],
    observation: dict[str, Any],
    comparison: dict[str, Any],
) -> dict[str, Any]:
    surface_id = str(surface.get("surface_id"))
    drift_status = str(drift.get("status", "missing_drift_evidence"))
    allowed_actions = set(_list(runbook.get("allowed_actions")))
    observed_actions = {str(action.get("action_id")) for action in _list(surface.get("actions"))}
    unsafe_actions = sorted(observed_actions - allowed_actions)
    return {
        "finding_id": f"finding-{surface_id}",
        "surface_id": surface_id,
        "review_status": "manual_review_required" if drift_status != "matched" or unsafe_actions else "accepted_read_only",
        "drift_status": drift_status,
        "unsafe_action_ids": unsafe_actions,
        "summary": str(drift.get("summary", "Observed read-only surface matched fixture evidence.")),
        "evidence_ids": [
            str(runbook.get("runbook_candidate_id")),
            str(observation.get("observation_id")),
            str(comparison.get("comparison_id")),
        ],
    }


def _selector_confidence_notes(surface: dict[str, Any], drift: dict[str, Any]) -> list[dict[str, Any]]:
    notes = []
    drift_status = str(drift.get("status", "missing_drift_evidence"))
    for selector in _list(surface.get("selector_evidence")):
        confidence = float(selector.get("confidence", 0.0))
        if confidence >= 0.8 and drift_status == "matched":
            band = "stable_candidate"
        elif confidence >= 0.55:
            band = "needs_follow_up"
        else:
            band = "manual_handoff_only"
        notes.append(
            {
                "surface_id": str(surface.get("surface_id")),
                "selector_name": str(selector.get("name")),
                "confidence": confidence,
                "confidence_band": band,
                "selectors": [str(item) for item in _list(selector.get("selectors"))],
                "note": str(selector.get("rationale", "Synthetic selector evidence only.")),
            }
        )
    return notes


def _redaction_attestation(surface: dict[str, Any]) -> dict[str, Any]:
    fields = _list(surface.get("fields"))
    unsafe_fields = [
        str(field.get("field_id"))
        for field in fields
        if str(field.get("redaction_state")) not in SAFE_REDACTION_STATES
    ]
    return {
        "surface_id": str(surface.get("surface_id")),
        "field_count": len(fields),
        "attestation_status": "passes" if not unsafe_fields else "fails",
        "unsafe_field_ids": unsafe_fields,
        "raw_authenticated_values_present": False,
    }


def _manual_handoff_checkpoints(runbook: dict[str, Any], findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checkpoints = []
    for checkpoint in _list(runbook.get("manual_handoff_checkpoints")):
        checkpoints.append(
            {
                "checkpoint_id": str(checkpoint.get("checkpoint_id")),
                "trigger": str(checkpoint.get("trigger")),
                "required_operator_action": str(checkpoint.get("required_operator_action")),
            }
        )
    for finding in findings:
        if finding["review_status"] != "accepted_read_only":
            checkpoints.append(
                {
                    "checkpoint_id": f"handoff-{finding['surface_id']}",
                    "trigger": f"surface_review:{finding['review_status']}",
                    "required_operator_action": "Review synthetic drift finding before promoting selectors or registry candidates.",
                }
            )
    return checkpoints


def _list(value: Any) -> list[Any]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("expected list value")
    return value


__all__ = [
    "PRIVATE_ARTIFACT_NAMES",
    "build_readonly_pilot_evidence_review_packet",
    "load_json_fixture",
]
