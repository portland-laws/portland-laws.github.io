"""Fixture-first post-activation monitoring rehearsal v5.

This module consumes only inactive activation checklist v5 fixtures and builds
synthetic monitoring rows. It never activates guardrails, opens DevHub, reads
private documents, crawls live sites, uploads, submits, certifies, pays,
schedules, or makes legal/permitting guarantees.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any

PACKET_TYPE = "ppd.post_activation_monitoring_rehearsal.v5"
PACKET_VERSION = "v5"
MODE = "fixture_first_post_activation_monitoring_rehearsal_v5"
INACTIVE_CHECKLIST_PACKET_TYPE = "ppd.inactive_activation_checklist.v5"
VALIDATION_COMMANDS = [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]]

REQUIRED_BOUNDARIES = {
    "fixture_first": True,
    "offline_rehearsal_only": True,
    "synthetic_monitoring_rows_only": True,
    "inactive_activation_checklist_v5_fixtures_only": True,
    "live_monitoring_enabled": False,
    "guardrail_activation_enabled": False,
    "active_guardrail_mutation_enabled": False,
    "devhub_opened": False,
    "private_documents_read": False,
    "live_site_crawl_enabled": False,
    "upload_enabled": False,
    "submission_enabled": False,
    "certification_enabled": False,
    "financial_action_enabled": False,
    "scheduling_enabled": False,
    "legal_or_permitting_guarantee_enabled": False,
}

REQUIRED_ATTESTATIONS = {
    "guardrails_activated": False,
    "devhub_opened": False,
    "private_documents_read": False,
    "live_sites_crawled": False,
    "uploads_performed": False,
    "submissions_performed": False,
    "certifications_performed": False,
    "financial_actions_performed": False,
    "scheduling_performed": False,
    "legal_or_permitting_guarantees_made": False,
}

REQUIRED_SECTIONS = (
    "guardrail_lookup_health_rows",
    "stale_source_stop_gate_rows",
    "exact_confirmation_gate_behavior_rows",
    "refused_consequential_and_financial_action_rows",
    "rollback_trigger_threshold_rows",
    "reviewer_escalation_routing_rows",
    "agent_notification_routing_rows",
    "exact_offline_validation_command_rows",
)

REQUIRED_TEXT_FIELDS = {
    "activation_checklist_references": (
        "activation_checklist_reference_id",
        "source_packet_id",
        "source_packet_type",
    ),
    "guardrail_lookup_health_rows": (
        "monitoring_row_id",
        "source_activation_checklist_reference",
        "lookup_name",
        "expected_status",
    ),
    "stale_source_stop_gate_rows": (
        "monitoring_row_id",
        "source_activation_checklist_reference",
        "stale_condition",
        "expected_result",
    ),
    "exact_confirmation_gate_behavior_rows": (
        "monitoring_row_id",
        "source_activation_checklist_reference",
        "action_class",
        "expected_result",
    ),
    "refused_consequential_and_financial_action_rows": (
        "monitoring_row_id",
        "source_activation_checklist_reference",
        "action_class",
        "expected_result",
    ),
    "rollback_trigger_threshold_rows": (
        "monitoring_row_id",
        "source_activation_checklist_reference",
        "threshold",
        "expected_result",
    ),
    "reviewer_escalation_routing_rows": (
        "monitoring_row_id",
        "source_activation_checklist_reference",
        "reviewer_role",
        "expected_route",
    ),
    "agent_notification_routing_rows": (
        "monitoring_row_id",
        "source_activation_checklist_reference",
        "agent_channel",
        "expected_route",
    ),
    "exact_offline_validation_command_rows": (
        "monitoring_row_id",
        "source_activation_checklist_reference",
        "command_label",
        "expected_result",
    ),
}

EXPECTED_VALUES = {
    "guardrail_lookup_health_rows": {"expected_status": "synthetic_lookup_row_present_offline"},
    "stale_source_stop_gate_rows": {"expected_result": "agent_blocks_until_source_refresh_or_reviewer_disposition"},
    "exact_confirmation_gate_behavior_rows": {"expected_result": "exact_confirmation_required_before_consequential_step"},
    "refused_consequential_and_financial_action_rows": {"expected_result": "refused_without_user_attendance_and_exact_confirmation"},
    "rollback_trigger_threshold_rows": {"expected_result": "rollback_reviewer_hold"},
    "reviewer_escalation_routing_rows": {"expected_route": "human_reviewer_queue"},
    "agent_notification_routing_rows": {"expected_route": "agent_consumer_notice_queue"},
    "exact_offline_validation_command_rows": {"expected_result": "only_daemon_self_test_allowed"},
}

FORBIDDEN_TRUE_KEYS = frozenset(
    {
        "active_activation",
        "active_guardrail_activation",
        "active_guardrail_mutation",
        "active_guardrail_mutation_enabled",
        "active_monitoring",
        "active_mutation",
        "active_mutation_enabled",
        "approval_guaranteed",
        "automated_submission_enabled",
        "browser_automation_enabled",
        "certification_completed",
        "certification_enabled",
        "certifications_performed",
        "devhub_opened",
        "financial_action_completed",
        "financial_action_enabled",
        "financial_actions_performed",
        "guardrail_activation_enabled",
        "guardrails_activated",
        "legal_guarantee",
        "legal_or_permitting_guarantee_enabled",
        "legal_or_permitting_guarantees_made",
        "live_monitoring",
        "live_monitoring_enabled",
        "live_site_crawl_enabled",
        "live_sites_crawled",
        "monitoring_active",
        "mutation_active",
        "mutation_enabled",
        "official_action_complete",
        "official_action_completed",
        "official_action_enabled",
        "permit_guaranteed",
        "permitting_guarantee",
        "private_documents_read",
        "scheduling_enabled",
        "scheduling_performed",
        "submission_completed",
        "submission_enabled",
        "submissions_performed",
        "upload_completed",
        "upload_enabled",
        "uploads_performed",
    }
)

PRIVATE_KEY_RE = re.compile(
    r"(^|_)(auth|auth_state|browser_state|cookie|credential|downloaded|har|password|private|private_artifact|raw|raw_crawl|screenshot|secret|session|session_state|storage_state|token|trace)(_|$)",
    re.IGNORECASE,
)
FORBIDDEN_TEXT_RE = re.compile(
    r"("
    r"activation complete|activated guardrail|active guardrail|active monitoring|active mutation|"
    r"approval guaranteed|auth artifact|certification completed|completed official action|"
    r"devhub opened|downloaded document|final financial action|guardrails activated|"
    r"guarantee approval|guarantee permit|legal advice|legal guarantee|live monitoring|"
    r"live site crawl|monitoring active|monitoring is active|mutation enabled|official-action completed|"
    r"official action completed|payment submitted|permit approval guaranteed|permit guarantee|"
    r"permit will be approved|permit will be issued|permitting guarantee|private artifact|"
    r"private session|raw crawl|scheduled inspection|session state|storage state|submitted permit|"
    r"trace file|uploaded correction|uploaded plans"
    r")",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class PostActivationMonitoringRehearsalV5Result:
    valid: bool
    problems: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {"valid": self.valid, "problems": list(self.problems)}


class PostActivationMonitoringRehearsalV5Error(ValueError):
    def __init__(self, problems: Sequence[str]) -> None:
        self.problems = tuple(problems)
        super().__init__("invalid post-activation monitoring rehearsal v5: " + "; ".join(self.problems))


def load_post_activation_monitoring_rehearsal_v5_fixture(path: str | Path) -> dict[str, Any]:
    loaded = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(loaded, Mapping):
        raise ValueError("post-activation monitoring rehearsal v5 source fixture must be an object")
    return build_post_activation_monitoring_rehearsal_v5(loaded)


def assert_valid_post_activation_monitoring_rehearsal_v5(packet: Mapping[str, Any]) -> None:
    result = validate_post_activation_monitoring_rehearsal_v5(packet)
    if not result.valid:
        raise PostActivationMonitoringRehearsalV5Error(result.problems)


def build_post_activation_monitoring_rehearsal_v5(source_fixture: Mapping[str, Any]) -> dict[str, Any]:
    checklists = _mapping_sequence(source_fixture.get("inactive_activation_checklist_v5_fixtures"))
    if not checklists:
        raise ValueError("inactive_activation_checklist_v5_fixtures must be non-empty")
    for index, checklist in enumerate(checklists):
        _validate_inactive_checklist_fixture(index, checklist)

    refs = [_checklist_reference(checklist) for checklist in checklists]
    packet = {
        "packet_type": PACKET_TYPE,
        "packet_version": PACKET_VERSION,
        "packet_id": "post-activation-monitoring-rehearsal-v5-fixture",
        "mode": MODE,
        "consumes_only": {"inactive_activation_checklist_v5_fixtures": True},
        "boundaries": dict(REQUIRED_BOUNDARIES),
        "activation_checklist_references": refs,
        "guardrail_lookup_health_rows": [_guardrail_lookup_row(ref) for ref in refs],
        "stale_source_stop_gate_rows": [_stale_source_row(ref) for ref in refs],
        "exact_confirmation_gate_behavior_rows": [_exact_confirmation_row(ref) for ref in refs],
        "refused_consequential_and_financial_action_rows": [_refusal_row(ref) for ref in refs],
        "rollback_trigger_threshold_rows": [_rollback_threshold_row(ref) for ref in refs],
        "reviewer_escalation_routing_rows": [_reviewer_route_row(ref) for ref in refs],
        "agent_notification_routing_rows": [_agent_route_row(ref) for ref in refs],
        "exact_offline_validation_command_rows": [_validation_command_row(ref) for ref in refs],
        "attestations": dict(REQUIRED_ATTESTATIONS),
        "validation_commands": [list(command) for command in VALIDATION_COMMANDS],
    }
    assert_valid_post_activation_monitoring_rehearsal_v5(packet)
    return packet


def validate_post_activation_monitoring_rehearsal_v5(packet: Mapping[str, Any]) -> PostActivationMonitoringRehearsalV5Result:
    if not isinstance(packet, Mapping):
        return PostActivationMonitoringRehearsalV5Result(False, ("packet must be an object",))

    problems: list[str] = []
    if packet.get("packet_type") != PACKET_TYPE:
        problems.append(f"packet_type must be {PACKET_TYPE}")
    if packet.get("packet_version") != PACKET_VERSION:
        problems.append("packet_version must be v5")
    if packet.get("mode") != MODE:
        problems.append(f"mode must be {MODE}")
    if packet.get("consumes_only") != {"inactive_activation_checklist_v5_fixtures": True}:
        problems.append("consumes_only must allow only inactive activation checklist v5 fixtures")
    if packet.get("boundaries") != REQUIRED_BOUNDARIES:
        problems.append("boundaries must exactly declare fixture-only offline monitoring rehearsal limits")
    if packet.get("attestations") != REQUIRED_ATTESTATIONS:
        problems.append("attestations must deny activation, DevHub access, private documents, live crawling, official actions, financial actions, scheduling, and guarantees")
    if packet.get("validation_commands") != VALIDATION_COMMANDS:
        problems.append("validation_commands must contain only the PP&D daemon self-test command")

    checklist_refs = _activation_checklist_reference_ids(packet.get("activation_checklist_references"), problems)
    for section in REQUIRED_SECTIONS:
        _validate_referenced_section(section, packet.get(section), checklist_refs, problems)
    _scan_for_forbidden_payload(packet, "$", problems)
    return PostActivationMonitoringRehearsalV5Result(not problems, tuple(dict.fromkeys(problems)))


def _validate_inactive_checklist_fixture(index: int, checklist: Mapping[str, Any]) -> None:
    if checklist.get("packet_type") != INACTIVE_CHECKLIST_PACKET_TYPE:
        raise ValueError(f"inactive_activation_checklist_v5_fixtures[{index}].packet_type must be {INACTIVE_CHECKLIST_PACKET_TYPE}")
    if checklist.get("packet_version") != "v5":
        raise ValueError(f"inactive_activation_checklist_v5_fixtures[{index}].packet_version must be v5")
    if not _text(checklist.get("packet_id")):
        raise ValueError(f"inactive_activation_checklist_v5_fixtures[{index}].packet_id is required")
    if checklist.get("validation_commands") != VALIDATION_COMMANDS:
        raise ValueError(f"inactive_activation_checklist_v5_fixtures[{index}].validation_commands must contain only the daemon self-test command")
    for key in (
        "reviewer_controlled_activation_prerequisites",
        "source_freshness_hold_clearance_criteria",
        "rollback_checkpoint_rows",
        "post_activation_smoke_checks",
        "agent_notification_notes",
    ):
        if not _mapping_sequence(checklist.get(key)):
            raise ValueError(f"inactive_activation_checklist_v5_fixtures[{index}] must include non-empty {key}")
    fixture_problems: list[str] = []
    _scan_for_forbidden_payload(checklist, f"inactive_activation_checklist_v5_fixtures[{index}]", fixture_problems)
    if fixture_problems:
        raise ValueError(fixture_problems[0])


def _checklist_reference(checklist: Mapping[str, Any]) -> dict[str, str]:
    packet_id = _text(checklist.get("packet_id"))
    return {
        "activation_checklist_reference_id": _stable_id("inactive-checklist-v5", packet_id),
        "source_packet_id": packet_id,
        "source_packet_type": INACTIVE_CHECKLIST_PACKET_TYPE,
    }


def _guardrail_lookup_row(ref: Mapping[str, str]) -> dict[str, str]:
    return {
        "monitoring_row_id": _stable_id("guardrail-lookup-health", ref["activation_checklist_reference_id"]),
        "source_activation_checklist_reference": ref["activation_checklist_reference_id"],
        "lookup_name": "compiled_guardrail_bundle_lookup",
        "expected_status": "synthetic_lookup_row_present_offline",
    }


def _stale_source_row(ref: Mapping[str, str]) -> dict[str, str]:
    return {
        "monitoring_row_id": _stable_id("stale-source-stop", ref["activation_checklist_reference_id"]),
        "source_activation_checklist_reference": ref["activation_checklist_reference_id"],
        "stale_condition": "source_freshness_hold_or_unknown_public_source_age",
        "expected_result": "agent_blocks_until_source_refresh_or_reviewer_disposition",
    }


def _exact_confirmation_row(ref: Mapping[str, str]) -> dict[str, str]:
    return {
        "monitoring_row_id": _stable_id("exact-confirmation-gate", ref["activation_checklist_reference_id"]),
        "source_activation_checklist_reference": ref["activation_checklist_reference_id"],
        "action_class": "consequential_official_step",
        "expected_result": "exact_confirmation_required_before_consequential_step",
    }


def _refusal_row(ref: Mapping[str, str]) -> dict[str, str]:
    return {
        "monitoring_row_id": _stable_id("refused-action", ref["activation_checklist_reference_id"]),
        "source_activation_checklist_reference": ref["activation_checklist_reference_id"],
        "action_class": "consequential_or_financial_action",
        "expected_result": "refused_without_user_attendance_and_exact_confirmation",
    }


def _rollback_threshold_row(ref: Mapping[str, str]) -> dict[str, str]:
    return {
        "monitoring_row_id": _stable_id("rollback-threshold", ref["activation_checklist_reference_id"]),
        "source_activation_checklist_reference": ref["activation_checklist_reference_id"],
        "threshold": "any_guardrail_lookup_failure_or_stale_source_gate_regression",
        "expected_result": "rollback_reviewer_hold",
    }


def _reviewer_route_row(ref: Mapping[str, str]) -> dict[str, str]:
    return {
        "monitoring_row_id": _stable_id("reviewer-route", ref["activation_checklist_reference_id"]),
        "source_activation_checklist_reference": ref["activation_checklist_reference_id"],
        "reviewer_role": "TBD_RELEASE_REVIEWER",
        "expected_route": "human_reviewer_queue",
    }


def _agent_route_row(ref: Mapping[str, str]) -> dict[str, str]:
    return {
        "monitoring_row_id": _stable_id("agent-route", ref["activation_checklist_reference_id"]),
        "source_activation_checklist_reference": ref["activation_checklist_reference_id"],
        "agent_channel": "guarded_agent_consumer_notifications",
        "expected_route": "agent_consumer_notice_queue",
    }


def _validation_command_row(ref: Mapping[str, str]) -> dict[str, str]:
    return {
        "monitoring_row_id": _stable_id("offline-validation-command", ref["activation_checklist_reference_id"]),
        "source_activation_checklist_reference": ref["activation_checklist_reference_id"],
        "command_label": "python3 ppd/daemon/ppd_daemon.py --self-test",
        "expected_result": "only_daemon_self_test_allowed",
    }


def _activation_checklist_reference_ids(value: Any, problems: list[str]) -> set[str]:
    rows = _required_mapping_rows("activation_checklist_references", value, problems)
    refs: set[str] = set()
    for index, row in enumerate(rows):
        prefix = f"activation_checklist_references[{index}]"
        _require_text_fields(row, prefix, REQUIRED_TEXT_FIELDS["activation_checklist_references"], problems)
        if row.get("source_packet_type") != INACTIVE_CHECKLIST_PACKET_TYPE:
            problems.append(f"{prefix}.source_packet_type must be {INACTIVE_CHECKLIST_PACKET_TYPE}")
        ref_id = _text(row.get("activation_checklist_reference_id"))
        if ref_id:
            refs.add(ref_id)
    if len(refs) != len(rows):
        problems.append("activation_checklist_references must have unique non-empty activation_checklist_reference_id values")
    return refs


def _validate_referenced_section(section: str, value: Any, checklist_refs: set[str], problems: list[str]) -> None:
    rows = _required_mapping_rows(section, value, problems)
    observed_refs: set[str] = set()
    for index, row in enumerate(rows):
        prefix = f"{section}[{index}]"
        _require_text_fields(row, prefix, REQUIRED_TEXT_FIELDS[section], problems)
        source_ref = _text(row.get("source_activation_checklist_reference"))
        if source_ref:
            observed_refs.add(source_ref)
            if checklist_refs and source_ref not in checklist_refs:
                problems.append(f"{prefix}.source_activation_checklist_reference references unknown activation checklist reference {source_ref}")
        for field, expected in EXPECTED_VALUES[section].items():
            if row.get(field) != expected:
                problems.append(f"{prefix}.{field} must be {expected}")
    for missing_ref in sorted(checklist_refs - observed_refs):
        problems.append(f"{section} missing activation checklist reference {missing_ref}")


def _required_mapping_rows(section: str, value: Any, problems: list[str]) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)) or not value:
        problems.append(f"{section} must be a non-empty list")
        return []
    rows: list[Mapping[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            problems.append(f"{section}[{index}] must be an object")
            continue
        rows.append(item)
    return rows


def _require_text_fields(row: Mapping[str, Any], prefix: str, fields: Sequence[str], problems: list[str]) -> None:
    for field in fields:
        if not _text(row.get(field)):
            problems.append(f"{prefix}.{field} must be non-empty")


def _mapping_sequence(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _truthy(value: Any) -> bool:
    if value is None or value is False or value == "":
        return False
    if isinstance(value, Mapping) and not value:
        return False
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)) and not value:
        return False
    return True


def _stable_id(prefix: str, value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


def _scan_for_forbidden_payload(value: Any, path: str, problems: list[str]) -> None:
    if isinstance(value, Mapping):
        for raw_key, child in value.items():
            key = str(raw_key)
            normalized_key = key.lower().replace("-", "_")
            child_path = f"{path}.{key}" if path != "$" else key
            if normalized_key in FORBIDDEN_TRUE_KEYS and child is True:
                problems.append(f"{child_path} must not be true")
            if "mutation" in normalized_key and child is True:
                problems.append(f"{child_path} must not enable mutation")
            if PRIVATE_KEY_RE.search(normalized_key) and _truthy(child):
                problems.append(f"{child_path} must not contain private, session, auth, raw, browser, trace, or downloaded artifacts")
            _scan_for_forbidden_payload(child, child_path, problems)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _scan_for_forbidden_payload(child, f"{path}[{index}]", problems)
        return
    if isinstance(value, str) and FORBIDDEN_TEXT_RE.search(value):
        problems.append(f"{path} contains a prohibited activation, live, official-action, private-artifact, or guarantee claim")
