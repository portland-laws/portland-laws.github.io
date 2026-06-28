"""Fixture-first inactive guardrail recompile staging packet v7.

This module consumes only committed process model refresh impact queue v7
fixtures and assembles reviewer-facing GuardrailBundle recompile staging rows.
It does not compile, activate, promote, crawl, open DevHub, read private
artifacts, upload, submit, certify, pay, schedule, or provide legal/permitting
guarantees.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

from ppd.logic.process_model_refresh_impact_queue_v7_validation import (
    QueueValidationIssue,
    validate_process_model_refresh_impact_queue_v7,
)

PACKET_TYPE = "ppd.inactive_guardrail_recompile_staging_packet.v7"
PACKET_VERSION = "v7"
PACKET_MODE = "fixture_first_inactive_recompile_staging_only"
SOURCE_QUEUE_VERSION = "process_model_refresh_impact_queue_v7"
EXPECTED_VALIDATION_COMMANDS = [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]]

FALSE_ATTESTATIONS = (
    "guardrails_activated",
    "guardrails_compiled",
    "guardrails_promoted",
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

PROHIBITED_KEYS = frozenset(
    {
        "access_token",
        "auth_state",
        "browser_state",
        "cookie",
        "cookies",
        "credential",
        "credentials",
        "downloaded_artifact",
        "downloaded_document",
        "har",
        "local_private_path",
        "password",
        "private_document",
        "raw_body",
        "raw_crawl_artifact",
        "raw_html",
        "raw_pdf",
        "screenshot",
        "session",
        "session_id",
        "storage_state",
        "trace",
    }
)

PROHIBITED_PHRASES = tuple(
    sorted(
        {
            "activated guardrails",
            "application submitted",
            "approval guaranteed",
            "certification completed",
            "compiled guardrails",
            "devhub opened",
            "downloaded document",
            "executed live crawl",
            "guardrails activated",
            "guardrails compiled",
            "guaranteed approval",
            "inspection scheduled",
            "legal advice",
            "live crawl executed",
            "official action completed",
            "payment completed",
            "permit guaranteed",
            "private document read",
            "raw crawl artifact",
            "submitted to city",
            "upload completed",
            "will be approved",
            "will pass inspection",
        }
    )
)


@dataclass(frozen=True)
class GuardrailRecompileStagingFinding:
    code: str
    path: str
    message: str


class GuardrailRecompileStagingError(ValueError):
    """Raised when an inactive guardrail recompile staging packet is invalid."""


def load_process_model_refresh_impact_queue_v7_fixture(path: str | Path) -> dict[str, Any]:
    """Load and validate a process model refresh impact queue v7 fixture."""

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise GuardrailRecompileStagingError("process model refresh impact queue v7 fixture must be an object")
    _assert_valid_source_queue(payload)
    return payload


def build_inactive_guardrail_recompile_staging_packet_v7_from_fixture(path: str | Path) -> dict[str, Any]:
    """Build a deterministic inactive recompile staging packet from one queue fixture."""

    queue = load_process_model_refresh_impact_queue_v7_fixture(path)
    return build_inactive_guardrail_recompile_staging_packet_v7(queue)


def build_inactive_guardrail_recompile_staging_packet_v7(queue: Mapping[str, Any]) -> dict[str, Any]:
    """Assemble reviewer-only GuardrailBundle recompile staging rows from a v7 queue."""

    _assert_valid_source_queue(queue)
    process_rows = _required_mapping_list(queue, "affected_process_model_rows")
    guardrail_rows = [_guardrail_bundle_row(row) for row in process_rows]
    affected_bundle_ids = _sorted_unique(row["guardrail_bundle_id"] for row in guardrail_rows)
    affected_process_ids = _sorted_unique(row["process_id"] for row in guardrail_rows)
    source_queue_ref = str(queue.get("queue_id") or _stable_hash(queue))

    packet = {
        "packet_type": PACKET_TYPE,
        "packet_version": PACKET_VERSION,
        "packet_id": "inactive-guardrail-recompile-staging-v7-" + _stable_hash(
            {"source_queue_ref": source_queue_ref, "affected_bundle_ids": affected_bundle_ids}
        ),
        "mode": PACKET_MODE,
        "fixture_first": True,
        "inactive_only": True,
        "consumes_only_process_model_refresh_impact_queue_v7_fixtures": True,
        "source_queue_ref": source_queue_ref,
        "affected_guardrail_bundle_rows": guardrail_rows,
        "deterministic_predicate_change_placeholders": _predicate_placeholders(queue),
        "deontic_rule_review_placeholders": _review_placeholders(
            queue,
            "guardrail_bundle_recompile_suggestions",
            "deontic_rule_review_placeholder",
        ),
        "temporal_rule_review_placeholders": _review_placeholders(
            queue,
            "deadline_impact_placeholders",
            "temporal_rule_review_placeholder",
        ),
        "reversible_action_predicate_preservation_notes": _preservation_notes(
            guardrail_rows,
            "reversible_action_predicates",
            "Keep reversible draft predicates inactive and preserve citation links until reviewer approval.",
        ),
        "exact_confirmation_gate_preservation_notes": _preservation_notes(
            guardrail_rows,
            "exact_confirmation_predicates",
            "Preserve exact-confirmation gates for upload, submission, certification, payment, scheduling, and cancellation boundaries.",
        ),
        "refused_action_gate_preservation_notes": _preservation_notes(
            guardrail_rows,
            "refused_action_predicates",
            "Preserve refused-action gates for unsupported, consequential, private, or stale-evidence actions.",
        ),
        "stale_evidence_hold_propagation_rows": _stale_evidence_rows(queue),
        "rollback_checkpoint_placeholders": _rollback_rows(guardrail_rows),
        "reviewer_signoff_placeholders": _reviewer_signoff_rows(queue),
        "validation_commands": EXPECTED_VALIDATION_COMMANDS,
        "attestations": {flag: False for flag in FALSE_ATTESTATIONS},
        "activation_allowed": False,
    }
    validate_inactive_guardrail_recompile_staging_packet_v7(packet)
    return packet


def validate_inactive_guardrail_recompile_staging_packet_v7(packet: Mapping[str, Any]) -> None:
    """Raise when the inactive recompile staging packet is not commit-safe."""

    findings = collect_inactive_guardrail_recompile_staging_packet_v7_findings(packet)
    if findings:
        detail = "; ".join(f"{finding.path}: {finding.message}" for finding in findings)
        raise GuardrailRecompileStagingError("inactive guardrail recompile staging packet v7 is invalid: " + detail)


def collect_inactive_guardrail_recompile_staging_packet_v7_findings(
    packet: Mapping[str, Any],
) -> list[GuardrailRecompileStagingFinding]:
    """Return deterministic findings for a staging packet."""

    findings: list[GuardrailRecompileStagingFinding] = []
    if not isinstance(packet, Mapping):
        return [GuardrailRecompileStagingFinding("invalid_packet", "$", "packet must be an object")]
    _reject_prohibited_content(packet, "$", findings)

    expected_scalars = {
        "packet_type": PACKET_TYPE,
        "packet_version": PACKET_VERSION,
        "mode": PACKET_MODE,
        "fixture_first": True,
        "inactive_only": True,
        "consumes_only_process_model_refresh_impact_queue_v7_fixtures": True,
        "activation_allowed": False,
    }
    for key, expected in expected_scalars.items():
        if packet.get(key) != expected:
            findings.append(GuardrailRecompileStagingFinding("invalid_packet_field", f"$.{key}", f"{key} must be {expected!r}"))

    for key in (
        "source_queue_ref",
        "packet_id",
    ):
        if not _non_empty_text(packet.get(key)):
            findings.append(GuardrailRecompileStagingFinding("missing_text_field", f"$.{key}", f"{key} is required"))

    for key in (
        "affected_guardrail_bundle_rows",
        "deterministic_predicate_change_placeholders",
        "deontic_rule_review_placeholders",
        "temporal_rule_review_placeholders",
        "reversible_action_predicate_preservation_notes",
        "exact_confirmation_gate_preservation_notes",
        "refused_action_gate_preservation_notes",
        "stale_evidence_hold_propagation_rows",
        "rollback_checkpoint_placeholders",
        "reviewer_signoff_placeholders",
    ):
        if not _non_empty_mapping_list(packet.get(key)):
            findings.append(GuardrailRecompileStagingFinding("missing_required_rows", f"$.{key}", f"{key} must contain rows"))

    if packet.get("validation_commands") != EXPECTED_VALIDATION_COMMANDS:
        findings.append(
            GuardrailRecompileStagingFinding(
                "invalid_validation_commands",
                "$.validation_commands",
                "validation_commands must contain only the exact offline daemon self-test command",
            )
        )

    attestations = packet.get("attestations")
    if not isinstance(attestations, Mapping):
        findings.append(GuardrailRecompileStagingFinding("missing_attestations", "$.attestations", "attestations are required"))
    else:
        for flag in FALSE_ATTESTATIONS:
            if attestations.get(flag) is not False:
                findings.append(
                    GuardrailRecompileStagingFinding(
                        "attestation_not_false",
                        f"$.attestations.{flag}",
                        f"{flag} must be false",
                    )
                )

    _validate_row_activation_false(packet, findings)
    return findings


def _assert_valid_source_queue(queue: Mapping[str, Any]) -> None:
    issues = validate_process_model_refresh_impact_queue_v7(queue)
    if issues:
        detail = "; ".join(_format_queue_issue(issue) for issue in issues)
        raise GuardrailRecompileStagingError("invalid process model refresh impact queue v7 fixture: " + detail)
    if queue.get("queue_version") != SOURCE_QUEUE_VERSION:
        raise GuardrailRecompileStagingError("source queue must be process_model_refresh_impact_queue_v7")
    if queue.get("validation_commands") != EXPECTED_VALIDATION_COMMANDS:
        raise GuardrailRecompileStagingError("source queue must contain only exact offline validation commands")


def _guardrail_bundle_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "guardrail_bundle_id": _required_text(row, "guardrail_bundle_id"),
        "process_id": _required_text(row, "process_id"),
        "permit_type": _required_text(row, "permit_type"),
        "staging_status": "inactive_recompile_review_only",
        "activation_allowed": False,
    }


def _predicate_placeholders(queue: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_field, predicate_family in (
        ("eligibility_impact_placeholders", "eligibility_predicates"),
        ("document_impact_placeholders", "document_requirement_predicates"),
        ("fee_impact_placeholders", "fee_trigger_predicates"),
        ("stage_impact_placeholders", "process_stage_predicates"),
        ("unsupported_path_carry_forward_notes", "unsupported_path_predicates"),
    ):
        for index, item in enumerate(_required_mapping_list(queue, source_field)):
            rows.append(
                {
                    "placeholder_id": f"predicate-change:{predicate_family}:{index + 1}",
                    "source_queue_field": source_field,
                    "predicate_family": predicate_family,
                    "source_ref": _source_ref(item, index),
                    "review_status": "placeholder_requires_human_review",
                    "activation_allowed": False,
                }
            )
    return rows


def _review_placeholders(queue: Mapping[str, Any], source_field: str, review_type: str) -> list[dict[str, Any]]:
    rows = []
    for index, item in enumerate(_required_mapping_list(queue, source_field)):
        rows.append(
            {
                "placeholder_id": f"{review_type}:{index + 1}",
                "source_queue_field": source_field,
                "review_type": review_type,
                "source_ref": _source_ref(item, index),
                "review_status": "placeholder_requires_human_review",
                "activation_allowed": False,
            }
        )
    return rows


def _preservation_notes(guardrail_rows: Sequence[Mapping[str, Any]], note_type: str, note: str) -> list[dict[str, Any]]:
    return [
        {
            "note_id": f"{note_type}:{row['guardrail_bundle_id']}",
            "guardrail_bundle_id": row["guardrail_bundle_id"],
            "process_id": row["process_id"],
            "note_type": note_type,
            "note": note,
            "activation_allowed": False,
        }
        for row in guardrail_rows
    ]


def _stale_evidence_rows(queue: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for index, item in enumerate(_required_mapping_list(queue, "stale_evidence_holds")):
        rows.append(
            {
                "hold_id": _source_ref(item, index),
                "source_queue_field": "stale_evidence_holds",
                "propagation_status": "propagate_hold_to_guardrail_recompile_review",
                "guardrail_activation_blocked_until_review": True,
                "activation_allowed": False,
            }
        )
    return rows


def _rollback_rows(guardrail_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "rollback_checkpoint_id": f"rollback-checkpoint:{row['guardrail_bundle_id']}",
            "guardrail_bundle_id": row["guardrail_bundle_id"],
            "checkpoint_status": "placeholder_existing_bundle_snapshot_required_before_activation",
            "activation_allowed": False,
        }
        for row in guardrail_rows
    ]


def _reviewer_signoff_rows(queue: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for index, item in enumerate(_required_mapping_list(queue, "reviewer_signoff_placeholders")):
        rows.append(
            {
                "signoff_id": _source_ref(item, index),
                "source_queue_field": "reviewer_signoff_placeholders",
                "review_status": "required_before_recompile_activation",
                "activation_allowed": False,
            }
        )
    return rows


def _validate_row_activation_false(packet: Mapping[str, Any], findings: list[GuardrailRecompileStagingFinding]) -> None:
    for row_field in (
        "affected_guardrail_bundle_rows",
        "deterministic_predicate_change_placeholders",
        "deontic_rule_review_placeholders",
        "temporal_rule_review_placeholders",
        "reversible_action_predicate_preservation_notes",
        "exact_confirmation_gate_preservation_notes",
        "refused_action_gate_preservation_notes",
        "stale_evidence_hold_propagation_rows",
        "rollback_checkpoint_placeholders",
        "reviewer_signoff_placeholders",
    ):
        rows = packet.get(row_field)
        if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
            continue
        for index, row in enumerate(rows):
            if isinstance(row, Mapping) and row.get("activation_allowed") is not False:
                findings.append(
                    GuardrailRecompileStagingFinding(
                        "row_activation_not_false",
                        f"$.{row_field}[{index}].activation_allowed",
                        "staging rows must keep activation_allowed false",
                    )
                )


def _reject_prohibited_content(value: Any, path: str, findings: list[GuardrailRecompileStagingFinding]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized_key = _normalize_text(key_text)
            child_path = f"{path}.{key_text}" if path != "$" else f"$.{key_text}"
            if normalized_key in PROHIBITED_KEYS:
                findings.append(
                    GuardrailRecompileStagingFinding(
                        "prohibited_key",
                        child_path,
                        "private, auth, raw, downloaded, trace, or session artifact keys are not allowed",
                    )
                )
            _reject_prohibited_content(child, child_path, findings)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _reject_prohibited_content(child, f"{path}[{index}]", findings)
    elif isinstance(value, str):
        normalized = _normalize_text(value)
        for phrase in PROHIBITED_PHRASES:
            if phrase in normalized:
                findings.append(
                    GuardrailRecompileStagingFinding(
                        "prohibited_claim_phrase",
                        path,
                        "staging packet must not claim activation, live work, private access, official action, or guarantees",
                    )
                )
                break


def _required_mapping_list(row: Mapping[str, Any], key: str) -> list[Mapping[str, Any]]:
    value = row.get(key)
    if not isinstance(value, list) or not value:
        raise GuardrailRecompileStagingError(f"{key} must be a non-empty list")
    if not all(isinstance(item, Mapping) for item in value):
        raise GuardrailRecompileStagingError(f"{key} must contain only objects")
    return value


def _required_text(row: Mapping[str, Any], key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise GuardrailRecompileStagingError(f"{key} must be a non-empty string")
    return value


def _source_ref(item: Mapping[str, Any], index: int) -> str:
    for key in ("placeholder_id", "hold_id", "signoff_id", "suggestion_id", "note_id", "row_id", "ref"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return "source-row:" + str(index + 1)


def _non_empty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _non_empty_mapping_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, Mapping) for item in value)


def _sorted_unique(values: Any) -> list[str]:
    return sorted({value for value in values if isinstance(value, str) and value.strip()})


def _stable_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def _format_queue_issue(issue: QueueValidationIssue) -> str:
    return f"{issue.path}: {issue.message}"


def _normalize_text(value: str) -> str:
    return "_".join(value.strip().lower().replace("-", "_").replace(" ", "_").split("_"))
