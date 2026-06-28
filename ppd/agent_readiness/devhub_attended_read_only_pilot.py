"""Validation for DevHub attended read-only pilot launch readiness packets."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePath
from typing import Any, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class LaunchReadinessViolation:
    """A deterministic launch-readiness validation problem."""

    code: str
    path: str
    message: str


class LaunchReadinessError(ValueError):
    """Raised when a DevHub attended read-only pilot packet is not launch-ready."""

    def __init__(self, violations: Sequence[LaunchReadinessViolation]) -> None:
        self.violations = tuple(violations)
        codes = ", ".join(violation.code for violation in self.violations)
        super().__init__(f"DevHub attended read-only pilot launch readiness rejected: {codes}")


CONSEQUENTIAL_TERMS = (
    "submit",
    "certify",
    "acknowledge",
    "upload",
    "attach",
    "payment",
    "pay",
    "purchase",
    "schedule",
    "cancel",
    "withdraw",
    "reactivate",
    "extension",
    "inspection",
)

LIVE_EXECUTION_TERMS = (
    "live browser",
    "browser executed",
    "playwright executed",
    "clicked in devhub",
    "filled in devhub",
    "ran against devhub",
    "opened devhub",
    "launched browser",
)

PRIVATE_KEY_TERMS = (
    "password",
    "credential",
    "cookie",
    "token",
    "secret",
    "session",
    "storage_state",
    "auth_state",
)

RAW_VALUE_KEY_TERMS = (
    "raw_authenticated_value",
    "raw_authenticated_values",
    "authenticated_value",
    "private_value",
    "field_value",
    "raw_value",
)

SCREENSHOT_TERMS = ("screenshot", ".png", ".jpg", ".jpeg", ".webp")
TRACE_HAR_TERMS = ("trace.zip", "trace/", ".har", "har_path", "network.har")
AUTH_STATE_TERMS = ("storage_state", "auth_state", "cookies.json", "playwright/.auth")

REQUIRED_REDACTION_CHECKS = frozenset(
    {
        "no_auth_state",
        "no_screenshots",
        "no_traces_or_har_files",
        "no_raw_authenticated_values",
    }
)


def validate_launch_readiness_packet(packet: Mapping[str, Any]) -> None:
    """Raise if a DevHub attended read-only pilot packet is unsafe to launch."""

    violations = list(iter_launch_readiness_violations(packet))
    if violations:
        raise LaunchReadinessError(violations)


def packet_is_launch_ready(packet: Mapping[str, Any]) -> bool:
    """Return True only when the packet satisfies all launch-readiness checks."""

    return not any(iter_launch_readiness_violations(packet))


def iter_launch_readiness_violations(packet: Mapping[str, Any]) -> Iterable[LaunchReadinessViolation]:
    if not isinstance(packet, Mapping):
        yield LaunchReadinessViolation("invalid_packet", "$", "Launch readiness packet must be a mapping.")
        return

    yield from _validate_attendance_prerequisites(packet)
    yield from _validate_manual_stop_points(packet)
    yield from _validate_selector_confidence_notes(packet)
    yield from _validate_redaction_checklist(packet)
    yield from _validate_reviewer_owners(packet)
    yield from _scan_for_forbidden_values(packet)
    yield from _validate_consequential_controls(packet)
    yield from _validate_mutation_flags(packet)


def _validate_attendance_prerequisites(packet: Mapping[str, Any]) -> Iterable[LaunchReadinessViolation]:
    prerequisites = packet.get("attendance_prerequisites")
    if packet.get("manual_attendance_required") is not True or not _non_empty_sequence(prerequisites):
        yield LaunchReadinessViolation(
            "missing_attendance_prerequisite",
            "$.attendance_prerequisites",
            "Launch packets require manual attendance and at least one cited attendance prerequisite.",
        )
        return

    for index, prerequisite in enumerate(prerequisites):
        path = f"$.attendance_prerequisites[{index}]"
        if not isinstance(prerequisite, Mapping):
            yield LaunchReadinessViolation("missing_attendance_prerequisite", path, "Attendance prerequisites must be mappings.")
            continue
        if prerequisite.get("required_before_launch") is not True or prerequisite.get("operator_present") is not True:
            yield LaunchReadinessViolation(
                "missing_attendance_prerequisite",
                path,
                "Attendance prerequisites must require pre-launch operator presence.",
            )
        if not _has_citation(prerequisite):
            yield LaunchReadinessViolation(
                "missing_attendance_prerequisite",
                path,
                "Attendance prerequisites must cite source evidence.",
            )


def _validate_manual_stop_points(packet: Mapping[str, Any]) -> Iterable[LaunchReadinessViolation]:
    stop_points = packet.get("manual_stop_points")
    if not _non_empty_sequence(stop_points):
        yield LaunchReadinessViolation(
            "missing_manual_stop_point",
            "$.manual_stop_points",
            "Launch packets require cited manual stop points.",
        )
        return

    trigger_text = " ".join(str(item.get("trigger", "")).lower() for item in stop_points if isinstance(item, Mapping))
    required_terms = ("credential", "consequential", "private")
    if not all(term in trigger_text for term in required_terms):
        yield LaunchReadinessViolation(
            "missing_manual_stop_point",
            "$.manual_stop_points",
            "Manual stop points must cover credentials, consequential controls, and private artifacts.",
        )

    for index, stop_point in enumerate(stop_points):
        path = f"$.manual_stop_points[{index}]"
        if not isinstance(stop_point, Mapping) or not _has_citation(stop_point):
            yield LaunchReadinessViolation("missing_manual_stop_point", path, "Manual stop points must be cited mappings.")
        elif stop_point.get("official_action_allowed_after_stop") is not False:
            yield LaunchReadinessViolation(
                "missing_manual_stop_point",
                path,
                "Manual stop points must fail closed for official actions.",
            )


def _validate_selector_confidence_notes(packet: Mapping[str, Any]) -> Iterable[LaunchReadinessViolation]:
    notes = packet.get("selector_confidence_notes")
    if not _non_empty_sequence(notes):
        yield LaunchReadinessViolation(
            "uncited_selector_confidence_note",
            "$.selector_confidence_notes",
            "Launch packets require cited selector confidence notes.",
        )
        return

    for index, note in enumerate(notes):
        path = f"$.selector_confidence_notes[{index}]"
        if not isinstance(note, Mapping) or not _has_citation(note):
            yield LaunchReadinessViolation(
                "uncited_selector_confidence_note",
                path,
                "Selector confidence notes must cite evidence.",
            )


def _validate_redaction_checklist(packet: Mapping[str, Any]) -> Iterable[LaunchReadinessViolation]:
    checks = packet.get("redaction_checklist_items")
    if not _non_empty_sequence(checks):
        yield LaunchReadinessViolation(
            "missing_redaction_checklist_item",
            "$.redaction_checklist_items",
            "Launch packets require redaction checklist items.",
        )
        return

    seen = set()
    for index, check in enumerate(checks):
        path = f"$.redaction_checklist_items[{index}]"
        if not isinstance(check, Mapping):
            yield LaunchReadinessViolation("missing_redaction_checklist_item", path, "Redaction checklist items must be mappings.")
            continue
        check_id = str(check.get("check_id", ""))
        seen.add(check_id)
        if check.get("required") is not True or check.get("raw_value_allowed") is not False or check.get("private_value_allowed") is not False:
            yield LaunchReadinessViolation(
                "missing_redaction_checklist_item",
                path,
                "Redaction checklist items must be required and disallow raw/private values.",
            )
        if not _has_citation(check):
            yield LaunchReadinessViolation("missing_redaction_checklist_item", path, "Redaction checklist items must cite evidence.")

    missing = REQUIRED_REDACTION_CHECKS - seen
    if missing:
        yield LaunchReadinessViolation(
            "missing_redaction_checklist_item",
            "$.redaction_checklist_items",
            f"Missing required redaction checklist items: {', '.join(sorted(missing))}.",
        )


def _validate_reviewer_owners(packet: Mapping[str, Any]) -> Iterable[LaunchReadinessViolation]:
    owners = packet.get("reviewer_owner_signoff_slots")
    if not _non_empty_sequence(owners):
        yield LaunchReadinessViolation(
            "missing_reviewer_owner",
            "$.reviewer_owner_signoff_slots",
            "Launch packets require reviewer owner signoff slots.",
        )
        return

    for index, owner in enumerate(owners):
        path = f"$.reviewer_owner_signoff_slots[{index}]"
        if not isinstance(owner, Mapping) or not str(owner.get("owner", "")).strip():
            yield LaunchReadinessViolation("missing_reviewer_owner", path, "Reviewer signoff slots require an owner.")
        elif owner.get("can_enable_official_action") is not False:
            yield LaunchReadinessViolation(
                "missing_reviewer_owner",
                path,
                "Reviewer signoff slots cannot enable official actions for a read-only pilot.",
            )


def _scan_for_forbidden_values(value: Any, path: str = "$", key_hint: str = "") -> Iterable[LaunchReadinessViolation]:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            lowered_key = key_text.lower().replace("-", "_")
            if lowered_key in RAW_VALUE_KEY_TERMS and _is_present(child):
                yield LaunchReadinessViolation("raw_authenticated_value", child_path, "Raw authenticated values are not allowed.")
            if any(term in lowered_key for term in PRIVATE_KEY_TERMS) and _is_present(child):
                yield LaunchReadinessViolation("private_or_session_artifact", child_path, "Private/session artifacts are not allowed.")
            yield from _scan_for_forbidden_values(child, child_path, lowered_key)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _scan_for_forbidden_values(child, f"{path}[{index}]", key_hint)
    elif isinstance(value, str):
        lowered = value.lower()
        if any(term in lowered for term in SCREENSHOT_TERMS):
            yield LaunchReadinessViolation("screenshot_artifact", path, "Screenshot artifacts are not allowed.")
        if any(term in lowered for term in TRACE_HAR_TERMS):
            yield LaunchReadinessViolation("trace_or_har_artifact", path, "Trace and HAR artifacts are not allowed.")
        if any(term in lowered for term in AUTH_STATE_TERMS):
            yield LaunchReadinessViolation("stored_auth_state", path, "Stored auth state is not allowed.")
        if any(term in lowered for term in LIVE_EXECUTION_TERMS):
            yield LaunchReadinessViolation("live_browser_execution_claim", path, "Live browser execution claims are not allowed.")
        if _looks_like_private_path(value):
            yield LaunchReadinessViolation("local_private_path", path, "Local private paths are not allowed.")


def _validate_consequential_controls(packet: Mapping[str, Any]) -> Iterable[LaunchReadinessViolation]:
    controls = packet.get("controls") or packet.get("consequential_controls") or []
    if not _non_empty_sequence(controls):
        return

    for index, control in enumerate(controls):
        path = f"$.controls[{index}]"
        if not isinstance(control, Mapping):
            continue
        label = str(control.get("label") or control.get("name") or control.get("action") or "").lower()
        kind = str(control.get("kind") or control.get("classification") or "").lower()
        is_consequential = "consequential" in kind or any(term in label for term in CONSEQUENTIAL_TERMS)
        is_enabled = control.get("enabled") is True or control.get("disabled") is False
        if is_consequential and is_enabled:
            yield LaunchReadinessViolation(
                "enabled_consequential_control",
                path,
                "Consequential controls must be absent or disabled.",
            )


def _validate_mutation_flags(packet: Mapping[str, Any]) -> Iterable[LaunchReadinessViolation]:
    yield from _flag_if_active(packet, ("mutates_surface_registry", "surface_registry_mutation_enabled", "active_surface_registry_mutation"), "active_surface_registry_mutation_flag")
    yield from _flag_if_active(packet, ("mutates_agent_state", "agent_state_mutation_enabled", "active_agent_state_mutation"), "active_agent_state_mutation_flag")


def _flag_if_active(packet: Mapping[str, Any], keys: Sequence[str], code: str) -> Iterable[LaunchReadinessViolation]:
    for key in keys:
        if packet.get(key) is True:
            yield LaunchReadinessViolation(code, f"$.{key}", "Read-only pilot launch packets cannot enable mutation flags.")


def _has_citation(value: Mapping[str, Any]) -> bool:
    for key in ("citation", "citations", "source_evidence_id", "source_evidence_ids", "evidence", "evidence_ids"):
        if key in value and _is_present(value[key]):
            return True
    return False


def _is_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return bool(value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return bool(value)
    return True


def _non_empty_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)) and bool(value)


def _looks_like_private_path(value: str) -> bool:
    lowered = value.lower().replace("\\", "/")
    if lowered.startswith(("/home/", "/users/", "c:/users/", "file:///")):
        return True
    if "/.auth/" in lowered or "/private/" in lowered or "/session" in lowered:
        return True
    if "/" not in lowered:
        return False
    name = PurePath(lowered).name
    return name.endswith((".har", ".png", ".jpg", ".jpeg", ".webp", "cookies.json", "storage_state.json"))
