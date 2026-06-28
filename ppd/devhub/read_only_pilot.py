"""Fixture-first DevHub read-only pilot dry-run evidence packets.

This module intentionally does not launch browsers, persist session state, or collect
private DevHub values. It converts a committed operator go/no-go packet into a
commit-safe evidence packet suitable for validation before any attended live pilot.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence


READ_ONLY_OBJECTIVES: tuple[str, ...] = (
    "Confirm authenticated DevHub landing surfaces can be observed without writes.",
    "Record only redacted surface identifiers and accessible structure metadata.",
    "Verify permit/status/attachment/fee-notice review remains read-only.",
    "Stop before upload, submit, certify, schedule, cancel, withdraw, or payment actions.",
)

ABORT_DECISION_EXAMPLES: tuple[dict[str, str], ...] = (
    {
        "condition": "DevHub prompts for credentials, automated login, MFA, CAPTCHA, password recovery, or account creation.",
        "decision": "abort_and_manual_handoff",
        "reason": "Authentication challenges and account setup must be completed by the user without automation.",
    },
    {
        "condition": "A page requires upload, certification, submission, scheduling, cancellation, or payment to continue.",
        "decision": "abort_before_consequential_action",
        "reason": "The pilot is limited to read-only observation and cannot perform official or financial actions.",
    },
    {
        "condition": "A private value, document, screenshot, trace, HAR, cookie, or auth token would be stored.",
        "decision": "abort_before_artifact_capture",
        "reason": "Committed evidence may contain only redacted metadata and synthetic acknowledgements.",
    },
)

DEFERRED_LIVE_SESSION_PREREQUISITES: tuple[str, ...] = (
    "Attended user-visible browser session approved for the specific operator and account.",
    "Manual PortlandOregon.gov sign-in, MFA, and CAPTCHA handling by the user if presented.",
    "Gitignored ephemeral browser profile and trace/HAR/screenshot capture disabled by default.",
    "Operator review of exact abort conditions before opening DevHub.",
    "Post-session review confirming no browser artifacts or private values were committed.",
)

_REQUIRED_ACK_KEYS = (
    "read_only_scope",
    "no_browser_artifacts",
    "no_private_values",
    "abort_before_consequential_actions",
)
_ALLOWED_PILOT_DECISIONS = {"go_for_fixture_dry_run", "go"}
_REQUIRED_GO_NO_GO_LINK_TYPES = {"operator_go_no_go"}
_REQUIRED_ABORT_TERMS = (
    "credential",
    "automated login",
    "mfa",
    "captcha",
    "account creation",
    "upload",
    "submission",
    "payment",
    "scheduling",
    "cancellation",
    "certification",
    "screenshot",
    "trace",
    "har",
    "cookie",
    "auth state",
    "private value",
)
_REQUIRED_DISABLED_CONTROLS = (
    "upload",
    "submission",
    "payment",
    "scheduling",
    "cancellation",
    "certification",
)
_FORBIDDEN_KEYS = {
    "auth_state",
    "auth_state_path",
    "automated_login",
    "captcha_solution",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "field_value",
    "har",
    "har_path",
    "mfa_code",
    "password",
    "private_field_value",
    "raw_authenticated_text",
    "raw_dom",
    "screenshot",
    "screenshot_path",
    "session_state",
    "storage_state",
    "storage_state_path",
    "trace",
    "trace_path",
}
_FORBIDDEN_TEXT_PATTERNS = (
    re.compile(r"\bcredential(?:s)?\b", re.IGNORECASE),
    re.compile(r"\bautomated login\b|\blogin automation\b", re.IGNORECASE),
    re.compile(r"\b(?:automated|solved|completed)\s+(?:mfa|captcha)\b", re.IGNORECASE),
    re.compile(r"\baccount creation\b", re.IGNORECASE),
    re.compile(r"\b(?:screenshot|trace|har|cookie|auth state|storage state|private value)\b", re.IGNORECASE),
    re.compile(r"\b(?:uploaded|submitted|certified|paid|scheduled|cancelled|canceled)\b", re.IGNORECASE),
)


@dataclass(frozen=True)
class PilotEvidencePacket:
    """Commit-safe dry-run evidence for a future attended DevHub pilot."""

    packet_id: str
    source_operator_packet_id: str
    generated_at: str
    execution_mode: str
    devhub_launched: bool
    browser_artifacts_stored: bool
    live_session_deferred: bool
    synthetic_operator_acknowledgements: tuple[dict[str, str], ...]
    redacted_surface_ids: tuple[str, ...]
    read_only_observation_objectives: tuple[str, ...]
    abort_decision_examples: tuple[dict[str, str], ...]
    go_no_go_links: tuple[dict[str, str], ...]
    abort_decisions: tuple[dict[str, str], ...]
    disabled_consequential_controls: tuple[dict[str, Any], ...]
    journal_event_ids: tuple[str, ...]
    deferred_live_session_prerequisites: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "packet_id": self.packet_id,
            "source_operator_packet_id": self.source_operator_packet_id,
            "generated_at": self.generated_at,
            "execution_mode": self.execution_mode,
            "devhub_launched": self.devhub_launched,
            "browser_artifacts_stored": self.browser_artifacts_stored,
            "live_session_deferred": self.live_session_deferred,
            "synthetic_operator_acknowledgements": list(self.synthetic_operator_acknowledgements),
            "redacted_surface_ids": list(self.redacted_surface_ids),
            "read_only_observation_objectives": list(self.read_only_observation_objectives),
            "abort_decision_examples": list(self.abort_decision_examples),
            "go_no_go_links": list(self.go_no_go_links),
            "abort_decisions": list(self.abort_decisions),
            "disabled_consequential_controls": list(self.disabled_consequential_controls),
            "journal_event_ids": list(self.journal_event_ids),
            "deferred_live_session_prerequisites": list(self.deferred_live_session_prerequisites),
        }


def load_operator_go_no_go_packet(path: Path) -> dict[str, Any]:
    """Load a deterministic operator packet from a committed fixture."""

    with path.open("r", encoding="utf-8") as packet_file:
        packet = json.load(packet_file)
    if not isinstance(packet, dict):
        raise ValueError("operator go/no-go packet must be a JSON object")
    return packet


def build_read_only_pilot_evidence_packet(
    operator_packet: Mapping[str, Any],
    *,
    generated_at: str = "2026-05-28T00:00:00Z",
) -> PilotEvidencePacket:
    """Build a dry-run packet without opening DevHub or storing browser artifacts."""

    _validate_operator_packet(operator_packet)
    source_packet_id = _string_field(operator_packet, "packet_id")
    redacted_surface_ids = _redacted_surface_ids(operator_packet.get("surface_observations", ()))
    journal_event_ids = _journal_event_ids(source_packet_id, redacted_surface_ids)

    return PilotEvidencePacket(
        packet_id=_packet_id(source_packet_id, redacted_surface_ids),
        source_operator_packet_id=source_packet_id,
        generated_at=generated_at,
        execution_mode="fixture_first_devhub_read_only_pilot_dry_run",
        devhub_launched=False,
        browser_artifacts_stored=False,
        live_session_deferred=True,
        synthetic_operator_acknowledgements=_synthetic_acknowledgements(operator_packet),
        redacted_surface_ids=redacted_surface_ids,
        read_only_observation_objectives=READ_ONLY_OBJECTIVES,
        abort_decision_examples=ABORT_DECISION_EXAMPLES,
        go_no_go_links=_go_no_go_links(source_packet_id),
        abort_decisions=_abort_decisions(),
        disabled_consequential_controls=_disabled_consequential_controls(),
        journal_event_ids=journal_event_ids,
        deferred_live_session_prerequisites=DEFERRED_LIVE_SESSION_PREREQUISITES,
    )


def validate_read_only_pilot_evidence_packet(packet: Mapping[str, Any]) -> list[str]:
    """Return validation errors for a commit-safe dry-run evidence packet."""

    errors: list[str] = []
    if packet.get("execution_mode") != "fixture_first_devhub_read_only_pilot_dry_run":
        errors.append("execution_mode must identify the fixture-first read-only pilot dry-run")
    if packet.get("devhub_launched") is not False:
        errors.append("devhub_launched must be false")
    if packet.get("browser_artifacts_stored") is not False:
        errors.append("browser_artifacts_stored must be false")
    if packet.get("live_session_deferred") is not True:
        errors.append("live_session_deferred must be true")
    if not packet.get("synthetic_operator_acknowledgements"):
        errors.append("synthetic operator acknowledgements are required")
    if not packet.get("redacted_surface_ids"):
        errors.append("at least one redacted surface id is required")
    if not packet.get("read_only_observation_objectives"):
        errors.append("read-only observation objectives are required")
    if not packet.get("abort_decision_examples"):
        errors.append("abort-decision examples are required")
    if not packet.get("journal_event_ids"):
        errors.append("journal event ids are required")
    if not packet.get("deferred_live_session_prerequisites"):
        errors.append("deferred live-session prerequisites are required")
    _validate_go_no_go_links(errors, packet)
    _validate_abort_decisions(errors, packet.get("abort_decisions"))
    _validate_disabled_controls(errors, packet.get("disabled_consequential_controls"))
    _scan_for_forbidden_packet_content(errors, packet, "packet")
    return list(_dedupe(errors))


def _validate_operator_packet(operator_packet: Mapping[str, Any]) -> None:
    decision = _string_field(operator_packet, "pilot_decision")
    if decision not in _ALLOWED_PILOT_DECISIONS:
        raise ValueError(f"unsupported pilot_decision for fixture dry-run: {decision}")

    acknowledgements = operator_packet.get("operator_acknowledgements")
    if not isinstance(acknowledgements, Mapping):
        raise ValueError("operator_acknowledgements must be an object")
    missing = [key for key in _REQUIRED_ACK_KEYS if acknowledgements.get(key) is not True]
    if missing:
        raise ValueError("operator packet is missing required acknowledgement(s): " + ", ".join(missing))

    prohibited = operator_packet.get("prohibited_artifacts", ())
    if not isinstance(prohibited, Sequence) or isinstance(prohibited, (str, bytes)):
        raise ValueError("prohibited_artifacts must be an array")
    expected = {"credentials", "cookies", "auth_state", "screenshots", "traces", "har", "raw_private_values"}
    missing_artifacts = sorted(expected.difference(str(item) for item in prohibited))
    if missing_artifacts:
        raise ValueError("operator packet must prohibit artifact(s): " + ", ".join(missing_artifacts))


def _validate_go_no_go_links(errors: list[str], packet: Mapping[str, Any]) -> None:
    links = _sequence(packet.get("go_no_go_links"))
    if not links:
        errors.append("go_no_go_links must include the source operator go/no-go packet")
        return
    source_packet_id = _text(packet.get("source_operator_packet_id"))
    seen_types: set[str] = set()
    for index, row in enumerate(links):
        item = _mapping(row)
        path = f"go_no_go_links[{index}]"
        link_type = _text(item.get("link_type"))
        if link_type:
            seen_types.add(link_type)
        if link_type == "operator_go_no_go":
            if item.get("packet_id") != source_packet_id:
                errors.append(f"{path}.packet_id must match source_operator_packet_id")
            if item.get("consumed") is not True:
                errors.append(f"{path}.consumed must be true")
            if not _text(item.get("path")).startswith("ppd/tests/fixtures/"):
                errors.append(f"{path}.path must point to a committed PP&D fixture")
    missing = sorted(_REQUIRED_GO_NO_GO_LINK_TYPES - seen_types)
    if missing:
        errors.append("go_no_go_links missing link type(s): " + ", ".join(missing))


def _validate_abort_decisions(errors: list[str], value: Any) -> None:
    decisions = _sequence(value)
    if not decisions:
        errors.append("abort_decisions must be non-empty")
        return
    combined = "\n".join(
        " ".join(_text(_mapping(decision).get(field)) for field in ("condition", "decision", "reason"))
        for decision in decisions
    ).casefold()
    for term in _REQUIRED_ABORT_TERMS:
        if term not in combined:
            errors.append("abort_decisions missing required term: " + term)
    for index, decision in enumerate(decisions):
        item = _mapping(decision)
        path = f"abort_decisions[{index}]"
        for field in ("condition", "decision", "reason"):
            if not _text(item.get(field)):
                errors.append(f"{path}.{field} is required")
        if not _text(item.get("decision")).startswith("abort"):
            errors.append(f"{path}.decision must be an abort decision")


def _validate_disabled_controls(errors: list[str], value: Any) -> None:
    controls = _sequence(value)
    if not controls:
        errors.append("disabled_consequential_controls must be non-empty")
        return
    by_id = {_text(_mapping(control).get("control_id")): _mapping(control) for control in controls}
    for control_id in _REQUIRED_DISABLED_CONTROLS:
        control = by_id.get(control_id)
        if not control:
            errors.append("disabled_consequential_controls missing: " + control_id)
            continue
        if control.get("enabled") is not False:
            errors.append(f"disabled_consequential_controls.{control_id}.enabled must be false")
        if control.get("allowed_in_pilot") is not False:
            errors.append(f"disabled_consequential_controls.{control_id}.allowed_in_pilot must be false")
        if control.get("official_action_completed") is not False:
            errors.append(f"disabled_consequential_controls.{control_id}.official_action_completed must be false")


def _scan_for_forbidden_packet_content(errors: list[str], value: Any, path: str) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if key_text.casefold() in _FORBIDDEN_KEYS:
                errors.append(f"{path}.{key_text} contains forbidden credential/session/artifact/private field")
            if key_text.casefold() in {"official_action_completed", "official_actions_completed", "completed_official_action"} and _truthy(child):
                errors.append(f"{path}.{key_text} claims official action completion")
            _scan_for_forbidden_packet_content(errors, child, f"{path}.{key_text}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _scan_for_forbidden_packet_content(errors, child, f"{path}[{index}]")
    elif isinstance(value, str):
        for pattern in _FORBIDDEN_TEXT_PATTERNS:
            if pattern.search(value):
                errors.append(f"{path} contains prohibited DevHub pilot evidence content")
                break


def _synthetic_acknowledgements(operator_packet: Mapping[str, Any]) -> tuple[dict[str, str], ...]:
    acknowledgements = operator_packet["operator_acknowledgements"]
    if not isinstance(acknowledgements, Mapping):
        raise ValueError("operator_acknowledgements must be an object")

    operator_id = _string_field(operator_packet, "operator_id")
    return tuple(
        {
            "acknowledgement_id": f"ack-{name.replace('_', '-')}",
            "operator_id": operator_id,
            "status": "synthetic_acknowledged",
            "statement": _ack_statement(name),
        }
        for name in _REQUIRED_ACK_KEYS
        if acknowledgements.get(name) is True
    )


def _redacted_surface_ids(surface_observations: Any) -> tuple[str, ...]:
    if not isinstance(surface_observations, Sequence) or isinstance(surface_observations, (str, bytes)):
        raise ValueError("surface_observations must be an array")

    redacted_ids: list[str] = []
    for index, observation in enumerate(surface_observations, start=1):
        if not isinstance(observation, Mapping):
            raise ValueError("each surface observation must be an object")
        label = _string_field(observation, "surface_label")
        digest = hashlib.sha256(label.encode("utf-8")).hexdigest()[:12]
        redacted_ids.append(f"devhub-surface-redacted-{index:02d}-{digest}")

    if not redacted_ids:
        raise ValueError("surface_observations must include at least one read-only surface")
    return tuple(redacted_ids)


def _go_no_go_links(source_packet_id: str) -> tuple[dict[str, str], ...]:
    return (
        {
            "link_type": "operator_go_no_go",
            "packet_id": source_packet_id,
            "path": "ppd/tests/fixtures/devhub_read_only_pilot/operator_go_no_go_packet.json",
            "consumed": "true",
        },
    )


def _abort_decisions() -> tuple[dict[str, str], ...]:
    return ABORT_DECISION_EXAMPLES


def _disabled_consequential_controls() -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "control_id": control_id,
            "enabled": False,
            "allowed_in_pilot": False,
            "official_action_completed": False,
        }
        for control_id in _REQUIRED_DISABLED_CONTROLS
    )


def _journal_event_ids(source_packet_id: str, redacted_surface_ids: Sequence[str]) -> tuple[str, ...]:
    base = source_packet_id.lower().replace("_", "-")
    events = [f"journal-{base}-devhub-attended-preflight"]
    events.extend(f"journal-{base}-{surface_id}-read-only-observation" for surface_id in redacted_surface_ids)
    events.append(f"journal-{base}-manual-handoff-deferred")
    events.append(f"journal-{base}-completion-evidence-dry-run")
    return tuple(events)


def _packet_id(source_packet_id: str, redacted_surface_ids: Sequence[str]) -> str:
    digest_source = "|".join((source_packet_id, *redacted_surface_ids))
    digest = hashlib.sha256(digest_source.encode("utf-8")).hexdigest()[:16]
    return f"devhub-read-only-pilot-dry-run-{digest}"


def _ack_statement(name: str) -> str:
    statements = {
        "read_only_scope": "Operator accepted that this pilot evidence covers read-only observation only.",
        "no_browser_artifacts": "Operator accepted that no screenshots, traces, HAR files, cookies, or auth state are stored.",
        "no_private_values": "Operator accepted that private DevHub values are excluded from committed evidence.",
        "abort_before_consequential_actions": "Operator accepted abort-before-action rules for official and financial workflows.",
    }
    return statements[name]


def _string_field(mapping: Mapping[str, Any], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: Any) -> tuple[Any, ...]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(value)
    return ()


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _truthy(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, str):
        return value.strip().casefold() not in {"", "false", "no", "none", "not_applicable", "not applicable"}
    if isinstance(value, Mapping):
        return any(_truthy(child) for child in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_truthy(child) for child in value)
    return False


def _dedupe(values: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            output.append(value)
    return tuple(output)


def utc_now_iso() -> str:
    """Return a second-precision UTC timestamp for callers that need live metadata."""

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
