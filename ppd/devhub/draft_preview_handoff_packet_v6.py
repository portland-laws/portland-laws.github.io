"""Fixture-first guarded draft preview handoff packet v6.

This module is intentionally offline-only. It assembles reversible draft
preview rows from already-redacted guardrail and attended read-only preflight
packets. It does not open DevHub, read private documents, upload, submit,
certify, pay, schedule, or make permitting/legal guarantees.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Iterable, List, Mapping

Packet = Dict[str, Any]

PACKET_TYPE = "guarded_draft_preview_handoff_packet"
PACKET_VERSION = "v6"
INPUT_GUARDRAIL_PACKET_TYPE = "agent_guardrail_api_compatibility_packet"
INPUT_PREFLIGHT_PACKET_TYPE = "attended_devhub_read_only_preflight_packet"

STOP_GATES = [
    {
        "gate_id": "upload_stop_gate",
        "blocked_actions": ["upload", "replace_upload", "remove_uploaded_file"],
        "required_checkpoint": "User-attended exact confirmation is required before any upload-related action.",
    },
    {
        "gate_id": "submission_stop_gate",
        "blocked_actions": ["submit", "final_submit", "send_application"],
        "required_checkpoint": "User-attended exact confirmation is required before any submission action.",
    },
    {
        "gate_id": "payment_stop_gate",
        "blocked_actions": ["enter_payment_details", "submit_payment", "authorize_payment"],
        "required_checkpoint": "User-attended exact confirmation is required before any payment action.",
    },
    {
        "gate_id": "certification_stop_gate",
        "blocked_actions": ["certify", "acknowledge", "sign", "attest"],
        "required_checkpoint": "User-attended exact confirmation is required before any certification, acknowledgement, signature, or attestation.",
    },
]

LOCAL_PDF_PREVIEW_BOUNDARIES = {
    "allowed": [
        "render local draft preview from redacted fixture values",
        "show field labels, proposed values, provenance, and caveats",
        "export no official filing artifact",
    ],
    "disallowed": [
        "open DevHub",
        "read private documents",
        "download official records",
        "upload files",
        "submit applications",
        "certify statements",
        "pay fees",
        "schedule inspections",
        "make legal or permitting guarantees",
    ],
}

OFFLINE_VALIDATION_COMMANDS = [
    ["python3", "-m", "py_compile", "ppd/devhub/draft_preview_handoff_packet_v6.py", "ppd/tests/test_draft_preview_handoff_packet_v6.py"],
    ["python3", "-m", "unittest", "ppd.tests.test_draft_preview_handoff_packet_v6"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]


def build_guarded_draft_preview_handoff_packet_v6(
    guardrail_packet: Mapping[str, Any],
    attended_preflight_packet: Mapping[str, Any],
) -> Packet:
    """Build a deterministic guarded draft preview handoff packet v6."""

    _require_packet(guardrail_packet, INPUT_GUARDRAIL_PACKET_TYPE)
    _require_packet(attended_preflight_packet, INPUT_PREFLIGHT_PACKET_TYPE)

    guardrail_rows = _rows_by_field_id(guardrail_packet.get("draft_fields", []))
    preflight_rows = _rows_by_field_id(attended_preflight_packet.get("read_only_fields", []))

    field_ids = sorted(set(guardrail_rows).intersection(preflight_rows))
    preview_rows = [
        _build_preview_row(field_id, guardrail_rows[field_id], preflight_rows[field_id])
        for field_id in field_ids
    ]

    return {
        "packet_type": PACKET_TYPE,
        "packet_version": PACKET_VERSION,
        "mode": "fixture_first_offline_only",
        "consumes_only": [INPUT_GUARDRAIL_PACKET_TYPE + ":v6", INPUT_PREFLIGHT_PACKET_TYPE + ":v6"],
        "case_id": guardrail_packet.get("case_id"),
        "process_id": guardrail_packet.get("process_id"),
        "surface_id": attended_preflight_packet.get("surface_id"),
        "reversible_draft_preview_rows": preview_rows,
        "user_fact_provenance_requirements": _user_fact_provenance_requirements(preview_rows),
        "selector_confidence_caveats": _selector_confidence_caveats(attended_preflight_packet),
        "stop_gates": deepcopy(STOP_GATES),
        "local_pdf_preview_boundaries": deepcopy(LOCAL_PDF_PREVIEW_BOUNDARIES),
        "exact_confirmation_checkpoint_reminders": _checkpoint_reminders(),
        "manual_handoff_notes": _manual_handoff_notes(),
        "offline_validation_commands": deepcopy(OFFLINE_VALIDATION_COMMANDS),
        "refusals": [
            "No DevHub access is performed by this packet.",
            "No private documents are read by this packet.",
            "No uploads, submissions, certifications, payments, scheduling, or guarantees are performed by this packet.",
        ],
    }


def _require_packet(packet: Mapping[str, Any], expected_type: str) -> None:
    actual_type = packet.get("packet_type")
    actual_version = packet.get("packet_version")
    if actual_type != expected_type or actual_version != PACKET_VERSION:
        raise ValueError(
            "expected %s:%s, got %s:%s"
            % (expected_type, PACKET_VERSION, actual_type, actual_version)
        )


def _rows_by_field_id(rows: Iterable[Mapping[str, Any]]) -> Dict[str, Mapping[str, Any]]:
    indexed: Dict[str, Mapping[str, Any]] = {}
    for row in rows:
        field_id = row.get("field_id")
        if not isinstance(field_id, str) or not field_id:
            raise ValueError("every draft/preflight row must include a non-empty field_id")
        indexed[field_id] = row
    return indexed


def _build_preview_row(
    field_id: str,
    guardrail_row: Mapping[str, Any],
    preflight_row: Mapping[str, Any],
) -> Packet:
    provenance = list(guardrail_row.get("user_fact_provenance", []))
    caveats = list(preflight_row.get("selector_caveats", []))
    selector_confidence = preflight_row.get("selector_confidence", "unknown")

    return {
        "field_id": field_id,
        "label": preflight_row.get("label", guardrail_row.get("label", field_id)),
        "draft_value": guardrail_row.get("draft_value"),
        "value_source": guardrail_row.get("value_source", "fixture_redacted_user_fact"),
        "reversible_only": True,
        "may_autofill_devhub": False,
        "requires_user_fact_provenance": bool(provenance),
        "user_fact_provenance": provenance,
        "selector": preflight_row.get("selector"),
        "selector_confidence": selector_confidence,
        "selector_confidence_caveats": caveats,
        "blocked_if_missing_provenance": bool(guardrail_row.get("blocked_if_missing_provenance", True)),
        "manual_review_required": selector_confidence != "high" or bool(caveats),
    }


def _user_fact_provenance_requirements(rows: List[Mapping[str, Any]]) -> List[Packet]:
    requirements: List[Packet] = []
    for row in rows:
        requirements.append(
            {
                "field_id": row["field_id"],
                "required": row["requires_user_fact_provenance"],
                "accepted_sources": list(row.get("user_fact_provenance", [])),
                "missing_fact_behavior": "ask_user_before_preview_or_leave_blank",
            }
        )
    return requirements


def _selector_confidence_caveats(attended_preflight_packet: Mapping[str, Any]) -> List[Packet]:
    caveats: List[Packet] = []
    for row in attended_preflight_packet.get("read_only_fields", []):
        confidence = row.get("selector_confidence", "unknown")
        row_caveats = list(row.get("selector_caveats", []))
        if confidence != "high" or row_caveats:
            caveats.append(
                {
                    "field_id": row.get("field_id"),
                    "selector_confidence": confidence,
                    "caveats": row_caveats or ["Selector must be reviewed manually before any attended use."],
                }
            )
    return caveats


def _checkpoint_reminders() -> List[Packet]:
    return [
        {
            "checkpoint_id": "before_devhub_use",
            "reminder": "Confirm the exact attended action and visible target before using DevHub.",
        },
        {
            "checkpoint_id": "before_consequential_action",
            "reminder": "Stop before upload, submission, payment, certification, scheduling, cancellation, or official change.",
        },
        {
            "checkpoint_id": "before_user_statement",
            "reminder": "Do not certify or guarantee facts; require the user to review and confirm their own statements.",
        },
    ]


def _manual_handoff_notes() -> List[str]:
    return [
        "Use this packet as a local draft preview checklist only.",
        "Carry forward field labels, proposed values, provenance needs, and selector caveats for attended review.",
        "Leave any unsupported, stale, conflicting, or unproven value blank and ask the user for the missing fact.",
        "Escalate to manual PP&D/DevHub review for any upload, submission, payment, certification, scheduling, cancellation, or official status change.",
    ]
