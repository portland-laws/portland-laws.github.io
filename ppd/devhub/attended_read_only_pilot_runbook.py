from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from ppd.devhub.read_only_observation_packet import assert_devhub_read_only_observation_packet
from ppd.devhub.read_only_pilot_operator_checklist import assert_valid_operator_checklist
from ppd.devhub.read_only_surface_drift_comparison_packet import assert_valid_read_only_surface_drift_comparison_packet


REQUIRED_PACKET_ID = "devhub-attended-read-only-pilot-runbook-v1"
REQUIRED_PACKET_TYPE = "devhub_attended_read_only_pilot_runbook"
REQUIRED_MODE = "fixture_first_attended_read_only_pilot_runbook"
REQUIRED_SOURCE_PACKET_KEYS = (
    "devhub_read_only_pilot_operator_checklist",
    "devhub_read_only_observation_packet",
    "devhub_read_only_surface_drift_comparison_packet",
)
REQUIRED_STEP_IDS = (
    "fixture_input_crosscheck",
    "manual_login_boundary",
    "read_only_scope_boundary",
    "redaction_preflight",
    "page_observation_entry",
    "surface_drift_reviewer_checkpoint",
    "abort_and_refusal_gate",
    "closeout_without_artifacts",
)
REQUIRED_PAGE_OBSERVATION_FIELDS = (
    "stable_surface_id",
    "page_heading",
    "route_pattern",
    "accessible_landmark_summary",
    "synthetic_record_status_label",
    "disabled_consequential_controls",
    "operator_decision_code",
    "redacted_timestamp",
)
REQUIRED_REDACTION_CHECKS = (
    "no_credentials",
    "no_credential_prompts",
    "no_cookies",
    "no_auth_state",
    "no_session_state",
    "no_screenshots",
    "no_traces",
    "no_har_files",
    "no_downloads",
    "no_raw_dom",
    "no_raw_authenticated_text",
    "no_private_field_values",
    "no_local_private_paths",
    "no_payment_details",
)
REQUIRED_REVIEWER_CHECKPOINTS = (
    "manual_login_boundary_review",
    "redaction_review",
    "page_observation_review",
    "surface_drift_review",
    "selector_confidence_review",
    "consequential_control_review",
    "closeout_review",
)
REQUIRED_ABORT_TERMS = (
    "credential",
    "mfa",
    "captcha",
    "account creation",
    "payment",
    "upload",
    "submit",
    "certify",
    "schedule",
    "cancel",
    "raw authenticated",
    "auth state",
    "screenshot",
    "trace",
    "har",
    "browser artifact",
)
PROHIBITED_TRUE_FLAGS = frozenset(
    {
        "launches_browser",
        "launches_playwright",
        "stores_private_session_state",
        "stores_browser_artifacts",
        "stores_auth_state",
        "stores_screenshots",
        "stores_traces",
        "stores_har_files",
        "stores_raw_authenticated_values",
        "captures_screenshots",
        "captures_traces",
        "captures_har_files",
        "stores_cookies",
        "stores_session_state",
        "saves_storage_state",
        "uses_stored_auth_state",
        "live_browser_execution",
        "browser_execution_enabled",
        "playwright_execution_enabled",
        "agent_may_automate_mfa_or_captcha",
        "account_creation_allowed",
        "captcha_automation_allowed",
        "mfa_automation_allowed",
    }
)
ENABLED_CONSEQUENTIAL_FLAGS = frozenset(
    {
        "upload_enabled",
        "uploads_enabled",
        "official_upload_enabled",
        "submission_enabled",
        "submit_enabled",
        "payment_enabled",
        "payments_enabled",
        "scheduling_enabled",
        "schedule_enabled",
        "cancellation_enabled",
        "cancel_enabled",
        "certification_enabled",
        "certify_enabled",
    }
)
PROHIBITED_ARTIFACT_KEY_MARKERS = (
    "screenshot",
    "trace",
    "har",
    "storage_state",
    "auth_state",
    "session_state",
    "cookie",
    "download_path",
    "downloaded_document",
    "browser_artifact",
    "raw_authenticated",
)
PRIVATE_PATH_MARKERS = (
    "/home/",
    "/users/",
    "c:\\",
    "d:\\",
    "file://",
    ".auth/",
    "storage_state",
    "storage-state",
    "trace.zip",
    ".har",
    ".png",
    ".webm",
)


@dataclass(frozen=True)
class RunbookValidationResult:
    packet_id: str
    ok: bool
    errors: tuple[str, ...]


def load_runbook_packet(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("runbook packet must be a JSON object")
    return data


def load_json_packet(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("packet must be a JSON object")
    return data


def build_attended_read_only_pilot_runbook(
    operator_checklist: Mapping[str, Any],
    observation_packet: Mapping[str, Any],
    drift_comparison_packet: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a commit-safe synthetic attended read-only pilot runbook."""

    assert_valid_operator_checklist(operator_checklist)
    assert_devhub_read_only_observation_packet(observation_packet)
    assert_valid_read_only_surface_drift_comparison_packet(drift_comparison_packet)

    operator_packet_id = _text(operator_checklist.get("packet_id"))
    observation_packet_id = _text(observation_packet.get("packet_id"))
    drift_packet_id = _text(drift_comparison_packet.get("packet_id"))

    return {
        "packet_id": REQUIRED_PACKET_ID,
        "packet_type": REQUIRED_PACKET_TYPE,
        "mode": REQUIRED_MODE,
        "fixture_first": True,
        "read_only_only": True,
        "manual_attendance_required": True,
        "launches_browser": False,
        "launches_playwright": False,
        "stores_private_session_state": False,
        "stores_browser_artifacts": False,
        "stores_auth_state": False,
        "stores_screenshots": False,
        "stores_traces": False,
        "stores_har_files": False,
        "stores_raw_authenticated_values": False,
        "source_packets": {
            "devhub_read_only_pilot_operator_checklist": {"packet_id": operator_packet_id, "consumed": True},
            "devhub_read_only_observation_packet": {"packet_id": observation_packet_id, "consumed": True},
            "devhub_read_only_surface_drift_comparison_packet": {"packet_id": drift_packet_id, "consumed": True},
        },
        "synthetic_attended_pilot_steps": _pilot_steps(operator_packet_id, observation_packet_id, drift_packet_id),
        "manual_login_boundaries": _manual_login_boundaries(operator_packet_id),
        "page_observation_fields": _page_observation_fields(observation_packet_id, drift_packet_id),
        "redaction_checks": _redaction_checks(operator_packet_id, observation_packet_id),
        "reviewer_checkpoints": _reviewer_checkpoints(operator_packet_id, observation_packet_id, drift_packet_id),
        "abort_prompts": _abort_prompts(operator_packet_id),
        "closeout_attestations": {
            "official_state_changed": False,
            "browser_artifacts_created_for_storage": False,
            "auth_state_saved": False,
            "screenshots_saved": False,
            "traces_saved": False,
            "har_files_saved": False,
            "raw_authenticated_values_saved": False,
            "next_actions_limited_to": ["read_only_review", "local_preview", "manual_reviewer_decision"],
        },
    }


def validate_runbook_packet(packet: Mapping[str, Any]) -> RunbookValidationResult:
    errors: list[str] = []
    packet_id = _text(packet.get("packet_id"))

    _require(errors, packet_id == REQUIRED_PACKET_ID, "packet_id must identify the attended read-only pilot runbook")
    _require(errors, packet.get("packet_type") == REQUIRED_PACKET_TYPE, "packet_type must be devhub_attended_read_only_pilot_runbook")
    _require(errors, packet.get("mode") == REQUIRED_MODE, "mode must be fixture_first_attended_read_only_pilot_runbook")
    for flag in ("fixture_first", "read_only_only", "manual_attendance_required"):
        _require(errors, packet.get(flag) is True, f"{flag} must be true")
    for flag in (
        "launches_browser",
        "launches_playwright",
        "stores_private_session_state",
        "stores_browser_artifacts",
        "stores_auth_state",
        "stores_screenshots",
        "stores_traces",
        "stores_har_files",
        "stores_raw_authenticated_values",
    ):
        _require(errors, packet.get(flag) is False, f"{flag} must be false")

    _validate_source_packets(errors, _mapping(packet.get("source_packets")))
    _validate_steps(errors, _sequence(packet.get("synthetic_attended_pilot_steps")))
    _validate_manual_login_boundaries(errors, _sequence(packet.get("manual_login_boundaries")))
    _validate_page_fields(errors, _sequence(packet.get("page_observation_fields")))
    _validate_redaction_checks(errors, _sequence(packet.get("redaction_checks")))
    _validate_reviewer_checkpoints(errors, _sequence(packet.get("reviewer_checkpoints")))
    _validate_abort_prompts(errors, _string_tuple(packet.get("abort_prompts")))
    _validate_candidate_safety(errors, packet)

    closeout = _mapping(packet.get("closeout_attestations"))
    for flag in (
        "official_state_changed",
        "browser_artifacts_created_for_storage",
        "auth_state_saved",
        "screenshots_saved",
        "traces_saved",
        "har_files_saved",
        "raw_authenticated_values_saved",
    ):
        _require(errors, closeout.get(flag) is False, f"closeout_attestations.{flag} must be false")
    _require(
        errors,
        closeout.get("next_actions_limited_to") == ["read_only_review", "local_preview", "manual_reviewer_decision"],
        "closeout_attestations.next_actions_limited_to must stay read-only/local/manual",
    )

    return RunbookValidationResult(packet_id=packet_id, ok=not errors, errors=tuple(_dedupe(errors)))


def assert_valid_runbook_packet(packet: Mapping[str, Any]) -> None:
    result = validate_runbook_packet(packet)
    if not result.ok:
        raise AssertionError("; ".join(result.errors))


def _pilot_steps(operator_packet_id: str, observation_packet_id: str, drift_packet_id: str) -> list[dict[str, Any]]:
    step_text = {
        "fixture_input_crosscheck": "Confirm the operator checklist, read-only observation packet, and surface drift comparison packet identifiers before scheduling an attended pilot.",
        "manual_login_boundary": "Human operator opens DevHub in their own browser and handles sign-in, credentials, MFA, CAPTCHA, and security prompts manually.",
        "read_only_scope_boundary": "Limit the pilot to read-only home, list, detail, status, heading, landmark, and disabled-control observation fields.",
        "redaction_preflight": "Verify that only synthetic metadata fields will be written and that no browser, session, or raw authenticated artifact will be stored.",
        "page_observation_entry": "Transcribe only allowed page-observation fields using redacted labels and synthetic status categories.",
        "surface_drift_reviewer_checkpoint": "Compare redacted route, heading, disabled-control, and selector-confidence notes against the drift comparison packet without mutating registry state.",
        "abort_and_refusal_gate": "Stop and write only a commit-safe refusal summary if any abort prompt appears.",
        "closeout_without_artifacts": "Close the manual browser session without saving auth state, screenshots, traces, HAR files, downloads, raw DOM, or raw authenticated values.",
    }
    source_by_step = {
        "fixture_input_crosscheck": [operator_packet_id, observation_packet_id, drift_packet_id],
        "manual_login_boundary": [operator_packet_id],
        "read_only_scope_boundary": [operator_packet_id, observation_packet_id],
        "redaction_preflight": [operator_packet_id, observation_packet_id],
        "page_observation_entry": [observation_packet_id],
        "surface_drift_reviewer_checkpoint": [drift_packet_id],
        "abort_and_refusal_gate": [operator_packet_id],
        "closeout_without_artifacts": [operator_packet_id, observation_packet_id, drift_packet_id],
    }
    return [
        {
            "step_id": step_id,
            "manual_action": step_text[step_id],
            "source_packet_ids": source_by_step[step_id],
            "operator_attendance_required": True,
            "automated": False,
            "browser_launch_allowed_by_runbook": False,
            "playwright_allowed": False,
            "stores_browser_artifacts": False,
            "stores_private_values": False,
            "allows_consequential_action": False,
        }
        for step_id in REQUIRED_STEP_IDS
    ]


def _manual_login_boundaries(operator_packet_id: str) -> list[dict[str, Any]]:
    return [
        {
            "boundary_id": "portlandoregon_gov_login_manual_only",
            "source_packet_ids": [operator_packet_id],
            "human_operator_required": True,
            "agent_may_request_credentials": False,
            "agent_may_store_credentials": False,
            "agent_may_automate_mfa_or_captcha": False,
            "account_creation_allowed": False,
            "browser_state_storage_allowed": False,
            "prompt": "The operator completes login and security prompts manually; the runbook records no credential, MFA, CAPTCHA, cookie, or auth state value.",
        }
    ]


def _page_observation_fields(observation_packet_id: str, drift_packet_id: str) -> list[dict[str, Any]]:
    fields = []
    for field_id in REQUIRED_PAGE_OBSERVATION_FIELDS:
        fields.append(
            {
                "field_id": field_id,
                "source_packet_ids": [observation_packet_id, drift_packet_id],
                "raw_value_allowed": False,
                "private_value_allowed": False,
                "review_required": True,
            }
        )
    return fields


def _redaction_checks(operator_packet_id: str, observation_packet_id: str) -> list[dict[str, Any]]:
    return [
        {
            "check_id": check_id,
            "source_packet_ids": [operator_packet_id, observation_packet_id],
            "required": True,
            "passes_when": "The runbook stores only redacted synthetic metadata and omits the prohibited value or artifact.",
        }
        for check_id in REQUIRED_REDACTION_CHECKS
    ]


def _reviewer_checkpoints(operator_packet_id: str, observation_packet_id: str, drift_packet_id: str) -> list[dict[str, Any]]:
    sources = {
        "manual_login_boundary_review": [operator_packet_id],
        "redaction_review": [operator_packet_id, observation_packet_id],
        "page_observation_review": [observation_packet_id],
        "surface_drift_review": [drift_packet_id],
        "selector_confidence_review": [drift_packet_id],
        "consequential_control_review": [operator_packet_id, observation_packet_id, drift_packet_id],
        "closeout_review": [operator_packet_id, observation_packet_id, drift_packet_id],
    }
    return [
        {
            "checkpoint_id": checkpoint_id,
            "reviewer_role": "ppd-devhub-read-only-reviewer",
            "source_packet_ids": sources[checkpoint_id],
            "required_before_pilot_closeout": True,
            "approval_can_enable_official_action": False,
        }
        for checkpoint_id in REQUIRED_REVIEWER_CHECKPOINTS
    ]


def _abort_prompts(operator_packet_id: str) -> list[str]:
    return [
        "Abort if a credential, MFA, CAPTCHA, password recovery, or account creation prompt would require automation or recording rather than manual operator handling.",
        "Abort if any payment, upload, submit, certify, schedule, cancel, withdraw, extension, reactivation, or account security control is in scope.",
        "Abort if raw authenticated text, raw DOM, private field values, local private paths, downloads, auth state, cookies, screenshot, trace, HAR, or any browser artifact would be stored.",
        "Abort on timeout, unexpected private account data, or any request to treat the fixture-first runbook as live browser execution.",
        "Record only a commit-safe refusal reason citing the operator checklist packet " + operator_packet_id + ".",
    ]


def _validate_source_packets(errors: list[str], source_packets: Mapping[str, Any]) -> None:
    for key in REQUIRED_SOURCE_PACKET_KEYS:
        source = _mapping(source_packets.get(key))
        _require(errors, bool(_text(source.get("packet_id"))), f"source_packets.{key}.packet_id is required")
        _require(errors, source.get("consumed") is True, f"source_packets.{key}.consumed must be true")


def _validate_steps(errors: list[str], steps: Sequence[Any]) -> None:
    step_ids = tuple(_text(_mapping(step).get("step_id")) for step in steps)
    missing = [step_id for step_id in REQUIRED_STEP_IDS if step_id not in step_ids]
    if missing:
        errors.append("synthetic_attended_pilot_steps missing required steps: " + ", ".join(missing))
    for index, step_value in enumerate(steps):
        step = _mapping(step_value)
        path = f"synthetic_attended_pilot_steps[{index}]"
        _require(errors, bool(_text(step.get("manual_action"))), f"{path}.manual_action is required")
        _require(errors, bool(_sequence(step.get("source_packet_ids"))), f"{path}.source_packet_ids must not be empty")
        _require(errors, step.get("operator_attendance_required") is True, f"{path}.operator_attendance_required must be true")
        for flag in (
            "automated",
            "browser_launch_allowed_by_runbook",
            "playwright_allowed",
            "stores_browser_artifacts",
            "stores_private_values",
            "allows_consequential_action",
        ):
            _require(errors, step.get(flag) is False, f"{path}.{flag} must be false")


def _validate_manual_login_boundaries(errors: list[str], boundaries: Sequence[Any]) -> None:
    _require(errors, bool(boundaries), "manual_login_boundaries must not be empty")
    for index, boundary_value in enumerate(boundaries):
        boundary = _mapping(boundary_value)
        path = f"manual_login_boundaries[{index}]"
        _require(errors, boundary.get("human_operator_required") is True, f"{path}.human_operator_required must be true")
        for flag in (
            "agent_may_request_credentials",
            "agent_may_store_credentials",
            "agent_may_automate_mfa_or_captcha",
            "account_creation_allowed",
            "browser_state_storage_allowed",
        ):
            _require(errors, boundary.get(flag) is False, f"{path}.{flag} must be false")


def _validate_page_fields(errors: list[str], fields: Sequence[Any]) -> None:
    field_ids = tuple(_text(_mapping(field).get("field_id")) for field in fields)
    missing = [field_id for field_id in REQUIRED_PAGE_OBSERVATION_FIELDS if field_id not in field_ids]
    if missing:
        errors.append("page_observation_fields missing: " + ", ".join(missing))
    for index, field_value in enumerate(fields):
        field = _mapping(field_value)
        path = f"page_observation_fields[{index}]"
        _require(errors, bool(_sequence(field.get("source_packet_ids"))), f"{path}.source_packet_ids must not be empty")
        _require(errors, field.get("raw_value_allowed") is False, f"{path}.raw_value_allowed must be false")
        _require(errors, field.get("private_value_allowed") is False, f"{path}.private_value_allowed must be false")
        _require(errors, field.get("review_required") is True, f"{path}.review_required must be true")


def _validate_redaction_checks(errors: list[str], checks: Sequence[Any]) -> None:
    check_ids = tuple(_text(_mapping(check).get("check_id")) for check in checks)
    missing = [check_id for check_id in REQUIRED_REDACTION_CHECKS if check_id not in check_ids]
    if missing:
        errors.append("redaction_checks missing: " + ", ".join(missing))
    for index, check_value in enumerate(checks):
        check = _mapping(check_value)
        _require(errors, check.get("required") is True, f"redaction_checks[{index}].required must be true")


def _validate_reviewer_checkpoints(errors: list[str], checkpoints: Sequence[Any]) -> None:
    checkpoint_ids = tuple(_text(_mapping(checkpoint).get("checkpoint_id")) for checkpoint in checkpoints)
    missing = [checkpoint_id for checkpoint_id in REQUIRED_REVIEWER_CHECKPOINTS if checkpoint_id not in checkpoint_ids]
    if missing:
        errors.append("reviewer_checkpoints missing: " + ", ".join(missing))
    for index, checkpoint_value in enumerate(checkpoints):
        checkpoint = _mapping(checkpoint_value)
        path = f"reviewer_checkpoints[{index}]"
        _require(errors, bool(_text(checkpoint.get("reviewer_role"))), f"{path}.reviewer_role is required")
        _require(errors, bool(_sequence(checkpoint.get("source_packet_ids"))), f"{path}.source_packet_ids must not be empty")
        _require(errors, checkpoint.get("required_before_pilot_closeout") is True, f"{path}.required_before_pilot_closeout must be true")
        _require(errors, checkpoint.get("approval_can_enable_official_action") is False, f"{path}.approval_can_enable_official_action must be false")


def _validate_abort_prompts(errors: list[str], prompts: tuple[str, ...]) -> None:
    _require(errors, bool(prompts), "abort_prompts must not be empty")
    haystack = "\n".join(prompts).casefold()
    missing = [term for term in REQUIRED_ABORT_TERMS if term.casefold() not in haystack]
    if missing:
        errors.append("abort_prompts missing required terms: " + ", ".join(missing))


def _validate_candidate_safety(errors: list[str], packet: Mapping[str, Any]) -> None:
    for path, value in _walk(packet):
        leaf = path[-1].casefold() if path else ""
        path_name = _path_name(path)
        if value is True:
            if leaf in PROHIBITED_TRUE_FLAGS:
                errors.append(f"{path_name} must be false for attended read-only pilot runbooks")
            if leaf in ENABLED_CONSEQUENTIAL_FLAGS or _is_enabled_consequential_leaf(leaf):
                errors.append(f"{path_name} must not enable upload/submission/payment/scheduling/cancellation/certification controls")
        if isinstance(value, str):
            text = value.strip()
            if not text:
                continue
            lowered = text.casefold()
            if _is_artifact_path_leaf(leaf) and not _is_negative_or_abort_context(lowered):
                errors.append(f"{path_name} must not reference private/session/browser artifact paths")
            if _looks_like_private_path(lowered):
                errors.append(f"{path_name} must not contain local private paths")
            if _looks_like_raw_authenticated_value(path, lowered):
                errors.append(f"{path_name} must not contain raw authenticated values")
            if _looks_like_live_execution_claim(lowered):
                errors.append(f"{path_name} must not claim live browser execution")
            if _looks_like_security_automation_claim(path, lowered):
                errors.append(f"{path_name} must not claim CAPTCHA/MFA/account-creation automation")


def _walk(value: Any, path: tuple[str, ...] = ()) -> Sequence[tuple[tuple[str, ...], Any]]:
    items: list[tuple[tuple[str, ...], Any]] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            items.extend(_walk(child, path + (_text(key),)))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            items.extend(_walk(child, path + (f"[{index}]",)))
    else:
        items.append((path, value))
    return tuple(items)


def _path_name(path: Sequence[str]) -> str:
    return ".".join(path) if path else ""


def _is_enabled_consequential_leaf(leaf: str) -> bool:
    if not (leaf.endswith("_enabled") or leaf.endswith("_allowed") or leaf.endswith("_available")):
        return False
    return any(term in leaf for term in ("upload", "submit", "submission", "payment", "schedule", "scheduling", "cancel", "cancellation", "certify", "certification"))


def _is_artifact_path_leaf(leaf: str) -> bool:
    if not (leaf.endswith("path") or leaf.endswith("paths") or leaf.endswith("file") or leaf.endswith("files") or leaf.endswith("uri") or leaf.endswith("url") or leaf.endswith("artifact") or leaf.endswith("artifacts")):
        return False
    return any(marker in leaf for marker in PROHIBITED_ARTIFACT_KEY_MARKERS)


def _looks_like_private_path(lowered: str) -> bool:
    return any(marker in lowered for marker in PRIVATE_PATH_MARKERS)


def _looks_like_raw_authenticated_value(path: Sequence[str], lowered: str) -> bool:
    joined_path = ".".join(path).casefold()
    if "raw_authenticated" in joined_path and lowered not in {"false", "none", "no", "not stored"}:
        return True
    return "permit number:" in lowered or "account email:" in lowered or "private field value:" in lowered


def _looks_like_live_execution_claim(lowered: str) -> bool:
    if _is_negative_or_abort_context(lowered):
        return False
    patterns = (
        r"\blive browser execution (completed|ran|executed|launched|succeeded)\b",
        r"\b(browser|playwright) (executed|launched|ran)\b",
        r"\blaunched (a )?(live )?(browser|playwright)\b",
    )
    return any(re.search(pattern, lowered) for pattern in patterns)


def _looks_like_security_automation_claim(path: Sequence[str], lowered: str) -> bool:
    joined_path = ".".join(path).casefold()
    if _is_negative_or_abort_context(lowered):
        return False
    mentions_security = any(term in lowered or term in joined_path for term in ("captcha", "mfa", "multi-factor", "account creation"))
    mentions_automation = any(term in lowered or term in joined_path for term in ("automate", "automation", "bypass", "solve", "create account"))
    return mentions_security and mentions_automation


def _is_negative_or_abort_context(lowered: str) -> bool:
    return lowered.startswith("abort ") or " must not " in lowered or " no " in lowered or "without " in lowered or "manually" in lowered


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: Any) -> tuple[Any, ...]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(value)
    return ()


def _string_tuple(value: Any) -> tuple[str, ...]:
    return tuple(item for item in _sequence(value) if isinstance(item, str))


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def _dedupe(values: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            deduped.append(value)
    return tuple(deduped)
