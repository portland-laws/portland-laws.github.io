"""Validation for post-candidate public-refresh monitoring plan v1.

This module is fixture-first and side-effect free. It validates committed
metadata only; it does not crawl, open DevHub, mutate scheduler state, or touch
browser/session artifacts.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import re
from typing import Any

PACKET_TYPE = "ppd.public_refresh_monitoring_plan.v1"
VALIDATION_COMMANDS = [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]]

REQUIRED_COVERAGE = {
    "official_anchor_coverage": "official anchors",
    "file_preparation_or_fee_payment_guidance_coverage": "file preparation or fee/payment guidance",
    "devhub_public_guidance_coverage": "DevHub public guidance",
    "forms_index_coverage": "forms index",
    "linked_portland_maps_coverage": "linked Portland Maps guidance",
}

_COVERAGE_ALIASES = {
    "official_anchor_coverage": {
        "official_anchor",
        "official_anchors",
        "official_anchor_coverage",
        "ppd_official_anchor",
    },
    "file_preparation_or_fee_payment_guidance_coverage": {
        "file_preparation",
        "file_preparation_guidance",
        "file_preparation_or_fee_payment_guidance",
        "fee_payment",
        "fee_payment_guidance",
        "file_preparation_or_fee_payment_guidance_coverage",
    },
    "devhub_public_guidance_coverage": {
        "devhub_public",
        "devhub_public_guidance",
        "devhub_public_guidance_coverage",
    },
    "forms_index_coverage": {
        "forms_index",
        "forms_index_coverage",
        "permit_applications_and_forms_index",
    },
    "linked_portland_maps_coverage": {
        "linked_portland_maps",
        "linked_portland_maps_coverage",
        "portland_maps",
        "portland_maps_linked_reference",
    },
}

_PRIVATE_ARTIFACT_FIELD_RE = re.compile(
    r"(auth[_-]?state|browser[_-]?(artifact|profile|state)?|cookie|credential|download(ed)?[_-]?(artifact|document|file|pdf)?|har|private[_-]?(artifact|file|path|value)?|raw[_-]?(artifact|body|capture|crawl|data|download|html|pdf)?|screenshot|session[_-]?(artifact|state|storage)?|storage[_-]?state|token|trace)",
    re.IGNORECASE,
)
_PRIVATE_ARTIFACT_TEXT_RE = re.compile(
    r"(^file://)|(^/home/[^/]+/)|(^/Users/[^/]+/)|(^/root/)|(^/tmp/)|(^[A-Za-z]:[\\/]Users[\\/][^\\/]+[\\/])|(auth[_ -]?state|browser[_ -]?(artifact|profile|state)|cookie|credential|downloaded[_ -]?(artifact|document|file|pdf)|har\b|private[_ -]?(artifact|file|path|value)|raw[_ -]?(artifact|body|capture|crawl|data|download|html|pdf)|screenshot|session[_ -]?(artifact|state|storage)|storage[_ -]?state|token|trace[_ -]?(file|zip)?)",
    re.IGNORECASE,
)
_LIVE_CLAIM_RE = re.compile(
    r"\b(live\s+(crawl|crawler|devhub|browser|fetch|monitor|run|execution)|ran\s+(crawl|crawler|devhub|browser|fetch|monitor)|opened\s+(devhub|a browser)|accessed\s+devhub|logged\s+in\s+to\s+devhub|used\s+authenticated\s+session)\b",
    re.IGNORECASE,
)
_OFFICIAL_ACTION_COMPLETION_RE = re.compile(
    r"\b(official\s+action\s+completed|completed\s+official\s+action|submitted\s+(the\s+)?(permit|application|request)|paid\s+(the\s+)?fee|payment\s+completed|scheduled\s+(an\s+)?inspection|uploaded\s+corrections?|certified\s+(the\s+)?acknowledg(e)?ment|cancelled\s+(the\s+)?(permit|application|request)|withdrew\s+(the\s+)?(permit|application|request))\b",
    re.IGNORECASE,
)
_SCHEDULER_MUTATION_FIELD_RE = re.compile(
    r"(^|_)(scheduler|schedule|cron|job|timer)[_-]?(state)?[_-]?(mutation|mutating|update|write|enable|activation|active)(_|$)|(^|_)(mutates|updates|writes|enables|activates)[_-]?(scheduler|schedule|cron|job|timer)(_|$)",
    re.IGNORECASE,
)
_SCHEDULER_MUTATION_TEXT_RE = re.compile(
    r"\b(mutates?|updates?|writes?|enables?|activates?)\s+(scheduler|schedule|cron|job|timer)\b|\b(scheduler|schedule|cron|job|timer)\s+(state\s+)?(mutation|update|write|enabled|activated)\b",
    re.IGNORECASE,
)
_ACTIVE_MUTATION_FIELD_RE = re.compile(
    r"(^|_)(active[_-]?)?(artifact|browser|crawl|devhub|guardrail|monitoring|prompt|release|scheduler|source|surface|agent|process|requirement)[_-]?(state[_-]?)?(mutation|mutating|update|write|promotion|refresh)(_|$)|(^|_)(mutates|updates|promotes|refreshes|writes)[_-]?(artifacts|browser|crawl|devhub|guardrails|monitoring|prompts|release|scheduler|sources|surfaces|agent|processes|requirements)(_|$)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class PublicRefreshMonitoringPlanV1ValidationResult:
    """Machine-readable validation result."""

    ready: bool
    problems: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {"ready": self.ready, "problems": list(self.problems)}


def validate_public_refresh_monitoring_plan_v1(packet: Mapping[str, Any]) -> PublicRefreshMonitoringPlanV1ValidationResult:
    """Validate a post-candidate public-refresh monitoring plan v1."""

    problems: list[str] = []
    if packet.get("packet_type") != PACKET_TYPE:
        problems.append(f"packet_type must be {PACKET_TYPE}")

    coverage = _coverage_keys(packet)
    for key, label in REQUIRED_COVERAGE.items():
        if key not in coverage:
            problems.append(f"missing {label} coverage")

    checks = _mapping_sequence(packet.get("monitoring_checks"))
    if not checks:
        problems.append("monitoring_checks must include at least one check")
    for index, check in enumerate(checks):
        path = f"monitoring_checks[{index}]"
        if not check.get("check_id"):
            problems.append(f"{path} lacks check_id")
        if not _text_list(check.get("source_evidence_ids")):
            problems.append(f"{path} lacks source_evidence_ids")
        if not _nonempty_mapping(check.get("hold_thresholds")) and not _nonempty_mapping(check.get("hold_threshold")):
            problems.append(f"{path} lacks hold thresholds")
        if not _has_reviewer_routing(check):
            problems.append(f"{path} lacks reviewer routing")

    if not _has_reviewer_routing(packet):
        problems.append("packet lacks reviewer routing")

    if packet.get("validation_commands") != VALIDATION_COMMANDS:
        problems.append("validation_commands must contain the exact PP&D daemon self-test command")

    problems.extend(_safety_problems(packet))
    return PublicRefreshMonitoringPlanV1ValidationResult(ready=not problems, problems=tuple(problems))


def require_public_refresh_monitoring_plan_v1(packet: Mapping[str, Any]) -> None:
    """Raise ValueError when a public-refresh monitoring plan v1 is invalid."""

    result = validate_public_refresh_monitoring_plan_v1(packet)
    if not result.ready:
        raise ValueError("invalid_public_refresh_monitoring_plan_v1: " + "; ".join(result.problems))


def _coverage_keys(packet: Mapping[str, Any]) -> set[str]:
    found: set[str] = set()
    candidates: list[Any] = []
    for key in ("coverage", "coverage_matrix", "required_coverage", "source_coverage", "monitoring_coverage"):
        value = packet.get(key)
        if value not in (None, False, "", [], {}):
            candidates.append(value)
    candidates.extend(_mapping_sequence(packet.get("normalized_source_evidence")))
    candidates.extend(_mapping_sequence(packet.get("sources")))
    candidates.extend(_mapping_sequence(packet.get("source_registry")))

    def visit(value: Any) -> None:
        if isinstance(value, Mapping):
            for key, child in value.items():
                key_text = str(key)
                if child is True:
                    _add_coverage(found, key_text)
                if key_text in {"coverage", "coverage_tags", "tags", "source_roles", "required_coverage"}:
                    visit(child)
                elif isinstance(child, (Mapping, list, tuple)):
                    visit(child)
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            for item in value:
                visit(item)
        elif isinstance(value, str):
            _add_coverage(found, value)

    for candidate in candidates:
        visit(candidate)
    return found


def _add_coverage(found: set[str], raw: str) -> None:
    normalized = raw.strip().lower().replace("-", "_").replace(" ", "_")
    for canonical, aliases in _COVERAGE_ALIASES.items():
        if normalized == canonical or normalized in aliases:
            found.add(canonical)


def _safety_problems(value: Any, path: str = "$") -> list[str]:
    problems: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if _PRIVATE_ARTIFACT_FIELD_RE.search(key_text) and child not in (None, False, "", [], {}):
                problems.append(f"private/session/browser/raw/downloaded artifact is not allowed at {child_path}")
            if _SCHEDULER_MUTATION_FIELD_RE.search(key_text) and child not in (None, False, "", [], {}):
                problems.append(f"scheduler-state mutation claim is not allowed at {child_path}")
            if _ACTIVE_MUTATION_FIELD_RE.search(key_text) and child is True:
                problems.append(f"active mutation flag is not allowed at {child_path}")
            problems.extend(_safety_problems(child, child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            problems.extend(_safety_problems(child, f"{path}[{index}]"))
    elif isinstance(value, str):
        if _PRIVATE_ARTIFACT_TEXT_RE.search(value):
            problems.append(f"private/session/browser/raw/downloaded artifact text is not allowed at {path}")
        if _LIVE_CLAIM_RE.search(value):
            problems.append(f"live crawl or DevHub claim is not allowed at {path}")
        if _OFFICIAL_ACTION_COMPLETION_RE.search(value):
            problems.append(f"official-action completion claim is not allowed at {path}")
        if _SCHEDULER_MUTATION_TEXT_RE.search(value):
            problems.append(f"scheduler-state mutation claim is not allowed at {path}")
    return problems


def _has_reviewer_routing(value: Mapping[str, Any]) -> bool:
    raw = value.get("reviewer_routing") or value.get("reviewer_route") or value.get("reviewer_owner")
    if isinstance(raw, str):
        return bool(raw)
    if isinstance(raw, Mapping):
        return bool(raw.get("primary_reviewer") or raw.get("reviewer_owner") or raw.get("escalation_reviewer") or raw.get("route_id"))
    if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes, bytearray)):
        return any(item not in (None, False, "", [], {}) for item in raw)
    return False


def _nonempty_mapping(value: Any) -> bool:
    return isinstance(value, Mapping) and bool(value)


def _mapping_sequence(value: Any) -> list[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        return [value]
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [item for item in value if isinstance(item, Mapping)]
    return []


def _text_list(value: Any) -> list[str]:
    if isinstance(value, str) and value:
        return [value]
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [item for item in value if isinstance(item, str) and item]
    return []
