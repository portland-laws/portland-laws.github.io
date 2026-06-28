"""Validation-first release approval checklist packet v1.

This module validates committed synthetic approval checklist packets before any
inactive PP&D release candidate is assembled. It is offline-only and must not
crawl sources, open DevHub, fill forms, upload, submit, certify, pay, schedule,
promote releases, or mutate active PP&D state.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


PACKET_TYPE = "ppd.release_approval_checklist_packet.v1"
PACKET_VERSION = "v1"
MODE = "validation_first_inactive_release_candidate_checklist_only"

REQUIRED_GATES = (
    "source_freshness",
    "requirement_extraction",
    "process_dependency",
    "guardrail_impact",
    "agent_gap_analysis",
    "reviewer_disposition",
    "rollback_note",
    "dependency_order",
)

REQUIRED_DEPENDENCY_ORDER = REQUIRED_GATES + ("inactive_release_candidate_assembly",)
ALLOWED_RECOMMENDATIONS = frozenset({"release-ready", "release-held", "release-rejected"})
ALLOWED_GATE_STATUSES = frozenset({"passed", "requires_review", "blocked"})

OFFLINE_VALIDATION_COMMANDS: list[list[str]] = [
    ["python3", "-m", "py_compile", "ppd/release_approval_checklist_packet_v1.py"],
    ["python3", "-m", "unittest", "ppd.tests.test_release_approval_checklist_packet_v1"],
]

ACTIVE_MUTATION_KEYS = frozenset(
    {
        "active_source_mutation",
        "active_archive_mutation",
        "active_document_mutation",
        "active_requirement_mutation",
        "active_process_mutation",
        "active_process_model_mutation",
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
    r"\b(?:authenticated devhub|devhub login completed|live crawl completed|live crawl ran|live devhub|opened devhub|production crawl|used devhub access|crawled live sources)\b",
    re.IGNORECASE,
)
_OFFICIAL_ACTION_RE = re.compile(
    r"\b(?:application submitted|certification completed|fee paid|form filled|inspection scheduled|official action completed|payment submitted|permit approved|permit issued|scheduled inspection|submitted to devhub|upload completed)\b",
    re.IGNORECASE,
)
_RELEASE_PROMOTION_RE = re.compile(
    r"\b(?:active release enabled|assembled active release|promoted to production|promotion completed|release promoted|released to production)\b",
    re.IGNORECASE,
)
_LEGAL_OR_PERMITTING_GUARANTEE_RE = re.compile(
    r"\b(?:approval is guaranteed|guarantee approval|guaranteed approval|legal advice|legally sufficient|permit will be approved|permit will be issued|will pass review)\b",
    re.IGNORECASE,
)


class ReleaseApprovalChecklistPacketV1Error(ValueError):
    """Raised when a release approval checklist packet is invalid."""

    def __init__(self, errors: Iterable[str]) -> None:
        self.errors = tuple(errors)
        super().__init__("invalid release approval checklist packet v1: " + "; ".join(self.errors))


def load_release_approval_checklist_packet_v1(path: str | Path) -> dict[str, Any]:
    """Load a JSON approval checklist packet from disk."""

    with Path(path).open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object at {path}")
    return value


def build_release_approval_checklist_packet_v1(recommendations: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Build a validation-first checklist from synthetic rehearsal recommendations."""

    rows: list[dict[str, Any]] = []
    for recommendation in recommendations:
        candidate_id = _text(recommendation.get("candidate_id"))
        category = _text(recommendation.get("recommendation"))
        if not candidate_id:
            raise ValueError("recommendation candidate_id is required")
        if category not in ALLOWED_RECOMMENDATIONS:
            raise ValueError(f"unsupported recommendation for {candidate_id}: {category}")
        rows.append(
            {
                "candidate_id": candidate_id,
                "recommendation": category,
                "inactive_release_candidate_assembled": False,
                "assembly_allowed_before_checklist_passes": False,
                "checklist": _default_checklist_rows(candidate_id),
                "dependency_order": list(REQUIRED_DEPENDENCY_ORDER),
            }
        )

    return {
        "packet_type": PACKET_TYPE,
        "packet_version": PACKET_VERSION,
        "mode": MODE,
        "recommendations": rows,
        "inactive_release_candidate_assembly": {
            "status": "not_assembled",
            "allowed": False,
            "reason": "Approval checklist validation must pass before any inactive release candidate is assembled.",
        },
        "validation_commands": [list(command) for command in OFFLINE_VALIDATION_COMMANDS],
        "safety_attestations": {
            "offline_only": True,
            "no_live_crawling": True,
            "no_devhub_access": True,
            "no_private_files": True,
            "no_form_filling_upload_submission_certification_payment_or_scheduling": True,
            "no_release_promotion": True,
            "no_active_state_mutation": True,
        },
    }


def assert_release_approval_checklist_packet_v1(packet: Mapping[str, Any]) -> None:
    """Raise when the packet fails deterministic validation."""

    errors = validate_release_approval_checklist_packet_v1(packet)
    if errors:
        raise ReleaseApprovalChecklistPacketV1Error(errors)


def validate_release_approval_checklist_packet_v1(packet: Mapping[str, Any]) -> list[str]:
    """Return deterministic validation errors for a v1 approval checklist packet."""

    errors: list[str] = []

    if packet.get("packet_type") != PACKET_TYPE:
        errors.append(f"packet_type must be {PACKET_TYPE}")
    if packet.get("packet_version") != PACKET_VERSION:
        errors.append(f"packet_version must be {PACKET_VERSION}")
    if packet.get("mode") != MODE:
        errors.append(f"mode must be {MODE}")
    if packet.get("validation_commands") != OFFLINE_VALIDATION_COMMANDS:
        errors.append("validation_commands must exactly match the offline approval checklist commands")

    assembly = packet.get("inactive_release_candidate_assembly")
    if not isinstance(assembly, Mapping):
        errors.append("inactive_release_candidate_assembly must be present")
    else:
        if assembly.get("status") != "not_assembled":
            errors.append("inactive_release_candidate_assembly.status must be not_assembled")
        if assembly.get("allowed") is not False:
            errors.append("inactive_release_candidate_assembly.allowed must be false before checklist approval")

    attestations = packet.get("safety_attestations")
    if not isinstance(attestations, Mapping):
        errors.append("safety_attestations must be present")
    else:
        for key in (
            "offline_only",
            "no_live_crawling",
            "no_devhub_access",
            "no_private_files",
            "no_form_filling_upload_submission_certification_payment_or_scheduling",
            "no_release_promotion",
            "no_active_state_mutation",
        ):
            if attestations.get(key) is not True:
                errors.append(f"safety_attestations.{key} must be true")

    recommendations = _mapping_sequence(packet.get("recommendations"))
    if not recommendations:
        errors.append("recommendations must include synthetic next-release rehearsal rows")
    for index, recommendation in enumerate(recommendations):
        _validate_recommendation(index, recommendation, errors)

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


def _validate_recommendation(index: int, recommendation: Mapping[str, Any], errors: list[str]) -> None:
    path = f"recommendations[{index}]"
    candidate_id = _text(recommendation.get("candidate_id"))
    if not candidate_id:
        errors.append(f"{path}.candidate_id must be present")
    if recommendation.get("recommendation") not in ALLOWED_RECOMMENDATIONS:
        errors.append(f"{path}.recommendation must be release-ready, release-held, or release-rejected")
    if recommendation.get("inactive_release_candidate_assembled") is not False:
        errors.append(f"{path}.inactive_release_candidate_assembled must be false")
    if recommendation.get("assembly_allowed_before_checklist_passes") is not False:
        errors.append(f"{path}.assembly_allowed_before_checklist_passes must be false")

    dependency_order = _text_sequence(recommendation.get("dependency_order"))
    if dependency_order != list(REQUIRED_DEPENDENCY_ORDER):
        errors.append(f"{path}.dependency_order must cover required gates before inactive assembly")

    checklist = _mapping_sequence(recommendation.get("checklist"))
    gates = [_text(row.get("gate_id")) for row in checklist]
    missing_gates = [gate for gate in REQUIRED_GATES if gate not in gates]
    if missing_gates:
        errors.append(f"{path}.checklist missing gates: " + ", ".join(missing_gates))

    for row_index, row in enumerate(checklist):
        _validate_checklist_row(path, row_index, row, errors)


def _validate_checklist_row(parent_path: str, index: int, row: Mapping[str, Any], errors: list[str]) -> None:
    path = f"{parent_path}.checklist[{index}]"
    gate_id = _text(row.get("gate_id"))
    if gate_id not in REQUIRED_GATES:
        errors.append(f"{path}.gate_id must be one of the required approval gates")
    if row.get("status") not in ALLOWED_GATE_STATUSES:
        errors.append(f"{path}.status must be passed, requires_review, or blocked")
    if row.get("checked_before_candidate_assembly") is not True:
        errors.append(f"{path}.checked_before_candidate_assembly must be true")
    if not _text_sequence(row.get("evidence_ids")):
        errors.append(f"{path}.evidence_ids must cite synthetic fixture evidence")
    if not _text(row.get("reviewer_action")):
        errors.append(f"{path}.reviewer_action must be present")
    if row.get("offline_validation_commands") != OFFLINE_VALIDATION_COMMANDS:
        errors.append(f"{path}.offline_validation_commands must exactly match packet validation commands")


def _default_checklist_rows(candidate_id: str) -> list[dict[str, Any]]:
    labels = {
        "source_freshness": "Verify synthetic source freshness status and stale-source holds.",
        "requirement_extraction": "Verify synthetic requirement extraction coverage and human-review state.",
        "process_dependency": "Verify process dependency impacts before release recommendation review.",
        "guardrail_impact": "Verify guardrail impact rows and consequential-action blocks.",
        "agent_gap_analysis": "Verify changed missing facts, documents, confirmations, and blocked actions.",
        "reviewer_disposition": "Record reviewer disposition before candidate assembly.",
        "rollback_note": "Record rollback note proving no active state changed.",
        "dependency_order": "Verify dependency order covers every upstream packet before inactive assembly.",
    }
    return [
        {
            "gate_id": gate_id,
            "status": "requires_review",
            "checked_before_candidate_assembly": True,
            "evidence_ids": [f"synthetic:{candidate_id}:{gate_id}"],
            "reviewer_action": labels[gate_id],
            "offline_validation_commands": [list(command) for command in OFFLINE_VALIDATION_COMMANDS],
        }
        for gate_id in REQUIRED_GATES
    ]


def _check_forbidden_text(path: str, value: str, errors: list[str]) -> None:
    if _PRIVATE_VALUE_RE.search(value):
        errors.append(f"private/session/browser/raw/downloaded artifact reference is not allowed: {path}")
    if _LIVE_OR_DEVHUB_RE.search(value):
        errors.append(f"live crawl or DevHub claim is not allowed: {path}")
    if _OFFICIAL_ACTION_RE.search(value):
        errors.append(f"official action claim is not allowed: {path}")
    if _RELEASE_PROMOTION_RE.search(value):
        errors.append(f"release promotion claim is not allowed: {path}")
    if _LEGAL_OR_PERMITTING_GUARANTEE_RE.search(value):
        errors.append(f"legal or permitting guarantee is not allowed: {path}")


def _is_active_mutation_flag(key: str, value: Any) -> bool:
    if value is not True:
        return False
    return key in ACTIVE_MUTATION_KEYS or (key.startswith("active_") and key.endswith("_mutation"))


def _mapping_sequence(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _text_sequence(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


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


__all__ = [
    "OFFLINE_VALIDATION_COMMANDS",
    "PACKET_TYPE",
    "ReleaseApprovalChecklistPacketV1Error",
    "assert_release_approval_checklist_packet_v1",
    "build_release_approval_checklist_packet_v1",
    "load_release_approval_checklist_packet_v1",
    "validate_release_approval_checklist_packet_v1",
]
