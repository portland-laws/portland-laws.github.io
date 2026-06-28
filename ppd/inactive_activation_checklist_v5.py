"""Fixture-first inactive activation checklist v5 assembly and validation.

This module intentionally consumes only committed post-decision smoke replay v5
fixtures. It does not activate guardrails, open DevHub, submit, upload, certify,
pay, schedule, or make legal/permitting guarantees.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any


REQUIRED_REPLAY_VERSION = "post-decision-smoke-replay-v5"
CHECKLIST_VERSION = "inactive-activation-checklist-v5"
CHECKLIST_STATUS = "inactive-review-only"
OFFLINE_VALIDATION_COMMANDS = [
    ["python3", "-m", "py_compile", "ppd/inactive_activation_checklist_v5.py"],
    ["python3", "-m", "pytest", "ppd/tests/test_inactive_activation_checklist_v5.py"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]

_REQUIRED_LIST_FIELDS = (
    "smoke_replay_references",
    "activation_prerequisites",
    "required_signoff_placeholders",
    "source_freshness_hold_clearance_criteria",
    "rollback_checkpoint_rows",
    "post_activation_smoke_checks",
    "agent_notification_notes",
    "monitoring_rehearsal_handoff_rows",
    "offline_validation_commands",
)

_REQUIRED_FIELD_CODES = {
    "smoke_replay_references": "missing_smoke_replay_references",
    "activation_prerequisites": "missing_reviewer_controlled_activation_prerequisites",
    "required_signoff_placeholders": "missing_signoff_placeholders",
    "source_freshness_hold_clearance_criteria": "missing_source_freshness_hold_clearance_criteria",
    "rollback_checkpoint_rows": "missing_rollback_checkpoint_rows",
    "post_activation_smoke_checks": "missing_post_activation_smoke_checks",
    "agent_notification_notes": "missing_agent_notification_notes",
    "monitoring_rehearsal_handoff_rows": "missing_monitoring_rehearsal_handoff_rows",
    "offline_validation_commands": "missing_validation_commands",
}

_FALSE_BOUNDARY_FLAGS = {
    "activation_allowed",
    "activation_enabled",
    "activation_performed",
    "active_activation",
    "active_guardrail_mutation",
    "active_mutation",
    "allow_payment",
    "allow_schedule",
    "allow_submit",
    "allow_upload",
    "certification_enabled",
    "devhub_opened",
    "guardrail_activation_enabled",
    "live_write",
    "mutation_enabled",
    "payment_enabled",
    "private_documents_read",
    "scheduling_enabled",
    "submission_enabled",
    "upload_enabled",
    "write_mode",
    "writes_enabled",
}

_ACTIVE_ACTIVATION_RE = re.compile(
    r"\b(activation\s+(is\s+)?(active|enabled|live|complete|completed|succeeded)|"
    r"activated\s+(guardrails|successfully|in\s+production)|production\s+activation\s+(enabled|complete|completed))\b",
    re.IGNORECASE,
)
_PRIVATE_ARTIFACT_RE = re.compile(
    r"\b(auth\s*state|storage_state|cookie|credential|password|session\s+file|private\s+session|"
    r"HAR\b|trace\.zip|screenshot|MFA\s+secret|token|browser\s+state|downloaded\s+document)\b",
    re.IGNORECASE,
)
_OFFICIAL_COMPLETION_RE = re.compile(
    r"\b(submitted|uploaded|certified|paid|scheduled|cancelled|canceled|withdrawn|completed)\b"
    r"[^\n]{0,80}\b(permit|application|inspection|fee|payment|correction|official\s+record|official\s+action)\b",
    re.IGNORECASE,
)
_LEGAL_GUARANTEE_RE = re.compile(
    r"\b(guarantee[sd]?|legally\s+binding|legal\s+advice|legal\s+guarantee|permit\s+will\s+be\s+(approved|issued)|"
    r"approval\s+guaranteed|issuance\s+guaranteed|compliance\s+guaranteed)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ChecklistV5Issue:
    """A deterministic validation issue for inactive activation checklist v5."""

    code: str
    path: str
    message: str


def _require_fixture_path(path: Path) -> None:
    normalized = path.as_posix()
    if "/ppd/tests/fixtures/" not in normalized and not normalized.startswith("ppd/tests/fixtures/"):
        raise ValueError("activation checklist v5 must be assembled from ppd/tests/fixtures only")
    if path.name != "post_decision_smoke_replay_v5.json":
        raise ValueError("activation checklist v5 requires the post_decision_smoke_replay_v5.json fixture")


def load_post_decision_smoke_replay_v5(path: Path) -> dict[str, Any]:
    """Load and validate the committed offline replay fixture."""
    _require_fixture_path(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("replay_version") != REQUIRED_REPLAY_VERSION:
        raise ValueError("unexpected post-decision smoke replay fixture version")
    if payload.get("source") != "committed-offline-fixture":
        raise ValueError("activation checklist v5 refuses non-fixture sources")
    return payload


def build_inactive_activation_checklist_v5(replay: dict[str, Any]) -> dict[str, Any]:
    """Build an inactive, reviewer-controlled activation checklist."""
    decisions = _mapping_sequence(replay.get("decision_smoke_results"))
    freshness = replay.get("source_freshness") if isinstance(replay.get("source_freshness"), Mapping) else {}
    monitoring = _mapping_sequence(replay.get("monitoring_rehearsal"))
    fixture_id = _text(replay.get("fixture_id"))

    checklist = {
        "checklist_version": CHECKLIST_VERSION,
        "status": CHECKLIST_STATUS,
        "fixture_source": fixture_id,
        "smoke_replay_references": [
            {
                "fixture_id": fixture_id,
                "replay_version": _text(replay.get("replay_version")),
                "source": _text(replay.get("source")),
                "reviewer_controlled": True,
                "activation_allowed": False,
            }
        ],
        "non_actions": [
            "does_not_activate_guardrails",
            "does_not_open_devhub",
            "does_not_read_private_documents",
            "does_not_upload_or_submit",
            "does_not_certify_pay_or_schedule",
            "does_not_make_legal_or_permitting_guarantees",
        ],
        "activation_prerequisites": [
            {
                "id": "fixture-replay-reviewed",
                "description": "Reviewer confirms the committed post-decision smoke replay v5 fixture was used as the only source.",
                "owner": "reviewer",
                "state": "placeholder-required",
                "reviewer_controlled": True,
                "activation_allowed": False,
            },
            {
                "id": "decision-smoke-results-reviewed",
                "description": "Reviewer checks each post-decision smoke replay row before any separate activation decision.",
                "owner": "reviewer",
                "state": "placeholder-required",
                "reviewer_controlled": True,
                "activation_allowed": False,
            },
        ],
        "required_signoff_placeholders": [
            {"role": "PP&D reviewer", "placeholder": "name/date required before activation consideration", "signed_by": None, "activation_allowed": False},
            {"role": "automation owner", "placeholder": "name/date required before activation consideration", "signed_by": None, "activation_allowed": False},
            {"role": "rollback owner", "placeholder": "name/date required before activation consideration", "signed_by": None, "activation_allowed": False},
        ],
        "source_freshness_hold_clearance_criteria": [
            {
                "id": "freshness-window",
                "criterion": "Freshness hold remains uncleared until reviewer confirms fixture timestamp and source label are acceptable.",
                "fixture_value": freshness.get("hold_state", "unknown"),
                "clearance": "manual-review-placeholder",
                "activation_allowed": False,
            },
            {
                "id": "no-live-refresh",
                "criterion": "No live crawl or authenticated refresh is performed by this checklist.",
                "fixture_value": freshness.get("live_refresh_attempted", False),
                "clearance": "must-remain-false",
                "activation_allowed": False,
            },
        ],
        "rollback_checkpoint_rows": [
            {
                "checkpoint": row.get("checkpoint"),
                "expected_state": row.get("expected_state"),
                "reviewer_note": "placeholder-required",
                "active_state_changed": False,
                "activation_allowed": False,
            }
            for row in _mapping_sequence(replay.get("rollback_checkpoints"))
        ],
        "post_activation_smoke_checks": [
            {
                "check_id": row.get("check_id"),
                "observed": row.get("observed"),
                "expected": row.get("expected"),
                "result": row.get("result"),
                "reviewer_note": "placeholder-required",
                "activation_allowed": False,
            }
            for row in decisions
        ],
        "agent_notification_notes": [
            {
                "recipient": "automation-agent",
                "note": "Checklist is inactive and fixture-derived; do not run live DevHub automation from this artifact.",
                "activation_allowed": False,
            },
            {
                "recipient": "reviewer-agent",
                "note": "Review placeholders must be completed outside this fixture assembly step.",
                "activation_allowed": False,
            },
        ],
        "monitoring_rehearsal_handoff_rows": [
            {
                "monitor": row.get("monitor"),
                "handoff_state": row.get("handoff_state"),
                "next_reviewer_action": "manual-review-placeholder",
                "activation_allowed": False,
            }
            for row in monitoring
        ],
        "offline_validation_commands": OFFLINE_VALIDATION_COMMANDS,
    }
    assert_valid_inactive_activation_checklist_v5(checklist)
    return checklist


def build_from_fixture_path(path: Path) -> dict[str, Any]:
    return build_inactive_activation_checklist_v5(load_post_decision_smoke_replay_v5(path))


def validate_inactive_activation_checklist_v5(checklist: Mapping[str, Any]) -> list[ChecklistV5Issue]:
    """Return validation issues for an inactive activation checklist v5 object."""
    issues: list[ChecklistV5Issue] = []
    if not isinstance(checklist, Mapping):
        return [ChecklistV5Issue("invalid_checklist", "$", "checklist must be an object")]
    if checklist.get("checklist_version") != CHECKLIST_VERSION:
        issues.append(ChecklistV5Issue("missing_checklist_v5_marker", "$.checklist_version", f"checklist_version must be {CHECKLIST_VERSION}"))
    if checklist.get("status") != CHECKLIST_STATUS:
        issues.append(ChecklistV5Issue("missing_inactive_status", "$.status", f"status must be {CHECKLIST_STATUS}"))
    for field in _REQUIRED_LIST_FIELDS:
        if not _non_empty_sequence(checklist.get(field)):
            issues.append(ChecklistV5Issue(_REQUIRED_FIELD_CODES[field], f"$.{field}", f"{field} must be a non-empty list"))
    if checklist.get("offline_validation_commands") != OFFLINE_VALIDATION_COMMANDS:
        issues.append(ChecklistV5Issue("invalid_validation_commands", "$.offline_validation_commands", "offline_validation_commands must exactly match the approved offline validation commands"))
    _validate_replay_references(checklist.get("smoke_replay_references"), issues)
    _validate_prerequisites(checklist.get("activation_prerequisites"), issues)
    _validate_signoffs(checklist.get("required_signoff_placeholders"), issues)
    _validate_freshness(checklist.get("source_freshness_hold_clearance_criteria"), issues)
    _validate_rollback(checklist.get("rollback_checkpoint_rows"), issues)
    _validate_smoke(checklist.get("post_activation_smoke_checks"), issues)
    _validate_notes(checklist.get("agent_notification_notes"), issues)
    _validate_monitoring(checklist.get("monitoring_rehearsal_handoff_rows"), issues)
    _scan_for_forbidden_payload(checklist, "$", issues)
    return _dedupe_issues(issues)


def assert_valid_inactive_activation_checklist_v5(checklist: Mapping[str, Any]) -> None:
    issues = validate_inactive_activation_checklist_v5(checklist)
    if issues:
        raise ValueError("invalid inactive activation checklist v5: " + "; ".join(issue.message for issue in issues))


def issue_codes(issues: Sequence[ChecklistV5Issue]) -> set[str]:
    return {issue.code for issue in issues}


def _validate_replay_references(value: Any, issues: list[ChecklistV5Issue]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        path = f"$.smoke_replay_references[{index}]"
        if not _text(row.get("fixture_id")) or row.get("replay_version") != REQUIRED_REPLAY_VERSION:
            issues.append(ChecklistV5Issue("invalid_smoke_replay_reference", path, "smoke replay references must name the v5 fixture and version"))
        if row.get("reviewer_controlled") is not True:
            issues.append(ChecklistV5Issue("missing_reviewer_control", path + ".reviewer_controlled", "smoke replay references must remain reviewer controlled"))
        if row.get("activation_allowed") is not False:
            issues.append(ChecklistV5Issue("active_activation_claim", path + ".activation_allowed", "smoke replay references must not allow activation"))


def _validate_prerequisites(value: Any, issues: list[ChecklistV5Issue]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        path = f"$.activation_prerequisites[{index}]"
        if row.get("owner") != "reviewer" or row.get("reviewer_controlled") is not True:
            issues.append(ChecklistV5Issue("missing_reviewer_controlled_activation_prerequisites", path, "activation prerequisites must be reviewer controlled"))
        if row.get("state") != "placeholder-required":
            issues.append(ChecklistV5Issue("missing_reviewer_controlled_activation_prerequisites", path + ".state", "activation prerequisites must remain placeholder-required"))
        if row.get("activation_allowed") is not False:
            issues.append(ChecklistV5Issue("active_activation_claim", path + ".activation_allowed", "activation prerequisites must not allow activation"))


def _validate_signoffs(value: Any, issues: list[ChecklistV5Issue]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        path = f"$.required_signoff_placeholders[{index}]"
        if not _text(row.get("role")) or "placeholder" not in row or not _text(row.get("placeholder")):
            issues.append(ChecklistV5Issue("missing_signoff_placeholders", path, "signoff rows must include role and placeholder"))
        if row.get("signed_by") is not None:
            issues.append(ChecklistV5Issue("missing_signoff_placeholders", path + ".signed_by", "signoff placeholders must not be pre-signed"))
        if row.get("activation_allowed") is not False:
            issues.append(ChecklistV5Issue("active_activation_claim", path + ".activation_allowed", "signoff placeholders must not allow activation"))


def _validate_freshness(value: Any, issues: list[ChecklistV5Issue]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        path = f"$.source_freshness_hold_clearance_criteria[{index}]"
        if not _text(row.get("criterion")) or not _text(row.get("clearance")):
            issues.append(ChecklistV5Issue("missing_source_freshness_hold_clearance_criteria", path, "freshness rows must include criterion and clearance"))
        if row.get("activation_allowed") is not False:
            issues.append(ChecklistV5Issue("active_activation_claim", path + ".activation_allowed", "freshness clearance rows must not allow activation"))


def _validate_rollback(value: Any, issues: list[ChecklistV5Issue]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        path = f"$.rollback_checkpoint_rows[{index}]"
        if not _text(row.get("checkpoint")) or not _text(row.get("expected_state")):
            issues.append(ChecklistV5Issue("missing_rollback_checkpoint_rows", path, "rollback checkpoint rows must include checkpoint and expected_state"))
        if row.get("active_state_changed") is not False:
            issues.append(ChecklistV5Issue("active_mutation_flag", path + ".active_state_changed", "rollback checkpoint rows must not claim active state changes"))
        if row.get("activation_allowed") is not False:
            issues.append(ChecklistV5Issue("active_activation_claim", path + ".activation_allowed", "rollback checkpoint rows must not allow activation"))


def _validate_smoke(value: Any, issues: list[ChecklistV5Issue]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        path = f"$.post_activation_smoke_checks[{index}]"
        if not _text(row.get("check_id")) or not _text(row.get("expected")):
            issues.append(ChecklistV5Issue("missing_post_activation_smoke_checks", path, "post-activation smoke checks must include check_id and expected"))
        if row.get("activation_allowed") is not False:
            issues.append(ChecklistV5Issue("active_activation_claim", path + ".activation_allowed", "post-activation smoke checks must not allow activation"))


def _validate_notes(value: Any, issues: list[ChecklistV5Issue]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        path = f"$.agent_notification_notes[{index}]"
        if not _text(row.get("recipient")) or not _text(row.get("note")):
            issues.append(ChecklistV5Issue("missing_agent_notification_notes", path, "agent notification rows must include recipient and note"))
        if row.get("activation_allowed") is not False:
            issues.append(ChecklistV5Issue("active_activation_claim", path + ".activation_allowed", "agent notification notes must not allow activation"))


def _validate_monitoring(value: Any, issues: list[ChecklistV5Issue]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        path = f"$.monitoring_rehearsal_handoff_rows[{index}]"
        if not _text(row.get("monitor")) or not _text(row.get("handoff_state")) or not _text(row.get("next_reviewer_action")):
            issues.append(ChecklistV5Issue("missing_monitoring_rehearsal_handoff_rows", path, "monitoring handoff rows must include monitor, handoff_state, and next_reviewer_action"))
        if row.get("activation_allowed") is not False:
            issues.append(ChecklistV5Issue("active_activation_claim", path + ".activation_allowed", "monitoring handoff rows must not allow activation"))


def _scan_for_forbidden_payload(value: Any, path: str, issues: list[ChecklistV5Issue]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text in _FALSE_BOUNDARY_FLAGS and child is True:
                issues.append(ChecklistV5Issue("active_mutation_flag", child_path, f"{key_text} must not be true in inactive checklist v5"))
            if _PRIVATE_ARTIFACT_RE.search(key_text) and child not in (False, None, "", [], {}):
                issues.append(ChecklistV5Issue("private_session_auth_artifact", child_path, "private/session/auth artifacts are not allowed"))
            _scan_for_forbidden_payload(child, child_path, issues)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _scan_for_forbidden_payload(child, f"{path}[{index}]", issues)
    elif isinstance(value, str):
        if _ACTIVE_ACTIVATION_RE.search(value):
            issues.append(ChecklistV5Issue("active_activation_claim", path, "active activation claims are not allowed"))
        if _PRIVATE_ARTIFACT_RE.search(value):
            issues.append(ChecklistV5Issue("private_session_auth_artifact", path, "private/session/auth artifacts are not allowed"))
        if _OFFICIAL_COMPLETION_RE.search(value):
            issues.append(ChecklistV5Issue("official_action_completion_claim", path, "official-action completion claims are not allowed"))
        if _LEGAL_GUARANTEE_RE.search(value):
            issues.append(ChecklistV5Issue("legal_or_permitting_guarantee", path, "legal or permitting guarantees are not allowed"))


def _mapping_sequence(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _non_empty_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)) and len(value) > 0


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _dedupe_issues(issues: Sequence[ChecklistV5Issue]) -> list[ChecklistV5Issue]:
    seen: set[tuple[str, str, str]] = set()
    deduped: list[ChecklistV5Issue] = []
    for issue in issues:
        key = (issue.code, issue.path, issue.message)
        if key not in seen:
            seen.add(key)
            deduped.append(issue)
    return deduped
