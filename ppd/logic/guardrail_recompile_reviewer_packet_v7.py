"""Fixture-first guardrail recompile reviewer packet v7.

This module consumes only inactive guardrail recompile staging packet v7
fixtures and assembles deterministic reviewer packet rows. It does not activate
guardrails, crawl live sites, open DevHub, read private documents, upload,
submit, certify, pay, schedule, or provide legal/permitting guarantees.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

from ppd.logic.inactive_guardrail_recompile_staging_packet_v7 import (
    validate_inactive_guardrail_recompile_staging_packet_v7,
)

PACKET_TYPE = "ppd.guardrail_recompile_reviewer_packet.v7"
PACKET_VERSION = "v7"
PACKET_MODE = "fixture_first_inactive_guardrail_recompile_review_only"
EXPECTED_VALIDATION_COMMANDS = [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]]

FALSE_ATTESTATIONS = (
    "guardrails_activated",
    "live_crawl_executed",
    "devhub_opened",
    "private_documents_read",
    "uploads_attempted",
    "submissions_attempted",
    "certifications_attempted",
    "payments_attempted",
    "inspection_scheduling_attempted",
    "legal_or_permitting_guarantee",
)


@dataclass(frozen=True)
class ReviewerPacketV7Finding:
    code: str
    path: str
    message: str


class ReviewerPacketV7Error(ValueError):
    """Raised when a guardrail recompile reviewer packet v7 is invalid."""


def load_inactive_guardrail_recompile_staging_packet_v7_fixture(path: str | Path) -> dict[str, Any]:
    """Load and validate an inactive staging packet v7 fixture."""

    fixture_path = Path(path)
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ReviewerPacketV7Error("inactive guardrail recompile staging packet v7 fixture must be an object")
    validate_inactive_guardrail_recompile_staging_packet_v7(payload)
    return payload


def build_guardrail_recompile_reviewer_packet_v7_from_fixture(path: str | Path) -> dict[str, Any]:
    """Build reviewer packet v7 from one committed staging packet fixture."""

    fixture_path = Path(path)
    staging_packet = load_inactive_guardrail_recompile_staging_packet_v7_fixture(fixture_path)
    return build_guardrail_recompile_reviewer_packet_v7(
        staging_packet,
        staging_fixture_ref=fixture_path.name,
    )


def build_guardrail_recompile_reviewer_packet_v7(
    staging_packet: Mapping[str, Any],
    *,
    staging_fixture_ref: str = "inactive_guardrail_recompile_staging_packet_v7.json",
) -> dict[str, Any]:
    """Assemble a deterministic reviewer packet from an inactive staging packet."""

    validate_inactive_guardrail_recompile_staging_packet_v7(staging_packet)
    affected_rows = _required_mapping_list(staging_packet, "affected_guardrail_bundle_rows")
    predicate_rows = _required_mapping_list(staging_packet, "deterministic_predicate_change_placeholders")
    stale_rows = _required_mapping_list(staging_packet, "stale_evidence_hold_propagation_rows")
    rollback_rows = _required_mapping_list(staging_packet, "rollback_checkpoint_placeholders")
    signoff_rows = _required_mapping_list(staging_packet, "reviewer_signoff_placeholders")

    staging_packet_id = _required_text(staging_packet, "packet_id")
    packet = {
        "packet_type": PACKET_TYPE,
        "packet_version": PACKET_VERSION,
        "packet_id": "guardrail-recompile-reviewer-v7-" + _stable_hash(
            {"staging_packet_id": staging_packet_id, "fixture_ref": staging_fixture_ref}
        ),
        "mode": PACKET_MODE,
        "fixture_first": True,
        "inactive_only": True,
        "consumes_only_inactive_guardrail_recompile_staging_packet_v7_fixtures": True,
        "staging_packet_references": [
            {
                "fixture_ref": staging_fixture_ref,
                "packet_id": staging_packet_id,
                "source_queue_ref": _required_text(staging_packet, "source_queue_ref"),
                "reference_status": "inactive_staging_fixture_validated_offline",
            }
        ],
        "reviewer_comparison_rows": _comparison_rows(affected_rows, predicate_rows),
        "inactive_guardrail_status_notes": _inactive_status_notes(affected_rows),
        "source_evidence_continuity_checks": _source_evidence_continuity_checks(staging_packet),
        "deterministic_predicate_review_prompts": _predicate_review_prompts(predicate_rows),
        "exact_confirmation_preservation_summaries": _preservation_summaries(
            staging_packet,
            "exact_confirmation_gate_preservation_notes",
            "exact_confirmation_preservation",
        ),
        "refused_action_preservation_summaries": _preservation_summaries(
            staging_packet,
            "refused_action_gate_preservation_notes",
            "refused_action_preservation",
        ),
        "stale_evidence_hold_carry_forward_rows": _stale_hold_carry_forward_rows(stale_rows),
        "rollback_readiness_notes": _rollback_readiness_notes(rollback_rows),
        "signoff_owner_placeholders": _signoff_owner_placeholders(signoff_rows),
        "validation_commands": EXPECTED_VALIDATION_COMMANDS,
        "attestations": {flag: False for flag in FALSE_ATTESTATIONS},
        "activation_allowed": False,
    }
    validate_guardrail_recompile_reviewer_packet_v7(packet)
    return packet


def validate_guardrail_recompile_reviewer_packet_v7(packet: Mapping[str, Any]) -> None:
    """Raise when reviewer packet v7 is not fixture-first and review-only."""

    findings = collect_guardrail_recompile_reviewer_packet_v7_findings(packet)
    if findings:
        detail = "; ".join(f"{finding.path}: {finding.message}" for finding in findings)
        raise ReviewerPacketV7Error("guardrail recompile reviewer packet v7 is invalid: " + detail)


def collect_guardrail_recompile_reviewer_packet_v7_findings(packet: Mapping[str, Any]) -> list[ReviewerPacketV7Finding]:
    """Return deterministic reviewer packet validation findings."""

    findings: list[ReviewerPacketV7Finding] = []
    if not isinstance(packet, Mapping):
        return [ReviewerPacketV7Finding("invalid_packet", "$", "packet must be an object")]

    expected_scalars = {
        "packet_type": PACKET_TYPE,
        "packet_version": PACKET_VERSION,
        "mode": PACKET_MODE,
        "fixture_first": True,
        "inactive_only": True,
        "consumes_only_inactive_guardrail_recompile_staging_packet_v7_fixtures": True,
        "activation_allowed": False,
    }
    for key, expected in expected_scalars.items():
        if packet.get(key) != expected:
            findings.append(ReviewerPacketV7Finding("invalid_packet_field", f"$.{key}", f"{key} must be {expected!r}"))

    if packet.get("validation_commands") != EXPECTED_VALIDATION_COMMANDS:
        findings.append(
            ReviewerPacketV7Finding(
                "invalid_validation_commands",
                "$.validation_commands",
                "validation_commands must contain only the exact offline daemon self-test command",
            )
        )

    for key in (
        "packet_id",
        "staging_packet_references",
        "reviewer_comparison_rows",
        "inactive_guardrail_status_notes",
        "source_evidence_continuity_checks",
        "deterministic_predicate_review_prompts",
        "exact_confirmation_preservation_summaries",
        "refused_action_preservation_summaries",
        "stale_evidence_hold_carry_forward_rows",
        "rollback_readiness_notes",
        "signoff_owner_placeholders",
    ):
        if _is_missing(packet.get(key)):
            findings.append(ReviewerPacketV7Finding("missing_required_field", f"$.{key}", f"{key} is required"))

    attestations = packet.get("attestations")
    if not isinstance(attestations, Mapping):
        findings.append(ReviewerPacketV7Finding("missing_attestations", "$.attestations", "attestations are required"))
    else:
        for flag in FALSE_ATTESTATIONS:
            if attestations.get(flag) is not False:
                findings.append(ReviewerPacketV7Finding("attestation_not_false", f"$.attestations.{flag}", f"{flag} must be false"))

    _validate_row_activation_false(packet, findings)
    return findings


def _comparison_rows(affected_rows: Sequence[Mapping[str, Any]], predicate_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    predicate_count_by_bundle: dict[str, int] = {}
    for predicate in predicate_rows:
        bundle_id = _text(predicate.get("guardrail_bundle_id")) or "unassigned"
        predicate_count_by_bundle[bundle_id] = predicate_count_by_bundle.get(bundle_id, 0) + 1
    fallback_count = len(predicate_rows)
    rows = []
    for index, row in enumerate(affected_rows):
        bundle_id = _required_text(row, "guardrail_bundle_id")
        rows.append(
            {
                "comparison_row_id": f"reviewer-comparison:v7:{index + 1:02d}",
                "guardrail_bundle_id": bundle_id,
                "process_id": _required_text(row, "process_id"),
                "permit_type": _required_text(row, "permit_type"),
                "staging_status": _required_text(row, "staging_status"),
                "reviewer_packet_status": "inactive_review_only_pending_owner_signoff",
                "predicate_placeholder_count": predicate_count_by_bundle.get(bundle_id, fallback_count),
                "comparison_prompt": "Compare inactive staging placeholders to existing inactive guardrail behavior before any activation decision.",
                "activation_allowed": False,
            }
        )
    return rows


def _inactive_status_notes(affected_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "note_id": f"inactive-status:v7:{_required_text(row, 'guardrail_bundle_id')}",
            "guardrail_bundle_id": _required_text(row, "guardrail_bundle_id"),
            "status_note": "Inactive guardrail status is unchanged; reviewer packet is comparison-only.",
            "activation_allowed": False,
        }
        for row in affected_rows
    ]


def _source_evidence_continuity_checks(staging_packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    checks = []
    for field in (
        "deterministic_predicate_change_placeholders",
        "deontic_rule_review_placeholders",
        "temporal_rule_review_placeholders",
        "stale_evidence_hold_propagation_rows",
    ):
        for index, row in enumerate(_required_mapping_list(staging_packet, field)):
            checks.append(
                {
                    "check_id": f"source-continuity:v7:{field}:{index + 1}",
                    "source_staging_field": field,
                    "source_ref": _source_ref(row, index),
                    "continuity_status": "source_ref_carried_forward_for_reviewer_confirmation",
                    "activation_allowed": False,
                }
            )
    return checks


def _predicate_review_prompts(predicate_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    prompts = []
    for index, row in enumerate(predicate_rows):
        predicate_family = _required_text(row, "predicate_family")
        prompts.append(
            {
                "prompt_id": f"predicate-review:v7:{index + 1:02d}",
                "predicate_family": predicate_family,
                "source_ref": _source_ref(row, index),
                "review_prompt": "Confirm the deterministic predicate placeholder is still supported by cited public evidence and keeps inactive gates unchanged.",
                "activation_allowed": False,
            }
        )
    return prompts


def _preservation_summaries(staging_packet: Mapping[str, Any], field: str, summary_type: str) -> list[dict[str, Any]]:
    summaries = []
    for index, row in enumerate(_required_mapping_list(staging_packet, field)):
        summaries.append(
            {
                "summary_id": f"{summary_type}:v7:{index + 1:02d}",
                "guardrail_bundle_id": _required_text(row, "guardrail_bundle_id"),
                "process_id": _required_text(row, "process_id"),
                "source_note_id": _required_text(row, "note_id"),
                "preservation_status": "preserve_gate_behavior_pending_reviewer_signoff",
                "activation_allowed": False,
            }
        )
    return summaries


def _stale_hold_carry_forward_rows(stale_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(stale_rows):
        rows.append(
            {
                "carry_forward_id": f"stale-hold-carry-forward:v7:{index + 1:02d}",
                "source_hold_id": _required_text(row, "hold_id"),
                "carry_forward_status": "hold_remains_active_until_source_evidence_review",
                "guardrail_activation_blocked_until_review": row.get("guardrail_activation_blocked_until_review") is True,
                "activation_allowed": False,
            }
        )
    return rows


def _rollback_readiness_notes(rollback_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "rollback_readiness_id": f"rollback-readiness:v7:{index + 1:02d}",
            "rollback_checkpoint_id": _required_text(row, "rollback_checkpoint_id"),
            "guardrail_bundle_id": _required_text(row, "guardrail_bundle_id"),
            "readiness_note": "Reviewer must confirm inactive bundle snapshot and rollback owner before any later activation path.",
            "activation_allowed": False,
        }
        for index, row in enumerate(rollback_rows)
    ]


def _signoff_owner_placeholders(signoff_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    placeholders = []
    for index, row in enumerate(signoff_rows):
        placeholders.append(
            {
                "owner_placeholder_id": f"signoff-owner:v7:{index + 1:02d}",
                "source_signoff_id": _required_text(row, "signoff_id"),
                "review_status": _required_text(row, "review_status"),
                "owner_placeholder": "unassigned_reviewer_owner_required_before_activation_review",
                "activation_allowed": False,
            }
        )
    return placeholders


def _validate_row_activation_false(packet: Mapping[str, Any], findings: list[ReviewerPacketV7Finding]) -> None:
    for row_field in (
        "reviewer_comparison_rows",
        "inactive_guardrail_status_notes",
        "source_evidence_continuity_checks",
        "deterministic_predicate_review_prompts",
        "exact_confirmation_preservation_summaries",
        "refused_action_preservation_summaries",
        "stale_evidence_hold_carry_forward_rows",
        "rollback_readiness_notes",
        "signoff_owner_placeholders",
    ):
        rows = packet.get(row_field)
        if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
            continue
        for index, row in enumerate(rows):
            if isinstance(row, Mapping) and row.get("activation_allowed") is not False:
                findings.append(
                    ReviewerPacketV7Finding(
                        "row_activation_not_false",
                        f"$.{row_field}[{index}].activation_allowed",
                        "reviewer rows must keep activation_allowed false",
                    )
                )


def _required_mapping_list(row: Mapping[str, Any], key: str) -> list[Mapping[str, Any]]:
    value = row.get(key)
    if not isinstance(value, list) or not value:
        raise ReviewerPacketV7Error(f"{key} must be a non-empty list")
    if not all(isinstance(item, Mapping) for item in value):
        raise ReviewerPacketV7Error(f"{key} must contain only objects")
    return value


def _required_text(row: Mapping[str, Any], key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ReviewerPacketV7Error(f"{key} must be a non-empty string")
    return value


def _source_ref(item: Mapping[str, Any], index: int) -> str:
    for key in ("placeholder_id", "hold_id", "signoff_id", "suggestion_id", "note_id", "row_id", "ref"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return "source-row:" + str(index + 1)


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, Mapping):
        return not value
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return len(value) == 0
    return False


def _stable_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]
