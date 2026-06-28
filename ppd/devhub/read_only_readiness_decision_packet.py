"""Fixture-first DevHub read-only readiness decision packets.

This module joins already-sanitized PP&D DevHub read-only pilot checklist,
DevHub surface registry update candidate, and post-release audit findings
packets. It is intentionally offline-only: it does not launch a browser,
read private files, store session artifacts, or enable consequential actions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from ppd.agent_readiness.post_release_audit_validation import require_post_release_audit_findings_packet
from ppd.devhub.surface_registry_update_candidate import assert_valid_surface_registry_update_candidate_packet


REQUIRED_PACKET_TYPE = "ppd.devhub.read_only_readiness_decision_packet.v1"
REQUIRED_MODE = "fixture_first_attended_devhub_read_only_readiness_decision"
REQUIRED_CHECKLIST_PACKET_TYPE = "devhub_read_only_observation_checklist_packet"
REQUIRED_DEFERRALS = (
    "uploads",
    "submissions",
    "payments",
    "certifications",
    "cancellations",
    "inspection_scheduling",
)
FORBIDDEN_KEYS = frozenset(
    {
        "auth_state",
        "browser_state",
        "captcha_solution",
        "cookies",
        "credential",
        "credentials",
        "downloaded_document",
        "downloaded_file",
        "har",
        "password",
        "payment_details",
        "private_value",
        "raw_authenticated_text",
        "raw_crawl_output",
        "raw_html",
        "screenshot",
        "session_cookie",
        "session_state",
        "storage_state",
        "token",
        "trace",
        "upload_payload",
    }
)


def load_json_packet(path: str | Path) -> dict[str, Any]:
    """Load a JSON object fixture from a committed fixture path."""

    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("read-only readiness source fixture must be a JSON object")
    return data


def build_read_only_readiness_decision_packet(
    operator_checklist: Mapping[str, Any],
    devhub_surface_registry_update_candidate: Mapping[str, Any],
    post_release_audit_findings_packet: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a cited manual-login read-only readiness packet from fixtures."""

    _assert_operator_checklist(operator_checklist)
    assert_valid_surface_registry_update_candidate_packet(devhub_surface_registry_update_candidate)
    require_post_release_audit_findings_packet(post_release_audit_findings_packet)

    checklist_citations = _checklist_evidence_ids(operator_checklist)
    surface_citations = _surface_citations(devhub_surface_registry_update_candidate)
    audit_citations = _audit_citations(post_release_audit_findings_packet)

    packet = {
        "packet_id": "devhub-read-only-readiness-decision-synthetic-v1",
        "packet_type": REQUIRED_PACKET_TYPE,
        "mode": REQUIRED_MODE,
        "fixture_first": True,
        "offline_only": True,
        "llm_invoked": False,
        "launches_devhub": False,
        "launches_playwright": False,
        "network_requests_made": False,
        "reads_private_files": False,
        "stores_private_artifacts": False,
        "decision": "read_only_attended_pilot_ready_after_manual_login_prerequisites",
        "source_packets": {
            "devhub_read_only_pilot_operator_checklist": {
                "packet_id": _text(operator_checklist.get("packet_id")),
                "packet_type": _text(operator_checklist.get("packet_type")),
                "consumed": True,
                "citations": checklist_citations,
            },
            "devhub_surface_registry_update_candidate": {
                "packet_id": _text(devhub_surface_registry_update_candidate.get("packet_id")),
                "packet_type": _text(devhub_surface_registry_update_candidate.get("packet_type")),
                "consumed": True,
                "citations": surface_citations,
            },
            "post_release_audit_findings_packet": {
                "packet_type": _text(post_release_audit_findings_packet.get("packet_type")),
                "release_status": _text(post_release_audit_findings_packet.get("release_status")),
                "consumed": True,
                "citations": audit_citations,
            },
        },
        "cited_manual_login_prerequisites": _manual_login_prerequisites(checklist_citations, surface_citations),
        "read_only_scope_limits": _read_only_scope_limits(operator_checklist),
        "reviewer_owners": _reviewer_owners(surface_citations, audit_citations),
        "abort_conditions": _abort_conditions(operator_checklist, checklist_citations),
        "private_artifact_prohibitions": _private_artifact_prohibitions(operator_checklist, checklist_citations),
        "explicit_deferrals": _explicit_deferrals(audit_citations, surface_citations),
    }
    assert_valid_read_only_readiness_decision_packet(packet)
    return packet


def assert_valid_read_only_readiness_decision_packet(packet: Mapping[str, Any]) -> None:
    errors = validate_read_only_readiness_decision_packet(packet)
    if errors:
        raise AssertionError("; ".join(errors))


def validate_read_only_readiness_decision_packet(packet: Mapping[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    _require(errors, packet.get("packet_type") == REQUIRED_PACKET_TYPE, f"packet_type must be {REQUIRED_PACKET_TYPE}")
    _require(errors, packet.get("mode") == REQUIRED_MODE, f"mode must be {REQUIRED_MODE}")
    for field in ("fixture_first", "offline_only"):
        _require(errors, packet.get(field) is True, f"{field} must be true")
    for field in (
        "llm_invoked",
        "launches_devhub",
        "launches_playwright",
        "network_requests_made",
        "reads_private_files",
        "stores_private_artifacts",
    ):
        _require(errors, packet.get(field) is False, f"{field} must be false")
    _validate_forbidden_content(errors, packet)

    source_packets = _mapping(packet.get("source_packets"))
    for key in (
        "devhub_read_only_pilot_operator_checklist",
        "devhub_surface_registry_update_candidate",
        "post_release_audit_findings_packet",
    ):
        source = _mapping(source_packets.get(key))
        _require(errors, source.get("consumed") is True, f"source_packets.{key}.consumed must be true")
        _require(errors, bool(_text_list(source.get("citations"))), f"source_packets.{key}.citations must be non-empty")

    _validate_cited_rows(errors, packet.get("cited_manual_login_prerequisites"), "cited_manual_login_prerequisites")
    _validate_cited_rows(errors, packet.get("read_only_scope_limits"), "read_only_scope_limits")
    _validate_cited_rows(errors, packet.get("reviewer_owners"), "reviewer_owners")
    _validate_cited_rows(errors, packet.get("abort_conditions"), "abort_conditions")
    _validate_cited_rows(errors, packet.get("private_artifact_prohibitions"), "private_artifact_prohibitions")

    deferrals = _sequence(packet.get("explicit_deferrals"))
    seen_deferrals = {_text(_mapping(item).get("action_id")) for item in deferrals}
    for action_id in REQUIRED_DEFERRALS:
        _require(errors, action_id in seen_deferrals, f"explicit_deferrals must include {action_id}")
    for index, raw_deferral in enumerate(deferrals):
        deferral = _mapping(raw_deferral)
        prefix = f"explicit_deferrals[{index}]"
        _require(errors, deferral.get("deferred") is True, f"{prefix}.deferred must be true")
        _require(errors, deferral.get("allowed") is False, f"{prefix}.allowed must be false")
        _require(errors, deferral.get("requires_future_attended_confirmation") is True, f"{prefix}.requires_future_attended_confirmation must be true")
        _require(errors, bool(_text_list(deferral.get("citations"))), f"{prefix}.citations must be non-empty")
    return tuple(dict.fromkeys(errors))


def _assert_operator_checklist(packet: Mapping[str, Any]) -> None:
    errors: list[str] = []
    _require(errors, packet.get("packet_type") == REQUIRED_CHECKLIST_PACKET_TYPE, "operator checklist packet_type is invalid")
    _require(errors, packet.get("fixture_first") is True, "operator checklist must be fixture_first")
    workflow = _mapping(packet.get("workflow"))
    _require(errors, workflow.get("attendance_required") is True, "operator checklist must require attendance")
    _require(errors, workflow.get("live_devhub_allowed") is False, "operator checklist must keep live DevHub disabled")
    _require(errors, workflow.get("official_actions_allowed") is False, "operator checklist must block official actions")
    _require(errors, bool(_checklist_evidence_ids(packet)), "operator checklist must include synthetic evidence ids")
    if errors:
        raise AssertionError("; ".join(errors))


def _manual_login_prerequisites(checklist_citations: list[str], surface_citations: list[str]) -> list[dict[str, Any]]:
    citations = checklist_citations[:2] + surface_citations[:1]
    return [
        {
            "prerequisite_id": "manual-login-user-present",
            "description": "The user must remain present before any future attended DevHub observation begins.",
            "manual_only": True,
            "browser_launch_allowed_by_packet": False,
            "citations": citations,
        },
        {
            "prerequisite_id": "manual-login-portlandoregon-credentials",
            "description": "The user manually completes PortlandOregon.gov sign-in, MFA, CAPTCHA, and account prompts if a future attended pilot is separately approved.",
            "manual_only": True,
            "credential_storage_allowed": False,
            "citations": citations,
        },
        {
            "prerequisite_id": "manual-login-read-only-mode-confirmed",
            "description": "The operator confirms the session is limited to redacted read-only labels before observing any authenticated surface.",
            "manual_only": True,
            "official_action_allowed": False,
            "citations": citations,
        },
    ]


def _read_only_scope_limits(operator_checklist: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        _scope_row("devhub_home_and_dashboard_labels", "Home, dashboard, and permits navigation labels only.", ["ev-heading-dashboard"]),
        _scope_row("permit_status_messages", "Generic permit status labels only; redact identifiers and private values.", ["ev-status-review"]),
        _scope_row("attachment_list_review", "Attachment list and column labels only; do not open, preview, download, or name private documents.", ["ev-attachments-list"]),
        _scope_row("fee_notice_review", "Fee notice labels only; do not enter checkout or store payment data.", ["ev-fee-notice"]),
        _scope_row("correction_request_review", "Correction request labels and generic categories only; do not record private message bodies.", ["ev-correction-request"]),
        _scope_row("inspection_result_review", "Inspection result labels only; do not schedule, reschedule, or cancel inspections.", ["ev-inspection-result"]),
    ]


def _scope_row(scope_id: str, description: str, citations: list[str]) -> dict[str, Any]:
    return {
        "scope_id": scope_id,
        "description": description,
        "read_only": True,
        "redacted_metadata_only": True,
        "official_action_allowed": False,
        "citations": citations,
    }


def _reviewer_owners(surface_citations: list[str], audit_citations: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "owner_id": "devhub_pilot_operator",
            "reviewer_role": "DevHub read-only pilot operator",
            "owns": "manual login attendance, stop-condition enforcement, and redacted note discipline",
            "requires_reviewer": True,
            "citations": surface_citations[:2],
        },
        {
            "owner_id": "devhub_surface_reviewer",
            "reviewer_role": "DevHub surface registry reviewer",
            "owns": "candidate surface metadata and selector-confidence deferral",
            "requires_reviewer": True,
            "citations": surface_citations,
        },
        {
            "owner_id": "ppd_guardrail_reviewer",
            "reviewer_role": "PP&D guardrail reviewer",
            "owns": "consequential-action blocks and exact-confirmation gates",
            "requires_reviewer": True,
            "citations": audit_citations,
        },
        {
            "owner_id": "post_release_audit_reviewer",
            "reviewer_role": "Post-release audit reviewer",
            "owns": "audit finding closure before any production-readiness claim",
            "requires_reviewer": True,
            "citations": audit_citations,
        },
    ]


def _abort_conditions(operator_checklist: Mapping[str, Any], citations: list[str]) -> list[dict[str, Any]]:
    raw_conditions = _sequence(_mapping(operator_checklist.get("manual_stop_conditions")).get("stop_immediately_when"))
    return [
        {
            "abort_id": f"abort-{index + 1:02d}",
            "condition": _text(condition),
            "operator_result": _text(_mapping(operator_checklist.get("manual_stop_conditions")).get("operator_result")),
            "citations": citations[:2] or ["devhub-observation-checklist-synthetic-v1"],
        }
        for index, condition in enumerate(raw_conditions)
        if _text(condition)
    ]


def _private_artifact_prohibitions(operator_checklist: Mapping[str, Any], citations: list[str]) -> list[dict[str, Any]]:
    raw_rules = _sequence(_mapping(operator_checklist.get("redaction_rules")).get("prohibited_storage"))
    return [
        {
            "prohibition_id": f"private-artifact-prohibition-{index + 1:02d}",
            "prohibition": _text(rule),
            "commit_safe": True,
            "citations": citations[:2] or ["devhub-observation-checklist-synthetic-v1"],
        }
        for index, rule in enumerate(raw_rules)
        if _text(rule)
    ]


def _explicit_deferrals(audit_citations: list[str], surface_citations: list[str]) -> list[dict[str, Any]]:
    labels = {
        "uploads": "official uploads and correction uploads",
        "submissions": "permit request submissions",
        "payments": "fee payment and checkout workflows",
        "certifications": "acknowledgement and certification controls",
        "cancellations": "withdrawal, cancellation, extension, and reactivation controls",
        "inspection_scheduling": "inspection scheduling, rescheduling, and cancellation controls",
    }
    citations = audit_citations + surface_citations[:2]
    return [
        {
            "action_id": action_id,
            "description": labels[action_id],
            "deferred": True,
            "allowed": False,
            "requires_future_attended_confirmation": True,
            "deferral_reason": "Consequential DevHub action remains outside the read-only readiness decision packet.",
            "citations": citations,
        }
        for action_id in REQUIRED_DEFERRALS
    ]


def _checklist_evidence_ids(packet: Mapping[str, Any]) -> list[str]:
    evidence = _sequence(_mapping(packet.get("synthetic_surface_evidence")).get("evidence_items"))
    return [_text(item.get("evidence_id")) for item in evidence if isinstance(item, Mapping) and _text(item.get("evidence_id"))]


def _surface_citations(packet: Mapping[str, Any]) -> list[str]:
    citations = [_text(packet.get("packet_id"))]
    for candidate in _sequence(packet.get("registry_update_candidates")):
        surface_id = _text(_mapping(candidate).get("surface_id"))
        if surface_id:
            citations.append(surface_id)
    return [citation for citation in citations if citation]


def _audit_citations(packet: Mapping[str, Any]) -> list[str]:
    citations: list[str] = []
    for finding in _sequence(packet.get("findings")):
        citations.extend(_text_list(_mapping(finding).get("source_evidence_ids")))
    return list(dict.fromkeys(citations))


def _validate_cited_rows(errors: list[str], value: Any, path: str) -> None:
    rows = _sequence(value)
    _require(errors, bool(rows), f"{path} must be non-empty")
    for index, raw_row in enumerate(rows):
        row = _mapping(raw_row)
        _require(errors, bool(_text_list(row.get("citations"))), f"{path}[{index}].citations must be non-empty")


def _validate_forbidden_content(errors: list[str], value: Any, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text.lower() in FORBIDDEN_KEYS and child not in (None, False, "", [], {}):
                errors.append(f"forbidden private or browser artifact field at {child_path}")
            _validate_forbidden_content(errors, child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _validate_forbidden_content(errors, child, f"{path}[{index}]")


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: Any) -> Sequence[Any]:
    return value if isinstance(value, list) else []


def _text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _text_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_text(item) for item in value if _text(item)]


def _require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)
