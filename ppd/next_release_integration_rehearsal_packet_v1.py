"""Validation for PP&D next-release integration rehearsal packet v1.

The packet is an offline-only rehearsal artifact. It references committed synthetic
inputs and reviewer decisions, but it must not claim live crawling, DevHub access,
official action completion, release promotion, private artifacts, or active state
mutation.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


PACKET_TYPE = "ppd.next_release_integration_rehearsal_packet.v1"
PACKET_VERSION = "v1"
REQUIRED_SCENARIOS = frozenset({"release-ready", "release-held", "release-rejected"})

REQUIRED_REFERENCE_SECTIONS = (
    ("source_freshness_references", "source freshness references"),
    ("requirement_delta_references", "requirement delta references"),
    ("process_delta_references", "process delta references"),
    ("guardrail_delta_references", "guardrail delta references"),
    ("gap_analysis_delta_references", "gap-analysis delta references"),
)

ACTIVE_MUTATION_KEYS = frozenset(
    {
        "active_source_mutation",
        "active_archive_mutation",
        "active_document_mutation",
        "active_requirement_mutation",
        "active_process_mutation",
        "active_guardrail_mutation",
        "active_gap_analysis_mutation",
        "active_prompt_mutation",
        "active_contract_mutation",
        "active_devhub_surface_mutation",
        "active_crawler_mutation",
        "active_release_mutation",
        "active_release_state_mutation",
        "active_daemon_state_mutation",
        "mutation_enabled",
        "allow_mutation",
        "write_enabled",
        "release_state_mutation",
    }
)

_PRIVATE_KEY_RE = re.compile(
    r"(?:auth_state|browser_state|browser_artifact|cookie|credential|downloaded|har|private_artifact|raw_body|raw_crawl|raw_download|screenshot|session|storage_state|trace)",
    re.IGNORECASE,
)
_PRIVATE_VALUE_RE = re.compile(
    r"(?:\b(?:auth_state|browser state|browser_state|cookie|credential|downloaded document|downloaded pdf|har file|private artifact|raw body|raw crawl output|raw download|screenshot|session storage|storage_state|trace file)\b|(?:^|[/\\])(?:downloads?|private|sessions?|traces?|raw)(?:[/\\]|$))",
    re.IGNORECASE,
)
_LIVE_OR_DEVHUB_RE = re.compile(
    r"\b(?:authenticated devhub|devhub login completed|live crawl completed|live crawl ran|live devhub|opened devhub|production crawl|used devhub access)\b",
    re.IGNORECASE,
)
_LEGAL_OR_PERMITTING_GUARANTEE_RE = re.compile(
    r"\b(?:approval is guaranteed|guarantee approval|guaranteed approval|legal advice|legally sufficient|permit will be approved|permit will be issued|will pass review)\b",
    re.IGNORECASE,
)
_OFFICIAL_ACTION_COMPLETION_RE = re.compile(
    r"\b(?:application submitted|certification completed|fee paid|inspection scheduled|official action completed|permit approved|permit issued|submitted to devhub|upload completed)\b",
    re.IGNORECASE,
)
_RELEASE_PROMOTION_RE = re.compile(
    r"\b(?:active release enabled|promoted to production|promotion completed|release promoted|released to production)\b",
    re.IGNORECASE,
)


class NextReleaseIntegrationRehearsalPacketV1Error(ValueError):
    """Raised when a next-release integration rehearsal packet is invalid."""

    def __init__(self, errors: Iterable[str]) -> None:
        self.errors = tuple(errors)
        super().__init__("invalid next-release integration rehearsal packet v1: " + "; ".join(self.errors))


def load_next_release_integration_rehearsal_packet_v1(path: Path | str) -> dict[str, Any]:
    """Load a JSON packet fixture from disk."""

    with Path(path).open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object at {path}")
    return value


def assert_next_release_integration_rehearsal_packet_v1(packet: Mapping[str, Any]) -> None:
    """Raise when the packet fails deterministic validation."""

    errors = validate_next_release_integration_rehearsal_packet_v1(packet)
    if errors:
        raise NextReleaseIntegrationRehearsalPacketV1Error(errors)


def validate_next_release_integration_rehearsal_packet_v1(packet: Mapping[str, Any]) -> list[str]:
    """Return deterministic validation errors for a v1 rehearsal packet."""

    errors: list[str] = []

    if packet.get("packet_type") != PACKET_TYPE:
        errors.append(f"packet_type must be {PACKET_TYPE}")
    if packet.get("packet_version") != PACKET_VERSION:
        errors.append(f"packet_version must be {PACKET_VERSION}")
    if packet.get("mode") != "offline_fixture_integration_rehearsal_only":
        errors.append("mode must be offline_fixture_integration_rehearsal_only")

    for section, label in REQUIRED_REFERENCE_SECTIONS:
        rows = _mapping_sequence(packet.get(section))
        if not rows:
            errors.append(f"missing {label}")
            continue
        for index, row in enumerate(rows):
            path = f"{section}[{index}]"
            if not _text(row.get("reference_id") or row.get("id")):
                errors.append(f"{path} must include reference_id")
            if not _text_sequence(row.get("source_evidence_ids")):
                errors.append(f"{path}.source_evidence_ids must include cited evidence")

    scenario_rows = _mapping_sequence(packet.get("release_scenarios"))
    present_scenarios = {_scenario_name(row) for row in scenario_rows if _scenario_name(row)}
    missing_scenarios = sorted(REQUIRED_SCENARIOS - present_scenarios)
    if missing_scenarios:
        errors.append("missing release scenario coverage: " + ", ".join(missing_scenarios))
    for index, row in enumerate(scenario_rows):
        path = f"release_scenarios[{index}]"
        if _scenario_name(row) not in REQUIRED_SCENARIOS:
            errors.append(f"{path}.scenario must be one of release-ready, release-held, release-rejected")
        if not _text(row.get("recommendation")):
            errors.append(f"{path}.recommendation must be present")
        if not _text_sequence(row.get("depends_on")):
            errors.append(f"{path}.depends_on must reference ordered dependencies")

    if not _mapping_sequence(packet.get("rollback_notes")):
        errors.append("missing rollback notes")
    if not _mapping_sequence(packet.get("reviewer_dispositions")):
        errors.append("missing reviewer dispositions")
    if not _mapping_sequence(packet.get("dependency_ordering")):
        errors.append("missing dependency ordering")
    if not _valid_commands(packet.get("validation_commands")):
        errors.append("missing validation commands")

    for path, value in _walk(packet):
        key = path[-1] if path else ""
        dotted = ".".join(path)
        lowered_key = key.lower()
        if _PRIVATE_KEY_RE.search(lowered_key):
            errors.append(f"private/session/browser/raw/downloaded artifact field is not allowed: {dotted}")
        if isinstance(value, str):
            _check_forbidden_text(dotted, value, errors)
        if _is_active_mutation_flag(lowered_key, value):
            errors.append(f"active mutation flag must not be true: {dotted}")

    return list(dict.fromkeys(errors))


def _check_forbidden_text(path: str, value: str, errors: list[str]) -> None:
    if _PRIVATE_VALUE_RE.search(value):
        errors.append(f"private/session/browser/raw/downloaded artifact reference is not allowed: {path}")
    if _LIVE_OR_DEVHUB_RE.search(value):
        errors.append(f"live crawl or DevHub claim is not allowed: {path}")
    if _LEGAL_OR_PERMITTING_GUARANTEE_RE.search(value):
        errors.append(f"legal or permitting guarantee is not allowed: {path}")
    if _OFFICIAL_ACTION_COMPLETION_RE.search(value):
        errors.append(f"official-action completion claim is not allowed: {path}")
    if _RELEASE_PROMOTION_RE.search(value):
        errors.append(f"release promotion claim is not allowed: {path}")


def _is_active_mutation_flag(key: str, value: Any) -> bool:
    if value is not True:
        return False
    return key in ACTIVE_MUTATION_KEYS or (key.startswith("active_") and key.endswith("_mutation"))


def _scenario_name(row: Mapping[str, Any]) -> str:
    value = row.get("scenario")
    return value.strip() if isinstance(value, str) else ""


def _mapping_sequence(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _text_sequence(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _valid_commands(value: Any) -> bool:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)) or not value:
        return False
    for command in value:
        if not isinstance(command, Sequence) or isinstance(command, (str, bytes, bytearray)) or not command:
            return False
        if not all(isinstance(part, str) and part.strip() for part in command):
            return False
    return True


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _walk(value: Any, path: tuple[str, ...] = ()) -> Iterable[tuple[tuple[str, ...], Any]]:
    yield path, value
    if isinstance(value, Mapping):
        for key, child in value.items():
            yield from _walk(child, path + (str(key),))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            yield from _walk(child, path + (str(index),))
