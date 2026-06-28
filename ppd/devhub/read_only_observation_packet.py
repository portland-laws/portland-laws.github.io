"""Validation for redacted DevHub read-only observation packets.

The validator is intentionally fixture-friendly and side-effect free. It accepts
only metadata-only read-only observation packets and rejects browser/session
artifacts, raw authenticated values, unsafe automation claims, and enabled
consequential DevHub controls.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Iterable, Mapping, Sequence


CONSEQUENTIAL_CONTROL_TYPES = frozenset(
    {
        "upload",
        "submission",
        "submit",
        "payment",
        "pay",
        "scheduling",
        "schedule",
        "cancellation",
        "cancel",
        "certification",
        "certify",
    }
)

ARTIFACT_KEY_MARKERS = (
    "auth_state",
    "authstate",
    "browser_context",
    "cookie",
    "credential",
    "download_path",
    "har",
    "har_path",
    "local_storage",
    "session_artifact",
    "session_file",
    "session_path",
    "session_state",
    "screenshot",
    "screenshot_path",
    "storage_state",
    "trace",
    "trace_path",
)

RAW_VALUE_KEY_MARKERS = (
    "account_number",
    "card_number",
    "cookie_value",
    "credential_value",
    "cvv",
    "password",
    "private_value",
    "raw_authenticated_text",
    "raw_authenticated_value",
    "raw_dom",
    "raw_field_value",
    "raw_page_text",
    "raw_private_value",
    "routing_number",
    "secret",
    "token",
)

LOCAL_PRIVATE_PATH_RE = re.compile(
    r"(^|\s)(/home/[^\s]+|/Users/[^\s]+|/private/[^\s]+|[A-Za-z]:\\\\Users\\\\[^\s]+|/tmp/devhub[^\s]*|/var/folders/[^\s]+)",
    re.IGNORECASE,
)

ARTIFACT_TEXT_RE = re.compile(
    r"\b(auth[-_ ]?state|storage[-_ ]?state|session[-_ ]?(state|file|path|artifact)|cookie|localStorage|sessionStorage|screenshot|trace\.zip|\bhar\b|\.har\b|downloaded? document|raw crawl output)\b",
    re.IGNORECASE,
)

RAW_AUTH_TEXT_RE = re.compile(
    r"\b(raw authenticated (text|value|page|dom)|raw private (text|value)|raw dom|unredacted (account|permit|invoice|payment|field|page)|bearer\s+[A-Za-z0-9._-]+|password=|token=|cookie=|cvv\b|card_number)\b",
    re.IGNORECASE,
)

UNSAFE_AUTOMATION_RE = re.compile(
    r"\b((automate|auto[- ]?solve|solve|bypass|complete|perform)\s+(captcha|mfa|multi[- ]?factor|account creation|account registration)|create\s+(a\s+)?devhub\s+account|register\s+(a\s+)?devhub\s+account)\b",
    re.IGNORECASE,
)

NEGATED_SAFETY_RE = re.compile(
    r"\b(do not|don't|must not|never|refuse|abort|manual only|human only|unsupported|not automate|without automating)\b",
    re.IGNORECASE,
)

TRUE_ENABLED_STATES = frozenset({"active", "allowed", "available", "enabled", "on", "ready", "true"})
FALSE_DISABLED_STATES = frozenset({"blocked", "disabled", "false", "manual_only", "off", "refused", "unavailable"})


@dataclass(frozen=True)
class ObservationPacketFinding:
    code: str
    path: str
    message: str


@dataclass(frozen=True)
class ObservationPacketValidationResult:
    findings: tuple[ObservationPacketFinding, ...]

    @property
    def ok(self) -> bool:
        return not self.findings

    def messages(self) -> list[str]:
        return [f"{finding.path}: {finding.message}" for finding in self.findings]

    def require_ok(self) -> None:
        if self.findings:
            raise ValueError("DevHub read-only observation packet failed validation: " + "; ".join(self.messages()))


def validate_devhub_read_only_observation_packet(packet: Mapping[str, Any]) -> ObservationPacketValidationResult:
    """Return validation findings for a DevHub read-only observation packet."""

    findings: list[ObservationPacketFinding] = []

    if not isinstance(packet, Mapping):
        return ObservationPacketValidationResult(
            (ObservationPacketFinding("invalid_packet", "$", "packet must be a mapping"),)
        )

    _require_non_empty_sequence(packet, "reviewer_notes", "$", findings)
    _require_non_empty_sequence(packet, "abort_prompts", "$", findings)
    _require_read_only_mode(packet, findings)
    _walk(packet, "$", findings)
    _require_observation_reviews(packet, findings)

    return ObservationPacketValidationResult(tuple(findings))


def assert_devhub_read_only_observation_packet(packet: Mapping[str, Any]) -> None:
    validate_devhub_read_only_observation_packet(packet).require_ok()


def _require_read_only_mode(packet: Mapping[str, Any], findings: list[ObservationPacketFinding]) -> None:
    mode = _text(packet.get("mode") or packet.get("run_mode") or packet.get("observation_mode")).lower()
    packet_kind = _text(packet.get("packet_kind") or packet.get("packet_type")).lower()
    if "read_only" not in mode and "read-only" not in mode and "read_only" not in packet_kind and "read-only" not in packet_kind:
        findings.append(
            ObservationPacketFinding(
                "missing_read_only_mode",
                "$",
                "packet must declare a read-only observation mode or packet kind",
            )
        )
    if packet.get("read_only_only") is False or packet.get("metadata_only") is False:
        findings.append(
            ObservationPacketFinding(
                "not_read_only_metadata_only",
                "$",
                "packet must be read-only and metadata-only",
            )
        )


def _require_observation_reviews(packet: Mapping[str, Any], findings: list[ObservationPacketFinding]) -> None:
    observations = packet.get("observations") or packet.get("observed_surfaces") or packet.get("redacted_observed_surfaces") or []
    if not isinstance(observations, Sequence) or isinstance(observations, (str, bytes, bytearray)):
        findings.append(
            ObservationPacketFinding("invalid_observations", "$.observations", "observations must be a sequence")
        )
        return
    for index, observation in enumerate(observations):
        if not isinstance(observation, Mapping):
            findings.append(
                ObservationPacketFinding(
                    "invalid_observation",
                    f"$.observations[{index}]",
                    "observation must be a mapping",
                )
            )
            continue
        path = f"$.observations[{index}]"
        _require_non_empty_sequence(observation, "reviewer_notes", path, findings)
        _require_non_empty_sequence(observation, "abort_prompts", path, findings)


def _require_non_empty_sequence(
    value: Mapping[str, Any], key: str, path: str, findings: list[ObservationPacketFinding]
) -> None:
    candidate = value.get(key)
    if not isinstance(candidate, Sequence) or isinstance(candidate, (str, bytes, bytearray)) or not candidate:
        findings.append(
            ObservationPacketFinding(
                f"missing_{key}",
                f"{path}.{key}",
                f"{key} must be a non-empty list",
            )
        )
        return
    if not all(_text(item).strip() for item in candidate):
        findings.append(
            ObservationPacketFinding(
                f"blank_{key}",
                f"{path}.{key}",
                f"{key} must not contain blank entries",
            )
        )


def _walk(value: Any, path: str, findings: list[ObservationPacketFinding]) -> None:
    if isinstance(value, Mapping):
        _reject_enabled_consequential_control(value, path, findings)
        for key, child in value.items():
            child_path = f"{path}.{key}"
            key_text = str(key)
            key_lower = _normalize_token(key_text)
            if _contains_marker(key_lower, ARTIFACT_KEY_MARKERS) and _artifact_key_has_private_payload(child):
                findings.append(
                    ObservationPacketFinding(
                        "private_session_artifact",
                        child_path,
                        "read-only observation packets must not include session, auth, screenshot, trace, HAR, cookie, or download artifacts",
                    )
                )
            if _contains_marker(key_lower, RAW_VALUE_KEY_MARKERS) and _has_present_value(child):
                findings.append(
                    ObservationPacketFinding(
                        "raw_authenticated_value",
                        child_path,
                        "read-only observation packets must not include raw authenticated values or secrets",
                    )
                )
            if _is_enabled_unsafe_automation_flag(key_lower, child):
                findings.append(
                    ObservationPacketFinding(
                        "unsafe_automation_claim",
                        child_path,
                        "CAPTCHA, MFA, and account creation automation must be refused or manual-only",
                    )
                )
            _walk(child, child_path, findings)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _walk(child, f"{path}[{index}]", findings)
    elif isinstance(value, str):
        _reject_string(value, path, findings)


def _reject_string(value: str, path: str, findings: list[ObservationPacketFinding]) -> None:
    text = value.strip()
    if not text:
        return
    if LOCAL_PRIVATE_PATH_RE.search(text):
        findings.append(
            ObservationPacketFinding(
                "local_private_path",
                path,
                "read-only observation packets must not reference local private paths",
            )
        )
    if ARTIFACT_TEXT_RE.search(text) and not _is_safety_negated(text):
        findings.append(
            ObservationPacketFinding(
                "private_session_artifact",
                path,
                "read-only observation packets must not reference persisted session, screenshot, trace, HAR, cookie, download, or auth artifacts",
            )
        )
    if RAW_AUTH_TEXT_RE.search(text) and not _is_safety_negated(text):
        findings.append(
            ObservationPacketFinding(
                "raw_authenticated_value",
                path,
                "read-only observation packets must not contain raw authenticated values",
            )
        )
    if UNSAFE_AUTOMATION_RE.search(text) and not _is_safety_negated(text):
        findings.append(
            ObservationPacketFinding(
                "unsafe_automation_claim",
                path,
                "CAPTCHA, MFA, and account creation automation claims are not allowed",
            )
        )


def _reject_enabled_consequential_control(
    value: Mapping[str, Any], path: str, findings: list[ObservationPacketFinding]
) -> None:
    control_text = " ".join(
        _text(value.get(key))
        for key in (
            "action",
            "action_class",
            "action_type",
            "capability",
            "category",
            "classification",
            "control_id",
            "control_type",
            "id",
            "kind",
            "label",
            "name",
            "type",
        )
    ).lower()
    mentioned_types = [control for control in CONSEQUENTIAL_CONTROL_TYPES if control in control_text]
    if not mentioned_types:
        return
    enabled = any(
        _is_enabled_state(value.get(key))
        for key in ("allowed", "automation_enabled", "control_enabled", "enabled", "may_execute", "submission_enabled")
    )
    enabled = enabled or _is_enabled_state(value.get("control_state")) or _is_enabled_state(value.get("state"))
    if enabled:
        findings.append(
            ObservationPacketFinding(
                "enabled_consequential_control",
                path,
                "upload, submission, payment, scheduling, cancellation, and certification controls must be disabled in read-only observation packets",
            )
        )


def _artifact_key_has_private_payload(value: Any) -> bool:
    if value in (None, False, "", [], {}, ()):
        return False
    if isinstance(value, str):
        return value.strip().lower() not in {"false", "none", "not_stored", "not stored", "absent", "redacted"}
    return value is not False


def _has_present_value(value: Any) -> bool:
    if value in (None, False, "", [], {}, ()):
        return False
    if isinstance(value, str):
        return value.strip().lower() not in {"redacted", "[redacted]", "not_recorded", "not recorded", "absent"}
    return True


def _is_enabled_unsafe_automation_flag(key_lower: str, value: Any) -> bool:
    if not any(marker in key_lower for marker in ("captcha", "mfa", "multi_factor", "account_creation", "account_registration")):
        return False
    if any(marker in key_lower for marker in ("refused", "blocked", "manual", "abort", "unsupported")):
        return False
    if any(marker in key_lower for marker in ("automation", "automated", "bypass", "solver", "create", "registration")):
        return _is_enabled_state(value) or _has_present_value(value)
    return False


def _is_enabled_state(value: Any) -> bool:
    if value is True:
        return True
    if value in (None, False):
        return False
    if isinstance(value, str):
        normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
        if normalized in FALSE_DISABLED_STATES:
            return False
        return normalized in TRUE_ENABLED_STATES
    return False


def _is_safety_negated(text: str) -> bool:
    return bool(NEGATED_SAFETY_RE.search(text))


def _contains_marker(key_lower: str, markers: Iterable[str]) -> bool:
    return any(marker in key_lower for marker in markers)


def _normalize_token(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)
