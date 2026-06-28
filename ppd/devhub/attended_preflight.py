from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


MINIMUM_SELECTOR_CONFIDENCE = 0.85
REQUIRED_REFUSAL_POLICIES = (
    "automated_login",
    "mfa",
    "captcha",
    "account_creation",
    "credential_prompts",
    "cookies",
    "auth_state",
    "screenshots",
    "traces",
    "har_data",
    "private_field_values",
    "consequential_controls",
    "authenticated_session_capture",
)
REQUIRED_SAFETY_ASSERTIONS = (
    "automated_login",
    "automated_mfa",
    "automated_captcha",
    "account_creation",
    "credential_prompt_capture",
    "cookie_capture",
    "auth_state_capture",
    "screenshot_capture",
    "trace_capture",
    "har_capture",
    "private_field_value_capture",
    "consequential_control_automation",
    "authenticated_session_captured",
)
FORBIDDEN_TRUTHY_KEYS = {
    "automated_login": "automated login is prohibited",
    "login_automated": "automated login is prohibited",
    "automated_mfa": "MFA automation is prohibited",
    "mfa_automated": "MFA automation is prohibited",
    "automated_captcha": "CAPTCHA automation is prohibited",
    "captcha_automated": "CAPTCHA automation is prohibited",
    "account_creation_allowed": "account creation is prohibited",
    "automated_account_creation": "account creation is prohibited",
    "credential_prompt_capture": "credential prompts are prohibited",
    "credential_capture": "credential prompts are prohibited",
    "cookie_capture": "cookie capture is prohibited",
    "cookies_captured": "cookie capture is prohibited",
    "auth_state_capture": "auth state capture is prohibited",
    "storage_state_capture": "auth state capture is prohibited",
    "screenshot_capture": "screenshot capture is prohibited",
    "screenshots_captured": "screenshot capture is prohibited",
    "trace_capture": "trace capture is prohibited",
    "traces_captured": "trace capture is prohibited",
    "har_capture": "HAR data capture is prohibited",
    "har_data_capture": "HAR data capture is prohibited",
    "private_field_value_capture": "private field values are prohibited",
    "private_values_captured": "private field values are prohibited",
    "consequential_control_automation": "consequential controls are prohibited",
    "authenticated_session_captured": "claims that an authenticated session was captured are prohibited",
}
FORBIDDEN_TEXT_PATTERNS = (
    (re.compile(r"\bautomated\s+(login|sign[- ]?in)\b", re.IGNORECASE), "automated login is prohibited"),
    (re.compile(r"\b(login|sign[- ]?in)\s+was\s+automated\b", re.IGNORECASE), "automated login is prohibited"),
    (re.compile(r"\b(MFA|multi[- ]?factor)\s+(was\s+)?(automated|solved|completed\s+by\s+automation)\b", re.IGNORECASE), "MFA automation is prohibited"),
    (re.compile(r"\bCAPTCHA\s+(was\s+)?(automated|solved|bypassed|completed\s+by\s+automation)\b", re.IGNORECASE), "CAPTCHA automation is prohibited"),
    (re.compile(r"\b(account\s+creation|create\s+account)\s+(was\s+)?(automated|allowed|completed)\b", re.IGNORECASE), "account creation is prohibited"),
    (re.compile(r"\b(credentials?|passwords?)\s+(prompt\s+)?(captured|stored|saved|recorded)\b", re.IGNORECASE), "credential prompts are prohibited"),
    (re.compile(r"\bcookies?\s+(captured|stored|saved|recorded|included)\b", re.IGNORECASE), "cookie capture is prohibited"),
    (re.compile(r"\b(auth|authentication|storage)\s+state\s+(captured|stored|saved|recorded|included)\b", re.IGNORECASE), "auth state capture is prohibited"),
    (re.compile(r"\bscreenshots?\s+(captured|stored|saved|recorded|included)\b", re.IGNORECASE), "screenshot capture is prohibited"),
    (re.compile(r"\btraces?\s+(captured|stored|saved|recorded|included)\b", re.IGNORECASE), "trace capture is prohibited"),
    (re.compile(r"\bHAR\s+(data\s+)?(captured|stored|saved|recorded|included)\b", re.IGNORECASE), "HAR data capture is prohibited"),
    (re.compile(r"\bprivate\s+(field\s+)?values?\s+(captured|stored|saved|recorded|included)\b", re.IGNORECASE), "private field values are prohibited"),
    (re.compile(r"\bconsequential\s+controls?\s+(automated|clicked|submitted|activated)\b", re.IGNORECASE), "consequential controls are prohibited"),
    (re.compile(r"\bauthenticated\s+session\s+(was\s+)?captured\b", re.IGNORECASE), "claims that an authenticated session was captured are prohibited"),
    (re.compile(r"\bcaptured\s+an?\s+authenticated\s+session\b", re.IGNORECASE), "claims that an authenticated session was captured are prohibited"),
)
CONSEQUENTIAL_CONTROL_KINDS = {
    "submit",
    "upload",
    "certify",
    "pay",
    "payment",
    "schedule",
    "cancel",
    "withdraw",
    "account_creation",
    "login",
    "mfa",
    "captcha",
}


@dataclass(frozen=True)
class AttendedPreflightResult:
    preflight_passed: bool
    browser_action_plan_allowed: bool
    browser_launch_allowed: bool
    issues: tuple[str, ...]
    matched_surfaces: tuple[str, ...]
    exact_confirmation_checkpoints: tuple[str, ...]
    refused_action_policies: tuple[str, ...]


def load_attended_preflight_fixture(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("attended preflight fixture must be a JSON object")
    return value


def validate_attended_preflight_fixture(
    fixture: dict[str, Any],
    minimum_selector_confidence: float = MINIMUM_SELECTOR_CONFIDENCE,
) -> AttendedPreflightResult:
    issues: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            issues.append(message)

    require(fixture.get("fixture_only") is True, "fixture must be explicitly fixture_only")
    require(fixture.get("uses_live_devhub") is False, "fixture must not use live DevHub")
    require(fixture.get("stores_private_session_artifacts") is False, "fixture must not store private session artifacts")

    _validate_no_prohibited_packet_content(fixture, require)
    _validate_pilot_safety_assertions(fixture, require)

    manual_login = _as_mapping(fixture.get("manual_login_handoff"))
    require(manual_login.get("required") is True, "manual login handoff must be required")
    require(manual_login.get("requires_user_attendance") is True, "manual login handoff must require user attendance")
    require(manual_login.get("actor") == "user", "manual login handoff actor must be user")
    require(manual_login.get("credential_storage") == "forbidden", "credential storage must be forbidden")
    require(manual_login.get("credential_prompt_capture") is False, "credential prompt capture must be false")
    require(manual_login.get("session_state_storage") == "forbidden", "session state storage must be forbidden")
    require(manual_login.get("cookie_storage") == "forbidden", "cookie storage must be forbidden")
    require(manual_login.get("automated_login") is False, "automated login must be false")
    require(manual_login.get("account_creation_allowed") is False, "account creation must not be allowed during handoff")

    refused_policy_names = _validate_refusal_policies(fixture, require)
    checkpoints = _validate_exact_confirmation_checkpoints(fixture, require)
    surface_by_id = _validate_surface_map(fixture, minimum_selector_confidence, require)
    matched_surfaces = _validate_candidate_action_plan(
        fixture,
        surface_by_id,
        checkpoints,
        minimum_selector_confidence,
        require,
    )

    passed = not issues
    plan = _as_mapping(fixture.get("candidate_browser_action_plan"))
    browser_launch_allowed = bool(plan.get("browser_launch_allowed")) and passed

    return AttendedPreflightResult(
        preflight_passed=passed,
        browser_action_plan_allowed=passed,
        browser_launch_allowed=browser_launch_allowed,
        issues=tuple(issues),
        matched_surfaces=tuple(matched_surfaces),
        exact_confirmation_checkpoints=tuple(sorted(checkpoints)),
        refused_action_policies=tuple(sorted(refused_policy_names)),
    )


def _validate_pilot_safety_assertions(fixture: dict[str, Any], require: Any) -> None:
    assertions = _as_mapping(fixture.get("pilot_safety_assertions"))
    require(bool(assertions), "pilot safety assertions are required")
    for assertion in REQUIRED_SAFETY_ASSERTIONS:
        require(assertions.get(assertion) is False, f"{assertion} must be explicitly false")


def _validate_refusal_policies(fixture: dict[str, Any], require: Any) -> set[str]:
    policies = _as_mapping(fixture.get("refused_action_policies"))
    represented: set[str] = set()
    for policy_name in REQUIRED_REFUSAL_POLICIES:
        policy = _as_mapping(policies.get(policy_name))
        if policy:
            represented.add(policy_name)
        require(policy.get("decision") == "refuse", f"{policy_name} policy must refuse automation")
        require(policy.get("automate") is False, f"{policy_name} policy must set automate false")
        require(policy.get("requires_user_handoff") is True, f"{policy_name} policy must require user handoff")
    return represented


def _validate_exact_confirmation_checkpoints(fixture: dict[str, Any], require: Any) -> set[str]:
    checkpoint_ids: set[str] = set()
    for checkpoint in _as_list(fixture.get("exact_confirmation_checkpoints")):
        checkpoint_map = _as_mapping(checkpoint)
        checkpoint_id = checkpoint_map.get("checkpoint_id")
        if isinstance(checkpoint_id, str) and checkpoint_id:
            checkpoint_ids.add(checkpoint_id)
        require(isinstance(checkpoint_id, str) and bool(checkpoint_id), "exact confirmation checkpoint must have checkpoint_id")
        require(checkpoint_map.get("requires_user_presence") is True, "checkpoint must require user presence")
        require(checkpoint_map.get("before_browser_action_plan") is True, "checkpoint must be represented before browser action planning")
        text = checkpoint_map.get("exact_confirmation_text")
        require(isinstance(text, str) and bool(text.strip()), "checkpoint must include exact confirmation text")
    require(bool(checkpoint_ids), "at least one exact confirmation checkpoint is required")
    return checkpoint_ids


def _validate_surface_map(
    fixture: dict[str, Any],
    minimum_selector_confidence: float,
    require: Any,
) -> dict[str, dict[str, Any]]:
    surfaces = _as_list(fixture.get("surface_map"))
    require(bool(surfaces), "surface map must not be empty")
    surface_by_id: dict[str, dict[str, Any]] = {}
    for surface in surfaces:
        surface_map = _as_mapping(surface)
        surface_id = surface_map.get("surface_id")
        if isinstance(surface_id, str) and surface_id:
            surface_by_id[surface_id] = surface_map
        require(isinstance(surface_id, str) and bool(surface_id), "surface must have surface_id")
        require(surface_map.get("requires_attendance") is True, f"surface {surface_id!r} must require attendance")
        require(surface_map.get("requires_exact_confirmation") is True, f"surface {surface_id!r} must require exact confirmation")
        require(surface_map.get("stores_private_field_values") is False, f"surface {surface_id!r} must not store private field values")
        require(surface_map.get("captures_browser_artifacts") is False, f"surface {surface_id!r} must not capture browser artifacts")
        confidence = surface_map.get("selector_confidence")
        require(_is_number(confidence), f"surface {surface_id!r} selector confidence must be numeric")
        if _is_number(confidence):
            require(float(confidence) >= minimum_selector_confidence, f"surface {surface_id!r} selector confidence below threshold")
        selectors = _as_mapping(surface_map.get("selectors"))
        require(bool(selectors), f"surface {surface_id!r} must include selectors")
    return surface_by_id


def _validate_candidate_action_plan(
    fixture: dict[str, Any],
    surface_by_id: dict[str, dict[str, Any]],
    checkpoints: set[str],
    minimum_selector_confidence: float,
    require: Any,
) -> list[str]:
    plan = _as_mapping(fixture.get("candidate_browser_action_plan"))
    require(plan.get("fixture_only") is True, "candidate browser action plan must be fixture-only")
    require(plan.get("uses_live_devhub") is False, "candidate browser action plan must not use live DevHub")
    require(plan.get("browser_launch_allowed") is False, "candidate browser action plan must not allow browser launch")
    require(plan.get("captures_authenticated_session") is False, "candidate browser action plan must not claim an authenticated session was captured")
    require(plan.get("stores_private_session_artifacts") is False, "candidate browser action plan must not store private session artifacts")

    matched_surfaces: list[str] = []
    for action in _as_list(plan.get("actions")):
        action_map = _as_mapping(action)
        action_id = action_map.get("action_id")
        surface_id = action_map.get("surface_id")
        require(isinstance(action_id, str) and bool(action_id), "planned action must have action_id")
        require(isinstance(surface_id, str) and surface_id in surface_by_id, f"planned action {action_id!r} must match a known surface")
        if isinstance(surface_id, str) and surface_id in surface_by_id:
            matched_surfaces.append(surface_id)
        confidence = action_map.get("selector_confidence")
        require(_is_number(confidence), f"planned action {action_id!r} selector confidence must be numeric")
        if _is_number(confidence):
            require(float(confidence) >= minimum_selector_confidence, f"planned action {action_id!r} selector confidence below threshold")
        checkpoint_id = action_map.get("exact_confirmation_checkpoint_id")
        require(isinstance(checkpoint_id, str) and checkpoint_id in checkpoints, f"planned action {action_id!r} must reference an exact confirmation checkpoint")
        require(action_map.get("automates_consequential_action") is False, f"planned action {action_id!r} must not automate consequential action")
        require(action_map.get("automates_login") is False, f"planned action {action_id!r} must not automate login")
        require(action_map.get("captures_private_values") is False, f"planned action {action_id!r} must not capture private values")
        _validate_controls(action_id, action_map, require)
    require(bool(matched_surfaces), "candidate browser action plan must include at least one surface-matched action")
    return matched_surfaces


def _validate_controls(action_id: Any, action_map: dict[str, Any], require: Any) -> None:
    for control in _as_list(action_map.get("controls")):
        control_map = _as_mapping(control)
        control_kind = control_map.get("kind")
        automates = control_map.get("automates") is True or control_map.get("clicks") is True
        if isinstance(control_kind, str) and control_kind.lower() in CONSEQUENTIAL_CONTROL_KINDS:
            require(not automates, f"planned action {action_id!r} must not automate consequential control {control_kind!r}")


def _validate_no_prohibited_packet_content(fixture: dict[str, Any], require: Any) -> None:
    for path, key, value in _walk(fixture):
        if key in FORBIDDEN_TRUTHY_KEYS and _is_prohibited_truthy(value):
            require(False, f"{path}: {FORBIDDEN_TRUTHY_KEYS[key]}")
        if isinstance(value, str):
            for pattern, message in FORBIDDEN_TEXT_PATTERNS:
                if pattern.search(value):
                    require(False, f"{path}: {message}")


def _walk(value: Any, path: str = "$", key: str = "") -> list[tuple[str, str, Any]]:
    rows = [(path, key, value)]
    if isinstance(value, dict):
        for child_key, child_value in value.items():
            child_key_text = str(child_key)
            rows.extend(_walk(child_value, f"{path}.{child_key_text}", child_key_text))
    elif isinstance(value, list):
        for index, child_value in enumerate(value):
            rows.extend(_walk(child_value, f"{path}[{index}]", key))
    return rows


def _is_prohibited_truthy(value: Any) -> bool:
    if value is True:
        return True
    if value in (False, None):
        return False
    if isinstance(value, str):
        return value.strip().lower() not in {"", "false", "forbidden", "none", "not_captured", "not captured", "redacted"}
    return bool(value)


def _as_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return []


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)
